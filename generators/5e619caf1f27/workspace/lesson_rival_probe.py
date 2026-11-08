#!/usr/bin/env python3
"""Source-bound lesson census for canonical-fitting shortcut rules.

The sampler intentionally matches the semantic-gate pinned lesson plan but
extends it to 100 lessons per difficulty band.  It uses the generator's
``rule_mirror`` for throughput; the normal battery remains responsible for
checking that mirror against the canonical Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

TASK_ID = "5e619caf1f27"
HERE = Path(__file__).resolve()
TASK_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")
LESSONS_PER_BAND = 100

sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))
SPEC = importlib.util.spec_from_file_location(
    f"task_{TASK_ID}_lesson_rival_probe", GENERATOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_sha(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    return _sha256_bytes(payload)


def _normalize_grid(grid: Any) -> list[list[int]]:
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [[int(value) for value in row] for row in grid]


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = []
            for pair in list(row.get("train") or []) + list(row.get("test") or []):
                pairs.append(
                    {
                        "input": _normalize_grid(pair["input"]),
                        "output": _normalize_grid(pair["output"]),
                    }
                )
            return pairs
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _lesson_seed(band: str, k: int) -> int:
    text = f"profile-floor:v1:{TASK_ID}:lesson:{band}:{k}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)


def _episode(seed: int, start: int, band: str):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=band)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_index = start + GEN.EXAMPLES_NEEDED
    query_grid = GEN.generate(seed, query_index, difficulty=band)
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    return demos, query


def _pair_record(
    pair: dict[str, Any], rival: Callable[[Any], list[list[int]]]
) -> dict[str, Any]:
    rival_output = rival(pair["input"])
    return {
        "input": pair["input"],
        "authority_output": pair["output"],
        "rival_output": rival_output,
        "input_sha256": _grid_sha(pair["input"]),
        "authority_output_sha256": _grid_sha(pair["output"]),
        "rival_output_sha256": _grid_sha(rival_output),
        "observables": GEN.semantic_observables(pair["input"]),
    }


def _canonical_report(
    pairs: list[dict[str, Any]], rivals: dict[str, Callable[[Any], list[list[int]]]]
):
    report = {}
    for name, rival in rivals.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in pairs]
        report[name] = {
            "fit_count": sum(fits),
            "pair_count": len(pairs),
            "fits_all": all(fits),
            "pair_fits": fits,
        }
    return report


def _band_report(
    band: str,
    rivals: dict[str, Callable[[Any], list[list[int]]]],
) -> dict[str, Any]:
    profiles: Counter[str] = Counter()
    factors: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    identifiability_failures: list[dict[str, Any]] = []
    rival_stats = {
        name: {
            "competitor_refuted": 0,
            "competitor_survived_demos": 0,
            "competitor_survived_all": 0,
            "query_discriminates": 0,
            "first_refuter": None,
            "first_survivor": None,
        }
        for name in rivals
    }

    for k in range(LESSONS_PER_BAND):
        seed = _lesson_seed(band, k)
        start = k * 11
        demos, query = _episode(seed, start, band)
        reasons = GEN.lesson_identifiable(demos, query)
        if reasons:
            identifiability_failures.append(
                {"k": k, "seed": seed, "sample_index": start, "reasons": reasons}
            )

        for pair in [*demos, query]:
            obs = GEN.semantic_observables(pair["input"])
            profiles[obs["profile"]] += 1
            factors.update(obs["limiting_factors"])
            unique_inputs.add(_grid_sha(pair["input"]))

        for name, rival in rivals.items():
            demo_agreements = [
                rival(pair["input"]) == pair["output"] for pair in demos
            ]
            query_agrees = rival(query["input"]) == query["output"]
            stats = rival_stats[name]
            if all(demo_agreements):
                stats["competitor_survived_demos"] += 1
                if query_agrees:
                    stats["competitor_survived_all"] += 1
                else:
                    stats["query_discriminates"] += 1
                if stats["first_survivor"] is None:
                    stats["first_survivor"] = {
                        "k": k,
                        "seed": seed,
                        "sample_index": start,
                        "query_agrees": query_agrees,
                        "demo_observables": [
                            GEN.semantic_observables(pair["input"]) for pair in demos
                        ],
                        "query_observables": GEN.semantic_observables(query["input"]),
                    }
            else:
                stats["competitor_refuted"] += 1
                if stats["first_refuter"] is None:
                    first_index = demo_agreements.index(False)
                    stats["first_refuter"] = {
                        "k": k,
                        "seed": seed,
                        "sample_index": start,
                        "refuting_demo_offset": first_index,
                        "refuting_pair": _pair_record(demos[first_index], rival),
                        "demo_observables": [
                            GEN.semantic_observables(pair["input"]) for pair in demos
                        ],
                    }

    return {
        "lessons": LESSONS_PER_BAND,
        "demos_per_lesson": GEN.EXAMPLES_NEEDED,
        "queries_per_lesson": 1,
        "unique_inputs": len(unique_inputs),
        "profile_counts": dict(sorted(profiles.items())),
        "limiting_factor_counts": dict(sorted(factors.items())),
        "lesson_identifiability_failures": identifiability_failures,
        "rivals": rival_stats,
    }


def build_report(phase: str) -> dict[str, Any]:
    canonical_pairs = _canonical_pairs()
    all_rivals = dict(GEN.CANONICAL_SHORTCUTS)
    canonical = _canonical_report(canonical_pairs, all_rivals)
    fitting = {
        name: all_rivals[name]
        for name, record in canonical.items()
        if record["fits_all"]
    }
    bands = {band: _band_report(band, fitting) for band in BANDS}
    return {
        "schema": "arcpuzzles-task-local-rival-probe-v2",
        "task_id": TASK_ID,
        "phase": phase,
        "generator_version": GEN.VERSION,
        "declared_rule_hash": GEN.RULE_HASH,
        "generator_sha256": _sha256_bytes(GENERATOR_PATH.read_bytes()),
        "probe_sha256": _sha256_bytes(HERE.read_bytes()),
        "canonical_pair_count": len(canonical_pairs),
        "canonical_shortcuts": canonical,
        "canonical_fitting_shortcuts": sorted(fitting),
        "sampler": {
            "source": "semantic-gate pinned lesson plan replicated exactly for 100 lessons per band",
            "bands": list(BANDS),
            "k_range": f"0..{LESSONS_PER_BAND - 1} inclusive",
            "seed_formula": "sha256('profile-floor:v1:' + task_id + ':lesson:' + band + ':' + k), first 12 hex digits",
            "sample_index_formula": "k * 11",
            "lesson_assembly": "EXAMPLES_NEEDED consecutive demos followed by one query",
            "outputs": "generator rule_mirror; Racket/mirror parity is checked separately by the battery",
        },
        "domain_limits": (
            "Lawful generator outputs only; bounded rival census, not proof of "
            "unique induction. Only declared rivals that fit every canonical pair "
            "receive the 100-lesson census."
        ),
        "bands": bands,
        "all_unique_inputs": sum(record["unique_inputs"] for record in bands.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=("before", "after"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args.phase)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"wrote {args.out}")
    print("canonical-fitting shortcuts:", ", ".join(report["canonical_fitting_shortcuts"]) or "none")
    for band, record in report["bands"].items():
        print(f"{band}: {record['unique_inputs']} unique inputs")
        for name, stats in record["rivals"].items():
            print(
                f"  {name}: survived_demos={stats['competitor_survived_demos']} "
                f"survived_all={stats['competitor_survived_all']} "
                f"refuted={stats['competitor_refuted']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
