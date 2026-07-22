#pragma once
#include <cstdint>
#include <limits>

namespace mathart {
constexpr double pi = 3.14159265358979323846;
double clamp(double v, double low = 0, double high = 1) { return std::max(low, std::min(high, v)); }
struct Vec {
    double x,y,z;
    Vec operator+(Vec b) const {return {x+b.x,y+b.y,z+b.z};}
    Vec operator-(Vec b) const {return {x-b.x,y-b.y,z-b.z};}
    Vec operator*(double k) const {return {x*k,y*k,z*k};}
};
double dot(Vec a, Vec b) { return a.x*b.x+a.y*b.y+a.z*b.z; }

double length(Vec v) { return std::sqrt(dot(v,v)); }

Vec unit(Vec v) { return v*(1/std::max(1e-10,length(v))); }

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
double number(const std::string& text) {return std::stod(text);}
bool one_of(const std::string& v, const std::vector<std::string>& values) {
    return std::find(values.begin(),values.end(),v)!=values.end();
}
double torus(Vec p, double t) {
    double a=t*.65+.5, b=t*.37+.25;
    Vec q={p.x, std::cos(a)*p.y-std::sin(a)*p.z, std::sin(a)*p.y+std::cos(a)*p.z};
    p={std::cos(b)*q.x-std::sin(b)*q.z,q.y,std::sin(b)*q.x+std::cos(b)*q.z};
    double ring=std::hypot(p.x,p.z)-.65;
    return std::hypot(ring,p.y)-.25;
}
double donut(double x,double y,double t) {
    Vec origin={0,0,3}, direction=unit({x*.75,y*.75,-2});
    double travel=0;
    for(int i=0;i<100 && travel<7;++i) {
        Vec p=origin+direction*travel;
        double distance=torus(p,t);
        if(distance<.001) {
            constexpr double e=.001;
            Vec normal=unit({torus(p+Vec{e,0,0},t)-torus(p-Vec{e,0,0},t),
                             torus(p+Vec{0,e,0},t)-torus(p-Vec{0,e,0},t),
                             torus(p+Vec{0,0,e},t)-torus(p-Vec{0,0,e},t)});
            Vec light=unit({-.6,.8,1});
            double diffuse=std::max(0.0,dot(normal,light));
            return clamp(.14+.72*diffuse);
        }
        travel+=std::max(.0005,distance);
    }
    return 0;
}
double smooth_min(double a,double b,double k) {
    double h=clamp(.5+.5*(b-a)/k);
    return mix(b,a,h)-k*h*(1-h);
}
double fractal(double x,double y,double t,bool julia) {
    double cr=julia ? -.74+.05*std::cos(t*.3) : x*1.4-.45;
    double ci=julia ? .21+.04*std::sin(t*.3) : y*1.4;
    double zr=julia?x*1.5:0, zi=julia?y*1.5:0;
    for(int i=0;i<100;++i) {
        double next=zr*zr-zi*zi+cr;
        zi=2*zr*zi+ci; zr=next;
        if(zr*zr+zi*zi>64) return std::pow(i/100.0,.5);
    }
    return 1;
}
std::vector<double> clifford(double t) {
    std::vector<double> density(256*256);
    double x=.1,y=.1,a=-1.4+.05*std::sin(t),b=1.6,c=1,d=.7;
    for(int i=0;i<90000;++i) {
        double nx=std::sin(a*y)+c*std::cos(a*x), ny=std::sin(b*x)+d*std::cos(b*y);
        x=nx;y=ny;
        if(i<100) continue;
        int ix=static_cast<int>((x+2)*63.75),iy=static_cast<int>((2-y)*63.75);
        if(ix>=0&&ix<256&&iy>=0&&iy<256) density[iy*256+ix]+=1;
    }
    for(double& v:density) v=clamp(std::log1p(v)/4);
    return density;
}
void coordinates(double& x,double& y,const Options& o) {
    (void)x;(void)y;(void)o;
}
double field(double x,double y,const Options& o,const std::vector<double>& density) {
    if(o.shape=="donut") return donut(x,y,o.time);
    if(o.shape=="fractal"||o.shape=="julia") return fractal(x,y,o.time,o.shape=="julia");
    if(o.shape=="circle") return clamp((.7-std::hypot(x,y))*5);
    if(o.shape=="star") {
        double r=std::hypot(x,y),a=std::atan2(y,x);
        return clamp((.58+.24*std::cos(5*(a-pi/2))-r)*6);
    }
    if(o.shape=="metaball") {
        double distance=10;
        for(int i=0;i<4;++i) {
            double phase=o.time*.7+i*pi/2;
            double cx=.53*std::cos(phase),cy=.38*std::sin(phase*1.3+i);
            distance=smooth_min(distance,std::hypot(x-cx,y-cy)-.29,.38);
        }
        return clamp(.5-distance*4);
    }
    if(o.shape=="moire") {
        double a=.14+o.time*.08, rx=x*std::cos(a)-y*std::sin(a),ry=x*std::sin(a)+y*std::cos(a);
        double rings=std::cos(35*std::hypot(x+.13,y-.08)+o.time);
        double grid=std::cos(35*rx)*std::cos(35*ry);
        return clamp(.5+.25*(rings+grid));
    }
    if(o.shape=="clifford") {
        int ix=static_cast<int>((x+1)*127.5),iy=static_cast<int>((1-y)*127.5);
        if(ix<0||ix>=256||iy<0||iy>=256) return 0;
        double v=0;
        for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx)
            if(ix+dx>=0&&ix+dx<256&&iy+dy>=0&&iy+dy<256)
                v=std::max(v,density[(iy+dy)*256+ix+dx]);
        return v;
    }
    return 0;
}
void draw(const Options& o) {
    auto density=o.shape=="clifford"?clifford(o.time):std::vector<double>{};
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
        else if(arg=="--time") o.time=number(take());
        else throw std::runtime_error("Unknown math option: "+arg);
    }
    if(!one_of(o.shape,{"circle","star","metaball","fractal","moire","julia","clifford","donut"})) throw std::runtime_error("Unknown math shape");
    draw(o);
    return 0;
}
} // namespace mathart
