#include "profile_store.hpp"
#include <stdexcept>
#include <limits>

namespace pvz2_recovered {
Handle32 ProfileStore::create(const Name& name, std::uint32_t creation_time) {
    if (next_handle_ == 0) throw std::overflow_error("handle space exhausted");
    const auto key = next_handle_++;
    auto& r = records_[key];
    r.name = name;
    // 007be820 -> time() -> 00721ce4 writes +0x1ec, then selects that value.
    r.data.profile_id = creation_time;
    manager.selected_id = creation_time;
    events.push_back("create");
    return {key, 1};
}
Handle32 ProfileStore::find_by_name(ProfileManagerLayout32&, const Name& name) {
    for (auto& item : records_)
        if (item.second.live && item.second.name == name) return {item.first, 1};
    return {0, 0};
}
PlayerInfoPrefix32* ProfileStore::resolve(const Handle32& h) {
    auto i = records_.find(h.low);
    return h.high == 1 && i != records_.end() && i->second.live ? &i->second.data : nullptr;
}
void ProfileStore::release(Handle32& h) { h = {0, 0}; }
void ProfileStore::set_name(PlayerInfoPrefix32& p, const Name& name) {
    for (auto& item : records_) if (&item.second.data == &p && item.second.live) {
        item.second.name = name; events.push_back("rename"); return;
    }
    throw std::invalid_argument("unknown profile");
}
void ProfileStore::sync(ProfileManagerLayout32&, int a, int b) {
    if (a != 0 || b != 0) throw std::invalid_argument("unsupported sync mode");
    // Preserve the recovered call boundary; this is an observable request only.
    events.push_back("sync-request");
}
std::int32_t ProfileStore::find_substring(const Name& name, const Name& token,
                                         std::uint32_t start, std::uint32_t count) {
    auto index = name.find(token.substr(0, count), start);
    if (index == Name::npos) return -1;
    if (index > static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max()))
        throw std::overflow_error("search position exceeds ARM string range");
    return static_cast<std::int32_t>(index);
}
std::vector<Handle32> ProfileStore::enumerate_profiles() {
    std::vector<Handle32> result;
    for (auto& item : records_) if (item.second.live) result.push_back({item.first, 1});
    return result;
}
Name ProfileStore::name_of(PlayerInfoPrefix32& p) {
    for (auto& item : records_) if (&item.second.data == &p && item.second.live) return item.second.name;
    throw std::invalid_argument("unknown profile");
}
void ProfileStore::notify_delete(const Handle32&) { events.push_back("notify-delete"); }
void ProfileStore::remove_from_store(const Handle32& h) {
    if (!resolve(h)) throw std::invalid_argument("expired handle");
    records_.at(h.low).live = false; events.push_back("remove");
}
std::size_t ProfileStore::profile_count() {
    std::size_t count = 0;
    for (auto& item : records_) if (item.second.live) ++count;
    return count;
}
}
