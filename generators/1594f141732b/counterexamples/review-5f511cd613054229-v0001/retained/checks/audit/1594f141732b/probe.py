#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

TASK_ID = "1594f141732b"
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


def to_grid(rows):
    if rows and isinstance(rows[0], str):
        return [[int(ch) for ch in row] for row in rows]
    return [list(row) for row in rows]


def components4(grid, predicate):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or not predicate(r, c):
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and predicate(nr, nc)
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, sorted(cells)))
    return result


def loose_bbox_cross(grid):
    out = [row[:] for row in grid]
    comps = components4(grid, lambda r, c: grid[r][c] != 0)
    frames = []
    dots = []
    for color, cells in comps:
        if color == 2 and len(cells) == 1:
            dots.append(cells[0])
        elif color != 2:
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            if r2 - r1 >= 2 and c2 - c1 >= 2:
                frames.append((color, r1, c1, r2, c2))
    for color, r1, c1, r2, c2 in frames:
        for dr, dc in dots:
            if r1 < dr < r2 and c1 < dc < c2:
                for c in range(c1 + 1, c2):
                    out[dr][c] = color
                for r in range(r1 + 1, r2):
                    out[r][dc] = color
    return out


def prepare() -> None:
    module = load_module()
    canonical = load_canonical()
    inputs = []
    records = []
    canonical_pairs = canonical["train"] + ([canonical["test"]] if isinstance(canonical["test"], dict) else canonical["test"])
    for index, pair in enumerate(canonical_pairs):
        inputs.append(to_grid(pair["input"]))
        records.append({"kind": "canonical", "index": index, "expected": to_grid(pair["output"])})
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(10):
            grid = module.generate(8100 + band_index, sample_index, difficulty=band)
            inputs.append(grid)
            records.append({
                "kind": "generated",
                "difficulty": band,
                "seed": 8100 + band_index,
                "sample_index": sample_index,
                "self_check": module.self_check(grid, difficulty=band),
            })
    for texture in module.DEGENERATE_TEXTURES:
        grid = module.generate(0, 0, texture=texture)
        inputs.append(grid)
        records.append({
            "kind": "degenerate",
            "texture": texture,
            "seed": 0,
            "sample_index": 0,
            "self_check_with_meta": module.self_check(grid, meta={"texture": texture}),
        })
    (OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (OUT / "records.json").write_text(json.dumps(records, indent=2) + "\n")
    binding = {
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
        "generator_sha256": sha256(GENERATOR_PATH),
        "canonical_path": str(CANONICAL_PATH.relative_to(REPO)),
        "input_count": len(inputs),
        "sample_design": "3 canonical + 10 deterministic draws per band + 3 declared degenerates",
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
    if len(racket["results"]) != len(inputs):
        raise AssertionError("Racket result count mismatch")
    rows = []
    witnesses = []
    for index, (grid, record, result) in enumerate(zip(inputs, records, racket["results"])):
        if result.get("error") is not None:
            raise AssertionError(f"Racket error at {index}: {result['error']}")
        actual = result["output"]
        rival = loose_bbox_cross(grid)
        row = dict(record)
        row.update({
            "index": index,
            "racket_matches_rival": actual == rival,
            "racket_rival_diff_cells": count_diff(actual, rival),
            "self_check_default": module.self_check(grid),
        })
        if record["kind"] == "canonical":
            row["racket_matches_canonical_label"] = actual == record["expected"]
        rows.append(row)
        if actual != rival:
            witnesses.append({
                "index": index,
                "record": record,
                "input": grid,
                "racket_output": actual,
                "rival_output": rival,
                "differing_cells": [
                    [r, c, actual[r][c], rival[r][c]]
                    for r in range(len(grid))
                    for c in range(len(grid[0]))
                    if actual[r][c] != rival[r][c]
                ],
                "self_check_default": module.self_check(grid),
            })
    generated = [row for row in rows if row["kind"] == "generated"]
    degenerates = [row for row in rows if row["kind"] == "degenerate"]
    canonical = [row for row in rows if row["kind"] == "canonical"]
    summary = {
        "task_id": TASK_ID,
        "generator_sha256": sha256(GENERATOR_PATH),
        "executed_rule_hash": racket["executed_rule_hash"],
        "racket_rule_text_sha256": racket["rule_text_sha256"],
        "racket_inputs_accepted": sum(item.get("error") is None for item in racket["results"]),
        "input_count": len(inputs),
        "canonical_labels_matched": sum(row.get("racket_matches_canonical_label", False) for row in canonical),
        "canonical_count": len(canonical),
        "canonical_rival_matches": sum(row["racket_matches_rival"] for row in canonical),
        "generated_rival_matches": sum(row["racket_matches_rival"] for row in generated),
        "generated_count": len(generated),
        "degenerate_rival_matches": sum(row["racket_matches_rival"] for row in degenerates),
        "degenerate_count": len(degenerates),
        "canonical_witness_indices": [w["index"] for w in witnesses if w["record"]["kind"] == "canonical"],
        "canonical_witnesses_passing_self_check": sum(
            w["self_check_default"] == [] for w in witnesses if w["record"]["kind"] == "canonical"
        ),
        "finding": (
            "Generated support and declared degenerates do not distinguish exact rectangular-outline "
            "recognition from a bounding-box shortcut; canonical incomplete/overwritten outlines do."
        ),
    }
    (OUT / "analysis-rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (OUT / "witnesses.json").write_text(json.dumps(witnesses, indent=2) + "\n")
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
