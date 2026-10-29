// Semantic recovery from libSrc.so ARM32; addresses use Ghidra ELF + 0x10000.
// Not linked to the game. Backend replaces unresolved engine/ABI dependencies.
// Host C++ standard library types below are NOT binary-compatible with the game.
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace pvz2_recovered {
struct Handle32 { std::uint32_t low, high; };
static_assert(sizeof(Handle32) == 8, "Original handles occupy two ARM words");
struct ProfileManagerLayout32 {
    std::uint8_t unknown00[0x74];
    std::uint32_t selected_id;
    std::uint8_t unknown78[8];
    std::uint8_t pending_save;
    std::uint8_t save_blocked;
    std::uint8_t unknown82[0x98 - 0x82];
};
static_assert(offsetof(ProfileManagerLayout32, selected_id) == 0x74, "Selected ID offset");
static_assert(sizeof(ProfileManagerLayout32) == 0x98, "Original manager allocation");
struct PlayerInfoPrefix32 {
    std::uint32_t unknown00;
    float pending_time;
    std::uint8_t unknown08[0x1ec - 8];
    std::uint32_t profile_id;
    std::uint8_t unknown1f0[0x4d4 - 0x1f0];
    std::int32_t modified_time;
};
static_assert(offsetof(PlayerInfoPrefix32, profile_id) == 0x1ec, "Player ID offset");
static_assert(offsetof(PlayerInfoPrefix32, pending_time) == 4, "Dirty scheduling field");
static_assert(offsetof(PlayerInfoPrefix32, modified_time) == 0x4d4, "Modification time offset");
static_assert(offsetof(ProfileManagerLayout32, pending_save) == 0x80, "Pending save flag");
static_assert(offsetof(ProfileManagerLayout32, save_blocked) == 0x81, "Save gate flag");

// A returned handle is held until release(). Conversion to native std::wstring,
// registry ownership and callback binding remain the backend's responsibility.
using Name = std::u32string;
struct Backend {
    virtual ~Backend() = default;
    virtual Handle32 find_by_name(ProfileManagerLayout32&, const Name&) = 0;
    virtual PlayerInfoPrefix32* resolve(const Handle32&) = 0;
    virtual void release(Handle32&) = 0;
    virtual void set_name(PlayerInfoPrefix32&, const Name&) = 0;
    virtual void sync(ProfileManagerLayout32&, int, int) = 0;
    virtual std::int32_t find_substring(const Name&, const Name&,
                                      std::uint32_t start, std::uint32_t count) = 0;
    // Used by the additional, not emulation-checked semantic reconstructions.
    virtual std::vector<Handle32> enumerate_profiles() = 0;
    virtual Name name_of(PlayerInfoPrefix32&) = 0;
    virtual void notify_delete(const Handle32&) = 0;
    virtual void remove_from_store(const Handle32&) = 0;
    virtual std::size_t profile_count() = 0;
};
struct HandleScope {
    Backend& backend;
    Handle32 handle;
    ~HandleScope() { backend.release(handle); }
    HandleScope(const HandleScope&) = delete;
    HandleScope& operator=(const HandleScope&) = delete;
    HandleScope(Backend& b, Handle32 h) : backend(b), handle(h) {}
    bool nonzero() const { return handle.low != 0 || handle.high != 0; }
};

// 007ba9f4. Assembly keeps the handle at fp-0x1c unchanged between resolves;
// Ghidra's overwritten uStack_20 variable is an SSA/type-recovery artifact.
inline bool select_by_name(Backend& b, ProfileManagerLayout32& mgr, const Name& name) {
    HandleScope h(b, b.find_by_name(mgr, name));
    if (!h.nonzero() || !b.resolve(h.handle)) return false;
    auto* profile = b.resolve(h.handle); // Original resolves twice.
    mgr.selected_id = profile->profile_id;
    return true;
}

// 007ba95c. Does not enforce uniqueness or input filtering: the editor's
// ValidateAndRename wrapper (007c13d0) supplies those checks.
inline bool rename_by_name(Backend& b, ProfileManagerLayout32& mgr,
                           const Name& old_name, const Name& new_name) {
    HandleScope h(b, b.find_by_name(mgr, old_name));
    if (!h.nonzero() || !b.resolve(h.handle)) return false;
    b.set_name(*b.resolve(h.handle), new_name);
    b.sync(mgr, 0, 0);
    return true;
}

// 007c0b38. Returns false on any match, including a match at index zero.
// Original code calls the Thumb basic_string::find helper with token length.
inline bool passes_substring_filter(Backend& b, const Name& name,
                                    const std::vector<Name>& tokens) {
    for (const auto& token : tokens) {
        if (b.find_substring(name, token, 0,
                            static_cast<std::uint32_t>(token.size())) != -1)
            return false;
    }
    return true;
}

// 007baa74. Original returns true after attempting to select the first entry;
// it does not propagate the result of select_by_name(). Enumeration order is
// engine registry order, not the UI list's separately sorted order.
inline bool select_first_available(Backend& b, ProfileManagerLayout32& mgr) {
    auto handles = b.enumerate_profiles();
    if (handles.empty()) return false;
    auto name = b.name_of(*b.resolve(handles.front()));
    select_by_name(b, mgr, name);
    return true;
}

// 007bdeac. Semantic reconstruction, not covered by this round's ARM tests.
// 0 = missing/expired; 1 = removed with profiles remaining; 2 = last removed.
// Local disk saving is NOT performed here; v4 adds it in the UI callback shim.
inline int delete_by_name(Backend& b, ProfileManagerLayout32& mgr, const Name& name) {
    HandleScope h(b, b.find_by_name(mgr, name));
    if (!h.nonzero() || !b.resolve(h.handle)) return 0;
    b.notify_delete(h.handle);
    b.remove_from_store(h.handle);
    if (b.profile_count() == 0) {
        mgr.selected_id = 0;
        return 2;
    }
    select_first_available(b, mgr);
    b.sync(mgr, 0, 0);
    return 1;
}
} // namespace pvz2_recovered
