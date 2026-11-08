#!/usr/bin/env python3
"""Reproduce the cell-count-vs-bounding-box curriculum counterexample.

Authoring helper only: this reads canonical labels and must never be used during
visible-only solve episodes.  It dynamically audits every rival declared by the
current generator, then writes one deterministic generated witness.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5cf662353a2a"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE.parent / "generator.py"))


def load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 1) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells)})
    return result


def normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def independent_cell_count_oracle(grid):
    """Independent transcription of the selected sort-and-drop authority."""
    h, w = len(grid), len(grid[0])
    marker_cols = [c for c, value in enumerate(grid[-1]) if value == 1]
    motifs = sorted(components(grid), key=lambda item: len(item["cells"]))
    out = [[0] * w for _ in range(h)]
    for col in marker_cols:
        out[-1][col] = 1
    for col, motif in zip(marker_cols, motifs):
        shape = normalize(motif["cells"])
        top = h - 2 - max(r for r, _ in shape)
        for dr, dc in shape:
            out[top + dr][col + dc] = motif["color"]
    return out


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def declared_rivals(generator):
    result = {}
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        for name, rule in getattr(generator, namespace, {}).items():
            result.setdefault(name, rule)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE.parent / "counterexamples" / "cell-count-vs-bbox" / "witness.json")
    args = parser.parse_args()

    generator = load_generator()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    rivals = declared_rivals(generator)
    canonical_fit = {
        name: all(rule(pair["input"]) == pair["output"] for pair in pairs)
        for name, rule in rivals.items()
    }

    seed, sample_index = 31337, 4
    overrides = {"layout_profile": "canonical_10x12_3", "palette_start": 2}
    grid = generator.generate(seed, sample_index, **overrides)
    authoritative = independent_cell_count_oracle(grid)
    rival_outputs = {name: rule(deepcopy(grid)) for name, rule in rivals.items()}
    differences = {
        name: [
            [r, c, authoritative[r][c], output[r][c]]
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if authoritative[r][c] != output[r][c]
        ]
        for name, output in rival_outputs.items()
    }

    report = {
        "schema": "5cf662353a2a-size-order-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH),
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "declared_rule_hash": generator.RULE_HASH,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": None,
        "overrides": overrides,
        "self_check": generator.self_check(grid),
        "observed_overrides": generator.observe_overrides(grid),
        "canonical_pairs_checked": len(pairs),
        "canonical_rival_fit": canonical_fit,
        "input": grid,
        "independent_authoritative_output": authoritative,
        "rival_outputs": rival_outputs,
        "differing_cells": differences,
        "input_sha256": digest(grid),
        "authoritative_output_sha256": digest(authoritative),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": report["generator_sha256"],
        "canonical_rival_fit": canonical_fit,
        "difference_counts": {name: len(rows) for name, rows in differences.items()},
    }, indent=2, sort_keys=True))
    return 0 if report["self_check"] == [] and all(canonical_fit.values()) and all(differences.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
