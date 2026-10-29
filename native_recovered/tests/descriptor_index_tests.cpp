#include "engine_slot_index.hpp"
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
using namespace pvz2_recovered::engine;
enum class Operation { put, insert, erase, find };
struct IndexStep {
    Operation operation;
    Descriptor32 key;
    Handle value;
    bool has_hint;
    Descriptor32 hint;
    std::vector<std::uint32_t> result, state;
};
struct IndexScenario {
    const char* label;
    std::vector<std::uint32_t> initial;
    std::vector<IndexStep> steps;
};
#include "descriptor_index_fixtures.inc"
void compare(const std::vector<std::uint32_t>& actual, const std::vector<std::uint32_t>& expected) {
    if (actual.size() != expected.size()) throw std::runtime_error("node state size differs from ARM");
    for (std::size_t i = 0; i < actual.size(); ++i) {
        if (actual[i] != expected[i]) throw std::runtime_error("node field " + std::to_string(i) +
            " differs: actual=" + std::to_string(actual[i]) + " ARM=" + std::to_string(expected[i]));
    }
}
int main() {
    const char* label = "initialization";
    unsigned number = 0, checks = 0;
    try {
        for (const auto& sc : index_scenarios) {
            label = sc.label; number = 0;
            DescriptorIndex index;
            index.validate();
            compare(index.normalized_state(), sc.initial);
            for (const auto& step : sc.steps) {
                // This map is test-only address bookkeeping, never index storage.
                std::map<Descriptor32, const Handle*> before;
                for (const auto& entry : index.entries()) before.emplace(entry.first, index.find(entry.first));
                std::vector<std::uint32_t> result;
                switch (step.operation) {
                case Operation::put: index.put(step.key, step.value); break;
                case Operation::insert: result = {index.insert_unique(step.key, step.value, step.has_hint ? &step.hint : nullptr)}; break;
                case Operation::erase: result = {index.erase(step.key)}; break;
                case Operation::find: {
                    const auto* value = index.find(step.key);
                    result = value ? std::vector<std::uint32_t>{1, value->low, value->high} : std::vector<std::uint32_t>{0};
                    break;
                }
                }
                if (result != step.result) throw std::runtime_error("return/lookup value differs from ARM");
                index.validate();
                compare(index.normalized_state(), step.state);
                for (const auto& entry : before) {
                    const auto* now = index.find(entry.first);
                    if (now && now != entry.second) throw std::runtime_error("surviving node changed address");
                }
                // attach must expose the recovered shape, not rebuild a new balanced tree.
                const auto view = index.attach({});
                if ((view.descriptors == nullptr) != (index.size() == 0)) throw std::runtime_error("index view root");
                ++number; ++checks;
            }
        }
        std::cout << "PASS " << checks << " descriptor tree ARM/Thumb exact-state checkpoints\n";
    } catch (const std::exception& error) {
        std::cerr << label << '/' << number << ": " << error.what() << '\n';
        return 1;
    }
}
