#!/usr/bin/env python3
"""Verify this task-local proposal in a disposable, self-contained runtime.

Also execute the two-wall mutation on the seven retained baseline inputs under
the protected Racket rule, separating the mutation from the version seed bump.
Run through review.py run from WORK/repo; --out must be a new directory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from arcpuzzles.runtime import prepare_runtime
from border_probe import RIVAL, TASK


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = Path.cwd()
    folder = Path(__file__).resolve().parent
    task = folder / "proposal/generators" / TASK
    source = task / "generator.py"
    spec = importlib.util.spec_from_file_location("mutation_proposal", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    fixture = task / "counterexamples/small-region-ordered-lesson.json"
    witness = json.loads(fixture.read_bytes())
    program = witness["canonical_program"]
    current = {r["program_solution"] for r in Catalog(root)._variants()[TASK]}
    assert current == {program}
    apply, runtime_identity, bridge = _real_evaluator(root / "shared/runtime")
    cases = []
    try:
        for pair in witness["pairs"]:
            grid = [row[:] for row in pair["input"]]
            color = sorted({value for row in grid for value in row if value})[0]
            gen._ensure_small_border_region(grid, color, random.Random(0))
            output, rival = apply(program, grid), apply(RIVAL, grid)
            changed = [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row)
                       if value != pair["input"][r][c]]
            assert output == pair["output"]
            assert rival != output
            assert gen.observe_overrides(grid) == gen.observe_overrides(pair["input"])
            cases.append({"sample_index": pair["sample_index"], "input": grid, "output": output,
                          "rival_output": rival, "changed_cells": changed,
                          "reference_answer_preserved": True, "rival_refuted": True})
    finally:
        bridge.close()
    write(out / "mutation-racket.json", {
        "schema": "border-decoy-frozen-mutation-proof-v1", "task_id": TASK,
        "proposal_sha256": sha(source), "baseline_fixture_sha256": sha(fixture),
        "canonical_program": program, "rival_program": RIVAL,
        "runtime_identity": runtime_identity, "racket_evaluations": 14, "cases": cases,
        "scope": "Direct mutation of fixed old-source inputs; not a same-seed equality claim across versions.",
    })
    runtime = Path(tempfile.mkdtemp(prefix="extra-ticket-tests-", dir=root.parent / ".review"))
    catalog = Catalog(root)
    prepared = prepare_runtime(catalog, runtime, TASK)
    row = catalog.describe(TASK)
    staged_source = runtime / row["runtime_generator"]
    shutil.copy2(source, staged_source)
    staged_task = staged_source.parent
    for name in ("tests/test_border_regions.py", "counterexamples/small-region-ordered-lesson.json"):
        target = staged_task / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(task / name, target)
    native_tests = [str(runtime / item["runtime_path"]) for item in prepared["files"]
                    if item["library_path"].startswith(f"generators/{TASK}/tests/")
                    and Path(item["library_path"]).name.startswith("test_")
                    and item["library_path"].endswith(".py")]
    assert native_tests
    command = [sys.executable, "-m", "pytest", "--import-mode=importlib", *native_tests,
               str(staged_task / "tests/test_border_regions.py"), "-q", f"--junitxml={out / 'tests.xml'}"]
    env = dict(os.environ)
    env.pop("ARCPUZZLES_HOME", None)
    env["PYTHONPATH"] = str(runtime)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, cwd=runtime, env=env, text=True, capture_output=True, timeout=60)
    (out / "tests.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    suites = ElementTree.parse(out / "tests.xml").getroot().findall("testsuite")
    counts = {key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    report = {
        "schema": "border-proposal-isolated-tests-v1", "task_id": TASK,
        "proposal_sha256": sha(source), "tested_source_sha256": sha(staged_source),
        "baseline_sha256": row["generator_sha256"],
        "new_tests_sha256": sha(task / "tests/test_border_regions.py"),
        "retained_fixture_sha256": sha(fixture),
        "baseline_runtime_manifest_sha256": sha(runtime / "RUNTIME_MANIFEST.json"),
        "runtime_note": "Native prepare_runtime copied baseline code; only this task's staged generator was replaced by the proposal and its new test/fixture added. The inherited runtime manifest describes preparation, not the overridden tested source.",
        "command": command, "cwd": str(runtime), "returncode": result.returncode,
        "pythonpath": str(runtime), "counts": counts,
        "source_isolation": "Only copied runtime on PYTHONPATH; no parent repository imports.",
        "mutation_racket_evaluations": 14,
    }
    write(out / "tests.json", report)
    print(json.dumps({"counts": counts, "returncode": result.returncode,
                      "tested_source_sha256": report["tested_source_sha256"],
                      "mutation_racket_evaluations": 14, "out": str(out)}, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
