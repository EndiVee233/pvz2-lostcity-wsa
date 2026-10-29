#include "engine_rton_reader.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
using namespace pvz2_recovered::engine;
std::string quote(std::string_view text) {
    constexpr char hex[]="0123456789abcdef";std::string out="\"";
    for(unsigned char c:text) {
        if(c=='"' || c=='\\') {out.push_back('\\');out.push_back(static_cast<char>(c));}
        else if(c<32) {out+="\\u00";out.push_back(hex[c>>4]);out.push_back(hex[c&15]);}
        else out.push_back(static_cast<char>(c));
    }
    out.push_back('"');return out;
}
std::uint32_t member(IndexedRtonReader& reader,std::uint32_t object,std::string_view name) {return reader.value_offset(reader.find_field(object,name));}
std::string value_text(IndexedRtonReader& reader,std::uint32_t value) {return reader.narrow_text_at(reader.narrow_value_offset(value));}
int main(int argc,char** argv) {
    if(argc!=3) {std::cerr<<"Usage: rton_inspect plaintext.rton summary.json\n";return 2;}
    try {
        std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("cannot open input");
        std::vector<std::uint8_t> data((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());
        auto doc=normalize_rton(std::move(data));if(!doc.success)throw std::runtime_error("invalid raw RTON header/trailer");
        IndexedRtonReader reader(std::move(doc));if(!reader.valid())throw std::runtime_error("invalid indexed header");
        std::ostringstream out;out<<"{\n  \"root_fields\": [";bool comma=false;
        for(auto field=reader.first_field(reader.root());field;field=reader.next_field(field)) {
            reader.seek(field);const auto kind=reader.peek();if(kind!=0xb4 && kind!=0xb5)throw std::runtime_error("summary tool requires narrow root keys");
            const auto key=reader.narrow_text_at(reader.key_text_offset(field));const auto value=reader.value_offset(field);reader.seek(value);const auto tag=reader.peek();
            if(comma)out<<',';
            comma=true;out<<"\n    {\"key\": "<<quote(key)<<", \"key_offset\": "<<field<<", \"value_offset\": "<<value<<", \"tag\": "<<static_cast<unsigned>(tag)<<'}';
        }
        const auto objects=member(reader,reader.root(),"objects");const auto count=reader.array_count(objects);
        const auto version_bits=reader.scalar_int32_bits(member(reader,reader.root(),"version"));
        const auto version=version_bits>=0x80000000U?static_cast<std::int64_t>(version_bits)-0x100000000LL:static_cast<std::int64_t>(version_bits);
        out<<"\n  ],\n  \"version\": "<<version<<",\n  \"object_count\": "<<count<<",\n  \"objects\": [";
        for(std::uint32_t i=0;i<count;++i) {
            const auto object=reader.array_element(objects,i);const auto aliases=member(reader,object,"aliases");const auto alias_count=reader.array_count(aliases);
            const auto name=value_text(reader,member(reader,object,"objclass"));if(i)out<<',';
            out<<"\n    {\"index\": "<<i<<", \"objclass\": "<<quote(name)<<", \"aliases\": [";
            for(std::uint32_t j=0;j<alias_count;++j) {if(j)out<<", ";out<<quote(value_text(reader,reader.array_element(aliases,j)));}
            out<<"]}";
        }
        out<<"\n  ]\n}\n";
        std::ofstream output(argv[2],std::ios::binary);if(!output)throw std::runtime_error("cannot open output");output<<out.str();if(!output)throw std::runtime_error("summary write failed");
        std::cout<<"Inspected "<<count<<" object declarations; summary saved\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
