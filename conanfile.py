# pylint: disable=not-callable
import os
import re

from conan import ConanFile
from conan.tools.cmake import CMake
from conan.tools.cmake import cmake_layout
from conan.tools.cmake import CMakeDeps
from conan.tools.cmake import CMakeToolchain
from conan.tools.files import collect_libs
from conan.tools.files import load


class ToxConan(ConanFile):
    name = "toxcore"
    url = "https://tox.chat"
    description = "The future of online communications."
    license = "GPL-3.0-only"
    settings = "os", "compiler", "build_type", "arch"
    requires = (
        "libsodium/1.0.20",
        "opus/1.4",
        "libvpx/1.14.1",
    )
    scm = {"type": "git", "url": "auto", "revision": "auto"}

    options = {
        "shared": [True, False],
        "with_tests": [True, False],
    }
    default_options = {
        "shared": False,
        "with_tests": False,
    }

    def set_version(self):
        content = load(self, os.path.join(self.recipe_folder,
                                          "CMakeLists.txt"))
        version_major = re.search(r"set\(PROJECT_VERSION_MAJOR \"(.*)\"\)",
                                  content).group(1)
        version_minor = re.search(r"set\(PROJECT_VERSION_MINOR \"(.*)\"\)",
                                  content).group(1)
        version_patch = re.search(r"set\(PROJECT_VERSION_PATCH \"(.*)\"\)",
                                  content).group(1)
        self.version = "%s.%s.%s" % (
            version_major.strip(),
            version_minor.strip(),
            version_patch.strip(),
        )

    def requirements(self):
        if self.settings.os == "Windows":
            self.requires("pthreads4w/3.0.0")
        if self.options.with_tests:
            self.build_requires("gtest/1.15.0")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables["AUTOTEST"] = self.options.with_tests
        tc.variables["BUILD_MISC_TESTS"] = self.options.with_tests
        tc.variables["UNITTEST"] = self.options.with_tests
        tc.variables["TEST_TIMEOUT_SECONDS"] = "300"

        tc.variables["ENABLE_SHARED"] = self.options.shared
        tc.variables["ENABLE_STATIC"] = not self.options.shared

        tc.variables["MUST_BUILD_TOXAV"] = True

        if self.settings.os == "Windows":
            tc.variables["MSVC_STATIC_SODIUM"] = True
            tc.variables[
                "CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = self.options.shared
            tc.variables["FLAT_OUTPUT_STRUCTURE"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
        if self.options.with_tests:
            cmake.ctest(cli_args=["--output-on-failure"])

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)

        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["Ws2_32", "Iphlpapi"]
