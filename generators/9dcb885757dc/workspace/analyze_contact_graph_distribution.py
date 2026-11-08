#!/usr/bin/env python3
"""Measure semantic coverage and shortcut survival for generator 9dcb885757dc.

This is intentionally task-linked. Generic diversity probes can report many
unique grids while every output still collapses to the same rule branch. This
script asks the questions that mattered in this review:

* Which declared contact-graph profiles and component styles were generated?
* Which object-degree branches 0..5 were exercised?
* How often would each named shortcut produce the authoritative answer?
* Do canonical inputs and generated inputs pass the same structural contract?

Run from anywhere:

    python3 workspace/analyze_contact_graph_distribution.py --samples-per-band 20

Use ``--json-out`` to retain a machine-readable report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any


SCRIPT = Path(__file__).resolve()
GENERATOR_DIR = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
CANONICAL = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")


def _load_generator() -> ModuleType:
    sys.path.insert(0, str(RUNTIME))
    path = GENERATOR_DIR / "generator.py"
    name = "contact_graph_distribution_subject"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _band_seed(task_id: str, band: str, base_seed: int) -> int:
    digest = hashlib.sha256(f"{task_id}|{band}|{base_seed}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _canonical_inputs(task_id: str) -> list[list[list[int]]]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return [
                    pair["input"]
                    for pair in list(row.get("train", [])) + list(row.get("test", []))
                ]
    raise RuntimeError(f"canonical task {task_id} not found in {CANONICAL}")


def _counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _empty_stats(shortcut_names: list[str]) -> dict[str, Any]:
    return {
        "draws": 0,
        "invalid_draws": 0,
        "invalid_examples": [],
        "profiles": Counter(),
        "styles": Counter(),
        "degree_multisets": Counter(),
        "output_class_sets": Counter(),
        "degrees_seen": set(),
        "shortcut_matches": Counter({name: 0 for name in shortcut_names}),
    }


def _add_draw(stats: dict[str, Any], gen: ModuleType, grid: list[list[int]], replay: str) -> None:
    stats["draws"] += 1
    errors = gen.self_check(grid)
    if errors:
        stats["invalid_draws"] += 1
        if len(stats["invalid_examples"]) < 3:
            stats["invalid_examples"].append({"replay": replay, "errors": errors[:3]})
        return

    facts = gen.semantic_observables(grid)
    stats["profiles"][facts["scene_profile"]] += 1
    stats["styles"][facts["component_style"]] += 1
    stats["degree_multisets"][tuple(facts["degree_multiset"])] += 1
    stats["output_class_sets"][tuple(facts["output_classes"])] += 1
    stats["degrees_seen"].update(facts["degrees"])

    expected = gen.rule_mirror(grid)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        if rival(grid) == expected:
            stats["shortcut_matches"][name] += 1


def _finalize(stats: dict[str, Any], shortcut_names: list[str]) -> dict[str, Any]:
    draws = stats["draws"]
    return {
        "draws": draws,
        "invalid_draws": stats["invalid_draws"],
        "invalid_examples": stats["invalid_examples"],
        "profiles": _counter(stats["profiles"]),
        "styles": _counter(stats["styles"]),
        "degree_multisets": _counter(stats["degree_multisets"]),
        "output_class_sets": _counter(stats["output_class_sets"]),
        "degrees_seen": sorted(stats["degrees_seen"]),
        "shortcut_survival": {
            name: (stats["shortcut_matches"][name] / draws if draws else 0.0)
            for name in shortcut_names
        },
        "shortcut_match_counts": {
            name: stats["shortcut_matches"][name] for name in shortcut_names
        },
    }


def analyze(samples_per_band: int, base_seed: int) -> dict[str, Any]:
    if samples_per_band <= 0:
        raise ValueError("samples_per_band must be positive")
    gen = _load_generator()
    shortcut_names = sorted(gen.SEMANTIC_RIVALS)
    pooled = _empty_stats(shortcut_names)
    per_band: dict[str, Any] = {}

    for band in BANDS:
        raw = _empty_stats(shortcut_names)
        seed = _band_seed(gen.TASK_ID, band, base_seed)
        for sample_index in range(samples_per_band):
            grid = gen.generate(seed, sample_index, difficulty=band)
            replay = f"band={band},seed={seed},sample_index={sample_index}"
            _add_draw(raw, gen, grid, replay)
            _add_draw(pooled, gen, grid, replay)
        per_band[band] = _finalize(raw, shortcut_names)

    canonical_rows: list[dict[str, Any]] = []
    for index, grid in enumerate(_canonical_inputs(gen.TASK_ID)):
        errors = gen.self_check(grid)
        facts = gen.semantic_observables(grid) if not errors else None
        canonical_rows.append(
            {
                "index": index,
                "accepted": not errors,
                "errors": errors,
                "profile": None if facts is None else facts["scene_profile"],
                "degree_multiset": None if facts is None else list(facts["degree_multiset"]),
                "dimensions": [len(grid), len(grid[0])],
            }
        )

    return {
        "schema": "contact-graph-distribution-analysis/1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "samples_per_band": samples_per_band,
        "base_seed": base_seed,
        "canonical": canonical_rows,
        "per_band": per_band,
        "pooled": _finalize(pooled, shortcut_names),
    }


def _print_report(report: dict[str, Any]) -> None:
    pooled = report["pooled"]
    print(
        f"{report['task_id']} v{report['generator_version']}: "
        f"{pooled['draws']} draws, {pooled['invalid_draws']} invalid"
    )
    print("degree coverage: " + ",".join(str(value) for value in pooled["degrees_seen"]))
    print("profiles: " + json.dumps(pooled["profiles"], sort_keys=True))
    print("styles: " + json.dumps(pooled["styles"], sort_keys=True))
    print("shortcut survival (lower is better):")
    for name, rate in sorted(pooled["shortcut_survival"].items()):
        matches = pooled["shortcut_match_counts"][name]
        print(f"  {name}: {matches}/{pooled['draws']} ({rate:.1%})")
    rejected = [row for row in report["canonical"] if not row["accepted"]]
    print(f"canonical accepted: {len(report['canonical']) - len(rejected)}/{len(report['canonical'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=20)
    parser.add_argument("--base-seed", type=int, default=0)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--allow-missing-degree-branches",
        action="store_true",
        help="report missing branches without returning a failing exit code",
    )
    args = parser.parse_args(argv)

    report = analyze(args.samples_per_band, args.base_seed)
    _print_report(report)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    expected_degrees = set(range(6))
    seen = set(report["pooled"]["degrees_seen"])
    canonical_rejected = any(not row["accepted"] for row in report["canonical"])
    invalid = report["pooled"]["invalid_draws"] > 0
    missing = expected_degrees - seen
    if invalid or canonical_rejected:
        return 2
    if missing and not args.allow_missing_degree_branches:
        print(f"ERROR: missing degree branches {sorted(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
