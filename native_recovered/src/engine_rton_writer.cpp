#include "engine_rton_writer.hpp"
#include "engine_package_paths.hpp"
#include "engine_store.hpp"

namespace pvz2_recovered::engine {
void RtonWriter::varuint(std::uint32_t value) {
    while (value >= 0x80U) { byte(static_cast<std::uint8_t>(value | 0x80U)); value >>= 7; }
    byte(static_cast<std::uint8_t>(value));
}
void RtonWriter::raw_string(std::string_view value) {
    varuint(static_cast<std::uint32_t>(value.size()));
    for (unsigned char c : value) byte(c);
}
void RtonWriter::key(std::string_view value) { if (!value.empty()) string({}, value, true); }
void RtonWriter::string(std::string_view name, std::string_view value, bool cached) {
    key(name);
    if (!cached) { byte(0x81); raw_string(value); return; }
    for (const auto& item : cache_) if (item.first == value) { byte(0x91); varuint(item.second); return; }
    byte(0x90); raw_string(value);
    cache_.emplace_back(std::string(value), static_cast<std::uint32_t>(cache_.size()));
}
void RtonWriter::integer(std::string_view name, std::uint32_t bits) {
    key(name);
    if (!bits) { byte(0x21); return; }
    const auto length = [](std::uint32_t value) { unsigned n = 1; while (value >>= 7) ++n; return n; };
    const auto zigzag = (bits << 1) ^ (0U - (bits >> 31));
    const auto raw_length = length(bits), signed_length = length(zigzag);
    if ((raw_length < 4 && signed_length < raw_length) || (raw_length >= 4 && signed_length < 4)) {
        byte(0x25); varuint(zigzag);
    } else if (raw_length < 4) { byte(0x24); varuint(bits); }
    else { byte(0x20); for (unsigned i = 0; i < 4; ++i) byte(static_cast<std::uint8_t>(bits >> (i * 8))); }
}
void RtonWriter::wide_string(std::string_view name, std::u32string_view text) {
    key(name); byte(0x82);
    const auto nul = text.find(U'\0'); if (nul != std::u32string_view::npos) text = text.substr(0, nul);
    std::uint32_t encoded_size = 0;
    for (auto c : text) encoded_size += c < 0x80U ? 1 : c < 0x800U ? 2 : c < 0x10000U ? 3 : c < 0x110000U ? 4 : 0;
    varuint(static_cast<std::uint32_t>(text.size())); varuint(encoded_size);
    for (auto c : text) {
        const auto value = static_cast<std::uint32_t>(c);
        if (value < 0x80U) byte(static_cast<std::uint8_t>(value));
        else if (value < 0x800U) { byte(static_cast<std::uint8_t>(0xc0U | (value >> 6))); byte(static_cast<std::uint8_t>(0x80U | (value & 63U))); }
        else if (value < 0x10000U) { byte(static_cast<std::uint8_t>(0xe0U | (value >> 12))); byte(static_cast<std::uint8_t>(0x80U | ((value >> 6) & 63U))); byte(static_cast<std::uint8_t>(0x80U | (value & 63U))); }
        else if (value < 0x110000U) { byte(static_cast<std::uint8_t>(0xf0U | (value >> 18))); byte(static_cast<std::uint8_t>(0x80U | ((value >> 12) & 63U))); byte(static_cast<std::uint8_t>(0x80U | ((value >> 6) & 63U))); byte(static_cast<std::uint8_t>(0x80U | (value & 63U))); }
    }
}
void RtonWriter::boolean(std::string_view name, std::uint8_t raw_value) { key(name); byte(raw_value); }
void RtonWriter::store_metadata(const OwnedStore& store, const InternPool& strings) {
    integer("table_index", store.type());
    boolean("is_system_table", (store.type() & 0x2000U) ? static_cast<std::uint8_t>(store.system_byte() ^ 1U) : 0);
    if (store.name_id()) {
        const auto& name = strings.text(store.name_id());
        string("table_name", narrow_low_bytes(std::u32string_view(name).substr(name.empty() ? 0 : 1)));
    }
    if (!store.display_name().empty()) string("display_name", store.display_name());
    if (store.fixed_content()) boolean("is_fixed_content", 1);
    wide_string("current_package", strings.text(store.effective_name_id()));
}
}
