#!/usr/bin/env python3
"""Source-bound area-rank census, rival probe and Racket differential check.

Run from the packet root; --baseline-generator can replay the immutable original
file without changing the working generator. This is a task-local review tool,
not a training admission certificate. It stages the repository's own runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

TASK_ID = "996fc37f49d9"
BANDS = ("easy", "medium", "hard")
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    """Independent set-based flood fill, not the generator's deque routine."""
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    found = []
    while pending:
        first = min(pending)
        todo, cells = [first], {first}
        pending.remove(first)
        while todo:
            row, col = todo.pop()
            for dr, dc in DIRS:
                p = row + dr, col + dc
                if p in pending:
                    pending.remove(p)
                    cells.add(p)
                    todo.append(p)
        found.append(tuple(sorted(cells)))
    return found


def bbox_area(cells):
    rows, cols = zip(*cells)
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def paint_order(grid, key):
    out = [[0] * len(grid[0]) for _ in grid]
    for rank, cells in enumerate(sorted(components(grid), key=key)):
        for r, c in cells:
            out[r][c] = rank + 2
    return out


def intended(grid):
    return paint_order(grid, lambda cells: len(cells))


def rival(grid, name):
    if name == "bbox":
        return paint_order(grid, lambda cells: (bbox_area(cells), min(cells)))
    if name == "scan":
        return paint_order(grid, lambda cells: min(cells))
    if name == "colour":
        return paint_order(grid, lambda cells: (grid[cells[0][0]][cells[0][1]], min(cells)))
    if name == "largest_first":
        return paint_order(grid, lambda cells: -len(cells))
    if name == "identity":
        return [row[:] for row in grid]
    raise ValueError(name)


RIVALS = ("bbox", "scan", "colour", "largest_first", "identity")


