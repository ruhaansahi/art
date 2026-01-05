#include <algorithm>
#include <cmath>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Coordinates use y-up geometry. Every output pixel occupies two columns.
static const std::vector<std::string> names = {"square", "rectangle", "triangle", "inverted-triangle", "diamond", "circle", "heart", "star", "arrow", "cross", "hourglass", "hexagon"};

bool star(double x, double y) {
    constexpr double pi = 3.14159265358979323846;
    std::vector<std::pair<double, double>> points;
    for (int i = 0; i < 10; ++i) {
        double angle = pi / 2 + i * pi / 5;
        double radius = i % 2 == 0 ? 0.98 : 0.43;
        points.emplace_back(radius * std::cos(angle), radius * std::sin(angle));
    }
    bool inside = false;
    for (int i = 0, j = 9; i < 10; j = i++) {
        auto [xi, yi] = points[i];
        auto [xj, yj] = points[j];
        if ((yi > y) != (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            inside = !inside;
    }
    return inside;
}

bool mask(const std::string& shape, double x, double y) {
    double ax = std::abs(x), ay = std::abs(y);
    if (shape == "square") return ax <= .8 && ay <= .8;
    if (shape == "rectangle") return ax <= .95 && ay <= .55;
    if (shape == "inverted-triangle") return mask("triangle", x, -y);
    if (shape == "triangle") return y >= -.85 && y <= .9 && ax <= (.9 - y) * .54;
    if (shape == "diamond") return ax + ay <= .95;
    if (shape == "circle") return x * x + y * y <= .81;
    if (shape == "heart") {
        double hx = x * 1.25, hy = y * 1.25 + .15;
        double a = hx * hx + hy * hy - 1;
        return a * a * a - hx * hx * hy * hy * hy <= 0;
    }
    if (shape == "star") return star(x, y);
    if (shape == "arrow")
        return (ax <= .24 && y >= -.9 && y <= .15) ||
               (y >= -.05 && y <= .95 && ax <= (.95 - y) * .95);
    if (shape == "cross") return (ax <= .27 && ay <= .9) || (ax <= .9 && ay <= .27);
    if (shape == "hourglass") return ay <= .9 && ax <= std::max(.06, ay);
    if (shape == "hexagon") return ay <= .8 && ax <= .95 - .5 * ay;
    return false;
}

std::vector<std::string> raster(const std::string& shape, int size, bool outline) {
    std::vector<std::vector<bool>> pixels(size, std::vector<bool>(size));
    for (int row = 0; row < size; ++row)
        for (int col = 0; col < size; ++col)
            pixels[row][col] = mask(shape, 2.0 * col / (size - 1) - 1,
                                    1 - 2.0 * row / (size - 1));
    std::vector<std::string> lines(size);
    for (int row = 0; row < size; ++row) {
        for (int col = 0; col < size; ++col) {
            bool on = pixels[row][col];
            if (on && outline && row > 0 && row + 1 < size && col > 0 && col + 1 < size)
                on = !(pixels[row - 1][col] && pixels[row + 1][col] &&
                       pixels[row][col - 1] && pixels[row][col + 1]);
            lines[row] += on ? "**" : "  ";
        }
    }
    return lines;
}

int integer(const std::string& text) { return std::stoi(text); }

int main(int argc, char** argv) {
    try {
        int rows=1, cols=1, size=21;
        std::string sequence="heart", style="filled";
        for (int i=1;i<argc;++i) {
            std::string arg=argv[i];
            if(arg=="--outline") {style="outline";continue;}
            if(i+1>=argc) throw std::runtime_error("An option needs a value");
            std::string value=argv[++i];
            if(arg=="--sequence") sequence=value;
            else if(arg=="--size") size=integer(value);
            else throw std::runtime_error("Unknown option: "+arg);
        }
        std::vector<std::string> shapes(rows*cols,sequence);
        std::vector<std::vector<std::string>> cells;
        for(const auto& shape:shapes) cells.push_back(raster(shape,size,style=="outline"));
        for(int row=0;row<rows;++row) {
            for(int pixel=0;pixel<size;++pixel) {
                for(int col=0;col<cols;++col) {
                    if(col) std::cout<<"    ";
                    std::cout<<cells[row*cols+col][pixel];
                }
                std::cout<<'\n';
            }
        }
    } catch(const std::exception& error) {
        std::cerr<<"art: "<<error.what()<<'\n';
        return 2;
    }
}
