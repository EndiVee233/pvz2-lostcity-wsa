#include "engine_rton_input.hpp"
#include "engine_rton_writer.hpp"
#include <iostream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
enum class Operation {read,var32,var64,zig32,zig64,narrow,wide,codepoint,utf8,decode,header};
enum class WriterKind {none,varuint,narrow,utf8};
struct Step {Operation op;std::uint32_t a;std::vector<std::uint32_t> result,state;};
struct Scenario {const char* label;std::vector<std::uint32_t> data;std::uint32_t original_buffer_mode;WriterKind writer;std::vector<std::uint32_t> writer_value;std::vector<Step> steps;};
#include "rton_input_fixtures.inc"
void compare(const std::vector<std::uint32_t>& a,const std::vector<std::uint32_t>& b,const char* what) {
    if(a.size()!=b.size())throw std::runtime_error(std::string(what)+" length differs from ARM: "+std::to_string(a.size())+" vs "+std::to_string(b.size()));
    for(std::size_t i=0;i<a.size();++i)if(a[i]!=b[i])throw std::runtime_error(std::string(what)+" value "+std::to_string(i)+": "+std::to_string(a[i])+" vs ARM "+std::to_string(b[i]));
}
int main() {
    unsigned checks=0,number=0;const char* label="initialization";
    try {
        for(const auto& sc:scenarios) {
            label=sc.label;number=0;std::vector<std::uint8_t> data;for(auto v:sc.data)data.push_back(static_cast<std::uint8_t>(v));
            if(sc.writer!=WriterKind::none) {
                RtonWriter writer;
                if(sc.writer==WriterKind::varuint)for(auto v:sc.writer_value)writer.varuint(v);
                else if(sc.writer==WriterKind::narrow) {std::string text;for(auto v:sc.writer_value)text.push_back(static_cast<char>(v));writer.string({},text);}
                else {std::u32string text;for(auto v:sc.writer_value)text.push_back(static_cast<char32_t>(v));writer.wide_string({},text);}
                compare(std::vector<std::uint32_t>(writer.bytes().begin(),writer.bytes().end()),sc.data,"writer input bytes");
            }
            RtonInput input(data);
            for(const auto& s:sc.steps) {
                std::vector<std::uint32_t> result;
                switch(s.op) {
                case Operation::read: {const auto v=input.read_bytes(s.a);result.assign(v.begin(),v.end());break;}
                case Operation::var32:result={input.varuint32()};break;
                case Operation::zig32:result={input.zigzag32()};break;
                case Operation::var64:
                case Operation::zig64: {const auto v=s.op==Operation::var64?input.varuint64():input.zigzag64();result={static_cast<std::uint32_t>(v),static_cast<std::uint32_t>(v>>32)};break;}
                case Operation::narrow: {const auto v=input.raw_string();for(unsigned char c:v)result.push_back(c);break;}
                case Operation::wide:
                case Operation::utf8: {const auto v=s.op==Operation::wide?input.raw_wide_string():input.utf8_string();for(auto c:v)result.push_back(static_cast<std::uint32_t>(c));break;}
                case Operation::codepoint:result={input.utf8_codepoint()};break;
                case Operation::decode: {
                    std::uint32_t value=0xdecafbadU;const auto pos=input.position();
                    const auto consumed=decode_engine_utf8(data.empty()?nullptr:data.data()+pos,data.size()-pos,value);
                    result={static_cast<std::uint32_t>(consumed),value,static_cast<std::uint32_t>(consumed)};break;
                }
                case Operation::header:result={input.normalized_header()?1U:0U};break;
                }
                compare(result,s.result,"read result");
                compare({static_cast<std::uint32_t>(input.position()),input.root_offset(),input.header_read_mode()?1U:0U},s.state,"read state");
                ++checks;++number;
            }
        }
        std::cout<<"PASS "<<checks<<" RTON input ARM value/position checkpoints\n";
    }catch(const std::exception& e){std::cerr<<label<<" step "<<number<<": "<<e.what()<<'\n';return 1;}
}