def exact_counterexample():
    grid = [[0] * 14 for _ in range(13)]
    for r, c in ((1, 1), (2, 1), (3, 1), (3, 2), (3, 3)):
        grid[r][c] = 7
    for r in (8, 9):
        for c in (8, 9, 10):
            grid[r][c] = 7
    return grid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", choices=("before", "intermediate", "final"), required=True)
    parser.add_argument("--per-band", type=int, default=600)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--lesson-seeds", type=int, default=30)
    parser.add_argument("--racket-per-band", type=int, default=64)
    parser.add_argument("--baseline-generator", type=Path)
    args = parser.parse_args()
    if args.per_band <= 0 or args.lesson_seeds < 0 or not 0 <= args.racket_per_band <= args.per_band:
        parser.error("need positive per-band; nonnegative lesson-seeds; racket-per-band in 0..per-band")
    root = next((p for p in Path(__file__).resolve().parents if (p / "src/arcpuzzles").is_dir()), None)
    if root is None:
        parser.error("run this task-local tool from a native ARCpuzzles library")
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    args.out.mkdir(parents=True)
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    source = args.baseline_generator.resolve() if args.baseline_generator else root / "generators" / TASK_ID / "generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    started = time.perf_counter()
    report = {"schema": "area-rank-review-census-v1", "phase": args.phase, "task_id": TASK_ID,
              "generator_sha256": source_hash, "command": [sys.executable, *sys.argv],
              "working_directory": str(Path.cwd()), "bands": {}, "failures": [],
              "plan": {"seed_start": args.seed_start, "seed_stop_exclusive": args.seed_start + args.per_band,
                       "sample_index": 0, "lesson_seed_start": args.seed_start,
                       "lesson_seed_stop_exclusive": args.seed_start + args.lesson_seeds,
                       "lesson_offsets": list(range(12)), "demos_per_lesson": 3, "queries_per_lesson": 1,
                       "racket_seed_stop_exclusive": args.seed_start + args.racket_per_band}}
    with tempfile.TemporaryDirectory(prefix="area-rank-census-") as temporary:
        runtime = Path(temporary)
        prepare_runtime(Catalog(root), runtime, TASK_ID)
        staged = runtime / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
        shutil.copy2(source, staged)
        sys.path.insert(0, str(runtime))
        spec = importlib.util.spec_from_file_location("subject_generator", staged)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        from puzzle_generators.rule_wrap import wrap_rule
        from puzzle_generators.runner import _open_bridge_with_rule, _apply_rule
        record = next(json.loads(line) for line in (runtime / "data/canonical/puzzles.jsonl").open()
                      if json.loads(line).get("task_id") == TASK_ID)
        program = record["program_solution"]
        report["rule_sha256"] = hashlib.sha256(program.encode()).hexdigest()
        report["canonical_file_sha256"] = hashlib.sha256((runtime / "data/canonical/puzzles.jsonl").read_bytes()).hexdigest()
        bridge, function = _open_bridge_with_rule(wrap_rule(program))
        try:
            report["racket_checked"] = 0
            def apply(grid):
                actual = _apply_rule(bridge, function, grid)
                report["racket_checked"] += 1
                if actual != intended(grid):
                    report["failures"].append({"type": "racket_mismatch", "input": grid, "actual": actual,
                                                "expected": intended(grid)})
                return actual
            public = [*record["train"], *record["test"]]
            report["canonical"] = []
            for index, pair in enumerate(public):
                actual = apply(pair["input"])
                report["canonical"].append({"index": index, "stored_equals_racket": actual == pair["output"],
                                            "validator_errors": gen.self_check(pair["input"]),
                                            "bbox_equals_racket": rival(pair["input"], "bbox") == actual})
                if actual != pair["output"] or gen.self_check(pair["input"]):
                    report["failures"].append({"type": "canonical_mismatch", "index": index})
            grid = exact_counterexample()
            counterexample = {"task_id": TASK_ID, "generator_sha256": source_hash, "rule_sha256": report["rule_sha256"],
                              "seed": None, "sample_index": None, "origin": "handcrafted in documented general_2 domain",
                              "input": grid, "actual_racket_output": apply(grid), "rival_output": rival(grid, "bbox"),
                              "validator_errors": gen.self_check(grid), "command": report["command"],
                              "working_directory": report["working_directory"]}
            (args.out / "bbox_counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
            first_witness = None
            for band in BANDS:
                profiles, palettes, sizes, dimensions = Counter(), Counter(), Counter(), Counter()
                roles, colours = defaultdict(set), defaultdict(Counter)
                unique_inputs, unique_outputs = set(), set()
                disagreements = Counter()
                strict, inversions, invalid, edge = 0, 0, 0, 0
                for seed in range(args.seed_start, args.seed_start + args.per_band):
                    grid = gen.generate(seed, 0, difficulty=band)
                    errors = gen.self_check(grid)
                    invalid += bool(errors)
                    if errors:
                        report["failures"].append({"type": "invalid", "band": band, "seed": seed, "errors": errors})
                    observed = gen.observe_overrides(grid)
                    profiles[observed.get("scene_profile")] += 1
                    palettes[observed.get("color_mode")] += 1
                    strict += not gen.strict_canonical_like(grid)
                    objects = sorted(components(grid), key=len)
                    boxes = [bbox_area(c) for c in objects]
                    inversion = boxes != sorted(boxes)
                    inversions += inversion
                    edge += any(r in (0, len(grid)-1) or c in (0, len(grid[0])-1) for cells in objects for r,c in cells)
                    dimensions[f"{len(grid)}x{len(grid[0])}"] += 1
                    sizes[str(tuple(map(len, objects)))] += 1
                    for rank, cells in enumerate(objects):
                        roles[len(cells)].add(rank + 2)
                        colours[f"{len(objects)}:{observed.get('color_mode')}:{rank+2}"][grid[cells[0][0]][cells[0][1]]] += 1
                    answer = intended(grid)
                    unique_inputs.add(digest(grid)); unique_outputs.add(digest(answer))
                    for name in RIVALS:
                        disagreements[name] += rival(grid, name) != answer
                    if seed < args.seed_start + args.racket_per_band:
                        apply(grid)
                    if inversion and first_witness is None:
                        first_witness = {"task_id": TASK_ID, "generator_sha256": source_hash,
                                         "rule_sha256": report["rule_sha256"], "seed": seed, "sample_index": 0,
                                         "difficulty": band, "overrides": {}, "input": grid,
                                         "actual_racket_output": apply(grid), "rival_output": rival(grid, "bbox"),
                                         "validator_errors": errors, "command": report["command"],
                                         "working_directory": report["working_directory"]}
                report["bands"][band] = {
                    "n": args.per_band, "unique_inputs": len(unique_inputs), "unique_independent_outputs": len(unique_outputs),
                    "invalid": invalid, "strict_canonical": strict, "bbox_strict_inversions": inversions,
                    "rival_disagreements": dict(disagreements), "profiles": dict(profiles), "palettes": dict(palettes),
                    "size_tuples": dict(sizes), "dimensions": dict(dimensions), "edge_touching": edge,
                    "area_to_output_colour_support": {str(k): sorted(v) for k,v in sorted(roles.items())},
                    "rank_input_colour_counts": {k: dict(v) for k,v in sorted(colours.items())}}
            if first_witness is not None:
                (args.out / "generated_bbox_witness.json").write_text(json.dumps(first_witness, indent=2) + "\n")
            lesson_count, ambiguous, hook_rejected, hook_missed, unique_lesson_inputs = 0, [], [], [], set()
            for band in BANDS:
                for seed in range(args.seed_start, args.seed_start + args.lesson_seeds):
                    grids = [gen.generate(seed, si, difficulty=band) for si in range(15)]
                    unique_lesson_inputs.update(digest(g) for g in grids)
                    answers = [intended(g) for g in grids]
                    for offset in range(12):
                        lesson_count += 1
                        demos = [{"input": g, "output": a} for g,a in zip(grids[offset:offset+3], answers[offset:offset+3])]
                        query = {"input": grids[offset+3], "output": answers[offset+3]}
                        bad = [name for name in RIVALS if all(rival(p["input"], name) == p["output"] for p in demos)
                               and rival(query["input"], name) != query["output"]]
                        hook = gen.lesson_identifiable(demos, query)
                        item = {"band": band, "seed": seed, "sample_index": offset, "rivals": bad, "hook_reasons": hook}
                        if bad: ambiguous.append(item)
                        if hook: hook_rejected.append(item)
                        if bad and not hook: hook_missed.append(item)
            report["lessons"] = {"n_overlapping_windows": lesson_count, "n_unique_inputs": len(unique_lesson_inputs),
                                 "ambiguous": ambiguous, "hook_rejected": hook_rejected, "hook_missed": hook_missed}
        finally:
            bridge.shutdown()
    if args.phase == "final" and (report["lessons"]["ambiguous"] or report["lessons"]["hook_rejected"]):
        report["failures"].append({"type": "default_lesson_ambiguity"})
    report["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    report["passed"] = not report["failures"]
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "generator_sha256": source_hash,
                      "bbox_inversions": {b: r["bbox_strict_inversions"] for b,r in report["bands"].items()},
                      "lessons": lesson_count, "ambiguous": len(ambiguous), "hook_missed": len(hook_missed),
                      "racket_checked": report["racket_checked"], "seconds": report["elapsed_seconds"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
