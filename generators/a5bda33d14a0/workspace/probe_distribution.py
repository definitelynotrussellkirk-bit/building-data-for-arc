#!/usr/bin/env python3
"""Portable input-distribution probe; no Racket or third-party package needed.

From the repository or an exported runtime, run this file with --out REPORT.
Optional --rival FILE loads a Python solve(grid) and passes inputs only. Reports
bind observed samples to exact generator bytes, seed and sample index. Built-in
rivals are explicit weak hypotheses, never used to derive generator outputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _support():
    try:
        import reviewer_support
        return reviewer_support
    except ImportError:
        for parent in Path(__file__).resolve().parents:
            for relative in ("shared/runtime", ""):
                candidate = parent / relative
                if (candidate / "reviewer_support.py").is_file():
                    sys.path.insert(0, str(candidate))
                    import reviewer_support
                    return reviewer_support
        raise


support = _support()


def describe(grid):
    """Measure actual input geometry and colors, independently of AXES labels."""
    cells = [(r, c, v) for r, row in enumerate(grid)
             for c, v in enumerate(row) if v != 0]
    colors = sorted({v for row in grid for v in row})
    info = {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_cells": len(cells), "source_palette_count": len({v for _, _, v in cells}),
            "n_distinct_colors": len(colors), "input_colors": colors,
            "source_cells": cells}
    if not cells:
        return info
    r0, r1 = min(r for r, _, _ in cells), max(r for r, _, _ in cells)
    c0, c1 = min(c for _, c, _ in cells), max(c for _, c, _ in cells)
    coords = {(r, c) for r, c, _ in cells}
    sides = {"top": sum(r == r0 for r, c in coords),
             "bottom": sum(r == r1 for r, c in coords),
             "left": sum(c == c0 for r, c in coords),
             "right": sum(c == c1 for r, c in coords)}
    corners = [name for name, coord in (("NW", (r0, c0)), ("NE", (r0, c1)),
               ("SW", (r1, c0)), ("SE", (r1, c1))) if coord in coords]
    first, last = cells[0], cells[-1]
    info.update(bbox=[r0, c0, r1, c1], bbox_shape=[r1-r0+1, c1-c0+1],
                corners=corners, side_counts=sides,
                interior_cells=sum(r0 < r < r1 and c0 < c < c1 for r, c in coords),
                row_first_last_bbox_exact=(sorted([first[1], last[1]]) == [c0, c1]),
                nw_se_pair=("NW" in corners and "SE" in corners))
    return info


def border_rule(grid, *, first_last=False):
    """Independent Python global-bbox interpretation, preserving source cells."""
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    out = [row[:] for row in grid]
    if not cells:
        return out
    considered = [cells[0], cells[-1]] if first_last else cells
    r0, r1 = min(r for r, _ in considered), max(r for r, _ in considered)
    c0, c1 = min(c for _, c in considered), max(c for _, c in considered)
    for r in range(r0, r1+1):
        for c in range(c0, c1+1):
            if (r in (r0, r1) or c in (c0, c1)) and out[r][c] == 0:
                out[r][c] = 8
    return out


def _counts(values):
    return dict(sorted(Counter(values).items()))


def probe(*, task_id="a5bda33d14a0", root=None, seed=1729, samples=128,
          rival_paths=()):
    root = Path(root).resolve() if root else support.find_root(__file__)
    module, source, digest = support.load_selected_generator(task_id, root=root)
    records, failures = [], []
    for index in range(samples):
        try:
            grid = module.generate(seed, index)
            record = describe(grid)
            record.update(seed=seed, sample_index=index,
                          self_check_errors=module.self_check(grid),
                          shortcut_matches_global=(border_rule(grid, first_last=True) == border_rule(grid)))
            records.append(record)
        except Exception as exc:
            failures.append({"seed": seed, "sample_index": index,
                             "error_type": type(exc).__name__, "error": str(exc)})
    requests = [{"grid_h": 4, "grid_w": 4}, {"grid_h": 18, "grid_w": 18},
                {"n_cells": 8}, {"palette_size": 1}, {"palette_count": 1},
                {"n_distinct_colors": 2}, {"n_distinct_colors": 9},
                {"n_cells": 3, "n_distinct_colors": 9}, {"palette_kind": "warm"},
                {"palette_kind": "cool"}, {"position_bias": "edge"},
                {"texture": "unrecognized"}, {"unknown_axis": 1},
                {"grid_h": 8.0}, {"grid_w": "9"}, {"n_cells": True},
                {"n_distinct_colors": 4.0}]
    overrides = []
    for request in requests:
        row = {"seed": seed, "sample_index": 0, "overrides": request}
        try:
            grid = module.generate(seed, 0, **request)
            row.update(status="accepted", observed=describe(grid),
                       same_as_default=(grid == module.generate(seed, 0)))
        except Exception as exc:
            row.update(status="rejected", error_type=type(exc).__name__, error=str(exc))
        overrides.append(row)
    canonical = []
    for pair in support.canonical_pairs(task_id, root=root):
        canonical.append({"variant": pair["variant"], "split": pair["split"],
                          "pair_index": pair["pair_index"], "observed": describe(pair["input"]),
                          "self_check_errors": module.self_check(pair["input"]),
                          "python_rule_matches_output": border_rule(pair["input"]) == pair["output"],
                          "shortcut_matches_output": border_rule(pair["input"], first_last=True) == pair["output"]})
    rivals = []
    for rival_path in rival_paths:
        path = Path(rival_path).resolve()
        body = path.read_bytes()
        spec = importlib.util.spec_from_file_location("_distribution_rival", path)
        rival = importlib.util.module_from_spec(spec)
        exec(compile(body, str(path), "exec"), rival.__dict__)
        results = []
        for index in range(samples):
            try:
                grid = module.generate(seed, index)
                prediction = rival.solve([row[:] for row in grid])
                results.append({"seed": seed, "sample_index": index,
                                "matches_python_global_rule": prediction == border_rule(grid)})
            except Exception as exc:
                results.append({"seed": seed, "sample_index": index, "error": repr(exc)})
        rivals.append({"source_name": path.name, "sha256": hashlib.sha256(body).hexdigest(), "results": results})
    return {"schema": "arc-input-distribution-probe-v1", "task_id": task_id,
            "generator_source": str(source.relative_to(root)), "generator_sha256": digest,
            "seed": seed, "sample_indices": [0, samples-1], "requested_samples": samples,
            "declared_axes": module.AXES,
            "summary": {"successful_samples": len(records), "generation_failures": len(failures),
                        "n_cells": _counts(str(row["n_cells"]) for row in records),
                        "source_palette_count": _counts(str(row["source_palette_count"]) for row in records),
                        "n_distinct_colors": _counts(str(row["n_distinct_colors"]) for row in records),
                        "joint_shape_source_palette": _counts(f'{row["grid_h"]}x{row["grid_w"]}|{row["source_palette_count"]}' for row in records),
                        "corner_signatures": _counts("+".join(row.get("corners", [])) or "none" for row in records),
                        "nw_se_pair": sum(row.get("nw_se_pair", False) for row in records),
                        "row_first_last_shortcut_matches": sum(row["shortcut_matches_global"] for row in records)},
            "samples": records, "failures": failures, "override_probes": overrides,
            "canonical": canonical, "rivals": rivals,
            "limits": "Input measurements and optional Python hypotheses only. This probe does not execute the authoritative Racket rule or certify correctness."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="a5bda33d14a0")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--rival", type=Path, action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    result = probe(task_id=args.task, root=args.root, seed=args.seed,
                   samples=args.samples, rival_paths=args.rival)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({key: result[key] for key in ("task_id", "generator_sha256", "summary")}))


if __name__ == "__main__":
    main()
