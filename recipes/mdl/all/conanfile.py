import os
import shutil

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import Environment
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    replace_in_file,
    rmdir,
)
from conan.tools.microsoft import check_min_vs, is_msvc_static_runtime

required_conan_version = ">=1.53.0"


class MdlConan(ConanFile):
    name = "mdl"
    description = "The NVIDIA Material Definition Language (MDL) SDK is an open source set of tools that enable the integration of physically-based materials into rendering applications."
    license = "BSD 3-Clause License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/NVIDIA/MDL-SDK"
    topics = ("game-development",)

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "use_cuda": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "use_cuda": False,
    }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.84.0")
        self.requires("openimageio/2.5.18.0")
        self.requires("zstd/1.5.6", override=True)
        self.requires("libdeflate/1.22", override=True)
        self.requires("openexr/3.2.3", override=True)
        self.requires("llvm-core/19.1.7")
        self.requires("cpython/3.10.14", options={"shared": True})

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.21 <4]")

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def validate(self):
        if self.settings.os not in [
            "Windows",
            "Linux",
            "FreeBSD",
            "Macos",
            "Android",
            "iOS",
        ]:
            raise ConanInvalidConfiguration(f"{self.settings.os} is not supported")

        if not self.options.shared:
            raise ConanInvalidConfiguration("Static builds are not supported")
        if self.settings.build_type not in ["Debug", "RelWithDebInfo", "Release"]:
            raise ConanInvalidConfiguration(f"{self.settings.build_type} build_type is not supported")

        check_min_vs(self, 150)
        check_min_cppstd(self, 11)

    def generate(self):
        tc = CMakeToolchain(self)

        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        if self.settings.os == "Windows":
            tc.variables["MDL_MSVC_DYNAMIC_RUNTIME"] = False
        # Convert all paths to use forward slashes
        source_folder = self.source_folder.replace("\\", "/")
        tc.variables["MDL_BASE_FOLDER"] = source_folder
        tc.variables["MDL_INCLUDE_FOLDER"] = f"{source_folder}/include"
        tc.variables["MDL_SRC_FOLDER"] = f"{source_folder}/src"
        tc.variables["MDL_EXAMPLES_FOLDER"] = f"{source_folder}/examples"
        tc.variables["MDL_DOC_FOLDER"] = f"{source_folder}/doc"

        tc.variables["MDL_USE_LOCAL_DEPENDENCIES"] = True
        tc.variables["MDL_BUILD_SDK_EXAMPLES"] = False
        tc.variables["MDL_BUILD_CORE_EXAMPLES"] = False
        tc.variables["MDL_ENABLE_CUDA_EXAMPLES"] = False
        tc.variables["MDL_ENABLE_OPENGL_EXAMPLES"] = False
        tc.variables["MDL_ENABLE_VULKAN_EXAMPLES"] = False
        tc.variables["MDL_ENABLE_QT_EXAMPLES"] = False
        tc.variables["MDL_ENABLE_D3D12_EXAMPLES"] = False
        tc.variables["MDL_ENABLE_OPTIX7_EXAMPLES"] = False
        tc.variables["MDL_BUILD_ARNOLD_PLUGIN"] = False
        tc.variables["MDL_BUILD_WITHOUT_CUDA_DRIVER"] = not self.options.use_cuda
        tc.variables["MDL_BUILD_DOCUMENTATION"] = False
        tc.variables["MDL_TREAT_RUNTIME_DEPS_AS_BUILD_DEPS"] = False
        tc.variables["MDL_ENABLE_PYTHON_BINDINGS"] = False
        tc.variables["MDL_BUILD_ARNOLD_PLUGIN"] = False
        tc.variables["MDL_BUILD_DDS_PLUGIN"] = False
        tc.variables["MDL_BUILD_OPENIMAGEIO_PLUGIN"] = False

        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder=self.source_folder)
        cmake.build()

    def package(self):
        copy(self, "LICENSE.md",
            dst=self.package_folder,
            src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "mdl")
        self.cpp_info.set_property("cmake_target_name", "mdl::mdl")

        self.cpp_info.libs = ["mdl_core", "mdl_sdk"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.bindirs = ["bin"]

        if self.settings.os in ("FreeBSD", "Linux"):
            self.cpp_info.system_libs.append("m")
