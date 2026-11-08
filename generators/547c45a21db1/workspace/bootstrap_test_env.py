"""Create an offline verification environment from installed host test packages.

The portable runner intentionally disables the user site. If pytest exists only
there, use this helper to copy its installed distribution and dependencies into
a fresh venv. No downloads, sibling imports, or changes to the host installation.
On an ordinary machine, installing the declared runtime/dev dependencies into
a normal venv is equally suitable. Run with the host Python that imports pytest.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import pathlib
import shutil
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"refusing to reuse an existing environment: {out}")
    distributions = [importlib.metadata.distribution(name)
                     for name in ("pytest", "pluggy", "iniconfig", "packaging", "pygments")]
    venv.EnvBuilder(with_pip=False, system_site_packages=True, symlinks=False).create(out)
    python = out / "bin/python"
    site = pathlib.Path(subprocess.check_output(
        [str(python), "-s", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True).strip())
    copied = []
    for dist in distributions:
        records = []
        for relative in dist.files or ():
            relative = pathlib.PurePosixPath(str(relative))
            # Console entry points outside site-packages are unnecessary for -m.
            if relative.is_absolute() or ".." in relative.parts or "__pycache__" in relative.parts:
                continue
            source = pathlib.Path(dist.locate_file(str(relative)))
            if not source.is_file():
                continue
            target = site / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            records.append({"path": str(relative), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        copied.append({"name": dist.metadata["Name"], "version": dist.version, "files": records})
    command = [str(python), "-E", "-s", "-c",
               "import pytest,numpy,PIL; print('pytest='+pytest.__version__+' numpy='+numpy.__version__+' Pillow='+PIL.__version__)"]
    check = subprocess.run(command, text=True, capture_output=True)
    report = {"python": str(python), "python_version": sys.version,
              "host_python": sys.executable, "system_site_packages": True,
              "copied_distributions": copied, "verification_argv": command,
              "exit_code": check.returncode, "stdout": check.stdout, "stderr": check.stderr}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"python": str(python), "exit_code": check.returncode,
                      "stdout": check.stdout, "report": str(args.report)}, indent=2))
    return check.returncode


if __name__ == "__main__":
    raise SystemExit(main())
