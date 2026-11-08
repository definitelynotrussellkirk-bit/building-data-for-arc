#!/usr/bin/env python3
"""Focused, reproducible override and shape diagnostics for e521d16d403e.

This is a task-local diagnostic, not the full battery or a replacement oracle.
It records grid-derived measurements and (when the original shape helpers are
present) temporary in-memory instrumentation of accepted placements. Production
source is never modified. Run from the packet root, for example::

    python3 run_with_racket.py python3 \
      generators/e521d16d403e/workspace/override_probe.py \
      --generator ../checks/override-investigation/baseline_generator.py \
      --out ../checks/override-investigation/baseline-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                     sort_keys=True).encode()).hexdigest()


def components(grid, same_color=True):
    """Independent 4-connected cell lists in row-major component order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] and
                            (not same_color or grid[nr][nc] == color)):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            r0, r1 = min(x[0] for x in cells), max(x[0] for x in cells)
            c0, c1 = min(x[1] for x in cells), max(x[1] for x in cells)
            mask = set(cells)
            crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
            mask_sym = all((rr, c0 + c1 - cc) in mask for rr, cc in cells)
            raw_sym = all(row == row[::-1] for row in crop)
            result.append({
                "color": color, "colors": sorted({grid[rr][cc] for rr, cc in cells}),
                "cells": sorted(cells), "size": len(cells),
                "bbox": [r0, c0, r1, c1], "height": r1 - r0 + 1,
                "width": c1 - c0 + 1, "mask_lr_symmetric": mask_sym,
                "raw_crop_lr_symmetric": raw_sym,
                "eligible_raw_lr_symmetric": c1 > c0 and raw_sym,
                "crop": crop,
            })
    return result


@contextmanager
def placement_trace(module):
    """Tag helper-produced blocks and record only actual painted placements."""
    names = ("_make_sym_block", "_make_asym_block", "_paint")
    records = []
    if not all(callable(getattr(module, name, None)) for name in names):
        yield records
        return
    original = {name: getattr(module, name) for name in names}
    tags = {}
    retained = []
    sym_calls = 0

    def make_sym(*args, **kwargs):
        nonlocal sym_calls
        block = original["_make_sym_block"](*args, **kwargs)
        tags[id(block)] = "answer" if sym_calls == 0 else "symmetric_decoy"
        retained.append(block)
        sym_calls += 1
        return block

    def make_asym(*args, **kwargs):
        block = original["_make_asym_block"](*args, **kwargs)
        tags[id(block)] = "asymmetric_distractor"
        retained.append(block)
        return block

    def paint(grid, block, rr, rc):
        records.append({"role": tags.get(id(block), "other"),
                        "origin": [rr, rc], "block": block,
                        "block_shape": [len(block), len(block[0])],
                        "components": components(block)})
        return original["_paint"](grid, block, rr, rc)

    module._make_sym_block = make_sym
    module._make_asym_block = make_asym
    module._paint = paint
    try:
        yield records
    finally:
        for name, fn in original.items():
            setattr(module, name, fn)


