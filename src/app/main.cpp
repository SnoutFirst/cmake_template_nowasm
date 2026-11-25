#include <CLI/CLI.hpp>
#include <cstdlib>
#include <exception>
#include <fmt/base.h>
#include <fmt/format.h>
#include <spdlog/spdlog.h>
#include <string>

// This file will be generated automatically when you run the CMake
// configuration step. It creates a namespace called `cmake_template_nowasm`. You can modify
// the source template at `configured_files/config.hpp.in`.
#include <internal_use_only/config.hpp>

// NOLINTNEXTLINE(bugprone-exception-escape)
int main(int argc, const char **argv)
{
  try {
    CLI::App app{ fmt::format(
      "{} version {}", cmake_template_nowasm::cmake::project_name, cmake_template_nowasm::cmake::project_version) };

    std::string name{ "world" };
    app.add_option("-n,--name", name, "Name to greet");

    bool show_version = false;
    app.add_flag("--version", show_version, "Show version information");

    CLI11_PARSE(app, argc, argv);

    if (show_version) {
      fmt::print("{}\n", cmake_template_nowasm::cmake::project_version);
      return EXIT_SUCCESS;
    }

    fmt::print("Hello, {}!\n", name);
  } catch (const std::exception &e) {
    spdlog::error("Unhandled exception in main: {}", e.what());
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
