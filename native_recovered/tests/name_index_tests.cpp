#include "engine_name_index.hpp"
#include "engine_intern.hpp"
#include "engine_slot_index.hpp"
#include "engine_slots.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace pvz2_recovered::engine;
enum class Kind { index, binding, factory };
enum class Operation { put, insert, find, erase, clear, bind, lookup, canonical, resolve, drop_name, ensure };
struct Step {
    Operation op;
    std::uint32_t key, a, b;
    Descriptor32 descriptor;
    bool has_hint;
    std::uint32_t hint;
    std::vector<std::uint32_t> result, events, state;
};
struct Scenario { const char* label; Kind kind; bool object; std::vector<std::uint32_t> initial; std::vector<Step> steps; };
#include "name_index_fixtures.inc"
unsigned checks = 0, number = 0;
void compare(const std::vector<std::uint32_t>& actual, const std::vector<std::uint32_t>& expected, const char* what) {
    if (actual.size() != expected.size()) throw std::runtime_error(std::string(what)+" size differs from ARM");
    for (std::size_t i=0; i<actual.size(); ++i) if (actual[i]!=expected[i])
        throw std::runtime_error(std::string(what)+" field "+std::to_string(i)+" differs: actual="+std::to_string(actual[i])+" ARM="+std::to_string(expected[i]));
}
struct MockPool final : InternStrings {
    std::vector<std::uint32_t> events;
    void retain(std::uint32_t id) override { events.insert(events.end(),{0,id}); }
    void release(std::uint32_t id) override { events.insert(events.end(),{2,id}); }
    std::uint32_t text_address(std::uint32_t id) override { events.insert(events.end(),{1,id}); return 0x16c5e40; }
};
template<bool Object> void raw_scenario(const Scenario& sc) {
    MockPool pool;
    NameIndex<Object> index(&pool);
    compare(index.normalized_state(),sc.initial,"initial name tree");
    for (const auto& s:sc.steps) {
        typename NameIndex<Object>::Value value{};
        if constexpr (Object) value=s.descriptor; else value=s.a;
        pool.events.clear(); std::vector<std::uint32_t> result;
        switch (s.op) {
        case Operation::put: index.put(s.key,value); break;
        case Operation::insert: result={index.insert_unique(s.key,value,s.has_hint?&s.hint:nullptr)}; break;
        case Operation::erase: result={index.erase(s.key)}; break;
        case Operation::clear: index.clear(); break;
        case Operation::find: {
            const auto* found=index.find(s.key); result={found?1U:0U};
            if (found) {
                if constexpr (Object) result.insert(result.end(),found->begin(),found->end());
                else result.push_back(*found);
            }
            break;
        }
        default: throw std::runtime_error("unexpected raw name operation");
        }
        index.validate(); compare(result,s.result,"result"); compare(pool.events,s.events,"intern call order");
        compare(index.normalized_state(),s.state,"name tree"); ++checks; ++number;
    }
}
std::vector<std::uint32_t> binding_state(const ObjectNameIndex& index,const InternPool& pool) {
    auto tree=index.normalized_state(); std::vector<std::uint32_t> result{static_cast<std::uint32_t>(tree.size())};
    result.insert(result.end(),tree.begin(),tree.end()); auto state=pool.normalized_state();
    result.insert(result.end(),state.begin(),state.end()); return result;
}
void binding_scenario(const Scenario& sc) {
    InternPool pool;
    for (unsigned i=1;i<=8;++i) {
        std::u32string name=U"名称-"; name.push_back(static_cast<char32_t>(U'0'+i));
        if (pool.acquire(name.c_str()).id!=i) throw std::runtime_error("binding name seed");
    }
    ObjectNameIndex names(&pool);
    TypeNameIndex types; types.put(1,2);
    DescriptorIndex descriptors;
    Slot32 slots[3]{};
    const Descriptor32 keys[]={{4,5,6},{7,8,9},{0,0,0}};
    for (unsigned i=0;i<3;++i) {
        slots[i].generation=i+1; slots[i].flags=1; slots[i].object_address=0x12345678U+i;
        for (unsigned k=0;k<3;++k) slots[i].unknown14[k]=keys[i][k];
        descriptors.put(keys[i],{((i+1)<<16)|i,2U<<17});
    }
    compare(binding_state(names,pool),sc.initial,"initial binding state");
    for (const auto& s:sc.steps) {
        auto store=names.attach(descriptors.attach({2,slots,3,nullptr,nullptr,nullptr}));
        const auto registry=types.attach({{}, {nullptr,nullptr,&store}, nullptr});
        std::vector<std::uint32_t> result;
        switch (s.op) {
        case Operation::bind: result={bind_object_name(store,names,s.key,{s.a,s.b})}; break;
        case Operation::lookup: {
            const auto h=handle_from_name(store,s.key,pool); result={h.low,h.high}; break;
        }
        case Operation::canonical: {
            const auto h=canonical_handle(registry,{0x80000000U|s.key,0x80000000U},pool); result={h.low,h.high}; break;
        }
        case Operation::resolve: result={resolve_registered_object(registry,{0x80000000U|s.key,0x80000000U},pool)}; break;
        case Operation::drop_name: pool.release(s.key); break;
        case Operation::clear: names.clear(); break;
        default: throw std::runtime_error("unexpected binding operation");
        }
        names.validate(); types.validate(); pool.validate();
        compare(result,s.result,"binding result"); compare({},s.events,"binding external events");
        compare(binding_state(names,pool),s.state,"binding tree/pool"); ++checks; ++number;
    }
}
struct Factory final : StoreFactory {
    RegistryBanks& banks;
    std::vector<std::unique_ptr<StoreView>> stores;
    std::vector<std::uint32_t> events;
    explicit Factory(RegistryBanks& b):banks(b) {}
    std::uint32_t id(const StoreView* value) const {
        if (!value) return 0;
        for (std::size_t i=0;i<stores.size();++i) if (stores[i].get()==value) return static_cast<std::uint32_t>(i+1);
        throw std::runtime_error("unknown constructed store");
    }
    StoreView* construct(std::uint32_t type,std::uint32_t parameter) override {
        const auto view=banks.view(); const auto serial=static_cast<std::uint32_t>(stores.size()+1);
        events.insert(events.end(),{0,serial,type,parameter,find_store(view,type)?1U:0U});
        auto store=std::make_unique<StoreView>(); store->type=type; auto* p=store.get(); stores.push_back(std::move(store)); return p;
    }
    void install_forwarder(StoreView& store,std::uint32_t offset) override {
        events.insert(events.end(),{1,id(&store),offset,find_store(banks.view(),store.type)==&store?1U:0U});
    }
};
std::vector<std::uint32_t> factory_state(const RegistryBanks& banks,const Factory& factory) {
    const auto view=banks.view();
    std::vector<std::uint32_t> out{static_cast<std::uint32_t>(view.primary.size()),banks.primary_capacity()};
    for (const auto* p:view.primary) out.push_back(factory.id(p));
    out.insert(out.end(),{static_cast<std::uint32_t>(view.secondary.size()),banks.secondary_capacity()});
    for (const auto* p:view.secondary) out.push_back(factory.id(p));
    return out;
}
void factory_scenario(const Scenario& sc) {
    RegistryBanks banks; Factory factory(banks);
    compare(factory_state(banks,factory),sc.initial,"initial banks");
    for (const auto& s:sc.steps) {
        factory.events.clear();
        const auto* p=banks.ensure(s.key,s.a,factory);
        compare({factory.id(p)},s.result,"factory result"); compare(factory.events,s.events,"factory event order");
        compare(factory_state(banks,factory),s.state,"registry banks"); ++checks; ++number;
    }
}
unsigned integration_checks() {
    unsigned count=0;
    const auto require=[&](bool ok,const char* message) { if (!ok) throw std::runtime_error(message); ++count; };
    InternPool strings;
    const auto type_name=strings.acquire(U"$植物");
    const auto object_name=strings.acquire(U"豌豆射手");
    SlotPool slots(2);
    DescriptorIndex descriptors;
    ObjectNameIndex names(&strings);
    TypeNameIndex types;
    struct Services final : SlotServices {
        DescriptorIndex& index;
        std::vector<std::uint32_t> destroyed;
        explicit Services(DescriptorIndex& i):index(i) {}
        std::size_t callback_count(SlotEvent) override { return 0; }
        void callback(SlotEvent,std::size_t,Handle) override { throw std::runtime_error("unexpected integration callback"); }
        void put_descriptor(const Descriptor32& d,Handle h) override { index.put(d,h); }
        void erase_descriptor(const Descriptor32& d) override { index.erase(d); }
        void destroy_object(std::uint32_t object) override { destroyed.push_back(object); }
    } services(descriptors);
    StoreView store=slots.view();
    struct ViewFactory final : StoreFactory {
        StoreView& store;
        std::vector<std::uint32_t> offsets;
        explicit ViewFactory(StoreView& v):store(v) {}
        StoreView* construct(std::uint32_t,std::uint32_t) override { return &store; }
        void install_forwarder(StoreView&,std::uint32_t offset) override { offsets.push_back(offset); }
    } factory(store);
    RegistryBanks banks;
    require(banks.ensure(2,0,factory)==&store && factory.offsets==std::vector<std::uint32_t>{0x34,0x44,0x54,0x64},"dynamic bank setup");
    types.put(type_name.id,2);
    const Descriptor32 descriptor{17,18,19};
    const auto object=slots.create(0x12345678U,0,0,&descriptor,1,services);
    const auto refresh=[&]() { store=names.attach(descriptors.attach(slots.view())); return types.attach(banks.view()); };
    (void)refresh();
    require(bind_object_name(store,names,object_name.id,object),"dynamic name binding");
    require(strings.reference_count(object_name.id)==2,"name index ownership");
    strings.release(object_name.id);
    Handle symbolic{};
    assign_handle(symbolic,{object_name.id|((type_name.id&1U)<<31),0x80000000U|(type_name.id>>1)},strings);
    require(resolve_registered_object(refresh(),symbolic,strings)==0x12345678U,"dynamic symbolic object lookup");
    slots.grow(600);
    require(resolve_registered_object(refresh(),symbolic,strings)==0x12345678U,"dynamic lookup after growth");
    require(slots.release(object,services) && services.destroyed==std::vector<std::uint32_t>{0x12345678U} && !slots.counts.live,"dynamic object release");
    require(resolve_registered_object(refresh(),symbolic,strings)==0,"stale symbolic target");
    require(names.size()==1 && strings.reference_count(object_name.id)==2,"alias remains until explicitly removed");
    require(bind_object_name(store,names,object_name.id,{}) && !names.size() && strings.reference_count(object_name.id)==1,"dynamic alias removal");
    assign_handle(symbolic,{},strings);
    require(strings.find_id(U"豌豆射手")==0,"handle releases final object-name reference");
    require(types.erase(type_name.id) && strings.reference_count(type_name.id)==1,"type index does not own name references");
    strings.release(type_name.id);
    require(strings.find_id(U"$植物")==0 && !types.size() && !names.size() && !descriptors.size(),"dynamic index/name cleanup");
    strings.validate(); names.validate(); types.validate(); descriptors.validate();
    return count;
}
int main() {
    const char* label="initialization";
    try {
        for (const auto& sc:scenarios) {
            label=sc.label; number=0;
            switch (sc.kind) {
            case Kind::index: if (sc.object) raw_scenario<true>(sc); else raw_scenario<false>(sc); break;
            case Kind::binding: binding_scenario(sc); break;
            case Kind::factory: factory_scenario(sc); break;
            }
        }
        std::cout<<"PASS "<<checks<<" name-index/binding/bank ARM full-state checkpoints\n";
        label="dynamic registry/name/slot integration"; number=0;
        std::cout<<"PASS "<<integration_checks()<<" dynamic registry integration checks\n";
    } catch (const std::exception& e) { std::cerr<<label<<'/'<<number<<": "<<e.what()<<'\n'; return 1; }
}
