#pragma once
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace pvz2_recovered::engine {
class InternPool;
class OwnedStore;
// Recovered append-only RTON field writer. Owns bytes and a logical narrow
// string cache; does not reproduce the Android stream/COW/tree memory ABI.
class RtonWriter {
    std::vector<std::uint8_t> bytes_;
    std::vector<std::pair<std::string, std::uint32_t>> cache_;
    void key(std::string_view);
    void raw_string(std::string_view);
public:
    const std::vector<std::uint8_t>& bytes() const { return bytes_; }
    const std::vector<std::pair<std::string, std::uint32_t>>& string_cache() const { return cache_; }
    void byte(std::uint8_t value) { bytes_.push_back(value); }
    // 011fd650, 01200a88: input preserves the original 32-bit bit pattern.
    void varuint(std::uint32_t);
    void integer(std::string_view key, std::uint32_t bits);
    // 012000d4 / 01200230: cached strings use 90/91; raw strings use 81.
    void string(std::string_view key, std::string_view value, bool cached = false);
    // 01205280 mode 0 / 011fd9d4: stops at wide NUL, uses original UTF-8 rules.
    void wide_string(std::string_view key, std::u32string_view value);
    void boolean(std::string_view key, std::uint8_t raw_value);
    // 011e6b70: fields only, without a document header or root terminator.
    void store_metadata(const OwnedStore&, const InternPool&);
};
}
