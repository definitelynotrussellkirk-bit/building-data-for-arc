from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "c4d63d8b4567"
root = find_root(Path.cwd())
gen, source_path, source_sha = load_selected_generator(TASK, root=root)


def horizontal_for_repeated_only(grid):
    """Wrong rival: full rule for globally-count-two colors, rows only otherwise."""
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    h, w = len(source), len(source[0])
    colors = sorted({v for row in source for v in row if v})
    counts = {color: sum(v == color for row in source for v in row) for color in colors}

    for r in range(h):
        for color in colors:
            cols = [c for c in range(w) if source[r][c] == color]
            if len(cols) == 2:
                lo, hi = min(cols), max(cols)
                if all(source[r][c] == 0 for c in range(lo + 1, hi)):
                    for c in range(lo, hi + 1):
                        out[r][c] = color

    for c in range(w):
        for color in colors:
            if counts[color] != 2:
                continue
            rows = [r for r in range(h) if source[r][c] == color]
            if len(rows) == 2:
                lo, hi = min(rows), max(rows)
                if all(source[r][c] == 0 for r in range(lo + 1, hi)):
                    for r in range(lo, hi + 1):
                        out[r][c] = color
    return out


counts = {"repeated_total": 0, "horizontal": 0, "vertical": 0, "other": 0}
rival_mismatches = 0
sampled = 0
for band in ("easy", "medium", "hard"):
    for seed in range(50):
        for sample_index in range(4):
            grid = gen.generate(seed, sample_index, difficulty=band)
            sampled += 1
            analysis = gen._analyze(grid)
            assert not analysis["errors"], analysis["errors"]
            repeated = analysis.get("repeated") or []
            for record in repeated:
                counts["repeated_total"] += 1
                orientation = record.get("orientation")
                if orientation == "H":
                    counts["horizontal"] += 1
                elif orientation == "V":
                    counts["vertical"] += 1
                else:
                    counts["other"] += 1
            if horizontal_for_repeated_only(grid) != gen.rule_mirror(grid):
                rival_mismatches += 1

witness = [[0] * 8 for _ in range(7)]
for r, c in ((1, 1), (5, 1), (3, 6)):
    witness[r][c] = 2
for r, c in ((6, 3), (6, 6)):
    witness[r][c] = 4

witness_analysis = gen._analyze(witness)
canonical = gen.rule_mirror(witness)
rival = horizontal_for_repeated_only(witness)
report = {
    "schema": "audit-c4d63d8b4567-vertical-repetition-v1",
    "task_id": TASK,
    "source_path": str(source_path),
    "source_sha256": source_sha,
    "sampled": sampled,
    "counts": counts,
    "rival_mismatches_on_generated": rival_mismatches,
    "witness": witness,
    "witness_self_check": gen.self_check(witness),
    "witness_analysis_errors": witness_analysis["errors"],
    "witness_repeated_orientations": [r["orientation"] for r in witness_analysis.get("repeated", [])],
    "canonical_output": canonical,
    "rival_output": rival,
    "witness_refutes_rival": canonical != rival,
    "witness_input_sha256": hashlib.sha256(json.dumps(witness, separators=(",", ":")).encode()).hexdigest(),
}
Path(__file__).with_name("vertical_repetition_probe.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
Path(__file__).with_name("vertical_repetition_input.json").write_text(
    json.dumps(witness, indent=2) + "\n"
)
print(json.dumps(report, indent=2))
