from __future__ import annotations
from collections import deque
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = "2776235f38d3"
GEN, SOURCE, SHA = load_selected_generator(TASK, root=ROOT)


def component(grid, color):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    if not cells:
        return set()
    start = next(iter(cells)); seen = {start}; q = deque([start])
    while q:
        r, c = q.popleft()
        for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if p in cells and p not in seen:
                seen.add(p); q.append(p)
    if seen != cells:
        raise ValueError(f"color {color} is disconnected")
    return seen


def norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return {(r-mr, c-mc) for r, c in cells}


def oracle(grid):
    diff = norm(component(grid, 1)) ^ norm(component(grid, 2))
    if not diff:
        return [[0]]
    r0 = min(r for r, _ in diff); r1 = max(r for r, _ in diff)
    c0 = min(c for _, c in diff); c1 = max(c for _, c in diff)
    out = [[0] * (c1-c0+1) for _ in range(r1-r0+1)]
    for r, c in diff:
        out[r-r0][c-c0] = 8
    return out


def rival(grid):
    expected = oracle(grid)
    if sum(v == 7 for row in grid for v in row) == 1:
        return expected
    return [[0] * len(expected[0]) for _ in expected]

pairs = canonical_pairs(TASK, root=ROOT)
canonical_rows = []
for i, pair in enumerate(pairs):
    errors = GEN.self_check(pair["input"])
    distractors = sorted({v for row in pair["input"] for v in row if v not in (0, 1, 2)})
    canonical_rows.append({
        "index": i,
        "split": pair["split"],
        "pair_index": pair["pair_index"],
        "distractor_colors": distractors,
        "self_check_errors": errors,
        "oracle_matches_label": oracle(pair["input"]) == pair["output"],
        "rival_matches_label": rival(pair["input"]) == pair["output"],
    })

samples = []
inputs = []
for difficulty in ("easy", "medium", "hard"):
    for seed in range(10):
        grid = GEN.generate(seed, 0, difficulty=difficulty)
        expected = oracle(grid)
        inputs.append(grid)
        samples.append({
            "difficulty": difficulty,
            "seed": seed,
            "sample_index": 0,
            "self_check_errors": GEN.self_check(grid),
            "n_color_7": sum(v == 7 for row in grid for v in row),
            "rival_matches_oracle": rival(grid) == expected,
        })

witness = pairs[1]
witness_oracle = oracle(witness["input"])
witness_rival = rival(witness["input"])
(HERE / "input.json").write_text(json.dumps(witness["input"], indent=2) + "\n")
(HERE / "canonical_expected.json").write_text(json.dumps(witness["output"], indent=2) + "\n")
(HERE / "oracle.json").write_text(json.dumps(witness_oracle, indent=2) + "\n")
(HERE / "rival.json").write_text(json.dumps(witness_rival, indent=2) + "\n")
(HERE / "generated-inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SHA,
    "prior_lead": "review-29dec646310b6c97:v0001 (same source SHA)",
    "canonical": {
        "pairs": len(pairs),
        "self_check_rejected": sum(bool(row["self_check_errors"]) for row in canonical_rows),
        "oracle_label_matches": sum(row["oracle_matches_label"] for row in canonical_rows),
        "rival_label_matches": sum(row["rival_matches_label"] for row in canonical_rows),
        "rows": canonical_rows,
    },
    "generated": {
        "cases": len(samples),
        "unique_inputs": len({json.dumps(g, separators=(",", ":")) for g in inputs}),
        "self_check_passes": sum(not row["self_check_errors"] for row in samples),
        "exactly_one_color_7": sum(row["n_color_7"] == 1 for row in samples),
        "rival_oracle_matches": sum(row["rival_matches_oracle"] for row in samples),
        "rows": samples,
    },
    "witness": {
        "canonical_index": 1,
        "distractor_color": 6,
        "self_check_errors": GEN.self_check(witness["input"]),
        "expected": witness["output"],
        "oracle": witness_oracle,
        "rival": witness_rival,
        "disagrees": witness_oracle != witness_rival,
    },
}
(HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "source_sha256": SHA,
    "canonical_rejected": report["canonical"]["self_check_rejected"],
    "generated_rival_matches": report["generated"]["rival_oracle_matches"],
    "witness_disagrees": report["witness"]["disagrees"],
}, sort_keys=True))
