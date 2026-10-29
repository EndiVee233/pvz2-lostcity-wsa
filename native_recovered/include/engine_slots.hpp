#pragma once
#include "engine_registry.hpp"

namespace pvz2_recovered::engine {
enum class SlotEvent { created, before_release };
struct SlotServices {
    // Callbacks/destructors must not relocate the slot array, reenter release,
    // invalidate the current slot, or throw. Such behavior is outside recovery.
    virtual ~SlotServices() = default;
    virtual std::size_t callback_count(SlotEvent) = 0;
    virtual void callback(SlotEvent, std::size_t, Handle) = 0;
    // DescriptorIndex supplies the recovered tree implementation through this
    // boundary. Object ownership and external callbacks remain caller services.
    virtual void put_descriptor(const Descriptor32&, Handle) = 0;
    virtual void erase_descriptor(const Descriptor32&) = 0;
    // The original invokes object vtable +0x14. Addresses here are ARM32 tokens.
    virtual void destroy_object(std::uint32_t) = 0;
};
struct SlotCounts { std::uint32_t free = 0, live = 0, deferred = 0, retired = 0; };

class SlotPool {
public:
    // Stable index links replace relocated ARM32 pointers in this host owner.
    // Slot payload offsets stay identical; unknown00 holds these internal tokens.
    static constexpr std::uint32_t free_list = 0xfffffffcU;
    static constexpr std::uint32_t active_list = 0xfffffffdU;
    static constexpr std::uint32_t deferred_list = 0xfffffffeU;
    static constexpr std::uint32_t retired_list = 0xffffffffU;
private:
    std::uint32_t type_;
    std::vector<Slot32> slots_;
    std::array<std::array<std::uint32_t, 2>, 4> anchors_{};
    std::uint32_t& link(std::uint32_t token, unsigned word);
    const std::uint32_t& link(std::uint32_t token, unsigned word) const;
    void detach(std::uint32_t index);
    void insert_before(std::uint32_t index, std::uint32_t next);
    Handle packed(std::uint32_t index) const;
public:
    SlotCounts counts;
    explicit SlotPool(std::uint32_t type);
    // 011e5f08. Growth only; views/pointers must be refreshed after a growth.
    void grow(std::uint32_t capacity);
    // 011e60e8. Move the free-list tail to the active-list tail; does not init payload.
    std::uint32_t take_slot();
    // 011e6168. Caller must supply a slot already belonging to one of the lists.
    void recycle(std::uint32_t index, bool defer);
    // 011ed120, including the optional default-descriptor path via 011f173c.
    Handle create(std::uint32_t object, int mode, std::uint8_t marked,
                  const Descriptor32* descriptor, std::uint32_t descriptor_seed, SlotServices&);
    // 011e6424 / 011e6450 / 011e6600. Reference count is the low 26 bits of flags.
    void retain(Handle);
    bool release(Handle, SlotServices&);
    std::uint32_t reference_count(Handle);
    // 011e6b0c. Destroy deferred objects, then return slots to free/retired lists.
    void drain_deferred(SlotServices&);
    // Storage discard substep of 011ea17c hard reset. Object destruction/index
    // cleanup belongs to its caller; does not advance generations or release refs.
    void discard_storage();
    // 011e66cc / 011e66f0 / 011e6740.
    bool set_object(Handle, std::uint32_t);
    bool set_mode(Handle, int);
    std::uint32_t mode(Handle);
    // 011e6778 / 011e67b8 / 011e67dc / 011e681c. Neutral bit names retained.
    bool set_bit28(Handle, int);
    bool bit28(Handle);
    bool set_lazy(Handle, int);
    bool lazy(Handle);
    StoreView view();
    const std::vector<Slot32>& slots() const { return slots_; }
    Slot32& slot(std::uint32_t index) { return slots_.at(index); }
    std::vector<std::uint32_t> list(std::uint32_t anchor) const;
};
}
