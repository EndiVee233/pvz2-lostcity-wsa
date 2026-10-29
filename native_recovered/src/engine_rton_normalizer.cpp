#include "engine_rton_normalizer.hpp"
#include "engine_rton_input.hpp"
#include "engine_rton_writer.hpp"
#include "engine_intern.hpp"
#include <algorithm>
#include <stdexcept>

namespace pvz2_recovered::engine {
namespace {
class Normalizer {
    RtonInput input_;
    NormalizedRton result_;
    std::vector<std::uint32_t> narrow_cache_, wide_cache_;
    unsigned depth_ = 0;
    InternPool* ambient_;
    std::size_t cursor_ = 0;
    std::uint32_t position() const { return static_cast<std::uint32_t>(cursor_); }
    void byte(std::uint8_t value) {
        if (cursor_ == result_.bytes.size()) result_.bytes.push_back(value);
        else result_.bytes[cursor_] = value;
        ++cursor_;
    }
    void le(std::uint64_t value, unsigned count) { for (unsigned i = 0; i < count; ++i) byte(static_cast<std::uint8_t>(value >> (i * 8))); }
    std::uint32_t read_le(unsigned count) { std::uint32_t v = 0; for (unsigned i = 0; i < count; ++i) v |= static_cast<std::uint32_t>(input_.byte()) << (i * 8); return v; }
    void patch(std::uint32_t offset, std::uint32_t value) {
        // Original fixed-buffer patches can extend beyond its current logical
        // end (notably count=ffffffff arrays). Keep storage and cursor separate.
        if (offset > 0x2000000U) throw std::length_error("RTON patch limit");
        if (result_.bytes.size() < static_cast<std::size_t>(offset) + 4) result_.bytes.resize(static_cast<std::size_t>(offset) + 4);
        for (unsigned i = 0; i < 4; ++i) result_.bytes[offset + i] = static_cast<std::uint8_t>(value >> (i * 8));
    }
    std::uint32_t narrow(const std::string& text, bool key, bool cached) {
        const auto it = std::find_if(result_.narrow_strings.begin(), result_.narrow_strings.end(), [&](const auto& x) { return x.first == text; });
        std::uint32_t offset;
        if (it == result_.narrow_strings.end()) {
            byte(key ? 0xb4 : 0xb0); le(text.size() + 1, 4); offset = position();
            result_.narrow_strings.emplace_back(text, offset);
            for (unsigned char c : text) byte(c);
            byte(0);
        } else { byte(key ? 0xb5 : 0xb1); offset = it->second; le(offset, 4); }
        auto slot = position(); if (key) le(0, 4);
        if (cached) narrow_cache_.push_back(offset);
        return slot;
    }
    std::uint32_t wide(const std::u32string& text, bool key, bool cached) {
        const auto it = std::find_if(result_.wide_strings.begin(), result_.wide_strings.end(), [&](const auto& x) { return x.first == text; });
        std::uint32_t offset;
        if (it == result_.wide_strings.end()) {
            byte(key ? 0xb6 : 0xb2); le((text.size() + 1) * 4, 4); offset = position();
            result_.wide_strings.emplace_back(text, offset);
            for (auto c : text) le(static_cast<std::uint32_t>(c), 4);
            le(0, 4);
        } else { byte(key ? 0xb7 : 0xb3); offset = it->second; le(offset, 4); }
        auto slot = position(); if (key) le(0, 4);
        if (cached) wide_cache_.push_back(offset);
        return slot;
    }
    void emit_utf8(std::u32string_view text) {
        RtonWriter writer; writer.wide_string({}, text);
        const auto& bytes = writer.bytes(); for (std::size_t i = 1; i < bytes.size(); ++i) byte(bytes[i]);
    }
    static std::u32string intern_text(std::u32string text) {
        const auto nul = text.find(U'\0'); if (nul != std::u32string::npos) text.resize(nul); return text;
    }
    // Wire behavior of 011f4394 on a fresh descriptor. Text drives the output;
    // an optional shared pool also preserves transient interning side effects.
    void reference(bool has_payload) {
        std::uint32_t a = 0, b = 0, c = 0; std::u32string package, name;
        if (has_payload) {
            const auto kind = input_.byte();
            if (kind == 3) {
                auto package_text = input_.utf8_string(); name = intern_text(input_.utf8_string());
                if (package_text == U".") package_text.clear();
                package = intern_text(std::move(package_text));
            } else if (kind == 1 || kind == 2) {
                if (kind == 2) package = intern_text(input_.utf8_string());
                a = input_.varuint32(); b = input_.varuint32(); c = read_le(4);
            }
        }
        InternValue transient_package, transient_name;
        if (ambient_) { transient_package = ambient_->acquire(package.c_str()); transient_name = ambient_->acquire(name.c_str()); }
        byte(0xba);
        if (!name.empty()) { byte(3); emit_utf8(package.empty() ? std::u32string_view(U".") : std::u32string_view(package)); emit_utf8(name); }
        else if (!a && !b && !c && package.empty()) byte(0);
        else {
            byte(package.empty() ? 1 : 2); if (!package.empty()) emit_utf8(package);
            RtonWriter writer; writer.varuint(a); writer.varuint(b);
            for (auto b8 : writer.bytes()) byte(b8);
            le(c, 4);
        }
        // Original fresh descriptor's destruction releases package, then name.
        if (ambient_) { ambient_->release(transient_package.id); ambient_->release(transient_name.id); }
    }
    std::uint32_t token(std::uint8_t tag, bool key) {
        if (key && tag != 2 && tag != 0x81 && tag != 0x82 && (tag < 0x90 || tag > 0x93)) throw std::invalid_argument("RTON object key must be text");
        if (tag == 0 || tag == 1) { byte(0xbc); byte(tag); }
        else if (tag == 2 || tag == 0x81 || tag == 0x90) return narrow(tag == 2 ? std::string("*") : input_.raw_string(), key, tag == 0x90);
        else if (tag == 0x82 || tag == 0x92) return wide(input_.utf8_string(), key, tag == 0x92);
        else if (tag == 0x91 || tag == 0x93) {
            const auto id = input_.varuint32(); const auto& cache = tag == 0x91 ? narrow_cache_ : wide_cache_;
            if (id >= cache.size()) throw std::out_of_range("RTON string cache reference");
            byte(tag == 0x91 ? (key ? 0xb5 : 0xb1) : (key ? 0xb7 : 0xb3)); le(cache[id], 4);
            const auto slot = position(); if (key) le(0, 4); return slot;
        } else if (tag == 0x83 || tag == 0x84) reference(tag == 0x83);
        else if (tag == 0x85) { byte(0xb8); container(false, 0); }
        else if (tag == 0x86) {
            const auto subtype = input_.byte(); const auto count = input_.varuint32();
            byte(0xb9); byte(subtype); le(count, 4); const auto table = position();
            // The original reserves count+1 offsets, except ffffffff reserves
            // none. Backpatch writes may then be overwritten by token output.
            if (count != 0xffffffffU) for (std::uint64_t i = 0; i <= count; ++i) le(0, 4);
            container(true, table);
        } else if (tag == 0x87) {
            byte(0xbb); (void)input_.byte(); (void)narrow(input_.raw_string(), false, false);
            const auto size = input_.varuint32(); le(size, 4);
            for (auto b8 : input_.read_bytes(size)) byte(b8);
        } else {
            unsigned size = 0; std::uint8_t output = 0; bool zero = false;
            switch (tag) {
            case 8: case 9: output = 8; size = 1; zero = tag == 9; break;
            case 10: case 11: output = 10; size = 1; zero = tag == 11; break;
            case 0x10: case 0x11: output = 0x10; size = 2; zero = tag == 0x11; break;
            case 0x12: case 0x13: output = 0x12; size = 2; zero = tag == 0x13; break;
            case 0x20: case 0x21: case 0x22: case 0x23: case 0x26: case 0x27:
                output = tag & 0xfeU; size = 4; zero = (tag & 1U) != 0; break;
            case 0x40: case 0x41: case 0x42: case 0x43: case 0x46: case 0x47:
                output = tag & 0xfeU; size = 8; zero = (tag & 1U) != 0; break;
            case 0x24: case 0x25: case 0x28:
                byte(tag == 0x28 ? 0x26 : 0x20); le(tag == 0x25 ? input_.zigzag32() : input_.varuint32(), 4); return 0;
            case 0x44: case 0x45: case 0x48:
                byte(tag == 0x48 ? 0x46 : 0x40); le(tag == 0x45 ? input_.zigzag64() : input_.varuint64(), 8); return 0;
            default: return 0; // Original unhandled tags emit/consume nothing.
            }
            byte(output);
            if (zero) le(0, size);
            else for (auto b8 : input_.read_bytes(size)) byte(b8);
        }
        return 0;
    }
    void container(bool array, std::uint32_t table) {
        if (++depth_ > 512) throw std::length_error("RTON nesting limit");
        auto tag = input_.byte();
        while (tag != (array ? 0xfe : 0xff)) {
            if (array) { patch(table, position()); table += 4; (void)token(tag, false); }
            else {
                const auto slot = token(tag, true); (void)token(input_.byte(), false); patch(slot, position());
            }
            tag = input_.byte();
        }
        byte(array ? 0xfe : 0xff); if (array) patch(table, position()); --depth_;
    }
public:
    Normalizer(std::vector<std::uint8_t> data, InternPool* ambient) : input_(std::move(data)), ambient_(ambient) {}
    NormalizedRton run() {
        if (read_le(4) == 0x4e4f5452U && read_le(2) == 1 && read_le(2) == 0) {
            le(0x4e4f5452U, 4); le(1, 2); le(1, 2); byte(0xb8); container(false, 0);
            result_.success = read_le(4) == 0x454e4f44U;
            if (result_.success) le(0x454e4f44U, 4);
        }
        result_.input_consumed = input_.position();
        result_.bytes.resize(cursor_);
        std::sort(result_.narrow_strings.begin(), result_.narrow_strings.end());
        std::sort(result_.wide_strings.begin(), result_.wide_strings.end());
        return std::move(result_);
    }
};
}
NormalizedRton normalize_rton(std::vector<std::uint8_t> input, InternPool* ambient_pool) { return Normalizer(std::move(input), ambient_pool).run(); }
}
