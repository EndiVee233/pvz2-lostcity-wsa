#include "engine_slots.hpp"
#include "engine_slot_index.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace pvz2_recovered::engine;
enum class Operation { callbacks, write, handle, grow, take, recycle, create, create_default,
    drain, describe, lookup, resolve, retain, release, refs, set_object, set_mode, mode,
    set_bit28, bit28, set_lazy, lazy };
struct Step {
    Operation op;
    std::uint32_t a, b, c, h;
    Descriptor32 descriptor;
    std::vector<std::uint32_t> result, events;
    std::uint64_t digest;
};
struct Scenario {
    const char* label;
    std::uint32_t capacity, seed, type;
    std::uint64_t initial_digest;
    std::vector<Step> steps;
};
#include "engine_slot_fixtures.inc"
struct Services final : SlotServices {
    SlotPool& pool;
    DescriptorIndex descriptors;
    std::vector<std::uint32_t> events;
    unsigned created = 0, released = 0;
    std::uint32_t mutate = 0xffffffffU;
    explicit Services(SlotPool& p) : pool(p) {}
    std::size_t callback_count(SlotEvent kind) override { return kind == SlotEvent::created ? created : released; }
    void event(unsigned kind, unsigned index, Handle h, const Slot32& s) {
        const std::uint32_t row[] = {kind, index, h.low, h.high, s.flags, s.generation,
            s.unknown14[0], pool.counts.live, static_cast<std::uint32_t>(descriptors.size())};
        events.insert(events.end(), std::begin(row), std::end(row));
    }
    void callback(SlotEvent kind, std::size_t index, Handle h) override {
        event(kind == SlotEvent::created ? 0 : 1, static_cast<unsigned>(index), h, pool.slot(decode(h).index));
        if (kind == SlotEvent::before_release && mutate != 0xffffffffU)
            pool.set_mode(h, static_cast<std::int32_t>(mutate));
    }
    void put_descriptor(const Descriptor32& d, Handle h) override { descriptors.put(d, h); }
    void erase_descriptor(const Descriptor32& d) override { descriptors.erase(d); }
    void destroy_object(std::uint32_t object) override {
        for (const auto& s : pool.slots()) {
            if (s.object_address == object) { event(2, 0, {object, 0}, s); return; }
        }
        throw std::runtime_error("destructor object not in a slot");
    }
};
struct Fingerprint {
    std::uint64_t value = 0xcbf29ce484222325ULL;
    void word(std::uint32_t x) {
        for (unsigned i = 0; i < 4; ++i) { value ^= (x >> (8 * i)) & 255U; value *= 0x100000001b3ULL; }
    }
};
std::uint64_t snapshot(const SlotPool& pool, const Services& services) {
    Fingerprint f;
    f.word(static_cast<std::uint32_t>(pool.slots().size()));
    f.word(pool.counts.free); f.word(pool.counts.live); f.word(pool.counts.deferred); f.word(pool.counts.retired);
    for (std::uint32_t i = 0; i < 4; ++i) {
        const auto anchor = SlotPool::free_list + i;
        const auto list = pool.list(anchor);
        f.word(list.empty() ? anchor : list.front()); f.word(list.empty() ? anchor : list.back());
    }
    for (const auto& s : pool.slots()) {
        for (auto v : s.unknown00) f.word(v);
        f.word(s.object_address); f.word(s.generation); f.word(s.flags);
        for (auto v : s.unknown14) f.word(v);
    }
    f.word(static_cast<std::uint32_t>(services.descriptors.size()));
    for (const auto& entry : services.descriptors.entries()) {
        for (auto word : entry.first) f.word(word);
        f.word(entry.second.low); f.word(entry.second.high);
    }
    return f.value;
}
struct NoResolvers final : LazyResolvers {
    std::size_t count() override { return 0; }
    void invoke(std::size_t, Handle) override { throw std::runtime_error("unexpected lazy callback"); }
};
struct DirectReferences final : InternReferences {
    void retain(std::uint32_t) override { throw std::runtime_error("unexpected symbolic reference"); }
    void release(std::uint32_t) override { throw std::runtime_error("unexpected symbolic reference"); }
};
unsigned integration_checks() {
    SlotPool pool(2);
    Services services(pool);
    DirectReferences references;
    NoResolvers resolvers;
    const Descriptor32 key{7, 8, 9};
    const auto first = pool.create(0x600a000U, 0, 0, &key, 1, services);
    auto view = services.descriptors.attach(pool.view());
    const auto found = handle_from_descriptor(view, key, references);
    if (found.low != first.low || found.high != first.high) throw std::runtime_error("created descriptor not found");
    if (resolve_object(view.type, view.slots, view.capacity, found, resolvers) != 0x600a000U)
        throw std::runtime_error("created object not resolved");
    pool.grow(300);
    view = services.descriptors.attach(pool.view());
    const auto moved = handle_from_descriptor(view, key, references);
    if (resolve_object(view.type, view.slots, view.capacity, moved, resolvers) != 0x600a000U)
        throw std::runtime_error("growth lost object lookup");
    pool.release(first, services);
    view = services.descriptors.attach(pool.view());
    if (lookup_slot(view.type, view.slots, view.capacity, first)) throw std::runtime_error("released handle stayed valid");
    const auto missing = handle_from_descriptor(view, key, references);
    if (missing.low || missing.high) throw std::runtime_error("released descriptor stayed indexed");
    const auto second = pool.create(0x600a020U, 1, 0, &key, 1, services);
    if (second.low == first.low && second.high == first.high) throw std::runtime_error("reused slot retained old generation");
    services.events.clear();
    pool.release(second, services);
    if (!services.events.empty() || pool.counts.deferred != 1) throw std::runtime_error("deferred object destroyed too soon");
    pool.drain_deferred(services);
    if (services.events.size() != 9 || services.events[0] != 2 || services.events[2] != 0x600a020U || pool.counts.deferred)
        throw std::runtime_error("deferred object not destroyed");
    return 8;
}
int main() {
    unsigned count = 0, number = 0;
    const char* label = "initialization";
    try {
        for (const auto& sc : scenarios) {
            label = sc.label; number = 0;
            SlotPool pool(sc.type);
            Services services(pool);
            NoResolvers resolvers;
            std::array<Handle, 8> handles{};
            if (sc.capacity) pool.grow(sc.capacity);
            for (std::uint32_t i = 0; i < sc.seed; ++i)
                if (pool.take_slot() != i) throw std::runtime_error("seed order differs");
            if (snapshot(pool, services) != sc.initial_digest) throw std::runtime_error("initial state differs from ARM");
            for (const auto& s : sc.steps) {
                const auto h = handles[s.h];
                std::vector<std::uint32_t> result;
                services.events.clear();
                auto view = pool.view();
                switch (s.op) {
                case Operation::callbacks: services.created = s.a; services.released = s.b; services.mutate = s.c; break;
                case Operation::write: {
                    auto& slot = pool.slot(s.a);
                    switch (s.b) {
                    case 2: slot.object_address = s.c; break;
                    case 3: slot.generation = s.c; break;
                    case 4: slot.flags = s.c; break;
                    default: throw std::runtime_error("unsupported fixture write");
                    }
                    break;
                }
                case Operation::handle: handles[s.h] = {s.a, s.b}; break;
                case Operation::grow: pool.grow(s.a); break;
                case Operation::take: result = {pool.take_slot()}; break;
                case Operation::recycle: pool.recycle(s.a, s.b != 0); break;
                case Operation::create:
                case Operation::create_default: {
                    const auto value = pool.create(s.a, static_cast<std::int32_t>(s.b), static_cast<std::uint8_t>(s.c),
                        s.op == Operation::create ? &s.descriptor : nullptr, 0x87654321U, services);
                    handles[s.h] = value; result = {value.low, value.high}; break;
                }
                case Operation::drain: pool.drain_deferred(services); break;
                case Operation::retain: pool.retain(h); break;
                case Operation::release: result = {pool.release(h, services)}; break;
                case Operation::refs: result = {pool.reference_count(h)}; break;
                case Operation::lookup: result = {lookup_slot(view.type, view.slots, view.capacity, h) != nullptr}; break;
                case Operation::describe: {
                    const auto d = describe_handle(view, h); result.assign(d.begin(), d.end()); break;
                }
                case Operation::resolve: result = {resolve_object(view.type, view.slots, view.capacity, h, resolvers)}; break;
                case Operation::set_object: result = {pool.set_object(h, s.a)}; break;
                case Operation::set_mode: result = {pool.set_mode(h, static_cast<std::int32_t>(s.a))}; break;
                case Operation::mode: result = {pool.mode(h)}; break;
                case Operation::set_bit28: result = {pool.set_bit28(h, static_cast<std::int32_t>(s.a))}; break;
                case Operation::bit28: result = {pool.bit28(h)}; break;
                case Operation::set_lazy: result = {pool.set_lazy(h, static_cast<std::int32_t>(s.a))}; break;
                case Operation::lazy: result = {pool.lazy(h)}; break;
                }
                if (result != s.result) throw std::runtime_error("return value differs from ARM");
                if (services.events != s.events) throw std::runtime_error("callback/destructor observations differ from ARM");
                if (snapshot(pool, services) != s.digest) throw std::runtime_error("normalized slot/index state differs from ARM");
                ++count; ++number;
            }
        }
        std::cout << "PASS " << count << " engine slot ARM differential checkpoints\n";
        label = "owned-slot/descriptor integration"; number = 0;
        std::cout << "PASS " << integration_checks() << " owned-slot integration checks\n";
    } catch (const std::exception& e) {
        std::cerr << label << '/' << number << ": " << e.what() << '\n';
        return 1;
    }
}
