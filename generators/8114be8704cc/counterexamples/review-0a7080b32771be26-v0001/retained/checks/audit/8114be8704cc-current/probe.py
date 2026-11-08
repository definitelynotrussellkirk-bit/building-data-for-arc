from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "8114be8704cc"
HERE = Path(__file__).resolve().parent
ROOT = find_root(HERE)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
EXPECTED_SOURCE_SHA = "8b067da41c9991c7672c206f9b9e1b563822edb410fabf94b04282e7d3b7665f"


def one_wall_interpretation(grid):
    """Generator's documented semantics: only 1 is wall; other nonzero cells seed rooms."""
    h, w = len(grid), len(grid[0])
    out = [[1 if grid[r][c] == 1 else 0 for c in range(w)] for r in range(h)]
    seen = set()
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 1 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 1 and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            seeds = [(r, c, grid[r][c]) for r, c in cells if grid[r][c] not in (0, 1)]
            if seeds:
                min_r, max_r = min(r for r, _ in cells), max(r for r, _ in cells)
                min_c, max_c = min(c for _, c in cells), max(c for _, c in cells)
                out[min_r + (max_r - min_r + 1) // 2][min_c + (max_c - min_c + 1) // 2] = 8
    return out


def prepare():
    assert SOURCE_SHA == EXPECTED_SOURCE_SHA, (SOURCE_SHA, EXPECTED_SOURCE_SHA)
    grid = GEN.generate(1, 0, difficulty=None)
    colors = sorted({value for row in grid for value in row})
    assert {7, 9} <= set(colors), colors
    errors = GEN.self_check(grid)
    assert errors == [], errors
    rival = one_wall_interpretation(grid)
    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    frequency = {}
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        draws = 200
        count = 0
        valid = 0
        unique = set()
        for i in range(draws):
            sample = GEN.generate(811_400 + band_index * 1000 + i, i, difficulty=band)
            unique.add(json.dumps(sample, separators=(",", ":")))
            count += int(bool({value for row in sample for value in row} & {7, 9}))
            valid += int(GEN.self_check(sample, difficulty=band) == [])
        frequency[str(band)] = {
            "draws": draws,
            "with_7_or_9": count,
            "fraction": count / draws,
            "self_check_pass": valid,
            "unique_inputs": len(unique),
        }
    payload = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "generator_path": SOURCE.relative_to(ROOT).as_posix(),
        "generator_sha256": SOURCE_SHA,
        "seed": 1,
        "sample_index": 0,
        "difficulty": None,
        "input": grid,
        "input_sha256": hashlib.sha256(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "input_colors": colors,
        "self_check": errors,
        "generator_domain_rival": rival,
        "frequency": frequency,
        "advertised_override_equal_baseline": {
            "palette_kind_warm": GEN.generate(1, 0, palette_kind="warm") == grid,
            "palette_kind_cool": GEN.generate(1, 0, palette_kind="cool") == grid,
            "anchor_corner_true": GEN.generate(1, 0, anchor_corner=True) == grid,
            "asymmetry_force_true": GEN.generate(1, 0, asymmetry_force=True) == grid,
        },
    }
    (HERE / "probe-pre.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"source_sha256": SOURCE_SHA, "colors": colors, "self_check": errors, "frequency": frequency}, indent=2))


def verify():
    pre = json.loads((HERE / "probe-pre.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    assert SOURCE_SHA == pre["generator_sha256"] == racket["generator_sha256"]
    assert len(racket["results"]) == 1
    result = racket["results"][0]
    assert result["input"] == pre["input"]
    assert result["valid_output"] and result["error"] is None
    actual = result["output"]
    rival = pre["generator_domain_rival"]
    differences = [
        {"row": r, "col": c, "canonical": actual[r][c], "generator_domain": rival[r][c]}
        for r in range(len(actual))
        for c in range(len(actual[0]))
        if actual[r][c] != rival[r][c]
    ]
    assert differences and actual != rival
    payload = {
        **pre,
        "classification": "reproduced defect",
        "finding": "Generator uses 7 and 9 as room seeds, but canonical authority treats 1, 7, and 9 as walls.",
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "canonical_racket_output": actual,
        "differences": differences,
        "outputs_differ": True,
        "apply_command": racket["command"],
        "apply_cwd": "repo",
    }
    (HERE / "counterexample.json").write_text(json.dumps(payload, indent=2) + "\n")
    report = {
        "generator_sha256": SOURCE_SHA,
        "rule_hash": racket["executed_rule_hash"],
        "self_check_pass": pre["self_check"] == [],
        "input_contains_7_and_9": {7, 9} <= set(pre["input_colors"]),
        "outputs_differ": True,
        "difference_count": len(differences),
        "differences": differences,
        "frequency": pre["frequency"],
    }
    (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify"))
    args = parser.parse_args()
    {"prepare": prepare, "verify": verify}[args.mode]()


if __name__ == "__main__":
    main()
