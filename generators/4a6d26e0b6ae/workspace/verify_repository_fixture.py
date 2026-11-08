"""Verify a narrowly scoped shared-test proposal in a disposable repository copy.

The original repository is never patched. A minimal synthetic packet needs its
own CLI sources before packing; changing PYTHONPATH isolation is not a repair.
Runs the original focused reproducer, applies the proposal ONLY in the copied
test, then runs focused or full repository tests with copied CLI imports.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
RELATIVE_TEST = Path("tests/test_review_solve.py")
TEST = "tests/test_review_solve.py::test_duties_solve_preparation_runs_from_packet_root"


def proposed_fixture_text(text):
    marker = "def test_duties_solve_preparation_runs_from_packet_root(library, tmp_path):\n"
    if text.count(marker) != 1:
        raise ValueError("unrecognized fixture test; refusing to guess a patch")
    head, tail = text.split(marker, 1)
    needle = "    root = packet(library, tmp_path)\n"
    inserted_marker = "    # The child packet must carry its own CLI, not borrow a parent import path.\n"
    if tail.count(needle) != 1 or inserted_marker in tail:
        raise ValueError("fixture source changed or proposal already applied")
    addition = '''    from pathlib import Path
    import shutil
    # The child packet must carry its own CLI, not borrow a parent import path.
    shutil.copytree(Path(solves.__file__).resolve().parent, library / "src/arcpuzzles",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
'''
    return head + marker + tail.replace(needle, addition + needle, 1)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(stage, out, name, test_args, timeout):
    xml_path = out / (name + ".xml")
    code = ("import pathlib, sys; "
            "root=pathlib.Path.cwd().resolve(); sys.path.insert(0, str(root/'src')); "
            "import arcpuzzles; "
            "assert pathlib.Path(arcpuzzles.__file__).resolve().is_relative_to(root); "
            "print('COPIED_CLI=' + arcpuzzles.__file__, flush=True); "
            "import pytest; raise SystemExit(pytest.main(" + repr(["-q", *test_args, "--junitxml=" + str(xml_path)]) + "))")
    argv = [sys.executable, "-E", "-c", code]
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
    record = {"argv": argv, "cwd": str(stage), "environment_removed": ["PYTHONPATH", "PYTHONHOME"]}
    started = time.perf_counter()
    with (out / (name + ".log")).open("w") as log:
        try:
            result = subprocess.run(argv, cwd=stage, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            record["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            record.update(exit_code=None, timed_out=True)
    record["elapsed_seconds"] = time.perf_counter() - started
    if xml_path.is_file():
        root = ET.parse(xml_path).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        record["tests"] = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    (out / (name + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    return record


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--suite", choices=("focused", "full"), default="focused")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args(argv)
    if args.timeout < 1:
        ap.error("timeout must be positive")
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    original = ROOT / RELATIVE_TEST
    original_hash = sha(original)
    runtime_hash = sha(ROOT / "src/arcpuzzles/runtime.py")
    before_text = original.read_text(); after_text = proposed_fixture_text(before_text)
    patch = "".join(difflib.unified_diff(before_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
                                       fromfile="a/repo/" + RELATIVE_TEST.as_posix(), tofile="b/repo/" + RELATIVE_TEST.as_posix()))
    (out / "proposed-shared-test.patch").write_text(patch)
    record = {"schema": "isolated-fixture-proposal-v1", "proposal_only": True,
              "source_test_sha256": original_hash, "source_runtime_sha256": runtime_hash,
              "probe_sha256": sha(Path(__file__)), "suite": args.suite}
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-fixture-round2-") as temp:
        stage = Path(temp) / "repo"
        shutil.copytree(ROOT, stage, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", "*.pyc", "var", "build", "dist"))
        record["actual_runtime_directory"] = str(stage)
        record["copied_cli_files"] = {p.relative_to(stage).as_posix(): sha(p) for p in (stage / "src/arcpuzzles").rglob("*") if p.is_file()}
        (out / "staging.json").write_text(json.dumps(record, indent=2) + "\n")
        record["before"] = run(stage, out, "before", [TEST], args.timeout)
        (stage / RELATIVE_TEST).write_text(after_text)
        record["after"] = run(stage, out, "after", [] if args.suite == "full" else [TEST], args.timeout)
    record["temporary_runtime_removed"] = True
    record["shared_source_unchanged"] = sha(original) == original_hash and sha(ROOT / "src/arcpuzzles/runtime.py") == runtime_hash
    reproduced = record["before"]["exit_code"] == 1 and "No module named 'arcpuzzles'" in (out / "before.log").read_text()
    record["baseline_import_failure_reproduced"] = reproduced
    record["passed"] = reproduced and record["after"]["exit_code"] == 0 and record["shared_source_unchanged"]
    (out / "summary.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "copied_cli_files"}, indent=2))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
