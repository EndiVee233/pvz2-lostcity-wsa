#include "engine_store.hpp"
#include "engine_package_paths.hpp"
#include <algorithm>
#include <stdexcept>

namespace pvz2_recovered::engine {
OwnedStore::OwnedStore(OwnedRegistry& registry, std::uint32_t serial, std::uint32_t type, const StoreConfig& config)
    : registry_(registry), serial_(serial), type_(type), reserved_(config.reserved_slots),
      display_(config.display_name), fixed_(config.fixed_content), system_(config.system_byte),
      slots_(type), names_(&registry.strings_) {
    auto& strings = registry_.strings_;
    if (config.name.id) { name_id_ = config.name.id; strings.retain(name_id_); (void)strings.text_address(name_id_); }
    const auto assign_name = [&](std::uint32_t id) {
        if (name_id_ != id) { strings.release(name_id_); name_id_ = id; strings.retain(id); (void)strings.text_address(id); }
    };
    if (!name_id_) {
        const auto ascii = std::to_string(static_cast<std::int32_t>(type));
        const std::u32string wide(ascii.begin(), ascii.end());
        const auto temporary = strings.acquire(wide.c_str());
        assign_name(temporary.id); strings.release(temporary.id);
    }
    const auto prefixed = std::u32string(U"$") + strings.text(name_id_);
    const auto temporary = strings.acquire(prefixed.c_str());
    assign_name(temporary.id); strings.release(temporary.id);
    registry_.types_.put(name_id_, type_);
    reset(true);
}
OwnedStore::~OwnedStore() { if (!closed_) close(); }
void OwnedStore::forward(std::uint32_t offset) {
    if (std::find(forwarders_.begin(), forwarders_.end(), offset) == forwarders_.end()) return;
    const auto count = registry_.services_.callback_count(offset);
    for (std::size_t i = 0; i < count; ++i) registry_.services_.callback(offset, i, *this);
}
void OwnedStore::callback(SlotEvent, std::size_t, Handle) { throw std::logic_error("unregistered slot callback"); }
void OwnedStore::put_descriptor(const Descriptor32& key, Handle value) { descriptors_.put(key, value); }
void OwnedStore::erase_descriptor(const Descriptor32& key) { descriptors_.erase(key); }
void OwnedStore::destroy_object(std::uint32_t object) { registry_.services_.destroy_object(object); }
StoreView& OwnedStore::view() { view_ = names_.attach(descriptors_.attach(slots_.view())); return view_; }
Handle OwnedStore::create(std::uint32_t object, int mode, std::uint8_t marked, const Descriptor32* descriptor) {
    auto h = slots_.create(object, mode, marked, descriptor, registry_.descriptor_seed_, *this); (void)view(); return h;
}
bool OwnedStore::release(Handle h) { const auto result = slots_.release(h, *this); (void)view(); return result; }
void OwnedStore::retain(Handle h) { slots_.retain(h); }
bool OwnedStore::bind_name(std::uint32_t name, Handle h) { const auto result = bind_object_name(view(), names_, name, h); (void)view(); return result; }
bool OwnedStore::set_object(Handle h, std::uint32_t token) { const auto ok = slots_.set_object(h, token); (void)view(); return ok; }
bool OwnedStore::insert_loaded_name(std::uint32_t name, Handle h) {
    const auto value = describe_handle(view(), h); const auto ok = names_.insert_unique(name, value); (void)view(); return ok;
}
void OwnedStore::set_package(std::uint32_t input_id) {
    auto& strings = registry_.strings_;
    auto temporary = input_id;
    strings.retain(temporary); (void)strings.text_address(temporary);
    if (temporary) {
        const auto bytes = narrow_low_bytes(strings.text(input_id));
        const auto normalized = widen_bytes(normalize_package_path(bytes));
        const auto canonical = strings.acquire(normalized.c_str());
        if (temporary != canonical.id) {
            strings.release(temporary); temporary = canonical.id;
            strings.retain(temporary); (void)strings.text_address(temporary);
        }
        strings.release(canonical.id);
    }
    if (package_id_ == temporary) { strings.release(temporary); return; }
    if (package_id_) registry_.types_.erase(package_id_);
    strings.release(package_id_); package_id_ = temporary;
    strings.retain(package_id_); (void)strings.text_address(package_id_);
    const auto bytes = narrow_low_bytes(strings.text(input_id));
    package_filename_ = widen_bytes(package_resource_filename(bytes));
    if (package_id_) registry_.types_.put(package_id_, type_);
    strings.release(temporary);
}
void OwnedStore::reset(bool hard) {
    forward(0x34);
    if (hard) {
        slots_.drain_deferred(*this);
        const auto active = slots_.list(SlotPool::active_list);
        for (auto it = active.rbegin(); it != active.rend(); ++it) {
            auto& slot = slots_.slot(*it);
            if (slot.object_address) {
                if (!(slot.flags & 0x20000000U)) destroy_object(slot.object_address);
                slot.object_address = 0;
                for (auto& word : slot.unknown14) word = 0;
            }
        }
        slots_.discard_storage(); descriptors_.clear(); names_.clear();
        if (reserved_) slots_.grow(reserved_);
    } else {
        auto active = slots_.list(SlotPool::active_list);
        while (!active.empty()) {
            const auto index = active.back(); const auto& slot = slots_.slot(index); const auto gen = slot.generation;
            const Handle h = index < 0x10000U ? Handle{index | (gen << 16),(type_ << 17) | (gen >> 16)}
                : Handle{index | (gen << 24),(type_ << 17) | (gen >> 8) | 0x10000U};
            while (slots_.reference_count(h)) slots_.release(h, *this);
            const auto after = slots_.list(SlotPool::active_list);
            // The original loops indefinitely on a zero-ref active slot. Make
            // that unsupported invariant violation explicit in this host owner.
            if (!after.empty() && after.back() == index) throw std::logic_error("soft reset requires positive active references");
            active = after;
        }
        names_.clear();
    }
    (void)view(); forward(0x44);
}
void OwnedStore::close() {
    reserved_ = 0; reset(true);
    if (name_id_) registry_.types_.erase(name_id_);
    set_package(0);
    (void)registry_.banks_.remove(type_);
    // Original teardown releases the store name after both aliases/indices.
    registry_.strings_.release(name_id_); name_id_ = 0; closed_ = true;
}
OwnedRegistry::~OwnedRegistry() { clear(); }
StoreView* OwnedRegistry::construct(std::uint32_t type, std::uint32_t) {
    const StoreConfig empty;
    auto store = std::unique_ptr<OwnedStore>(new OwnedStore(*this, ++next_serial_, type, pending_ ? *pending_ : empty));
    auto* result = &store->view(); stores_.push_back(std::move(store)); return result;
}
void OwnedRegistry::install_forwarder(StoreView& view, std::uint32_t offset) {
    for (const auto& store : stores_) if (store && &store->view_ == &view) { store->forwarders_.push_back(offset); return; }
    throw std::logic_error("forwarder target is not owned");
}
OwnedStore& OwnedRegistry::ensure(std::uint32_t type, const StoreConfig* config) {
    pending_ = config; auto* value = banks_.ensure(type, 0, *this); pending_ = nullptr;
    for (const auto& store : stores_) if (store && &store->view_ == value) return *store;
    throw std::logic_error("bank target is not owned");
}
OwnedStore* OwnedRegistry::find(std::uint32_t type) {
    auto* value = find_store(banks_.view(), type);
    for (const auto& store : stores_) if (store && &store->view_ == value) return store.get();
    return nullptr;
}
bool OwnedRegistry::remove(std::uint32_t type) {
    auto* store = find(type); if (!store) return false;
    for (auto& item : stores_) if (item.get() == store) { item->close(); item.reset(); return true; }
    return false;
}
void OwnedRegistry::clear() {
    const auto banks = banks_.view();
    for (const auto* view : banks.primary) if (view) (void)remove(view->type);
    for (const auto* view : banks.secondary) if (view) (void)remove(view->type);
}
RegistryView OwnedRegistry::view() {
    for (const auto& store : stores_) if (store) (void)store->view();
    return types_.attach(banks_.view());
}
}
