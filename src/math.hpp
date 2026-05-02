#pragma once
#include <cstdint>
#include <limits>

namespace mathart {
constexpr double pi = 3.14159265358979323846;
double clamp(double v, double low = 0, double high = 1) { return std::max(low, std::min(high, v)); }
double mix(double a, double b, double t) { return a+(b-a)*t; }

struct Options {
    std::string shape="moire", matrix="grid", shading="solid", ramp=" .:-=+*#%@";
    int width=120, height=40;
    unsigned seed=20261022;
    double scale=1, rotation=0, skew_x=0, skew_y=0, time=0;
};
void coordinates(double& x,double& y,const Options& o) {
    (void)x;(void)y;(void)o;
}
double field(double x,double y,const Options& o,const std::vector<double>& density) {
    if(o.shape=="circle") return std::hypot(x,y)<.7?1:0;
    return 0;
}
void draw(const Options& o) {
    std::vector<double> density;
    for(int row=0;row<o.height;++row) {
        for(int col=0;col<o.width;++col) {
            double x=(2.0*col/(o.width-1)-1)*(o.width/static_cast<double>(o.height))*.5;
            double y=1-2.0*row/(o.height-1);
            coordinates(x,y,o);
            double value=clamp(field(x,y,o,density));
            char pixel=' ';
            if(o.shading=="solid") pixel=value>.22?'*':' ';
            std::cout<<pixel;
        }
        std::cout<<'\n';
    }
}
int run(int argc,char** argv) {
    Options o;
    for(int i=1;i<argc;++i) {
        std::string arg=argv[i];
        auto take=[&]() {if(i+1>=argc) throw std::runtime_error("Missing value for "+arg);return std::string(argv[++i]);};
        if(arg=="--shape") o.shape=take();
        else throw std::runtime_error("Unknown math option: "+arg);
    }
    draw(o);
    return 0;
}
} // namespace mathart
