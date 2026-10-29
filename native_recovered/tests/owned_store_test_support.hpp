#pragma once
#include "engine_store.hpp"
#include <stdexcept>
#include <string>
namespace owned_store_test {
using namespace pvz2_recovered::engine;
inline void append(std::vector<std::uint32_t>& out,const std::vector<std::uint32_t>& part) {
    out.push_back(static_cast<std::uint32_t>(part.size())); out.insert(out.end(),part.begin(),part.end());
}
inline void compare(const std::vector<std::uint32_t>& actual,const std::vector<std::uint32_t>& expected,const char* what) {
    if (actual.size()!=expected.size()) throw std::runtime_error(std::string(what)+" length differs from ARM: "+std::to_string(actual.size())+" vs "+std::to_string(expected.size()));
    for (std::size_t i=0;i<actual.size();++i) if (actual[i]!=expected[i]) throw std::runtime_error(std::string(what)+" field "+std::to_string(i)+": actual="+std::to_string(actual[i])+" ARM="+std::to_string(expected[i]));
}
struct Services final : RegistryServices {
    OwnedRegistry* registry=nullptr;
    std::vector<std::uint32_t> events;
    std::size_t callback_count(std::uint32_t offset) override { return offset==0x34 || offset==0x44 ? 1 : 0; }
    void callback(std::uint32_t offset,std::size_t i,const OwnedStore& store) override {
        if (i) throw std::runtime_error("unexpected callback index");
        const auto* alias=registry->type_names().find(store.name_id());
        const auto& slots=store.slots();
        events.insert(events.end(),{0,offset,store.serial(),store.reserved_slots(),static_cast<std::uint32_t>(slots.slots().size()),
            slots.counts.live,slots.counts.free,slots.counts.deferred,slots.counts.retired,
            static_cast<std::uint32_t>(store.descriptors().size()),static_cast<std::uint32_t>(store.names().size()),
            alias?1U:0U,alias?*alias:0U,find_store(registry->banks().view(),store.type())?1U:0U});
    }
    void destroy_object(std::uint32_t object) override {
        for (const auto& store:registry->stores()) if (store) {
            const auto& slots=store->slots();
            for (std::size_t i=0;i<slots.slots().size();++i) {
                const auto& slot=slots.slots()[i];
                if (slot.object_address==object) {
                    events.insert(events.end(),{1,object,store->serial(),static_cast<std::uint32_t>(i),slot.generation,slot.flags,slot.unknown14[0],
                        slots.counts.live,slots.counts.deferred,static_cast<std::uint32_t>(store->descriptors().size()),static_cast<std::uint32_t>(store->names().size())});
                    return;
                }
            }
        }
        throw std::runtime_error("destroyed object has no owned slot");
    }
};
inline std::uint32_t serial(const OwnedRegistry& registry,const StoreView* value) {
    if (!value) return 0;
    for (const auto& store:registry.stores()) if (store && &store->view()==value) return store->serial();
    throw std::runtime_error("unknown store view");
}
inline std::vector<std::uint32_t> slot_state(const SlotPool& slots) {
    std::vector<std::uint32_t> out{static_cast<std::uint32_t>(slots.slots().size()),slots.counts.free,slots.counts.live,slots.counts.deferred,slots.counts.retired};
    for (unsigned i=0;i<4;++i) {
        const auto anchor=SlotPool::free_list+i;const auto list=slots.list(anchor);
        out.insert(out.end(),{list.empty()?anchor:list.front(),list.empty()?anchor:list.back()});
    }
    for (const auto& slot:slots.slots()) {
        for (auto word:slot.unknown00) out.push_back(word);
        out.insert(out.end(),{slot.object_address,slot.generation,slot.flags});
        for (auto word:slot.unknown14) out.push_back(word);
    }
    return out;
}
inline std::vector<std::uint32_t> snapshot(const OwnedRegistry& registry,const InternPool& strings) {
    std::vector<std::uint32_t> out,bank;
    const auto banks=registry.banks().view();
    bank.insert(bank.end(),{static_cast<std::uint32_t>(banks.primary.size()),registry.banks().primary_capacity()});
    for (const auto* p:banks.primary) bank.push_back(serial(registry,p));
    bank.insert(bank.end(),{static_cast<std::uint32_t>(banks.secondary.size()),registry.banks().secondary_capacity()});
    for (const auto* p:banks.secondary) bank.push_back(serial(registry,p));
    append(out,bank);append(out,registry.type_names().normalized_state());append(out,strings.normalized_state());
    out.push_back(static_cast<std::uint32_t>(registry.stores().size()));
    for (const auto& store:registry.stores()) {
        out.push_back(store?1U:0U);if (!store) continue;
        std::vector<std::uint32_t> data{store->type(),store->reserved_slots(),store->name_id(),store->fixed_content(),store->system_byte(),static_cast<std::uint32_t>(store->display_name().size())};
        for (unsigned char b:store->display_name()) data.push_back(b);
        append(data,slot_state(store->slots()));append(data,store->descriptors().normalized_state());append(data,store->names().normalized_state());
        for (auto offset:{0x34U,0x44U,0x54U,0x64U}) data.push_back(static_cast<std::uint32_t>(std::count(store->forwarders().begin(),store->forwarders().end(),offset)));
        append(out,data);
    }
    return out;
}
}
