#include "engine_store.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace pvz2_recovered::engine;
enum class Operation { ensure,remove,reset,drop_config,create,create_default,retain,release,bind,resolve };
struct Config {
    std::uint32_t reserve; bool null_name;
    std::vector<std::uint32_t> name,display;
    std::uint32_t fixed,system;
};
struct Step {
    Operation op;
    std::uint32_t type,a,b,c,h,name;
    Descriptor32 descriptor;
    std::vector<std::uint32_t> result,events,state;
};
struct Scenario { const char* label; std::vector<Config> configs; std::vector<std::uint32_t> initial; std::vector<Step> steps; };
#include "owned_store_fixtures.inc"
#include "owned_store_test_support.hpp"
using namespace owned_store_test;
int main() {
    unsigned checks=0,number=0;const char* label="initialization";
    try {
        for (const auto& sc:scenarios) {
            label=sc.label;number=0;
            InternPool strings;Services services;OwnedRegistry registry(strings,services,0x87654321U);services.registry=&registry;
            std::array<std::uint32_t,3> aliases{};
            for (unsigned i=0;i<3;++i) { std::u32string text=U"别名-";text.push_back(static_cast<char32_t>(U'0'+i));aliases[i]=strings.acquire(text.c_str()).id; }
            std::vector<StoreConfig> configs;
            for (const auto& input:sc.configs) {
                StoreConfig config;config.reserved_slots=input.reserve;
                if (!input.null_name) { std::u32string text;for (auto c:input.name) text.push_back(static_cast<char32_t>(c));config.name=strings.acquire(text.c_str()); }
                for (auto b:input.display) config.display_name.push_back(static_cast<char>(b));
                config.fixed_content=static_cast<std::uint8_t>(input.fixed);config.system_byte=static_cast<std::uint8_t>(input.system);configs.push_back(config);
            }
            std::array<Handle,32> handles{};
            compare(snapshot(registry,strings),sc.initial,"initial owner state");
            for (const auto& s:sc.steps) {
                services.events.clear();std::vector<std::uint32_t> result;
                auto* store=registry.find(s.type);
                switch (s.op) {
                case Operation::ensure: result={registry.ensure(s.type,s.a==0xffffffffU?nullptr:&configs.at(s.a)).serial()};break;
                case Operation::remove: result={registry.remove(s.type)};break;
                case Operation::drop_config: strings.release(configs.at(s.a).name.id);break;
                case Operation::reset: store->reset(s.a!=0);break;
                case Operation::create: {
                    const auto h=store->create(s.a?0x600a000U+s.a*32:0,static_cast<int>(s.b),static_cast<std::uint8_t>(s.c),&s.descriptor);
                    handles[s.h]=h;result={h.low,h.high};break;
                }
                case Operation::create_default: {
                    const auto h=store->create(s.a?0x600a000U+s.a*32:0,static_cast<int>(s.b),static_cast<std::uint8_t>(s.c));
                    handles[s.h]=h;result={h.low,h.high};break;
                }
                case Operation::retain: store->retain(handles[s.h]);break;
                case Operation::release: result={store->release(handles[s.h])};break;
                case Operation::bind: result={store->bind_name(aliases[s.name],handles[s.h])};break;
                case Operation::resolve: {
                    const auto name=store->name_id();result={registry.resolve({aliases[s.name]|((name&1U)<<31),0x80000000U|(name>>1)})};break;
                }
                }
                strings.validate();registry.type_names().validate();
                for (const auto& item:registry.stores()) if (item) { item->names().validate();item->descriptors().validate(); }
                compare(result,s.result,"owner result");compare(services.events,s.events,"owner callback/destruction order");compare(snapshot(registry,strings),s.state,"owner state");
                ++checks;++number;
            }
        }
        std::cout<<"PASS "<<checks<<" real-constructor/store-lifecycle ARM full-state checkpoints\n";
    } catch (const std::exception& e) { std::cerr<<label<<'/'<<number<<": "<<e.what()<<'\n';return 1; }
}
