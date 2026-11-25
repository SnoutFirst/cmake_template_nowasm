add_executable(intro main.cpp)

target_link_libraries(
  intro
  PRIVATE cmake_template_nowasm::cmake_template_nowasm_options
          cmake_template_nowasm::cmake_template_nowasm_warnings
          CLI11::CLI11
          fmt::fmt
          spdlog::spdlog
          lefticus::tools
          ftxui::screen
          ftxui::dom
          ftxui::component)


cmake_template_nowasm_configure_linker(intro)

target_include_directories(intro PRIVATE "${CMAKE_BINARY_DIR}/configured_files/include")

# Apply WASM-specific configuration
if(EMSCRIPTEN)
  cmake_template_nowasm_configure_wasm_target(intro
    TITLE "Intro - FTXUI Sample"
    DESCRIPTION "FTXUI-based terminal application"
  )
endif()
