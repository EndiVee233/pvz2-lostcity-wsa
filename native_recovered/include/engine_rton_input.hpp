#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace pvz2_recovered::engine {
// 01141fb4: returns bytes consumed; failure leaves value unchanged. Preserves
// original legacy UTF-8 acceptance rules, including five-byte sequences.
std::size_t decode_engine_utf8(const std::uint8_t*, std::size_t, std::uint32_t& value);

// Recovered byte input primitives, not a complete RTON document/object reader.
// Owns a host buffer; raw out-of-buffer reads throw instead of invoking UB.
class RtonInput {
    std::vector<std::uint8_t> data_;
    std::size_t position_ = 0;
    std::uint32_t root_offset_ = 0;
    bool header_read_mode_ = false;
public:
    explicit RtonInput(std::vector<std::uint8_t> data);
    std::size_t position() const { return position_; }
    void seek(std::size_t);
    std::vector<std::uint8_t> read_bytes(std::size_t);
    std::uint8_t byte();
    std::uint32_t varuint32();
    std::uint64_t varuint64();
    // Signed results returned as bit patterns, avoiding host signed overflow.
    std::uint32_t zigzag32();
    std::uint64_t zigzag64();
    std::string raw_string();
    std::u32string raw_wide_string();
    // Invalid UTF-8 returns zero and does not advance the input.
    std::uint32_t utf8_codepoint();
    std::u32string utf8_string();
    // 011f873c accepts RTON/version=1/internal-format=1. Raw format=0 must
    // first pass through normalize_rton's normalization/indexing stage.
    bool normalized_header();
    std::uint32_t root_offset() const { return root_offset_; }
    bool header_read_mode() const { return header_read_mode_; }
};
}
