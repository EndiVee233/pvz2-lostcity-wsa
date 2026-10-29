#include "engine_registry.hpp"
#include <stdexcept>

namespace pvz2_recovered::engine {
StoreView* find_store(const RegistryView& registry, std::uint32_t type) {
    const bool primary = (type & 0x2000U) != 0;
    const auto& table = primary ? registry.primary : registry.secondary;
    if (primary) type &= ~0x2000U;
    return type < table.size() ? table[type] : nullptr;
}
StoreView* find_named_store(const RegistryView& registry, std::uint32_t name) {
    const auto* node = registry.names;
    const StoreNameNode* candidate = nullptr;
    while (node) {
        if (node->name < name) node = node->right;
        else { candidate = node; node = node->left; }
    }
    return candidate && candidate->name == name
        ? find_store(registry, candidate->encoded_type) : nullptr;
}
Descriptor32 describe_handle(const StoreView& store, Handle h) {
    auto* slot = lookup_slot(store.type, store.slots, store.capacity, h);
    if (!slot) return {};
    return {slot->unknown14[0], slot->unknown14[1], slot->unknown14[2]};
}
Handle handle_from_descriptor(const StoreView& store, const Descriptor32& key,
                              InternReferences& pool) {
    const auto* node = store.descriptors;
    const DescriptorNode* candidate = nullptr;
    while (node) {
        if (node->key < key) node = node->right;
        else { candidate = node; node = node->left; }
    }
    if (!candidate || candidate->key != key) return {};
    Handle temporary{};
    assign_handle(temporary, candidate->handle, pool);
    auto* slot = lookup_slot(store.type, store.slots, store.capacity, temporary);
    // The ARM routine dereferences this pointer without a null check. Keep the
    // live-index precondition explicit instead of claiming stale-index recovery.
    if (!slot) throw std::logic_error("descriptor index contains an invalid handle");
    Handle result{};
    if (describe_handle(store, temporary) == key) {
        const auto index = static_cast<std::uint32_t>(slot - store.slots);
        const auto generation = slot->generation;
        Handle packed;
        if (index < 0x10000U)
            packed = {index | (generation << 16), (store.type << 17) | (generation >> 16)};
        else
            packed = {index | (generation << 24), (store.type << 17) | (generation >> 8) | 0x10000U};
        assign_handle(result, packed, pool);
    }
    assign_handle(temporary, {}, pool);
    return result;
}
Handle handle_from_name(const StoreView& store, std::uint32_t name, InternReferences& pool) {
    const auto* node = store.names;
    const ObjectNameNode* candidate = nullptr;
    while (node) {
        if (node->name < name) node = node->right;
        else { candidate = node; node = node->left; }
    }
    return candidate && candidate->name == name
        ? handle_from_descriptor(store, candidate->descriptor, pool) : Handle{};
}
Handle canonical_handle(const RegistryView& registry, Handle h, InternStrings& pool) {
    if (!(h.high & 0x80000000U)) {
        Handle result{};
        assign_handle(result, h, pool);
        return result;
    }
    const auto store_name = (h.low >> 31) | ((h.high & 0x3fffffffU) << 1);
    pool.retain(store_name);
    (void)pool.text_address(store_name);
    const auto* store = find_named_store(registry, store_name);
    Handle result{};
    if (store) {
        const auto object_name = h.low & 0x7fffffffU;
        pool.retain(object_name);
        (void)pool.text_address(object_name);
        result = handle_from_name(*store, object_name, pool);
        pool.release(object_name);
    }
    pool.release(store_name);
    return result;
}
std::uint32_t resolve_registered_object(const RegistryView& registry, Handle h, InternStrings& pool) {
    auto canonical = canonical_handle(registry, h, pool);
    std::uint32_t result = 0;
    if (canonical.low || canonical.high) {
        const auto* store = find_store(registry, decode(canonical).store);
        if (store) {
            auto* slot = lookup_slot(store->type, store->slots, store->capacity, canonical);
            if (slot && !slot->object_address && (slot->flags & 0x08000000U) && !store->resolvers)
                throw std::logic_error("lazy store requires a resolver list");
            if (store->resolvers)
                result = resolve_object(store->type, store->slots, store->capacity, canonical, *store->resolvers);
            else if (slot) result = slot->object_address;
        }
    }
    assign_handle(canonical, {}, pool);
    return result;
}
}
