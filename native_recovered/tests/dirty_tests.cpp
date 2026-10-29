#include "profile_dirty.hpp"
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace pvz2_recovered;
struct Services final : DirtyServices {
    unsigned clock_reads = 0, service_reads = 0, system_reads = 0, requests = 0;
    int t = 999;
    bool blocked = false;
    float clock_value() override { ++clock_reads; return 10; }
    std::int32_t service_time() override { ++service_reads; return t; }
    std::int32_t system_time() override { ++system_reads; return 123456; }
    bool global_save_blocked() override { return blocked; }
    void request_save() override { ++requests; }
};
static unsigned checks = 0;
static void check(bool ok) { if (!ok) throw std::runtime_error("dirty state mismatch"); ++checks; }
int main() {
    try {
        for (float value : {-1.0f, 0.0f, 9.0f, 10.0f, 11.0f,
                            std::numeric_limits<float>::quiet_NaN(),
                            std::numeric_limits<float>::infinity(),
                            -std::numeric_limits<float>::infinity()}) {
            PlayerInfoPrefix32 p{}; ProfileManagerLayout32 m{}; Services s;
            p.pending_time = value; p.modified_time = 42;
            const bool changed = value < 0 || value < 10;
            check(mark_profile_changed(p, m, s) == changed);
            check(s.clock_reads == unsigned(!(value < 0)));
            check(m.pending_save == unsigned(changed) && s.requests == unsigned(changed));
            check(p.modified_time == (changed ? 999 : 42));
        }
        for (int t : {-1, 0, 999}) {
            PlayerInfoPrefix32 p{}; Services s; s.t = t;
            update_modified_time(p, s);
            check(p.modified_time == (t > 0 ? t : 123456));
            check(s.system_reads == unsigned(t <= 0));
        }
        for (int local : {0, 1}) for (bool global : {false, true}) {
            ProfileManagerLayout32 m{}; Services s; m.save_blocked = static_cast<std::uint8_t>(local); s.blocked = global;
            request_profile_save(m, s);
            check(m.pending_save == 1);
            check(s.requests == unsigned(!local && !global));
        }
        PlayerInfoPrefix32 p{}; ProfileManagerLayout32 m{}; Services s;
        set_profile_creation_time(p, 777, m, s);
        check(p.profile_id == 777 && p.modified_time == 999 && s.requests == 1);
        std::cout << "PASS " << checks << " dirty-state checks\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
