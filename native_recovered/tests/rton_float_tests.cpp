#include "engine_rton_reader.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
struct FloatCase {const char* label;std::vector<std::uint32_t> data;std::uint32_t offset,fallback,result,position;};
#include "rton_float_fixtures.inc"
int main() {
    unsigned checks=0;const char* label="initialization";
    try {
        for(const auto& s:float_cases) {
            label=s.label;NormalizedRton document;document.success=true;
            for(auto b:s.data)document.bytes.push_back(static_cast<std::uint8_t>(b));
            IndexedRtonReader reader(std::move(document));reader.seek(13);
            const auto result=reader.scalar_float32_bits(s.offset,s.fallback);
            if(result!=s.result || reader.position()!=s.position)throw std::runtime_error("bits/cursor "+std::to_string(result)+"/"+std::to_string(reader.position())+" vs ARM "+std::to_string(s.result)+"/"+std::to_string(s.position));
            ++checks;
        }
        std::cout<<"PASS "<<checks<<" RTON numeric/narrow-decimal float ARM bits/cursor checkpoints\n";
    }catch(const std::exception& e){std::cerr<<label<<": "<<e.what()<<'\n';return 1;}
}
