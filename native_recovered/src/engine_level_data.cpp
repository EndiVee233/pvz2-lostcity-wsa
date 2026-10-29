#include "engine_level_data.hpp"
#include "engine_intern.hpp"
#include "engine_rton_reader.hpp"
#include <cerrno>
#include <cstdlib>
#include <stdexcept>
namespace pvz2_recovered::engine {
namespace {
std::uint32_t member(IndexedRtonReader& reader,std::uint32_t node,const char* name) {return reader.value_offset(reader.find_field(node,name));}
std::string narrow(IndexedRtonReader& reader,std::uint32_t value) {
    reader.seek(value);const auto tag=reader.peek();
    if(tag!=0xb0 && tag!=0xb1)throw std::logic_error("level text currently requires narrow string input");
    return reader.narrow_text_at(reader.narrow_value_offset(value));
}
std::uint32_t reward(IndexedRtonReader& reader,std::uint32_t value) {
    auto text=narrow(reader,value);const auto first=text.find_first_not_of(" \t\n\r\v\f");
    if(first==std::string::npos)text.clear();else {text.erase(0,first);text.erase(text.find_last_not_of(" \t\n\r\v\f")+1);}
    const char* entries[]{"none","present","collectable","seed_packet","powerup","upgrade","bonus","mapgadget","powerupgadget","firstkey","note","worldtrophy","starkey","piece_firegourd","piece_gravebuster"};
    for(std::uint32_t i=0;i<15;++i)if(text==entries[i])return i;
    errno=0;const auto result=std::strtoll(text.c_str(),nullptr,10);
    if(errno==ERANGE || result<-2147483648LL || result>2147483647LL)throw std::out_of_range("reward enum decimal range");
    return static_cast<std::uint32_t>(result);
}
}
LevelDefinitionData::LevelDefinitionData(InternPool& pool):strings(pool) {
    texts[2]="[SURVIVE_ZOMBIE_ATTACK]";texts[6]="moneybag";texts[7]="moneybag";
}
LevelDefinitionData::~LevelDefinitionData() {
    for(auto& value:warnings)assign_handle(value.type,{},strings);
    assign_handle(references[2],{},strings);
    for(auto& value:modules)assign_handle(value,{},strings);
    assign_handle(references[1],{},strings);assign_handle(references[0],{},strings);
}
void fill_level_definition(LevelDefinitionData& target,IndexedRtonReader& reader,std::uint32_t data,OwnedRegistry& registry,std::uint32_t current) {
    const auto text=[&](std::size_t i){const auto value=member(reader,data,level_text_names[i]);if(value)target.texts[i]=narrow(reader,value);};
    const auto integer=[&](const char* name,std::uint32_t& output){const auto value=member(reader,data,name);if(value)output=reader.scalar_int32_bits(value);};
    const auto flag=[&](std::size_t i){const auto value=member(reader,data,level_flag_names[i]);if(value)target.flags[i]=static_cast<std::uint8_t>(reader.scalar_boolean_bits(value));};
    const auto assign=[&](std::uint32_t value,Handle& output){auto owned=reader.reference_value(value,registry,target.strings,current);assign_handle(output,owned,target.strings);assign_handle(owned,{},target.strings);};
    const auto ref=[&](const char* name,Handle& output){const auto value=member(reader,data,name);if(value)assign(value,output);};
    const auto array=[&](const char* name){const auto value=member(reader,data,name);if(value && !reader.is_array(value))throw std::logic_error("level list requires array; malformed context propagation not recovered");return value;};
    for(std::size_t i=0;i<3;++i)text(i);
    const auto sun=member(reader,data,"StartingSun");if(sun)target.starting_sun=static_cast<std::uint16_t>(reader.scalar_int32_bits(sun));
    integer("LevelNumber",target.level_number);integer("LevelIndex",target.level_index);
    ref("StageModule",target.references[0]);ref("VictoryModule",target.references[1]);
    const auto modules=array("Modules");if(modules) {
        const auto count=reader.array_count(modules);for(std::size_t i=count;i<target.modules.size();++i)assign_handle(target.modules[i],{},target.strings);
        target.modules.resize(count);for(std::uint32_t i=0;i<count;++i)assign(reader.array_element(modules,i),target.modules[i]);
    }
    ref("Loot",target.references[2]);for(std::size_t i=3;i<6;++i)text(i);flag(0);
    const auto first=member(reader,data,"FirstRewardType");if(first)target.reward_types[0]=reward(reader,first);text(6);
    const auto replay=member(reader,data,"ReplayRewardType");if(replay)target.reward_types[1]=reward(reader,replay);text(7);
    flag(1);flag(2);for(std::size_t i=8;i<13;++i)text(i);for(std::size_t i=3;i<9;++i)flag(i);
    text(13);const auto features=array("GameFeaturesToUnlock");if(features)target.feature_slots.resize(reader.array_count(features),0);
    text(14);const auto warnings=array("ZombieWarningInfos");if(warnings) {
        const auto count=reader.array_count(warnings);for(std::size_t i=count;i<target.warnings.size();++i)assign_handle(target.warnings[i].type,{},target.strings);
        target.warnings.resize(count);
        for(std::uint32_t i=0;i<count;++i) {
            const auto node=reader.array_element(warnings,i);if(!reader.is_object(node))continue;
            auto& value=target.warnings[i];
            const auto type=member(reader,node,"Type");if(type)assign(type,value.type);
            const auto message=member(reader,node,"Text");if(message)value.text=narrow(reader,message);
            const auto level=member(reader,node,"Level");if(level)value.level=reader.scalar_int32_bits(level);
        }
    }
    integer("ZombieMaxLevel",target.zombie_max_level);
}
}
