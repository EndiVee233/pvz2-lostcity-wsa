#include "engine_handles.hpp"
namespace pvz2_recovered::engine {
DecodedHandle decode(Handle h) {
    const auto type = (h.high >> 17) & 0x3fffU;
    if (h.high & 0x10000U)
        return {type, h.low & 0xffffffU, ((h.low >> 24) | (h.high << 8)) & 0xffffffU};
    return {type, h.low & 0xffffU, (h.low >> 16) | (h.high << 16)};
}
Slot32* lookup_slot(std::uint32_t store_type, Slot32* slots, std::size_t capacity, Handle h) {
    auto d = decode(h);
    if (store_type != d.store || d.index >= capacity) return nullptr;
    auto* slot = slots + d.index;
    return slot->generation == d.generation ? slot : nullptr;
}
std::uint32_t registry_store(const std::vector<std::uint32_t>& primary,
                             const std::vector<std::uint32_t>& secondary,
                             std::uint32_t type) {
    const bool use_primary = (type & 0x2000U) != 0;
    const auto& table = use_primary ? primary : secondary;
    if (use_primary) type &= ~0x2000U;
    return type < table.size() ? table[type] : 0;
}
void assign_handle(Handle& destination, Handle source, InternReferences& pool) {
    const auto old = destination;
    if (source.high & 0x80000000U) {
        pool.retain((source.low >> 31) | ((source.high & 0x3fffffffU) << 1));
        pool.retain(source.low & 0x7fffffffU);
    }
    if (old.high & 0x80000000U) {
        pool.release((old.low >> 31) | ((old.high & 0x3fffffffU) << 1));
        pool.release(old.low & 0x7fffffffU);
    }
    destination = source;
}
std::uint32_t resolve_object(std::uint32_t type, Slot32* slots, std::size_t capacity,
                              Handle h, LazyResolvers& resolvers) {
    auto* slot = lookup_slot(type, slots, capacity, h);
    if (!slot) return 0;
    if (slot->object_address == 0 && (slot->flags & 0x08000000U)) {
        const auto count = resolvers.count();
        for (std::size_t i = 0; i < count; ++i) resolvers.invoke(i, h);
    }
    return slot->object_address;
}
}
