"""Build an isolated test environment from already installed distributions.

No network, pip index, user-site dependency at execution time, or symlinked
third-party packages are used. Console entry points are unnecessary because
the checks invoke ``python -m pytest``. Run with a Python 3.12+ interpreter
that can currently import the required packages.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

PACKAGES = ("pytest", "pluggy", "iniconfig", "pygments", "packaging", "numpy", "Pillow")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    target = args.venv.resolve()
    if sys.version_info < (3, 12):
        parser.error("Python 3.12+ is required")
    if target.exists():
        parser.error("environment destination already exists; choose a new path")
    distributions = [(name, importlib.metadata.distribution(name)) for name in PACKAGES]
    venv.EnvBuilder(with_pip=False, symlinks=False).create(target)
    python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    clean_env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    clean_env["PYTHONNOUSERSITE"] = "1"
    site_path = Path(subprocess.check_output(
        [str(python), "-I", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        text=True, env=clean_env).strip())
    receipt = {"schema": "offline-review-test-environment-v1", "environment": str(target),
               "python": str(python), "packages": [], "network_used": False}
    for name, distribution in distributions:
        files = distribution.files
        if files is None:
            raise RuntimeError(f"{name} has no installed-file manifest")
        digest, copied, skipped = hashlib.sha256(), 0, []
        for item in sorted(files, key=str):
            relative = Path(str(item))
            if relative.is_absolute() or ".." in relative.parts or "__pycache__" in relative.parts:
                skipped.append(str(item))
                continue
            source = Path(distribution.locate_file(item))
            if not source.is_file():
                raise RuntimeError(f"missing installed distribution file: {source}")
            destination = site_path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            digest.update(str(relative).encode() + b"\0")
            digest.update(hashlib.file_digest(destination.open("rb"), "sha256").digest())
            copied += 1
        receipt["packages"].append({"name": name, "version": distribution.version,
                                    "copied_files": copied, "content_digest": digest.hexdigest(),
                                    "skipped_entrypoints_or_caches": skipped})
    probe = (
        "import json, sys, pytest, numpy, PIL, pluggy, packaging, iniconfig, pygments; "
        "print(json.dumps({'python':sys.executable,'version':sys.version,"
        "'pytest':pytest.__version__,'numpy':numpy.__version__,'Pillow':PIL.__version__,"
        "'paths':{m.__name__:m.__file__ for m in "
        "(pytest,numpy,PIL,pluggy,packaging,iniconfig,pygments)}}))"
    )
    result = subprocess.run([str(python), "-I", "-c", probe], env=clean_env,
                            capture_output=True, text=True, check=False)
    receipt.update({"probe_argv": [str(python), "-I", "-c", probe],
                    "probe_exit_code": result.returncode, "probe_stderr": result.stderr})
    if result.returncode == 0:
        receipt["probe"] = json.loads(result.stdout)
        if not all(Path(p).is_relative_to(target) for p in receipt["probe"]["paths"].values()):
            raise RuntimeError("probe imported a package from outside the new environment")
    else:
        receipt["probe_stdout"] = result.stdout
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"python": str(python), "packages": len(PACKAGES),
                      "probe_exit_code": result.returncode, "receipt": str(args.receipt)}))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
