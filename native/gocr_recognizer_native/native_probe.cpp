// Standalone regression probe; no models, interpreter or Python dependencies.
#include "image_ops.h"
#include "sha256.h"
#include "unicode.h"
#include <cstdio>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::string unhex(const std::string& s) {
    if (s.size()%2) throw std::runtime_error("invalid hex");
    std::string out;
    for (size_t i=0;i<s.size();i+=2) out+=char(std::stoi(s.substr(i,2),nullptr,16));
    return out;
}
static std::string hex(const std::string& s) {
    std::string out;
    for (unsigned char c:s) { char b[3]; std::snprintf(b,3,"%02x",c); out+=b; }
    return out;
}
int main(int argc,char** argv) {
    try {
        if (argc<2) throw std::runtime_error("mode required");
        std::string mode=argv[1];
        if (mode=="nfc" || mode=="sha") {
            std::string line;
            while (std::getline(std::cin,line)) {
                auto value=unhex(line);
                if (mode=="nfc") std::cout<<hex(gocr::nfc_strip(value))<<'\n';
                else { gocr::Sha256 s; s.update(value.data(),value.size()); std::cout<<s.finish()<<'\n'; }
            }
            return 0;
        }
        if (argc<4) throw std::runtime_error("image input and output required");
        std::ifstream input(argv[2],std::ios::binary);
        std::string magic; int w,h,maximum;
        input>>magic>>w>>h>>maximum; input.get();
        if (!input || (magic!="P6" && magic!="P5") || w<1 || h<1 || maximum!=255)
            throw std::runtime_error("invalid probe PPM/PGM");
        int channels=magic=="P6" ? 3 : 1;
        std::vector<uint8_t> bytes(size_t(w)*h*channels);
        input.read(reinterpret_cast<char*>(bytes.data()),std::streamsize(bytes.size()));
        if (!input) throw std::runtime_error("truncated image");
        std::ofstream output(argv[3],std::ios::binary);
        if (mode=="rectify") {
            if (argc!=12 || channels!=3) throw std::runtime_error("RGB quad required");
            double quad[8];
            for (int i=0;i<8;++i) quad[i]=std::stod(argv[4+i]);
            auto crop=gocr::rectify(bytes.data(),w,h,quad);
            output<<"P6\n"<<crop.width<<' '<<crop.height<<"\n255\n";
            output.write(reinterpret_cast<char*>(crop.pixels.data()),std::streamsize(crop.pixels.size()));
        } else if (mode=="windows") {
            auto gray=gocr::normalize_line(bytes.data(),w,h,channels);
            std::vector<uint8_t> window(32*168);
            for (int x=0;x<gray.width;x+=136) {
                gocr::make_window(gray,x,window.data());
                output.write(reinterpret_cast<char*>(window.data()),std::streamsize(window.size()));
            }
        } else throw std::runtime_error("unknown probe mode");
        if (!output) throw std::runtime_error("probe write failed");
        return 0;
    } catch (const std::exception& exc) { std::cerr<<exc.what()<<'\n'; return 1; }
}
