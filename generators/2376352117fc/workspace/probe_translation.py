"""Reproducible branch/shortcut/Racket probe for source OR relocated runtime.

Run from the repository:
 python generators/2376352117fc/workspace/probe_translation.py --root . \
     --out ../checks/probe_final --seeds 128 --racket
A --generator PATH permits before/after comparison without modifying authority.
Outputs include exact seeds, hashes, denominator, full counterexample grids,
all per-sample records, and all failures. No training labels are written.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

TASK = "2376352117fc"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def positions(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}


def geometry(grid):
    p1, p2 = next(iter(positions(grid, 1))), next(iter(positions(grid, 2)))
    dr, dc = p2[0] - p1[0], p2[1] - p1[1]
    source = positions(grid, 3)
    targets = {(r + dr, c + dc) for r, c in source
               if 0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])}
    return dr, dc, source, targets


def output_and_rivals(grid):
    _, _, source, targets = geometry(grid)
    out = [[0] * len(grid[0]) for _ in grid]
    for r, c in targets:
        out[r][c] = 8
    rivals = {
        "all_or_nothing": out if len(targets) == len(source) else [[0] * len(grid[0]) for _ in grid],
        "background_only": [[8 if (r, c) in targets and v == 0 else 0
                              for c, v in enumerate(row)] for r, row in enumerate(grid)],
    }
    return out, rivals


def normalize(cells):
    rmin, cmin = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - rmin, c - cmin) for r, c in cells))


def dihedral(cells):
    variants = []
    for swap in (False, True):
        for sr in (-1, 1):
            for sc in (-1, 1):
                variants.append(normalize({(sr * (c if swap else r), sc * (r if swap else c)) for r, c in cells}))
    return min(variants)


def describe(grid):
    dr, dc, source, targets = geometry(grid)
    contact = any(grid[r][c] != 0 for r, c in targets)
    visibility = "empty" if not targets else "full" if len(targets) == len(source) else "partial"
    return {
        "shape": [len(grid), len(grid[0])], "motif_size": len(source),
        "vector": [dr, dc], "direction": [(dr > 0) - (dr < 0), (dc > 0) - (dc < 0)],
        "texture": visibility if visibility == "empty" else visibility + ("_overlap" if contact else "_clear"),
        "visible_cells": len(targets), "source_overlap": len(targets & source),
        "blue_overlap": len(targets & positions(grid, 1)), "red_overlap": len(targets & positions(grid, 2)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--expect-improved", action="store_true")
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    root = args.root.resolve()
    source_layout = (root / "shared/runtime").is_dir()
    runtime = root / "shared/runtime" if source_layout else root
    canonical = root / "shared/data/canonical/puzzles.jsonl" if source_layout else root / "data/canonical/puzzles.jsonl"
    gp = (args.generator.resolve() if args.generator else
          root / (f"generators/{TASK}/generator.py" if source_layout else f"puzzle_generators/per_puzzle/{TASK}/generator.py"))
    runtime_temp = None
    if args.racket and source_layout:
        # Rule wrapping imports scripts.*, which exists only in the public
        # portable runtime. Use the supported copy operation, never an alias
        # into an unrelated checkout or a duplicate normalization routine.
        sys.path.insert(0, str(root / "src"))
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime
        runtime_temp = tempfile.TemporaryDirectory(prefix="translation-probe-")
        runtime = Path(runtime_temp.name)
        prepare_runtime(Catalog(root), runtime, TASK)
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("translation_probe_generator", gp)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    task = next(json.loads(line) for line in canonical.open() if json.loads(line).get("task_id") == TASK)
    rule = task["program_solution"]
    args.out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "translation-probe-v1", "task_id": TASK,
        "generator_sha256": hashlib.sha256(gp.read_bytes()).hexdigest(),
        "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "layout": "source" if source_layout else "relocated_runtime",
        "runtime_root": str(runtime), "generator_path": str(gp),
        "cohort": {"seeds": [0, args.seeds - 1], "sample_indices": [0, 7],
                   "bands": ["easy", "medium", "hard"], "requested": args.seeds * 8 * 3},
        "canonical": [], "failures": [], "racket_checked": 0, "racket_mismatches": 0,
    }
    b = None
    application = None
    if args.racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        wrapped = wrap_rule(rule)
        def application(grid):
            text = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            return f"({wrapped} '{text})"
        b = RacketBridge(max_calls_before_restart=512)
    counts = {key: Counter() for key in ("texture", "direction", "shape", "motif_size", "rival_disagreement")}
    unique_in, unique_out, unique_shapes, unique_dihedral = set(), set(), set(), set()
    witnesses = {}
    timings = []
    try:
        for i, pair in enumerate([*task["train"], *task["test"]]):
            expected, rivals = output_and_rivals(pair["input"])
            actual = b.eval_text(application(pair["input"])) if b else expected
            report["racket_checked"] += int(b is not None)
            ok = actual == expected == pair["output"]
            report["canonical"].append({"index": i, "output_match": ok,
                "self_check": gen.self_check(pair["input"]),
                "rivals_fit": {name: output == pair["output"] for name, output in rivals.items()}})
            if not ok:
                report["failures"].append({"canonical_index": i, "pair": pair, "actual": actual, "expected": expected})
        with (args.out / "samples.jsonl").open("w") as samples:
            for band in ("easy", "medium", "hard"):
                for seed in range(args.seeds):
                    for index in range(8):
                        entry = {"band": band, "seed": seed, "sample_index": index}
                        grid = None
                        try:
                            t = time.perf_counter()
                            grid = gen.generate(seed, index, difficulty=band)
                            timings.append(1000 * (time.perf_counter() - t))
                            if grid != gen.generate(seed, index, difficulty=band):
                                raise AssertionError("replay mismatch")
                            errors = gen.self_check(grid)
                            if errors:
                                raise AssertionError(f"self_check: {errors}")
                            expected, rivals = output_and_rivals(grid)
                            actual = b.eval_text(application(grid)) if b else expected
                            report["racket_checked"] += int(b is not None)
                            if actual != expected:
                                report["racket_mismatches"] += 1
                                raise AssertionError("Racket/Python mismatch")
                            if hasattr(gen, "rule_mirror") and gen.rule_mirror(grid) != actual:
                                raise AssertionError("declared mirror mismatch")
                            description = describe(grid)
                            entry.update(description)
                            entry.update(input_sha256=digest(grid), output_sha256=digest(actual))
                            source = positions(grid, 3)
                            unique_in.add(entry["input_sha256"])
                            unique_out.add(entry["output_sha256"])
                            unique_shapes.add(normalize(source))
                            unique_dihedral.add(dihedral(source))
                            for key in ("texture", "direction", "shape", "motif_size"):
                                counts[key][json.dumps(description[key])] += 1
                            for name, rival_output in rivals.items():
                                if rival_output != actual:
                                    counts["rival_disagreement"][name] += 1
                                    if name not in witnesses:
                                        witnesses[name] = {**entry, "input": grid, "expected": actual,
                                            "rival_output": rival_output, "checked_by": "Racket" if b else "Python only"}
                        except Exception as exc:
                            report["failures"].append({**entry, "input": grid, "error": f"{type(exc).__name__}: {exc}"})
                            entry["error"] = str(exc)
                        samples.write(json.dumps(entry, separators=(",", ":")) + "\n")
    finally:
        if b:
            b.close()
        if runtime_temp:
            runtime_temp.cleanup()
    report.update(successful=report["cohort"]["requested"] - sum("seed" in failure for failure in report["failures"]),
                  unique_inputs=len(unique_in), unique_outputs=len(unique_out),
                  translated_motif_shapes=len(unique_shapes), dihedral_motif_shapes=len(unique_dihedral),
                  counts={key: dict(value) for key, value in counts.items()}, witnesses=list(witnesses))
    if timings:
        timings.sort()
        report["generation_ms"] = {"median": timings[len(timings) // 2], "p95": timings[int(.95 * (len(timings) - 1))], "max": max(timings)}
    report["samples_sha256"] = hashlib.sha256((args.out / "samples.jsonl").read_bytes()).hexdigest()
    improved_errors = []
    if args.expect_improved:
        if any(row["self_check"] for row in report["canonical"]):
            improved_errors.append("canonical input rejected")
        if set(witnesses) != {"all_or_nothing", "background_only"}:
            improved_errors.append("a canonical-fitting shortcut has no generated counterexample")
        if len(counts["direction"]) != 8 or len(counts["texture"]) != 5:
            improved_errors.append("direction/texture branch missing")
    report["improved_contract_errors"] = improved_errors
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "witnesses.json").write_text(json.dumps(witnesses, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "cohort", "successful", "unique_inputs", "unique_outputs", "racket_checked", "racket_mismatches", "counts", "generation_ms", "improved_contract_errors")}, indent=2))
    return 1 if report["failures"] or improved_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
