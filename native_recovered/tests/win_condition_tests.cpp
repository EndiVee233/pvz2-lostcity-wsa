#include "engine_win_condition.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
struct Case {std::vector<unsigned> flags,kinds;unsigned result,releases;std::vector<std::string> events;};
#include "win_condition_fixtures.inc"
struct Services final:WinConditionServices {
    const Case& test;std::vector<std::string> events;unsigned releases=0,current=0;
    explicit Services(const Case& c):test(c){}
    std::vector<std::uint32_t> snapshot_entity_flags() override {return test.flags;}
    std::vector<Handle> enumerate_type_0x25() override {
        events.push_back("enumerate-0x25");std::vector<Handle> r;
        for(unsigned i=0;i<test.kinds.size();++i)r.push_back(test.kinds[i]?Handle{i+1,0x25U<<17}:Handle{});
        return r;
    }
    Handle copy_handle(Handle h) override {return h;}
    Handle normalize(Handle h) override {if(h.low)current=h.low-1;return h;}
    std::uint32_t find_store(std::uint32_t type) override {
        if(type!=0x25)throw std::runtime_error("wrong type");
        events.push_back("find-bank-"+std::to_string(current));
        return test.kinds.at(current)==1?0:99;
    }
    std::uint32_t resolve(std::uint32_t,Handle h) override {events.push_back("resolve-"+std::to_string(h.low-1));return test.kinds.at(h.low-1)<=2?0:h.low;}
    bool predicate_d4(std::uint32_t object) override {
        events.push_back("predicate-"+std::to_string(object-1));return test.kinds.at(object-1)==4;
    }
    void release_handle(Handle& h) override {++releases;h={};}
    void release_enumeration() override {events.push_back("release-enumeration");}
};
int main() {
    try {
        unsigned passed=0;
        for(const auto& c:cases) {
            Services s(c);const auto result=zombies_dead_condition(s);
            if(result!=bool(c.result) || s.events!=c.events || s.releases!=c.releases)throw std::runtime_error("win condition differs from original ARM");
            ++passed;
        }
        std::cout<<"PASS "<<passed<<" win condition original ARM branch/callback cases\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
