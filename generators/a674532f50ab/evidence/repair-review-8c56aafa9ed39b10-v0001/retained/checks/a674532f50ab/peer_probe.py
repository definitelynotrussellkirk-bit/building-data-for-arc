"""Bounded learnability probe for a674532f50ab's restricted corner support."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
TASK = "a674532f50ab"
SEED = 9


def crop_top_right(grid):
    width = len(grid[0])
    return [list(row[width - 3 : width]) for row in grid[:3]]


def crop_top_left(grid):
    return [list(row[:3]) for row in grid[:3]]


def corner_has_nine_distinct(grid):
    return len({value for row in crop_top_right(grid) for value in row}) == 9


def rival(grid):
    return crop_top_right(grid) if corner_has_nine_distinct(grid) else crop_top_left(grid)


def rival_program():
    names = [f"x{i}" for i in range(9)]
    bindings = []
    index = 0
    for row in range(3):
        for offset in range(3):
            bindings.append(
                f"({names[index]} (at g {row} (+ (- (cols g) 3) {offset})))"
            )
            index += 1
    comparisons = [
        f"(!= {names[i]} {names[j]})"
        for i in range(9)
        for j in range(i + 1, 9)
    ]
    return (
        "(rule! (lambda (g)\n"
        f"  (let* ((w (cols g)) {' '.join(bindings)})\n"
        f"    (if (and {' '.join(comparisons)})\n"
        "        (build-grid 3 3 (r c) (at g r (+ c (- w 3))))\n"
        "        (build-grid 3 3 (r c) (at g r c))))))"
    )


def main():
    generator, source_path, source_sha = load_selected_generator(TASK, root=ROOT)
    canonical = None
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                canonical = row
                break
    if canonical is None:
        raise RuntimeError("canonical task missing")

    pairs = []
    for index in range(4):
        grid = generator.generate(SEED, index)
        issues = generator.self_check(grid)
        if issues:
            raise AssertionError(f"generated case {index} rejected: {issues}")
        pairs.append({"input": grid, "output": crop_top_right(grid)})

    signatures = [len({v for row in pair["output"] for v in row}) for pair in pairs]
    python_fits = [rival(pair["input"]) == pair["output"] for pair in pairs]
    if signatures[:3] != [9, 9, 9] or signatures[3] == 9:
        raise AssertionError(f"unexpected support witness signatures: {signatures}")
    if python_fits != [True, True, True, False]:
        raise AssertionError(f"rival did not form the intended lesson witness: {python_fits}")

    witness = {
        "seed": SEED,
        "demo_indices": [0, 1, 2],
        "query_index": 3,
        "rule": "crop the top-right 3x3 corner",
        "rival": "crop top-right only when those nine cells are all distinct; otherwise crop top-left",
        "corner_distinct_color_counts": signatures,
        "train": pairs[:3],
        "test": [pairs[3]],
        "query_rival_output": rival(pairs[3]["input"]),
        "canonical_program": canonical["program_solution"],
        "rival_program": rival_program(),
    }
    (HERE / "counterexample.json").write_text(
        json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = {
        "schema": "bounded-peer-audit-v1",
        "task_id": TASK,
        "source_sha256": source_sha,
        "rule_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
        "scope": "One deterministic four-example default lesson; one support-conditioned positional rival.",
        "status": "counterexample_python_confirmed_racket_pending",
        "lesson_seed": SEED,
        "draws_checked": 4,
        "lessons_checked": 1,
        "corner_distinct_color_counts": signatures,
        "python_comparisons": [
            {"split": "train" if i < 3 else "test", "rival_equals_canonical": value}
            for i, value in enumerate(python_fits)
        ],
        "racket_evaluations": 0,
        "limits": "Finite lesson-composition audit, not universal identifiability or a full generator repair. Source unchanged.",
        "related_open_issue": "Default generation restricts top-right answer equality patterns; see evidence/review_index.json.",
    }

    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, source_path.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        report["racket_runtime"] = identity
        try:
            comparisons = []
            for split, selected in (("train", pairs[:3]), ("test", pairs[3:])):
                for pair in selected:
                    truth = _grid(apply(witness["canonical_program"], pair["input"]))
                    report["racket_evaluations"] += 1
                    alternate = _grid(apply(witness["rival_program"], pair["input"]))
                    report["racket_evaluations"] += 1
                    if truth != pair["output"]:
                        raise AssertionError("canonical Racket output mismatch")
                    if alternate != rival(pair["input"]):
                        raise AssertionError("rival Racket output mismatch")
                    comparisons.append(
                        {"split": split, "rival_equals_canonical": alternate == truth}
                    )
            if [row["rival_equals_canonical"] for row in comparisons] != [True, True, True, False]:
                raise AssertionError(f"unexpected protected comparisons: {comparisons}")
            report["protected_comparisons"] = comparisons
            report["status"] = "counterexample_protected_racket_confirmed"
        finally:
            bridge.close()

    report["counterexample"] = "checks/a674532f50ab/counterexample.json"
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_sha:
        raise AssertionError("source drifted during probe")
    (HERE / "peer_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
