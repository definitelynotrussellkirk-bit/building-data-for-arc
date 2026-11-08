"""Bounded authoring audit: four ordinary draws and one lawful long route.

All reference labels are obtained with the supported public arcpuzzles apply
command. The independent tracer below implements the visible selected Racket
semantics, including its 500-cell fuel limit, and a finite-depth rival.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "8b3462620478"
EXPECTED_SOURCE = "f3794014b466fab737ca0249cdb02fe187d86f16bd46a40a45657da1d49008d0"
OUT = Path(__file__).resolve().parent


def trace(grid, *, mirror_limit=None, fuel=500):
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    arrow = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    assert len(source) == len(arrow) == 1
    dr, dc = arrow[0][0] - source[0][0], arrow[0][1] - source[0][1]
    assert abs(dr) + abs(dc) == 1
    row, col = arrow[0][0] + dr, arrow[0][1] + dc
    height, width = len(grid), len(grid[0])
    output = [list(cells) for cells in grid]
    seen = set()
    steps = mirror_count = 0
    while True:
        if fuel is not None and steps == fuel:
            stop = "fuel"
            break
        if not (0 <= row < height and 0 <= col < width):
            stop = "edge"
            break
        if grid[row][col] == 5:
            stop = "wall"
            break
        state = row, col, dr, dc
        if state in seen:
            stop = "loop"
            break
        seen.add(state)
        value = grid[row][col]
        if value == 0:
            output[row][col] = 8
        elif value in (3, 4):
            mirror_count += 1
            if mirror_limit is None or mirror_count <= mirror_limit:
                dr, dc = (-dc, -dr) if value == 3 else (dc, dr)
        row, col = row + dr, col + dc
        steps += 1
    return output, {"steps_after_heading": steps, "mirrors_encountered": mirror_count,
                    "stop": stop, "next_position": [row, col]}


def long_snake():
    """18x28: 502 post-heading positions, no repeated position/direction."""
    height, width = 18, 28
    grid = [[0] * width for _ in range(height)]
    grid[0][0], grid[0][1] = 2, 1
    for row in range(height - 1):
        rightward = row % 2 == 0
        col = width - 1 if rightward else 0
        grid[row][col] = 4 if rightward else 3
        grid[row + 1][col] = 3 if rightward else 4
    return grid


def differences(authority, rival):
    return [{"row": r, "col": c, "racket": color, "alternative": rival[r][c]}
            for r, row in enumerate(authority) for c, color in enumerate(row)
            if color != rival[r][c]]


def save(name, value):
    # Compact JSON keeps the exact grids without a large transport payload.
    (OUT / name).write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8")


def main():
    root = find_root(__file__)
    generator, path, source_hash = load_selected_generator(TASK, root=root)
    assert source_hash == EXPECTED_SOURCE
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    cases = []
    for index in range(4):
        grid = generator.generate(0, index)
        expected, stats = trace(grid)
        rival, rival_stats = trace(grid, mirror_limit=4)
        cases.append({"kind": "ordinary_generated", "seed": 0, "sample_index": index,
                      "difficulty": None, "overrides": {}, "input": grid,
                      "validator_errors": generator.self_check(grid),
                      "observed_axes": generator.observe_overrides(grid),
                      "independent_selected_rule_output": expected,
                      "rival_output": rival, "trace": stats, "rival_trace": rival_stats,
                      "selected_python_mirror": generator._intended_output(grid)})
    long_grid = long_snake()
    expected, stats = trace(long_grid)
    unbounded, unbounded_stats = trace(long_grid, fuel=None)
    cases.append({"kind": "hand_constructed_validator_domain", "seed": None,
                  "sample_index": None, "overrides": None,
                  "construction": "18x28 serpentine crossing every cell exactly once; red (0,0), blue (0,1), alternating paired edge mirrors",
                  "input": long_grid, "validator_errors": generator.self_check(long_grid),
                  "independent_selected_rule_output": expected,
                  "rival_output": unbounded, "trace": stats,
                  "unbounded_trace": unbounded_stats,
                  "selected_python_mirror": generator._intended_output(long_grid)})
    inputs = [pair["input"] for pair in pairs] + [case["input"] for case in cases]
    save("inputs.json", {"inputs": inputs})
    command = [sys.executable, "-m", "arcpuzzles", "--library", str(root), "apply", TASK,
               "--input", str(OUT / "inputs.json"), "--check-generator-domain",
               "--out", str(OUT / "racket.json")]
    start = datetime.now(timezone.utc).isoformat()
    before = time.monotonic()
    process = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=150)
    save("apply-command.json", {"argv": command, "cwd": str(root), "started_at": start,
                               "elapsed_seconds": round(time.monotonic() - before, 3),
                               "exit_code": process.returncode, "stdout": process.stdout,
                               "stderr": process.stderr, "generator_sha256": source_hash})
    assert process.returncode == 0, process.stderr
    receipt = json.loads((OUT / "racket.json").read_text())
    assert receipt["generator_sha256"] == source_hash
    assert hashlib.sha256(path.read_bytes()).hexdigest() == source_hash
    assert len(receipt["results"]) == len(inputs)
    for result in receipt["results"]:
        assert result["valid_output"] and result["error"] is None
        assert result["generator_domain"] == {"status": "valid", "errors": []}
    canonical_rows = []
    for pair, result in zip(pairs, receipt["results"][:len(pairs)], strict=True):
        rival, stats = trace(pair["input"], mirror_limit=4)
        canonical_rows.append({"variant": pair["variant"], "split": pair["split"],
                               "pair_index": pair["pair_index"],
                               "racket_matches_saved_label": result["output"] == pair["output"],
                               "rival_matches_racket": rival == result["output"],
                               "rival_trace": stats})
    for case, result in zip(cases, receipt["results"][len(pairs):], strict=True):
        case["racket_output"] = result["output"]
        case["racket_matches_independent_selected_rule"] = result["output"] == case["independent_selected_rule_output"]
        case["racket_matches_selected_python_mirror"] = result["output"] == case["selected_python_mirror"]
        case["differing_cells"] = differences(result["output"], case["rival_output"])
    demos = [{"input": case["input"], "output": case["racket_output"]} for case in cases[:3]]
    query = {"input": cases[3]["input"], "output": cases[3]["racket_output"]}
    declared = {name: all(solve(pair["input"]) == pair["output"] for pair in demos)
                for name, solve in generator.LESSON_COMPETITORS.items()}
    report = {
        "schema": "mirror-route-bounded-audit-v1", "task_id": TASK,
        "generator_sha256": source_hash, "selected_source": str(path.relative_to(root)),
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"], "rule_file": receipt["rule_file"],
        "canonical": canonical_rows, "cases": cases,
        "ordinary_scene_draws": 4, "hand_constructed_inputs": 1,
        "racket_checked_inputs": len(inputs),
        "ordinary_lesson": {
            "n_demos": 3, "n_queries": 1, "seed": 0, "sample_indices": [0, 1, 2, 3],
            "new_rival": "first_four_mirrors_only",
            "rival_fits_all_canonical_pairs": all(row["rival_matches_racket"] for row in canonical_rows),
            "rival_fits_all_demos": all(not case["differing_cells"] for case in cases[:3]),
            "rival_changes_query": bool(cases[3]["differing_cells"]),
            "declared_rival_survival_on_demos": declared,
            "lesson_identifiable_reasons": generator.lesson_identifiable(demos, query),
        },
        "domain_mirror_mismatch": {
            "validator_accepts": not cases[4]["validator_errors"],
            "racket_matches_independent_500_step_trace": cases[4]["racket_matches_independent_selected_rule"],
            "racket_matches_selected_python_mirror": cases[4]["racket_matches_selected_python_mirror"],
            "differing_cells": differences(cases[4]["racket_output"], cases[4]["selected_python_mirror"]),
            "scope": "Hand-constructed validator-admitted route; outside the ordinary constructor's dimensions/mirror-count family. No ordinary generated-label mismatch is claimed.",
        },
        "limits": "Four ordinary draws at one seed and default difficulty, five labeled canonical pairs, one constructed domain probe. No random prevalence estimate, full battery, universal identifiability claim, or source changes.",
    }
    save("findings.json", report)
    print(json.dumps({"generator_sha256": source_hash,
                      "executed_rule_hash": receipt["executed_rule_hash"],
                      "rule_text_sha256": receipt["rule_text_sha256"],
                      "ordinary_lesson": report["ordinary_lesson"],
                      "ordinary_mismatch_cells": [len(case["differing_cells"]) for case in cases[:4]],
                      "domain_mirror_mismatch": report["domain_mirror_mismatch"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
