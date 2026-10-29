#include "engine_reflection.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
struct Case {const char* hex;std::uint32_t expected;};
#include "brain_properties_fixtures.inc"
int main() {
    try {
        ReflectionDataRuntime rt;rt.register_brain_properties_class();rt.ensure_store(2,U"local");ObjectLoadResult objects;unsigned checks=0;
        for(auto c:cases) {
            std::vector<std::uint8_t> bytes;const auto digit=[](char c){return c<='9'?c-'0':c-'a'+10;};
            for(auto p=c.hex;*p;p+=2)bytes.push_back(static_cast<std::uint8_t>(digit(p[0])*16+digit(p[1])));
            auto document=normalize_rton(std::move(bytes),&rt.strings());if(!document.success)throw std::runtime_error("normalization failed");
            IndexedRtonReader reader(std::move(document));if(objects.objects.empty())objects=rt.create_objects(reader,2);
            rt.populate_objects(reader,2,objects);auto* object=rt.object(objects.objects.at(0));
            if(!object || object->type.name!="ZombiesAteYourBrainsProperties" || object->zombie_win_x_bits!=c.expected)throw std::runtime_error("brain boundary differs from original ARM");
            ++checks;
        }
        std::cout<<"PASS "<<checks<<" brain boundary original ARM field checkpoints\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
