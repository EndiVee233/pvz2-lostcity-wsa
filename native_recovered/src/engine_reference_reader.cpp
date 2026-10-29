#include "engine_rton_reader.hpp"
#include "engine_store.hpp"
#include <stdexcept>

namespace pvz2_recovered::engine {
Handle IndexedRtonReader::reference_value(std::uint32_t value, OwnedRegistry& registry, InternPool& strings, std::uint32_t current_type) {
    if (!value) return {};
    seek(value); const auto tag = input_.byte();
    if (tag != 0xba) {
        if (tag >= 0xb0 && tag <= 0xb3) throw std::logic_error("text RTID parser not recovered");
        return {}; // Covered numeric/boolean/default-to-empty weak pointer path.
    }
    const auto kind = input_.byte();
    if (kind == 0 || kind > 3) return {};
    if (kind == 1 || kind == 2) {
        OwnedStore* store = registry.find(current_type);
        if (kind == 2) {
            const auto text = input_.utf8_string(); const auto name = strings.acquire(text.c_str());
            auto* view = find_named_store(registry.view(), name.id); store = view ? registry.find(view->type) : nullptr;
            strings.release(name.id);
        }
        const auto first = input_.varuint32(); const auto second = input_.varuint32(); const auto third = le32();
        if (!store || !(first | second | third)) return {};
        return handle_from_descriptor(store->view(), {first, second, third}, strings);
    }
    const auto package = input_.utf8_string(); const auto name = input_.utf8_string();
    Handle result;
    if (package == U".") {
        auto* store = registry.find(current_type);
        if (!store) throw std::logic_error("relative RTID requires current store");
        const auto object = strings.acquire(name.c_str()); const auto id = store->effective_name_id();
        assign_handle(result, {object.id | (id << 31), (id >> 1) | 0x80000000U}, strings);
        strings.release(object.id);
    } else {
        const auto pkg = strings.acquire(package.c_str()); const auto object = strings.acquire(name.c_str());
        assign_handle(result, {object.id | (pkg.id << 31), (pkg.id >> 1) | 0x80000000U}, strings);
        strings.release(object.id); strings.release(pkg.id);
    }
    return result;
}
}
