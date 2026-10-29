#pragma once
#include "engine_intern.hpp"
#include "engine_name_index.hpp"
#include "engine_slot_index.hpp"
#include "engine_slots.hpp"

namespace pvz2_recovered::engine {
struct StoreConfig {
    std::uint32_t reserved_slots = 0;
    InternValue name{};
    std::string display_name;
    std::uint8_t fixed_content = 0, system_byte = 0;
};
class OwnedStore;
struct RegistryServices {
    virtual ~RegistryServices() = default;
    virtual std::size_t callback_count(std::uint32_t registry_offset) = 0;
    virtual void callback(std::uint32_t registry_offset, std::size_t, const OwnedStore&) = 0;
    virtual void destroy_object(std::uint32_t object_token) = 0;
};
class OwnedRegistry;
// Recovered store metadata construction/reset and package-aware teardown.
// Explicit host ownership replaces original allocator/COW storage ABI.
class OwnedStore final : private SlotServices {
    friend class OwnedRegistry;
    OwnedRegistry& registry_;
    std::uint32_t serial_, type_, reserved_, name_id_ = 0;
    std::uint32_t package_id_ = 0;
    std::u32string package_filename_;
    std::string display_;
    std::uint8_t fixed_, system_;
    SlotPool slots_;
    DescriptorIndex descriptors_;
    ObjectNameIndex names_;
    StoreView view_;
    std::vector<std::uint32_t> forwarders_;
    bool closed_ = false;
    OwnedStore(OwnedRegistry&, std::uint32_t serial, std::uint32_t type, const StoreConfig&);
    void close();
    std::size_t callback_count(SlotEvent) override { return 0; }
    void callback(SlotEvent, std::size_t, Handle) override;
    void put_descriptor(const Descriptor32&, Handle) override;
    void erase_descriptor(const Descriptor32&) override;
    void destroy_object(std::uint32_t) override;
    void forward(std::uint32_t offset);
public:
    ~OwnedStore() override;
    OwnedStore(const OwnedStore&) = delete;
    OwnedStore& operator=(const OwnedStore&) = delete;
    // 011ea17c. soft release is valid only for active slots with positive refs.
    void reset(bool hard);
    Handle create(std::uint32_t object, int mode = 0, std::uint8_t marked = 0, const Descriptor32* descriptor = nullptr);
    bool release(Handle);
    void retain(Handle);
    bool bind_name(std::uint32_t name, Handle);
    // Loader adapters: publish after factory creation; first loaded alias wins.
    bool set_object(Handle, std::uint32_t token);
    bool insert_loaded_name(std::uint32_t name, Handle);
    // 011ebe2c. Input is an interned wide path; normalized aliases share the
    // registry's type-name tree. Caller must hold a valid nonzero input ID.
    void set_package(std::uint32_t input_id);
    StoreView& view();
    std::uint32_t serial() const { return serial_; }
    std::uint32_t type() const { return type_; }
    std::uint32_t name_id() const { return name_id_; }
    std::uint32_t package_id() const { return package_id_; }
    const std::u32string& package_filename() const { return package_filename_; }
    // 011e63b4 chooses the package name when present, otherwise the store name.
    std::uint32_t effective_name_id() const { return package_id_ ? package_id_ : name_id_; }
    std::uint32_t reserved_slots() const { return reserved_; }
    const std::string& display_name() const { return display_; }
    std::uint8_t fixed_content() const { return fixed_; }
    std::uint8_t system_byte() const { return system_; }
    const SlotPool& slots() const { return slots_; }
    const DescriptorIndex& descriptors() const { return descriptors_; }
    const ObjectNameIndex& names() const { return names_; }
    const std::vector<std::uint32_t>& forwarders() const { return forwarders_; }
};
class OwnedRegistry final : private StoreFactory {
    friend class OwnedStore;
    InternPool& strings_;
    RegistryServices& services_;
    TypeNameIndex types_;
    RegistryBanks banks_;
    std::vector<std::unique_ptr<OwnedStore>> stores_;
    const StoreConfig* pending_ = nullptr;
    std::uint32_t next_serial_ = 0;
    std::uint32_t descriptor_seed_;
    StoreView* construct(std::uint32_t type, std::uint32_t parameter) override;
    void install_forwarder(StoreView&, std::uint32_t) override;
public:
    OwnedRegistry(InternPool& strings, RegistryServices& services, std::uint32_t descriptor_seed = 0)
        : strings_(strings), services_(services), descriptor_seed_(descriptor_seed) {}
    ~OwnedRegistry() override;
    OwnedRegistry(const OwnedRegistry&) = delete;
    OwnedRegistry& operator=(const OwnedRegistry&) = delete;
    OwnedStore& ensure(std::uint32_t type, const StoreConfig* = nullptr);
    OwnedStore* find(std::uint32_t type);
    bool remove(std::uint32_t type);
    void clear();
    RegistryView view();
    std::uint32_t resolve(Handle h) { return resolve_registered_object(view(), h, strings_); }
    const TypeNameIndex& type_names() const { return types_; }
    const RegistryBanks& banks() const { return banks_; }
    const std::vector<std::unique_ptr<OwnedStore>>& stores() const { return stores_; }
};
}
