#include "engine_rton_reader.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
enum class Operation {i32,u32,boolean};
struct Step {Operation op;std::uint32_t offset,fallback,result,position;};
struct Scenario {const char* label;std::vector<std::uint32_t> data;std::vector<Step> steps;};
#include "rton_scalar_fixtures.inc"
int main() {
    unsigned checks=0;const char* label="initialization";
    try {
        for(const auto& sc:scenarios) {
            label=sc.label;NormalizedRton document;document.success=true;
            for(auto b:sc.data)document.bytes.push_back(static_cast<std::uint8_t>(b));
            IndexedRtonReader reader(std::move(document));if(!reader.valid())throw std::runtime_error("invalid fixture header");
            for(const auto& s:sc.steps) {
                reader.seek(13);std::uint32_t result=0;
                switch(s.op) {
                case Operation::i32:result=reader.scalar_int32_bits(s.offset,s.fallback);break;
                case Operation::u32:result=reader.scalar_uint32(s.offset,s.fallback);break;
                case Operation::boolean:result=reader.scalar_boolean_bits(s.offset,s.fallback);break;
                }
                if(result!=s.result || reader.position()!=s.position)throw std::runtime_error("result/cursor: "+std::to_string(result)+"/"+std::to_string(reader.position())+" vs ARM "+std::to_string(s.result)+"/"+std::to_string(s.position));
                ++checks;
            }
        }
        std::cout<<"PASS "<<checks<<" non-RTID RTON scalar ARM bits/cursor checkpoints\n";
    }catch(const std::exception& e){std::cerr<<label<<": "<<e.what()<<'\n';return 1;}
}
