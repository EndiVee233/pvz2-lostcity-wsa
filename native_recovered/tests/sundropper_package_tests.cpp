#include "engine_reflection.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
using namespace pvz2_recovered::engine;
static ObjectLoadResult load(ReflectionDataRuntime& rt, const char* path, std::uint32_t type) {
    std::ifstream f(path,std::ios::binary); if(!f)throw std::runtime_error("input unavailable");
    std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());
    auto doc=normalize_rton(std::move(bytes),&rt.strings());if(!doc.success)throw std::runtime_error("normalization failure");
    IndexedRtonReader reader(std::move(doc));auto result=rt.create_objects(reader,type);
    if(!result.success)throw std::runtime_error("load failure");
    rt.populate_objects(reader,type,result);return result;
}
int main(int argc,char** argv) {
    if(argc!=3)return 2;
    try {
        ReflectionDataRuntime rt;
#if defined(PVZ2_BRAIN_PACKAGE)
        rt.register_brain_properties_class();
        const unsigned expected_links=8;
#elif defined(PVZ2_DANGER_PACKAGE)
        rt.register_danger_module_class();
        const unsigned expected_links=7;
#elif defined(PVZ2_WIN_PACKAGE)
        rt.register_zombiesdead_class();
        const unsigned expected_links=6;
#else
        rt.register_sundropper_class();
        const unsigned expected_links=5;
#endif
        rt.ensure_store(2,U"local");rt.set_package(2,U"packages/CurrentLevel.rton");
        auto current=load(rt,argv[1],2);
        const auto* root=rt.object(current.objects.at(0));if(!root || !root->level)throw std::runtime_error("missing level");
        unsigned before=0,after=0;for(auto h:root->level->modules)before+=rt.resolve(h)!=0;
        rt.ensure_store(3,U"external");rt.set_package(3,U"packages/LevelModules.rton");
        auto external=load(rt,argv[2],3);unsigned created=0;for(auto t:external.objects)created+=t!=0;
        const ReflectedDataObject* sun=nullptr;bool win=false,danger=false,brain=false;
        for(auto h:root->level->modules)if(auto t=rt.resolve(h)) {++after;auto* o=rt.object(t);if(o && o->type.name=="SunDropperProperties")sun=o;if(o && o->type.name=="ZombiesDeadWinConProperties")win=true;if(o && o->type.name=="DangerRoomModuleProperties")danger=true;if(o && o->type.name=="ZombiesAteYourBrainsProperties" && o->zombie_win_x_bits==0xc2a00000U)brain=true;}
        if(current.objects.size()!=5 || before!=4 || after!=expected_links || !sun || (expected_links>=6 && !win) || (expected_links>=7 && !danger) || (expected_links==8 && !brain))throw std::runtime_error("package edge not closed");
        const std::array<std::uint32_t,5> expected{{0x40000000U,0x40880000U,0x40300000U,0x41180000U,0x3dcccccdU}};
        if(sun->sun_drop_bits!=expected)throw std::runtime_error("real package values mismatch");
        std::cout<<"PASS real package integration: module links "<<before<<" -> "<<after<<"; LevelModules factories "<<created<<"/"<<external.objects.size()<<"\n";
        return 0;
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
