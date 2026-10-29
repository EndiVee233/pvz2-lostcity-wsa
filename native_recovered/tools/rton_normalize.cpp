#include "engine_rton_normalizer.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
int main(int argc,char** argv) {
    if(argc!=3) {std::cerr<<"Usage: rton_normalize plaintext.rton indexed.rton\n";return 2;}
    try {
        std::ifstream input(argv[1],std::ios::binary);if(!input)throw std::runtime_error("cannot open input");
        std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),std::istreambuf_iterator<char>());
        const auto result=pvz2_recovered::engine::normalize_rton(std::move(bytes));
        if(!result.success)throw std::runtime_error("invalid raw RTON header or trailer");
        std::ofstream output(argv[2],std::ios::binary);if(!output)throw std::runtime_error("cannot open output");
        output.write(reinterpret_cast<const char*>(result.bytes.data()),static_cast<std::streamsize>(result.bytes.size()));
        if(!output)throw std::runtime_error("output write failed");
        std::cout<<"Normalized "<<result.input_consumed<<" input bytes to "<<result.bytes.size()<<" indexed bytes; "<<result.narrow_strings.size()<<" narrow / "<<result.wide_strings.size()<<" wide strings\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
