#!/usr/bin/env python3
"""Source-bound semantic census for generator ``1b9d8370e28b``.

The probe imports an explicit generator path, hashes the exact bytes it used,
iterates the generator's own shortcut/rival/witness declarations, verifies every
declared canonical shortcut against every usable canonical pair, and assembles
independent deterministic lessons in each difficulty band.

Generated outputs are labelled with the generator's task-local ``rule_mirror``.
That mirror is not treated as an authority: the returned report says so and must
be read together with the battery's source-bound Racket ``rule_smoke`` evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "1b9d8370e28b"
BANDS = ("easy", "medium", "hard")
DEFAULT_LESSONS_PER_BAND = 100
DEFAULT_BASE_SEED = 910_000


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path):
    digest = _sha256(path)
    name = f"probe_generator_{TASK_ID}_{digest[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest


def _canonical_row(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _grid_key(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _canonical_audit(gen, canonical: dict[str, Any]) -> dict[str, Any]:
    pairs = list(canonical.get("train", [])) + list(canonical.get("test", []))
    result: dict[str, Any] = {"pair_count": len(pairs)}
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    for name, rival in sorted(shortcuts.items()):
        fits = 0
        first_mismatch = None
        for index, pair in enumerate(pairs):
            rival_output = rival(pair["input"])
            if rival_output == pair["output"]:
                fits += 1
            elif first_mismatch is None:
                first_mismatch = {
                    "pair_index": index,
                    "input_sha256": _grid_key(pair["input"]),
                    "expected_sha256": _grid_key(pair["output"]),
                    "rival_sha256": _grid_key(rival_output),
                }
        result[name] = {
            "fits": fits,
            "total": len(pairs),
            "first_mismatch": first_mismatch,
        }
    return result


def build_report(
    *,
    generator_path: Path,
    canonical_path: Path,
    lessons_per_band: int = DEFAULT_LESSONS_PER_BAND,
    base_seed: int = DEFAULT_BASE_SEED,
) -> dict[str, Any]:
    if lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be positive")
    generator_path = generator_path.resolve()
    canonical_path = canonical_path.resolve()
    gen, generator_sha = _load_module(generator_path)
    if getattr(gen, "TASK_ID", None) != TASK_ID:
        raise RuntimeError(
            f"loaded TASK_ID {getattr(gen, 'TASK_ID', None)!r}, expected {TASK_ID}"
        )

    canonical = _canonical_row(canonical_path)
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    if not competitors or not shortcuts or not witnesses:
        raise RuntimeError(
            "generator must declare LESSON_COMPETITORS, CANONICAL_SHORTCUTS, "
            "and SEMANTIC_WITNESSES"
        )
    if not hasattr(gen, "rule_mirror"):
        raise RuntimeError("generator must expose rule_mirror for this local probe")

    demos_per_lesson = int(getattr(gen, "EXAMPLES_NEEDED", 3))
    pairs_per_lesson = demos_per_lesson + 1
    report: dict[str, Any] = {
        "schema": "1b9d8370e28b-rival-probe/1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": generator_sha,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "labelling": {
            "method": "generator.rule_mirror",
            "authority_limit": (
                "Python mirror only; use with the battery rule_smoke and authority "
                "evidence for Racket parity. No private answers are read."
            ),
        },
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": demos_per_lesson,
            "queries_per_lesson": 1,
            "pairs_per_lesson": pairs_per_lesson,
            "base_seed": base_seed,
            "seed_formula": "base_seed + band_index*100000 + lesson_index",
            "sample_index_formula": "lesson_index*pairs_per_lesson + pair_index",
            "lesson_policy": (
                "Each lesson is an independent deterministic block of public "
                "generate(seed, sample_index, difficulty=band) calls."
            ),
        },
        "declarations": {
            "canonical_shortcuts": sorted(shortcuts),
            "lesson_competitors": sorted(competitors),
            "semantic_witnesses": sorted(witnesses),
            "witness_rivals": getattr(gen, "WITNESS_RIVALS", {}),
        },
        "canonical": _canonical_audit(gen, canonical),
        "per_band": {},
        "domain_limits": [
            "Only grid sizes and axes emitted by generator VERSION 3.0.0 are sampled.",
            "The census tests the declared rigid-components rival, not every imaginable hypothesis.",
            "Counts describe deterministic sampled lessons, not universal induction or model accuracy.",
            "Racket parity is delegated to the separately retained source-bound rule_smoke stage.",
        ],
    }

    for band_index, band in enumerate(BANDS):
        input_hashes: set[str] = set()
        output_hashes: set[str] = set()
        strict_rejections = 0
        witness_hits = {name: 0 for name in witnesses}
        rival_pair_disagreements = {name: 0 for name in competitors}
        competitor_stats = {
            name: {
                "demo_refuted": 0,
                "demo_survived": 0,
                "survived_and_query_disagreed": 0,
                "survived_query_tied": 0,
            }
            for name in competitors
        }
        identifiable_failures = 0
        first_counterexamples: dict[str, dict[str, Any] | None] = {
            name: None for name in competitors
        }

        for lesson_index in range(lessons_per_band):
            seed = base_seed + band_index * 100_000 + lesson_index
            pairs = []
            for pair_index in range(pairs_per_lesson):
                sample_index = lesson_index * pairs_per_lesson + pair_index
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = list(gen.strict_canonical_like(grid))
                if errors:
                    strict_rejections += 1
                output = gen.rule_mirror(grid)
                input_hashes.add(_grid_key(grid))
                output_hashes.add(_grid_key(output))
                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_hits[name] += 1
                for name, rival in competitors.items():
                    rival_output = rival(grid)
                    if rival_output != output:
                        rival_pair_disagreements[name] += 1
                        if first_counterexamples[name] is None:
                            first_counterexamples[name] = {
                                "band": band,
                                "lesson_index": lesson_index,
                                "pair_index": pair_index,
                                "seed": seed,
                                "sample_index": sample_index,
                                "input": grid,
                                "official_mirror": output,
                                "rival": rival_output,
                            }
                pairs.append({"input": grid, "output": output})

            demos = pairs[:demos_per_lesson]
            query = pairs[demos_per_lesson]
            if gen.lesson_identifiable(demos, query):
                identifiable_failures += 1
            for name, rival in competitors.items():
                survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                if not survives:
                    competitor_stats[name]["demo_refuted"] += 1
                    continue
                competitor_stats[name]["demo_survived"] += 1
                if rival(query["input"]) != query["output"]:
                    competitor_stats[name]["survived_and_query_disagreed"] += 1
                else:
                    competitor_stats[name]["survived_query_tied"] += 1

        report["per_band"][band] = {
            "lessons": lessons_per_band,
            "pairs": lessons_per_band * pairs_per_lesson,
            "unique_inputs": len(input_hashes),
            "unique_outputs": len(output_hashes),
            "strict_rejections": strict_rejections,
            "witness_hits": witness_hits,
            "rival_pair_disagreements": rival_pair_disagreements,
            "lesson_competitors": competitor_stats,
            "lesson_identifiable_failures": identifiable_failures,
            "first_counterexamples": first_counterexamples,
        }

    return report


def main() -> int:
    here = Path(__file__).resolve()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=here.parents[1] / "generator.py",
        help="exact generator.py to hash and import",
    )
    parser.add_argument(
        "--canonical",
        type=Path,
        default=here.parents[3] / "shared/data/canonical/puzzles.jsonl",
        help="canonical JSONL ledger",
    )
    parser.add_argument("--lessons-per-band", type=int, default=DEFAULT_LESSONS_PER_BAND)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(
        generator_path=args.generator,
        canonical_path=args.canonical,
        lessons_per_band=args.lessons_per_band,
        base_seed=args.base_seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": report["generator_sha256"],
        "lessons_per_band": args.lessons_per_band,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
