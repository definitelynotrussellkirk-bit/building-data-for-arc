#!/usr/bin/env python3
"""Source-bound Racket timing and semantic comparisons for task 4f065093e631.

Run through review.py run.  Timings are evidence, not unit-test thresholds.
The reference fixtures are exact retained texts; this tool never edits authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid


TASK_ID = "4f065093e631"
HERE = Path(__file__).resolve().parent


def sha256(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid):
    return sha256(json.dumps(grid, separators=(",", ":")))


def source_record(path):
    path = Path(path)
    source = path.read_text()
    return {
        "path": str(path),
        "sha256": sha256(path.read_bytes()),
        "normalized_sha256": sha256(" ".join(source.split())),
    }


def racket_literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute(bridge, source, grid):
    """Execute ordinary lambda text without importing private runner functions.

    These retained programs contain no comment/dict/for-shorthand syntax.
    strip_rule_wrapper is the public extraction helper.  Every source binds
    its own h and w, so the production auto-bind preamble is redundant here.
    """
    body = strip_rule_wrapper(source)
    if not body.lstrip().startswith("(lambda "):
        raise ValueError("This probe accepts explicit ordinary lambda rules only")
    return normalize_grid(bridge.eval_text(f"({body} {racket_literal(grid)})"))


def border(box):
    top, left, bottom, right = box
    return [
        (r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    ]


def paint(grid, box, color):
    result = [row[:] for row in grid]
    for row, col in border(box):
        result[row][col] = color
    return result


def scene(height, width, frames, slots):
    """Construct known roles on nonzero checkerboard noise; no rule inference."""
    grid = [[1 + ((r + c) % 2) for c in range(width)] for r in range(height)]
    for box in [box for _color, box in frames] + list(slots):
        top, left, bottom, right = box
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                grid[row][col] = 0
    for color, box in frames:
        grid = paint(grid, box, color)
    return grid


def handmade_cases():
    """Expected outputs follow named construction roles, including observable ties."""
    specs = [
        ("smallest_3x3", 3, 7, [(8, (0, 0, 2, 2))], [(0, 4, 2, 6)], (0, 4, 2, 6), 8),
        ("boundary_source", 9, 13, [(7, (5, 8, 8, 12))], [(0, 0, 3, 4)], (0, 0, 3, 4), 7),
        ("multiple_targets_first", 13, 16, [(6, (8, 10, 11, 14))],
         [(0, 8, 3, 12), (4, 0, 7, 4), (8, 0, 11, 4)], (0, 8, 3, 12), 6),
        ("equal_area_color_order", 6, 9,
         [(4, (0, 0, 2, 2)), (8, (3, 6, 5, 8))], [], (0, 0, 2, 2), 8),
        ("equal_area_later_top", 12, 15,
         [(8, (0, 0, 3, 4)), (8, (6, 7, 10, 10))],
         [(0, 8, 3, 12), (6, 0, 10, 3)], (6, 0, 10, 3), 8),
        ("equal_area_later_bottom", 10, 20,
         [(8, (0, 10, 2, 17)), (8, (0, 0, 3, 5))],
         [(6, 10, 8, 17), (6, 0, 9, 5)], (6, 0, 9, 5), 8),
        ("smaller_high_color_distractor", 12, 16,
         [(5, (6, 9, 10, 14)), (9, (0, 11, 2, 13))],
         [(0, 0, 4, 5)], (0, 0, 4, 5), 5),
        ("dense_30x30", 30, 30,
         [(5, (20, 20, 26, 25)), (9, (0, 20, 2, 22))],
         [(0, 0, 6, 5), (10, 0, 16, 5)], (0, 0, 6, 5), 5),
        ("tall_boundary_30x30", 30, 30,
         [(7, (0, 0, 29, 13))], [(0, 16, 29, 29)], (0, 16, 29, 29), 7),
    ]
    result = []
    for name, height, width, frames, slots, target, color in specs:
        grid = scene(height, width, frames, slots)
        result.append({
            "id": name, "kind": "handmade", "input": grid,
            "expected": paint(grid, target, color),
            "constructed_frames": frames, "constructed_slots": slots,
            "expected_target": target, "expected_color": color,
        })
    wide = scene(30, 30, [(7, (0, 0, 29, 13))], [(0, 16, 29, 29)])
    for row in range(30):
        for col in (14, 15):
            wide[row][col] = 1 + ((row * 2 + col) % 9)
    result.append({
        "id": "wide_palette_tall_30x30", "kind": "handmade", "input": wide,
        "expected": paint(wide, (0, 16, 29, 29), 7),
        "constructed_frames": [(7, (0, 0, 29, 13))],
        "constructed_slots": [(0, 16, 29, 29)],
        "expected_target": (0, 16, 29, 29), "expected_color": 7,
    })
    return result


def collect_cases():
    root = find_root(__file__)
    generator, path, digest = load_selected_generator(TASK_ID, root=root)
    result = []
    for pair in canonical_pairs(TASK_ID, root=root):
        result.append({
            "id": f"canonical_{pair['split']}_{pair['pair_index']}",
            "kind": "canonical", "input": pair["input"], "expected": pair["output"],
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
        })
    draws = [("reported_failure_seed4_index3", 4, 3, None, None)]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            seed = 4000 + 100 * band_index + profile_index
            draws.append((f"generated_{band}_{profile}", seed, 17 + profile_index, band, profile))
    for name, seed, index, band, profile in draws:
        kwargs = {"difficulty": band}
        if profile is not None:
            kwargs["scene_profile"] = profile
        grid = generator.generate(seed, index, **kwargs)
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError((name, errors))
        result.append({
            "id": name, "kind": "reported_failure" if profile is None else "generated",
            "input": grid, "seed": seed, "sample_index": index,
            "difficulty": band, "overrides": {} if profile is None else {"scene_profile": profile},
            "generator_sha256": digest, "validator": {"passed": True, "errors": errors},
        })
    result.extend(handmade_cases())
    for case in result:
        case["input_sha256"] = grid_hash(case["input"])
    return {
        "schema": "4f065093e631-performance-cases-v1", "task_id": TASK_ID,
        "generator": {"path": str(path), "sha256": digest}, "cases": result,
    }


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run_probe(args):
    cases_path = Path(args.cases)
    cases = json.loads(cases_path.read_text())["cases"]
    if args.select:
        tokens = set(args.select.split(","))
        cases = [case for case in cases if case["id"] in tokens or case["kind"] in tokens]
    if not cases:
        raise ValueError("No cases selected")
    sources = [(Path(path), Path(path).read_text()) for path in args.rule]
    result = {
        "schema": "4f065093e631-rule-comparison-v1", "task_id": TASK_ID,
        "invocation": {"cwd": os.getcwd(), "argv": [sys.executable, *sys.argv]},
        "probe_source": source_record(__file__),
        "cases_path": str(cases_path), "cases_file_sha256": sha256(cases_path.read_bytes()),
        "timeout_seconds": args.timeout, "sources": [source_record(p) for p, _s in sources],
        "cases": [], "complete": False,
    }
    measurements = {}
    for path, source in sources:
        with RacketBridge(timeout=args.timeout) as bridge:
            result.setdefault("runtimes", []).append(bridge.runtime_identity)
            for case in cases:
                entry = {"id": case["id"], "kind": case["kind"],
                         "input_sha256": case["input_sha256"], "rule_sha256": sha256(source)}
                start = time.perf_counter()
                try:
                    output = execute(bridge, source, case["input"])
                    entry.update(status="ok", output=output, output_sha256=grid_hash(output))
                    if "expected" in case:
                        entry["matches_constructed_or_canonical_expected"] = output == case["expected"]
                    measurements[(str(path), case["id"])] = output
                except Exception as exc:
                    entry.update(status="error", error_type=type(exc).__name__, error=str(exc))
                entry["elapsed_seconds"] = round(time.perf_counter() - start, 6)
                result["cases"].append(entry)
                write_json(args.out, result)
                print(json.dumps({k: v for k, v in entry.items() if k != "output"}), flush=True)
    compared = 0
    disagreements = []
    if len(sources) > 1:
        for case in cases:
            outputs = [measurements.get((str(path), case["id"])) for path, _source in sources]
            if all(output is not None for output in outputs):
                compared += 1
                if any(output != outputs[0] for output in outputs[1:]):
                    disagreements.append(case["id"])
    errors = [entry["id"] for entry in result["cases"] if entry["status"] != "ok"]
    expected_mismatches = [entry["id"] for entry in result["cases"]
                           if entry.get("matches_constructed_or_canonical_expected") is False]
    exit_code = int(bool(errors or disagreements or expected_mismatches))
    result.update(complete=True, comparison_count=compared, disagreements=disagreements,
                  errors=errors, expected_mismatches=expected_mismatches, exit_code=exit_code)
    write_json(args.out, result)
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("--out", required=True)
    probe = commands.add_parser("probe")
    probe.add_argument("--cases", required=True)
    probe.add_argument("--rule", action="append", required=True)
    probe.add_argument("--select", default="")
    probe.add_argument("--timeout", type=float, default=10.0)
    probe.add_argument("--out", required=True)
    args = parser.parse_args()
    if Path(args.out).exists():
        parser.error("Choose a new output path; retained evidence is never overwritten")
    if args.command == "capture":
        value = collect_cases()
        write_json(args.out, value)
        print(json.dumps({"path": args.out, "count": len(value["cases"]),
                          "generator_sha256": value["generator"]["sha256"]}))
        return 0
    return run_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
