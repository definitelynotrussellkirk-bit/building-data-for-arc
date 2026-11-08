"""Validate a review ZIP and replay its patch against immutable original files.

Run from the matching packet root. No patch is applied to the live repository.
Only the task-scoped changed paths are copied to a temporary tree. This checks
patch application and exact source identity, not an independent scientific rerun.
Requires git on PATH and the original packet's immutable baseline and manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO.parent
sys.path.insert(0, str(REPO / "src"))
from arcpuzzles.review_full_return import validate_full_return


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(archive_path: Path, output_path: Path) -> int:
    if output_path.exists():
        raise FileExistsError(output_path)
    manifest = json.loads((ROOT / "PACKET-MANIFEST.json").read_text())
    report = {"schema": "review-patch-replay-v1", "status": "running",
              "archive_path": str(archive_path.resolve()), "source_directory": str(ROOT),
              "scientific_checks_rerun": False, "runtime_retained": False}
    try:
        with zipfile.ZipFile(archive_path) as archive:
            checked = validate_full_return(archive, manifest)
            report["contract_validation"] = "pass"
            report["assignment_id"] = checked["assignment_id"]
            patches = sorted(name for name in archive.namelist() if name.startswith("patches/"))
            report["patch_sha256"] = {name: digest(archive.read(name)) for name in patches}
            report["changed_paths"] = checked["patch_paths"]
            with tempfile.TemporaryDirectory(prefix="frame-return-replay-") as temporary:
                runtime = Path(temporary)
                report["runtime_directory"] = str(runtime)
                for relative in checked["patch_paths"]:
                    original = ROOT / ".review/baseline" / relative
                    if original.is_file():
                        target = runtime / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(original, target)
                report["commands"] = []
                for index, name in enumerate(patches):
                    patch = runtime / f"review-{index}.patch"
                    patch.write_bytes(archive.read(name))
                    for flags in (["--check"], []):
                        argv = ["git", "apply", *flags, str(patch)]
                        completed = subprocess.run(argv, cwd=runtime, capture_output=True,
                                                   text=True, timeout=30)
                        report["commands"].append({"cwd": str(runtime), "argv": argv,
                            "exit_code": completed.returncode, "stdout": completed.stdout,
                            "stderr": completed.stderr})
                        if completed.returncode:
                            raise RuntimeError("Patch application failed; see command stderr")
                report["replayed_files"] = []
                for relative in checked["patch_paths"]:
                    replayed = (runtime / relative).read_bytes()
                    live = (ROOT / relative).read_bytes()
                    report["replayed_files"].append({"path": relative,
                        "sha256": digest(replayed), "matches_working_source": replayed == live})
                report["status"] = "pass" if all(
                    item["matches_working_source"] for item in report["replayed_files"]) else "fail"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                     if key not in ("commands", "replayed_files")}, indent=2))
    return 0 if report["status"] == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    return verify(args.archive, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
