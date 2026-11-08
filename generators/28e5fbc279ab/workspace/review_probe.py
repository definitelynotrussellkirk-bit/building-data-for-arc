#!/usr/bin/env python3
"""Reproducible, source-bound stamp-domain census; never modifies a runtime.

Run against an ordinary relocated runtime prepared by arcpuzzles.runtime.
Counts unique inputs separately from draws and retains concrete counterexamples.
All recorded labels are evaluated by the unchanged canonical Racket authority.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "28e5fbc279ab"


def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r+dr, c+dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append(cells)
    return sorted(result, key=lambda cells: (-len(cells), min(cells)))


def inspect_grid(grid):
    h, w = len(grid), len(grid[0])
    green_components = _color_components(grid, 3)
    markers = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 3)]
    if not green_components:
        return {"missing_reference": True, "green_component_count": 0}, None
    largest_size = len(green_components[0])
    ambiguous = sum(len(cells) == largest_size for cells in green_components) != 1
    ref = green_components[0]
    distractors = green_components[1:]
    all_green = set().union(*green_components)
    r0, c0 = min(r for r, c in ref), min(c for r, c in ref)
    shape = {(r-r0, c-c0) for r, c in ref}
    footprints = [{(r+dr, c+dc) for dr, dc in shape} | {(r, c)} for r, c, v in markers]
    metrics = {
        "green_component_count": len(green_components),
        "multiple_green_components": len(green_components) > 1,
        "ambiguous_green_reference": ambiguous,
        "nonsingleton_green_distractor": any(len(cells) != 1 for cells in distractors),
        "stamp_overlap": any(a & b for i, a in enumerate(footprints) for b in footprints[i+1:]),
        "reference_overlap": any(f & all_green for f in footprints),
        "out_of_bounds": any(not (0 <= r < h and 0 <= c < w) for f in footprints for r, c in f),
        "all_markers_lower_right": all(r >= h//2 and c >= w//2 for r, c, v in markers),
        "reference_upper_left": r0 < h//2 and c0 < w//2,
        "marker_above_reference": any(r < r0 for r, c, v in markers),
        "marker_left_of_reference": any(c < c0 for r, c, v in markers),
        "missing_bbox_corner": (0, 0) not in shape,
        "stamp_touches_edge": any(r in (0, h-1) or c in (0, w-1) for f in footprints for r, c in f),
    }
    return metrics, {"shape": sorted(shape), "reference": sorted(ref),
                     "green_distractors": [sorted(cells) for cells in distractors],
                     "markers": markers, "footprints": [sorted(f) for f in footprints]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--per-band", type=int, default=200)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--phase", choices=("before", "intermediate", "final"), required=True)
    args = ap.parse_args()
    if args.per_band <= 0:
        ap.error("--per-band must be positive")
    runtime = args.runtime.resolve()
    sys.path.insert(0, str(runtime))
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, normalized_rule_hash
    bundle = runner._load_bundle(TASK)
    gen = bundle.generator_module
    bridge, fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
    totals, bands, shapes, examples, seen = Counter(), {}, Counter(), {}, set()
    failures = []
    try:
        canonical = []
        for i, pair in enumerate(canonical_pairs(TASK)):
            output = runner._apply_rule(bridge, fn, pair["input"])
            canonical.append({"index": i, "self_check": gen.self_check(pair["input"]),
                              "racket_matches_stored": output == pair["output"]})
        for band in ("easy", "medium", "hard"):
            counts = Counter()
            for index in range(args.per_band):
                counts["attempts"] += 1
                try:
                    g = gen.generate(args.seed, index, difficulty=band)
                    metrics, detail = inspect_grid(g)
                    out = runner._apply_rule(bridge, fn, g)
                    metrics["self_check_rejected"] = bool(gen.self_check(g))
                    metrics["input_marker_overwritten"] = any(out[r][c] != v for r,c,v in detail["markers"])
                    metrics["identity"] = g == out
                    if hasattr(gen, "rule_mirror"):
                        metrics["mirror_disagreement"] = gen.rule_mirror(g) != out
                    for name, value in metrics.items():
                        counts[name] += int(value)
                        if value and name in {"ambiguous_green_reference", "nonsingleton_green_distractor",
                                                  "stamp_overlap", "reference_overlap", "out_of_bounds",
                                                  "input_marker_overwritten", "mirror_disagreement"}:
                            examples.setdefault(name, {"seed": args.seed, "sample_index": index, "difficulty": band,
                                                      "overrides": {}, "input": g, "actual_racket_output": out,
                                                      "validator_messages": gen.self_check(g), "geometry": detail})
                    shapes[str(detail["shape"])] += 1
                    seen.add(json.dumps(g, separators=(",", ":")))
                    counts["completed"] += 1
                except Exception as exc:
                    counts["errors"] += 1
                    failures.append({"seed": args.seed, "sample_index": index, "difficulty": band,
                                     "error": f"{type(exc).__name__}: {exc}"})
            totals.update(counts)
            bands[band] = dict(counts)
    finally:
        bridge.shutdown()
    path = Path(gen.__file__)
    report = {"schema": "stamp-domain-census-v1", "task_id": TASK, "phase": args.phase,
              "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "rule_sha256": hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
              "rule_hash": normalized_rule_hash(bundle.rule_source), "runtime": str(runtime),
              "sampling": {"seed": args.seed, "sample_index_inclusive": [0, args.per_band-1],
                           "bands": ["easy", "medium", "hard"]},
              "totals": dict(totals), "bands": bands, "unique_inputs": len(seen),
              "unique_normalized_shapes": len(shapes), "shape_counts": dict(shapes),
              "canonical": canonical, "counterexamples": examples, "failures": failures,
              "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("phase", "source_sha256", "totals", "unique_inputs", "unique_normalized_shapes", "canonical")}, indent=2))
    fatal = totals["errors"] + totals["mirror_disagreement"]
    if args.phase == "final":
        fatal += sum(totals[k] for k in (
            "ambiguous_green_reference", "nonsingleton_green_distractor",
            "stamp_overlap", "reference_overlap", "out_of_bounds",
            "input_marker_overwritten", "self_check_rejected", "identity"
        ))
        fatal += sum(not p["racket_matches_stored"] or bool(p["self_check"]) for p in canonical)
    return int(bool(fatal))


if __name__ == "__main__":
    raise SystemExit(main())
