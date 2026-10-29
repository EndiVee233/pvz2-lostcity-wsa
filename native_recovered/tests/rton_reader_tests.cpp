#include "engine_rton_reader.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
enum class Operation {seek,peek,key_text,value,narrow_text,is_object,first,next,is_array,count,element,find};
struct Step {Operation op;std::uint32_t a,b;std::vector<std::uint32_t> key,result,state;};
struct Scenario {const char* label;std::vector<std::uint32_t> data,indexed,initial;std::vector<Step> steps;};
#include "rton_reader_fixtures.inc"
void compare(const std::vector<std::uint32_t>& a,const std::vector<std::uint32_t>& b,const char* what) {
    if(a.size()!=b.size())throw std::runtime_error(std::string(what)+" length differs");
    for(std::size_t i=0;i<a.size();++i)if(a[i]!=b[i])throw std::runtime_error(std::string(what)+" at "+std::to_string(i)+": "+std::to_string(a[i])+" vs ARM "+std::to_string(b[i]));
}
int main() {
    unsigned checks=0,number=0;const char* label="initialization";
    try {
        for(const auto& sc:scenarios) {
            label=sc.label;number=0;std::vector<std::uint8_t> data;for(auto v:sc.data)data.push_back(static_cast<std::uint8_t>(v));
            auto doc=normalize_rton(std::move(data));
            compare(std::vector<std::uint32_t>(doc.bytes.begin(),doc.bytes.end()),sc.indexed,"original normalization input");
            IndexedRtonReader reader(std::move(doc));if(!reader.valid())throw std::runtime_error("indexed header rejected");
            compare({reader.position(),reader.root()},sc.initial,"initial reader state");
            for(const auto& s:sc.steps) {
                std::vector<std::uint32_t> result;
                switch(s.op) {
                case Operation::seek:reader.seek(s.a);break;
                case Operation::peek:result={reader.peek()};break;
                case Operation::key_text:result={reader.key_text_offset(s.a)};break;
                case Operation::value:result={reader.value_offset(s.a)};break;
                case Operation::narrow_text:result={reader.narrow_value_offset(s.a)};break;
                case Operation::is_object:result={reader.is_object(s.a)?1U:0U};break;
                case Operation::first:result={reader.first_field(s.a)};break;
                case Operation::next:result={reader.next_field(s.a)};break;
                case Operation::is_array:result={reader.is_array(s.a)?1U:0U};break;
                case Operation::count:result={reader.array_count(s.a)};break;
                case Operation::element:result={reader.array_element(s.a,s.b)};break;
                case Operation::find: {std::string key;for(auto c:s.key)key.push_back(static_cast<char>(c));result={reader.find_field(s.a,key)};break;}
                }
                compare(result,s.result,"navigation result");compare({reader.position(),reader.root()},s.state,"navigation cursor/root");
                if(s.op!=Operation::seek)++checks;
                ++number;
            }
        }
        std::cout<<"PASS "<<checks<<" indexed RTON reader ARM return/cursor checkpoints\n";
    }catch(const std::exception& e){std::cerr<<label<<" step "<<number<<": "<<e.what()<<'\n';return 1;}
}
