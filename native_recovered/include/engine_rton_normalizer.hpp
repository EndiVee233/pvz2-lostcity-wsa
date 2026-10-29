#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace pvz2_recovered::engine {
class InternPool;
struct NormalizedRton {
    bool success = false;
    std::size_t input_consumed = 0;
    std::vector<std::uint8_t> bytes;
    std::vector<std::pair<std::string, std::uint32_t>> narrow_strings;
    std::vector<std::pair<std::u32string, std::uint32_t>> wide_strings;
};
// 01202a74/012028a0/01201398: fresh output stream, raw format 0 -> indexed
// format 1. Returns original partial output on header/trailer failure.
// Host bounds/cache/recursion violations throw; original assumes valid input.
// Logical string/offset tables replace the original COW and tree memory ABI.
// Optional ambient pool restores transient reference-wire interning effects
// needed when normalization and object loading share the original global pool.
NormalizedRton normalize_rton(std::vector<std::uint8_t> input, InternPool* ambient_pool = nullptr);
}
