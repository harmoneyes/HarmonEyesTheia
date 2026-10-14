# Releasing (HarmonEyes maintainers only)

This repo ships **no source** — only compiled binaries vendored in from the
private `theia-native` repository. There is currently **no automated sync**;
the workflow that used to do this (`.github/workflows/sync-native-sdk.yml`)
was removed mid-migration because it assumed an S3 layout
(`vendor-bundles/latest/vendor-bundle.tar.gz`) that `theia-native`'s
publishing pipeline no longer produces. Don't resurrect it as-is — see
"Why there's no CI for this" below before building a new one.

## Updating the vendored SDK

1. **Produce a fresh build** in `theia-native`. Either push a GitHub release
   (`release: published`), or dispatch it manually:

   ```bash
   gh workflow run build-public-sdk.yml --ref <branch-or-tag>
   ```

   This builds a wheel for Linux/macOS/Windows, repairs it
   (auditwheel/delocate/delvewheel), builds the webcam sidecar, then
   Nuitka-compiles the Python wrapper to native code (no `.py`/`.pyc` ships)
   — one job per platform, since Nuitka only emits code for its host OS.

2. **Fetch the three per-platform bundles** once the run finishes. Either:
   - `gh run download <run-id> -n bundle-linux_x86_64 -n bundle-macos_arm64 -n bundle-win_amd64 -D bundle-merged/`
     (GitHub Actions artifacts, 90-day retention), or
   - `aws s3 sync s3://harmoneyes-internal-builds/nuitka-builds/<git-sha>/ bundle-merged/`
     (same content, durable).

   Both drop their payload into **one shared directory** — safe to merge
   because every extension is ABI-tagged
   (`...cpython-312-x86_64-linux-gnu.so` / `...cpython-312-darwin.so` /
   `...cp312-win_amd64.pyd`), so the three platforms' files coexist without
   collisions.

3. **Sync it into this repo:**

   ```bash
   python scripts/sync_vendor_bundle.py --bundle bundle-merged/ --bump-version
   ```

   This validates the bundle is fully compiled (no stray `.py`/`.pyc`),
   replaces `vendor/` wholesale, and bumps `pyproject.toml`'s version from
   the bundle's `VERSION` file (bump the `3.x`/`2.x` major yourself first in
   `pyproject.toml` if this release is a breaking change — the script only
   writes what the bundle's `VERSION` file says).

4. **Sanity-check before committing:**

   ```bash
   pip install -e . --force-reinstall --no-deps
   python -c "import harmoneyes_theia as ht; print(ht.version())"
   ```

5. **Review and commit.** `git status`/`git diff --stat` should show only
   `vendor/**` changing (plus `pyproject.toml`'s version line). Commit,
   push, and let the existing example scripts (`examples/*.py`) be your
   smoke test against a real lease before tagging a release.

## Why there's no CI for this

Two things changed since the sync workflow was originally written:

- **The S3 layout changed.** `build-public-sdk.yml` now uploads three
  separate per-platform bundles under `nuitka-builds/<git-sha>/`, not one
  merged tarball at a stable `latest` path. A workflow driving step 2 above
  automatically would need to either wait on and download three sibling
  jobs' artifacts, or have `build-public-sdk.yml` itself merge and publish
  one combined tarball per release — neither exists today.
- **Secrets.** The bundle needs `THEIA_MODEL_KEY_PASSPHRASE` baked in at
  build time to decrypt production models from the CDN; a locally-built
  binary (dev-key default) cannot decrypt them and is not distributable.
  Only `theia-native`'s own CI has that secret, so the build step (1) must
  stay there — only the sync step (2-3) is a candidate for automation here.

If this becomes a frequent enough chore to automate, the shape would be: a
`theia-native` workflow_dispatch/release step that merges the three
platforms' output into one tarball and publishes it to a stable path (or a
`repository_dispatch` carrying the git SHA), then a `HarmonEyesTheia`
workflow that downloads it and runs steps 3-5 above, opening a PR instead of
pushing directly to a protected branch.
