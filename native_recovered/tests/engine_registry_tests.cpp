#include "engine_registry.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
using namespace pvz2_recovered::engine;
enum class Function { named_store, describe, descriptor, name, canonical, object };
enum class Operation { retain, release, text, callback };
using Event = std::pair<Operation, std::uint32_t>;
struct RegistryCase {
    Function function;
    const char* label;
    std::uint32_t query;
    Descriptor32 descriptor;
    Handle source;
    std::uint32_t base_index, generation, type, bank_code, empty;
    int mismatch;
    unsigned callbacks;
    bool lazy, ready;
    Descriptor32 expected;
    std::vector<Event> events;
};
#include "engine_registry_fixtures.inc"
const std::uint32_t keys[] = {0, 1, 7, 0x7fffffffU, 0x80000000U, 0xfffffffeU, 0xffffffffU};
const Descriptor32 descriptors[] = {{1,5,9}, {1,5,0x80000000U}, {1,6,0}, {4,5,6},
    {0x80000000U,0,1}, {0xffffffffU,0,1}, {0xffffffffU,0xffffffffU,0xffffffffU}};
// Only fixture construction uses this encoder; expected handles are captured ARM outputs.
Handle fixture_handle(std::uint32_t index, std::uint32_t generation, std::uint32_t type) {
    if (index < 0x10000U) return {index | (generation << 16), (type << 17) | (generation >> 16)};
    return {index | (generation << 24), (type << 17) | (generation >> 8) | 0x10000U};
}
struct Pool final : InternStrings {
    std::vector<Event> events;
    void retain(std::uint32_t id) override { events.emplace_back(Operation::retain, id); }
    void release(std::uint32_t id) override { events.emplace_back(Operation::release, id); }
    std::uint32_t text_address(std::uint32_t id) override {
        events.emplace_back(Operation::text, id);
        return 0x600f000;
    }
};
struct Resolvers final : LazyResolvers {
    Slot32& slot;
    unsigned callbacks;
    Handle expected_handle;
    std::vector<Event>& events;
    Resolvers(Slot32& s, unsigned c, Handle h, std::vector<Event>& e)
        : slot(s), callbacks(c), expected_handle(h), events(e) {}
    std::size_t count() override { return callbacks; }
    void invoke(std::size_t index, Handle h) override {
        if (h.low != expected_handle.low || h.high != expected_handle.high)
            throw std::runtime_error("lazy callback handle differs from ARM");
        events.emplace_back(Operation::callback, static_cast<std::uint32_t>(index));
        slot.object_address = 0x12345678U + static_cast<std::uint32_t>(index);
    }
};
template<class Node> const Node* tree(std::array<Node, 7>& nodes, unsigned begin = 0, unsigned end = 7) {
    if (begin == end) return nullptr;
    const auto middle = (begin + end) / 2;
    nodes[middle].left = tree(nodes, begin, middle);
    nodes[middle].right = tree(nodes, middle + 1, end);
    return &nodes[middle];
}
int main() {
    unsigned count = 0;
    const char* label = "initialization";
    try {
        for (const auto& c : registry_cases) {
            label = c.label;
            Pool pool;
            std::vector<Slot32> slots(c.base_index + 7);
            std::array<StoreNameNode, 7> stores{};
            std::array<ObjectNameNode, 7> names{};
            std::array<DescriptorNode, 7> entries{};
            for (unsigned i = 0; i < 7; ++i) {
                stores[i].name = keys[i]; stores[i].encoded_type = c.bank_code;
                names[i].name = keys[i]; names[i].descriptor = descriptors[i];
                entries[i].key = descriptors[i];
                entries[i].handle = fixture_handle(c.base_index + i, c.generation, c.type);
                auto& slot = slots[c.base_index + i];
                slot.generation = c.generation;
                slot.object_address = c.ready ? 0x12345678U : 0;
                slot.flags = c.lazy ? 0x08000000U : 0;
                for (unsigned word = 0; word < 3; ++word) slot.unknown14[word] = descriptors[i][word];
                if (i == 3 && c.mismatch >= 0) slot.unknown14[c.mismatch] ^= 1;
            }
            Resolvers resolvers(slots[c.base_index + 3], c.callbacks,
                fixture_handle(c.base_index + 3, c.generation, c.type), pool.events);
            StoreView store{c.type, slots.data(), slots.size(), tree(entries), tree(names), &resolvers};
            RegistryView registry{{nullptr, &store}, {nullptr, nullptr, &store}, tree(stores)};
            if (c.empty & 1) registry.names = nullptr;
            if (c.empty & 2) store.names = nullptr;
            if (c.empty & 4) store.descriptors = nullptr;
            Descriptor32 result{};
            Handle handle{};
            switch (c.function) {
            case Function::named_store: {
                const auto* found = find_named_store(registry, c.query);
                if (found && found != &store) throw std::runtime_error("unknown store pointer");
                result[0] = found ? 0x6001000U : 0;
                break;
            }
            case Function::describe: result = describe_handle(store, c.source); break;
            case Function::descriptor: handle = handle_from_descriptor(store, c.descriptor, pool); break;
            case Function::name: handle = handle_from_name(store, c.query, pool); break;
            case Function::canonical: handle = canonical_handle(registry, c.source, pool); break;
            case Function::object: result[0] = resolve_registered_object(registry, c.source, pool); break;
            }
            if (c.function == Function::descriptor || c.function == Function::name || c.function == Function::canonical)
                result = {handle.low, handle.high, 0};
            if (result != c.expected) throw std::runtime_error("return value differs from ARM");
            if (pool.events != c.events) throw std::runtime_error("reference/text/callback order differs from ARM");
            ++count;
        }
        std::cout << "PASS " << count << " engine registry ARM differential checks\n";
    } catch (const std::exception& error) {
        std::cerr << label << ": " << error.what() << '\n';
        return 1;
    }
}
