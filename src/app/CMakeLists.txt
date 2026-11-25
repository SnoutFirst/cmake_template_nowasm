add_executable(cmake_template_nowasm main.cpp)

target_link_libraries(
  cmake_template_nowasm
  PRIVATE cmake_template_nowasm::cmake_template_nowasm_options
          cmake_template_nowasm::cmake_template_nowasm_warnings
          CLI11::CLI11
          fmt::fmt
          spdlog::spdlog)

cmake_template_nowasm_configure_linker(cmake_template_nowasm)

target_include_directories(cmake_template_nowasm PRIVATE "${CMAKE_BINARY_DIR}/configured_files/include")
