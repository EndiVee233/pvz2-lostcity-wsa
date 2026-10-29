#pragma once
#include "engine_rton_input.hpp"
#include "engine_rton_normalizer.hpp"
#include <string_view>

namespace pvz2_recovered::engine {
struct Handle;
class OwnedRegistry;
class InternPool;
// Indexed RTON navigation over an owned normalized document. Original pointers
// returned by text accessors become byte offsets; zero denotes a null result.
// Bounds errors throw. No game-object deserialization/RTTI is implemented here.
class IndexedRtonReader {
    NormalizedRton document_;
    RtonInput input_;
    bool valid_;
    std::uint32_t le32();
    std::uint8_t at(std::size_t) const;
    std::uint32_t scalar32(std::uint32_t value, std::uint32_t fallback, unsigned mode);
public:
    explicit IndexedRtonReader(NormalizedRton);
    bool valid() const { return valid_; }
    std::uint32_t root() const { return input_.root_offset(); }
    std::uint32_t position() const { return static_cast<std::uint32_t>(input_.position()); }
    void seek(std::uint32_t offset) { input_.seek(offset); }
    // 011f87d8: peek without advancing.
    std::uint8_t peek() const;
    // 011f884c / 011f8920 / 011fa28c.
    std::uint32_t key_text_offset(std::uint32_t key);
    std::uint32_t value_offset(std::uint32_t key);
    std::uint32_t narrow_value_offset(std::uint32_t value);
    // 011fc08c / 011fc0c0 / 011fc124.
    bool is_object(std::uint32_t value);
    std::uint32_t first_field(std::uint32_t object);
    std::uint32_t next_field(std::uint32_t key);
    // 011fc208 / 011fc23c / 011fc2ac.
    bool is_array(std::uint32_t value);
    std::uint32_t array_count(std::uint32_t value);
    std::uint32_t array_element(std::uint32_t array, std::uint32_t index);
    // 011fdd64 uses the NARROW global text table, even when scanning wide keys.
    std::uint32_t find_field(std::uint32_t object, std::string_view name);
    // Covered non-RTID branches of 011f8d6c/011f9070/011f8a24.
    // Signed values are bit patterns. Boolean fallback is returned verbatim.
    // RTID coercion and decimal text outside signed32 range are explicit gaps.
    std::uint32_t scalar_int32_bits(std::uint32_t value, std::uint32_t fallback = 0);
    std::uint32_t scalar_uint32(std::uint32_t value, std::uint32_t fallback = 0);
    std::uint32_t scalar_boolean_bits(std::uint32_t value, std::uint32_t fallback = 0);
    // Covered 011f9ae8 numeric/narrow-decimal branches; IEEE float32 bits.
    // Wide swscanf and RTID coercion remain explicit gaps.
    std::uint32_t scalar_float32_bits(std::uint32_t value, std::uint32_t fallback = 0);
    // Covered 011f4c90 READ branches 0..3 / 011fb300 BA branch. Returns an
    // owned symbolic handle: caller must assign/release it with assign_handle.
    Handle reference_value(std::uint32_t value, OwnedRegistry&, InternPool&, std::uint32_t current_type);
    // Host convenience for the inspector. Does not alter reader position;
    // returns bytes up to the first zero, matching the returned C-string view.
    std::string narrow_text_at(std::uint32_t offset) const;
};
}
