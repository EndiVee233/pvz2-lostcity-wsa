#pragma once
#include "engine_handles.hpp"
#include <array>
#include <optional>
namespace pvz2_recovered::engine {
class InternPool;
class OwnedRegistry;
class IndexedRtonReader;
struct ZombiePoolData {
    std::uint32_t cost=0xffffffffU,weight=0xffffffffU;
    std::uint8_t overridden=0;
    Handle type{};
};
struct SeedPoolData {
    std::uint32_t weight=1000,max_count=0;
    std::uint8_t includes_planted=0;
    Handle type{};
};
struct ZombieSpawnData {
    std::uint32_t row=6;
    std::uint8_t plant_food=0;
    // Loot, Level, Rise_GridX, Rise_GridY, SunDrop, BesiegeHit.
    std::array<std::uint32_t,6> integers{{0,1,0,0,0,1}};
    Handle type{};
    // ZombieRate, ZombieScale, TargetValidTime (IEEE float32 bits).
    std::array<std::uint32_t,3> floats{{0,0x3f800000U,0x3fc00000U}};
};
struct WaveEventData {
    std::uint8_t enabled=0;
    std::array<std::uint32_t,3> integers{{0xffffffffU,0,0xffffffffU}};
};
struct WaveData {
    // DisableRandomSpawns, WaitUntilAllZombiesDie, WavePointOverride.
    std::array<std::uint8_t,3> flags{};
    // ColNumPlantIsDragged, SpawnColStart, SpawnColEnd, SpawnPlantFoodCount,
    // WavePointStart, WavePointIncrement.
    std::array<std::uint32_t,6> integers{{0,0xffffffffU,0xffffffffU,0,0xffffffffU,0xffffffffU}};
    WaveEventData event;
    std::uint32_t spawn_time_bits=0x40000000U;
    std::vector<ZombieSpawnData> zombies;
    std::vector<ZombiePoolData> add_zombies,remove_zombies;
    std::vector<SeedPoolData> add_seeds,remove_seeds;
};
// Owns every symbolic handle in the nested POD records. Reallocation transfers
// ownership; shrink/clear release explicitly in original forward order.
class WaveGeneratorData {
public:
    InternPool& strings;
    Handle hero{};
    std::vector<WaveData> waves;
    std::vector<ZombiePoolData> zombie_pool;
    std::array<std::uint32_t,6> integers{{0xffffffffU,0xffffffffU,0xffffffffU,0xffffffffU,0xffffffffU,0xffffffffU}};
    // Original 009c4c70 does not initialize the registered +0x58 word.
    std::optional<std::uint32_t> spawn_count;
    std::array<std::uint8_t,2> flags{};
    explicit WaveGeneratorData(InternPool&);
    ~WaveGeneratorData();
    WaveGeneratorData(const WaveGeneratorData&)=delete;
    WaveGeneratorData& operator=(const WaveGeneratorData&)=delete;
};
void fill_wave_generator(WaveGeneratorData&,IndexedRtonReader&,std::uint32_t data,
                         std::uint32_t scope,OwnedRegistry&,std::uint32_t current_type);
}
