# %%myproject%%

[![ci](https://github.com/%%myorg%%/%%myproject%%/actions/workflows/ci.yml/badge.svg)](https://github.com/%%myorg%%/%%myproject%%/actions/workflows/ci.yml)
[![CodeQL](https://github.com/%%myorg%%/%%myproject%%/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/%%myorg%%/%%myproject%%/actions/workflows/codeql-analysis.yml)

%%description%%

Created from
[cmake_template_nowasm](https://github.com/SnoutFirst/cmake_template_nowasm),
the WASM-free variant of
[cpp-best-practices/cmake_template](https://github.com/cpp-best-practices/cmake_template),
by its cleanup workflow — the project name, the URLs and this file were
generated from your repository's name and description.

## Download

CI packages a Release build for Windows, macOS and Linux on every push to
`main` and attaches the archives to a rolling `ci-latest` GitHub Release, so no
build output is ever committed. Enable Pages once (Settings → Pages → *Deploy
from a branch* → `gh-pages` → `/`) and the download page appears at

**<https://%%myorg%%.github.io/%%myproject%%/>**

Tagged versions also get a GitHub Release with the CPack packages.

<!-- github-pages:start -->

## What it does

```sh
$ %%mysafeproject%% --name you
Hello, you!
```

It is deliberately tiny: the point of the template is the *surroundings*, not
the program. `--help` and a `--version` that matches what CMake was told are
covered by the tests, which also keep the CLI parsing (CLI11) and the
configured `config.hpp` exercised.

## What is in the box

* CMake ≥ 3.29, C++23, and the `%%mysafeproject%%_*` option namespace.
* Sanitizers (ASan/UBSan on by default where supported), hardening
  (`_FORTIFY_SOURCE`, stack protector, CFI on MSVC), warnings-as-errors,
  clang-tidy and cppcheck, IPO/LTO.
* CPM-fetched dependencies: fmt, spdlog, Catch2 and CLI11. A parent project can
  supply its own versions; every fetch is guarded by `if(NOT TARGET ...)`.
* Catch2 unit tests and constexpr tests, a libFuzzer harness that switches on
  when a fuzzing sanitizer is available, coverage collection with gcovr /
  OpenCppCoverage, and CPack packages whose names embed the compiler and the
  commit sha.
* A GitHub Actions matrix (Linux/macOS/Windows × GCC/Clang/MSVC ×
  Debug/Release, Ninja Multi-Config plus one plain Makefiles and four Visual
  Studio builds), CodeQL, the clang-format bot, Dependabot and the dev
  container.

<!-- github-pages:end -->

## Building

A C++23 compiler, CMake ≥ 3.29 and a generator are all you need; dependencies
are fetched with CPM at configure time:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build
```

Run the result with `./build/src/app/%%mysafeproject%%`
(`build\src\app\Release\%%mysafeproject%%.exe` for a multi-config build on
Windows).

Details, including the compiler-specific setup:

* [Building Details](README_building.md)
* [Dependency Setup](README_dependencies.md)
* [Design Choices](README_design.md)
* [Docker](README_docker.md)

## Testing

* `test/tests.cpp` — Catch2 unit tests (registered as `unittests.*`).
* `test/constexpr_tests.cpp` — the same checks at compile time (`constexpr.*`),
  plus a `relaxed_constexpr.*` build without `STATIC_REQUIRE` for debugging.
* `test/cmake/*.cmake` and `test/test_cmake_presets.cmake` — regression tests
  for the CMake modules themselves.
* `cli.*` — smoke tests for `--help`, `--version` and the greeting.
* `fuzz_test/` — libFuzzer harness, enabled automatically when a fuzzing
  sanitizer and libFuzzer are both available.
