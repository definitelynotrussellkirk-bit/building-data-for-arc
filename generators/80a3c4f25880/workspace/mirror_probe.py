"""Reproduce and test a proposed mirror-only crop repair without changing approval.

The native prototype has its own key-cleared crop. This separate probe binds the
unchanged production generator, retains the admitted counterexample, tests a
one-block repair in memory, and emits an owner-reviewable patch beside evidence.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import types

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import load_selected_generator

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "80a3c4f25880"
OLD = "    crop = _crop(grid, cells)\n"
NEW = ("    object_grid = [row[:] for row in grid]\n"
       "    object_grid[0][0] = 0\n"
       "    crop = _crop(object_grid, cells)\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("choose a new output directory")
    original, path, digest = load_selected_generator(TASK_ID, root=ROOT)
    source = path.read_text()
    if source.count(OLD) != 1:
        raise ValueError("current source no longer matches the proposed one-block repair")
    proposed = source.replace(OLD, NEW)
    patched = types.ModuleType("proposed_key_clear_mirror")
    patched.__file__ = str(path)
    exec(compile(proposed, str(path) + ":proposed-only", "exec"), patched.__dict__)
    row = next(json.loads(line) for line in
               (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
               if json.loads(line).get("task_id") == TASK_ID)
    grid = [[0] * 8 for _ in range(8)]
    grid[0][0] = 1
    for r, c in ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2)):
        grid[r][c] = 6
    assert original.self_check(grid) == []
    with _local_imports(ROOT / "shared/runtime", path.parent):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            answer = apply(row["program_solution"], grid)
            assert original.rule_mirror(grid) != answer
            assert patched.rule_mirror(grid) == answer
            for pair in row["train"] + row["test"]:
                executed = apply(row["program_solution"], pair["input"])
                assert patched.rule_mirror(pair["input"]) == executed == pair["output"]
        finally:
            bridge.close()
    relative = path.relative_to(ROOT).as_posix()
    patch = "".join(difflib.unified_diff(source.splitlines(keepends=True),
                                       proposed.splitlines(keepends=True),
                                       fromfile="a/" + relative, tofile="b/" + relative))
    args.out.mkdir(parents=True)
    (args.out / "proposed-mirror-fix.patch").write_text(patch)
    report = {
        "status": "confirmed_production_python_mirror_defect",
        "scope": "Authored input admitted by current self_check; canonical Racket is correct. Proposed patch tested in memory only.",
        "source": relative, "source_sha256": digest,
        "canonical_program_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "input": grid, "program": row["program_solution"], "output": answer,
        "current_mirror_output": original.rule_mirror(grid),
        "proposed_mirror_output": patched.rule_mirror(grid),
        "self_check": [], "racket": identity,
        "racket_evaluations": 5, "canonical_regressions": 4,
        "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
        "proposed_source_sha256": hashlib.sha256(proposed.encode()).hexdigest(),
        "source_modified": False,
        "owner_action": "Review/apply patch, reapprove exact generator source, regenerate inventory and requalify adapter before acceptance on those new bytes."
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "canonical_regressions": 4,
                      "racket_evaluations": 5, "source_modified": False}))


if __name__ == "__main__":
    main()
