#pragma once
// Included after wave_json.hpp's shared logical-reference renderer.
inline void append_level_json(std::ostream& out,const pvz2_recovered::engine::LevelDefinitionData& data,
                              pvz2_recovered::engine::ReflectionDataRuntime& runtime,const std::vector<std::uint32_t>& objects) {
    using namespace pvz2_recovered::engine;
    const auto key=[&](const char* name){out<<", "<<quote(name)<<": ";};
    const auto integer=[&](const char* name,std::uint32_t value){key(name);out<<static_cast<std::int32_t>(value);};
    for(std::size_t i=0;i<data.texts.size();++i){key(level_text_names[i]);out<<quote(data.texts[i]);}
    key("StartingSun");out<<static_cast<std::int16_t>(data.starting_sun);key("StartingSun_bits");out<<data.starting_sun;
    integer("LevelNumber",data.level_number);integer("LevelIndex",data.level_index);integer("ZombieMaxLevel",data.zombie_max_level);
    const char* refs[]{"StageModule","VictoryModule","Loot"};for(std::size_t i=0;i<3;++i){key(refs[i]);write_data_reference_json(out,data.references[i],runtime,objects);}
    key("Modules");out<<'[';for(std::size_t i=0;i<data.modules.size();++i){if(i)out<<", ";write_data_reference_json(out,data.modules[i],runtime,objects);}out<<']';
    key("FirstRewardType");out<<data.reward_types[0];key("ReplayRewardType");out<<data.reward_types[1];
    for(std::size_t i=0;i<data.flags.size();++i){key(level_flag_names[i]);out<<(data.flags[i]?"true":"false");}
    key("GameFeaturesToUnlock");out<<'[';for(std::size_t i=0;i<data.feature_slots.size();++i){if(i)out<<", ";out<<data.feature_slots[i];}out<<']';
    out<<", \"GameFeaturesToUnlock_values_read\": false";
    key("ZombieWarningInfos");out<<'[';
    for(std::size_t i=0;i<data.warnings.size();++i){if(i)out<<", ";const auto& value=data.warnings[i];out<<"{\"Type\": ";write_data_reference_json(out,value.type,runtime,objects);key("Text");out<<quote(value.text);integer("Level",value.level);out<<'}';}
    out<<']';
}
