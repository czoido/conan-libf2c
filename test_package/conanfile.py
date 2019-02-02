import os

from conans import ConanFile, CMake, tools


class Libf2cTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        # because the runtime will call Fortran _MAIN__     
        if self.settings.os == "Linux" and self.settings.compiler == "clang" and self.options["libf2c"].shared:
            cmake.definitions["CMAKE_CXX_FLAGS"] = "-Wl,--undefined=MAIN__"
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.dylib*", dst="bin", src="lib")
        self.copy('*.so*', dst='bin', src='lib')

    def test(self):
        if not tools.cross_building(self.settings):
            os.chdir("bin")
            self.run(".%sexample" % os.sep)
