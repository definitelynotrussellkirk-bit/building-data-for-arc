"""Reproduce the review's census, Racket parity and shortcut counterexamples.

Run from the packet root using run_with_racket.py (see workspace/README.md).
This is an AUTHORING probe: do not read or run it during an independent solve.
It stages the selected library into a fresh runtime; no training labels are
obtained from the Python diagnostic implementation below.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
TASK_ID = "954070a7d7ce"


def frame_records(grid):
    """Independent color-9 flood fill and axis-marker inventory."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9}
    records = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        queue, component = [first], {first}
        while queue:
            r, c = queue.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    component.add(p)
                    queue.append(p)
        r0, r1 = min(r for r, _ in component), max(r for r, _ in component)
        c0, c1 = min(c for _, c in component), max(c for _, c in component)
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        if component != border or min(r1 - r0, c1 - c0) < 3:
            raise ValueError("incomplete frame")
        top = [(c, grid[r0 + 1][c]) for c in range(c0 + 2, c1) if grid[r0 + 1][c] not in (0, 9)]
        left = [(r, grid[r][c0 + 1]) for r in range(r0 + 2, r1) if grid[r][c0 + 1] not in (0, 9)]
        if len(top) != 1 or len(left) != 1 or top[0][1] != left[0][1]:
            raise ValueError("invalid marker pair")
        records.append((r0, c0, r1, c1, top[0][0], left[0][0], top[0][1]))
    if not records:
        raise ValueError("no frames")
    return records


def diagnostic_output(grid, *, one_per_color=False):
    output, seen = [row[:] for row in grid], set()
    for r0, c0, r1, c1, tc, lr, color in frame_records(grid):
        if one_per_color and color in seen:
            continue
        seen.add(color)
        for r in range(r0 + 1, r1):
            output[r][tc] = color
        for c in range(c0 + 1, c1):
            output[lr][c] = color
    return output


