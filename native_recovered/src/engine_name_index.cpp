#include "engine_name_index.hpp"
namespace pvz2_recovered::engine {
StoreView* RegistryBanks::remove(std::uint32_t type) {
    auto& bank = (type & 0x2000U) ? view_.primary : view_.secondary;
    const auto index = (type & 0x2000U) ? type & ~0x2000U : type;
    if (index >= bank.size()) return nullptr;
    auto* old = bank[index]; bank[index] = nullptr; return old;
}
bool bind_object_name(StoreView store, ObjectNameIndex& names, std::uint32_t name, Handle handle) {
    names.erase(name);
    if (!handle.low && !handle.high) return true;
    const auto* slot = lookup_slot(store.type, store.slots, store.capacity, handle);
    if (!slot) return false;
    names.put(name, {slot->unknown14[0],slot->unknown14[1],slot->unknown14[2]});
    return true;
}
StoreView* RegistryBanks::ensure(std::uint32_t type, std::uint32_t parameter, StoreFactory& factory) {
    const bool primary = (type & 0x2000U) != 0;
    auto& bank = primary ? view_.primary : view_.secondary;
    auto& capacity = primary ? primary_capacity_ : secondary_capacity_;
    const auto index = primary ? type & ~0x2000U : type;
    if (index < bank.size() && bank[index]) return bank[index];
    if (index >= bank.size()) {
        if (index > 0x3fffffefU) throw std::length_error("registry bank size");
        const auto required = index + 0x10U;
        if (required > capacity) { bank.reserve(required); capacity = required; }
        bank.resize(required, nullptr);
    }
    auto* store = factory.construct(type, parameter);
    if (!store) throw std::logic_error("store constructor returned null");
    bank[index] = store;
    for (auto offset : {0x34U,0x44U,0x54U,0x64U}) factory.install_forwarder(*store, offset);
    return store;
}
}
