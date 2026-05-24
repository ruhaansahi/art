#pragma once
#include <cstdint>
#include <limits>

namespace mathart {
constexpr double pi = 3.14159265358979323846;
double clamp(double v, double low = 0, double high = 1) { return std::max(low, std::min(high, v)); }
double mix(double a, double b, double t) { return a+(b-a)*t; }

double wrap(double v) { return v-2*std::floor((v+1)/2); }

double fade(double t) { return t*t*t*(t*(t*6-15)+10); }

std::uint32_t hash(int x, int y, unsigned seed) {
    auto h = static_cast<std::uint32_t>(x)*374761393u + static_cast<std::uint32_t>(y)*668265263u + seed;
    h = (h^(h>>13))*1274126177u;
    return h^(h>>16);
}

double gradient(int x, int y, double dx, double dy, unsigned seed) {
    double angle = (hash(x,y,seed)%65536)*2*pi/65536;
    return std::cos(angle)*dx+std::sin(angle)*dy;
}

double perlin(double x, double y, unsigned seed) {
    int ix=static_cast<int>(std::floor(x)), iy=static_cast<int>(std::floor(y));
    double dx=x-ix, dy=y-iy, u=fade(dx), v=fade(dy);
    return mix(mix(gradient(ix,iy,dx,dy,seed),gradient(ix+1,iy,dx-1,dy,seed),u),
               mix(gradient(ix,iy+1,dx,dy-1,seed),gradient(ix+1,iy+1,dx-1,dy-1,seed),u),v);
}

double noise(double x, double y, unsigned seed) {
    double sum=0, amplitude=.55;
    for (int i=0;i<4;++i) { sum+=amplitude*perlin(x,y,seed+i*31); x*=2; y*=2; amplitude*=.5; }
    return sum;
}

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
    if(o.shape=="moire") {
        double a=.14+o.time*.08, rx=x*std::cos(a)-y*std::sin(a),ry=x*std::sin(a)+y*std::cos(a);
        double rings=std::cos(35*std::hypot(x+.13,y-.08)+o.time);
        double grid=std::cos(35*rx)*std::cos(35*ry);
        return clamp(.5+.25*(rings+grid));
    }
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
