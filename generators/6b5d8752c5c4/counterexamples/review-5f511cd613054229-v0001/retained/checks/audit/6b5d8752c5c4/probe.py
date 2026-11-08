#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "6b5d8752c5c4"
REPO = Path(__file__).resolve().parents[3] / "repo"
OUT = Path(__file__).resolve().parent
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical() -> dict:
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise KeyError(TASK_ID)


def components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(cells)
    return result


def stripe_divider_rival(grid):
    """Use each lane's nuisance cell as divider; never compute midpoint."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for cells in components8(grid):
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        horizontal = (c2 - c1) >= (r2 - r1)
        if horizontal:
            for r in range(r1, r2 + 1):
                lane = [(rr, cc) for rr, cc in cells if rr == r]
                dividers = [c for rr, c in lane if grid[rr][c] != 9]
                if len(dividers) != 1:
                    continue
                divider = dividers[0]
                for rr, c in lane:
                    if grid[rr][c] != 9:
                        continue
                    nc = c - 1 if c < divider else c + 1
                    if 0 <= nc < w:
                        out[rr][nc] = 9
        else:
            for c in range(c1, c2 + 1):
                lane = [(rr, cc) for rr, cc in cells if cc == c]
                dividers = [r for r, cc in lane if grid[r][cc] != 9]
                if len(dividers) != 1:
                    continue
                divider = dividers[0]
                for r, cc in lane:
                    if grid[r][cc] != 9:
                        continue
                    nr = r - 1 if r < divider else r + 1
                    if 0 <= nr < h:
                        out[nr][cc] = 9
    return out


def off_center_witness():
    grid = [[0 for _ in range(8)] for _ in range(8)]
    for r in (3, 4):
        for c in range(2, 6):
            grid[r][c] = 9
        grid[r][2] = 6
    return grid


def prepare() -> None:
    module = load_module()
    canonical = load_canonical()
    test_pairs = canonical["test"] if isinstance(canonical["test"], list) else [canonical["test"]]
    pairs = canonical["train"] + test_pairs
    inputs = []
    records = []
    for index, pair in enumerate(pairs):
        inputs.append(pair["input"])
        records.append({"kind": "canonical", "index": index, "expected": pair["output"]})
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(19):
            grid = module.generate(77000 + band_index, sample_index, difficulty=band)
            inputs.append(grid)
            records.append({
                "kind": "generated",
                "difficulty": band,
                "seed": 77000 + band_index,
                "sample_index": sample_index,
                "self_check": module.self_check(grid, difficulty=band),
            })
    witness = off_center_witness()
    inputs.append(witness)
    records.append({
        "kind": "off_center_witness",
        "description": "8x8 2x4 filled bar at rows 3..4, cols 2..5; nuisance cut at left edge of each lane",
        "self_check": module.self_check(witness),
    })
    if len(inputs) > 64:
        raise AssertionError("apply supports at most 64 inputs")
    (OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (OUT / "records.json").write_text(json.dumps(records, indent=2) + "\n")
    binding = {
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
        "generator_sha256": sha256(GENERATOR_PATH),
        "canonical_path": str(CANONICAL_PATH.relative_to(REPO)),
        "input_count": len(inputs),
        "sample_design": "4 canonical + 19 deterministic draws per band + 1 broad-rule off-center witness",
    }
    (OUT / "source-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    print(json.dumps(binding, indent=2))


def count_diff(a, b):
    return sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def analyze() -> None:
    module = load_module()
    inputs = json.loads((OUT / "input.json").read_text())
    records = json.loads((OUT / "records.json").read_text())
    racket = json.loads((OUT / "racket.json").read_text())
    rows = []
    witness_record = None
    for index, (grid, record, result) in enumerate(zip(inputs, records, racket["results"])):
        if result.get("error") is not None:
            raise AssertionError(f"Racket error at {index}: {result['error']}")
        actual = result["output"]
        rival = stripe_divider_rival(grid)
        row = dict(record)
        row.update({
            "index": index,
            "racket_matches_rival": actual == rival,
            "racket_rival_diff_cells": count_diff(actual, rival),
            "self_check_current": module.self_check(grid),
        })
        if record["kind"] == "canonical":
            row["racket_matches_canonical_label"] = actual == record["expected"]
        rows.append(row)
        if record["kind"] == "off_center_witness":
            witness_record = {
                "task_id": TASK_ID,
                "generator_sha256": sha256(GENERATOR_PATH),
                "executed_rule_hash": racket["executed_rule_hash"],
                "rule_text_sha256": racket["rule_text_sha256"],
                "input": grid,
                "racket_output": actual,
                "rival_output": rival,
                "differing_cells": [
                    [r, c, actual[r][c], rival[r][c]]
                    for r in range(len(grid))
                    for c in range(len(grid[0]))
                    if actual[r][c] != rival[r][c]
                ],
                "self_check": module.self_check(grid),
                "documented_generator_domain": False,
                "broad_racket_domain": True,
                "command": racket["command"],
                "cwd": racket["cwd"],
            }
    canonical_rows = [row for row in rows if row["kind"] == "canonical"]
    generated_rows = [row for row in rows if row["kind"] == "generated"]
    witness_row = next(row for row in rows if row["kind"] == "off_center_witness")
    summary = {
        "task_id": TASK_ID,
        "generator_sha256": sha256(GENERATOR_PATH),
        "executed_rule_hash": racket["executed_rule_hash"],
        "racket_rule_text_sha256": racket["rule_text_sha256"],
        "racket_inputs_accepted": sum(item.get("error") is None for item in racket["results"]),
        "input_count": len(inputs),
        "canonical_labels_matched": sum(row.get("racket_matches_canonical_label", False) for row in canonical_rows),
        "canonical_count": len(canonical_rows),
        "canonical_rival_matches": sum(row["racket_matches_rival"] for row in canonical_rows),
        "generated_rival_matches": sum(row["racket_matches_rival"] for row in generated_rows),
        "generated_count": len(generated_rows),
        "generated_breakdown": {
            band: {
                "matches": sum(row["racket_matches_rival"] for row in generated_rows if row["difficulty"] == band),
                "count": sum(row["difficulty"] == band for row in generated_rows),
            }
            for band in ("easy", "medium", "hard")
        },
        "off_center_witness_rival_match": witness_row["racket_matches_rival"],
        "off_center_witness_diff_cells": witness_row["racket_rival_diff_cells"],
        "off_center_witness_self_check": witness_row["self_check_current"],
        "finding": (
            "All sampled lawful lessons admit a stripe-divider shortcut that never computes the bounding-box midpoint; "
            "a broad-Racket off-center stripe separates the rules but is rejected by self_check."
        ),
    }
    (OUT / "analysis-rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (OUT / "counterexample.json").write_text(json.dumps(witness_record, indent=2) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "analyze"))
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        analyze()


if __name__ == "__main__":
    main()
