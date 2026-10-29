#pragma once
#include "engine_handles.hpp"
namespace pvz2_recovered::engine {
struct WinConditionServices {
    virtual ~WinConditionServices() = default;
    virtual std::vector<std::uint32_t> snapshot_entity_flags() = 0;
    virtual std::vector<Handle> enumerate_type_0x25() = 0;
    virtual Handle copy_handle(Handle) = 0;
    virtual Handle normalize(Handle) = 0;
    virtual std::uint32_t find_store(std::uint32_t type) = 0;
    virtual std::uint32_t resolve(std::uint32_t store, Handle) = 0;
    virtual bool predicate_d4(std::uint32_t object) = 0;
    virtual void release_handle(Handle&) = 0;
    virtual void release_enumeration() = 0;
};
// 00b78c70. A readiness predicate, not the victory transition/event machinery.
bool zombies_dead_condition(WinConditionServices&);
}
