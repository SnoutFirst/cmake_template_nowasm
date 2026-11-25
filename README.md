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
* the FTXUI example game is replaced by a minimal C++23 hello-world CLI;
* *Use this template* is wired up again: the cleanup workflow that renames a
  generated repository is back (see
  [What the cleanup workflow changes](#what-the-cleanup-workflow-changes)).

## Getting Started

First, click the green *Use this template* button near the top of this page.
That takes you to GitHub's
[*Generate Repository*](https://github.com/SnoutFirst/cmake_template_nowasm/generate)
page: fill in a repository name and a short description, and click *Create
repository from template*.

After creating the project please wait until the cleanup workflow has finished
setting up your project and committed the changes.

Now you can clone the project locally and get to work:

```sh
git clone https://github.com/<user>/<your_new_repo>.git
```

What the workflow did to get there is described in
[What the cleanup workflow changes](#what-the-cleanup-workflow-changes).

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
* **The cleanup workflow restored.** A repository generated from this template
  is renamed, documented and cleaned up by
  `.github/workflows/template-janitor.yml`, exactly as upstream does it.
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

## What the cleanup workflow changes

[`.github/workflows/template-janitor.yml`](.github/workflows/template-janitor.yml)
runs on the first push to a repository created from this template (`push`,
`pull_request` and a published `release`, but it only commits when the
repository is no longer marked as a template). It:

* replaces `cmake_template_nowasm` with your repository's name — with `-` and
  `.` turned into `_`, because the name is also a C++ identifier and the prefix
  of every CMake option — in every tracked file: `CMakeLists.txt`,
  `ProjectOptions.cmake`, the presets, the headers, the tests, the includes,
  the CI matrix and the page scripts. `SnoutFirst/cmake_template_nowasm`
  becomes your `<org>/<repo>`, so the project URL and the download-page
  defaults follow too;
* renames `include/cmake_template_nowasm/` to match;
* writes `README.md` for your project from `.github/template/README.md`, with
  your description and your download-page URL filled in;
* removes `.github/template/` and the workflow itself;
* builds the result with `-D<project>_PACKAGING_MAINTAINER_MODE=ON` (sanitizers,
  clang-tidy, cppcheck and IPO/LTO off, so it needs no extra tooling) and only
  then commits everything as *Template Janitor*.

While this repository is still a GitHub template the same job is a dry run: it
renames with deliberately awkward fake names (`my-unsafe.project`, a
description full of quotes and pipes) and commits nothing, so a rename that
would break the project fails CI here rather than in somebody's new repository.

The placeholder names it looks for are in `.github/template/template_name` and
`.github/template/template_repository`, so they survive a rename of this
repository. Nothing else needs renaming by hand; `grep -rl
cmake_template_nowasm .` finds every occurrence if you would rather do it
yourself.

One caveat: the cleanup commit is pushed with the repository's own
`GITHUB_TOKEN`, and a push made with that token does not start another workflow
run. The first `ci` run still describes the un-renamed template, so the release
assets and the download page catch up on your next push to `main`.
