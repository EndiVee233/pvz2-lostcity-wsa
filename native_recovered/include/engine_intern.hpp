#pragma once
#include "engine_registry.hpp"
#include <memory>
#include <string>

namespace pvz2_recovered::engine {
struct InternValue { std::uint32_t id = 0, text_token = 0; };
// Recovered pool ownership/count/list/index logic; std::u32string replaces the
// original Android wide-string storage ABI. ID zero represents empty text.
class InternPool final : public InternStrings {
    friend struct InternPoolFixtureAccess; // Test-only raw count boundary setup.
    struct Entry {
        std::uint32_t next, previous, index, references = 0;
        std::u32string text;
    };
    struct Node {
        std::uint32_t color = 0;
        Node *parent = nullptr, *left = nullptr, *right = nullptr;
        Entry* entry = nullptr;
    };
    struct Position { Node* x; Node* parent; };
    static constexpr std::uint32_t free_list = 0xfffffffeU, live_list = 0xffffffffU;
    std::vector<std::unique_ptr<Entry>> entries_;
    std::array<std::array<std::uint32_t, 2>, 2> anchors_{};
    std::uint32_t capacity_ = 0, size_ = 0;
    Node header_;
    Entry& entry(std::uint32_t id);
    const Entry& entry(std::uint32_t id) const;
    std::uint32_t& link(std::uint32_t token, unsigned word);
    const std::uint32_t& link(std::uint32_t token, unsigned word) const;
    void detach(std::uint32_t index);
    void insert_tail(std::uint32_t index, std::uint32_t anchor);
    Node* lower_bound(const std::u32string&) const;
    Position position(const std::u32string&);
    Position hinted_position(const std::u32string&, Node*);
    Node* insert_node(Entry&, Node* hint);
    static void ordered(Node*, std::vector<Node*>&);
    static void destroy(Node*);
    void remove_entry(Entry&);
public:
    InternPool();
    ~InternPool() override;
    InternPool(const InternPool&) = delete;
    InternPool& operator=(const InternPool&) = delete;
    InternPool(InternPool&&) = delete;
    InternPool& operator=(InternPool&&) = delete;
    // 011f2ed8/011f2d28: get/create ID, WITHOUT acquiring a reference.
    std::uint32_t intern(const char32_t*);
    // 011f1d88/011f1df8: lookup text without creating or retaining it.
    std::uint32_t find_id(const char32_t*) const;
    // 00594184: intern, retain, then read text.
    InternValue acquire(const char32_t*);
    // 011f153c/011f125c and 011f1f08/011f1ed4/011f1e38.
    // Nonzero IDs must refer to allocated entries. Arithmetic wraps at 32 bits.
    void retain(std::uint32_t) override;
    void release(std::uint32_t id) override { (void)release_counted(id); }
    std::uint32_t release_counted(std::uint32_t);
    // 011f14cc host boundary: an opaque ID token, NOT a truncated host pointer.
    // text(token) reads the associated UTF-32 content; zero reads empty content.
    std::uint32_t text_address(std::uint32_t) override;
    const std::u32string& text(std::uint32_t) const;
    std::uint32_t reference_count(std::uint32_t) const;
    // 00158a20 releases OLD before retaining NEW, even when IDs are equal.
    void assign_value(InternValue&, const InternValue&);
    // 001589f0 does not clear the value's ID/token.
    std::uint32_t release_value(const InternValue&);
    // Full normalized entry/list/index state for differential diagnostics.
    std::vector<std::uint32_t> normalized_state() const;
    void validate() const;
};
}
