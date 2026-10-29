#include "engine_reflection.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
struct Ref {const char* package;const char* name;int target;};
struct Case {const char* hex;Ref world;std::vector<Ref> designers;};
#include "danger_module_fixtures.inc"
int main() {
    try {
        ReflectionDataRuntime rt;rt.register_danger_module_class();rt.ensure_store(2,U"local");
        ObjectLoadResult objects;unsigned checks=0;
        const auto ascii=[](const std::u32string& s){std::string r;for(auto c:s)r.push_back(static_cast<char>(c));return r;};
        const auto compare=[&](Handle h,const Ref& expected) {
            std::string package,name;int index=-1;
            if(h.low||h.high) {
                package=ascii(rt.strings().text((h.low>>31)|((h.high&0x3fffffffU)<<1)));
                name=ascii(rt.strings().text(h.low&0x7fffffffU));
                auto token=rt.resolve(h);for(std::size_t i=0;i<objects.objects.size();++i)if(token && objects.objects[i]==token)index=static_cast<int>(i);
            }
            if(package!=expected.package || name!=expected.name || index!=expected.target)throw std::runtime_error("danger reference differs from original ARM");
            checks+=3;
        };
        for(const auto& c:cases) {
            std::vector<std::uint8_t> bytes;auto digit=[](char x){return x<='9'?x-'0':x-'a'+10;};
            for(auto p=c.hex;*p;p+=2)bytes.push_back(static_cast<std::uint8_t>(digit(p[0])*16+digit(p[1])));
            auto doc=normalize_rton(std::move(bytes),&rt.strings());if(!doc.success)throw std::runtime_error("invalid fixture");
            IndexedRtonReader reader(std::move(doc));if(objects.objects.empty())objects=rt.create_objects(reader,2);
            rt.populate_objects(reader,2,objects);auto* object=rt.object(objects.objects.at(0));
            if(!object || object->type.name!="DangerRoomModuleProperties")throw std::runtime_error("wrong class");
            compare(object->danger_world,c.world);
            if(object->danger_designers.size()!=c.designers.size())throw std::runtime_error("list length mismatch");++checks;
            for(std::size_t i=0;i<c.designers.size();++i)compare(object->danger_designers[i],c.designers[i]);
        }
        // Destruction must release the final world's and two designer references.
        const char32_t* names[]{U"FirstToRelease",U"SecondToRelease",U"WorldToRelease"};
        std::uint32_t ids[3],counts[3];for(unsigned i=0;i<3;++i){ids[i]=rt.strings().find_id(names[i]);counts[i]=rt.strings().reference_count(ids[i]);}
        rt.registry().remove(2);
        for(unsigned i=0;i<3;++i)if(rt.strings().reference_count(ids[i])+1!=counts[i])throw std::runtime_error("owned reference leak");
        std::cout<<"PASS "<<checks<<" danger module original ARM field/identity checkpoints; 3 host teardown checks\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
