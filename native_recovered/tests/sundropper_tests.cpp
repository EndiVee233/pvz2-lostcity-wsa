#include "engine_reflection.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
struct Case { const char* hex; std::array<std::uint32_t, 5> expected; };
#include "sundropper_fixtures.inc"
int main() {
    try {
        ReflectionDataRuntime runtime; runtime.register_sundropper_class();
        runtime.ensure_store(2, U"local"); runtime.set_package(2, U"packages/LevelModules.rton");
        ObjectLoadResult objects; unsigned checks = 0;
        for (const auto& c : cases) {
            std::vector<std::uint8_t> bytes;
            const auto digit=[](char ch) { return ch <= '9' ? ch-'0' : ch-'a'+10; };
            for (const char* p=c.hex; *p; p+=2) bytes.push_back(static_cast<std::uint8_t>(digit(p[0])*16+digit(p[1])));
            auto document=normalize_rton(std::move(bytes), &runtime.strings());
            if (!document.success) throw std::runtime_error("normalizer failure");
            IndexedRtonReader reader(std::move(document));
            if (!checks) objects=runtime.create_objects(reader, 2);
            runtime.populate_objects(reader, 2, objects);
            if (!objects.success || objects.objects.size()!=1) throw std::runtime_error("factory failure");
            const auto* object=runtime.object(objects.objects[0]);
            if (!object || object->type.name!="SunDropperProperties") throw std::runtime_error("wrong class");
            for (std::size_t i=0;i<5;++i) {
                if (object->sun_drop_bits[i]!=c.expected[i]) throw std::runtime_error("float state differs from original ARM");
                ++checks;
            }
        }
        std::cout<<"PASS "<<checks<<" SunDropper original ARM field checkpoints\n";
        return 0;
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