def draw(module, seed, overrides=None, band="easy", sample_index=0):
    overrides = dict(overrides or {})
    result = {"seed": seed, "sample_index": sample_index,
              "difficulty": band, "overrides": overrides}
    from puzzle_generators.base import set_ctx_observer
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        with placement_trace(module) as placements:
            grid = module.generate(seed, sample_index, difficulty=band, **overrides)
        result.update(grid=grid, grid_sha256=digest(grid),
                      shape=[len(grid), len(grid[0])],
                      components=components(grid), placements=placements,
                      placement_counts=dict(Counter(x["role"] for x in placements)))
        checker = getattr(module, "self_check", None)
        result["self_check"] = checker(grid, difficulty=band) if checker else None
        observer = getattr(module, "observe_overrides", None)
        if observer:
            result["observed_overrides"] = observer(grid)
        if contexts:
            result["keyed_draws"] = contexts[-1].recorded_draws()
            result["used_overrides"] = contexts[-1].overrides_used()
    except Exception as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        set_ctx_observer(None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path,
                        default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--out", required=True, type=Path,
                        help="new JSON evidence file; existing paths are refused")
    parser.add_argument("--search-seeds", type=int, default=500)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite existing evidence: {args.out}")
    if args.search_seeds < 0:
        parser.error("--search-seeds must be nonnegative")
    source = args.generator.resolve()
    spec = importlib.util.spec_from_file_location("override_probe_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = {"schema_version": 1, "generator_path": str(source),
              "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "command": sys.argv, "axes": getattr(module, "AXES", {}),
              "has_observe_overrides": callable(getattr(module, "observe_overrides", None)),
              "grid_hash_serialization": "JSON sorted keys, compact separators",
              "explicit_cases": [], "inert_axis_sweeps": {},
              "first_witnesses": {}, "search_counts": {}, "lawful_candidates": []}

    explicit = [
        (0, "easy", {}),
        (0, "easy", {"grid_h": 22}),
        (0, "hard", {"grid_h": 12}),
        (0, "easy", {"sym_w": 4}),
        (21, "easy", {"sym_h": 6, "sym_w": 4}),
        (0, "easy", {"sym_w": 5}),
        (0, "easy", {"sym_w": 7}),
        (0, "easy", {"grid_h": 12, "grid_w": 12, "n_asym": 3,
                      "sym_h": 6, "sym_w": 7, "n_sym_decoy": 2}),
        (0, "easy", {"__override_contract_unknown_axis__": 1}),
        (0, "easy", {"sym_w": 2}),
        (0, "easy", {"n_asym": 0}),
        (0, "easy", {"palette_size": 1}),
        (0, "easy", {"texture": "full_grid", "grid_h": 12}),
    ]
    report["explicit_cases"] = [draw(module, seed, ov, band) for seed, band, ov in explicit]

    sweeps = {"palette_kind": ["warm", "cool", "broad", "primary"],
              "position_bias": ["scattered", "spread", "centered", "rng"],
              "anchor_corner": [False, True],
              "texture": ["scattered", "spread", "centered", "rng"]}
    for axis, values in sweeps.items():
        rows = []
        for band in ("easy", "medium", "hard"):
            for seed in range(10):
                outputs = [draw(module, seed, {axis: v}, band) for v in values]
                rows.append({"seed": seed, "difficulty": band,
                             "values": values,
                             "hashes": [x.get("grid_sha256") for x in outputs],
                             "errors": [x.get("error") for x in outputs],
                             "all_equal": len({x.get("grid_sha256") for x in outputs}) == 1
                             and not any(x.get("error") for x in outputs)})
        report["inert_axis_sweeps"][axis] = rows

    search_cases = [
        ("default", "easy", {}),
        ("even_width", "easy", {"sym_w": 4}),
        ("wide_odd", "easy", {"sym_w": 7}),
        ("tight", "easy", {"grid_h": 12, "grid_w": 12, "n_asym": 3,
                             "sym_h": 6, "sym_w": 7, "n_sym_decoy": 2}),
    ]
    for name, band, overrides in search_cases:
        counts = Counter()
        for seed in range(args.search_seeds):
            row = draw(module, seed, overrides, band)
            if "error" in row:
                counts["generation_error"] += 1
                continue
            for p in row["placements"]:
                cs = p["components"]
                label = None
                if p["role"] == "answer" and cs:
                    if not cs[0]["eligible_raw_lr_symmetric"]:
                        label = "answer_not_eligible_symmetric"
                    if cs[0]["width"] != p["block_shape"][1]:
                        shrink = "answer_bbox_narrower_than_block"
                        counts[shrink] += 1
                        report["first_witnesses"].setdefault(name + ":" + shrink, row)
                elif p["role"] == "asymmetric_distractor":
                    if len(cs) > 1:
                        label = "disconnected_asymmetric_distractor"
                    elif cs and cs[0]["mask_lr_symmetric"]:
                        label = "asymmetric_distractor_is_symmetric"
                if label:
                    counts[label] += 1
                    report["first_witnesses"].setdefault(name + ":" + label, row)
            for role, requested in (("asymmetric_distractor", overrides.get("n_asym", 2)),
                                    ("symmetric_decoy", overrides.get("n_sym_decoy"))):
                if requested is not None and row["placements"] and row["placement_counts"].get(role, 0) < requested:
                    label = "underplaced_" + role
                    counts[label] += 1
                    report["first_witnesses"].setdefault(name + ":" + label, row)
            if row["self_check"]:
                counts["self_check_rejected"] += 1
                report["first_witnesses"].setdefault(name + ":self_check_rejected", row)
        report["search_counts"][name] = {"draws": args.search_seeds,
                                        "event_counts": dict(counts)}

    lawful = {
        "single_symmetric_object": [[0, 0, 0, 0], [0, 2, 2, 0], [0, 2, 2, 0]],
        "touching_distinct_colors": [[1, 1, 2, 2], [1, 1, 2, 2]],
        "tied_symmetric_objects": [[1, 1, 0, 2, 2], [1, 1, 0, 2, 2]],
        "only_width_one_symmetry": [[3, 0, 0, 0, 0], [3, 0, 2, 2, 0], [3, 0, 2, 0, 0]],
    }
    for name, grid in lawful.items():
        report["lawful_candidates"].append({"name": name, "grid": grid,
            "grid_sha256": digest(grid), "components": components(grid),
            "self_check": module.self_check(grid)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "generator_sha256": report["generator_sha256"],
                      "search_counts": report["search_counts"],
                      "first_witnesses": {key: {"seed": row["seed"],
                         "sample_index": row["sample_index"], "difficulty": row["difficulty"],
                         "overrides": row["overrides"], "grid_sha256": row.get("grid_sha256"),
                         "placement_counts": row.get("placement_counts"),
                         "self_check": row.get("self_check")}
                         for key, row in report["first_witnesses"].items()}}, indent=2))


if __name__ == "__main__":
    main()
