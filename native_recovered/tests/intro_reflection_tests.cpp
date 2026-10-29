#include "engine_reflection.hpp"
#include "owned_store_test_support.hpp"
#include <iostream>
#include <type_traits>
using namespace pvz2_recovered::engine;
using owned_store_test::append;
void compare(const std::vector<std::uint32_t>& a,const std::vector<std::uint32_t>& b,const char* what) {
    for(std::size_t i=0;i<std::min(a.size(),b.size());++i)if(a[i]!=b[i])throw std::runtime_error(std::string(what)+" first difference at "+std::to_string(i)+": "+std::to_string(a[i])+" vs ARM "+std::to_string(b[i])+"; sizes "+std::to_string(a.size())+"/"+std::to_string(b.size()));
    if(a.size()!=b.size())throw std::runtime_error(std::string(what)+" sizes differ "+std::to_string(a.size())+"/"+std::to_string(b.size()));
}
enum class Operation {ensure,package,load,populate,lookup};
struct Step {Operation op;std::uint32_t type;std::vector<std::uint32_t> name,data;const char* label;std::vector<std::vector<std::uint32_t>> results,states;};
#ifdef PVZ2_LEVEL_FIXTURES
#include "level_reflection_fixtures.inc"
#elif defined(PVZ2_WAVE_FIXTURES)
#include "wave_reflection_fixtures.inc"
#elif defined(PVZ2_SEEDBANK_FIXTURES)
#include "seedbank_reflection_fixtures.inc"
#elif defined(PVZ2_RAILCART_FIXTURES)
#include "railcart_reflection_fixtures.inc"
#else
#include "intro_reflection_fixtures.inc"
#endif
std::vector<std::uint32_t> snapshot(ReflectionDataRuntime& runtime) {
    std::vector<std::uint32_t> out;const auto& types=runtime.classes().ordered();out.push_back(static_cast<std::uint32_t>(types.size()));
    for(const auto* cls:types) {
        out.push_back(static_cast<std::uint32_t>(cls->name.size()));for(unsigned char c:cls->name)out.push_back(c);
        const auto parent=std::find(types.begin(),types.end(),cls->parent);
        out.push_back(parent==types.end()?0U:static_cast<std::uint32_t>(parent-types.begin()+1));out.push_back(cls->factory?1U:0U);
    }
    std::vector<const RuntimeClass*> queries{nullptr};queries.insert(queries.end(),types.begin(),types.end());
    for(auto* a:queries)for(auto* b:queries)out.push_back(ClassDirectory::derives_from(a,b)?1U:0U);
    append(out,runtime.strings().normalized_state());
    for(auto type:{2U,3U}) {
        auto* store=runtime.registry().find(type);out.push_back(store?1U:0U);if(!store)continue;
        out.push_back(store->name_id());out.push_back(store->package_id());append(out,owned_store_test::slot_state(store->slots()));
        append(out,store->descriptors().normalized_state());append(out,store->names().normalized_state());
    }
    const auto handle=[&](Handle h) {out.insert(out.end(),{h.low,h.high,runtime.resolve(h)});};
    const auto pool=[&](const auto& value) {
        if constexpr(std::is_same_v<std::decay_t<decltype(value)>,ZombiePoolData>)out.insert(out.end(),{value.cost,value.weight,value.overridden});
        else out.insert(out.end(),{value.weight,value.max_count,value.includes_planted});
        handle(value.type);
    };
    out.push_back(static_cast<std::uint32_t>(runtime.object_slots()));
    for(std::uint32_t i=1;i<=runtime.object_slots();++i) {
        const auto* object=runtime.object(i);out.push_back(object?1U:0U);if(!object)continue;
        const auto index=static_cast<std::size_t>(std::find(types.begin(),types.end(),&object->type)-types.begin());out.push_back(static_cast<std::uint32_t>(index+1));
        if(index==1) {out.insert(out.end(),{object->flag,object->ground_type});handle(object->effect);}
        else {
            handle(object->this_pointer);
            if(index>=4 && index<=10) {
                out.push_back(static_cast<std::uint32_t>(object->resource_groups.size()));
                for(const auto& text:object->resource_groups) {out.push_back(static_cast<std::uint32_t>(text.size()));for(unsigned char c:text)out.push_back(c);}
            }
            if(index==6 || index==7) {out.insert(out.end(),object->pan_bits.begin(),object->pan_bits.end());out.insert(out.end(),object->narration.begin(),object->narration.end());}
            if(index==8) {
                out.push_back(static_cast<std::uint32_t>(object->railcart_type.size()));for(unsigned char c:object->railcart_type)out.push_back(c);
                out.push_back(static_cast<std::uint32_t>(object->rails.size()));for(const auto& value:object->rails)out.insert(out.end(),value.begin(),value.end());
                out.push_back(static_cast<std::uint32_t>(object->railcarts.size()));for(const auto& value:object->railcarts)out.insert(out.end(),value.begin(),value.end());
            }
            if(index==9) {
                out.push_back(object->selection_method);out.insert(out.end(),object->seed_modes.begin(),object->seed_modes.end());
                for(const auto& list:object->plant_lists) {
                    out.push_back(static_cast<std::uint32_t>(list.size()));
                    for(const auto& text:list) {out.push_back(static_cast<std::uint32_t>(text.size()));for(unsigned char c:text)out.push_back(c);}
                }
                out.push_back(static_cast<std::uint32_t>(object->blacklist_lifted_by.size()));for(unsigned char c:object->blacklist_lifted_by)out.push_back(c);
            }
            if(index==10) {
                const auto& w=*object->wave;handle(w.hero);out.push_back(static_cast<std::uint32_t>(w.waves.size()));
                for(const auto& v:w.waves) {
                    out.insert(out.end(),v.flags.begin(),v.flags.end());out.insert(out.end(),v.integers.begin(),v.integers.end());out.push_back(v.event.enabled);
                    out.insert(out.end(),v.event.integers.begin(),v.event.integers.end());out.push_back(v.spawn_time_bits);
                    out.push_back(static_cast<std::uint32_t>(v.zombies.size()));
                    for(const auto& z:v.zombies) {out.insert(out.end(),{z.row,z.plant_food});out.insert(out.end(),z.integers.begin(),z.integers.end());handle(z.type);out.insert(out.end(),z.floats.begin(),z.floats.end());}
                    const auto list=[&](const auto& values) {out.push_back(static_cast<std::uint32_t>(values.size()));for(const auto& entry:values)pool(entry);};
                    list(v.add_zombies);list(v.remove_zombies);list(v.add_seeds);list(v.remove_seeds);
                }
                out.push_back(static_cast<std::uint32_t>(w.zombie_pool.size()));for(const auto& v:w.zombie_pool)pool(v);
                out.insert(out.end(),w.integers.begin(),w.integers.end());out.push_back(w.spawn_count?1U:0U);if(w.spawn_count)out.push_back(*w.spawn_count);
                out.insert(out.end(),w.flags.begin(),w.flags.end());
            }
            if(index==11) {
                const auto& v=*object->level;
                for(const auto& text:v.texts){out.push_back(static_cast<std::uint32_t>(text.size()));for(unsigned char c:text)out.push_back(c);}
                out.insert(out.end(),{v.starting_sun,v.level_number,v.level_index,v.zombie_max_level});for(auto h:v.references)handle(h);
                out.push_back(static_cast<std::uint32_t>(v.modules.size()));for(auto h:v.modules)handle(h);
                out.insert(out.end(),v.reward_types.begin(),v.reward_types.end());out.insert(out.end(),v.flags.begin(),v.flags.end());
                out.push_back(static_cast<std::uint32_t>(v.feature_slots.size()));out.insert(out.end(),v.feature_slots.begin(),v.feature_slots.end());
                out.push_back(static_cast<std::uint32_t>(v.warnings.size()));for(const auto& w:v.warnings){handle(w.type);out.push_back(static_cast<std::uint32_t>(w.text.size()));for(unsigned char c:w.text)out.push_back(c);out.push_back(w.level);}
            }
        }
    }
    return out;
}
int main() {
    unsigned checks=0;const char* label="initial state";
    try {
        ReflectionDataRuntime runtime;runtime.register_level_intro_classes();runtime.register_level_intro_classes();
#ifdef PVZ2_RAILCART_FIXTURES
        runtime.register_railcart_class();runtime.register_railcart_class();
#endif
#ifdef PVZ2_SEEDBANK_FIXTURES
        runtime.register_seedbank_class();runtime.register_seedbank_class();
#endif
#ifdef PVZ2_WAVE_FIXTURES
        runtime.register_wavegenerator_class();runtime.register_wavegenerator_class();
#endif
#ifdef PVZ2_LEVEL_FIXTURES
        runtime.register_leveldefinition_class();runtime.register_leveldefinition_class();
#endif
        compare(snapshot(runtime),initial_state,"initial reflection state");std::map<std::uint32_t,ObjectLoadResult> loaded;
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
                    compare(result,s.results[stage],"factory result");compare(snapshot(runtime),s.states[stage],"factory state");++stage;++checks;if(!created.success)continue;
                }
                result={runtime.populate_objects(reader,s.type,loaded[s.type])?1U:0U};
            }
            compare(result,s.results[stage],"operation result");compare(snapshot(runtime),s.states[stage],"reflection state");++checks;
        }
#ifdef PVZ2_LEVEL_FIXTURES
        std::cout<<"PASS "<<checks<<" level/inherited reflection module-reference ARM full-state checkpoints\n";
#elif defined(PVZ2_WAVE_FIXTURES)
        std::cout<<"PASS "<<checks<<" wave/inherited reflection nested-reference ARM full-state checkpoints\n";
#elif defined(PVZ2_SEEDBANK_FIXTURES)
        std::cout<<"PASS "<<checks<<" seedbank/inherited reflection enum/bool/string-list ARM full-state checkpoints\n";
#elif defined(PVZ2_RAILCART_FIXTURES)
        std::cout<<"PASS "<<checks<<" railcart/inherited reflection nested-record ARM full-state checkpoints\n";
#else
        std::cout<<"PASS "<<checks<<" inherited reflection factory/property/list/reference ARM full-state checkpoints\n";
#endif
    }catch(const std::exception& e){std::cerr<<label<<": "<<e.what()<<'\n';return 1;}
}
