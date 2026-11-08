"""Build an offline, isolated test environment from installed distributions.

Use when pytest is installed only in user-site and the portable runner correctly
sets PYTHONNOUSERSITE=1. Copies distribution-owned files, never source checkouts.
Normal pip installation of the same declared dependencies is equally suitable.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import venv

PACKAGES = ("numpy", "Pillow", "pytest", "pluggy", "iniconfig", "packaging", "Pygments")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    destination = args.out.resolve()
    if destination.exists():
        parser.error("--out must be a new directory")
    distributions = [(name, metadata.distribution(name)) for name in PACKAGES]
    venv.EnvBuilder(with_pip=False, symlinks=True).create(destination)
    python = destination / "bin/python"
    site = Path(subprocess.check_output(
        [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True).strip())
    package_rows = []
    for name, distribution in distributions:
        rows = []
        for member in distribution.files or ():
            relative = Path(str(member))
            if relative.is_absolute() or ".." in relative.parts or relative.suffix == ".pyc":
                continue  # Console entry points outside site-packages are unnecessary for -m.
            source = Path(distribution.locate_file(member))
            if not source.is_file():
                continue
            target = site / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            rows.append({"path": relative.as_posix(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        package_rows.append({"name": name, "version": distribution.version, "files": rows})
    command = [str(python), "-s", "-c", "import numpy, PIL, pytest; print('isolated imports ready')"]
    checked = subprocess.run(command, text=True, capture_output=True)
    receipt = {"schema": "arc-review-offline-test-env-v1", "python_source": sys.executable,
               "python_version": sys.version, "destination": str(destination),
               "packages": package_rows, "validation_argv": command,
               "validation_exit_code": checked.returncode,
               "stdout": checked.stdout, "stderr": checked.stderr}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"python": str(python), "packages": {r['name']: r['version'] for r in package_rows},
                      "validation_exit_code": checked.returncode}))
    raise SystemExit(checked.returncode)


if __name__ == "__main__":
    main()
