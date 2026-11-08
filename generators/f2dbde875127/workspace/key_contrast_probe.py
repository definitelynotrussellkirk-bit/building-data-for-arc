#!/usr/bin/env python3
"""Replayable source-bound key coverage and counterfactual gate for f2dbde875127.

Run through the packet's run_with_racket.py, or set RACKET_PATH explicitly.
The generator is never used as its own label oracle: labels come from the
unchanged canonical Racket source in an isolated copied runtime. A small Python
spec supplies an independent cross-check; it does not produce training labels.
Counterfactual scoring masks the changed key by comparing only frame interiors.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "f2dbde875127"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def frame_records(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1}
    records = []
    while remaining:
        todo = [min(remaining)]
        cells = set()
        while todo:
            p = todo.pop()
            if p not in remaining:
                continue
            remaining.remove(p)
            cells.add(p)
            r, c = p
            todo.extend(((r-1, c), (r+1, c), (r, c-1), (r, c+1)))
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        border = {(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)
                  if r in (r0, r1) or c in (c0, c1)}
        if cells != border or r0 < 1 or r1-r0 < 2 or c1-c0 < 2:
            raise ValueError("malformed frame")
        keys = [(r0-1, c, grid[r0-1][c]) for c in range(c0, c1+1) if grid[r0-1][c] in (2, 3, 4, 5)]
        if len(keys) != 1:
            raise ValueError("frame must have exactly one key")
        points = [(r, c) for r in range(r0+1, r1) for c in range(c0+1, c1) if grid[r][c]]
        if not points:
            raise ValueError("empty object")
        records.append({"box": [r0, c0, r1, c1], "key_cell": list(keys[0]), "points": points})
    return sorted(records, key=lambda item: item["box"])


def interior_signature(grid, box):
    r0, c0, r1, c1 = box
    return tuple(tuple(grid[r][c] for c in range(c0+1, c1)) for r in range(r0+1, r1))


def key_family(grid, frame_index=0):
    record = frame_records(grid)[frame_index]
    r, c, _ = record["key_cell"]
    family = []
    for key in (2, 3, 4, 5):
        mutated = deepcopy(grid)
        mutated[r][c] = key
        family.append({"key": key, "box": record["box"], "input": mutated})
    return family


def python_transform(grid, *, force_turns=None):
    """Independent, read-only, integer-grid specification for differential tests."""
    out = deepcopy(grid)
    for record in frame_records(grid):
        r0, c0, r1, c1 = record["box"]
        points = record["points"]
        rr = min(r for r, c in points)
        cc = min(c for r, c in points)
        rh = max(r for r, c in points) + 1
        cw = max(c for r, c in points) + 1
        patch = [row[cc:cw] for row in grid[rr:rh]]
        turns = record["key_cell"][2] - 2 if force_turns is None else force_turns
        for _ in range(turns % 4):
            patch = [list(row) for row in zip(*patch[::-1])]
        h, w = len(patch), len(patch[0])
        ih, iw = r1-r0-1, c1-c0-1
        if h > ih or w > iw:
            raise ValueError("rotated object does not fit")
        for r in range(r0+1, r1):
            for c in range(c0+1, c1):
                out[r][c] = 0
        top, left = r0+1+(ih-h)//2, c0+1+(iw-w)//2
        for r, row in enumerate(patch):
            for c, v in enumerate(row):
                out[top+r][left+c] = v
    return out


def _load_module(path):
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=HOME / "generator.py")
    parser.add_argument("--count", type=int, default=128, help="seeds per band, sample_index=0")
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--families", type=int, default=32, help="first N grids per band, first frame")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.count < 1 or args.families < 0 or not args.out.parent.exists():
        parser.error("count must be positive, families nonnegative, and output parent must exist")
    bands = args.bands.split(",")
    if any(b not in ("easy", "medium", "hard") for b in bands) or len(set(bands)) != len(bands):
        parser.error("bands must be distinct easy/medium/hard values")
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    catalog = Catalog(REPO)
    canonical = next(x for x in map(json.loads, (REPO / "shared/data/canonical/puzzles.jsonl").open()) if x["task_id"] == TASK_ID)
    source = canonical["program_solution"]
    report = {
        "schema": "key-contrast-probe-v1", "phase": args.phase,
        "generator_sha256": hashlib.sha256(args.generator.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_rule_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "sampling": {"seed_first": args.start_seed, "seed_last": args.start_seed+args.count-1,
                     "sample_index": 0, "bands": bands, "grids_per_band": args.count,
                     "families_per_band": min(args.families, args.count), "selected_frame": "first by bbox"},
        "canonical": [], "bands": {}, "failures": [], "counterfactual_failures": [],
        "evidence_examples": [], "gate_failures": [],
        "label_authority": "unchanged canonical Racket; Python used only as a differential check",
        "counterfactual_comparison": "selected frame interior, NOT full output including changed key",
    }
    unique = set()
    with tempfile.TemporaryDirectory(prefix="f2dbde-key-contrast-") as directory:
        stage = Path(directory)
        prepare_runtime(catalog, stage, TASK_ID)
        report["runtime_layout"] = str(stage)
        sys.path.insert(0, str(stage))
        from puzzle_generators import runner
        module = _load_module(args.generator)
        bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(source))
        try:
            for split in ("train", "test"):
                for index, pair in enumerate(canonical[split]):
                    output = runner._apply_rule(bridge, name, pair["input"])
                    item = {"split": split, "index": index, "self_check": module.self_check(pair["input"]),
                            "racket_matches_recorded": output == pair["output"],
                            "python_matches_racket": python_transform(pair["input"]) == output}
                    report["canonical"].append(item)
                    if item["self_check"] or not item["racket_matches_recorded"] or not item["python_matches_racket"]:
                        report["gate_failures"].append({"canonical": f"{split}:{index}", "details": item})
            for band in bands:
                counts = Counter()
                key_counts = Counter()
                witnesses = {}
                for offset in range(args.count):
                    seed = args.start_seed + offset
                    identity = {"difficulty": band, "seed": seed, "sample_index": 0}
                    try:
                        grid = module.generate(seed, 0, difficulty=band)
                        errors = module.self_check(grid, difficulty=band)
                        if errors:
                            raise ValueError(f"self_check: {errors}")
                        output = runner._apply_rule(bridge, name, grid)
                        counts["grids"] += 1
                        unique.add(digest(grid))
                        counts["racket_python_matches"] += output == python_transform(grid)
                        counts["identity_outputs"] += output == grid
                        counts["always_clockwise_matches"] += output == python_transform(grid, force_turns=1)
                        counts["recenter_only_matches"] += output == python_transform(grid, force_turns=0)
                        if output != python_transform(grid):
                            report["failures"].append({**identity, "error": "racket/python mismatch", "input": grid, "output": output})
                        ff = frame_records(grid)
                        keys = set()
                        for rec in ff:
                            key = rec["key_cell"][2]
                            keys.add(key)
                            key_counts[key] += 1
                            r0, c0, r1, c1 = rec["box"]
                            counts["frames"] += 1
                            counts["rectangular_frames"] += r1-r0 != c1-c0
                            counts["square_frames"] += r1-r0 == c1-c0
                            if key not in witnesses:
                                witnesses[key] = {**identity, "key": key, "input_sha256": digest(grid)}
                        counts["mixed_key_grids"] += len(keys) > 1
                        if offset < args.families:
                            family = key_family(grid)
                            outcomes = [runner._apply_rule(bridge, name, v["input"]) for v in family]
                            variants = len({interior_signature(o, v["box"]) for o, v in zip(outcomes, family)})
                            counts["counterfactual_families"] += 1
                            counts["counterfactual_racket_calls"] += 4
                            counts["four_distinct_interiors"] += variants == 4
                            if variants != 4:
                                report["counterfactual_failures"].append({**identity, "distinct_interiors": variants,
                                    "box": family[0]["box"], "input": grid,
                                    "interiors": {str(v["key"]): interior_signature(o, v["box"]) for v, o in zip(family, outcomes)}})
                            elif offset == 0:
                                report["evidence_examples"].append({**identity, "input": grid,
                                    "box": family[0]["box"],
                                    "interiors": {str(v["key"]): interior_signature(o, v["box"]) for v, o in zip(family, outcomes)}})
                    except Exception as exc:
                        counts["errors"] += 1
                        report["failures"].append({**identity, "error": f"{type(exc).__name__}: {exc}"})
                report["bands"][band] = {"counts": dict(counts), "keys": dict(key_counts), "key_witnesses": witnesses}
                missing = sorted(set((2, 3, 4, 5)) - set(key_counts))
                if missing:
                    report["gate_failures"].append({"band": band, "missing_keys": missing})
                if counts["grids"] != args.count or counts["identity_outputs"] or counts["racket_python_matches"] != args.count:
                    report["gate_failures"].append({"band": band, "generation_or_semantics": dict(counts)})
        finally:
            bridge.shutdown()
    if report["counterfactual_failures"]:
        report["gate_failures"].append({"nonseparating_key_families": len(report["counterfactual_failures"])})
    report["unique_inputs"] = len(unique)
    report["passed"] = not report["gate_failures"] and not report["failures"]
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("phase", "generator_sha256", "unique_inputs", "passed", "gate_failures")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
