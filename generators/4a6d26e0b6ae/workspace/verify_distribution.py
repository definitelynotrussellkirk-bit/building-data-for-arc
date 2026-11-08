"""Source-hashed, task-local independent integrity gate for bridge generators.

Run from the repository root; --source may point at the packet's frozen original.
All failing inputs are retained, not just the first counterexample. This checks
input structure, NOT labels, model improvement, or lesson identifiability.

Example:
 python3 generators/4a6d26e0b6ae/workspace/verify_distribution.py \
   --seeds 1000 --indices 0,7 --bands none,easy,medium,hard --out ../checks/integrity-final
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


def inspect_scene(grid, expected_count=None, *, overrides=None):
    """Independent center-first scan, unlike the generator's span constructor."""
    issues = []
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
            or any(type(c) is not int or not 0 <= c <= 9 for row in grid for c in row)):
        return {"issues": ["invalid grid"], "invalid_grid": True, "active_gaps": 0,
                "lost_gap": True, "touching": False, "count_mismatch": expected_count is not None}
    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 14 or not 5 <= w <= 14:
        return {"issues": ["grid dimensions outside 5..14"], "invalid_grid": True,
                "active_gaps": 0, "lost_gap": False, "touching": False,
                "count_mismatch": expected_count is not None}
    points, gaps = defaultdict(list), defaultdict(list)
    horizontal = vertical = 0
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                points[color].append((r, c))
                continue
            if 0 < c < w-1 and grid[r][c-1] and grid[r][c-1] == grid[r][c+1]:
                gaps[grid[r][c-1]].append(((r,c-1), (r,c), (r,c+1)))
                horizontal += 1
            if 0 < r < h-1 and grid[r-1][c] and grid[r-1][c] == grid[r+1][c]:
                gaps[grid[r-1][c]].append(((r-1,c), (r,c), (r+1,c)))
                vertical += 1
    bad_colors = [color for color, cells in points.items() if len(cells) != 2 or len(gaps[color]) != 1]
    if bad_colors:
        issues.append(f"colors without exactly one intact endpoint pair: {sorted(bad_colors)}")
    spans = [gaps[color][0] for color in points if color not in bad_colors]
    touching = False
    for i, span in enumerate(spans):
        neighborhoods = {(r+dy, c+dx) for r,c in span for dy in (-1,0,1) for dx in (-1,0,1)}
        if any(neighborhoods.intersection(other) for other in spans[i+1:]):
            touching = True
    if touching:
        issues.append("full motif spans touch or overlap")
    if not points:
        issues.append("no motifs")
    mismatch = expected_count is not None and len(spans) != expected_count
    if mismatch:
        issues.append(f"requested {expected_count} motifs, observed {len(spans)} intact pairs")
    overrides = overrides or {}
    contract_issues = []
    for axis, observed in (("grid_h", h), ("grid_w", w)):
        value = overrides.get(axis)
        if value is not None and (type(value) is not int or value != observed):
            contract_issues.append(f"{axis}: requested {value!r}, observed {observed}")
    boundary = any(r in (0,h-1) or c in (0,w-1) for span in spans for r,c in span)
    texture = overrides.get("texture")
    if texture == "horizontal" and vertical:
        contract_issues.append("horizontal texture contains vertical motifs")
    if texture == "vertical" and horizontal:
        contract_issues.append("vertical texture contains horizontal motifs")
    if texture == "edge" and not boundary:
        contract_issues.append("edge texture has no boundary motif")
    colors = overrides.get("colors")
    if colors is not None:
        if (not isinstance(colors, (list, tuple))
                or any(type(c) is not int or not 1 <= c <= 9 for c in colors)
                or len(set(colors)) != len(colors) or set(colors) != set(points)):
            contract_issues.append("explicit palette differs from observed nonzero colors")
    issues.extend(contract_issues)
    return {"issues": issues, "override_mismatch": bool(contract_issues),
            "contract_issues": contract_issues, "invalid_grid": False, "active_gaps": len(spans),
            "lost_gap": bool(bad_colors), "touching": touching, "count_mismatch": mismatch,
            "bad_colors": sorted(bad_colors), "horizontal_gaps": horizontal,
            "vertical_gaps": vertical, "shape": [h,w], "nonzero_colors": len(points),
            "has_boundary_motif": boundary}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[3]
    parser.add_argument("--repo", type=Path, default=default_root)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=1000)
    parser.add_argument("--indices", default="0")
    parser.add_argument("--bands", default="none")
    parser.add_argument("--override", action="append", default=[], metavar="KEY=JSON")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    try:
        indices = [int(x) for x in args.indices.split(",")]
        bands = [None if x == "none" else x for x in args.bands.split(",")]
        if len(indices) != len(set(indices)) or len(bands) != len(set(bands)):
            raise ValueError("duplicate indices or bands would double-count inputs")
        overrides = {}
        for item in args.override:
            name, raw = item.split("=", 1)
            if not name or name in overrides:
                raise ValueError(f"empty or duplicate override key: {name!r}")
            overrides[name] = json.loads(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    source = args.source or args.repo / "generators/4a6d26e0b6ae/generator.py"
    sys.path.insert(0, str(args.repo.resolve() / "shared/runtime"))
    from puzzle_generators.base import set_ctx_observer
    spec = importlib.util.spec_from_file_location("review_probe_source", source)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    # A replay must use a new evidence directory, never erase a failed run.
    args.out.mkdir(parents=True, exist_ok=False)
    counters, by_band = Counter(), defaultdict(Counter)
    shapes, gaps_hist, unique_inputs = Counter(), Counter(), set()
    started = time.perf_counter()
    with (args.out / "failures.jsonl").open("w") as failures:
        for band in bands:
            for seed in range(args.start_seed, args.start_seed + args.seeds):
                for index in indices:
                    contexts = []
                    set_ctx_observer(contexts.append)
                    location = {"seed": seed, "sample_index": index, "difficulty": band, "overrides": overrides}
                    counters["draws"] += 1
                    by_band[str(band)]["draws"] += 1
                    try:
                        grid = mod.generate(seed, index, difficulty=band, **overrides)
                        raw = json.dumps(grid, separators=(",", ":"))
                        unique_inputs.add(hashlib.sha256(raw.encode()).hexdigest())
                        drawn = contexts[-1].recorded_draws() if contexts else {}
                        # The caller's explicit request outranks a generator's
                        # recorded draws; otherwise ignored overrides can pass.
                        expected = overrides.get("gap_count")
                        if expected is None:
                            expected = drawn.get("gap_count")
                        checked = inspect_scene(grid, expected_count=expected, overrides=overrides)
                        self_errors = mod.self_check(grid, difficulty=band, meta=overrides)
                        # Preserve the full input for every failure; no preview truncation.
                        if self_errors:
                            counters["selfcheck_rejected_draws"] += 1
                            by_band[str(band)]["selfcheck_rejected_draws"] += 1
                        if checked["issues"] or self_errors:
                            counters["failed_draws"] += 1
                            by_band[str(band)]["failed_draws"] += 1
                            if checked["issues"] and not self_errors:
                                counters["invalid_selfcheck_accepted"] += 1
                            failures.write(json.dumps({**location, "input": grid, "inspection": checked,
                                                       "self_check": self_errors, "drawn": drawn}) + "\n")
                        for field in ("lost_gap", "touching", "count_mismatch", "invalid_grid", "override_mismatch"):
                            if checked.get(field):
                                counters[field + "_draws"] += 1
                                by_band[str(band)][field + "_draws"] += 1
                        for field in ("horizontal_gaps", "vertical_gaps"):
                            counters[field] += checked.get(field, 0)
                        counters["boundary_motif_draws"] += bool(checked.get("has_boundary_motif"))
                        if checked.get("shape"):
                            shapes["x".join(map(str, checked["shape"]))] += 1
                        gaps_hist[str(checked["active_gaps"])] += 1
                    except Exception as exc:
                        counters["exceptions"] += 1
                        counters["failed_draws"] += 1
                        by_band[str(band)]["failed_draws"] += 1
                        failures.write(json.dumps({**location, "exception": f"{type(exc).__name__}: {exc}"}) + "\n")
                    finally:
                        set_ctx_observer(None)
    for key in ("failed_draws", "exceptions", "invalid_selfcheck_accepted", "lost_gap_draws", "touching_draws", "count_mismatch_draws", "invalid_grid_draws", "selfcheck_rejected_draws", "override_mismatch_draws"):
        counters.setdefault(key, 0)
    summary = {"schema": "bridge-integrity-probe-v2", "task_id": getattr(mod, "TASK_ID", None),
               "source": str(source), "source_sha256": source_hash, "version": getattr(mod, "VERSION", None),
               "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "sample": {"seed_start": args.start_seed, "seed_stop_exclusive": args.start_seed + args.seeds,
                          "sample_indices": indices, "difficulties": bands, "overrides": overrides},
               "counters": dict(counters), "by_band": dict(by_band), "unique_inputs": len(unique_inputs),
               "shape_histogram": dict(sorted(shapes.items())), "gap_count_histogram": dict(sorted(gaps_hist.items())),
               "elapsed_seconds": time.perf_counter() - started,
               "passed": not counters["failed_draws"],
               "scope": "Input structural integrity only; not Racket parity or model quality."}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("source_sha256", "counters", "unique_inputs", "passed")}, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
