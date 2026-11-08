"""Bounded finite-rival learnability probe; no generator approval is implied.

From packet/: WORK/.venv/bin/python review.py run python3 ../checks/fd93f1d51f8b/probe.py
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from reviewer_support import load_selected_generator
from arcpuzzles.parametric_worker import _grid, _real_evaluator

TASK = "fd93f1d51f8b"
EXPECTED = "4a8587c42ed71bd6f66ec54b731ae8445988dbc0c11c38b8c36abaa1af54f67b"


def points(g):
    return [(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value]


def crop(g, cells):
    if not cells:
        return [[0]]
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    return [row[left:right + 1] for row in g[top:bottom + 1]]


def component_crop(g, diagonal=False):
    pending = set(points(g))
    groups = []
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                  if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    while pending:
        start = min(pending)
        pending.remove(start)
        stack, group = [start], [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                neighbor = r + dr, c + dc
                if neighbor in pending:
                    pending.remove(neighbor)
                    stack.append(neighbor)
                    group.append(neighbor)
        groups.append(sorted(group))
    chosen = min(groups, key=lambda group: (-len(group), group[0])) if groups else []
    return crop(g, chosen)


def biggest_color(g):
    counts = Counter(g[r][c] for r, c in points(g))
    color = min(counts, key=lambda value: (-counts[value], value)) if counts else 0
    return crop(g, [(r, c) for r, c in points(g) if g[r][c] == color])


def strip_all_empty_lines(g):
    rows = [r for r, row in enumerate(g) if any(row)]
    columns = [c for c in range(len(g[0])) if any(row[c] for row in g)]
    return [[g[r][c] for c in columns] for r in rows] if rows else [[0]]


RIVALS = {
    "largest_nonzero_4_component_bbox": lambda g: component_crop(g),
    "largest_nonzero_8_component_bbox": lambda g: component_crop(g, True),
    "most_frequent_color_bbox": biggest_color,
    "identity": lambda g: g,
    "delete_all_empty_rows_and_columns": strip_all_empty_lines,
}


def main():
    generator, source, digest = load_selected_generator(TASK, root=ROOT)
    assert digest == EXPECTED, (digest, EXPECTED)
    canonical_rows = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            canonical_rows.append(row)
    assert len(canonical_rows) == 1
    program = canonical_rows[0]["program_solution"]
    scanned = []
    selected = None
    # Exactly one bounded search: first witness among at most 24 easy episodes.
    for seed in range(24):
        grids = [generator.generate(seed, index, difficulty="easy") for index in range(4)]
        for grid in grids:
            assert not generator.self_check(grid, difficulty="easy")
        labels = [crop(grid, points(grid)) for grid in grids]
        matches = {name: [fn(grid) == label for grid, label in zip(grids, labels)]
                   for name, fn in RIVALS.items()}
        witnesses = [name for name, flags in matches.items() if all(flags[:3]) and not flags[3]]
        scanned.append({"seed": seed, "rival_matches": matches})
        if witnesses:
            selected = (seed, grids, labels, witnesses)
            break
    if selected is None:
        selected = (23, grids, labels, [])
    seed, grids, labels, witnesses = selected
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    cases = []
    try:
        for index, (grid, predicted) in enumerate(zip(grids, labels)):
            actual = _grid(apply(program, grid))
            assert actual == predicted
            cases.append({"split": "train" if index < 3 else "test", "sample_index": index,
                          "input": grid, "racket_output": actual,
                          "self_check": generator.self_check(grid, difficulty="easy"),
                          "rival_outputs": {name: fn(grid) for name, fn in RIVALS.items()}})
    finally:
        bridge.close()
    report = {
        "schema": "arcpuzzles-bounded-finite-rival-probe-v1", "task_id": TASK,
        "status": "teaching_hole_found" if witnesses else "no_issue_within_finite_probe",
        "source_binding": {"path": str(source.relative_to(ROOT)), "sha256": digest,
                           "rule_sha256": hashlib.sha256(program.encode()).hexdigest()},
        "program": program, "racket": identity, "racket_evaluations": 4,
        "search": {"maximum_seeds": 24, "seed_order": "0..23", "difficulty": "easy",
                   "demos": 3, "queries": 1, "stop": "first witness", "scanned": scanned},
        "selected_seed": seed, "witness_rivals": witnesses, "cases": cases,
        "rival_definitions": {
            "largest_nonzero_4_component_bbox": "Crop original grid to largest 4-connected nonzero component bbox; ignore color; ties choose lexicographically first cell.",
            "largest_nonzero_8_component_bbox": "Same, with 8-connectivity.",
            "most_frequent_color_bbox": "Crop original grid to most frequent nonzero color bbox; ties choose lower color.",
            "identity": "Return input unchanged.",
            "delete_all_empty_rows_and_columns": "Remove every all-zero row and column, including internal gaps."},
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limits": ["A finite rival search on consecutive sample indices, not a population estimate or exhaustive learnability result.",
                   "Python rivals are fully retained in probe.py; all retained gold labels were independently executed in protected Racket.",
                   "Episode grouping is this explicit three-demo/one-query probe, not a claim about every downstream sampler.",
                   "Selected generator remains unverified and unapproved; any teaching repair is an owner-review-pending proposal."]}
    output = Path(__file__).with_name("evidence.json")
    output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "selected_seed": seed,
                      "episodes_scanned": len(scanned), "witness_rivals": witnesses,
                      "racket_evaluations": 4, "evidence": str(output)}))


if __name__ == "__main__":
    main()
