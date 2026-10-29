#pragma once
#include <string>
#include <string_view>
namespace pvz2_recovered::engine {
// 01141e38 / 01141d80 byte conversion, intentionally NOT UTF-8 encoding.
std::string narrow_low_bytes(std::u32string_view);
std::u32string widen_bytes(std::string_view);
// 011e71c4 / 011e6f10 with the original packages/ prefix length (9).
std::string normalize_package_path(std::string_view);
std::string package_resource_filename(std::string_view);
}
