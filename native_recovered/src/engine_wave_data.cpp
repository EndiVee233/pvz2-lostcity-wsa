#include "engine_wave_data.hpp"
#include "engine_intern.hpp"
#include "engine_rton_reader.hpp"
#include <cerrno>
#include <cstdlib>
#include <stdexcept>
namespace pvz2_recovered::engine {
namespace {
template<class T> void release(T& value,InternPool& strings) {assign_handle(value.type,{},strings);}
void release(WaveData&,InternPool&);
template<class T> void release_list(std::vector<T>& values,InternPool& strings) {for(auto& value:values)release(value,strings);}
void release(WaveData& value,InternPool& strings) {
    // 009c7710: reverse field order; elements within each vector go forward.
    release_list(value.remove_seeds,strings);release_list(value.add_seeds,strings);
    release_list(value.remove_zombies,strings);release_list(value.add_zombies,strings);release_list(value.zombies,strings);
}
template<class T> void resize(std::vector<T>& values,std::uint32_t count,InternPool& strings) {
    for(std::size_t i=count;i<values.size();++i)release(values[i],strings);
    values.resize(count);
}
std::uint32_t member(IndexedRtonReader& reader,std::uint32_t node,const char* key) {return reader.value_offset(reader.find_field(node,key));}
std::uint32_t row_enum(IndexedRtonReader& reader,std::uint32_t value) {
    reader.seek(value);const auto tag=reader.peek();
    if(tag!=0xb0 && tag!=0xb1)throw std::logic_error("wave Row enum currently requires narrow text");
    auto name=reader.narrow_text_at(reader.narrow_value_offset(value));
    const auto first=name.find_first_not_of(" \t\n\r\v\f");
    if(first==std::string::npos)name.clear();else {name.erase(0,first);name.erase(name.find_last_not_of(" \t\n\r\v\f")+1);}
    const char* entries[]{"1","2","3","4","5","6","?","prev"};
    for(std::uint32_t i=0;i<8;++i)if(name==entries[i])return i;
    errno=0;const auto result=std::strtoll(name.c_str(),nullptr,10);
    if(errno==ERANGE || result<-2147483648LL || result>2147483647LL)throw std::out_of_range("wave Row enum decimal range");
    return static_cast<std::uint32_t>(result);
}
class Reader {
    IndexedRtonReader& reader;
    InternPool& strings;
    OwnedRegistry& registry;
    std::uint32_t current;
    void reference(std::uint32_t value,Handle& target) {
        auto result=reader.reference_value(value,registry,strings,current);
        assign_handle(target,result,strings);assign_handle(result,{},strings);
    }
    template<class T> void records(std::uint32_t value,std::vector<T>& target) {
        if(!reader.is_array(value))throw std::logic_error("wave record list requires an array; malformed nested scope not recovered");
        resize(target,reader.array_count(value),strings);
        for(std::uint32_t i=0;i<target.size();++i) {
            const auto node=reader.array_element(value,i);if(reader.is_object(node))fill(node,target[i]);
        }
    }
    void integer(std::uint32_t node,const char* key,std::uint32_t& target) {const auto value=member(reader,node,key);if(value)target=reader.scalar_int32_bits(value);}
    void boolean(std::uint32_t node,const char* key,std::uint8_t& target) {const auto value=member(reader,node,key);if(value)target=static_cast<std::uint8_t>(reader.scalar_boolean_bits(value));}
    void floating(std::uint32_t node,const char* key,std::uint32_t& target) {const auto value=member(reader,node,key);if(value)target=reader.scalar_float32_bits(value);}
    template<class T> void list(std::uint32_t node,const char* key,std::vector<T>& target) {const auto value=member(reader,node,key);if(value)records(value,target);}
    void ref(std::uint32_t node,const char* key,Handle& target) {const auto value=member(reader,node,key);if(value)reference(value,target);}
    void fill(std::uint32_t node,ZombiePoolData& value) {
        integer(node,"Cost",value.cost);integer(node,"Weight",value.weight);boolean(node,"Overridden",value.overridden);ref(node,"Type",value.type);
    }
    void fill(std::uint32_t node,SeedPoolData& value) {
        integer(node,"Weight",value.weight);integer(node,"MaxCount",value.max_count);boolean(node,"MaxCountIncludesPlanted",value.includes_planted);ref(node,"Type",value.type);
    }
    void fill(std::uint32_t node,ZombieSpawnData& value) {
        const auto row=member(reader,node,"Row");if(row)value.row=row_enum(reader,row);
        boolean(node,"HasPlantFood",value.plant_food);
        integer(node,"Loot",value.integers[0]);integer(node,"Level",value.integers[1]);ref(node,"Type",value.type);
        const char* names[]{"Rise_GridX","Rise_GridY","SunDrop","BesiegeHit"};
        for(std::size_t i=0;i<4;++i)integer(node,names[i],value.integers[i+2]);
        const char* floats[]{"ZombieRate","ZombieScale","TargetValidTime"};for(std::size_t i=0;i<3;++i)floating(node,floats[i],value.floats[i]);
    }
    void fill(std::uint32_t node,WaveData& value) {
        boolean(node,"DisableRandomSpawns",value.flags[0]);boolean(node,"WaitUntilAllZombiesDie",value.flags[1]);
        const char* names[]{"ColNumPlantIsDragged","SpawnColStart","SpawnColEnd","SpawnPlantFoodCount","WavePointStart","WavePointIncrement"};
        for(std::size_t i=0;i<6;++i)integer(node,names[i],value.integers[i]);boolean(node,"WavePointOverride",value.flags[2]);
        const auto event=member(reader,node,"Event");if(reader.is_object(event)) {
            boolean(event,"Enabled",value.event.enabled);const char* events[]{"Count","TimeSpread","Waves"};for(std::size_t i=0;i<3;++i)integer(event,events[i],value.event.integers[i]);
        }
        floating(node,"WaveSpawnTime",value.spawn_time_bits);
        list(node,"Zombies",value.zombies);list(node,"AddToZombiePool",value.add_zombies);list(node,"RemoveFromZombiePool",value.remove_zombies);
        list(node,"AddToSeedPool",value.add_seeds);list(node,"RemoveFromSeedPool",value.remove_seeds);
    }
public:
    Reader(IndexedRtonReader& input,WaveGeneratorData& data,OwnedRegistry& reg,std::uint32_t type):reader(input),strings(data.strings),registry(reg),current(type) {}
    void fill(std::uint32_t node,std::uint32_t scope,WaveGeneratorData& value) {
        if(member(reader,node,"HeroProps"))reference(member(reader,scope,"HeroProps"),value.hero);
        if(member(reader,node,"Waves"))records(member(reader,scope,"Waves"),value.waves);
        if(member(reader,node,"ZombiePool"))records(member(reader,scope,"ZombiePool"),value.zombie_pool);
        const char* names[]{"FlagWaveInterval","WaveCount","WaveSpendingPointIncrement","WaveSpendingPoints","SpawnColStart","SpawnColEnd"};
        for(std::size_t i=0;i<6;++i)if(member(reader,node,names[i]))value.integers[i]=reader.scalar_int32_bits(member(reader,scope,names[i]));
        if(member(reader,node,"SpawnCount"))value.spawn_count=reader.scalar_int32_bits(member(reader,scope,"SpawnCount"));
        const char* flags[]{"IgnoreFlagCarriers","IsRiseFromGroundMode"};for(std::size_t i=0;i<2;++i)if(member(reader,node,flags[i]))value.flags[i]=static_cast<std::uint8_t>(reader.scalar_boolean_bits(member(reader,scope,flags[i])));
    }
};
}
WaveGeneratorData::WaveGeneratorData(InternPool& pool):strings(pool) {
    const auto name=strings.acquire(U"DefaultHeroLevelProps");const auto package=strings.acquire(U"HeroTypes");
    assign_handle(hero,{name.id|(package.id<<31),(package.id>>1)|0x80000000U},strings);
    strings.release(package.id);strings.release(name.id);
}
WaveGeneratorData::~WaveGeneratorData() {release_list(zombie_pool,strings);release_list(waves,strings);assign_handle(hero,{},strings);}
void fill_wave_generator(WaveGeneratorData& target,IndexedRtonReader& reader,std::uint32_t data,std::uint32_t scope,OwnedRegistry& registry,std::uint32_t current) {
    Reader(reader,target,registry,current).fill(data,scope,target);
}
}
