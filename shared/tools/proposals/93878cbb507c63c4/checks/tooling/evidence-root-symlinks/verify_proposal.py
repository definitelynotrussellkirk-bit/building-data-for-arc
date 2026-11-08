"""Copy only imported tooling modules, prove baseline failures, and test the patch."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path,
                        help="New temporary test directory outside the source repo")
    parser.add_argument("--out", required=True, type=Path, help="Directory for compact receipts")
    args = parser.parse_args()
    repo, scratch, out = args.repo.resolve(), args.scratch.resolve(), args.out.resolve()
    if scratch == repo or repo in scratch.parents:
        parser.error("--scratch must be outside the source repo")
    scratch.mkdir(parents=True, exist_ok=False)
    out.mkdir(parents=True, exist_ok=True)
    proposal = Path(__file__).resolve().parent
    source = repo / "src/arcpuzzles/review_full_return.py"
    original_sha = sha(source)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "src"))
    import arcpuzzles.review_full_return
    import arcpuzzles.review_solve

    copies = {}
    for name, module in sorted(sys.modules.items()):
        if name == "arcpuzzles" or name.startswith("arcpuzzles."):
            path = Path(module.__file__).resolve()
            relative = path.relative_to(repo)
            copies[relative.as_posix()] = sha(path)
            for variant in ("baseline", "patched"):
                target = scratch / variant / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    commands = []

    def run(cwd, argv, log_name=None):
        process = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
        entry = {"cwd": str(cwd), "argv": argv, "exit_code": process.returncode}
        if log_name:
            raw = process.stdout + process.stderr
            (out / log_name).write_text(raw, encoding="utf-8")
            entry["evidence_paths"] = [log_name]
            for line in process.stdout.splitlines():
                if line.startswith("COUNTS "):
                    entry["test_counts"] = json.loads(line[len("COUNTS "):])
        commands.append(entry)
        return process.returncode

    patched = scratch / "patched"
    for argv in (["git", "init", "-q"],
                 ["git", "apply", "--check", str(proposal / "proposal.patch")],
                 ["git", "apply", str(proposal / "proposal.patch")]):
        if run(patched, argv) != 0:
            raise RuntimeError(f"Patch preparation failed: {argv}")
    results = {}
    for variant in ("baseline", "patched"):
        copy = scratch / variant
        argv = [sys.executable, "-B", str(proposal / "regression.py"), "--repo", str(copy)]
        code = run(scratch, argv, f"{variant}.log")
        commands[-1]["source_sha256"] = sha(copy / "src/arcpuzzles/review_full_return.py")
        results[variant] = commands[-1].get("test_counts")
        print(f"{variant}: exit={code}, counts={results[variant]}")
    unchanged = sha(source) == original_sha
    expected = (results["baseline"] == {"tests": 13, "failures": 6, "errors": 0, "skipped": 0, "passed": 7}
                and results["patched"] == {"tests": 13, "failures": 0, "errors": 0, "skipped": 0, "passed": 13}
                and commands[-2]["exit_code"] == 1 and commands[-1]["exit_code"] == 0 and unchanged)
    receipt = {"schema": "optional-tooling-proposal-results-v1", "status": "verified" if expected else "unexpected",
               "source_path": "src/arcpuzzles/review_full_return.py", "baseline_source_sha256": original_sha,
               "patched_source_sha256": sha(patched / "src/arcpuzzles/review_full_return.py"),
               "live_source_unchanged": unchanged, "copied_tooling_sha256": copies,
               "proposal_patch_sha256": sha(proposal / "proposal.patch"),
               "test_script_sha256": sha(proposal / "regression.py"),
               "python": sys.version, "verification_commands": commands,
               "test_results": results,
               "limitations": ["Static root symlink checks; no concurrent filesystem-race protection added.",
                               "Only artificial packet data used; no generator/rule or solve answers inspected."]}
    (out / "RESULTS.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0 if expected else 1


if __name__ == "__main__":
    sys.exit(main())
