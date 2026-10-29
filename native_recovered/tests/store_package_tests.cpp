#include "engine_package_paths.hpp"
#include "owned_store_test_support.hpp"
#include <iostream>
using namespace pvz2_recovered::engine;
using namespace owned_store_test;
enum class Operation { convert,normalize,filename,ensure,remove,set_package,effective,query_alias,query_effective,release_path,reset,create,bind,resolve_package };
struct Config { std::uint32_t reserve;bool null_name;std::vector<std::uint32_t> name,display;std::uint32_t fixed,system; };
struct Step {
    Operation op;std::uint32_t type,a,b,c,h,name;Descriptor32 descriptor;
    std::vector<std::uint32_t> result,events,state;
};
struct Scenario {
    const char* label;bool path_only;std::vector<std::vector<std::uint32_t>> paths;
    std::vector<Config> configs;std::vector<std::uint32_t> initial;std::vector<Step> steps;
};
#include "store_package_fixtures.inc"
void append_bytes(std::vector<std::uint32_t>& out,std::string_view bytes) {
    out.push_back(static_cast<std::uint32_t>(bytes.size()));for (unsigned char c:bytes) out.push_back(c);
}
void append_wide(std::vector<std::uint32_t>& out,std::u32string_view text) {
    out.push_back(static_cast<std::uint32_t>(text.size()));for (auto c:text) out.push_back(static_cast<std::uint32_t>(c));
}
std::vector<std::uint32_t> package_snapshot(const OwnedRegistry& registry,const InternPool& strings) {
    auto out=snapshot(registry,strings);
    for (const auto& store:registry.stores()) {
        out.push_back(store?1U:0U);if (!store) continue;
        out.push_back(store->package_id());append_wide(out,store->package_filename());out.push_back(store->effective_name_id());
    }
    return out;
}
int main() {
    unsigned checks=0,number=0;const char* label="initialization";
    try {
        for (const auto& sc:scenarios) {
            label=sc.label;number=0;
            std::vector<std::u32string> paths;
            for (const auto& input:sc.paths) {std::u32string text;for (auto c:input) text.push_back(static_cast<char32_t>(c));paths.push_back(text);}
            InternPool strings;Services services;OwnedRegistry registry(strings,services,0x87654321U);services.registry=&registry;
            std::array<std::uint32_t,3> aliases{};
            std::vector<StoreConfig> configs;std::vector<InternValue> inputs;
            if (!sc.path_only) {
                for (unsigned i=0;i<3;++i) {std::u32string text=U"别名-";text.push_back(static_cast<char32_t>(U'0'+i));aliases[i]=strings.acquire(text.c_str()).id;}
                for (const auto& input:sc.configs) {
                    StoreConfig config;config.reserved_slots=input.reserve;
                    if (!input.null_name) {std::u32string text;for (auto c:input.name) text.push_back(static_cast<char32_t>(c));config.name=strings.acquire(text.c_str());}
                    for (auto b:input.display) config.display_name.push_back(static_cast<char>(b));
                    config.fixed_content=static_cast<std::uint8_t>(input.fixed);config.system_byte=static_cast<std::uint8_t>(input.system);configs.push_back(config);
                }
                for (const auto& path:paths) inputs.push_back(strings.acquire(path.c_str()));
                compare(package_snapshot(registry,strings),sc.initial,"initial package owner");
            }
            std::array<Handle,32> handles{};
            for (const auto& s:sc.steps) {
                services.events.clear();std::vector<std::uint32_t> result;
                if (sc.path_only) {
                    const auto raw=narrow_low_bytes(paths.at(0));
                    switch (s.op) {
                    case Operation::convert: append_bytes(result,raw);append_wide(result,widen_bytes(raw));break;
                    case Operation::normalize: append_bytes(result,normalize_package_path(raw));break;
                    case Operation::filename: append_bytes(result,package_resource_filename(raw));break;
                    default:throw std::runtime_error("unexpected byte path operation");
                    }
                } else {
                    auto* store=registry.find(s.type);
                    switch (s.op) {
                    case Operation::ensure:result={registry.ensure(s.type,s.a==0xffffffffU?nullptr:&configs.at(s.a)).serial()};break;
                    case Operation::set_package:store->set_package(s.a==0xffffffffU?0:inputs.at(s.a).id);break;
                    case Operation::effective:result={store->effective_name_id()};break;
                    case Operation::query_alias:
                    case Operation::query_effective: {
                        const auto id=s.op==Operation::query_alias?store->package_id():store->effective_name_id();
                        result={serial(registry,find_named_store(registry.view(),id))};break;
                    }
                    case Operation::release_path:strings.release(inputs.at(s.a).id);break;
                    case Operation::remove:result={registry.remove(s.type)};break;
                    case Operation::reset:store->reset(s.a!=0);break;
                    case Operation::create: {
                        const auto h=store->create(s.a?0x600a000U+s.a*32:0,static_cast<int>(s.b),static_cast<std::uint8_t>(s.c),&s.descriptor);handles[s.h]=h;result={h.low,h.high};break;
                    }
                    case Operation::bind:result={store->bind_name(aliases[s.name],handles[s.h])};break;
                    case Operation::resolve_package: {
                        const auto id=store->effective_name_id();result={registry.resolve({aliases[s.name]|((id&1U)<<31),0x80000000U|(id>>1)})};break;
                    }
                    default:throw std::runtime_error("unexpected package owner operation");
                    }
                }
                strings.validate();registry.type_names().validate();
                for (const auto& item:registry.stores()) if (item) {item->names().validate();item->descriptors().validate();}
                compare(result,s.result,"package/path result");compare(services.events,s.events,"package owner event order");
                compare(sc.path_only?std::vector<std::uint32_t>{}:package_snapshot(registry,strings),s.state,"package owner state");
                ++checks;++number;
            }
        }
        std::cout<<"PASS "<<checks<<" package/path/nonempty-teardown ARM checkpoints\n";
    } catch (const std::exception& e) {std::cerr<<label<<'/'<<number<<": "<<e.what()<<'\n';return 1;}
}
