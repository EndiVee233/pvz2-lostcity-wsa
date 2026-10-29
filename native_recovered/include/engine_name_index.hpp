#pragma once
#include "engine_registry.hpp"
#include "recovered_rb_tree.hpp"
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <type_traits>
#include <utility>

namespace pvz2_recovered::engine {
// Unsigned intern-ID keys. Object-name nodes own a name reference; type-name
// nodes do not (the original store/package metadata owns those references).
template<bool ObjectNames> class NameIndex {
public:
    using Value = std::conditional_t<ObjectNames, Descriptor32, std::uint32_t>;
    using ViewNode = std::conditional_t<ObjectNames, ObjectNameNode, StoreNameNode>;
    using OwnerView = std::conditional_t<ObjectNames, StoreView, RegistryView>;
private:
    struct Node {
        std::uint32_t color = 0;
        Node *parent = nullptr, *left = nullptr, *right = nullptr;
        std::uint32_t key = 0;
        Value value{};
        ViewNode view{};
    };
    struct Position { Node* x; Node* parent; };
    Node header_;
    std::size_t size_ = 0;
    InternStrings* pool_;
    Node* lower_bound(std::uint32_t key) const {
        auto* n = header_.parent; auto* candidate = const_cast<Node*>(&header_);
        while (n) {
            if (n->key < key) n = n->right;
            else { candidate = n; n = n->left; }
        }
        return candidate;
    }
    // 011ed354 / 011ebbec.
    Position position(std::uint32_t key) {
        auto* parent = &header_; auto* n = header_.parent; bool left = true;
        while (n) { parent = n; left = key < n->key; n = left ? n->left : n->right; }
        auto* before = parent;
        if (left) {
            if (before == header_.left) return {nullptr, parent};
            before = rb::previous(before);
        }
        return before->key < key ? Position{nullptr, parent} : Position{before, nullptr};
    }
    // 011ed404 / hint handling in 011ebc9c.
    Position hinted_position(std::uint32_t key, Node* hint) {
        if (hint == &header_) {
            if (size_ && header_.right->key < key) return {nullptr, header_.right};
            return position(key);
        }
        if (key < hint->key) {
            if (hint == header_.left) return {hint, hint};
            auto* before = rb::previous(hint);
            if (before->key < key) return !before->right ? Position{nullptr, before} : Position{hint, hint};
            return position(key);
        }
        if (hint->key < key) {
            if (hint == header_.right) return {nullptr, hint};
            auto* after = rb::next(hint);
            if (key < after->key) return !hint->right ? Position{nullptr, hint} : Position{after, after};
            return position(key);
        }
        return {hint, nullptr};
    }
    void drop_node(Node* n) {
        if constexpr (ObjectNames) pool_->release(n->key);
        delete n;
    }
    // 011ea120: recurse right, then remove the current node and walk left.
    void destroy(Node* n) {
        while (n) { destroy(n->right); auto* left = n->left; drop_node(n); n = left; }
    }
    static void ordered(Node* n, std::vector<Node*>& out) {
        if (n) { ordered(n->left, out); out.push_back(n); ordered(n->right, out); }
    }
    static const ViewNode* sync(Node* n) {
        if (!n) return nullptr;
        n->view.left = sync(n->left); n->view.right = sync(n->right); n->view.name = n->key;
        if constexpr (ObjectNames) n->view.descriptor = n->value;
        else n->view.encoded_type = n->value;
        return &n->view;
    }
public:
    explicit NameIndex(InternStrings* pool = nullptr) : pool_(pool) {
        if constexpr (ObjectNames) if (!pool_) throw std::invalid_argument("object-name index requires intern pool");
        header_.left = header_.right = &header_;
    }
    ~NameIndex() { destroy(header_.parent); }
    NameIndex(const NameIndex&) = delete;
    NameIndex& operator=(const NameIndex&) = delete;
    NameIndex(NameIndex&&) = delete;
    NameIndex& operator=(NameIndex&&) = delete;
    std::size_t size() const { return size_; }
    const Value* find(std::uint32_t key) const {
        const auto* n = lower_bound(key);
        return n != &header_ && n->key == key ? &n->value : nullptr;
    }
    // 011ed520 / 011ebc9c plus caller value write. Duplicate insertion preserves
    // the old value; object-name candidate retain/text/release still occurs.
    bool insert_unique(std::uint32_t key, const Value& value, const std::uint32_t* hint_key = nullptr) {
        auto* hint = &header_;
        if (hint_key) {
            hint = lower_bound(*hint_key);
            if (hint == &header_ || hint->key != *hint_key) throw std::invalid_argument("name insertion hint");
        }
        auto n = std::make_unique<Node>(); n->key = key;
        if constexpr (ObjectNames) { pool_->retain(key); (void)pool_->text_address(key); }
        const auto pos = hinted_position(key, hint);
        if (!pos.parent) {
            if constexpr (ObjectNames) pool_->release(key);
            return false;
        }
        const bool left = pos.x || pos.parent == &header_ || key < pos.parent->key;
        rb::insert(header_, left, n.get(), pos.parent); n->value = value; n.release(); ++size_;
        return true;
    }
    void put(std::uint32_t key, const Value& value) {
        auto* n = lower_bound(key);
        if (n != &header_ && n->key == key) { n->value = value; return; }
        const auto* hint = n == &header_ ? nullptr : &n->key;
        (void)insert_unique(key, value, hint);
    }
    bool erase(std::uint32_t key) {
        auto* n = lower_bound(key);
        if (n == &header_ || n->key != key) return false;
        drop_node(rb::erase(header_, n)); --size_; return true;
    }
    void clear() {
        destroy(header_.parent); header_.parent = nullptr; header_.left = header_.right = &header_; size_ = 0;
    }
    OwnerView attach(OwnerView view) { view.names = sync(header_.parent); return view; }
    std::vector<std::pair<std::uint32_t, Value>> entries() const {
        std::vector<Node*> nodes; ordered(header_.parent, nodes);
        std::vector<std::pair<std::uint32_t, Value>> out;
        for (const auto* n : nodes) out.emplace_back(n->key, n->value);
        return out;
    }
    std::vector<std::uint32_t> normalized_state() const {
        std::vector<Node*> nodes; ordered(header_.parent, nodes);
        const auto id = [&](const Node* n) -> std::uint32_t {
            if (!n) return 0xffffffffU;
            if (n == &header_) return 0xfffffffeU;
            const auto it = std::lower_bound(nodes.begin(), nodes.end(), n->key, [](const Node* p, std::uint32_t k) { return p->key < k; });
            if (it == nodes.end() || *it != n) throw std::logic_error("unknown name node");
            return static_cast<std::uint32_t>(it - nodes.begin());
        };
        std::vector<std::uint32_t> out{header_.color,id(header_.parent),id(header_.left),id(header_.right),static_cast<std::uint32_t>(size_)};
        for (const auto* n : nodes) {
            out.insert(out.end(), {n->color,id(n->parent),id(n->left),id(n->right),n->key});
            if constexpr (ObjectNames) out.insert(out.end(), n->value.begin(), n->value.end());
            else out.push_back(n->value);
        }
        return out;
    }
    void validate() const {
        if (header_.color) throw std::logic_error("name header color");
        if (!size_) {
            if (header_.parent || header_.left != &header_ || header_.right != &header_) throw std::logic_error("empty name header");
            return;
        }
        if (!header_.parent || header_.parent->parent != &header_ || header_.parent->color != 1) throw std::logic_error("name root");
        std::size_t count = 0; std::vector<Node*> nodes;
        const auto walk = [&](const auto& self, Node* n, Node* p, const std::uint32_t* lo, const std::uint32_t* hi) -> unsigned {
            if (!n) return 1;
            if (++count > size_ || n->parent != p || n->color > 1 || (lo && *lo >= n->key) || (hi && n->key >= *hi)) throw std::logic_error("name links/order");
            if (!n->color && ((n->left && !n->left->color) || (n->right && !n->right->color))) throw std::logic_error("name adjacent red");
            const auto a = self(self,n->left,n,lo,&n->key); nodes.push_back(n);
            const auto b = self(self,n->right,n,&n->key,hi);
            if (a != b) throw std::logic_error("name black height");
            return a + n->color;
        };
        (void)walk(walk,header_.parent,const_cast<Node*>(&header_),nullptr,nullptr);
        if (count != size_ || nodes.front() != header_.left || nodes.back() != header_.right) throw std::logic_error("name extrema/count");
    }
};
using TypeNameIndex = NameIndex<false>;
using ObjectNameIndex = NameIndex<true>;
// 011ee270: erase old name FIRST. Empty handle succeeds; invalid handle fails.
bool bind_object_name(StoreView, ObjectNameIndex&, std::uint32_t name, Handle);

struct StoreFactory {
    virtual ~StoreFactory() = default;
    virtual StoreView* construct(std::uint32_t encoded_type, std::uint32_t parameter_token) = 0;
    virtual void install_forwarder(StoreView&, std::uint32_t registry_offset) = 0;
};
// 011eefb0 orchestration. Complete store constructor/RTTI stays a service boundary.
class RegistryBanks {
    RegistryView view_;
    std::uint32_t primary_capacity_ = 0, secondary_capacity_ = 0;
public:
    StoreView* ensure(std::uint32_t encoded_type, std::uint32_t parameter_token, StoreFactory&);
    // Unregister boundary from 011ec274: clear the slot without shrinking a bank.
    StoreView* remove(std::uint32_t encoded_type);
    RegistryView view() const { return view_; }
    std::uint32_t primary_capacity() const { return primary_capacity_; }
    std::uint32_t secondary_capacity() const { return secondary_capacity_; }
};
}
