#include "engine_intern.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
using namespace pvz2_recovered::engine;
namespace pvz2_recovered::engine {
struct InternPoolFixtureAccess {
    static void write_count(InternPool& pool, std::uint32_t id, std::uint32_t value) { pool.entry(id).references = value; }
};
}
enum class Operation { intern, lookup, acquire, assign, drop, retain, release, text, write_count, handle, canonical, resolve };
struct Step {
    Operation op;
    bool null_text;
    std::vector<std::uint32_t> text;
    std::uint32_t a, b, h, j;
    std::vector<std::uint32_t> result, state;
};
struct Scenario { const char* label; std::vector<std::uint32_t> initial; std::vector<Step> steps; };
#include "engine_intern_fixtures.inc"
void compare(const std::vector<std::uint32_t>& actual, const std::vector<std::uint32_t>& expected) {
    if (actual.size() != expected.size()) throw std::runtime_error("intern state length differs from ARM");
    for (std::size_t i = 0; i < actual.size(); ++i)
        if (actual[i] != expected[i]) throw std::runtime_error("intern field " + std::to_string(i) +
            " differs: actual=" + std::to_string(actual[i]) + " ARM=" + std::to_string(expected[i]));
}
void append_text(std::vector<std::uint32_t>& result, const std::u32string& text) {
    result.push_back(static_cast<std::uint32_t>(text.size()));
    for (auto c : text) result.push_back(static_cast<std::uint32_t>(c));
}
int main() {
    unsigned checks = 0, number = 0;
    const char* label = "initialization";
    try {
        for (const auto& sc : scenarios) {
            label = sc.label; number = 0;
            InternPool pool;
            std::array<InternValue, 64> values{};
            Handle handle{};
            Slot32 slot{}; slot.object_address = 0x12345678U; slot.generation = 1; slot.flags = 1;
            slot.unknown14[0] = 4; slot.unknown14[1] = 5; slot.unknown14[2] = 6;
            DescriptorNode descriptor{nullptr, nullptr, {4,5,6}, {0x10000,2U<<17}};
            ObjectNameNode object_name{nullptr, nullptr, 2, {4,5,6}};
            StoreView store{2, &slot, 1, &descriptor, &object_name, nullptr};
            StoreNameNode store_name{nullptr, nullptr, 1, 2};
            RegistryView registry{{}, {nullptr, nullptr, &store}, &store_name};
            pool.validate(); compare(pool.normalized_state(), sc.initial);
            for (const auto& s : sc.steps) {
                std::u32string query;
                for (auto c : s.text) query.push_back(static_cast<char32_t>(c));
                const auto* input = s.null_text ? nullptr : query.c_str();
                auto& value = values[s.h];
                std::vector<std::uint32_t> result;
                switch (s.op) {
                case Operation::intern: result = {pool.intern(input)}; break;
                case Operation::lookup: result = {pool.find_id(input)}; break;
                case Operation::acquire:
                    value = pool.acquire(input); result = {value.id}; append_text(result, pool.text(value.text_token)); break;
                case Operation::assign:
                    pool.assign_value(value, values[s.j]); result = {value.id}; append_text(result, pool.text(value.text_token)); break;
                case Operation::drop: result = {pool.release_value(value)}; break;
                case Operation::retain: pool.retain(value.id); break;
                case Operation::release: result = {pool.release_counted(value.id)}; break;
                case Operation::text: append_text(result, pool.text(pool.text_address(value.id))); break;
                case Operation::write_count: InternPoolFixtureAccess::write_count(pool, value.id, s.a); break;
                case Operation::handle:
                    assign_handle(handle, {s.a,s.b}, pool); result = {handle.low,handle.high}; break;
                case Operation::canonical: {
                    const auto h = canonical_handle(registry, handle, pool); result = {h.low,h.high}; break;
                }
                case Operation::resolve: result = {resolve_registered_object(registry, handle, pool)}; break;
                }
                if (result != s.result) throw std::runtime_error("intern/text/handle result differs from ARM");
                pool.validate(); compare(pool.normalized_state(), s.state);
                ++checks; ++number;
            }
        }
        std::cout << "PASS " << checks << " engine intern ARM full-state checkpoints\n";
    } catch (const std::exception& error) {
        std::cerr << label << '/' << number << ": " << error.what() << '\n';
        return 1;
    }
}
