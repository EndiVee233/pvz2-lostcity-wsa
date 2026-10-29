#pragma once
#include "engine_handles.hpp"
#include <array>
#include <string>
namespace pvz2_recovered::engine {
class InternPool;
class OwnedRegistry;
class IndexedRtonReader;
inline constexpr const char* level_text_names[]{"Name","Description","MainObjective","challengeDropGroupId","NormalPresentTable","ShinyPresentTable","FirstRewardParam","ReplayRewardParam","FirstIntroNarrative","ReplayIntroNarrative","FirstOutroNarrative","ReplayOutroNarrative","ForceNextLevel","CompletionAchievement","MusicType"};
inline constexpr const char* level_flag_names[]{"SuppressVictoryScreen","GameOverDialogShowBrain","GameOverDialogTaskFailed","ForceWarpTunnel","IsDangerRoom","IsBossFight","IsArenaBattle","IsArenaEdit","IsLevelOfTheDay"};
struct ZombieWarningData {Handle type{};std::string text;std::uint32_t level=0;};
class LevelDefinitionData {
public:
    InternPool& strings;
    std::array<std::string,15> texts;
    std::uint16_t starting_sun=50;
    std::uint32_t level_number=0,level_index=0xffffffffU,zombie_max_level=0xffffffffU;
    // StageModule, VictoryModule, Loot; all owned symbolic handles.
    std::array<Handle,3> references{};
    std::vector<Handle> modules;
    std::array<std::uint32_t,2> reward_types{{2,2}};
    std::array<std::uint8_t,9> flags{{0,1,0,0,0,0,0,0,0}};
    // The selected original registration leaves GameFeature as a read-declining
    // placeholder (011ab2bc). Resize is observed; no feature values are decoded.
    std::vector<std::uint32_t> feature_slots;
    std::vector<ZombieWarningData> warnings;
    explicit LevelDefinitionData(InternPool&);
    ~LevelDefinitionData();
    LevelDefinitionData(const LevelDefinitionData&)=delete;
    LevelDefinitionData& operator=(const LevelDefinitionData&)=delete;
};
void fill_level_definition(LevelDefinitionData&,IndexedRtonReader&,std::uint32_t data,OwnedRegistry&,std::uint32_t current_type);
}
