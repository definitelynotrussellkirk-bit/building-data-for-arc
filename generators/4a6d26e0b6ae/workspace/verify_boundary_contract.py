"""Exhaust the finite override grid, directly exercise fallback, and mutation-test checks.

No labels are produced. Ordinary scenes have an independent pixel/contract check;
explicit negatives get self-check and optional predecessor-equality checks.
All requests/failures are retained in a NEW source-hashed evidence directory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
HELPFUL = ("default", "horizontal", "vertical", "edge")
TEXTURES = HELPFUL + ("no_gaps", "gap_already_filled", "mismatched_endpoints")


def capacity(h, w, texture):
    horizontal = ((h+1)//2) * ((w+1)//4)
    vertical = ((w+1)//2) * ((h+1)//4)
    bound = horizontal if texture == "horizontal" else vertical if texture == "vertical" else max(horizontal, vertical)
    return min(4 if texture == "mismatched_endpoints" else 8, bound)


def requests(seeds):
    for seed in range(seeds):
        for h in range(5, 15):
            for w in range(5, 15):
                for texture in TEXTURES:
                    for count in ((None,) if texture == "no_gaps" else range(1, 9)):
                        overrides = {"grid_h": h, "grid_w": w, "texture": texture}
                        if count is not None:
                            overrides["gap_count"] = count
                        yield {"seed": seed, "sample_index": 7, "difficulty": None,
                               "overrides": overrides,
                               "expected_accept": count is None or count <= capacity(h, w, texture)}


def symmetries(grid):
    current = [row[:] for row in grid]
    for _ in range(4):
        yield [row[:] for row in current]
        yield [row[::-1] for row in current]
        current = [list(row) for row in zip(*current[::-1])]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def sample(module, row):
    try:
        return module.generate(row["seed"], row["sample_index"], difficulty=row["difficulty"], **row["overrides"]), None
    except Exception as exc:
        return None, {"type": type(exc).__name__, "message": str(exc),
                      "incompatible_axes": list(getattr(exc, "incompatible_axes", ()))}


def mutated_cases(grid, overrides):
    points = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                points[color].append((r, c))
    colors = sorted(points)
    a, b = points[colors[0]]
    middle = ((a[0]+b[0])//2, (a[1]+b[1])//2)
    unused = next(c for c in range(1, 10) if c not in points)
    bad = [row[:] for row in grid]; bad[a[0]][a[1]] = 0
    yield "remove_endpoint", bad, dict(overrides)
    bad = [row[:] for row in grid]; bad[middle[0]][middle[1]] = unused
    yield "occupy_gap", bad, dict(overrides)
    bad = [row[:] for row in grid]; bad[a[0]][a[1]] = unused
    yield "mismatch_one_endpoint", bad, dict(overrides)
    yield "wrong_palette", grid, {**overrides, "colors": [unused]}
    yield "wrong_count", grid, {**overrides, "gap_count": overrides["gap_count"] + 1}
    yield "wrong_height", grid, {**overrides, "grid_h": len(grid) + 1}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=HOME / "generator.py")
    ap.add_argument("--compare-source", type=Path)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--mutation-seeds", type=int, default=25)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.seeds < 1 or args.mutation_seeds < 1:
        ap.error("seed counts must be positive")
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(ROOT / "shared/runtime"))
    module = load(args.source, "boundary_generator")
    prior = load(args.compare_source, "boundary_predecessor") if args.compare_source else None
    scanner_path = HOME / "workspace/verify_distribution.py"
    scanner = load(scanner_path, "boundary_independent_scanner")
    counts = Counter(); counts["failures"] = 0
    start = time.perf_counter()
    with (args.out / "requests.jsonl").open("w") as log:
        for request in requests(args.seeds):
            counts["requests"] += 1
            grid, error = sample(module, request)
            row = dict(request); issues = []
            if request["expected_accept"]:
                counts["expected_accepted"] += 1
                if error:
                    issues.append("supported request raised")
                else:
                    problems = module.self_check(grid, meta=request["overrides"])
                    if problems:
                        issues.append("generator self-check rejected supported output")
                        row["self_check"] = problems
                    if request["overrides"]["texture"] in HELPFUL:
                        inspected = scanner.inspect_scene(grid, request["overrides"]["gap_count"], overrides=request["overrides"])
                        if inspected["issues"]:
                            issues.extend(inspected["issues"])
                    row["input_sha256"] = grid_hash(grid)
                    counts["generated"] += 1
            else:
                counts["expected_rejected"] += 1
                if not error or "gap_count" not in error["incompatible_axes"]:
                    issues.append("unsupported count did not produce its structured rejection")
                else:
                    counts["structured_rejections"] += 1
            if prior:
                old_grid, old_error = sample(prior, request)
                equal = (grid == old_grid and error == old_error)
                row["same_as_predecessor"] = equal
                counts["predecessor_comparisons"] += 1
                counts["predecessor_equal"] += equal
                if not equal:
                    issues.append("sampler output or exception changed from predecessor")
            row.update(error=error, issues=issues, passed=not issues)
            if issues:
                counts["failures"] += 1
                row["input"] = grid
            log.write(json.dumps(row) + "\n")
    with (args.out / "fallback.jsonl").open("w") as log:
        for request in requests(args.seeds):
            ov = request["overrides"]
            if not request["expected_accept"] or ov["texture"] not in HELPFUL:
                continue
            h, w, count = ov["grid_h"], ov["grid_w"], ov["gap_count"]
            row = dict(request)
            try:
                spans = module._lattice_fallback(h, w, count, ov["texture"], random.Random(request["seed"]))
                grid = [[0]*w for _ in range(h)]
                for color, (a, _, b) in enumerate(spans, 1):
                    grid[a[0]][a[1]] = grid[b[0]][b[1]] = color
                inspected = scanner.inspect_scene(grid, count, overrides=ov)
                row.update(issues=inspected["issues"], input_sha256=grid_hash(grid))
                if row["issues"]:
                    row["input"] = grid
            except Exception as exc:
                row["issues"] = [f"{type(exc).__name__}: {exc}"]
            counts["direct_fallback_cases"] += 1
            counts["failures"] += bool(row["issues"])
            row["passed"] = not row["issues"]
            log.write(json.dumps(row) + "\n")
    with (args.out / "mutations.jsonl").open("w") as negatives, (args.out / "metamorphic.jsonl").open("w") as positives:
        for seed in range(args.mutation_seeds):
            for texture in HELPFUL:
                ov = {"grid_h": 7, "grid_w": 9, "gap_count": 3, "texture": texture}
                grid = module.generate(seed, 7, **ov)
                for name, bad, meta in mutated_cases(grid, ov):
                    independent = scanner.inspect_scene(bad, meta["gap_count"], overrides=meta)
                    errors = module.self_check(bad, meta=meta)
                    passed = bool(independent["issues"]) and bool(errors)
                    row = {"seed": seed, "sample_index": 7, "base_texture": texture,
                           "mutation": name, "input": bad, "overrides": meta,
                           "independent_issues": independent["issues"], "self_check": errors, "passed": passed}
                    negatives.write(json.dumps(row) + "\n")
                    counts["mutation_cases"] += 1; counts["mutations_rejected"] += bool(errors)
                    counts["failures"] += not passed
                for transform_index, transformed in enumerate(symmetries(grid)):
                    transformed = [[c % 9 + 1 if c else 0 for c in row] for row in transformed]
                    meta = {"grid_h": len(transformed), "grid_w": len(transformed[0]), "gap_count": 3,
                            "colors": sorted({c for row in transformed for c in row if c})}
                    inspected = scanner.inspect_scene(transformed, 3, overrides=meta)
                    errors = module.self_check(transformed, meta=meta)
                    passed = not inspected["issues"] and not errors
                    row = {"seed": seed, "sample_index": 7, "base_texture": texture,
                           "transform_index": transform_index, "color_permutation": "c -> c % 9 + 1; 0 fixed",
                           "input_sha256": grid_hash(transformed), "overrides": meta,
                           "independent_issues": inspected["issues"], "self_check": errors, "passed": passed}
                    if not passed:
                        row["input"] = transformed
                    positives.write(json.dumps(row) + "\n")
                    counts["metamorphic_positive_cases"] += 1; counts["failures"] += not passed
    summary = {"schema": "bridge-boundary-contract-v1", "source_sha256": sha(args.source),
               "compare_source_sha256": sha(args.compare_source) if args.compare_source else None,
               "probe_sha256": sha(Path(__file__)), "independent_scanner_sha256": sha(scanner_path),
               "sample": {"seed_start": 0, "seed_stop_exclusive": args.seeds, "sample_index": 7,
                          "difficulty": None, "dimensions": "cartesian integers 5..14",
                          "textures": list(TEXTURES), "nonblank_counts": list(range(1, 9)),
                          "mutation_seed_stop_exclusive": args.mutation_seeds},
               "counters": dict(counts), "passed": not counts["failures"],
               "elapsed_seconds": time.perf_counter() - start,
               "scope": "Finite override contract and validation; direct fallback calls are separate from sampler requests. Explicit negatives are self-check/predecessor comparisons, not independent geometry proofs. No labels or model scores."}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
