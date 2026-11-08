#!/usr/bin/env python3
"""Exhaust declared override conjunctions; observes pixels without label access.

Run in a library or copied task runtime. --out is a required review JSON path.
Rejections describe supported sampler layouts, not general geometric impossibility.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys
import time

TASK_ID = "8e7f766c96bf"


def load_generator():
    # A staged runtime already exposes reviewer_support; a library keeps it here.
    for ancestor in Path(__file__).resolve().parents:
        for folder in (ancestor, ancestor / "shared/runtime"):
            if (folder / "reviewer_support.py").is_file():
                sys.path.insert(0, str(folder))
                break
        else:
            continue
        break
    from reviewer_support import find_root
    root = find_root(__file__)
    paths = (root / "generators" / TASK_ID / "generator.py",
             root / "puzzle_generators/per_puzzle" / (TASK_ID + ".py"),
             root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py")
    source = next(path for path in paths if path.is_file())
    spec = importlib.util.spec_from_file_location("override_support_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return root, source, module


def declared_values(axis):
    if axis["type"] == "int":
        match = re.fullmatch(r"(-?\d+)\.\.(-?\d+)", axis["valid"])
        if not match:
            raise ValueError(f"Unsupported integer declaration: {axis!r}")
        low, high = map(int, match.groups())
        return list(range(low, high + 1))
    if axis["type"] == "str":
        return axis["valid"].split("|")
    raise ValueError(f"Unsupported axis declaration: {axis!r}")


def observe_pixels(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected nonempty list grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected rectangular list rows")
    if any(type(cell) is not int or cell not in (0, 1) for row in grid for cell in row):
        raise ValueError("expected Python integer background/blue pixels")
    visited = set()
    shapes = Counter()
    for row in range(len(grid)):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in visited:
                continue
            cells = set()
            queue = deque([(row, col)])
            visited.add((row, col))
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if 0 <= nr < len(grid) and 0 <= nc < width and grid[nr][nc] == 1 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            rows, cols = zip(*cells)
            top, bottom, left, right = min(rows), max(rows), min(cols), max(cols)
            height, span = bottom-top+1, right-left+1
            if height < 3 or span < 3:
                raise ValueError("component cannot be a hollow rectangle")
            for r in range(top, bottom+1):
                for c in range(left, right+1):
                    expected = int(r in (top, bottom) or c in (left, right))
                    if grid[r][c] != expected:
                        raise ValueError("component bounding box is not empty-interior complete frame")
            shapes[height, span] += 1
    targets = shapes.pop((4, 4), 0)
    if not targets:
        raise ValueError("missing target")
    if set(shapes) <= {(5, 5)} and shapes.get((5, 5), 0) <= 1:
        texture = "sparse"
    elif shapes == Counter({(3, 3): 1, (4, 5): 1, (5, 4): 1}):
        texture = "contrast"
    else:
        raise ValueError(f"unexpected distractors: {shapes}")
    return {"grid_h": len(grid), "grid_w": width, "n_squares": targets, "texture": texture}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--bands", nargs="+", default=["easy", "medium", "hard"])
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root, source, module = load_generator()
    names = list(module.AXES)
    domain = {name: declared_values(module.AXES[name]) for name in names}
    configurations = [dict(zip(names, values)) for values in itertools.product(*(domain[name] for name in names))]
    counts = Counter()
    by_band = {}
    failures = []
    rejections = {}
    status_by_config = {json.dumps(config, sort_keys=True): set() for config in configurations}
    started = time.monotonic()
    for band in args.bands:
        band_counts = Counter()
        for config in configurations:
            key = json.dumps(config, sort_keys=True)
            for seed in args.seeds:
                case = {"seed": seed, "sample_index": args.sample_index, "difficulty": band, "overrides": config}
                counts["calls"] += 1
                band_counts["calls"] += 1
                try:
                    grid = module.generate(seed, args.sample_index, difficulty=band, **config)
                except ValueError as error:
                    counts["rejected_calls"] += 1
                    band_counts["rejected_calls"] += 1
                    status_by_config[key].add("rejected")
                    axes = getattr(error, "incompatible_axes", None)
                    row = rejections.setdefault(key, {"overrides": config, "calls": 0, "first_case": case,
                                                        "message": str(error), "incompatible_axes": axes})
                    row["calls"] += 1
                    if not isinstance(axes, (tuple, list)) or not axes or not set(axes) <= set(config):
                        failures.append({**case, "kind": "missing_explicit_incompatibility", "message": str(error)})
                    continue
                except Exception as error:
                    status_by_config[key].add("error")
                    counts["unexpected_exception_calls"] += 1
                    failures.append({**case, "kind": "unexpected_exception", "message": repr(error)})
                    continue
                counts["successful_calls"] += 1
                band_counts["successful_calls"] += 1
                status_by_config[key].add("success")
                try:
                    observed = observe_pixels(grid)
                    issues = module.self_check(grid)
                    if observed != config or issues:
                        failures.append({**case, "kind": "realized_override_mismatch", "observed": observed, "self_check": issues})
                except Exception as error:
                    failures.append({**case, "kind": "invalid_realized_pixels", "message": repr(error)})
        by_band[band] = dict(band_counts)
        print(f"{band}: {band_counts['successful_calls']} successes, {band_counts['rejected_calls']} rejections; elapsed {time.monotonic()-started:.2f}s", flush=True)
    for key, statuses in status_by_config.items():
        if len(statuses) > 1:
            failures.append({"kind": "seed_or_band_dependent_support", "overrides": json.loads(key), "statuses": sorted(statuses)})
    report = {"schema": "8e7f766c96bf-override-support-v1", "task_id": TASK_ID,
              "generator_version": module.VERSION, "source_path": str(source),
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "command": [sys.executable, *sys.argv], "args": {**vars(args), "out": str(args.out)},
              "root": str(root), "axis_domains": domain, "configuration_count": len(configurations),
              "counts": dict(counts), "counts_by_band": by_band,
              "supported_configuration_count": sum(statuses == {"success"} for statuses in status_by_config.values()),
              "rejected_configuration_count": len(rejections),
              "rejected_configurations": list(rejections.values()), "failure_count": len(failures),
              "first_failures": failures[:100], "elapsed_seconds": round(time.monotonic()-started, 3),
              "limitations": "Rejection confirms sampler shelf support only. No labels or solve evidence were read."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {args.out}; {len(failures)} failures", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
