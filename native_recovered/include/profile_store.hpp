#pragma once
#include "profile_lifecycle.hpp"
#include <map>

namespace pvz2_recovered {
// Standalone host implementation. It does not decode pp.dat or implement the
// original registry, cloud service, engine RTTI or Android binary ABI.
class ProfileStore final : public Backend {
    struct Record { PlayerInfoPrefix32 data{}; Name name; bool live = true; };
    std::map<std::uint32_t, Record> records_;
    std::uint32_t next_handle_ = 1;
public:
    ProfileManagerLayout32 manager{};
    std::vector<std::string> events;
    Handle32 create(const Name&, std::uint32_t creation_time);
    Handle32 find_by_name(ProfileManagerLayout32&, const Name&) override;
    PlayerInfoPrefix32* resolve(const Handle32&) override;
    void release(Handle32&) override;
    void set_name(PlayerInfoPrefix32&, const Name&) override;
    void sync(ProfileManagerLayout32&, int, int) override;
    std::int32_t find_substring(const Name&, const Name&, std::uint32_t, std::uint32_t) override;
    std::vector<Handle32> enumerate_profiles() override;
    Name name_of(PlayerInfoPrefix32&) override;
    void notify_delete(const Handle32&) override;
    void remove_from_store(const Handle32&) override;
    std::size_t profile_count() override;
};
}
