from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "7f2dafa2bee4"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
HERE = Path(__file__).resolve().parent
SEED = 0
START = 16
DIFFICULTY = None
DEMO_COUNT = 3
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARD:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append({"input_color": color, "cells": cells})
    return out


def degrees(grid):
    comps = components(grid)
    cell_sets = [set(comp["cells"]) for comp in comps]
    result = []
    for index, cells in enumerate(cell_sets):
        degree = 0
        for other_index, other in enumerate(cell_sets):
            if index == other_index:
                continue
            if any(
                (r + dr, c + dc) in other
                for r, c in cells
                for dr, dc in CARD
            ):
                degree += 1
        result.append(degree)
    return result


def recolor(grid, *, degree_zero_color):
    output = [[0 for _ in row] for row in grid]
    comps = components(grid)
    degree_values = degrees(grid)
    for comp, degree in zip(comps, degree_values):
        if degree == 0:
            color = degree_zero_color
        elif degree == 1:
            color = 2
        elif degree == 2:
            color = 3
        else:
            color = 4
        for r, c in comp["cells"]:
            output[r][c] = color
    return output


def build_probe():
    inputs = [
        GEN.generate(SEED, START + offset, difficulty=DIFFICULTY)
        for offset in range(DEMO_COUNT + 1)
    ]
    records = []
    for offset, grid in enumerate(inputs):
        ds = degrees(grid)
        records.append(
            {
                "role": "demo" if offset < DEMO_COUNT else "query",
                "sample_index": START + offset,
                "degree_sequence": ds,
                "has_degree_zero_object": 0 in ds,
                "self_check_errors": GEN.self_check(grid, difficulty=DIFFICULTY),
                "input": grid,
                "rival_output_degree_zero_to_2": recolor(
                    grid, degree_zero_color=2
                ),
            }
        )
    report = {
        "schema": "arcpuzzles-audit-lesson-ambiguity-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(Path(SOURCE_PATH).relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA256,
        "seed": SEED,
        "sample_start": START,
        "difficulty": DIFFICULTY,
        "demo_count": DEMO_COUNT,
        "rival_rule": (
            "same contact-degree recoloring as canonical except degree 0 maps "
            "to color 2 instead of color 1"
        ),
        "records": records,
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def finalize(racket_path: Path):
    probe = json.loads((HERE / "probe.json").read_text())
    receipt = json.loads(racket_path.read_text())
    results = receipt["results"]
    if len(results) != len(probe["records"]):
        raise RuntimeError("Racket result count does not match probe")
    demo_matches = []
    query_differs = None
    for record, result in zip(probe["records"], results):
        actual = result["output"]
        rival = record["rival_output_degree_zero_to_2"]
        record["racket_output"] = actual
        record["rival_matches_racket"] = rival == actual
        if record["role"] == "demo":
            demo_matches.append(rival == actual)
        else:
            query_differs = rival != actual
    final = {
        **probe,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "racket_receipt": "racket.json",
        "all_three_demos_fit_rival": all(demo_matches) and len(demo_matches) == 3,
        "query_refutes_rival": bool(query_differs),
        "records": probe["records"],
        "commands": [
            {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3",
                    "../checks/audit/7f2dafa2bee4/probe.py"
                ],
            },
            {
                "cwd": "packet_root",
                "argv": [
                    "python3", "review.py", "run", "python3", "-m",
                    "arcpuzzles", "apply", TASK_ID, "--input",
                    "../checks/audit/7f2dafa2bee4/inputs.json",
                    "--check-generator-domain", "--out",
                    "../checks/audit/7f2dafa2bee4/racket.json"
                ],
            },
        ],
    }
    (HERE / "counterexample.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n"
    )
    return final


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    if args.racket is None:
        report = build_probe()
        print(json.dumps({
            "generator_sha256": report["generator_sha256"],
            "degree_sequences": [r["degree_sequence"] for r in report["records"]],
            "self_check_errors": [r["self_check_errors"] for r in report["records"]],
        }, indent=2))
    else:
        report = finalize(args.racket)
        print(json.dumps({
            "generator_sha256": report["generator_sha256"],
            "executed_rule_hash": report["executed_rule_hash"],
            "all_three_demos_fit_rival": report["all_three_demos_fit_rival"],
            "query_refutes_rival": report["query_refutes_rival"],
        }, indent=2))


if __name__ == "__main__":
    main()
