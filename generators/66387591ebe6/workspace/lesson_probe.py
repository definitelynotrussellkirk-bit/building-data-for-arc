#!/usr/bin/env python3
"""Source-bound lesson census for ARC generator 66387591ebe6.

The probe mirrors the shared semantic gate's consecutive-index lesson shape and
11-step lesson-start stride, but scales to a configurable number of lessons per
band and records uniqueness, exact schedule coverage, witness firings, and
named-rival disagreements.  It uses the reviewed generator's Python mirror for
speed; the independent Racket battery remains the authority/parity check.

Key 1 is intentionally outside the ordinary sampler because it is a lawful
identity transformation and the generic rule-smoke gate only calibrates
identity when canonical training contains an identity pair.  This probe audits
that branch separately through exact overrides and records the limitation.
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


TASK_ID = "66387591ebe6"
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
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    module_name = f"reviewed_{TASK_ID}_{_sha256(generator_path)[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_record(repo: Path) -> dict[str, Any]:
    ledger = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise LookupError(f"canonical task {TASK_ID} not found")


def _as_pairs(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [pair for pair in value if isinstance(pair, dict)]
    return []


def _axis_signature(observed: dict[str, Any]) -> str:
    return "/".join(
        str(observed[name])
        for name in (
            "grid_h",
            "grid_w",
            "key",
            "n_cells",
            "pivot_region",
            "texture",
        )
    )


def _key_one_override_probe(gen: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rivals = dict(getattr(gen, "EXTRAPOLATION_RIVALS", {}))
    problems: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    regions = tuple(getattr(gen, "PIVOT_REGIONS", ("center",)))
    textures = tuple(getattr(gen, "TEXTURES", ("mono",)))

    for band_index, band in enumerate(BANDS):
        for index in range(12):
            kwargs = {
                "difficulty": band,
                "grid_h": (9, 11)[index % 2],
                "grid_w": (11, 9)[index % 2],
                "key": 1,
                "n_cells": (3, 4)[index % 2],
                "pivot_region": regions[index % len(regions)],
                "texture": textures[index % len(textures)],
            }
            seed = 910_000 + band_index * 10_000 + index * 97
            sample_index = 700 + index
            try:
                grid = gen.generate(seed, sample_index, **kwargs)
                errors = list(gen.self_check(grid, difficulty=band) or [])
                output = gen.rule_mirror(grid)
                observed = gen.observe_overrides(grid)
                rival_disagreements = {
                    name: rival(grid) != output for name, rival in rivals.items()
                }
            except Exception as exc:
                problems.append(
                    {
                        "kind": "key_one_override_exception",
                        "band": band,
                        "index": index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue

            row = {
                "band": band,
                "index": index,
                "seed": seed,
                "sample_index": sample_index,
                "self_check_errors": errors,
                "observed_key": observed.get("key"),
                "identity": output == grid,
                "rival_disagreements": rival_disagreements,
            }
            rows.append(row)
            if (
                errors
                or observed.get("key") != 1
                or output != grid
                or not rivals
                or not all(rival_disagreements.values())
            ):
                problems.append({"kind": "key_one_override_failure", **row})

    report = {
        "draws": len(rows),
        "bands": list(BANDS),
        "rivals": sorted(rivals),
        "identity_draws": sum(row["identity"] for row in rows),
        "exact_key_draws": sum(row["observed_key"] == 1 for row in rows),
        "per_rival_disagreements": {
            name: sum(row["rival_disagreements"].get(name, False) for row in rows)
            for name in sorted(rivals)
        },
        "passed": not problems and len(rows) == 12 * len(BANDS),
        "domain_note": (
            "Key 1 is a lawful exact-override identity branch, not part of the "
            "ordinary materialized curriculum because the generic rule-smoke "
            "identity calibration requires a canonical identity demonstration."
        ),
    }
    return report, problems


def run_probe(
    *,
    repo: Path,
    generator_path: Path,
    lessons_per_band: int,
    seed_base: int,
) -> tuple[dict[str, Any], bool]:
    if lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be positive")

    repo = repo.resolve()
    generator_path = generator_path.resolve()
    gen = _load_generator(repo, generator_path)
    generator_sha = _sha256(generator_path)
    canonical = _canonical_record(repo)
    canonical_pairs = [
        *_as_pairs(canonical.get("train")),
        *_as_pairs(canonical.get("test")),
    ]
    n_demos = int(gen.EXAMPLES_NEEDED)
    n_queries = 1

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))

    canonical_shortcuts: dict[str, Any] = {}
    for name, shortcut in shortcuts.items():
        canonical_shortcuts[name] = {
            "canonical_pairs": len(canonical_pairs),
            "canonical_pairs_fit": sum(
                shortcut(pair["input"]) == pair["output"]
                for pair in canonical_pairs
            ),
            "generated_pair_disagreements": 0,
        }

    input_hashes: set[str] = set()
    output_hashes: set[str] = set()
    pair_hashes: set[str] = set()
    axis_counts: dict[str, Counter[str]] = {
        name: Counter()
        for name in (
            "grid_h",
            "grid_w",
            "key",
            "n_cells",
            "pivot_region",
            "texture",
        )
    }
    axis_signatures: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    competitor_pair_disagreements: Counter[str] = Counter()
    competitor_survivors: Counter[str] = Counter()
    strict_hits = 0
    identity_pairs = 0
    identifiable_lessons = 0
    total_pairs = 0
    problems: list[dict[str, Any]] = []
    per_band: dict[str, Any] = {}

    for band_index, band in enumerate(BANDS):
        band_inputs: set[str] = set()
        band_outputs: set[str] = set()
        band_pairs: set[str] = set()
        band_witnesses: Counter[str] = Counter()
        band_pair_disagreements: Counter[str] = Counter()
        band_survivors: Counter[str] = Counter()
        band_axis_counts: dict[str, Counter[str]] = {
            name: Counter() for name in axis_counts
        }
        band_identifiable = 0
        band_identity = 0
        band_strict = 0
        start_residues: Counter[str] = Counter()

        for lesson_index in range(lessons_per_band):
            seed = seed_base + band_index * 1_000_000 + lesson_index * 1009
            start = lesson_index * LESSON_STRIDE
            start_residues[str(start % 4)] += 1
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
                    observed = dict(gen.observe_overrides(grid))
                except Exception as exc:
                    problems.append(
                        {
                            "kind": "generation_error",
                            "band": band,
                            "lesson": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    pairs = []
                    break

                total_pairs += 1
                ih = _grid_hash(grid)
                oh = _grid_hash(output)
                ph = _pair_hash(pair)
                input_hashes.add(ih)
                output_hashes.add(oh)
                pair_hashes.add(ph)
                band_inputs.add(ih)
                band_outputs.add(oh)
                band_pairs.add(ph)

                for name in axis_counts:
                    value = str(observed[name])
                    axis_counts[name][value] += 1
                    band_axis_counts[name][value] += 1
                axis_signatures[_axis_signature(observed)] += 1

                strict_reasons = list(gen.strict_canonical_like(grid) or [])
                if not strict_reasons:
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
                        band_pair_disagreements[rival_name] += 1
                for name, shortcut in shortcuts.items():
                    if shortcut(grid) != output:
                        canonical_shortcuts[name]["generated_pair_disagreements"] += 1

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
                problems.append(
                    {
                        "kind": "unidentifiable_lesson",
                        "band": band,
                        "lesson": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "reasons": reasons,
                        "survivors": surviving,
                    }
                )
            else:
                identifiable_lessons += 1
                band_identifiable += 1

        band_pair_count = lessons_per_band * (n_demos + n_queries)
        per_band[band] = {
            "lessons": lessons_per_band,
            "pairs": band_pair_count,
            "identifiable_lessons": band_identifiable,
            "unique_inputs": len(band_inputs),
            "unique_input_fraction": (
                len(band_inputs) / band_pair_count if band_pair_count else 0.0
            ),
            "unique_outputs": len(band_outputs),
            "unique_pairs": len(band_pairs),
            "strict_canonical_like_pairs": band_strict,
            "identity_pairs": band_identity,
            "axis_counts": {
                name: dict(sorted(counts.items()))
                for name, counts in band_axis_counts.items()
            },
            "witness_hits": {
                name: band_witnesses.get(name, 0) for name in sorted(witnesses)
            },
            "competitor_pair_disagreements": {
                name: band_pair_disagreements.get(name, 0)
                for name in sorted(competitors)
            },
            "competitor_survivor_lessons": {
                name: band_survivors.get(name, 0) for name in sorted(competitors)
            },
            "lesson_start_residues_mod_4": dict(sorted(start_residues.items())),
        }

    key_one_report, key_one_problems = _key_one_override_probe(gen)
    problems.extend(key_one_problems)

    expected_lessons = lessons_per_band * len(BANDS)
    expected_pairs = expected_lessons * (n_demos + n_queries)
    unique_fraction = len(input_hashes) / expected_pairs if expected_pairs else 0.0
    shortcut_checks_pass = all(
        row["canonical_pairs_fit"] == row["canonical_pairs"]
        and row["generated_pair_disagreements"] > 0
        for row in canonical_shortcuts.values()
    )
    witness_checks_pass = all(
        per_band[band]["witness_hits"].get(name, 0) > 0
        for band in BANDS
        for name in witnesses
    )
    rival_checks_pass = all(
        competitor_pair_disagreements.get(name, 0) > 0
        and competitor_survivors.get(name, 0) == 0
        for name in competitors
    )

    report = {
        "schema": "arc-generator-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": generator_sha,
        "generator_version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "oracle": (
            "generator.rule_mirror for high-volume census; independent Racket "
            "battery rule_smoke, semantic_gate, and authority_sync establish parity"
        ),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": n_demos,
            "queries_per_lesson": n_queries,
            "lesson_sample_index_stride": LESSON_STRIDE,
            "sample_indices": "start + offsets 0..EXAMPLES_NEEDED inclusive",
            "seed_formula": "seed_base + band_index*1000000 + lesson_index*1009",
            "seed_base": seed_base,
            "pairs_are_consecutive_indices": True,
            "overrides": {},
        },
        "domain_limits": {
            "axes": getattr(gen, "AXES", {}),
            "schedule_profiles": list(getattr(gen, "SCHEDULE_PROFILES", ())),
            "ordinary_keys": [2, 3, 4],
            "key_1": "exact override only; audited separately as lawful identity",
            "claim_limit": (
                "Sampled census only. It does not prove identifiability for "
                "arbitrary subsets, out-of-domain grids, or undeclared programs."
            ),
        },
        "quality_thresholds": {
            "minimum_unique_input_fraction": MIN_UNIQUE_INPUT_FRACTION,
        },
        "canonical_shortcuts": canonical_shortcuts,
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "totals": {
            "lessons": expected_lessons,
            "pairs": total_pairs,
            "identifiable_lessons": identifiable_lessons,
            "unique_inputs": len(input_hashes),
            "unique_input_fraction": unique_fraction,
            "unique_outputs": len(output_hashes),
            "unique_pairs": len(pair_hashes),
            "strict_canonical_like_pairs": strict_hits,
            "identity_pairs": identity_pairs,
        },
        "axis_counts": {
            name: dict(sorted(counts.items())) for name, counts in axis_counts.items()
        },
        "axis_signature_count": len(axis_signatures),
        "witness_hits": {
            name: witness_hits.get(name, 0) for name in sorted(witnesses)
        },
        "competitor_pair_disagreements": {
            name: competitor_pair_disagreements.get(name, 0)
            for name in sorted(competitors)
        },
        "competitor_survivor_lessons": {
            name: competitor_survivors.get(name, 0)
            for name in sorted(competitors)
        },
        "key_one_override_probe": key_one_report,
        "per_band": per_band,
        "problems": problems,
    }

    passed = (
        not problems
        and total_pairs == expected_pairs
        and identifiable_lessons == expected_lessons
        and unique_fraction >= MIN_UNIQUE_INPUT_FRACTION
        and strict_hits == expected_pairs
        and identity_pairs == 0
        and witness_checks_pass
        and rival_checks_pass
        and shortcut_checks_pass
        and key_one_report["passed"]
    )
    report["passed"] = passed
    return report, passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=663_875_910)
    args = parser.parse_args()

    report, passed = run_probe(
        repo=args.repo,
        generator_path=args.generator,
        lessons_per_band=args.lessons_per_band,
        seed_base=args.seed_base,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    totals = report["totals"]
    print(
        f"{TASK_ID}: {totals['identifiable_lessons']}/{totals['lessons']} "
        f"identifiable lessons; {totals['unique_inputs']}/{totals['pairs']} "
        f"unique inputs; identity={totals['identity_pairs']}; "
        f"source={report['generator_sha256'][:16]}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
