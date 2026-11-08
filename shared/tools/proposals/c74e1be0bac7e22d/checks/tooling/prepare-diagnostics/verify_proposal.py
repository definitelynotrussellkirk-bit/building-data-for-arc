"""Apply the optional patch in a temporary tree and run synthetic regressions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    bundle = Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("replay.json", "replay.log", "replay.junit.xml")):
        raise FileExistsError("Choose a fresh replay output directory")
    original = repo / "src/arcpuzzles/review_solve.py"
    before = sha(original)
    receipt = {"schema": "arcpuzzles-prepare-diagnostics-replay-v1",
               "source_sha256": before, "patch_sha256": sha(bundle / "prepare-diagnostics.patch"),
               "commands": [], "scope": "Synthetic preparation and CLI visibility tests only"}
    logs = []
    with tempfile.TemporaryDirectory(prefix="arc-prepare-proposal-") as directory:
        stage = Path(directory)
        target = stage / "src/arcpuzzles/review_solve.py"
        target.parent.mkdir(parents=True)
        shutil.copyfile(original, target)
        def run(argv, env=None):
            result = subprocess.run(argv, cwd=stage, env=env, capture_output=True, text=True)
            receipt["commands"].append({"cwd": str(stage), "argv": argv, "exit_code": result.returncode})
            logs.append(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f"Verification command failed: {argv[0]}")
            return result.stdout
        try:
            run(["git", "init", "-q"])
            assert Path(run(["git", "rev-parse", "--show-toplevel"]).strip()) == stage
            run(["git", "apply", "--check", str(bundle / "prepare-diagnostics.patch")])
            run(["git", "apply", str(bundle / "prepare-diagnostics.patch")])
            assert sha(target) == sha(bundle / "review_solve.proposed.py")
            receipt["patched_source_sha256"] = sha(target)
            settings = {"ARCPUZZLES_REVIEW_SOURCE": str(repo / "src"),
                        "PREPARE_TARGET_SOURCE": str(target), "CLI_TARGET_SOURCE": str(target),
                        "PYTHONDONTWRITEBYTECODE": "1"}
            receipt["test_environment"] = settings
            run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                 str(stage / "tests/test_review_solve_prepare_diagnostics.py"),
                 str(repo / "tests/test_review_solve_cli_visibility.py"),
                 "--junitxml=" + str(out / "replay.junit.xml")], {**os.environ, **settings})
            receipt["status"] = "passed"
        except Exception as exc:
            receipt["status"] = "failed"
            receipt["error"] = str(exc)
        finally:
            receipt["active_source_unchanged"] = sha(original) == before
            (out / "replay.log").write_text("\n".join(logs))
            (out / "replay.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "passed" and receipt["active_source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
