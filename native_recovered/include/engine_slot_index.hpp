#pragma once
#include "engine_registry.hpp"
#include <utility>

namespace pvz2_recovered::engine {
// Recovered descriptor red-black tree. Links are host pointers, not ARM32 ABI.
// Colors follow the original: red=0, black=1; the header remains red.
class DescriptorIndex {
    struct Node {
        std::uint32_t color = 0;
        Node *parent = nullptr, *left = nullptr, *right = nullptr;
        Descriptor32 key{};
        Handle value{};
        DescriptorNode view{};
    };
    struct Position { Node* x; Node* parent; };
    Node header_;
    std::size_t size_ = 0;
    Node* lower_bound(const Descriptor32&) const;
    static Node* next(Node*);
    static Node* previous(Node*);
    Position position(const Descriptor32&);
    Position hinted_position(const Descriptor32&, Node*);
    void rotate_left(Node*);
    void rotate_right(Node*);
    void insert_rebalance(bool left, Node*, Node* parent);
    Node* erase_rebalance(Node*);
    static void destroy(Node*);
    static const DescriptorNode* sync_view(Node*);
    static void ordered(Node*, std::vector<Node*>&);
public:
    DescriptorIndex();
    ~DescriptorIndex();
    DescriptorIndex(const DescriptorIndex&) = delete;
    DescriptorIndex& operator=(const DescriptorIndex&) = delete;
    DescriptorIndex(DescriptorIndex&&) = delete;
    DescriptorIndex& operator=(DescriptorIndex&&) = delete;
    // 011ecff0 plus caller value assignment. nullptr means the end hint.
    // A non-null hint must name an existing node. Duplicate keys keep their value.
    bool insert_unique(const Descriptor32&, Handle, const Descriptor32* hint = nullptr);
    // Slot creation caller semantics: replace the value of an existing key.
    void put(const Descriptor32&, Handle);
    // 014e2e64 plus the original caller's delete/count decrement.
    bool erase(const Descriptor32&);
    void clear();
    const Handle* find(const Descriptor32&) const;
    std::size_t size() const { return size_; }
    std::vector<std::pair<Descriptor32, Handle>> entries() const;
    // Adapts the actual recovered topology to the round-12 read-only interface.
    // Refresh after mutation or pool growth; no concurrent mutation of a view.
    StoreView attach(StoreView);
    // Header color/root/min/max/count, then key-ordered nodes serialized as
    // color/parent/left/right/key[3]/handle[2]. Links use key ranks;
    // 0xfffffffe denotes header and 0xffffffff denotes null.
    std::vector<std::uint32_t> normalized_state() const;
    void validate() const;
};
}
