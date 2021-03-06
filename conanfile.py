import os

from conans import ConanFile, tools


class Libf2cConan(ConanFile):
    name = "libf2c"
    version = "20181026"
    license = "HPND"
    url = "https://github.com/czoido/conan-libf2c"
    homepage = "https://www.netlib.org/f2c/"
    description = "libf2c is a library to convert Fortran 77 to C code."
    topics = ("fortran", "algebra", "matrix")
    generators = "cmake"

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False],
               "fPIC": [True, False]}
    default_options = "shared=False", "fPIC=True"
    _source_subfolder = "libf2c_sources"
    _targets = ["hadd", "f2c.h", "signal1.h", "sysdep1.h"]

    def source(self):
        tools.get("http://www.netlib.org/f2c/libf2c.zip",
                  sha256="ca404070e9ce0a9aaa6a71fc7d5489d014ade952c5d6de7efb88de8e24f2e8e0",
                  destination=self._source_subfolder)

    def build(self):
        def add_cflag(value):
            tools.replace_in_file("Makefile", "CFLAGS = ", "CFLAGS = %s " % value)

        arch = self.settings.arch
        if self.settings.os == "Windows":
            with (tools.vcvars(self.settings)):
                nmake = tools.which('nmake')
                if not nmake:
                    raise Exception("This package needs 'nmake' in Windows in the path to build")
        else:
            make = tools.get_env("CONAN_MAKE_PROGRAM", tools.which("make") or tools.which('nmake'))
            if not make:
                raise Exception("This package needs 'make' in Linux/Macos in the path to build")


        if self.settings.os == "Windows":
            if self.options.shared:
                self.output.warn("shared option is disabled for Windows. Setting to false")
                self.options.shared = False

        with tools.chdir(self._source_subfolder):
            os.rename("makefile.u", "Makefile")

            if self.options.fPIC or self.options.shared:
                add_cflag('-fPIC')

            if self.settings.os == "Macos":
                if self.options.shared:
                    # create the dynamic library; undefined dynamic lookup is needed
                    # because the runtime will call Fortran _MAIN__                    
                    tools.replace_in_file("Makefile", "libf2c.so: $(OFILES)", "libf2c.dylib: $(OFILES)")
                    tools.replace_in_file("Makefile", "$(CC) -shared -o libf2c.so $(OFILES)",
                                          "$(CC) -dynamiclib -all_load -headerpad_max_install_names -undefined dynamic_lookup -single_module -o libf2c.dylib $(OFILES)")
                    self._targets.append("libf2c.dylib")
                else:
                    self._targets.append("libf2c.a")
            elif self.settings.os == "Linux":
                add_cflag('-DNON_UNIX_STDIO')
                if self.options.shared:
                    self._targets.append("libf2c.so")
                else:
                    self._targets.append("libf2c.a")

            if self.settings.os == "Windows":
                vcvars = tools.vcvars_command(self.settings)
                build_command = "nmake -f makefile.vc"
                self.run("%s && %s" % (vcvars, build_command))
            else:
                self.run("%s arch=%s %s" % (make, arch, " ".join(self._targets)))

    def package(self):
        self.copy("Notice", dst="licenses", src=self._source_subfolder)
        self.copy("f2c.h", dst="include", src=self._source_subfolder)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["vcf2c"]
        else:
            self.cpp_info.libs = ["f2c"]
