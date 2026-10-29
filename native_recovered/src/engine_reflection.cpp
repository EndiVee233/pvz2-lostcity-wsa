#include "engine_reflection.hpp"
#include <cerrno>
#include <cstdlib>
#include <stdexcept>
#include <type_traits>

namespace pvz2_recovered::engine {
void ClassDirectory::publish(RuntimeClass& cls, std::string_view name, RuntimeClass* parent, RuntimeClass::Factory factory) {
    const auto nul = name.find('\0'); if (nul != std::string_view::npos) name = name.substr(0, nul);
    cls.name = name; cls.parent = parent; cls.factory = factory; ordered_.push_back(&cls); names_[cls.name] = &cls;
}
RuntimeClass* ClassDirectory::find(std::string_view name) const {
    const auto nul = name.find('\0'); if (nul != std::string_view::npos) name = name.substr(0, nul);
    const auto found = names_.find(name); return found == names_.end() ? nullptr : found->second;
}
bool ClassDirectory::derives_from(const RuntimeClass* cls, const RuntimeClass* base) {
    if (!base) return false;
    while (cls) { if (cls == base) return true; cls = cls->parent; }
    return false;
}
namespace {
std::unique_ptr<ReflectedDataObject> data_factory(InternPool& strings, const RuntimeClass& cls) { return std::make_unique<ReflectedDataObject>(strings, cls); }
std::unique_ptr<ReflectedDataObject> wave_factory(InternPool& strings, const RuntimeClass& cls) {
    auto object = data_factory(strings, cls); object->wave = std::make_unique<WaveGeneratorData>(strings); return object;
}
std::unique_ptr<ReflectedDataObject> level_factory(InternPool& strings, const RuntimeClass& cls) {
    auto object = data_factory(strings, cls); object->level = std::make_unique<LevelDefinitionData>(strings); return object;
}
std::uint32_t member(IndexedRtonReader& reader, std::uint32_t object, std::string_view name) { return reader.value_offset(reader.find_field(object, name)); }
std::string text(IndexedRtonReader& reader, std::uint32_t value) { return reader.narrow_text_at(reader.narrow_value_offset(value)); }
bool space(unsigned char c) { return c == 32 || (c >= 9 && c <= 13); }
std::uint32_t enum_value(IndexedRtonReader& reader, std::uint32_t value, const std::pair<const char*, std::uint32_t>* entries, std::size_t count) {
    if (!value) return 0;
    reader.seek(value); const auto tag = reader.peek();
    if (tag != 0xb0 && tag != 0xb1) throw std::logic_error("selected enum input currently requires narrow text");
    auto name = text(reader, value);
    const auto first = name.find_first_not_of(" \t\n\r\v\f");
    if (first == std::string::npos) name.clear();
    else { name.erase(0, first); while (!name.empty() && space(static_cast<unsigned char>(name.back()))) name.pop_back(); }
    for (std::size_t i = 0; i < count; ++i) if (name == entries[i].first) return entries[i].second;
    errno = 0; const auto number = std::strtoll(name.c_str(), nullptr, 10);
    if (errno == ERANGE || number < -2147483648LL || number > 2147483647LL) throw std::out_of_range("selected enum decimal range");
    return static_cast<std::uint32_t>(number);
}
}
ReflectionDataRuntime::ReflectionDataRuntime(std::uint32_t seed) : registry_(strings_, *this, seed) {
    (void)ensure_store(0x2001, U"System.ReflectionSymbols");
    auto& classes = ensure_store(0x2002, U"System.RtClasses");
    // Actual child metadata allocates its slot before requesting parent metadata.
    (void)classes.create(0xf0000001U, 2, 1); (void)classes.create(0xf0000002U, 2, 1);
    classes_.publish(root_, "RtObject", nullptr, nullptr);
    classes_.publish(ground_, "EntityComponent_GroundEffect", &root_, data_factory);
}
ReflectionDataRuntime::~ReflectionDataRuntime() { registry_.clear(); objects_.clear(); }
void ReflectionDataRuntime::register_level_intro_classes() {
    if (intro_registered_) return;
    auto* store = registry_.find(0x2002U);
    for (std::uint32_t i = 0; i < intro_classes_.size(); ++i) (void)store->create(0xf0000003U + i, 2, 1);
    const char* names[]{"GameObject", "PropertySheetBase", "LevelModuleProperties", "IntroModuleProperties", "StandardLevelIntroProperties", "DangerRoomLevelIntroProperties"};
    RuntimeClass* parent = &root_;
    for (std::size_t i = 0; i < intro_classes_.size(); ++i) {
        classes_.publish(intro_classes_[i], names[i], parent, data_factory); parent = &intro_classes_[i];
    }
    intro_registered_ = true;
}
void ReflectionDataRuntime::register_railcart_class() {
    if (railcart_registered_) return;
    register_level_intro_classes();
    (void)registry_.find(0x2002U)->create(0xf0000009U, 2, 1);
    classes_.publish(railcart_, "RailcartProperties", &intro_classes_[2], data_factory);
    railcart_registered_ = true;
}
void ReflectionDataRuntime::register_seedbank_class() {
    if (seedbank_registered_) return;
    register_railcart_class();
    (void)registry_.find(0x2002U)->create(0xf000000aU, 2, 1);
    classes_.publish(seedbank_, "SeedBankProperties", &intro_classes_[2], data_factory);
    seedbank_registered_ = true;
}
void ReflectionDataRuntime::register_wavegenerator_class() {
    if (wavegenerator_registered_) return;
    register_seedbank_class();
    (void)registry_.find(0x2002U)->create(0xf000000bU, 2, 1);
    classes_.publish(wavegenerator_, "WaveGeneratorProperties", &intro_classes_[2], wave_factory);
    wavegenerator_registered_ = true;
}
void ReflectionDataRuntime::register_leveldefinition_class() {
    if (leveldefinition_registered_) return;
    register_wavegenerator_class();
    (void)registry_.find(0x2002U)->create(0xf000000cU, 2, 1);
    classes_.publish(leveldefinition_, "LevelDefinition", &intro_classes_[1], level_factory);
    leveldefinition_registered_ = true;
}
void ReflectionDataRuntime::register_sundropper_class() {
    if (sundropper_registered_) return;
    register_leveldefinition_class();
    (void)registry_.find(0x2002U)->create(0xf000000dU, 2, 1);
    classes_.publish(sundropper_, "SunDropperProperties", &intro_classes_[2], data_factory);
    sundropper_registered_ = true;
}
void ReflectionDataRuntime::register_zombiesdead_class() {
    if (zombiesdead_registered_) return;
    register_sundropper_class();
    (void)registry_.find(0x2002U)->create(0xf000000eU, 2, 1);
    classes_.publish(zombiesdead_, "ZombiesDeadWinConProperties", &intro_classes_[2], data_factory);
    zombiesdead_registered_ = true;
}
void ReflectionDataRuntime::register_danger_module_class() {
    if (dangermodule_registered_) return;
    register_zombiesdead_class();
    (void)registry_.find(0x2002U)->create(0xf000000fU, 2, 1);
    classes_.publish(dangermodule_, "DangerRoomModuleProperties", &intro_classes_[2], data_factory);
    dangermodule_registered_ = true;
}
void ReflectionDataRuntime::register_brain_properties_class() {
    if (brainprops_registered_) return;
    register_danger_module_class();
    (void)registry_.find(0x2002U)->create(0xf0000010U, 2, 1);
    classes_.publish(brainprops_, "ZombiesAteYourBrainsProperties", &intro_classes_[2], data_factory);
    brainprops_registered_ = true;
}
OwnedStore& ReflectionDataRuntime::ensure_store(std::uint32_t type, const char32_t* name) {
    if (auto* store = registry_.find(type)) return *store;
    StoreConfig config; config.name = strings_.acquire(name);
    for (const auto c : strings_.text(config.name.id)) config.display_name.push_back(static_cast<char>(c & 255U));
    config.fixed_content = (type & 0x2000U) ? 1 : 0;
    auto& store = registry_.ensure(type, &config); strings_.release(config.name.id); return store;
}
void ReflectionDataRuntime::set_package(std::uint32_t type, const char32_t* path) {
    auto* store = registry_.find(type); if (!store) throw std::logic_error("package store missing");
    const auto input = strings_.acquire(path); store->set_package(input.id); strings_.release(input.id);
}
void ReflectionDataRuntime::destroy_object(std::uint32_t token) {
    if (token && token <= objects_.size()) objects_[token - 1].reset();
}
const ReflectedDataObject* ReflectionDataRuntime::object(std::uint32_t token) const { return token && token <= objects_.size() ? objects_[token - 1].get() : nullptr; }
ObjectLoadResult ReflectionDataRuntime::create_objects(IndexedRtonReader& reader, std::uint32_t type) {
    ObjectLoadResult result;
    if (reader.scalar_int32_bits(member(reader, reader.root(), "version")) != 1) return result;
    auto* store = registry_.find(type); if (!store) throw std::logic_error("load store missing");
    store->reset(false); const auto array = member(reader, reader.root(), "objects");
    result.success = true; if (!reader.is_array(array)) return result;
    const auto count = reader.array_count(array); result.objects.resize(count);
    for (std::uint32_t i = 0; i < count; ++i) {
        const auto node = reader.array_element(array, i);
        if (!reader.is_object(node)) throw std::logic_error("object declaration must be an object");
        if (member(reader, node, "uid")) throw std::logic_error("explicit UID loading not recovered");
        const Descriptor32 descriptor{i, 1, 0xffffffffU}; const auto handle = store->create(0, 0, 1, &descriptor);
        const auto* cls = classes_.find(text(reader, member(reader, node, "objclass")));
        auto instance = cls && cls->factory ? cls->factory(strings_, *cls) : nullptr;
        if (!instance) { (void)store->release(handle); continue; }
        objects_.push_back(std::move(instance)); const auto token = static_cast<std::uint32_t>(objects_.size());
        result.objects[i] = token; (void)store->set_object(handle, token);
        const auto aliases = member(reader, node, "aliases");
        for (std::uint32_t n = 0, size = reader.array_count(aliases); n < size; ++n) {
            const auto alias = text(reader, reader.array_element(aliases, n)); if (alias.empty()) continue;
            std::u32string wide; for (unsigned char c : alias) wide.push_back(static_cast<char32_t>(c));
            const auto name = strings_.acquire(wide.c_str());
            (void)store->insert_loaded_name(name.id, handle); strings_.release(name.id);
        }
    }
    return result;
}
bool ReflectionDataRuntime::fill(ReflectedDataObject& object, IndexedRtonReader& reader, std::uint32_t node, std::uint32_t type) {
    const auto data = member(reader, node, "objdata"); if (!reader.is_object(data)) return false;
    // 011b9bb0 gates each field using its saved object offset. The vector
    // codec 011b7180 unconditionally pops its scope, even for a non-array:
    // following codecs then read from the enclosing declaration instead.
    auto scope = data;
    const auto pop_scope = [&]() { scope = scope == data ? node : 0U; };
    const auto property = [&](const char* name) { return member(reader, scope, name); };
    const auto narrow = [&](std::uint32_t value) {
        if (!value) return std::string{};
        reader.seek(value); const auto tag = reader.peek();
        if (tag != 0xb0 && tag != 0xb1) throw std::logic_error("selected string property currently requires narrow text");
        return text(reader, value);
    };
    const auto string_list = [&](const char* field, std::vector<std::string>& target) {
        if (!member(reader, data, field)) return;
        const auto value = property(field); target.clear();
        if (!reader.is_array(value)) pop_scope();
        for (std::uint32_t i = 0, count = reader.array_count(value); i < count; ++i) target.push_back(narrow(reader.array_element(value, i)));
    };
    const auto reference = [&](const char* name, Handle& target) {
        const auto ref = member(reader, data, name);
        if (ref) { auto value = reader.reference_value(ref, registry_, strings_, type); assign_handle(target, value, strings_); assign_handle(value, {}, strings_); }
    };
    if (ClassDirectory::derives_from(&object.type, &ground_)) {
        static const std::pair<const char*, std::uint32_t> entries[]{{"tide",0},{"tide_with_tail",1},{"tide_gargantuar",2},{"rise",3},{"surf",5},{"stuck_under_ground",6},{"stuck_into_ground",7}};
        const auto value = member(reader, data, "m_type"); if (value) object.ground_type = enum_value(reader, value, entries, 7);
        reference("m_effect", object.effect);
    }
    if (intro_registered_ && ClassDirectory::derives_from(&object.type, &intro_classes_[0])) reference("m_thisPtr", object.this_pointer);
    if (intro_registered_ && ClassDirectory::derives_from(&object.type, &intro_classes_[2])) {
        string_list("ResourceGroupNames", object.resource_groups);
    }
    if (intro_registered_ && ClassDirectory::derives_from(&object.type, &intro_classes_[4])) {
        const char* floats[]{"PanStartOffset", "PanEndOffset", "PanRightDuration", "PanLeftDuration"};
        const char* integers[]{"NarrationID", "SubsequentPlayNarrationID"};
        for (std::size_t i = 0; i < object.pan_bits.size(); ++i) if (member(reader, data, floats[i])) object.pan_bits[i] = reader.scalar_float32_bits(property(floats[i]));
        for (std::size_t i = 0; i < object.narration.size(); ++i) if (member(reader, data, integers[i])) object.narration[i] = reader.scalar_int32_bits(property(integers[i]));
    }
    if (railcart_registered_ && ClassDirectory::derives_from(&object.type, &railcart_)) {
        if (member(reader, data, "RailcartType")) {
            object.railcart_type = narrow(property("RailcartType"));
        }
        const auto records = [&](const char* field, auto& target, const auto& columns) {
            if (!member(reader, data, field)) return;
            const auto value = property(field); if (!reader.is_array(value)) pop_scope();
            typename std::decay_t<decltype(target)>::value_type defaults; defaults.fill(0xffffffffU);
            target.resize(reader.array_count(value), defaults);
            for (std::uint32_t i = 0; i < target.size(); ++i) {
                const auto record = reader.array_element(value, i); if (!reader.is_object(record)) continue;
                for (std::size_t j = 0; j < target[i].size(); ++j) { const auto component = member(reader, record, columns[j]); if (component) target[i][j] = reader.scalar_int32_bits(component); }
            }
        };
        const char* rail_fields[]{"Column", "RowStart", "RowEnd"}; records("Rails", object.rails, rail_fields);
        const char* cart_fields[]{"Column", "Row"}; records("Railcarts", object.railcarts, cart_fields);
    }
    if (seedbank_registered_ && ClassDirectory::derives_from(&object.type, &seedbank_)) {
        static const std::pair<const char*, std::uint32_t> entries[]{{"preset",0},{"chooser",1}};
        if (member(reader, data, "SelectionMethod")) object.selection_method = enum_value(reader, property("SelectionMethod"), entries, 2);
        const char* modes[]{"AlwaysUseChooser", "ZombieMode", "GridItemMode"};
        for (std::size_t i = 0; i < object.seed_modes.size(); ++i) if (member(reader, data, modes[i])) object.seed_modes[i] = static_cast<std::uint8_t>(reader.scalar_boolean_bits(property(modes[i])));
        // Registration order differs from memory order: PresetPlantList is last.
        string_list("PlantWhiteList", object.plant_lists[0]);
        string_list("PlantBlackList", object.plant_lists[1]);
        if (member(reader, data, "BlackListLiftedBy")) object.blacklist_lifted_by = narrow(property("BlackListLiftedBy"));
        string_list("PresetPlantList", object.plant_lists[2]);
    }
    if (object.wave) fill_wave_generator(*object.wave, reader, data, scope, registry_, type);
    if (sundropper_registered_ && ClassDirectory::derives_from(&object.type, &sundropper_)) {
        const char* names[]{"InitialSunDropDelay", "SunCountdownBase", "SunCountdownRange", "SunCountdownMax", "SunCountdownIncreasePerSun"};
        for (std::size_t i = 0; i < object.sun_drop_bits.size(); ++i)
            if (member(reader, data, names[i])) object.sun_drop_bits[i] = reader.scalar_float32_bits(property(names[i]));
    }
    if (object.level) fill_level_definition(*object.level, reader, data, registry_, type);
    if (brainprops_registered_ && ClassDirectory::derives_from(&object.type, &brainprops_)) {
        const auto value=member(reader,data,"ZombieWinPositionX");
        if(value)object.zombie_win_x_bits=reader.scalar_float32_bits(value);
    }
    if (dangermodule_registered_ && ClassDirectory::derives_from(&object.type, &dangermodule_)) {
        reference("WorldSpecificProperties", object.danger_world);
        const auto value=member(reader,data,"LevelDesigners");
        if(value) {
            if(!reader.is_array(value))throw std::logic_error("danger designer list requires array; malformed scope propagation not recovered");
            const auto count=reader.array_count(value);
            for(std::size_t i=count;i<object.danger_designers.size();++i)assign_handle(object.danger_designers[i],{},strings_);
            object.danger_designers.resize(count);
            for(std::uint32_t i=0;i<count;++i) {
                auto ref=reader.reference_value(reader.array_element(value,i),registry_,strings_,type);
                assign_handle(object.danger_designers[i],ref,strings_);assign_handle(ref,{},strings_);
            }
        }
    }
    return true;
}
bool ReflectionDataRuntime::populate_objects(IndexedRtonReader& reader, std::uint32_t type, const ObjectLoadResult& objects) {
    const auto array = member(reader, reader.root(), "objects"); const auto count = reader.array_count(array);
    for (std::uint32_t i = 0; i < count && i < objects.objects.size(); ++i) {
        const auto token = objects.objects[i]; if (auto* object = token && token <= objects_.size() ? objects_[token - 1].get() : nullptr) (void)fill(*object, reader, reader.array_element(array, i), type);
    }
    return true; // Original second pass does not aggregate per-object failures.
}
}
