#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
namespace pvz2_recovered::engine {
struct Handle { std::uint32_t low = 0, high = 0; };
struct Slot32 {
    std::uint32_t unknown00[2];
    std::uint32_t object_address;
    std::uint32_t generation;
    std::uint32_t flags;
    std::uint32_t unknown14[3];
};
static_assert(sizeof(Slot32) == 0x20);
static_assert(offsetof(Slot32, object_address) == 8);
static_assert(offsetof(Slot32, generation) == 12);
static_assert(offsetof(Slot32, flags) == 16);
struct DecodedHandle { std::uint32_t store, index, generation; };
DecodedHandle decode(Handle);
// 011e62c8. Returned slot remains owned by the caller's backing array.
Slot32* lookup_slot(std::uint32_t store_type, Slot32* slots, std::size_t capacity, Handle);
// 011e7538. Tables contain ARM32 addresses, not host pointers.
std::uint32_t registry_store(const std::vector<std::uint32_t>& primary,
                             const std::vector<std::uint32_t>& secondary,
                             std::uint32_t encoded_type);
struct InternReferences {
    virtual ~InternReferences() = default;
    virtual void retain(std::uint32_t) = 0;
    virtual void release(std::uint32_t) = 0;
};
// 001e9bb4. Symbolic handles own two intern-table references; direct handles do not.
void assign_handle(Handle&, Handle, InternReferences&);
struct LazyResolvers {
    virtual ~LazyResolvers() = default;
    virtual std::size_t count() = 0;
    virtual void invoke(std::size_t, Handle) = 0;
};
// 011e6620. Call every registered resolver even if the first supplies an object.
std::uint32_t resolve_object(std::uint32_t store_type, Slot32*, std::size_t capacity,
                              Handle, LazyResolvers&);
}
