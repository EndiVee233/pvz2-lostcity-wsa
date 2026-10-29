#include "engine_rton_input.hpp"
#include <array>
#include <stdexcept>
#include <utility>

namespace pvz2_recovered::engine {
std::size_t decode_engine_utf8(const std::uint8_t* data, std::size_t size, std::uint32_t& value) {
    if (!size) return 0;
    const auto lead = static_cast<std::uint32_t>(data[0]);
    auto code = lead;
    std::size_t length = 1;
    if (lead & 0x80U) {
        if ((lead & 0xc0U) != 0xc0U) return 0;
        constexpr std::array<std::uint32_t, 5> masks{0xc0U, 0xe0U, 0xf0U, 0xf8U, 0xfcU};
        std::size_t index = 0;
        while (index < masks.size() && ((lead ^ (masks[index] << 1)) & masks[index])) ++index;
        if (!index || index == masks.size()) return 0;
        length = index + 1;
        if (size < length) return 0;
        code = lead & ~masks[index];
        for (std::size_t i = 1; i < length; ++i) {
            if ((data[i] & 0xc0U) != 0x80U) return 0;
            code = (code << 6) | (data[i] & 0x3fU);
        }
        if (length == 2 && !(lead & 0x3eU)) return 0;
        if (length == 3 && !(lead & 0x1fU) && !(data[1] & 0x20U)) return 0;
        if (length == 4 && !(lead & 0x0fU) && !(data[1] & 0x30U)) return 0;
        if (length == 5 && !(lead & 0x07U) && !(data[1] & 0x38U)) return 0;
    }
    if ((code >= 0xd800U && code <= 0xdfffU) || code == 0xfffeU || code == 0xffffU) return 0;
    value = code; return length;
}
RtonInput::RtonInput(std::vector<std::uint8_t> data) : data_(std::move(data)) {}
void RtonInput::seek(std::size_t offset) {
    if (offset > data_.size()) throw std::out_of_range("RTON input offset");
    position_ = offset;
}
std::vector<std::uint8_t> RtonInput::read_bytes(std::size_t count) {
    if (count > data_.size() - position_) throw std::out_of_range("RTON input read");
    const auto start = data_.begin() + static_cast<std::ptrdiff_t>(position_);
    std::vector<std::uint8_t> result(start, start + static_cast<std::ptrdiff_t>(count));
    position_ += count; return result;
}
std::uint8_t RtonInput::byte() {
    if (position_ == data_.size()) throw std::out_of_range("RTON input byte");
    return data_[position_++];
}
namespace {
// ARM register shifts use the low eight bits; shifts >=32 produce zero.
std::uint32_t arm_lsl(std::uint32_t value, std::uint32_t shift) { shift &= 255U; return shift < 32 ? value << shift : 0; }
std::uint32_t arm_lsr(std::uint32_t value, std::uint32_t shift) { shift &= 255U; return shift < 32 ? value >> shift : 0; }
}
std::uint32_t RtonInput::varuint32() {
    std::uint32_t result = 0, shift = 0;
    std::uint8_t b;
    do { b = byte(); result |= arm_lsl(b & 0x7fU, shift); shift += 7; } while (b & 0x80U);
    return result;
}
std::uint64_t RtonInput::varuint64() {
    std::uint32_t low = 0, high = 0, shift = 0;
    std::uint8_t b;
    do {
        b = byte(); const auto bits = b & 0x7fU;
        low |= arm_lsl(bits, shift);
        high |= arm_lsl(bits, shift - 32U) | arm_lsr(bits, 32U - shift);
        shift += 7;
    } while (b & 0x80U);
    return (static_cast<std::uint64_t>(high) << 32) | low;
}
std::uint32_t RtonInput::zigzag32() { const auto bits = varuint32(); return (bits >> 1) ^ (0U - (bits & 1U)); }
std::uint64_t RtonInput::zigzag64() { const auto bits = varuint64(); return (bits >> 1) ^ (std::uint64_t{0} - (bits & 1U)); }
std::string RtonInput::raw_string() {
    const auto bytes = read_bytes(varuint32()); return std::string(bytes.begin(), bytes.end());
}
std::u32string RtonInput::raw_wide_string() {
    const auto count = varuint32();
    if (count > (data_.size() - position_) / 4) throw std::out_of_range("RTON wide input read");
    std::u32string result; result.reserve(count);
    for (std::uint32_t i = 0; i < count; ++i) {
        std::uint32_t c = 0;
        for (unsigned j = 0; j < 4; ++j) c |= static_cast<std::uint32_t>(byte()) << (j * 8);
        result.push_back(static_cast<char32_t>(c));
    }
    return result;
}
std::uint32_t RtonInput::utf8_codepoint() {
    std::uint32_t value = 0;
    const auto consumed = decode_engine_utf8(data_.empty() ? nullptr : data_.data() + position_, data_.size() - position_, value);
    position_ += consumed; return value;
}
std::u32string RtonInput::utf8_string() {
    const auto count = varuint32(); (void)varuint32();
    std::u32string result; result.reserve(count);
    for (std::uint32_t i = 0; i < count; ++i) result.push_back(static_cast<char32_t>(utf8_codepoint()));
    return result;
}
bool RtonInput::normalized_header() {
    position_ = 0; header_read_mode_ = true;
    const auto le = [this](unsigned size) { std::uint32_t v = 0; for (unsigned i = 0; i < size; ++i) v |= static_cast<std::uint32_t>(byte()) << (i * 8); return v; };
    if (le(4) != 0x4e4f5452U || le(2) != 1 || le(2) != 1) return false;
    root_offset_ = static_cast<std::uint32_t>(position_); return true;
}
}
