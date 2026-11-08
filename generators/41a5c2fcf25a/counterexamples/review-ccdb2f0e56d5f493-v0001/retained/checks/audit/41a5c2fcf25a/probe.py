"""Findings-only probe. Run from the packet with the recorded public wrapper.

Only the selected generator, exact canonical task, and supplied Racket labels
are used. The independent Python oracle is never presented as a Racket label.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

TASK = "41a5c2fcf25a"
ROOT = Path.cwd().resolve()  # review.py run explicitly sets WORK/repo as cwd.
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(ROOT)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
OUT = Path(__file__).resolve().parent


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def components(grid, diagonal=False):
    pending = {(r, c) for r in range(1, len(grid)) for c in range(len(grid[0])) if grid[r][c]}
    result = []
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diagonal:
        directions += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    while pending:
        start = min(pending)
        pending.remove(start)
        cells, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in directions:
                point = r + dr, c + dc
                if point in pending:
                    pending.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(cells)
    return result


def solve(grid, *, cap=None, diagonal=False):
    comps = components(grid, diagonal)
    key = lambda cells: (-(min(len(cells), cap) if cap else len(cells)), min(r for r, _ in cells), min(c for _, c in cells))
    colors = [color for color in grid[0] if color]
    result = deepcopy(grid)
    for color, cells in zip(colors, sorted(comps, key=key)):
        for r, c in cells:
            result[r][c] = color
    return result


RIVALS = {
    "cap_area_at_five": lambda grid: solve(grid, cap=5),
    "eight_neighbor_components": lambda grid: solve(grid, diagonal=True),
}


def witness_grids():
    cap = [[0] * 11 for _ in range(10)]
    cap[0][:2] = [2, 3]
    for r, c in ((2, 1), (2, 2), (2, 3), (3, 1), (3, 2)):
        cap[r][c] = 8
    for r in (6, 7):
        for c in (6, 7, 8):
            cap[r][c] = 8
    diagonal = [[0] * 11 for _ in range(10)]
    diagonal[0][:2] = [2, 3]
    for r, c in ((2, 1), (2, 2), (3, 3), (3, 4)):
        diagonal[r][c] = 8
    return [("cap_area_at_five", cap), ("eight_neighbor_components", diagonal)]


def prepare():
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    can_counts = {name: sum(fn(p["input"]) == p["output"] for p in canonical) for name, fn in RIVALS.items()}
    can_oracle = sum(solve(p["input"]) == p["output"] for p in canonical)
    can_valid = sum(not GEN.self_check(p["input"]) for p in canonical)
    declared_canonical = {name: sum(fn(p["input"]) == p["output"] for p in canonical) for name, fn in GEN.CANONICAL_SHORTCUTS.items()}
    competitor_canonical = {name: sum(fn(p["input"]) == p["output"] for p in canonical) for name, fn in GEN.LESSON_COMPETITORS.items()}
    records, matches, checks, areas = [], Counter(), [], Counter()
    invalid_generated = []
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            for index in range(16):
                grid = GEN.generate(seed, index, difficulty=difficulty)
                call = {"seed": seed, "sample_index": index, "difficulty": difficulty, "overrides": {}}
                errors = GEN.self_check(grid, difficulty=difficulty)
                if errors:
                    invalid_generated.append({"call": call, "errors": errors})
                expected = solve(grid)
                for name, fn in RIVALS.items():
                    matches[name] += fn(grid) == expected
                spatial_sizes = tuple(len(c) for c in sorted(components(grid), key=lambda c: (min(r for r, _ in c), min(v for _, v in c))))
                areas[str(spatial_sizes)] += 1
                records.append((call, grid))
    overrides_tested, override_errors = 0, []
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(4):
            for h in (10, 14):
                for w in (11, 16):
                    for n in (2, 3, 4):
                        overrides = {"grid_h": h, "grid_w": w, "n_blobs": n}
                        grid = GEN.generate(17, index, difficulty=difficulty, **overrides)
                        errors = GEN.self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
                        observed = {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(components(grid))}
                        overrides_tested += 1
                        if errors or observed != overrides:
                            override_errors.append({"sample_index": index, "difficulty": difficulty, "overrides": overrides, "errors": errors, "observed": observed})
    bad_calls = [
        {"grid_h": True}, {"grid_h": 10.0}, {"grid_h": "10"}, {"grid_h": 9}, {"grid_h": 15},
        {"grid_w": 10}, {"grid_w": 17}, {"n_blobs": 1}, {"n_blobs": 5}, {"unknown_axis": 1},
    ]
    rejections = []
    for overrides in bad_calls:
        try:
            GEN.generate(17, 0, **overrides)
            rejections.append({"overrides": overrides, "rejected": False})
        except (TypeError, ValueError) as exc:
            rejections.append({"overrides": overrides, "rejected": True, "exception": str(exc)})
    examples = []
    for name, grid in witness_grids():
        examples.append({"kind": "constructed_counterexample", "name": name, "seed": None, "sample_index": None, "difficulty": None, "overrides": None, "construction": "minimum supported 10x11 canvas; see witness_grids()", "input": grid, "self_check": GEN.self_check(grid), "strict_canonical_like": GEN.strict_canonical_like(grid), "independent_python_output": solve(grid), "rival_output": RIVALS[name](grid)})
    for pair in canonical:
        examples.append({"kind": "canonical", "pair_identity": {k: pair[k] for k in ("variant", "split", "pair_index")}, "input": pair["input"], "canonical_output": pair["output"]})
    # Four bands, one seed, fourteen successive inputs per band: 56 exact
    # generated inputs retained, enough for 44 overlapping 4-pair windows.
    for call, grid in records:
        if call["seed"] == 0 and call["sample_index"] < 14:
            examples.append({"kind": "generated", **call, "input": grid})
    dump("input.json", [record["input"] for record in examples])
    dump("cases.json", examples)
    report = {
        "task_id": TASK, "generator_sha256": SOURCE_SHA, "generator_path": str(SOURCE.relative_to(ROOT)), "generator_version": GEN.VERSION, "declared_rule_hash": GEN.RULE_HASH,
        "canonical": {"labeled_pairs": len(canonical), "independent_oracle_matches": can_oracle, "validator_accepted": can_valid, "adversarial_rival_matches": can_counts, "actual_CANONICAL_SHORTCUTS": declared_canonical, "actual_LESSON_COMPETITORS": competitor_canonical},
        "bounded_generated": {"seeds": list(range(8)), "sample_indexes": list(range(16)), "difficulties": [None, "easy", "medium", "hard"], "overrides": {}, "draws": len(records), "unique_input_count": len({json.dumps(g) for _, g in records}), "self_check_failures": invalid_generated, "adversarial_rivals_matching_independent_python_oracle": dict(matches), "spatial_size_vectors": dict(areas)},
        "controls": {"exact_override_cases": overrides_tested, "seed": 17, "sample_indexes": list(range(4)), "difficulties": [None, "easy", "medium", "hard"], "grid_h": [10, 14], "grid_w": [11, 16], "n_blobs": [2, 3, 4], "errors": override_errors, "invalid_requests": rejections},
        "racket_request_count": len(examples), "racket_output_pending": True,
    }
    dump("probe-summary.json", report)
    print(json.dumps(report, indent=2))
    assert can_oracle == len(canonical) and can_valid == len(canonical)
    assert all(count == len(canonical) for count in can_counts.values())
    assert not invalid_generated and not override_errors and all(r["rejected"] for r in rejections)
    assert all(count == len(records) for count in matches.values())


def finalize():
    report = json.loads((OUT / "probe-summary.json").read_text())
    actual = json.loads((OUT / "racket.json").read_text())
    cases = json.loads((OUT / "cases.json").read_text())
    print(json.dumps({"racket_report_keys": list(actual)}, indent=2))
    # The public apply schema is inspected before this branch is invoked.
    rows = actual["results"]
    assert len(rows) == len(cases)
    assert actual["generator_sha256"] == SOURCE_SHA
    labels = []
    for case, row in zip(cases, rows):
        assert row["input"] == case["input"] and row["valid_output"] and not row["error"]
        expected = row["output"]
        assert expected == solve(case["input"])
        labels.append({**case, "actual_racket_output": expected})
    report["racket_output_pending"] = False
    report["actual_rule_binding"] = {k: v for k, v in actual.items() if k != "results"}
    report["racket_oracle_matches"] = len(rows)
    report["racket_witness_disagreements"] = [case["name"] for case in labels if case["kind"] == "constructed_counterexample" and case["rival_output"] != case["actual_racket_output"]]
    generated = [case for case in labels if case["kind"] == "generated"]
    report["racket_generated_count"] = len(generated)
    report["racket_generated_unique_inputs"] = len({json.dumps(c["input"]) for c in generated})
    report["racket_generated_rival_matches"] = {name: sum(fn(c["input"]) == c["actual_racket_output"] for c in generated) for name, fn in RIVALS.items()}
    lessons, rotations = 0, 0
    declared_failures, rival_survivals = [], Counter()
    for difficulty in (None, "easy", "medium", "hard"):
        band = sorted([c for c in generated if c["difficulty"] == difficulty], key=lambda c: c["sample_index"])
        for start in range(len(band) - 3):
            window = band[start:start + 4]
            lessons += 1
            for qi in range(4):
                demos = [{"input": c["input"], "output": c["actual_racket_output"]} for i, c in enumerate(window) if i != qi]
                query = window[qi]["input"]
                errors = GEN.lesson_identifiable(demos, query)
                rotations += 1
                if errors:
                    declared_failures.append({"difficulty": difficulty, "start": start, "query_position": qi, "errors": errors})
                for name, fn in RIVALS.items():
                    rival_survivals[name] += all(fn(c["input"]) == c["output"] for c in demos)
    report["lessons"] = {"demonstrations": 3, "query_policy": "four consecutive samples, production query last; all four holdouts checked", "ordered_production_windows": lessons, "rotations": rotations, "declared_competitor_failures": declared_failures, "new_rival_surviving_rotations": dict(rival_survivals), "scope": "44 overlapping windows from 56 generated Racket-labelled inputs, not 176 independent lessons"}
    dump("witnesses.json", {"task_id": TASK, "generator_sha256": SOURCE_SHA, "actual_rule_binding": report["actual_rule_binding"], "witnesses": [c for c in labels if c["kind"] == "constructed_counterexample"]})
    dump("probe-summary.json", report)
    print(json.dumps({k: report[k] for k in ("racket_oracle_matches", "racket_witness_disagreements", "racket_generated_rival_matches", "lessons")}, indent=2))
    assert report["generator_sha256"] == SOURCE_SHA
    assert len(report["racket_witness_disagreements"]) == 2 and not declared_failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "finalize"))
    args = parser.parse_args()
    (prepare if args.phase == "prepare" else finalize)()
