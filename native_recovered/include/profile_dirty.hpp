#pragma once
#include "profile_lifecycle.hpp"
namespace pvz2_recovered {
// Dependencies with known call boundaries but not yet recovered implementations.
struct DirtyServices {
    virtual ~DirtyServices() = default;
    virtual float clock_value() = 0;
    virtual std::int32_t service_time() = 0;
    virtual std::int32_t system_time() = 0;
    virtual bool global_save_blocked() = 0;
    virtual void request_save() = 0;
};
void update_modified_time(PlayerInfoPrefix32&, DirtyServices&); // 0071a924
void request_profile_save(ProfileManagerLayout32&, DirtyServices&); // 007b8ed0
bool mark_profile_changed(PlayerInfoPrefix32&, ProfileManagerLayout32&, DirtyServices&); // 007210c4
void set_profile_creation_time(PlayerInfoPrefix32&, std::uint32_t,
                               ProfileManagerLayout32&, DirtyServices&); // 00721ce4
}
