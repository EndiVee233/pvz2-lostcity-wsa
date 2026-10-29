#pragma once
#include <type_traits>
// Included after the CLI's JSON quote helper. Handles are rendered by logical
// package/name and local target index; intern IDs depend on loading history.
inline void write_data_reference_json(std::ostream& out,pvz2_recovered::engine::Handle value,
                             pvz2_recovered::engine::ReflectionDataRuntime& runtime,const std::vector<std::uint32_t>& objects) {
    using namespace pvz2_recovered::engine;
    const auto wide_utf8=[](const std::u32string& text) {
        std::string result;
        for(std::uint32_t c:text) {
            if(c<0x80)result.push_back(static_cast<char>(c));
            else if(c<0x800) {result.push_back(static_cast<char>(0xc0|(c>>6)));result.push_back(static_cast<char>(0x80|(c&63)));}
            else if(c<0x10000) {result.push_back(static_cast<char>(0xe0|(c>>12)));result.push_back(static_cast<char>(0x80|((c>>6)&63)));result.push_back(static_cast<char>(0x80|(c&63)));}
            else if(c<=0x10ffff) {result.push_back(static_cast<char>(0xf0|(c>>18)));result.push_back(static_cast<char>(0x80|((c>>12)&63)));result.push_back(static_cast<char>(0x80|((c>>6)&63)));result.push_back(static_cast<char>(0x80|(c&63)));}
            else throw std::logic_error("JSON tool requires Unicode reference text");
        }
        return result;
    };
        out<<"{\"package\": ";
        if(value.high&0x80000000U)out<<quote(wide_utf8(runtime.strings().text((value.low>>31)|((value.high&0x3fffffffU)<<1))));else out<<"null";
        out<<", \"name\": ";if(value.high&0x80000000U)out<<quote(wide_utf8(runtime.strings().text(value.low&0x7fffffffU)));else out<<"null";
        out<<", \"target\": ";const auto resolved=runtime.resolve(value);const auto found=std::find(objects.begin(),objects.end(),resolved);
        if(!resolved || found==objects.end())out<<"null";else out<<(found-objects.begin());out<<'}';
}
inline void append_wave_json(std::ostream& out,const pvz2_recovered::engine::WaveGeneratorData& data,
                             pvz2_recovered::engine::ReflectionDataRuntime& runtime,const std::vector<std::uint32_t>& objects) {
    using namespace pvz2_recovered::engine;
    const auto key=[&](const char* name){out<<", "<<quote(name)<<": ";};
    const auto reference=[&](Handle value){write_data_reference_json(out,value,runtime,objects);};
    const auto integer=[&](const char* name,std::uint32_t value){key(name);out<<static_cast<std::int32_t>(value);};
    const auto boolean=[&](const char* name,std::uint8_t value){key(name);out<<(value?"true":"false");};
    const auto floating=[&](const char* name,std::uint32_t bits){key(name);float value;std::memcpy(&value,&bits,sizeof(value));if(std::isfinite(value))out<<std::setprecision(17)<<static_cast<double>(value);else out<<"null";out<<", "<<quote(std::string(name)+"_bits")<<": "<<bits;};
    const auto list=[&](const char* name,const auto& values,const auto& write){key(name);out<<'[';for(std::size_t i=0;i<values.size();++i){if(i)out<<", ";write(values[i]);}out<<']';};
    const auto pool=[&](const auto& value) {
        if constexpr(std::is_same_v<std::decay_t<decltype(value)>,ZombiePoolData>) {
            out<<"{\"Cost\": "<<static_cast<std::int32_t>(value.cost);integer("Weight",value.weight);boolean("Overridden",value.overridden);
        }else {out<<"{\"Weight\": "<<static_cast<std::int32_t>(value.weight);integer("MaxCount",value.max_count);boolean("MaxCountIncludesPlanted",value.includes_planted);}
        key("Type");reference(value.type);out<<'}';
    };
    const auto zombie=[&](const ZombieSpawnData& value) {
        out<<"{\"Row\": "<<value.row;boolean("HasPlantFood",value.plant_food);integer("Loot",value.integers[0]);integer("Level",value.integers[1]);
        key("Type");reference(value.type);const char* ints[]{"Rise_GridX","Rise_GridY","SunDrop","BesiegeHit"};for(std::size_t i=0;i<4;++i)integer(ints[i],value.integers[i+2]);
        const char* floats[]{"ZombieRate","ZombieScale","TargetValidTime"};for(std::size_t i=0;i<3;++i)floating(floats[i],value.floats[i]);out<<'}';
    };
    const auto wave=[&](const WaveData& value) {
        out<<"{\"DisableRandomSpawns\": "<<(value.flags[0]?"true":"false");boolean("WaitUntilAllZombiesDie",value.flags[1]);
        const char* ints[]{"ColNumPlantIsDragged","SpawnColStart","SpawnColEnd","SpawnPlantFoodCount","WavePointStart","WavePointIncrement"};for(std::size_t i=0;i<6;++i)integer(ints[i],value.integers[i]);
        boolean("WavePointOverride",value.flags[2]);out<<", \"Event\": {\"Enabled\": "<<(value.event.enabled?"true":"false");
        const char* events[]{"Count","TimeSpread","Waves"};for(std::size_t i=0;i<3;++i)integer(events[i],value.event.integers[i]);out<<'}';
        floating("WaveSpawnTime",value.spawn_time_bits);list("Zombies",value.zombies,zombie);list("AddToZombiePool",value.add_zombies,pool);list("RemoveFromZombiePool",value.remove_zombies,pool);
        list("AddToSeedPool",value.add_seeds,pool);list("RemoveFromSeedPool",value.remove_seeds,pool);out<<'}';
    };
    key("HeroProps");reference(data.hero);list("Waves",data.waves,wave);list("ZombiePool",data.zombie_pool,pool);
    const char* ints[]{"FlagWaveInterval","WaveCount","WaveSpendingPointIncrement","WaveSpendingPoints","SpawnColStart","SpawnColEnd"};for(std::size_t i=0;i<6;++i)integer(ints[i],data.integers[i]);
    key("SpawnCount");if(data.spawn_count)out<<static_cast<std::int32_t>(*data.spawn_count);else out<<"null";
    boolean("SpawnCount_defined",data.spawn_count?1:0);boolean("IgnoreFlagCarriers",data.flags[0]);boolean("IsRiseFromGroundMode",data.flags[1]);
}
