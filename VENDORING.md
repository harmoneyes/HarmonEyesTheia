# Vendoring the native SDK

This repo ships **no source** — only the fully-compiled output of
[`theia-native`](https://github.com/RightEyeLLC/theia-native), dropped into
`vendor/` by the release pipeline. `import harmoneyes_theia` works with no build
step because `pyproject.toml` force-includes `vendor/` at the wheel root.

## What lives in `vendor/`

| Path | What it is |
|------|------------|
| `harmoneyes_theia.<abi>.so` / `.pyd` | Nuitka-compiled wrapper package (one per platform/ABI) |
| `ace.<abi>.so` / `.pyd` | Nuitka-compiled `ace` package |
| `harmoneyes_theia/_theia_native.<abi>.so` / `.pyd` | pybind11 C++ core |
| `harmoneyes_theia/models/…` | ML model data (if bundled) |
| `harmoneyes_theia/.dylibs/…` | macOS runtime deps (delocate) |
| `harmoneyes_theia.libs/…` | Linux/Windows runtime deps (auditwheel/delvewheel) |

No `.py`/`.pyc` ships — the wrapper layer is Nuitka-compiled to machine code, as
opaque as the C++ core. `scripts/sync_vendor_bundle.py` refuses any bundle that
contains source.

## How a bundle is produced

1. In `theia-native`, per-platform CI builds a cp312 wheel (pybind11 core +
   `harmoneyes_theia`/`ace` wrappers).
2. `theia-native/scripts/build_vendor_bundle.py` Nuitka-compiles the wrapper
   packages and assembles a source-free bundle. Nuitka emits host-only native
   code, so this runs once per OS (Linux / macOS arm64 / Windows) and the
   ABI-tagged outputs merge into one multi-platform bundle.
3. The bundle (`.tar.gz`, optionally carrying a `VERSION` file) is published to
   S3.

## How this repo consumes a bundle

```bash
# From a local theia-native bundle dir or tarball:
python scripts/sync_vendor_bundle.py --bundle ../theia-native/dist_vendor --bump-version

# From a published tarball / URL:
python scripts/sync_vendor_bundle.py --bundle bundle.tar.gz --bump-version
```

`sync_vendor_bundle.py` validates the bundle is source-free, replaces `vendor/`,
and (with `--bump-version`) sets `pyproject.toml`'s version from the bundle's
`VERSION` file.

CI does this automatically: `.github/workflows/sync-native-sdk.yml` ("Sync SDK")
downloads the bundle from S3, syncs it, smoke-tests the built wheel, commits the
new `vendor/`, and optionally cuts a release tag. It is triggered manually
(`workflow_dispatch`) or by a `native-sdk-published` `repository_dispatch` from
theia-native's release.

> **Versioning:** the installed package version tracks the theia-native package
> version (written into the bundle's `VERSION` file and applied by
> `--bump-version`). The `2.x` line supersedes the legacy Nuitka `1.x` builds.
