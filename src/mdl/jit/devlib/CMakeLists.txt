set(PROJECT_NAME mdl-jit-devlib)

# collect sources
set(PROJECT_SOURCES
    "main.cpp"
    )

# create target from template
create_from_base_preset(
    TARGET ${PROJECT_NAME}
    TYPE EXECUTABLE
    SOURCES ${PROJECT_SOURCES}
)

# additional definitions
target_compile_definitions(${PROJECT_NAME} 
    PRIVATE 
        # LLVM include files require this
        "__STDC_CONSTANT_MACROS"
        "__STDC_FORMAT_MACROS"
        "__STDC_LIMIT_MACROS"
    )

if(NOT MSVC)
    # LLVM does not use RTTI
    target_compile_options(${PROJECT_NAME} 
        PRIVATE 
            "$<$<COMPILE_LANGUAGE:CXX>:-fno-rtti>"
        )
    target_compile_definitions(${PROJECT_NAME} 
        PRIVATE 
            "$<$<COMPILE_LANGUAGE:CXX>:NO_RTTI>"
        )
endif()

if(CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    # Suppress warning from LLVM code
    target_compile_options(${PROJECT_NAME}
        PRIVATE
            "-Wno-deprecated-declarations"
        )
endif()

# add dependencies
target_add_dependencies(TARGET ${PROJECT_NAME} 
    DEPENDS 
        llvm
        system
    )

# Add system libraries for Windows
if(MSVC)
    target_link_libraries(${PROJECT_NAME} PRIVATE
        msvcrt.lib
        ucrt.lib
        vcruntime.lib
        oldnames.lib
        libcmt.lib
    )
    
    # Add Windows-specific compile definitions
    target_compile_definitions(${PROJECT_NAME} PRIVATE
        WIN32_LEAN_AND_MEAN
        NOMINMAX
        WINVER=0x0601
        _WIN32_WINNT=0x0601
    )
endif() 