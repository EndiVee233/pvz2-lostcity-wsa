#include "engine_rton_writer.hpp"
#include "owned_store_test_support.hpp"
#include <algorithm>
#include <iostream>
using namespace pvz2_recovered::engine;
using namespace owned_store_test;
enum class Operation { varuint,integer,string,wide,metadata,package };
struct Config {std::uint32_t type,reserve;bool null_name;std::vector<std::uint32_t> name,display;std::uint32_t fixed,system;};
struct Step {Operation op;std::uint32_t number;std::vector<std::uint32_t> key,value;bool cached;std::vector<std::uint32_t> state;};
struct Scenario {const char* label;bool metadata;Config config;std::vector<std::uint32_t> path,initial;std::vector<Step> steps;};
#include "rton_metadata_fixtures.inc"
std::string as_bytes(const std::vector<std::uint32_t>& data) {std::string text;for(auto c:data)text.push_back(static_cast<char>(c));return text;}
std::u32string as_wide(const std::vector<std::uint32_t>& data) {std::u32string text;for(auto c:data)text.push_back(static_cast<char32_t>(c));return text;}
std::vector<std::uint32_t> writer_state(const RtonWriter& writer) {
    std::vector<std::uint32_t> out{static_cast<std::uint32_t>(writer.bytes().size())};
    for (auto b:writer.bytes()) out.push_back(b);
    auto cache=writer.string_cache();std::sort(cache.begin(),cache.end(),[](const auto& a,const auto& b){return a.first<b.first;});
    out.push_back(static_cast<std::uint32_t>(cache.size()));out.push_back(static_cast<std::uint32_t>(cache.size()));
    for(const auto& item:cache) {out.push_back(static_cast<std::uint32_t>(item.first.size()));for(unsigned char b:item.first)out.push_back(b);out.push_back(item.second);}
    return out;
}
int main() {
    unsigned checks=0,number=0;const char* label="initialization";
    try {
        for(const auto& sc:scenarios) {
            label=sc.label;number=0;InternPool strings;Services services;OwnedRegistry registry(strings,services,0x87654321U);services.registry=&registry;
            OwnedStore* store=nullptr;std::uint32_t path_id=0;
            if(sc.metadata) {
                StoreConfig config;config.reserved_slots=sc.config.reserve;
                if(!sc.config.null_name)config.name=strings.acquire(as_wide(sc.config.name).c_str());
                config.display_name=as_bytes(sc.config.display);config.fixed_content=static_cast<std::uint8_t>(sc.config.fixed);config.system_byte=static_cast<std::uint8_t>(sc.config.system);
                store=&registry.ensure(sc.config.type,&config);path_id=strings.acquire(as_wide(sc.path).c_str()).id;
            }
            RtonWriter writer;compare(writer_state(writer),sc.initial,"initial writer");
            for(const auto& s:sc.steps) {
                const auto key=as_bytes(s.key);
                switch(s.op) {
                case Operation::varuint:writer.varuint(s.number);break;
                case Operation::integer:writer.integer(key,s.number);break;
                case Operation::string:writer.string(key,as_bytes(s.value),s.cached);break;
                case Operation::wide:writer.wide_string(key,as_wide(s.value));break;
                case Operation::package:store->set_package(s.number?path_id:0);break;
                case Operation::metadata: {
                    const auto before=snapshot(registry,strings);writer.store_metadata(*store,strings);compare(snapshot(registry,strings),before,"metadata owner unchanged");break;
                }
                }
                compare(writer_state(writer),s.state,"RTON bytes/cache");++checks;++number;
            }
        }
        std::cout<<"PASS "<<checks<<" RTON metadata ARM byte/cache checkpoints\n";
    } catch(const std::exception& error) {std::cerr<<label<<" step "<<number<<": "<<error.what()<<'\n';return 1;}
}
