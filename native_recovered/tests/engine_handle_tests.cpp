#include "engine_handles.hpp"
#include <iostream>
#include <stdexcept>
#include <utility>
using namespace pvz2_recovered::engine;
struct SlotCase { std::uint32_t low, high, type, generation; bool valid; };
struct BankCase { std::uint32_t encoded, result; };
struct AssignCase { Handle old_value, new_value; std::vector<std::pair<bool, std::uint32_t>> events; };
struct ResolveCase { bool missing, ready, lazy; unsigned callbacks, result, invoked; };
#include "engine_handle_fixtures.inc"
struct Pool final : InternReferences {
    std::vector<std::pair<bool, std::uint32_t>> events;
    void retain(std::uint32_t id) override { events.emplace_back(true, id); }
    void release(std::uint32_t id) override { events.emplace_back(false, id); }
};
struct Resolvers final : LazyResolvers {
    Slot32& slot;
    unsigned callbacks, invoked = 0;
    Resolvers(Slot32& s, unsigned c) : slot(s), callbacks(c) {}
    std::size_t count() override { return callbacks; }
    void invoke(std::size_t i, Handle h) override {
        if (i != invoked || h.low != 2 || h.high != (45U << 17)) throw std::runtime_error("callback argument mismatch");
        ++invoked; slot.object_address = 0x12345678U + static_cast<unsigned>(i);
    }
};
int main() {
    unsigned count = 0;
    try {
        for (auto c : slot_cases) {
            Slot32 slots[3]{}; slots[2].generation = c.generation;
            auto* actual = lookup_slot(c.type, slots, 3, {c.low, c.high});
            if (actual != (c.valid ? &slots[2] : nullptr)) throw std::runtime_error("slot result differs from ARM");
            ++count;
        }
        for (auto c : bank_cases) {
            if (registry_store({111, 222}, {333, 444}, c.encoded) != c.result)
                throw std::runtime_error("registry result differs from ARM");
            ++count;
        }
        for (const auto& c : assign_cases) {
            Pool pool; auto handle = c.old_value;
            assign_handle(handle, c.new_value, pool);
            if (handle.low != c.new_value.low || handle.high != c.new_value.high || pool.events != c.events)
                throw std::runtime_error("handle assignment differs from ARM");
            ++count;
        }
        for (auto c : resolve_cases) {
            Slot32 slots[3]{};
            slots[2].object_address = c.ready ? 0x12345678U : 0;
            slots[2].flags = c.lazy ? 0x08000000U : 0;
            Resolvers resolvers(slots[2], c.callbacks);
            auto result = resolve_object(c.missing ? 46 : 45, slots, 3, {2, 45U << 17}, resolvers);
            if (result != c.result || resolvers.invoked != c.invoked) throw std::runtime_error("lazy result differs from ARM");
            ++count;
        }
        std::cout << "PASS " << count << " engine handle ARM differential checks\n";
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
