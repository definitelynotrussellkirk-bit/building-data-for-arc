#!/usr/bin/env python3
"""Build an isolated review venv offline from existing pip HTTP wheel cache.

Use only when the normal task-test preflight reports missing dependencies and
network installs are unavailable. Never disables PYTHONNOUSERSITE or edits the
host interpreter. Requires cached wheels for pytest, NumPy, Pillow and their
transitive dependencies; pip validates compatibility and dependency resolution.
"""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

NAMES = {"pytest", "numpy", "pillow", "pluggy", "packaging", "iniconfig", "pygments"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", type=Path)
    p.add_argument("--env", type=Path, required=True)
    p.add_argument("--wheelhouse", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    if args.env.exists() or args.receipt.exists():
        p.error("env and receipt paths must be new; preserve earlier attempts")
    cache = args.cache or Path(subprocess.check_output([sys.executable, "-m", "pip", "cache", "dir"], text=True).strip())
    args.wheelhouse.mkdir(parents=True, exist_ok=True)
    report = {"schema": "review-offline-environment-v1", "cache": str(cache.resolve()),
              "environment": str(args.env.resolve()), "wheels": [], "commands": [], "passed": False}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)

    def run(argv, **kwargs):
        result = subprocess.run(argv, text=True, capture_output=True, **kwargs)
        report["commands"].append({"argv": list(map(str, argv)), "cwd": str(Path.cwd()),
                                   "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(f"command failed: {argv}; see receipt")
        return result

    try:
        for source in sorted(cache.rglob("*.body")):
            if not zipfile.is_zipfile(source):
                continue
            with zipfile.ZipFile(source) as archive:
                metadata = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
                if len(metadata) != 1:
                    continue
                info = BytesParser().parsebytes(archive.read(metadata[0]))
                name, version = info["Name"], info["Version"]
                if name.lower().replace("_", "-") not in NAMES:
                    continue
                wheel_info = BytesParser().parsebytes(archive.read(metadata[0].replace("/METADATA", "/WHEEL")))
                tag = wheel_info["Tag"]
                filename = f"{name.replace('-', '_')}-{version}-{tag}.whl"
                if Path(filename).name != filename or not tag:
                    raise ValueError("invalid cached wheel metadata")
            target = args.wheelhouse / filename
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError(f"conflicting wheel bytes: {filename}")
            if not target.exists():
                shutil.copyfile(source, target)
            report["wheels"].append({"name": name, "version": version, "filename": filename, "sha256": digest})
        run([sys.executable, "-m", "venv", str(args.env)])
        python = args.env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        isolated = dict(os.environ, PYTHONNOUSERSITE="1")
        isolated.pop("PYTHONPATH", None)
        isolated.pop("PYTHONHOME", None)
        run([str(python), "-m", "pip", "install", "--no-index", "--find-links", str(args.wheelhouse),
             "pytest>=8", "numpy>=1.26", "Pillow>=10"], env=isolated)
        run([str(python), "-I", "-c",
             "import sys,site,pytest,numpy,PIL; assert not site.ENABLE_USER_SITE; "
             "print(sys.executable); print('pytest',pytest.__version__,'numpy',numpy.__version__,'Pillow',PIL.__version__)"], env=isolated)
        report["passed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        args.receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "wheel_count": len(report["wheels"]), "receipt": str(args.receipt)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
