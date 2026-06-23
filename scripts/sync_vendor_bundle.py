#!/usr/bin/env python3
"""sync_vendor_bundle.py — drop a vendor bundle from theia-native into this repo.

The compiled, bytecode-stripped SDK is produced by theia-native's release CI
(`scripts/build_vendor_bundle.py`) and published as a `.tar.gz` bundle. This
script unpacks that bundle and replaces the vendored package trees in this repo:

    harmoneyes_theia/        ace/        harmoneyes_theia.libs/   (+ .dylibs)

It is the only supported way to refresh the binaries — there is no source here.
Run it from CI (see .github/workflows/sync-native-sdk.yml) or locally to test a
bundle before publishing.

Usage:
    # from a local bundle (dir or .tar.gz)
    python scripts/sync_vendor_bundle.py --bundle ../theia-native/dist_vendor
    python scripts/sync_vendor_bundle.py --bundle bundle.tar.gz

    # from a URL (CI downloads the artifact first; this also accepts http(s))
    python scripts/sync_vendor_bundle.py --bundle https://…/vendor-bundle.tar.gz

A bundle MAY include a top-level VERSION file (the theia-native package
version); when present and --bump-version is passed, pyproject.toml's version is
updated to `<VERSION>` so this repo's release matches the SDK it ships.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The compiled bundle is vendored under vendor/ to keep the repo root clean.
# pyproject.toml force-includes vendor/ at the wheel root, so the installed
# package layout is unchanged (`import harmoneyes_theia` still works).
VENDOR_DIR = REPO_ROOT / "vendor"


def _materialize(bundle: str) -> Path:
    """Return a local directory containing the bundle contents."""
    tmp = Path(tempfile.mkdtemp(prefix="theia-bundle-"))

    if bundle.startswith(("http://", "https://")):
        archive = tmp / "bundle.tar.gz"
        print(f"[sync] downloading {bundle}")
        urllib.request.urlretrieve(bundle, archive)  # noqa: S310 (trusted CI URL)
        bundle_path: Path = archive
    else:
        bundle_path = Path(bundle)
        if not bundle_path.exists():
            sys.exit(f"ERROR: bundle not found: {bundle}")

    if bundle_path.is_dir():
        return bundle_path

    if tarfile.is_tarfile(bundle_path):
        dest = tmp / "extracted"
        dest.mkdir()
        with tarfile.open(bundle_path) as tf:
            tf.extractall(dest, filter="data")
        # Allow a single top-level wrapper dir inside the archive.
        entries = list(dest.iterdir())
        has_pkg = any(
            e.name == "harmoneyes_theia" or e.name.startswith("harmoneyes_theia.")
            for e in entries
        )
        if not has_pkg and len(entries) == 1 and entries[0].is_dir():
            return entries[0]
        return dest

    sys.exit(f"ERROR: bundle is neither a directory nor a tarball: {bundle_path}")


def _validate(src: Path) -> None:
    """Refuse to sync anything that isn't fully compiled or is missing the SDK.

    The bundle must be source-free (Nuitka-compiled wrapper): no ``.py`` and no
    ``.pyc`` — only machine-code ``.so``/``.pyd``.
    """
    for bad in ("*.py", "*.pyc"):
        stray = list(src.rglob(bad))
        if stray:
            sys.exit(
                f"ERROR: bundle contains {len(stray)} {bad} file(s) — refusing to "
                f"publish non-compiled source to a public repo. e.g. {stray[:3]}"
            )
    wrapper = [p for p in src.glob("harmoneyes_theia.*") if p.suffix in (".so", ".pyd")]
    if not wrapper:
        sys.exit("ERROR: bundle has no compiled harmoneyes_theia extension")
    core = (list((src / "harmoneyes_theia").glob("_theia_native*"))
            if (src / "harmoneyes_theia").is_dir() else [])
    if not core:
        sys.exit("ERROR: bundle has no harmoneyes_theia/_theia_native extension")
    sos = [p for p in src.rglob("*") if p.suffix in (".so", ".pyd")]
    print(f"[sync] bundle OK: source-free, {len(sos)} compiled extension(s)")


def _replace_vendored(src: Path) -> None:
    # Migrate away from any legacy root-level vendored entries, then rebuild
    # vendor/ from the bundle. VERSION is build metadata (read by _bump_version),
    # not a package file, so it is not vendored.
    for pat in ("harmoneyes_theia", "harmoneyes_theia.*", "ace", "ace.*"):
        for old in REPO_ROOT.glob(pat):
            if old.is_dir():
                shutil.rmtree(old)
            else:
                old.unlink()
    if VENDOR_DIR.exists():
        shutil.rmtree(VENDOR_DIR)
    VENDOR_DIR.mkdir(parents=True)
    for entry in sorted(src.iterdir()):
        if entry.name == "VERSION":
            continue
        dest = VENDOR_DIR / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dest)
        else:
            shutil.copy2(entry, dest)
        print(f"[sync] placed vendor/{entry.name}")


def _bump_version(src: Path) -> None:
    version_file = src / "VERSION"
    if not version_file.exists():
        print("[sync] no VERSION file in bundle — leaving pyproject version as-is")
        return
    version = version_file.read_text().strip()
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text()
    new = re.sub(r'(?m)^version = ".*"$', f'version = "{version}"', text, count=1)
    if new != text:
        pyproject.write_text(new)
        print(f"[sync] set pyproject version -> {version}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="dir, .tar.gz path, or http(s) URL")
    ap.add_argument("--bump-version", action="store_true",
                    help="update pyproject version from the bundle's VERSION file")
    args = ap.parse_args()

    src = _materialize(args.bundle)
    _validate(src)
    _replace_vendored(src)
    if args.bump_version:
        _bump_version(src)
    print("[sync] done — review `git status` and commit the vendored package")


if __name__ == "__main__":
    main()
