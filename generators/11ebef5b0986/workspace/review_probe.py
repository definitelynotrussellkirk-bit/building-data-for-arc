"""Source-bound finite-rival census using real Racket outputs.

Run from the packet root; no mutable globals, labels or canonical examples are
used by the generator. Supports any per-puzzle task exposing SEMANTIC_RIVALS.
For a baseline comparison, --generator may select the frozen old generator and
--rivals-from may select the reviewed module. Both hashes are retained.
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


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(value):
    return sha(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def norm(grid):
    return [[int(v) for v in row] for row in grid]


def canonical_pairs(value):
    """The ledger uses either a list of pairs or a single test-pair dict."""
    pairs = [value] if isinstance(value, dict) else value
    if not isinstance(pairs, list) or any(
            not isinstance(pair, dict) or not {"input", "output"} <= pair.keys()
            for pair in pairs):
        raise ValueError("canonical authoring pairs must contain input and output")
    return pairs


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run(args, runtime):
    repo = args.repo.resolve()
    sys.path.insert(0, str(runtime))
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    gp = (args.generator or repo / f"generators/{args.task_id}/generator.py").resolve()
    rp = (args.rivals_from or gp).resolve()
    gen = load_module(gp, "census_generator")
    rivals_module = load_module(rp, "census_rivals")
    rivals = getattr(rivals_module, "SEMANTIC_RIVALS", {})
    if not isinstance(rivals, dict) or not all(callable(fn) for fn in rivals.values()):
        raise ValueError("SEMANTIC_RIVALS must map names to callables")
    canon_path = repo / "shared/data/canonical/puzzles.jsonl"
    records = [json.loads(line) for line in canon_path.open()]
    task = [d for d in records if d.get("task_id") == args.task_id]
    if len(task) != 1:
        raise ValueError("expected one unambiguous canonical task")
    task = task[0]
    rule = task["program_solution"]
    report = {
        "schema": "source-bound-rival-census-v1", "task_id": args.task_id,
        "phase": args.phase, "runtime_directory": str(runtime), "generator_sha256": sha(gp.read_bytes()),
        "rivals_sha256": sha(rp.read_bytes()), "rule_sha256": sha(rule.encode()),
        "canonical_ledger_sha256": sha(canon_path.read_bytes()),
        "command": {"cwd": "repo" if Path.cwd().resolve() == repo else "packet_root",
                    "argv": ["python3", *sys.argv], "racket_via": "run_with_racket.py"},
        "sample_domain": {"bands": args.bands, "seed_range_inclusive": [0, args.seeds - 1],
                          "sample_index_range_inclusive": [0, args.samples - 1],
                          "overrides": {}},
        "canonical": [], "counts": {}, "per_band": {}, "failures": [],
        "counterexamples": {}, "manifest": [],
    }
    counts = Counter()
    inputs, outputs = set(), set()
    shapes, palette_colors, longest_rays = Counter(), Counter(), Counter()
    bridge = RacketBridge(timeout=20)
    wrapped = wrap_rule(rule)
    def actual(grid):
        result = bridge.eval_text(f"({wrapped} {literal(grid)})")
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(str(result))
        return result
    try:
        for split in ("train", "test"):
            for index, pair in enumerate(canonical_pairs(task.get(split, []))):
                grid, expected = norm(pair["input"]), norm(pair["output"])
                output = actual(grid)
                entry = {"split": split, "index": index, "racket_matches_stored": output == expected,
                         "rival_matches": {name: fn(grid) == expected for name, fn in rivals.items()}}
                report["canonical"].append(entry)
                if output != expected:
                    report["failures"].append({"kind": "canonical_mismatch", **entry})
        for band in args.bands:
            band_counts = Counter()
            for seed in range(args.seeds):
                records_for_seed = []
                for index in range(args.samples):
                    loc = {"difficulty": band, "seed": seed, "sample_index": index, "overrides": {}}
                    try:
                        grid = gen.generate(seed, index, difficulty=band)
                        errors = gen.self_check(grid)
                        if errors:
                            report["failures"].append({"kind": "self_check", **loc, "errors": errors, "input": grid})
                        output = actual(grid)
                        if hasattr(rivals_module, "rule_mirror") and rivals_module.rule_mirror(grid) != output:
                            report["failures"].append({"kind": "mirror_mismatch", **loc, "input": grid, "racket_output": output})
                        ih, oh = fingerprint(grid), fingerprint(output)
                        inputs.add(ih); outputs.add(oh)
                        counts["draws"] += 1; band_counts["draws"] += 1
                        counts["valid"] += not bool(errors)
                        counts["nonidentity"] += grid != output
                        colors = set(v for row in grid for v in row)
                        if 5 in grid[0]:
                            counts["gray_legend"] += 1; band_counts["gray_legend"] += 1
                        for color in colors:
                            palette_colors[str(color)] += 1
                        shapes[f"{len(grid)}x{len(grid[0])}"] += 1
                        seeds = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 9]
                        if len(seeds) == 1:
                            sr, sc = seeds[0]
                            painted = [max(abs(r-sr), abs(c-sc)) for r,row in enumerate(grid)
                                       for c,v in enumerate(row) if v != output[r][c]]
                            longest_rays[str(max(painted, default=0))] += 1
                        killed = {}
                        for name, fn in rivals.items():
                            rival = fn(grid)
                            killed[name] = rival != output
                            counts[f"refutes:{name}"] += killed[name]
                            band_counts[f"refutes:{name}"] += killed[name]
                            if killed[name] and name not in report["counterexamples"]:
                                report["counterexamples"][name] = {
                                    "task_id": args.task_id, "generator_sha256": report["generator_sha256"],
                                    "rule_sha256": report["rule_sha256"], **loc,
                                    "input": grid, "racket_output": output, "rival_output": rival,
                                    "validator_errors": errors, "in_documented_generator_domain": not bool(errors),
                                    "command": report["command"],
                                    "different_cells": [[r,c,output[r][c],rival[r][c]]
                                                       for r,row in enumerate(output) for c,v in enumerate(row)
                                                       if v != rival[r][c]]}
                        record = {**loc, "input_sha256": ih, "output_sha256": oh, "rival_refuted": killed}
                        report["manifest"].append(record); records_for_seed.append(record)
                    except Exception as exc:
                        report["failures"].append({"kind": "execution", **loc, "type": type(exc).__name__, "message": str(exc)})
                        records_for_seed.append(None)
                # These windows overlap: report them separately from unique grids.
                for start in range(max(0, args.samples - args.demos + 1)):
                    window = records_for_seed[start:start+args.demos]
                    if any(r is None for r in window):
                        counts["blocked_windows"] += 1
                        continue
                    counts["overlapping_demo_windows"] += 1
                    for name in rivals:
                        if any(r["rival_refuted"][name] for r in window):
                            counts[f"windows_refute:{name}"] += 1
            report["per_band"][band] = dict(band_counts)
    finally:
        bridge.close()
    report["counts"] = {**dict(counts), "unique_inputs": len(inputs), "unique_outputs": len(outputs)}
    report["shape_histogram"] = dict(sorted(shapes.items()))
    report["color_presence_histogram"] = dict(sorted(palette_colors.items()))
    report["max_painted_distance_histogram"] = dict(sorted(longest_rays.items(), key=lambda kv:int(kv[0])))
    report["finite_rival_scope"] = sorted(rivals)
    report["window_size"] = args.demos
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"path": str(args.out), "phase": args.phase, "counts": report["counts"],
                      "failures": len(report["failures"])}, indent=2))
    return 1 if report["failures"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("repo"))
    parser.add_argument("--task-id", default="11ebef5b0986")
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--rivals-from", type=Path)
    parser.add_argument("--phase", required=True, choices=("before", "intermediate", "final"))
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--samples", type=int, default=15)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--bands", nargs="+", default=["easy", "medium", "hard"])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if min(args.seeds, args.samples, args.demos) < 1:
        parser.error("seeds, samples, demos must be positive")
    if any(b not in ("easy", "medium", "hard") for b in args.bands):
        parser.error("unknown difficulty band")
    sys.path.insert(0, str(args.repo.resolve() / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix="arc-rival-census-") as directory:
        runtime = Path(directory)
        prepare_runtime(Catalog(args.repo.resolve()), runtime, args.task_id)
        return run(args, runtime)


if __name__ == "__main__":
    raise SystemExit(main())
