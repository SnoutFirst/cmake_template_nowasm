# cmake_template_nowasm

[![ci](https://github.com/SnoutFirst/cmake_template_nowasm/actions/workflows/ci.yml/badge.svg)](https://github.com/SnoutFirst/cmake_template_nowasm/actions/workflows/ci.yml)
[![CodeQL](https://github.com/SnoutFirst/cmake_template_nowasm/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/SnoutFirst/cmake_template_nowasm/actions/workflows/codeql-analysis.yml)

A **WASM-free variant of
[cpp-best-practices/cmake_template](https://github.com/cpp-best-practices/cmake_template)**.

It keeps the upstream template's build system, testing infrastructure and
developer tooling exactly as they are — sanitizers, warnings-as-errors,
clang-tidy, cppcheck, hardening, Catch2 unit/constexpr tests, a libFuzzer
harness, CPack packaging and the large GitHub Actions matrix — and changes only
these things:

* the WebAssembly/Emscripten target, its workflow and its documentation are gone;
* the FTXUI example game is replaced by a minimal C++23 hello-world CLI.

## Download

Prebuilt Windows, macOS and Linux binaries are published to GitHub Pages by CI
on every push to `main`:

**<https://snoutfirst.github.io/cmake_template_nowasm/>**

The archives are attached to a rolling `ci-latest` GitHub Release, so no build
output is ever committed to the repository. Tagged versions also get a GitHub
Release with the CPack packages.

<!-- github-pages:start -->

## What it does

```sh
$ cmake_template_nowasm --name you
Hello, you!
```

It is deliberately tiny: the point of the template is the *surroundings*, not
the program. `--help` and a `--version` that matches what CMake was told are
covered by the tests, which also keeps the CLI parsing (CLI11) and the
configured `config.hpp` exercised.

## What is inherited from upstream

* CMake ≥ 3.29, C++23, and the `cmake_template_nowasm_*` option namespace.
* Sanitizers (ASan/UBSan on by default where supported), hardening
  (`_FORTIFY_SOURCE`, stack protector, CFI on MSVC), warnings-as-errors,
  clang-tidy and cppcheck, IPO/LTO.
* CPM-fetched dependencies: fmt, spdlog, Catch2 and CLI11. A parent project can
  supply its own versions; every fetch is guarded by `if(NOT TARGET ...)`.
* Catch2 unit tests and constexpr tests, a libFuzzer harness that switches on
  when a fuzzing sanitizer is available, coverage collection with gcovr /
  OpenCppCoverage, and CPack packages whose names embed the compiler and the
  commit sha.
* The GitHub Actions matrix (Linux/macOS/Windows × GCC/Clang/MSVC × Debug/Release,
  Ninja Multi-Config plus one plain Makefiles and four Visual Studio builds),
  CodeQL, the clang-format bot, Dependabot and the dev container.

## What was changed

* **WebAssembly removed.** `cmake/Emscripten.cmake`, the `web/` assets, the
  `EMSCRIPTEN` branches in the options and the "Build Intro WASM and Deploy to
  GitHub Pages" workflow are gone. Nothing conditional is left behind: the
  native build is the only build.
* **The example application replaced.** The FTXUI game (`intro`) became a
  hello-world CLI named after the project. FTXUI and lefticus/tools, which only
  the game used, are no longer fetched.
* **Downloads published.** CI packages one Release binary per platform, uploads
  it as a workflow artifact, attaches the archives to a rolling `ci-latest`
  release and publishes a download page to GitHub Pages — the same mechanism
  used by [QtWatchAllVideos](https://github.com/SnoutFirst/QtWatchAllVideos).
* **Two fixes the upstream generation step left behind.** `CMakePresets.json`
  still named its analyzer options `myproject_*`, so the Windows presets
  disabled nothing and `presets.windows_disables_static_analysis` failed; and
  the `factorial` declaration did not name its parameter, which modern cppcheck
  rejects (this failed every macOS job).

<!-- github-pages:end -->

## Building

A C++23 compiler, CMake ≥ 3.29 and a generator are all you need; dependencies
are fetched with CPM at configure time:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build
```

Run the result with `./build/src/app/cmake_template_nowasm`
(`build\src\app\Release\cmake_template_nowasm.exe` for a multi-config build on
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
* `test/cmake/*.cmake` and `test/test_cmake_presets.cmake` — regression tests for
  the CMake modules themselves.
* `cli.*` — smoke tests for `--help`, `--version` and the greeting.
* `fuzz_test/` — libFuzzer harness, enabled automatically when a fuzzing
  sanitizer and libFuzzer are both available (see
  [libFuzzer Tutorial](https://github.com/google/fuzzing/blob/master/tutorial/libFuzzerTutorial.md)).

Coverage is collected in the Debug jobs (gcovr on Unix, OpenCppCoverage on
Windows). Uploading it to Codecov requires a `CODECOV_TOKEN` secret; the upload
step is skipped while the secret is unset, and runs with `fail_ci_if_error` as
soon as it is configured.

## Using it as a template

The repository is a GitHub template: *Use this template* → *Create a new
repository*. The rename workflow of the upstream project is not part of this
variant, so replace `cmake_template_nowasm` with your project name yourself
(`grep -rl` over the tree finds every occurrence: `CMakeLists.txt`,
`ProjectOptions.cmake`, `Dependencies.cmake`, `src/`, `include/`, `test/`,
`configured_files/`, `.github/constants.env`, the presets and this README).
