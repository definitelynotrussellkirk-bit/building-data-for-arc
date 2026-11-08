#!/usr/bin/env python3
"""Regenerate source-bound adversarial lesson witnesses for this review.

This diagnostic never modifies an audited generator. It imports the exact packet
sources, searches deterministic lesson windows, and confirms labels with the
selected Racket rules before writing compact JSON witnesses.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

PACKET = Path(__file__).resolve().parents[3]
WORK = PACKET / "WORK"
REPO = WORK / "repo"
AUDIT_ROOT = WORK / "checks" / "audit"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]

from arcpuzzles import Catalog  # noqa: E402

EXPECTED_SHA = {
    "aae737932036": "976a9e1496e37af6b4e4e03ee06480998cc283c97b5f67fae84b7f81ea8f7f71",
    "0ee277d96857": "a46ff878e8d65ece582324710805019c0d04523e872a6eb2ae37d8de94e867e3",
}

Grid = list[list[int]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    actual = sha256(path)
    expected = EXPECTED_SHA[task_id]
    if actual != expected:
        raise RuntimeError(f"{task_id}: source hash changed: expected {expected}, got {actual}")
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, actual


def selected_outputs(task_id: str, grids: list[Grid]) -> tuple[list[Grid], dict[str, Any]]:
    result = Catalog(REPO).apply(task_id, grids, timeout=120)
    rows = result["results"]
    if not result.get("rule_hash_matches_catalog"):
        raise RuntimeError(f"{task_id}: selected rule hash mismatch")
    if not all(item.get("valid_output") and item.get("error") is None for item in rows):
        raise RuntimeError(f"{task_id}: selected Racket rule failed: {rows}")
    return [item["output"] for item in rows], {
        "rule_hash": result.get("rule_hash"),
        "rule_hash_matches_catalog": result.get("rule_hash_matches_catalog"),
        "cases": len(rows),
        "all_valid": True,
    }


def different_cells(left: Grid, right: Grid) -> list[list[int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return [[-1, -1, len(left), len(right)]]
    return [
        [r, c, left[r][c], right[r][c]]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def true_segment_gravity(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])
    out = [[1 if grid[r][c] == 1 else 0 for c in range(w)] for r in range(h)]
    for c in range(w):
        top = 0
        while top < h:
            if grid[top][c] == 1:
                top += 1
                continue
            bot = top
            while bot + 1 < h and grid[bot + 1][c] != 1:
                bot += 1
            vals = [grid[r][c] for r in range(top, bot + 1) if grid[r][c] not in (0, 1)]
            for offset, value in enumerate(reversed(vals)):
                out[bot - offset][c] = value
            top = bot + 1
    return out


def rival_global_pack_skipping_walls(grid: Grid) -> Grid:
    """Keep 1-cells fixed but pack each full column, ignoring segment boundaries."""
    h, w = len(grid), len(grid[0])
    out = [[1 if grid[r][c] == 1 else 0 for c in range(w)] for r in range(h)]
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] not in (0, 1)]
        slots = [r for r in range(h) if grid[r][c] != 1]
        for r, value in zip(reversed(slots), reversed(values)):
            out[r][c] = value
    return out


def build_segment_witness() -> Path:
    task_id = "aae737932036"
    gen, _, source_sha = load_generator(task_id)
    found: tuple[int, list[Grid], list[Grid], list[Grid]] | None = None
    for seed in range(50_000):
        grids = [gen.generate(seed, i) for i in range(4)]
        intended = [true_segment_gravity(g) for g in grids]
        rivals = [rival_global_pack_skipping_walls(g) for g in grids]
        demo_diffs = [different_cells(intended[i], rivals[i]) for i in range(3)]
        query_diff = different_cells(intended[3], rivals[3])
        if not any(demo_diffs) and query_diff:
            found = seed, grids, intended, rivals
            break
    if found is None:
        raise RuntimeError("no segment-boundary witness found")
    seed, grids, intended, rivals = found
    selected, racket = selected_outputs(task_id, grids)
    if selected != intended:
        raise RuntimeError("independent segment-gravity implementation disagrees with selected Racket")
    demo_diffs = [different_cells(selected[i], rivals[i]) for i in range(3)]
    query_diff = different_cells(selected[3], rivals[3])
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": source_sha,
        "generator_version": gen.VERSION,
        "lesson_convention": {
            "seed": seed,
            "sample_indices": [0, 1, 2, 3],
            "demo_count": 3,
            "query_index": 3,
            "basis": "No EXAMPLES_NEEDED literal is declared, so the authoring default is three demonstrations.",
        },
        "issue": (
            "Independently sampled walls and markers can leave every demonstration compatible with "
            "whole-column packing that ignores interior segment boundaries, while the query requires "
            "the intended independent-segment rule."
        ),
        "rival": {
            "name": "global_column_pack_skipping_ones",
            "definition": (
                "Preserve every 1-cell, collect all non-0/non-1 values in each full column, and pack "
                "them into the lowest non-1 cells without treating interior 1-cells as segment boundaries."
            ),
            "why_plausible": (
                "It is ordinary column gravity with 1-cells retained as occupied cells; demonstrations "
                "that never place a relevant marker above an interior wall cannot distinguish it."
            ),
        },
        "pairs": [
            {
                "role": "demo" if i < 3 else "query",
                "sample_index": i,
                "input": grids[i],
                "selected_racket_output": selected[i],
                "rival_output": rivals[i],
            }
            for i in range(4)
        ],
        "evidence": {
            "demo_difference_counts": [len(x) for x in demo_diffs],
            "query_difference_count": len(query_diff),
            "query_first_differences": query_diff[:40],
            "selected_racket": racket,
        },
        "limits": [
            "This proves one deterministic four-pair window admits the rival; it does not estimate prevalence.",
            "The rival is an adversarial teaching alternative, not a claim about human solver frequency.",
        ],
    }
    out = AUDIT_ROOT / task_id / "missing_segment_boundary_lesson.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def lattice_rival_cap_period_five(grid: Grid) -> Grid:
    n = len(grid)
    color = grid[0][0]
    period = min(n + 1, 5)
    line_index = period - 1
    return [
        [color if r % period == line_index or c % period == line_index else 0 for c in range(15)]
        for r in range(15)
    ]


def build_lattice_witness() -> Path:
    task_id = "0ee277d96857"
    gen, _, source_sha = load_generator(task_id)
    found: tuple[int, list[Grid], list[int]] | None = None
    for seed in range(10_000):
        grids = [gen.generate(seed, i) for i in range(5)]
        sides = [len(g) for g in grids]
        if 5 not in sides[:4] and sides[4] == 5:
            found = seed, grids, sides
            break
    if found is None:
        raise RuntimeError("no unseen-side witness found")
    seed, grids, sides = found
    selected, racket = selected_outputs(task_id, grids)
    rivals = [lattice_rival_cap_period_five(g) for g in grids]
    demo_diffs = [different_cells(selected[i], rivals[i]) for i in range(4)]
    query_diff = different_cells(selected[4], rivals[4])
    if any(demo_diffs) or not query_diff:
        raise RuntimeError("lattice rival did not fit demos and disagree on query")
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": source_sha,
        "generator_version": gen.VERSION,
        "lesson_convention": {
            "seed": seed,
            "sample_indices": [0, 1, 2, 3, 4],
            "demo_count": 4,
            "query_index": 4,
        },
        "issue": (
            "The source says four demonstrations pin side lengths 2, 3, 4, and 5, but side is sampled "
            "independently; a lesson can first expose side 5 only in the query."
        ),
        "rival": {
            "name": "cap_period_at_five",
            "definition": "Use period n+1 for n=2,3,4, but cap the period at 5 for n=5.",
            "why_plausible": "It agrees with every demonstrated side while saturating beyond the largest demonstrated period.",
        },
        "sides": sides,
        "pairs": [
            {
                "role": "demo" if i < 4 else "query",
                "sample_index": i,
                "input": grids[i],
                "selected_racket_output": selected[i],
                "rival_output": rivals[i],
            }
            for i in range(5)
        ],
        "evidence": {
            "demo_difference_counts": [len(x) for x in demo_diffs],
            "query_difference_count": len(query_diff),
            "query_first_differences": query_diff[:40],
            "selected_racket": racket,
        },
        "limits": [
            "This proves one deterministic five-pair window admits the rival; it does not estimate prevalence.",
            "The rival is an adversarial teaching alternative, not a claim about human solver frequency.",
        ],
    }
    out = AUDIT_ROOT / task_id / "unseen_side_lesson.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    paths = [build_segment_witness(), build_lattice_witness()]
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps({
            "path": str(path.relative_to(WORK)),
            "task_id": data["task_id"],
            "seed": data["lesson_convention"]["seed"],
            "demo_difference_counts": data["evidence"]["demo_difference_counts"],
            "query_difference_count": data["evidence"]["query_difference_count"],
            "generator_sha256": data["generator_sha256"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
