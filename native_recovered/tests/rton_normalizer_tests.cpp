#include "engine_rton_normalizer.hpp"
#include "engine_rton_input.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
struct Entry {std::vector<std::uint32_t> text;std::uint32_t offset;};
struct Scenario {const char* label;std::vector<std::uint32_t> input;bool success;std::uint32_t consumed;std::vector<std::uint32_t> output;std::vector<Entry> narrow,wide;};
#include "rton_normalizer_fixtures.inc"
void compare(const std::vector<std::uint32_t>& a,const std::vector<std::uint32_t>& b,const char* what) {
    if(a.size()!=b.size())throw std::runtime_error(std::string(what)+" size "+std::to_string(a.size())+" vs ARM "+std::to_string(b.size()));
    for(std::size_t i=0;i<a.size();++i)if(a[i]!=b[i])throw std::runtime_error(std::string(what)+" at "+std::to_string(i)+": "+std::to_string(a[i])+" vs ARM "+std::to_string(b[i]));
}
int main() {
    unsigned checks=0;const char* label="initialization";
    try {
        for(const auto& sc:scenarios) {
            label=sc.label;std::vector<std::uint8_t> bytes;for(auto v:sc.input)bytes.push_back(static_cast<std::uint8_t>(v));
            const auto result=normalize_rton(bytes);
            if(result.success!=sc.success || result.input_consumed!=sc.consumed)throw std::runtime_error("success/consumption differs from ARM");
            compare(std::vector<std::uint32_t>(result.bytes.begin(),result.bytes.end()),sc.output,"normalized bytes");
            if(result.narrow_strings.size()!=sc.narrow.size() || result.wide_strings.size()!=sc.wide.size())throw std::runtime_error("string table counts differ");
            for(std::size_t i=0;i<sc.narrow.size();++i) {
                std::vector<std::uint32_t> text;for(unsigned char c:result.narrow_strings[i].first)text.push_back(c);
                compare(text,sc.narrow[i].text,"narrow key");if(result.narrow_strings[i].second!=sc.narrow[i].offset)throw std::runtime_error("narrow offset differs");
            }
            for(std::size_t i=0;i<sc.wide.size();++i) {
                std::vector<std::uint32_t> text;for(auto c:result.wide_strings[i].first)text.push_back(static_cast<std::uint32_t>(c));
                compare(text,sc.wide[i].text,"wide key");if(result.wide_strings[i].second!=sc.wide[i].offset)throw std::runtime_error("wide offset differs");
            }
            if(result.success) {RtonInput input(result.bytes);if(!input.normalized_header() || input.root_offset()!=8)throw std::runtime_error("normalized output/header reader integration failed");}
            ++checks;
        }
        std::cout<<"PASS "<<checks<<" RTON normalizer ARM byte/table checkpoints\n";
    } catch(const std::exception& e) {std::cerr<<label<<": "<<e.what()<<'\n';return 1;}
}
