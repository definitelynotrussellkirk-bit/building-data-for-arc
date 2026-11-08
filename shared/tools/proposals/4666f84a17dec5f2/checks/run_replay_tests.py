"""Finish a public replay-return receipt with tests in its own prepared venv.

Prerequisites in the fresh checkout: review.py setup and WORK/.venv-review with
numpy, Pillow and pytest. This helper never installs dependencies or borrows
another checkout's environment. It retains failures as well as passing results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    replay, out = args.replay.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": "review-fresh-tests-v1", "status": "running", "commands": []}
    exit_code = 1
    try:
        patch_receipt = json.loads((replay / "replay.json").read_text())
        if patch_receipt["status"] != "patch_replay_passed_tests_pending":
            raise ValueError("Expected a successful public patch-replay receipt")
        work = Path(patch_receipt["work_root"]).resolve()
        if replay not in work.parents:
            raise ValueError("Replay work root is outside the requested replay directory")
        packet, python = work.parent, work / ".venv-review/bin/python"
        expected_prefix = work / ".venv-review"
        receipt.update({"work_root": str(work), "task_id": patch_receipt["task_id"],
                        "generator_sha256": patch_receipt["generator_sha256"],
                        "patch_replay_sha256": sha(replay / "replay.json"),
                        "extraction_mode": patch_receipt["extraction_mode"]})
        expected = patch_receipt["changed_files"]
        for row in expected:
            if sha(work / row["path"]) != row["sha256"]:
                raise ValueError(f"Before-test source mismatch: {row['path']}")

        probe = (
            "import json,sys,numpy,PIL,pytest; "
            "print(json.dumps({'prefix':sys.prefix,'executable':sys.executable,"
            "'version':sys.version,'packages':{m.__name__:{'version':m.__version__,"
            "'file':m.__file__} for m in (numpy,PIL,pytest)}}))"
        )
        command = [str(python), "-I", "-c", probe]
        result = subprocess.run(command, cwd=work, text=True, capture_output=True, timeout=30)
        receipt["commands"].append({"argv": command, "cwd": str(work), "exit_code": result.returncode})
        (out / "environment-probe.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError("Fresh-environment prerequisite probe failed")
        environment = json.loads(result.stdout)
        if Path(environment["prefix"]).resolve() != expected_prefix.resolve():
            raise ValueError("Interpreter is not using the fresh checkout's own venv")
        for name, row in environment["packages"].items():
            if expected_prefix.resolve() not in Path(row["file"]).resolve().parents:
                raise ValueError(f"Dependency comes from another environment: {name}")
        (out / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")

        test_output = work / "checks/fresh-replay-tests"
        if test_output.exists():
            raise FileExistsError(test_output)
        # Runtime-closure replay need not carry the review assignment wrapper.
        # The public check API accepts the exact task from the replay receipt.
        command = [str(python), "review.py", "run", str(python), "-m",
                   "arcpuzzles", "check", patch_receipt["task_id"], "--stage", "task_tests",
                   "--phase", "after", "--timeout", "600", "--out",
                   "../checks/fresh-replay-tests"]
        result = subprocess.run(command, cwd=packet, text=True, capture_output=True, timeout=660)
        receipt["commands"].append({"argv": command, "cwd": str(packet), "exit_code": result.returncode})
        (out / "task-tests.log").write_text(result.stdout + result.stderr)
        if test_output.exists():
            shutil.copytree(test_output, out / "task-tests")
        if not (test_output / "result.json").is_file():
            raise RuntimeError(f"Public task test exited {result.returncode} without a result; see task-tests.log")
        native = json.loads((test_output / "result.json").read_text())
        receipt["native_test_status"] = {key: native.get(key) for key in
                                         ("status", "passed", "exit_code", "timed_out")}
        after = [{"path": row["path"], "expected_sha256": row["sha256"],
                  "actual_sha256": sha(work / row["path"])} for row in expected]
        receipt["changed_file_comparisons"] = after
        receipt["all_changed_files_match"] = all(row["expected_sha256"] == row["actual_sha256"] for row in after)
        if result.returncode or not native.get("passed") or not receipt["all_changed_files_match"]:
            raise RuntimeError("Focused tests failed or changed source bytes")
        receipt["status"] = "patch_replay_and_focused_tests_passed"
        exit_code = 0
    except Exception as error:
        receipt.update({"status": "failed", "error_type": type(error).__name__, "error": str(error)})
    finally:
        receipt["exit_code"] = exit_code
        (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps({key: receipt.get(key) for key in
                          ("status", "exit_code", "generator_sha256", "all_changed_files_match", "error")}))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