def load_module(path):
    spec = importlib.util.spec_from_file_location("review_subject", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args):
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    generator = args.generator.resolve() if args.generator else HOME / "generator.py"
    args.out.mkdir(parents=True, exist_ok=False)
    canonical = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
                     if json.loads(line).get("task_id") == TASK_ID)
    report = {"schema": "frame-cross-review-probe-v1", "task_id": TASK_ID,
              "generator_sha256": hashlib.sha256(generator.read_bytes()).hexdigest(),
              "canonical_rule_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
              "cohort": "bands easy/medium/hard; seed=i; sample_index=i%8; i=0..per_band-1",
              "per_band": args.per_band, "matrix_enabled": args.matrix,
              "failures": [], "canonical": [], "counterexamples": []}
    shapes, heights, widths, counts, palettes = Counter(), Counter(), Counter(), Counter(), Counter()
    shared = identity = parity = lost = desired_two = total = disagreements = 0
    with tempfile.TemporaryDirectory(prefix="frame-cross-probe-") as temporary:
        runtime = Path(temporary) / "runtime"
        prepare_runtime(Catalog(REPO), runtime, TASK_ID)
        sys.path.insert(0, str(runtime))
        from puzzle_generators import runner
        from puzzle_generators.base import gen_ctx
        subject = load_module(generator)
        report["generator_version"] = subject.VERSION
        report["runtime_directory"] = str(runtime)
        bundle = runner._load_bundle(TASK_ID)
        bridge, function = runner._open_bridge_with_rule(bundle.rule_callable_text)
        try:
            def check_one(grid, coordinates, *, census):
                nonlocal shared, identity, parity, lost, desired_two, total, disagreements
                reasons = subject.self_check(grid)
                answer = runner._apply_rule(bridge, function, grid)
                expected = diagnostic_output(grid)
                records = frame_records(grid)
                if reasons or answer != expected:
                    report["failures"].append({**coordinates, "self_check": reasons,
                                               "racket_matches_diagnostic": answer == expected, "input": grid,
                                               "racket_output": answer, "diagnostic_output": expected})
                if not census:
                    observed = {"grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(records),
                                "n_distinct_colors": len({r[6] for r in records})}
                    if observed != coordinates["overrides"]:
                        report["failures"].append({**coordinates, "observed": observed})
                    return
                total += 1
                parity += answer == expected
                identity += answer == grid
                shapes[f"{len(grid)}x{len(grid[0])}"] += 1
                counts[str(len(records))] += 1
                colors = sorted({r[6] for r in records})
                palettes[",".join(map(str, colors))] += 1
                shared += len(records) > len(colors)
                for r0, c0, r1, c1, *_ in records:
                    heights[str(r1 - r0 + 1)] += 1
                    widths[str(c1 - c0 + 1)] += 1
                rival = diagnostic_output(grid, one_per_color=True)
                if rival != answer:
                    disagreements += 1
                    if not report["counterexamples"]:
                        case = {**coordinates, "input": grid, "reference_output": answer,
                                "rival": "one_cross_per_color", "rival_output": rival,
                                "disagreeing_cells": [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
                                                       if rival[r][c] != answer[r][c]]}
                        (args.out / "shortcut_counterexample.json").write_text(json.dumps(case, indent=2) + "\n")
                        report["counterexamples"].append("shortcut_counterexample.json")
                if subject.VERSION == "1.1.1":
                    ctx = gen_ctx(seed=coordinates["seed"], sample_index=coordinates["sample_index"],
                                  version=subject.VERSION, task_id=TASK_ID,
                                  difficulty=coordinates["difficulty"], overrides={})
                    requested = ctx.draw_rng("layout").randint(1, 2)
                    desired_two += requested == 2
                    lost += requested != len(records)

            for split in ("train", "test"):
                for index, pair in enumerate(canonical[split]):
                    answer = runner._apply_rule(bridge, function, pair["input"])
                    entry = {"split": split, "index": index, "racket_matches_pair": answer == pair["output"],
                             "diagnostic_matches_pair": diagnostic_output(pair["input"]) == pair["output"],
                             "rival_matches_pair": diagnostic_output(pair["input"], one_per_color=True) == pair["output"]}
                    report["canonical"].append(entry)
                    if not entry["racket_matches_pair"] or not entry["diagnostic_matches_pair"]:
                        report["failures"].append({"canonical": entry})
            for band in ("easy", "medium", "hard"):
                for index in range(args.per_band):
                    coords = {"seed": index, "sample_index": index % 8, "difficulty": band}
                    grid = subject.generate(index, index % 8, difficulty=band)
                    check_one(grid, coords, census=True)
            matrix_cases = 0
            if args.matrix:
                for h, w, (nf, nc), band, seed in itertools.product(
                        range(9, 15), range(11, 21), ((1, 1), (2, 1), (2, 2)),
                        ("easy", "medium", "hard"), (0, 17)):
                    overrides = {"grid_h": h, "grid_w": w, "n_frames": nf, "n_distinct_colors": nc}
                    grid = subject.generate(seed, 3, difficulty=band, **overrides)
                    check_one(grid, {"seed": seed, "sample_index": 3, "difficulty": band,
                                     "overrides": overrides}, census=False)
                    matrix_cases += 1
            report["matrix_cases"] = matrix_cases
        finally:
            bridge.shutdown()
    report.update(default_cases=total, default_racket_parity=parity, identity_cases=identity,
                  repeated_color_cases=shared, shortcut_disagreements=disagreements,
                  grid_shapes=dict(sorted(shapes.items())), frame_heights=dict(sorted(heights.items())),
                  frame_widths=dict(sorted(widths.items())), frame_counts=dict(counts),
                  marker_palettes=dict(sorted(palettes.items())),
                  legacy_requested_two=desired_two if subject.VERSION == "1.1.1" else None,
                  legacy_silent_frame_drops=lost if subject.VERSION == "1.1.1" else None)
    report["status"] = "pass" if not report["failures"] else "fail"
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "default_cases", "default_racket_parity",
                                                   "matrix_cases", "identity_cases", "repeated_color_cases",
                                                   "shortcut_disagreements", "legacy_requested_two",
                                                   "legacy_silent_frame_drops")}, indent=2))
    return 0 if report["status"] == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, help="Optional alternate source, e.g. the frozen baseline")
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--matrix", action="store_true", help="Racket-check all 1080 boundary/interior override combinations")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.per_band <= 10000:
        parser.error("--per-band must be in 1..10000")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
