#include "engine_package_paths.hpp"
#include <algorithm>

namespace pvz2_recovered::engine {
std::string narrow_low_bytes(std::u32string_view text) {
    std::string result; result.reserve(text.size());
    for (auto c : text) result.push_back(static_cast<char>(static_cast<unsigned>(c) & 255U));
    return result;
}
std::u32string widen_bytes(std::string_view bytes) {
    std::u32string result; result.reserve(bytes.size());
    for (unsigned char c : bytes) result.push_back(static_cast<char32_t>(c));
    return result;
}
namespace {
std::string_view c_string(std::string_view text) { return text.substr(0, text.find('\0')); }
// 011450b8(..., include_separator=1). This part uses string length, not strlen.
std::string directory(std::string_view path) {
    const auto last = path.find_last_of("\\/");
    return last == path.npos ? std::string{} : std::string(path.substr(0, last + 1));
}
// 011471cc + 011473ac(..., strip_extension=1). The original basename helper
// reads a C string, including its special UNC server-only rejection.
std::string basename(std::string_view path) {
    path = c_string(path);
    std::size_t begin = 0;
    if (path.size() >= 2 && path[0] == '\\' && path[1] == '\\') {
        begin = path.find_first_of("\\/", 2);
        if (begin == path.npos) return {};
    }
    const auto last = path.find_last_of("\\/:");
    if (last != path.npos && last >= begin) begin = last + 1;
    if (begin >= path.size()) return {};
    auto base = path.substr(begin);
    const auto dot = base.find_last_of('.');
    if (dot != base.npos) base = base.substr(0, dot);
    return std::string(base);
}
bool prefixed(std::string_view text) {
    constexpr std::string_view prefix = "packages/";
    if (text.size() < prefix.size()) return false;
    for (std::size_t i = 0; i < prefix.size(); ++i) {
        auto c = static_cast<unsigned char>(text[i]);
        if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
        if (c != static_cast<unsigned char>(prefix[i])) return false;
    }
    return true;
}
std::string combine(std::string_view path) {
    auto result = directory(path) + basename(path);
    std::replace(result.begin(), result.end(), '\\', '/');
    return result;
}
}
std::string normalize_package_path(std::string_view path) {
    if (path.empty()) return {};
    auto result = combine(path);
    // Original uses strlen after skipping the prefix, so embedded null bytes
    // only truncate this branch. Preserve the unprefixed string's full length.
    return prefixed(result) ? std::string(c_string(std::string_view(result).substr(9))) : result;
}
std::string package_resource_filename(std::string_view path) {
    if (path.empty()) return {};
    auto result = combine(path) + ".rton";
    if (!prefixed(result)) result.insert(0, "packages/");
    return result;
}
}
