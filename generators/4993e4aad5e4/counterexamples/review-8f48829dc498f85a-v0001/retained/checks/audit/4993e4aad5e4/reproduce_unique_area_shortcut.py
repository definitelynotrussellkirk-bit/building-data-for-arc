#!/usr/bin/env python3
"""Reproduce the unique-area shortcut in generator 4993e4aad5e4.

Run from WORK/repo with:
  python3 ../run_with_racket.py python3 ../checks/audit/4993e4aad5e4/reproduce_unique_area_shortcut.py
"""
from __future__ import annotations

import collections
import copy
import hashlib
import json
import sys
from pathlib import Path

_WORK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_WORK / "repo" / "shared" / "tools"))

import types
_scripts_pkg = types.ModuleType("scripts")
_scripts_pkg.__path__ = [str(_WORK / "repo" / "shared" / "tools")]
sys.modules.setdefault("scripts", _scripts_pkg)

from arc_repl.racket_bridge import RacketBridge
from generator_module_loader import load_module_from_path
from puzzle_generators.rule_wrap import wrap_rule


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(v) for v in row) + ")" for row in grid)
    return f"'({rows})"


def rule_application(source: str, grid: list[list[int]]) -> str:
    return f"({wrap_rule(source)} {_grid_literal(grid)})"

TASK_ID = "4993e4aad5e4"
REPO = Path(__file__).resolve().parents[3] / "repo"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
REPORT_PATH = Path(__file__).with_name("unique-area-shortcut-report.json")


def components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color not in {2, 3, 4, 5} or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": sorted(cells)})
    return result


def unique_area_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: crop the sole object whose cell count is unique."""
    objs = components(grid)
    frequencies = collections.Counter(len(obj["cells"]) for obj in objs)
    candidates = [obj for obj in objs if frequencies[len(obj["cells"])] == 1]
    if len(candidates) != 1:
        raise ValueError(f"expected one unique-area object, found {len(candidates)}")
    cells = candidates[0]["cells"]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    c1 = max(c for _, c in cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = 8
    return out


def canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError("canonical row not found")


def main() -> None:
    gen = load_module_from_path(f"audit_{TASK_ID}", GENERATOR_PATH)
    row = canonical_row()
    generator_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    samples: list[dict] = []
    generated_matches = 0
    generated_total = 0
    first_generated: dict | None = None
    bridge = RacketBridge(max_calls_before_restart=48)
    try:
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(20):
                sample_index = seed % 7
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                before = copy.deepcopy(grid)
                oracle = bridge.eval_text(rule_application(row["program_solution"], grid))
                shortcut = unique_area_shortcut(grid)
                matches = shortcut == oracle
                generated_total += 1
                generated_matches += int(matches)
                record = {
                    "difficulty": difficulty,
                    "seed": seed,
                    "sample_index": sample_index,
                    "object_areas": [len(obj["cells"]) for obj in components(grid)],
                    "matches_oracle": matches,
                }
                samples.append(record)
                if first_generated is None:
                    first_generated = {
                        **record,
                        "input": grid,
                        "oracle_output": oracle,
                        "shortcut_output": shortcut,
                    }
                if grid != before:
                    raise AssertionError("oracle application mutated generated input")

        canonical_results: list[dict] = []
        for split in ("train", "test"):
            pairs = row.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for index, pair in enumerate(pairs):
                objs = components(pair["input"])
                try:
                    shortcut = unique_area_shortcut(pair["input"])
                    shortcut_status = "defined"
                    matches = shortcut == pair["output"]
                except ValueError as exc:
                    shortcut = None
                    shortcut_status = str(exc)
                    matches = False
                canonical_results.append({
                    "split": split,
                    "index": index,
                    "object_areas": [len(obj["cells"]) for obj in objs],
                    "shortcut_status": shortcut_status,
                    "matches_label": matches,
                    "input": pair["input"],
                    "label": pair["output"],
                    "shortcut_output": shortcut,
                })
    finally:
        bridge.shutdown()

    report = {
        "task_id": TASK_ID,
        "generator_sha256": generator_hash,
        "generator_version": gen.VERSION,
        "shortcut": "crop the sole object whose cell count is unique, recolored 8",
        "generated": {
            "sample_count": generated_total,
            "oracle_matches": generated_matches,
            "all_match": generated_matches == generated_total,
            "per_band": {
                band: {
                    "sample_count": sum(s["difficulty"] == band for s in samples),
                    "oracle_matches": sum(s["difficulty"] == band and s["matches_oracle"] for s in samples),
                }
                for band in ("easy", "medium", "hard")
            },
            "first_exact_witness": first_generated,
            "sample_summaries": samples,
        },
        "canonical": {
            "pair_count": len(canonical_results),
            "matches": sum(r["matches_label"] for r in canonical_results),
            "fails_or_undefined": sum(not r["matches_label"] for r in canonical_results),
            "pairs": canonical_results,
        },
        "finding": (
            "The generator forces odd_k != k_common, so area alone identifies the target. "
            "That shortcut matches every sampled generated label but is undefined or wrong on "
            "canonical equal-area examples, which require dihedral shape comparison."
        ),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT_PATH),
        "generator_sha256": generator_hash,
        "generated_matches": f"{generated_matches}/{generated_total}",
        "canonical_fail_or_undefined": report["canonical"]["fails_or_undefined"],
    }, indent=2))
    if generated_matches != generated_total:
        raise SystemExit("shortcut did not match every sampled generated oracle output")
    if not report["canonical"]["fails_or_undefined"]:
        raise SystemExit("shortcut unexpectedly fits every canonical pair")


if __name__ == "__main__":
    main()
