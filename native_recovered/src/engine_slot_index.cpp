#include "engine_slot_index.hpp"
#include "recovered_rb_tree.hpp"
#include <algorithm>
#include <memory>
#include <stdexcept>

namespace pvz2_recovered::engine {
DescriptorIndex::DescriptorIndex() { header_.left = header_.right = &header_; }
DescriptorIndex::~DescriptorIndex() { destroy(header_.parent); }
void DescriptorIndex::clear() {
    destroy(header_.parent); header_.parent = nullptr; header_.left = header_.right = &header_; size_ = 0;
}
void DescriptorIndex::destroy(Node* n) {
    if (!n) return;
    destroy(n->left); destroy(n->right); delete n;
}
DescriptorIndex::Node* DescriptorIndex::lower_bound(const Descriptor32& key) const {
    auto* n = header_.parent;
    auto* candidate = const_cast<Node*>(&header_);
    while (n) {
        if (n->key < key) n = n->right;
        else { candidate = n; n = n->left; }
    }
    return candidate;
}
DescriptorIndex::Node* DescriptorIndex::next(Node* n) { return rb::next(n); }
DescriptorIndex::Node* DescriptorIndex::previous(Node* n) { return rb::previous(n); }
DescriptorIndex::Position DescriptorIndex::position(const Descriptor32& key) {
    auto* parent = &header_;
    auto* n = header_.parent;
    bool left = true;
    while (n) { parent = n; left = key < n->key; n = left ? n->left : n->right; }
    auto* before = parent;
    if (left) {
        if (before == header_.left) return {nullptr, parent};
        before = previous(before);
    }
    return before->key < key ? Position{nullptr, parent} : Position{before, nullptr};
}
DescriptorIndex::Position DescriptorIndex::hinted_position(const Descriptor32& key, Node* hint) {
    if (hint == &header_) {
        if (size_ && header_.right->key < key) return {nullptr, header_.right};
        return position(key);
    }
    if (key < hint->key) {
        if (hint == header_.left) return {hint, hint};
        auto* before = previous(hint);
        if (before->key < key) return !before->right ? Position{nullptr, before} : Position{hint, hint};
        return position(key);
    }
    if (hint->key < key) {
        if (hint == header_.right) return {nullptr, hint};
        auto* after = next(hint);
        if (key < after->key) return !hint->right ? Position{nullptr, hint} : Position{after, after};
        return position(key);
    }
    return {hint, nullptr};
}
void DescriptorIndex::rotate_left(Node* n) { rb::rotate_left(n, header_.parent); }
void DescriptorIndex::rotate_right(Node* n) { rb::rotate_right(n, header_.parent); }
void DescriptorIndex::insert_rebalance(bool left, Node* n, Node* parent) { rb::insert(header_, left, n, parent); }
bool DescriptorIndex::insert_unique(const Descriptor32& key, Handle value, const Descriptor32* hint_key) {
    auto* hint = &header_;
    if (hint_key) {
        hint = lower_bound(*hint_key);
        if (hint == &header_ || hint->key != *hint_key) throw std::invalid_argument("index insertion hint");
    }
    auto n = std::make_unique<Node>();
    n->key = key;
    const auto pos = hinted_position(key, hint);
    if (!pos.parent) return false;
    const bool left = pos.x || pos.parent == &header_ || key < pos.parent->key;
    insert_rebalance(left, n.get(), pos.parent);
    n->value = value;
    n.release();
    ++size_;
    return true;
}
void DescriptorIndex::put(const Descriptor32& key, Handle value) {
    auto* hint = lower_bound(key);
    if (hint != &header_ && hint->key == key) { hint->value = value; return; }
    const auto* hint_key = hint == &header_ ? nullptr : &hint->key;
    (void)insert_unique(key, value, hint_key);
}
DescriptorIndex::Node* DescriptorIndex::erase_rebalance(Node* z) { return rb::erase(header_, z); }
bool DescriptorIndex::erase(const Descriptor32& key) {
    auto* n = lower_bound(key);
    if (n == &header_ || n->key != key) return false;
    delete erase_rebalance(n);
    --size_;
    return true;
}
const Handle* DescriptorIndex::find(const Descriptor32& key) const {
    const auto* n = lower_bound(key);
    return n == &header_ || n->key != key ? nullptr : &n->value;
}
void DescriptorIndex::ordered(Node* n, std::vector<Node*>& nodes) {
    if (!n) return;
    ordered(n->left, nodes); nodes.push_back(n); ordered(n->right, nodes);
}
std::vector<std::pair<Descriptor32, Handle>> DescriptorIndex::entries() const {
    std::vector<Node*> nodes;
    ordered(header_.parent, nodes);
    std::vector<std::pair<Descriptor32, Handle>> result;
    result.reserve(size_);
    for (const auto* n : nodes) result.emplace_back(n->key, n->value);
    return result;
}
const DescriptorNode* DescriptorIndex::sync_view(Node* n) {
    if (!n) return nullptr;
    n->view = {sync_view(n->left), sync_view(n->right), n->key, n->value};
    return &n->view;
}
StoreView DescriptorIndex::attach(StoreView view) {
    view.descriptors = sync_view(header_.parent);
    return view;
}
std::vector<std::uint32_t> DescriptorIndex::normalized_state() const {
    std::vector<Node*> nodes;
    ordered(header_.parent, nodes);
    const auto id = [&](const Node* n) -> std::uint32_t {
        if (!n) return 0xffffffffU;
        if (n == &header_) return 0xfffffffeU;
        const auto it = std::lower_bound(nodes.begin(), nodes.end(), n->key,
            [](const Node* value, const Descriptor32& key) { return value->key < key; });
        if (it == nodes.end() || *it != n) throw std::logic_error("unknown descriptor node");
        return static_cast<std::uint32_t>(it - nodes.begin());
    };
    std::vector<std::uint32_t> result{header_.color, id(header_.parent), id(header_.left), id(header_.right),
        static_cast<std::uint32_t>(size_)};
    for (const auto* n : nodes) {
        result.insert(result.end(), {n->color, id(n->parent), id(n->left), id(n->right),
            n->key[0], n->key[1], n->key[2], n->value.low, n->value.high});
    }
    return result;
}
void DescriptorIndex::validate() const {
    if (header_.color != 0) throw std::logic_error("descriptor header color");
    if (!size_) {
        if (header_.parent || header_.left != &header_ || header_.right != &header_)
            throw std::logic_error("empty descriptor header");
        return;
    }
    if (!header_.parent || header_.parent->parent != &header_ || header_.parent->color != 1)
        throw std::logic_error("descriptor root");
    std::size_t visited = 0;
    const auto walk = [&](const auto& self, const Node* n, const Node* parent,
                           const Descriptor32* lo, const Descriptor32* hi) -> unsigned {
        if (!n) return 1;
        if (++visited > size_ || n->parent != parent || n->color > 1 ||
            (lo && !(*lo < n->key)) || (hi && !(n->key < *hi))) throw std::logic_error("descriptor links/order");
        if (n->color == 0 && ((n->left && n->left->color == 0) || (n->right && n->right->color == 0)))
            throw std::logic_error("adjacent red descriptor nodes");
        const auto l = self(self, n->left, n, lo, &n->key), r = self(self, n->right, n, &n->key, hi);
        if (l != r) throw std::logic_error("descriptor black height");
        return l + n->color;
    };
    (void)walk(walk, header_.parent, &header_, nullptr, nullptr);
    auto* minimum = header_.parent;
    while (minimum->left) minimum = minimum->left;
    auto* maximum = header_.parent;
    while (maximum->right) maximum = maximum->right;
    if (visited != size_ || header_.left != minimum || header_.right != maximum)
        throw std::logic_error("descriptor extrema/count");
}
}
