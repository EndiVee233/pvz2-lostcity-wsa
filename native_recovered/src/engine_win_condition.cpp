#include "engine_win_condition.hpp"
namespace pvz2_recovered::engine {
bool zombies_dead_condition(WinConditionServices& s) {
    // Host snapshot stores flags rather than ARM32 pointers to Board entities.
    // Snapshot/allocation ownership is supplied by the host adapter.
    const auto flags=s.snapshot_entity_flags();
    for(auto value:flags)if(value&2U)return false;
    auto objects=s.enumerate_type_0x25();
    for(auto value:objects) {
        value=s.copy_handle(value);
        auto direct=s.normalize(value);
        std::uint32_t object=0;
        if(direct.low || direct.high) {
            const auto store=s.find_store(decode(direct).store);
            if(store)object=s.resolve(store,direct);
        }
        s.release_handle(direct);
        if(object && s.predicate_d4(object)) {
            s.release_handle(value);s.release_enumeration();return false;
        }
        s.release_handle(value);
    }
    s.release_enumeration();return true;
}
}
