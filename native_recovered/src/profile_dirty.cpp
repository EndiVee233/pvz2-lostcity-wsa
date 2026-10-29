#include "profile_dirty.hpp"
namespace pvz2_recovered {
void update_modified_time(PlayerInfoPrefix32& p, DirtyServices& services) {
    const auto t = services.service_time();
    p.modified_time = t > 0 ? t : services.system_time();
}
void request_profile_save(ProfileManagerLayout32& m, DirtyServices& services) {
    m.pending_save = 1;
    if (m.save_blocked == 0 && !services.global_save_blocked()) services.request_save();
}
bool mark_profile_changed(PlayerInfoPrefix32& p, ProfileManagerLayout32& m,
                           DirtyServices& services) {
    // Preserve ordered comparisons and short circuit: NaN does not mark dirty;
    // a negative value must not consult the clock singleton.
    if (!(p.pending_time < 0.0f) && !(p.pending_time < services.clock_value())) return false;
    p.pending_time = -1.0f;
    update_modified_time(p, services);
    request_profile_save(m, services);
    return true; // Host diagnostic; original ARM function returns void.
}
void set_profile_creation_time(PlayerInfoPrefix32& p, std::uint32_t t,
                               ProfileManagerLayout32& m, DirtyServices& services) {
    p.profile_id = t;
    mark_profile_changed(p, m, services);
}
}
