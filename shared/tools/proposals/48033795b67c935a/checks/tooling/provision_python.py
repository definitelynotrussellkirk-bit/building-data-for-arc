"""Provision a packet-owned isolated venv from installed offline distributions.

Invoke with the provisioned Python 3.12+ that can import the source packages:
    python checks/tooling/provision_python.py --work /absolute/WORK
Creates .venv-review without system/user-site imports. Copies distribution
RECORD files and metadata as regular files; recreates console entry points.
Never overwrites an existing environment or receipt. No task code is executed.
"""
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PACKAGES = ("pytest", "numpy", "Pillow", "pluggy", "iniconfig", "packaging", "Pygments")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    target = work / ".venv-review"
    receipt_path = work / "checks/tooling/python-environment.json"
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12+ is required")
    if target.exists() or receipt_path.exists():
        raise SystemExit("Existing environment or receipt: choose a fresh WORK; refusing overwrite")
    sources = [metadata.distribution(name) for name in PACKAGES]
    receipt = {"schema": "arcpuzzles-offline-python-environment-v1", "status": "failed",
               "recipe": "checks/tooling/provision_python.py", "commands": [],
               "base_interpreter": sys.executable, "base_python_version": sys.version,
               "environment": str(target), "distributions": []}
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"

    def run(argv, cwd):
        result = subprocess.run(argv, cwd=cwd, env=environment, capture_output=True, text=True)
        receipt["commands"].append({"argv": argv, "cwd": str(cwd), "exit_code": result.returncode,
                                    "stdout": result.stdout, "stderr": result.stderr,
                                    "environment": {"PYTHONNOUSERSITE": "1", "PYTHONPATH": "absent", "PYTHONHOME": "absent"}})
        if result.returncode:
            raise RuntimeError(f"Command failed (exit {result.returncode}): {argv}")
        return result.stdout

    try:
        run([sys.executable, "-m", "venv", str(target)], work)
        python = str(target / "bin/python")
        site = Path(run([python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"], work).strip())
        for distribution in sources:
            digest = hashlib.sha256()
            count = total = 0
            skipped = []
            for record in sorted(distribution.files, key=str):
                if record.is_absolute() or ".." in record.parts:
                    skipped.append(str(record))
                    continue
                source = distribution.locate_file(record)
                destination = site / str(record)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination, follow_symlinks=True)
                raw = destination.read_bytes()
                digest.update(str(record).encode() + b"\0" + hashlib.sha256(raw).digest())
                total += len(raw)
                count += 1
            entrypoints = []
            for entry in distribution.entry_points:
                if entry.group != "console_scripts":
                    continue
                command = target / "bin" / entry.name
                command.write_text(f"#!{python}\nimport sys\nfrom importlib.metadata import distribution\n"
                    f"entry = next(e for e in distribution({distribution.metadata['Name']!r}).entry_points "
                    f"if e.group == 'console_scripts' and e.name == {entry.name!r})\n"
                    "sys.exit(entry.load()())\n")
                command.chmod(0o755)
                entrypoints.append(entry.name)
            receipt["distributions"].append({"name": distribution.metadata["Name"],
                "version": distribution.version, "source_site": str(distribution.locate_file("")),
                "copied_record_files": count, "copied_bytes": total,
                "path_and_file_sha256_inventory_digest": digest.hexdigest(),
                "skipped_external_record_paths": skipped, "recreated_console_scripts": entrypoints})
        probe = """import sys, site, json, pytest, numpy, PIL
from importlib.metadata import version
assert sys.version_info >= (3,12)
assert not site.ENABLE_USER_SITE
assert sys.prefix != sys.base_prefix
for module in (pytest, numpy, PIL):
    assert module.__file__.startswith(sys.prefix + '/'), module.__file__
print(json.dumps({'interpreter': sys.executable, 'python': sys.version,
 'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'user_site_enabled': site.ENABLE_USER_SITE,
 'versions': {name: version(name) for name in ('pytest','numpy','Pillow','pluggy','iniconfig','packaging','Pygments')},
 'module_paths': {module.__name__: module.__file__ for module in (pytest,numpy,PIL)}}))"""
        with tempfile.TemporaryDirectory(prefix="arc-python-empty-") as empty:
            receipt["isolated_probe"] = json.loads(run([python, "-c", probe], empty))
        receipt["interpreter"] = python
        receipt["status"] = "passed"
    except Exception as exc:
        receipt["error"] = str(exc)
    receipt["recipe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("x") as output:
        json.dump(receipt, output, indent=2, sort_keys=True)
        output.write("\n")
    print(f"Environment {receipt['status']}: {receipt_path}")
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
