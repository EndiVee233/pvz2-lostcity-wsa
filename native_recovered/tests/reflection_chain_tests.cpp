#include "engine_reflection.hpp"
#include "owned_store_test_support.hpp"
#include <iostream>
using namespace pvz2_recovered::engine;
using owned_store_test::append;
void compare(const std::vector<std::uint32_t>& a,const std::vector<std::uint32_t>& b,const char* what) {
    for(std::size_t i=0;i<std::min(a.size(),b.size());++i)if(a[i]!=b[i])throw std::runtime_error(std::string(what)+" first difference at "+std::to_string(i)+": "+std::to_string(a[i])+" vs ARM "+std::to_string(b[i])+"; sizes "+std::to_string(a.size())+"/"+std::to_string(b.size()));
    if(a.size()!=b.size())throw std::runtime_error(std::string(what)+" sizes differ "+std::to_string(a.size())+"/"+std::to_string(b.size()));
}
enum class Operation {ensure,package,load,populate,lookup};
struct Step {Operation op;std::uint32_t type;std::vector<std::uint32_t> name,data;const char* label;std::vector<std::vector<std::uint32_t>> results,states;};
#include "reflection_chain_fixtures.inc"
std::vector<std::uint32_t> snapshot(ReflectionDataRuntime& runtime) {
    std::vector<std::uint32_t> out;const auto& types=runtime.classes().ordered();out.push_back(static_cast<std::uint32_t>(types.size()));
    for(const auto* cls:types) {
        out.push_back(static_cast<std::uint32_t>(cls->name.size()));for(unsigned char c:cls->name)out.push_back(c);
        const auto parent=std::find(types.begin(),types.end(),cls->parent);
        out.push_back(parent==types.end()?0U:static_cast<std::uint32_t>(parent-types.begin()+1));out.push_back(cls->factory?1U:0U);
    }
    const RuntimeClass* query[]{nullptr,types[0],types[1]};
    for(auto* a:query)for(auto* b:query)out.push_back(ClassDirectory::derives_from(a,b)?1U:0U);
    append(out,runtime.strings().normalized_state());
    for(auto type:{2U,3U}) {
        auto* store=runtime.registry().find(type);out.push_back(store?1U:0U);if(!store)continue;
        out.push_back(store->name_id());out.push_back(store->package_id());append(out,owned_store_test::slot_state(store->slots()));
        append(out,store->descriptors().normalized_state());append(out,store->names().normalized_state());
    }
    out.push_back(static_cast<std::uint32_t>(runtime.object_slots()));
    for(std::uint32_t i=1;i<=runtime.object_slots();++i) {
        const auto* object=runtime.object(i);out.push_back(object?1U:0U);if(!object)continue;
        out.insert(out.end(),{object->flag,object->ground_type,object->effect.low,object->effect.high,runtime.resolve(object->effect)});
    }
    return out;
}
int main() {
    unsigned checks=0;const char* label="initial state";
    try {
        ReflectionDataRuntime runtime;compare(snapshot(runtime),initial_state,"initial reflection state");
        std::map<std::uint32_t,ObjectLoadResult> loaded;
        for(const auto& s:steps) {
            label=s.label;std::u32string name;for(auto c:s.name)name.push_back(static_cast<char32_t>(c));
            std::vector<std::uint32_t> result;std::size_t stage=0;
            if(s.op==Operation::ensure)runtime.ensure_store(s.type,name.c_str());
            else if(s.op==Operation::package)runtime.set_package(s.type,name.c_str());
            else if(s.op==Operation::lookup) {
                const std::string narrow(name.begin(),name.end());const auto* cls=runtime.classes().find(narrow);const auto& types=runtime.classes().ordered();
                const auto it=std::find(types.begin(),types.end(),cls);result={it==types.end()?0U:static_cast<std::uint32_t>(it-types.begin()+1)};
            } else {
                std::vector<std::uint8_t> bytes;for(auto b:s.data)bytes.push_back(static_cast<std::uint8_t>(b));
                auto doc=normalize_rton(std::move(bytes),&runtime.strings());if(!doc.success)throw std::runtime_error("fixture normalization failed");IndexedRtonReader reader(std::move(doc));
                if(s.op==Operation::load) {
                    auto created=runtime.create_objects(reader,s.type);result={created.success?1U:0U};result.insert(result.end(),created.objects.begin(),created.objects.end());loaded[s.type]=created;
                    compare(result,s.results[stage],"factory result");
                    compare(snapshot(runtime),s.states[stage],"factory state");++stage;++checks;
                    if(!created.success)continue;
                }
                result={runtime.populate_objects(reader,s.type,loaded[s.type])?1U:0U};
            }
            compare(result,s.results[stage],"operation result");
            compare(snapshot(runtime),s.states[stage],"reflection state");++checks;
        }
        std::cout<<"PASS "<<checks<<" real reflection factory/property/reference ARM full-state checkpoints\n";
    }catch(const std::exception& e){std::cerr<<label<<": "<<e.what()<<'\n';return 1;}
}
