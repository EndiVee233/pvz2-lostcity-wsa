#include "engine_reflection.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
std::string quote(std::string_view text) {
    constexpr char hex[]="0123456789abcdef";std::string out="\"";
    for(unsigned char c:text) {
        if(c=='"' || c=='\\') {out.push_back('\\');out.push_back(static_cast<char>(c));}
        else if(c<32) {out+="\\u00";out.push_back(hex[c>>4]);out.push_back(hex[c&15]);}
        else out.push_back(static_cast<char>(c));
    }
    out.push_back('"');return out;
}
#include "wave_json.hpp"
#include "level_json.hpp"
int main(int argc,char** argv) {
    const bool danger_module=argc==4 && std::string(argv[3])=="--danger-module";
    const bool sundropper=danger_module || (argc==4 && std::string(argv[3])=="--sundropper");
    const bool intro_only=argc==4 && std::string(argv[3])=="--intro-only";
    const bool railcart_only=argc==4 && std::string(argv[3])=="--railcart-only";
    const bool seedbank_only=argc==4 && std::string(argv[3])=="--seedbank-only";
    const bool wave_only=argc==4 && std::string(argv[3])=="--wave-only";
    if(argc!=3 && !intro_only && !railcart_only && !seedbank_only && !wave_only && !sundropper) {std::cerr<<"Usage: rton_load_objects plaintext.rton objects.json [--intro-only|--railcart-only|--seedbank-only|--wave-only|--sundropper|--danger-module]\n";return 2;}
    try {
        std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("cannot open input");
        std::vector<std::uint8_t> data((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());
        const bool latest=!(intro_only || railcart_only || seedbank_only || wave_only);
        ReflectionDataRuntime runtime;runtime.register_level_intro_classes();if(!intro_only)runtime.register_railcart_class();if(!intro_only && !railcart_only)runtime.register_seedbank_class();if(!intro_only && !railcart_only && !seedbank_only)runtime.register_wavegenerator_class();if(latest)runtime.register_leveldefinition_class();runtime.ensure_store(2,U"local");runtime.set_package(2,latest?U"packages/CurrentLevel.rton":U"packages/local.rton");
        if(sundropper)runtime.register_sundropper_class();
        if(danger_module)runtime.register_danger_module_class();
        auto document=normalize_rton(std::move(data),&runtime.strings());if(!document.success)throw std::runtime_error("invalid raw RTON document");
        IndexedRtonReader reader(std::move(document));const auto result=runtime.create_objects(reader,2);
        if(!result.success)throw std::runtime_error("unsupported RTON version");
        (void)runtime.populate_objects(reader,2,result);
        std::ostringstream out;out<<"{\n  \"data_only\": true,\n  \"success\": true,\n  \"objects\": [";std::size_t created=0;
        for(std::size_t i=0;i<result.objects.size();++i) {
            if(i)out<<',';
            const auto* object=runtime.object(result.objects[i]);if(!object) {out<<"\n    null";continue;}
            ++created;out<<"\n    {\"index\": "<<i<<", \"objclass\": "<<quote(object->type.name);
            const auto target=[&](Handle handle) {
                const auto resolved=runtime.resolve(handle);const auto found=std::find(result.objects.begin(),result.objects.end(),resolved);
                if(!resolved || found==result.objects.end())out<<"null";else out<<(found-result.objects.begin());
            };
            const auto strings=[&](const char* name,const auto& values) {
                out<<", "<<quote(name)<<": [";for(std::size_t j=0;j<values.size();++j) {if(j)out<<", ";out<<quote(values[j]);}out<<']';
            };
            if(object->type.name=="EntityComponent_GroundEffect") {
                out<<", \"m_type\": "<<object->ground_type<<", \"m_effect_target\": ";target(object->effect);
            } else {
                out<<", \"m_thisPtr_target\": ";target(object->this_pointer);
                const auto* modules=runtime.classes().find("LevelModuleProperties");
                if(ClassDirectory::derives_from(&object->type,modules)) {
                    strings("ResourceGroupNames",object->resource_groups);
                }
                if(ClassDirectory::derives_from(&object->type,runtime.classes().find("StandardLevelIntroProperties"))) {
                    out<<", \"float32_bits\": [";for(std::size_t j=0;j<4;++j) {if(j)out<<", ";out<<object->pan_bits[j];}out<<']';
                    const char* names[]{"PanStartOffset","PanEndOffset","PanRightDuration","PanLeftDuration"};
                    for(std::size_t j=0;j<4;++j) {
                        float value;std::memcpy(&value,&object->pan_bits[j],sizeof(value));out<<", "<<quote(names[j])<<": ";
                        if(std::isfinite(value))out<<std::setprecision(9)<<value;else out<<"null";
                    }
                    out<<", \"NarrationID\": "<<static_cast<std::int32_t>(object->narration[0])<<", \"SubsequentPlayNarrationID\": "<<static_cast<std::int32_t>(object->narration[1]);
                }
                if(object->type.name=="RailcartProperties") {
                    out<<", \"RailcartType\": "<<quote(object->railcart_type);
                    const auto records=[&](const char* name,const auto& values,const auto& fields) {
                        out<<", "<<quote(name)<<": [";
                        for(std::size_t n=0;n<values.size();++n) {
                            if(n)out<<", ";out<<'{';
                            for(std::size_t j=0;j<values[n].size();++j) {if(j)out<<", ";out<<quote(fields[j])<<": "<<static_cast<std::int32_t>(values[n][j]);}
                            out<<'}';
                        }
                        out<<']';
                    };
                    const char* rail_fields[]{"Column","RowStart","RowEnd"};records("Rails",object->rails,rail_fields);
                    const char* cart_fields[]{"Column","Row"};records("Railcarts",object->railcarts,cart_fields);
                }
                if(object->type.name=="SeedBankProperties") {
                    out<<", \"SelectionMethod\": "<<object->selection_method;
                    const char* names[]{"AlwaysUseChooser","ZombieMode","GridItemMode"};
                    for(std::size_t j=0;j<3;++j)out<<", "<<quote(names[j])<<": "<<(object->seed_modes[j]?"true":"false");
                    const char* lists[]{"PlantWhiteList","PlantBlackList","PresetPlantList"};
                    for(std::size_t j=0;j<3;++j)strings(lists[j],object->plant_lists[j]);
                    out<<", \"BlackListLiftedBy\": "<<quote(object->blacklist_lifted_by);
                }
                if(object->wave)append_wave_json(out,*object->wave,runtime,result.objects);
                if(object->level)append_level_json(out,*object->level,runtime,result.objects);
                if(object->type.name=="DangerRoomModuleProperties") {
                    out<<", \"WorldSpecificProperties\": ";write_data_reference_json(out,object->danger_world,runtime,result.objects);
                    out<<", \"LevelDesigners\": [";
                    for(std::size_t j=0;j<object->danger_designers.size();++j) {if(j)out<<',';write_data_reference_json(out,object->danger_designers[j],runtime,result.objects);}
                    out<<']';
                }
                if(object->type.name=="SunDropperProperties") {
                    const char* names[]{"InitialSunDropDelay", "SunCountdownBase", "SunCountdownRange", "SunCountdownMax", "SunCountdownIncreasePerSun"};
                    for(std::size_t j=0;j<5;++j)out<<", "<<quote(std::string(names[j])+"_bits")<<": "<<object->sun_drop_bits[j];
                }
            }
            out<<'}';
        }
        out<<"\n  ]\n}\n";
        std::ofstream output(argv[2],std::ios::binary);if(!output)throw std::runtime_error("cannot open output");output<<out.str();if(!output)throw std::runtime_error("object graph write failed");
        std::cout<<"Created "<<created<<" of "<<result.objects.size()<<" data objects; "<<(intro_only?7:railcart_only?8:seedbank_only?9:wave_only?10:danger_module?14:sundropper?12:11)<<" supported concrete data classes\n";
        if(created!=result.objects.size()) {std::cerr<<"Some declarations have unsupported/abstract factories\n";return 3;}
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
