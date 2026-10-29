#include "engine_intern.hpp"
#include "recovered_rb_tree.hpp"
#include <algorithm>
#include <stdexcept>

namespace pvz2_recovered::engine {
InternPool::InternPool() {
    anchors_[0] = {free_list, free_list}; anchors_[1] = {live_list, live_list};
    header_.left = header_.right = &header_;
}
InternPool::~InternPool() { destroy(header_.parent); }
void InternPool::destroy(Node* n) { if (n) { destroy(n->left); destroy(n->right); delete n; } }
InternPool::Entry& InternPool::entry(std::uint32_t id) { return *entries_.at(id - 1); }
const InternPool::Entry& InternPool::entry(std::uint32_t id) const { return *entries_.at(id - 1); }
std::uint32_t& InternPool::link(std::uint32_t token, unsigned word) {
    if (token >= free_list) return anchors_[token - free_list][word];
    auto& e = *entries_.at(token);
    return word ? e.previous : e.next;
}
const std::uint32_t& InternPool::link(std::uint32_t token, unsigned word) const {
    if (token >= free_list) return anchors_[token - free_list][word];
    const auto& e = *entries_.at(token);
    return word ? e.previous : e.next;
}
void InternPool::detach(std::uint32_t index) {
    const auto next = link(index, 0), previous = link(index, 1);
    link(previous, 0) = next; link(next, 1) = previous; link(index, 1) = index;
}
void InternPool::insert_tail(std::uint32_t index, std::uint32_t anchor) {
    const auto previous = link(anchor, 1);
    link(index, 0) = anchor; link(index, 1) = previous;
    link(anchor, 1) = index; link(previous, 0) = index;
}
InternPool::Node* InternPool::lower_bound(const std::u32string& text) const {
    auto* candidate = const_cast<Node*>(&header_);
    auto* n = header_.parent;
    while (n) {
        if (n->entry->text < text) n = n->right;
        else { candidate = n; n = n->left; }
    }
    return candidate;
}
InternPool::Position InternPool::position(const std::u32string& text) {
    auto* parent = &header_;
    auto* n = header_.parent;
    bool left = true;
    while (n) { parent = n; left = text < n->entry->text; n = left ? n->left : n->right; }
    auto* before = parent;
    if (left) {
        if (before == header_.left) return {nullptr, parent};
        before = rb::previous(before);
    }
    return before->entry->text < text ? Position{nullptr, parent} : Position{before, nullptr};
}
InternPool::Position InternPool::hinted_position(const std::u32string& text, Node* hint) {
    if (hint == &header_) {
        if (size_ && header_.right->entry->text < text) return {nullptr, header_.right};
        return position(text);
    }
    if (text < hint->entry->text) {
        if (hint == header_.left) return {hint, hint};
        auto* before = rb::previous(hint);
        if (before->entry->text < text) return !before->right ? Position{nullptr, before} : Position{hint, hint};
        return position(text);
    }
    if (hint->entry->text < text) {
        if (hint == header_.right) return {nullptr, hint};
        auto* after = rb::next(hint);
        if (text < after->entry->text) return !hint->right ? Position{nullptr, hint} : Position{after, after};
        return position(text);
    }
    return {hint, nullptr};
}
InternPool::Node* InternPool::insert_node(Entry& e, Node* hint) {
    auto node = std::make_unique<Node>();
    node->entry = &e;
    const auto pos = hinted_position(e.text, hint);
    if (!pos.parent) return pos.x;
    const bool left = pos.x || pos.parent == &header_ || e.text < pos.parent->entry->text;
    rb::insert(header_, left, node.get(), pos.parent);
    ++size_;
    return node.release();
}
std::uint32_t InternPool::find_id(const char32_t* query) const {
    // nullptr is the host empty-input boundary; the raw original lookup itself
    // requires a valid null-terminated string.
    if (!query) return 0;
    const std::u32string text(query);
    const auto* n = lower_bound(text);
    return n != &header_ && n->entry->text == text ? n->entry->index + 1 : 0;
}
std::uint32_t InternPool::intern(const char32_t* query) {
    if (!query || !*query) return 0;
    if (const auto id = find_id(query)) return id;
    std::uint32_t index = link(free_list, 1);
    if (index == free_list) {
        index = static_cast<std::uint32_t>(entries_.size());
        auto e = std::make_unique<Entry>();
        e->index = index; e->next = e->previous = index;
        if (entries_.size() == capacity_) {
            const auto capacity = capacity_ ? capacity_ * 2 : 1;
            if (capacity < capacity_ || capacity > 0x3fffffffU) throw std::length_error("intern pointer table capacity");
            entries_.reserve(capacity); capacity_ = capacity;
        }
        entries_.push_back(std::move(e));
    }
    auto& e = *entries_[index];
    e.text = query;
    e.references = 0;
    detach(index); insert_tail(index, live_list);
    auto* hint = lower_bound(e.text);
    auto* node = insert_node(e, hint);
    node->entry = &e;
    return index + 1;
}
InternValue InternPool::acquire(const char32_t* query) {
    const auto id = intern(query);
    retain(id);
    return {id, text_address(id)};
}
void InternPool::retain(std::uint32_t id) { if (id) ++entry(id).references; }
std::uint32_t InternPool::release_counted(std::uint32_t id) {
    if (!id) return 0;
    auto& e = entry(id);
    const auto remaining = --e.references;
    if (!remaining) remove_entry(e);
    return remaining;
}
void InternPool::remove_entry(Entry& e) {
    auto* n = lower_bound(e.text);
    // Original release dereferences the corresponding index result without a
    // missing-key fallback. A live matching entry is an explicit precondition.
    if (n == &header_ || n->entry != &e) throw std::logic_error("intern entry is not indexed");
    delete rb::erase(header_, n); --size_;
    e.text.clear();
    detach(e.index); insert_tail(e.index, free_list);
}
std::uint32_t InternPool::text_address(std::uint32_t id) { if (id) (void)entry(id); return id; }
const std::u32string& InternPool::text(std::uint32_t id) const {
    static const std::u32string empty;
    return id ? entry(id).text : empty;
}
std::uint32_t InternPool::reference_count(std::uint32_t id) const { return id ? entry(id).references : 0; }
void InternPool::assign_value(InternValue& destination, const InternValue& source) {
    release(destination.id);
    destination.id = source.id;
    retain(destination.id);
    destination.text_token = text_address(destination.id);
}
std::uint32_t InternPool::release_value(const InternValue& value) { return release_counted(value.id); }
void InternPool::ordered(Node* n, std::vector<Node*>& nodes) {
    if (n) { ordered(n->left, nodes); nodes.push_back(n); ordered(n->right, nodes); }
}
std::vector<std::uint32_t> InternPool::normalized_state() const {
    std::vector<std::uint32_t> result{static_cast<std::uint32_t>(entries_.size()), capacity_, size_};
    for (const auto& a : anchors_) result.insert(result.end(), a.begin(), a.end());
    for (const auto& e : entries_) {
        result.insert(result.end(), {e->next, e->previous, e->index, e->references, static_cast<std::uint32_t>(e->text.size())});
        for (auto c : e->text) result.push_back(static_cast<std::uint32_t>(c));
    }
    std::vector<Node*> nodes;
    ordered(header_.parent, nodes);
    const auto id = [&](const Node* n) -> std::uint32_t {
        if (!n) return 0xffffffffU;
        if (n == &header_) return 0xfffffffeU;
        const auto it = std::lower_bound(nodes.begin(), nodes.end(), n->entry->text,
            [](const Node* a, const std::u32string& t) { return a->entry->text < t; });
        if (it == nodes.end() || *it != n) throw std::logic_error("unknown intern node");
        return static_cast<std::uint32_t>(it - nodes.begin());
    };
    result.insert(result.end(), {header_.color, id(header_.parent), id(header_.left), id(header_.right), size_});
    for (const auto* n : nodes) result.insert(result.end(), {n->color, id(n->parent), id(n->left), id(n->right), n->entry->index});
    return result;
}
void InternPool::validate() const {
    if (header_.color || entries_.size() > capacity_) throw std::logic_error("intern header/capacity");
    std::vector<bool> listed(entries_.size());
    std::vector<bool> active(entries_.size());
    for (unsigned list = 0; list < 2; ++list) {
        const auto anchor = free_list + list;
        auto previous = anchor;
        for (auto i = link(anchor, 0); i != anchor; i = link(i, 0)) {
            if (i >= entries_.size() || listed[i] || link(i, 1) != previous || entries_[i]->index != i)
                throw std::logic_error("intern list links");
            if (!list && !entries_[i]->text.empty()) throw std::logic_error("free intern text");
            listed[i] = true; active[i] = list != 0; previous = i;
        }
        if (link(anchor, 1) != previous) throw std::logic_error("intern list tail");
    }
    if (std::find(listed.begin(), listed.end(), false) != listed.end()) throw std::logic_error("unlisted intern entry");
    if (!size_) {
        if (header_.parent || header_.left != &header_ || header_.right != &header_)
            throw std::logic_error("empty intern tree");
        return;
    }
    if (!header_.parent || header_.parent->parent != &header_ || header_.parent->color != 1)
        throw std::logic_error("intern root");
    std::vector<Node*> nodes;
    const auto walk = [&](const auto& self, Node* n, Node* parent,
                           const std::u32string* lo, const std::u32string* hi) -> unsigned {
        if (!n) return 1;
        if (n->parent != parent || n->color > 1 || !n->entry || !active.at(n->entry->index) ||
            (lo && !(*lo < n->entry->text)) || (hi && !(n->entry->text < *hi))) throw std::logic_error("intern tree links/order");
        if (n->color == 0 && ((n->left && !n->left->color) || (n->right && !n->right->color)))
            throw std::logic_error("intern adjacent red nodes");
        const auto l = self(self, n->left, n, lo, &n->entry->text);
        nodes.push_back(n);
        const auto r = self(self, n->right, n, &n->entry->text, hi);
        if (l != r) throw std::logic_error("intern black height");
        return l + n->color;
    };
    (void)walk(walk, header_.parent, const_cast<Node*>(&header_), nullptr, nullptr);
    if (nodes.size() != size_ || std::count(active.begin(), active.end(), true) != static_cast<std::ptrdiff_t>(size_) ||
        nodes.front() != header_.left || nodes.back() != header_.right) throw std::logic_error("intern count/extrema");
}
}
