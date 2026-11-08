#!/usr/bin/env python3
"""Source-bound lesson census for ARC generator 671a9af906aa.

The probe assembles the same kind of consecutive-index lessons shipped by the
runner, but uses the generator's fast Python mirror for a high-volume census.
Independent Racket battery stages remain the authority check.  Rival names are
read from the generator declarations rather than copied into this tool.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11
MIN_UNIQUE_INPUT_FRACTION = 0.95


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pair_hash(pair: dict[str, Any]) -> str:
    payload = json.dumps(
        [pair["input"], pair["output"]],
        separators=(",", ":"),
        sort_keys=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_generator(repo: Path, generator_path: Path):
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    name = "reviewed_671a9af906aa_probe"
    spec = importlib.util.spec_from_file_location(name, generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_record(repo: Path) -> dict[str, Any]:
    ledger = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "671a9af906aa":
            return row
    raise LookupError("canonical task 671a9af906aa not found")


def _all_test_pairs(record: dict[str, Any]) -> list[dict[str, Any]]:
    test = record.get("test", [])
    if isinstance(test, dict):
        return [test]
    return list(test)


def run_probe(
    *,
    repo: Path,
    generator_path: Path,
    lessons_per_band: int,
    seed_base: int,
) -> tuple[dict[str, Any], bool]:
    gen = _load_generator(repo, generator_path)
    generator_sha = _sha256(generator_path)
    canonical = _canonical_record(repo)
    n_demos = int(gen.EXAMPLES_NEEDED)
    n_queries = 1

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))

    canonical_train = list(canonical.get("train", []))
    canonical_test = _all_test_pairs(canonical)
    shortcut_report: dict[str, Any] = {}
    for name, shortcut in shortcuts.items():
        train_fits = all(
            shortcut(pair["input"]) == pair["output"]
            for pair in canonical_train
        )
        test_disagreements = sum(
            shortcut(pair["input"]) != pair["output"]
            for pair in canonical_test
        )
        shortcut_report[name] = {
            "canonical_train_fits": train_fits,
            "canonical_train_pairs": len(canonical_train),
            "canonical_test_disagreements": test_disagreements,
            "canonical_test_pairs": len(canonical_test),
        }

    input_hashes: set[str] = set()
    output_hashes: set[str] = set()
    pair_hashes: set[str] = set()
    mode_counts: Counter[str] = Counter()
    shape_counts: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    strict_hits = 0
    identity_pairs = 0
    identifiable_lessons = 0
    competitor_survivors: Counter[str] = Counter()
    competitor_pair_disagreements: Counter[str] = Counter()
    problems: list[dict[str, Any]] = []
    per_band: dict[str, Any] = {}

    total_lessons = 0
    total_pairs = 0
    for band_index, band in enumerate(BANDS):
        band_inputs: set[str] = set()
        band_outputs: set[str] = set()
        band_pairs: set[str] = set()
        band_modes: Counter[str] = Counter()
        band_shapes: Counter[str] = Counter()
        band_witnesses: Counter[str] = Counter()
        band_survivors: Counter[str] = Counter()
        band_identifiable = 0
        band_identity = 0
        band_strict = 0
        start_residues: Counter[str] = Counter()

        for lesson_index in range(lessons_per_band):
            total_lessons += 1
            seed = seed_base + band_index * 1_000_000 + lesson_index * 1009
            start = lesson_index * LESSON_STRIDE
            start_residues[str(start % len(getattr(gen, "_ROUTE_CYCLE", (0,))))] += 1
            pairs: list[dict[str, Any]] = []

            for offset in range(n_demos + n_queries):
                sample_index = start + offset
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    check = list(gen.self_check(grid, difficulty=band) or [])
                    if check:
                        raise ValueError("self_check: " + "; ".join(check))
                    output = gen.rule_mirror(grid)
                    pair = {"input": grid, "output": output}
                except Exception as exc:  # counted and replayable
                    problems.append({
                        "kind": "generation_error",
                        "band": band,
                        "lesson": lesson_index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    pairs = []
                    break

                total_pairs += 1
                ih, oh, ph = _grid_hash(grid), _grid_hash(output), _pair_hash(pair)
                input_hashes.add(ih)
                output_hashes.add(oh)
                pair_hashes.add(ph)
                band_inputs.add(ih)
                band_outputs.add(oh)
                band_pairs.add(ph)

                observed = gen.observe_overrides(grid)
                mode = str(observed["route_mode"])
                shape = f"{len(grid)}x{len(grid[0])}"
                mode_counts[mode] += 1
                shape_counts[shape] += 1
                band_modes[mode] += 1
                band_shapes[shape] += 1

                if not gen.strict_canonical_like(grid):
                    strict_hits += 1
                    band_strict += 1
                if grid == output:
                    identity_pairs += 1
                    band_identity += 1

                for witness_name, witness in witnesses.items():
                    if witness(grid):
                        witness_hits[witness_name] += 1
                        band_witnesses[witness_name] += 1
                for rival_name, rival in competitors.items():
                    if rival(grid) != output:
                        competitor_pair_disagreements[rival_name] += 1

                pairs.append(pair)

            if len(pairs) != n_demos + n_queries:
                continue

            demos = pairs[:n_demos]
            query = pairs[n_demos]
            reasons = list(gen.lesson_identifiable(demos, query) or [])
            surviving = [
                name
                for name, rival in competitors.items()
                if all(rival(pair["input"]) == pair["output"] for pair in demos)
            ]
            for name in surviving:
                competitor_survivors[name] += 1
                band_survivors[name] += 1

            if reasons or surviving:
                problems.append({
                    "kind": "unidentifiable_lesson",
                    "band": band,
                    "lesson": lesson_index,
                    "seed": seed,
                    "sample_index": start,
                    "reasons": reasons,
                    "survivors": surviving,
                })
            else:
                identifiable_lessons += 1
                band_identifiable += 1

        band_pair_count = lessons_per_band * (n_demos + n_queries)
        per_band[band] = {
            "lessons": lessons_per_band,
            "pairs": band_pair_count,
            "identifiable_lessons": band_identifiable,
            "unique_inputs": len(band_inputs),
            "unique_input_fraction": len(band_inputs) / band_pair_count if band_pair_count else 0.0,
            "unique_outputs": len(band_outputs),
            "unique_pairs": len(band_pairs),
            "strict_canonical_like_pairs": band_strict,
            "identity_pairs": band_identity,
            "route_mode_counts": dict(sorted(band_modes.items())),
            "shape_counts": dict(sorted(band_shapes.items())),
            "witness_hits": dict(sorted(band_witnesses.items())),
            "competitor_survivor_lessons": {
                name: band_survivors.get(name, 0) for name in sorted(competitors)
            },
            "lesson_start_residues_mod_cycle": dict(sorted(start_residues.items())),
        }

    report = {
        "schema": "arc-generator-lesson-probe-v1",
        "task_id": "671a9af906aa",
        "generator_path": str(generator_path),
        "generator_sha256": generator_sha,
        "generator_version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "oracle": (
            "generator.rule_mirror for the high-volume census; independent Racket "
            "battery rule_smoke/semantic_gate/authority_sync are required corroboration"
        ),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": n_demos,
            "queries_per_lesson": n_queries,
            "lesson_sample_index_stride": LESSON_STRIDE,
            "seed_formula": (
                "seed_base + band_index*1000000 + lesson_index*1009"
            ),
            "seed_base": seed_base,
            "pairs_are_consecutive_indices": True,
            "overrides": {},
        },
        "domain_limits": {
            "axes": getattr(gen, "AXES", {}),
            "profiles": list(getattr(gen, "SCHEDULE_PROFILES", ())),
            "claims": (
                "Sampled census only; it does not prove identifiability for arbitrary "
                "subsets, out-of-domain grids, or rival programs not declared by the generator."
            ),
        },
        "quality_thresholds": {
            "minimum_unique_input_fraction": MIN_UNIQUE_INPUT_FRACTION,
        },
        "canonical_shortcuts": shortcut_report,
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "totals": {
            "lessons": total_lessons,
            "pairs": total_pairs,
            "identifiable_lessons": identifiable_lessons,
            "unique_inputs": len(input_hashes),
            "unique_input_fraction": len(input_hashes) / total_pairs if total_pairs else 0.0,
            "unique_outputs": len(output_hashes),
            "unique_pairs": len(pair_hashes),
            "strict_canonical_like_pairs": strict_hits,
            "identity_pairs": identity_pairs,
        },
        "route_mode_counts": dict(sorted(mode_counts.items())),
        "shape_counts": dict(sorted(shape_counts.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "competitor_pair_disagreements": {
            name: competitor_pair_disagreements.get(name, 0)
            for name in sorted(competitors)
        },
        "competitor_survivor_lessons": {
            name: competitor_survivors.get(name, 0)
            for name in sorted(competitors)
        },
        "per_band": per_band,
        "problems": problems,
    }

    expected_lessons = lessons_per_band * len(BANDS)
    expected_pairs = expected_lessons * (n_demos + n_queries)
    ok = (
        not problems
        and identifiable_lessons == expected_lessons
        and total_pairs == expected_pairs
        and len(input_hashes) / expected_pairs >= MIN_UNIQUE_INPUT_FRACTION
        and all(value == 0 for value in competitor_survivors.values())
        and all(row["canonical_train_fits"] for row in shortcut_report.values())
    )
    report["passed"] = ok
    return report, ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=6710900)
    args = parser.parse_args()

    repo = args.repo.resolve()
    generator = args.generator.resolve()
    if args.lessons_per_band <= 0:
        parser.error("--lessons-per-band must be positive")
    report, ok = run_probe(
        repo=repo,
        generator_path=generator,
        lessons_per_band=args.lessons_per_band,
        seed_base=args.seed_base,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    totals = report["totals"]
    print(
        f"{report['task_id']}: {totals['identifiable_lessons']}/"
        f"{totals['lessons']} identifiable lessons, "
        f"{totals['unique_inputs']}/{totals['pairs']} unique inputs, "
        f"source={report['generator_sha256'][:16]}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
