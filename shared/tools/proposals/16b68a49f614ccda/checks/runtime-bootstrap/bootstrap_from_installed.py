"""Reinstall already available distributions into an isolated local test venv.

This is an offline environment repair, not a task-test isolation override.
Run from WORK with the ordinary interpreter that can import these packages.
Only the small receipt and this script belong in the return, not the wheels/venv.
"""
from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import re
import subprocess
import sys
from pathlib import Path

from wheel.wheelfile import WheelFile


def main() -> None:
    root = Path.cwd().resolve()
    wheel_dir = root / ".review" / "local-wheels"
    environment = root / ".venv-review"
    destination = root / "checks" / "runtime-bootstrap"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    names = ["pytest", "iniconfig", "pluggy", "pygments", "numpy", "Pillow", "packaging"]
    receipt = {
        "purpose": "Offline reinstall into an independent venv; PYTHONNOUSERSITE stays enabled in task_tests.",
        "cwd": str(root),
        "argv": [sys.executable, "checks/runtime-bootstrap/bootstrap_from_installed.py"],
        "source_interpreter": sys.executable,
        "environment": str(environment),
        "distributions": [],
        "commands": [],
    }
    for name in names:
        dist = metadata.distribution(name)
        files = list(dist.files or [])
        wheel_metadata = next(p for p in files if str(p).endswith(".dist-info/WHEEL"))
        wheel_text = Path(dist.locate_file(wheel_metadata)).read_text()
        tag = next(line[5:].strip() for line in wheel_text.splitlines() if line.startswith("Tag: "))
        normalized_name = re.sub(r"[-_.]+", "_", dist.metadata["Name"]).lower()
        wheel_path = wheel_dir / f"{normalized_name}-{dist.version}-{tag}.whl"
        if wheel_path.exists():
            raise FileExistsError(wheel_path)
        aggregate = hashlib.sha256()
        count = 0
        with WheelFile(wheel_path, "w") as archive:
            for relative in sorted(files, key=str):
                parts = relative.parts
                if ".." in parts or relative.is_absolute() or "__pycache__" in parts:
                    continue
                if relative.suffix == ".pyc" or (".dist-info/" in str(relative) and relative.name in {"RECORD", "INSTALLER", "REQUESTED", "direct_url.json"}):
                    continue
                original = Path(dist.locate_file(relative))
                if not original.is_file():
                    raise FileNotFoundError(original)
                data = original.read_bytes()
                aggregate.update(str(relative).encode() + b"\0" + hashlib.sha256(data).digest())
                archive.writestr(str(relative), data)
                count += 1
        receipt["distributions"].append({
            "name": name, "version": dist.version, "original_location": str(dist.locate_file(".")),
            "copied_files": count, "path_and_content_sha256": aggregate.hexdigest(),
            "wheel": str(wheel_path), "wheel_sha256": hashlib.sha256(wheel_path.read_bytes()).hexdigest(),
        })
    commands = [
        [sys.executable, "-m", "venv", str(environment)],
        [str(environment / "bin/python"), "-m", "pip", "install", "--no-index", "--no-deps", "--find-links", str(wheel_dir), *names],
        [str(environment / "bin/python"), "-I", "-c", "import numpy,PIL,pytest; print(numpy.__version__,PIL.__version__,pytest.__version__)"],
    ]
    for argv in commands:
        result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        receipt["commands"].append({"cwd": str(root), "argv": argv, "exit_code": result.returncode, "output": result.stdout})
        if result.returncode:
            receipt["exit_code"] = result.returncode
            (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
            raise SystemExit(result.returncode)
    receipt["exit_code"] = 0
    (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Isolated venv ready; all seven dependencies installed from hashed local distribution bytes.")


if __name__ == "__main__":
    main()
