#include "engine_rton_reader.hpp"
#include <algorithm>
#include <stdexcept>
#include <utility>

namespace pvz2_recovered::engine {
IndexedRtonReader::IndexedRtonReader(NormalizedRton document)
    : document_(std::move(document)), input_(document_.bytes), valid_(input_.normalized_header()) {}
std::uint8_t IndexedRtonReader::at(std::size_t offset) const {
    if (offset >= document_.bytes.size()) throw std::out_of_range("indexed RTON byte");
    return document_.bytes[offset];
}
std::uint8_t IndexedRtonReader::peek() const { return at(input_.position()); }
std::uint32_t IndexedRtonReader::le32() {
    std::uint32_t value = 0; for (unsigned i = 0; i < 4; ++i) value |= static_cast<std::uint32_t>(input_.byte()) << (i * 8); return value;
}
std::uint32_t IndexedRtonReader::key_text_offset(std::uint32_t key) {
    seek(key); const auto tag = input_.byte();
    if (tag == 0xb4 || tag == 0xb6) { (void)le32(); return position(); }
    if (tag == 0xb5 || tag == 0xb7) return le32();
    return 0;
}
std::uint32_t IndexedRtonReader::value_offset(std::uint32_t key) {
    if (!key) return 0;
    seek(key); const auto tag = input_.byte();
    if (tag == 0xb4 || tag == 0xb6) { const auto size = le32(); seek(position() + size); (void)le32(); return position(); }
    if (tag == 0xb5 || tag == 0xb7) { (void)le32(); (void)le32(); return position(); }
    return 0;
}
std::uint32_t IndexedRtonReader::narrow_value_offset(std::uint32_t value) {
    if (!value) return 0;
    seek(value); const auto tag = input_.byte();
    if (tag == 0xb0) { (void)le32(); return position(); }
    if (tag == 0xb1) return le32();
    return 0;
}
bool IndexedRtonReader::is_object(std::uint32_t value) { if (!value) return false; seek(value); return peek() == 0xb8; }
bool IndexedRtonReader::is_array(std::uint32_t value) { if (!value) return false; seek(value); return peek() == 0xb9; }
std::uint32_t IndexedRtonReader::first_field(std::uint32_t object) {
    if (!object) return 0;
    seek(object); return input_.byte() == 0xb8 && peek() != 0xff ? position() : 0;
}
std::uint32_t IndexedRtonReader::next_field(std::uint32_t key) {
    if (!key) return 0;
    seek(key); const auto tag = input_.byte();
    if (tag == 0xb4 || tag == 0xb6) { const auto size = le32(); seek(position() + size); const auto next = le32(); seek(next); }
    else if (tag == 0xb5 || tag == 0xb7) { (void)le32(); const auto next = le32(); seek(next); }
    return peek() == 0xff ? 0 : position();
}
std::uint32_t IndexedRtonReader::array_count(std::uint32_t value) {
    if (!value) return 0;
    seek(value); if (input_.byte() != 0xb9) return 0;
    (void)input_.byte(); return le32();
}
std::uint32_t IndexedRtonReader::array_element(std::uint32_t array, std::uint32_t index) {
    if (!array) return 0;
    seek(array); if (input_.byte() != 0xb9) return 0;
    (void)input_.byte(); const auto count = le32(); if (index >= count) return 0;
    seek(position() + index * 4U); return le32();
}
std::uint32_t IndexedRtonReader::find_field(std::uint32_t object, std::string_view name) {
    if (!object) return 0;
    const auto found = std::find_if(document_.narrow_strings.begin(), document_.narrow_strings.end(), [&](const auto& x) { return x.first == name; });
    if (found == document_.narrow_strings.end()) return 0;
    seek(object); if (input_.byte() != 0xb8) return 0;
    auto key = position(); auto tag = input_.byte();
    while (tag != 0xff) {
        if (tag == 0xb5 || tag == 0xb7) {
            if (le32() == found->second) return key;
            const auto next = le32(); seek(next); key = next;
        } else if (tag == 0xb4 || tag == 0xb6) {
            const auto size = le32(); if (position() == found->second) return key;
            seek(position() + size); const auto next = le32(); seek(next); key = next;
        } else key = position();
        tag = input_.byte();
    }
    return 0;
}
std::string IndexedRtonReader::narrow_text_at(std::uint32_t offset) const {
    if (!offset) return {};
    std::string text;
    while (const auto c = at(offset++)) text.push_back(static_cast<char>(c));
    return text;
}
}
