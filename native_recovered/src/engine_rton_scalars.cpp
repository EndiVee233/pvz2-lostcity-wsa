#include "engine_rton_reader.hpp"
#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <stdexcept>

namespace pvz2_recovered::engine {
namespace {
std::uint32_t decimal32(const std::string& text) {
    errno = 0; const auto value = std::strtoll(text.c_str(), nullptr, 10);
    // C-library overflow handling is not claimed equivalent across Android and
    // host runtimes. The covered decimal domain is the signed32 range.
    if (errno == ERANGE || value < -2147483648LL || value > 2147483647LL) throw std::out_of_range("RTON decimal32 coercion range");
    return static_cast<std::uint32_t>(value);
}
std::uint32_t convert_float(double value, unsigned mode) {
    if (mode == 2) return value != 0.0 ? 1U : 0U;
    if (std::isnan(value)) return 0;
    if (mode == 1) {
        if (value <= 0) return 0;
        if (value >= 4294967295.0) return 0xffffffffU;
        return static_cast<std::uint32_t>(value);
    }
    if (value >= 2147483647.0) return 0x7fffffffU;
    if (value <= -2147483648.0) return 0x80000000U;
    return static_cast<std::uint32_t>(static_cast<std::int32_t>(value));
}
}
std::uint32_t IndexedRtonReader::scalar32(std::uint32_t value, std::uint32_t fallback, unsigned mode) {
    if (!value) return fallback;
    seek(value); const auto tag = input_.byte();
    switch (tag) {
    case 8: case 10: case 0xbc: {
        const auto b = input_.byte(); if (mode == 2) return b != 0;
        return tag != 10 && (b & 0x80U) ? 0xffffff00U | b : b;
    }
    case 0x10: case 0x12: {
        const auto lo = input_.byte(); const auto bits = lo | (static_cast<std::uint32_t>(input_.byte()) << 8);
        if (mode == 2) return bits != 0;
        return tag == 0x10 && (bits & 0x8000U) ? 0xffff0000U | bits : bits;
    }
    case 0x20: case 0x26: {const auto bits = le32(); return mode == 2 ? static_cast<std::uint32_t>(bits != 0) : bits;}
    case 0x40: case 0x46: {const auto lo = le32(); const auto hi = le32(); return mode == 2 ? static_cast<std::uint32_t>((lo | hi) != 0) : lo;}
    case 0x22: {
        const auto bits = le32(); float number; static_assert(sizeof(number) == sizeof(bits)); std::memcpy(&number, &bits, sizeof(number));
        return convert_float(number, mode);
    }
    case 0x42: {
        const auto lo = le32(); const auto bits = (static_cast<std::uint64_t>(le32()) << 32) | lo;
        double number; static_assert(sizeof(number) == sizeof(bits)); std::memcpy(&number, &bits, sizeof(number)); return convert_float(number, mode);
    }
    case 0xb0: case 0xb1: case 0xb2: case 0xb3: {
        const auto stored = le32(); auto offset = tag == 0xb0 || tag == 0xb2 ? position() : stored;
        if (tag == 0xb0 || tag == 0xb1) {
            if (mode == 2) {const auto c = at(offset); return c != 0 && c != '0';}
            return decimal32(narrow_text_at(offset));
        }
        std::string low_bytes;
        for (;;) {
            std::uint32_t c = 0; for (unsigned i = 0; i < 4; ++i) c |= static_cast<std::uint32_t>(at(offset + i)) << (8 * i);
            if (mode == 2) return c != 0 && c != 0x30U;
            if (!c) break;
            low_bytes.push_back(static_cast<char>(c & 255U)); offset += 4;
        }
        return decimal32(low_bytes);
    }
    case 0xba: throw std::logic_error("RTON RTID scalar coercion requires unrecovered object resolver");
    default: return fallback;
    }
}
std::uint32_t IndexedRtonReader::scalar_int32_bits(std::uint32_t value, std::uint32_t fallback) { return scalar32(value, fallback, 0); }
std::uint32_t IndexedRtonReader::scalar_uint32(std::uint32_t value, std::uint32_t fallback) { return scalar32(value, fallback, 1); }
std::uint32_t IndexedRtonReader::scalar_boolean_bits(std::uint32_t value, std::uint32_t fallback) { return scalar32(value, fallback, 2); }
std::uint32_t IndexedRtonReader::scalar_float32_bits(std::uint32_t value, std::uint32_t fallback) {
    if (!value) return fallback;
    seek(value); const auto tag = input_.byte(); float number;
    switch (tag) {
    case 8: case 0xbc: number = static_cast<float>(static_cast<std::int8_t>(input_.byte())); break;
    case 10: number = static_cast<float>(input_.byte()); break;
    case 0x10: case 0x12: {
        const auto lo = input_.byte(); const auto bits = lo | (static_cast<std::uint32_t>(input_.byte()) << 8);
        number = tag == 0x10 ? static_cast<float>(static_cast<std::int16_t>(bits)) : static_cast<float>(bits); break;
    }
    case 0x20: number = static_cast<float>(static_cast<std::int32_t>(le32())); break;
    case 0x26: number = static_cast<float>(le32()); break;
    case 0x40: case 0x46: {
        const auto lo = le32(); const auto bits = (static_cast<std::uint64_t>(le32()) << 32) | lo;
        number = tag == 0x40 ? static_cast<float>(static_cast<std::int64_t>(bits)) : static_cast<float>(bits); break;
    }
    case 0x22: return le32();
    case 0x42: {
        const auto lo = le32(); const auto bits = (static_cast<std::uint64_t>(le32()) << 32) | lo;
        // Original __truncdfsf2 canonicalizes every double NaN to positive qNaN.
        if ((bits & 0x7ff0000000000000ULL) == 0x7ff0000000000000ULL && (bits & 0xfffffffffffffULL)) return 0x7fc00000U;
        double source; std::memcpy(&source, &bits, sizeof(source)); number = static_cast<float>(source); break;
    }
    case 0xb0: case 0xb1: {
        const auto stored = le32(); const auto offset = tag == 0xb0 ? position() : stored;
        const auto text = narrow_text_at(offset); const auto start = text.find_first_not_of(" \t\n\r\v\f");
        auto first = start == std::string::npos ? text.size() : start;
        if (first < text.size() && (text[first] == '+' || text[first] == '-')) ++first;
        if (first < text.size() && ((text[first] == '0' && first + 1 < text.size() && (text[first + 1] == 'x' || text[first + 1] == 'X')) || text[first] == 'i' || text[first] == 'I' || text[first] == 'n' || text[first] == 'N')) throw std::logic_error("RTON non-decimal float text libc parity not covered");
        number = static_cast<float>(std::strtod(text.c_str(), nullptr)); break;
    }
    case 0xb2: case 0xb3: throw std::logic_error("RTON wide float text coercion not recovered");
    case 0xba: throw std::logic_error("RTON RTID float coercion not recovered");
    default: return fallback;
    }
    std::uint32_t bits; std::memcpy(&bits, &number, sizeof(bits)); return bits;
}
}
