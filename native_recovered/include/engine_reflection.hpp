#pragma once
#include "engine_rton_reader.hpp"
#include "engine_store.hpp"
#include "engine_wave_data.hpp"
#include "engine_level_data.hpp"
#include <array>
#include <map>

namespace pvz2_recovered::engine {
struct ReflectedDataObject;
struct RuntimeClass {
    using Factory = std::unique_ptr<ReflectedDataObject>(*)(InternPool&, const RuntimeClass&);
    std::string name;
    RuntimeClass* parent = nullptr;
    Factory factory = nullptr;
};
// 011f761c/011f6120/011f60e4/011f6104/011f595c logical registry.
// Original metadata handles, COW/tree ABI and full reflection schema builder
// are separate from this explicit owner.
class ClassDirectory {
    std::vector<RuntimeClass*> ordered_;
    std::map<std::string, RuntimeClass*, std::less<>> names_;
public:
    void publish(RuntimeClass&, std::string_view name, RuntimeClass* parent, RuntimeClass::Factory);
    RuntimeClass* find(std::string_view name) const;
    const std::vector<RuntimeClass*>& ordered() const { return ordered_; }
    static bool derives_from(const RuntimeClass*, const RuntimeClass* base);
};
// Covered selected real factories and registered fields. This is a data representation, not game
// behavior/vtable/Android object ABI. Padding is deliberately not reproduced.
struct ReflectedDataObject {
    InternPool& strings;
    const RuntimeClass& type;
    std::uint8_t flag = 0;
    std::uint32_t ground_type = 0xffffffffU;
    Handle effect{};
    Handle this_pointer{};
    std::vector<std::string> resource_groups;
    std::array<std::uint32_t, 4> pan_bits{{0x429c0000U, 0x43ea0000U, 0x40000000U, 0x40200000U}};
    std::array<std::uint32_t, 2> narration{{0xffffffffU, 0xffffffffU}};
    std::string railcart_type;
    std::vector<std::array<std::uint32_t, 3>> rails;
    std::vector<std::array<std::uint32_t, 2>> railcarts;
    std::uint32_t selection_method = 1;
    std::array<std::uint8_t, 3> seed_modes{};
    std::array<std::vector<std::string>, 3> plant_lists;
    std::string blacklist_lifted_by;
    std::unique_ptr<WaveGeneratorData> wave;
    std::unique_ptr<LevelDefinitionData> level;
    std::array<std::uint32_t, 5> sun_drop_bits{};
    Handle danger_world{};
    std::vector<Handle> danger_designers;
    std::uint32_t zombie_win_x_bits=0xc2a00000U;
    ReflectedDataObject(InternPool& pool, const RuntimeClass& cls) : strings(pool), type(cls) {}
    ~ReflectedDataObject() { level.reset(); wave.reset(); for(auto& h:danger_designers)assign_handle(h,{},strings);assign_handle(danger_world,{},strings);assign_handle(effect, {}, strings); assign_handle(this_pointer, {}, strings); }
};
struct ObjectLoadResult { bool success = false; std::vector<std::uint32_t> objects; };
class ReflectionDataRuntime final : private RegistryServices {
    InternPool strings_;
    OwnedRegistry registry_;
    RuntimeClass root_, ground_;
    std::array<RuntimeClass, 6> intro_classes_;
    bool intro_registered_ = false;
    RuntimeClass railcart_;
    bool railcart_registered_ = false;
    RuntimeClass seedbank_;
    bool seedbank_registered_ = false;
    RuntimeClass wavegenerator_;
    bool wavegenerator_registered_ = false;
    RuntimeClass leveldefinition_;
    bool leveldefinition_registered_ = false;
    RuntimeClass sundropper_;
    bool sundropper_registered_ = false;
    RuntimeClass zombiesdead_;
    bool zombiesdead_registered_ = false;
    RuntimeClass dangermodule_;
    bool dangermodule_registered_ = false;
    RuntimeClass brainprops_;
    bool brainprops_registered_ = false;
    ClassDirectory classes_;
    std::vector<std::unique_ptr<ReflectedDataObject>> objects_;
    std::size_t callback_count(std::uint32_t) override { return 0; }
    void callback(std::uint32_t, std::size_t, const OwnedStore&) override {}
    void destroy_object(std::uint32_t token) override;
    bool fill(ReflectedDataObject&, IndexedRtonReader&, std::uint32_t object, std::uint32_t current_type);
public:
    explicit ReflectionDataRuntime(std::uint32_t seed = 0x87654321U);
    ~ReflectionDataRuntime() override;
    // Opt in to the evidenced GameObject -> DangerRoom intro inheritance chain.
    // Metadata/schema ABI and game behavior remain outside this data adapter.
    void register_level_intro_classes();
    void register_railcart_class();
    void register_seedbank_class();
    void register_wavegenerator_class();
    void register_leveldefinition_class();
    void register_sundropper_class();
    void register_zombiesdead_class();
    void register_danger_module_class();
    void register_brain_properties_class();
    OwnedStore& ensure_store(std::uint32_t type, const char32_t* name);
    void set_package(std::uint32_t type, const char32_t* path);
    // Bounded ports of the two-pass 011ed5fc/011ead94 read chain: version 1,
    // objects with string objclass/aliases, no explicit uid, supported schema.
    ObjectLoadResult create_objects(IndexedRtonReader&, std::uint32_t type);
    bool populate_objects(IndexedRtonReader&, std::uint32_t type, const ObjectLoadResult&);
    const ReflectedDataObject* object(std::uint32_t token) const;
    std::size_t object_slots() const { return objects_.size(); }
    std::uint32_t resolve(Handle h) { return registry_.resolve(h); }
    InternPool& strings() { return strings_; }
    OwnedRegistry& registry() { return registry_; }
    const ClassDirectory& classes() const { return classes_; }
};
}
