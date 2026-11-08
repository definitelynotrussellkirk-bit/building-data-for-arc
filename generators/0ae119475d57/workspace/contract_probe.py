#!/usr/bin/env python3
"""Cross the *declared* width domain with all bands, not only default draws.

Run from the packet root (Racket is optional unless --racket-per-stratum > 0):
  python3 run_with_racket.py python3 generators/0ae119475d57/workspace/contract_probe.py \
      --seeds 200 --racket-per-stratum 10 --out ../checks/contract-final.json

--generator can select the immutable baseline snapshot for an A/B comparison.
Failures retain exact inputs, seeds, overrides and hashes. This is an authoring
probe, never a model-visible solve tool. It does not certify training quality.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time
import tempfile
from typing import Any

TASK_ID = "0ae119475d57"
BANDS = ("easy", "medium", "hard")
WIDTHS = (None, *range(4, 17))


def structural_issues(grid: Any) -> list[str]:
    """Independent unique-separator check; do not just trust the generator hook."""
    if not isinstance(grid, list) or len(grid) != 11:
        return ["expected eleven rows"]
    if not isinstance(grid[0], list) or not 4 <= len(grid[0]) <= 16:
        return ["expected width in 4..16"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["expected rectangular rows"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["expected integer ARC colors"]
    full = [r for r, row in enumerate(grid) if row[0] != 0 and len(set(row)) == 1]
    return [] if full == [5] else [f"expected unique separator at row 5, found {full}"]


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("contract_probe_generator", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot import generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--racket-per-stratum", type=int, default=0)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1 or not 0 <= args.racket_per_stratum <= args.seeds:
        parser.error("need seeds >= 1 and 0 <= racket-per-stratum <= seeds")
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    library = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(library / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-contract-") as directory:
        runtime = Path(directory)
        prepare_runtime(Catalog(library), runtime, TASK_ID)
        return run_probe(args, library, runtime)


def run_probe(args, library: Path, runtime: Path) -> int:
    source = (args.generator or library / "generators" / TASK_ID / "generator.py").resolve()
    sys.path.insert(0, str(runtime))
    module = load_generator(source)
    canon_path = library / "shared/data/canonical/puzzles.jsonl"
    with canon_path.open() as handle:
        canonical = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK_ID)
    rule = canonical["program_solution"]
    report = {
        "schema": "0ae119475d57-contract-probe-v1", "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_ledger_sha256": hashlib.sha256(canon_path.read_bytes()).hexdigest(),
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "runtime_directory": str(runtime),
        "runtime_manifest_sha256": hashlib.sha256((runtime / "RUNTIME_MANIFEST.json").read_bytes()).hexdigest(),
        "seed_range_inclusive": [0, args.seeds - 1], "sample_index": "seed % 4",
        "strata": {}, "failures": [], "reference_pairs": [],
        "reference_requested_per_stratum": args.racket_per_stratum,
        "note": "Observations can repeat across default and explicit-width strata; unique inputs are counted separately.",
    }
    bridge = None
    if args.racket_per_stratum:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        wrapped = wrap_rule(rule)
        bridge = RacketBridge(max_calls_before_restart=64)
    unique = set()
    rng_before = random.getstate()
    started = time.monotonic()
    try:
        for band in BANDS:
            for width in WIDTHS:
                key = f"{band}:{'default' if width is None else width}"
                counts = Counter(observations=0, failed_observations=0, reference_checked=0,
                                 reference_failed=0, replay_checked=0)
                colors = Counter()
                strata_unique = set()
                for seed in range(args.seeds):
                    index = seed % 4
                    overrides = {} if width is None else {"grid_w": width}
                    record = dict(seed=seed, sample_index=index, difficulty=band, overrides=overrides)
                    counts["observations"] += 1
                    try:
                        grid = module.generate(seed, index, difficulty=band, **overrides)
                        record["input"] = grid
                        key_hash = digest(grid)
                        unique.add(key_hash)
                        strata_unique.add(key_hash)
                        issues = structural_issues(grid)
                        issues += module.self_check(grid) + module.strict_canonical_like(grid)
                        for name, predicate in module.SEMANTIC_WITNESSES.items():
                            if not predicate(grid):
                                issues.append(f"missing witness: {name}")
                        observed = module._analyze(grid)
                        target = module._branch_targets(5 * len(grid[0]), module._SCENE_PROFILES[index], band)
                        if observed.get("branch_counts") != target:
                            issues.append("branch counts changed from the requested density profile")
                        if observed.get("top_color") is not None and observed.get("bot_color") is not None:
                            colors["top_gt_bottom" if observed["top_color"] > observed["bot_color"] else "top_lt_bottom"] += 1
                        if seed < 4:
                            counts["replay_checked"] += 1
                            replay = module.generate(seed, index, difficulty=band, **overrides)
                            if replay != grid:
                                issues.append("deterministic replay differed")
                        if bridge is not None and seed < args.racket_per_stratum:
                            counts["reference_checked"] += 1
                            rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
                            actual = bridge.eval_text(f"({wrapped} '({rows}))")
                            expected = module.rule_mirror(grid)
                            equal = actual == expected
                            counts["reference_failed"] += not equal
                            report["reference_pairs"].append({**record, "racket_output": actual,
                                                             "mirror_output": expected, "matched": equal})
                            if not equal:
                                issues.append("canonical Racket/mirror mismatch")
                        if issues:
                            record["reasons"] = list(dict.fromkeys(issues))
                            report["failures"].append(record)
                            counts["failed_observations"] += 1
                    except Exception as exc:
                        # Fail visibly, retain this exact draw, and continue the census.
                        record["error"] = f"{type(exc).__name__}: {exc}"
                        report["failures"].append(record)
                        counts["failed_observations"] += 1
                report["strata"][key] = dict(counts, unique_inputs=len(strata_unique), palette_order=dict(colors))
    finally:
        if bridge is not None:
            bridge.close()
    report["global_rng_unchanged"] = random.getstate() == rng_before
    report["observations"] = sum(row["observations"] for row in report["strata"].values())
    report["unique_inputs"] = len(unique)
    report["failed_observations"] = len(report["failures"])
    report["reference_checked"] = len(report["reference_pairs"])
    report["reference_failed"] = sum(not row["matched"] for row in report["reference_pairs"])
    report["duration_seconds"] = time.monotonic() - started
    report["passed"] = not report["failures"] and report["global_rng_unchanged"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("passed", "observations", "unique_inputs",
                                                  "failed_observations", "reference_checked", "reference_failed",
                                                  "generator_sha256", "duration_seconds")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
