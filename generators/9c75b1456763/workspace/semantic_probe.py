#!/usr/bin/env python3
"""Source-bound semantic census for generator 9c75b1456763.

The probe uses the generator's real declarations rather than a copied rival
list.  It measures every cyclic lesson start, records exact sampling policy and
source hashes, and keeps per-band denominators explicit.  It is intentionally
Python-mirror-only; authoritative Racket parity remains the battery's
``rule_smoke`` responsibility and should be cited beside this report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
from typing import Any


TASK_ID = "9c75b1456763"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
BASE_PATH = (
    REPO
    / "shared"
    / "data"
    / "base"
    / "solutions"
    / "training"
    / "09c534e7__9c75b1456763.json"
)
BANDS = ("easy", "medium", "hard")
BAND_SEED_OFFSETS = {"easy": 0, "medium": 100_000, "hard": 200_000}


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _grid_sha(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return _sha_bytes(payload)


def _load_generator():
    runtime = REPO / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location(
        f"generator_{TASK_ID}_semantic_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_row() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} missing")


def _source_binding(generator, canonical: dict[str, Any]) -> dict[str, Any]:
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    selected = base["racket_target"]["target_code"]
    archival = base["racket_target"]["raw_code"]
    canonical_program = canonical["program_solution"]
    return {
        "generator_path": GENERATOR_PATH.relative_to(REPO).as_posix(),
        "generator_sha256": _sha_bytes(GENERATOR_PATH.read_bytes()),
        "generator_version": generator.VERSION,
        "declared_rule_hash": generator.RULE_HASH,
        "canonical_program_exact_sha256": _sha_bytes(canonical_program.encode()),
        "selected_target_exact_sha256": _sha_bytes(selected.encode()),
        "archival_raw_exact_sha256": _sha_bytes(archival.encode()),
        "selected_equals_canonical_exact": selected == canonical_program,
        "archival_equals_canonical_exact": archival == canonical_program,
    }


def _canonical_shortcut_fit(generator, canonical: dict[str, Any]) -> dict[str, Any]:
    pairs = list(canonical.get("train", [])) + list(canonical.get("test", []))
    results: dict[str, Any] = {}
    for name, rival in getattr(generator, "CANONICAL_SHORTCUTS", {}).items():
        matched = 0
        errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                if rival(pair["input"]) == pair["output"]:
                    matched += 1
            except Exception as exc:  # evidence, never conceal a broken rival
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        results[name] = {
            "matched": matched,
            "denominator": len(pairs),
            "fits_every_pair": matched == len(pairs) and not errors,
            "errors": errors,
        }
    return results


def _cyclic_window(items: list[Any], start: int, length: int) -> list[Any]:
    return [items[(start + offset) % len(items)] for offset in range(length)]


def run_probe(*, per_band: int = 120, seed_base: int = 31_000) -> dict[str, Any]:
    if type(per_band) is not int or per_band < 3:
        raise ValueError("per_band must be an integer >= 3")
    if type(seed_base) is not int:
        raise ValueError("seed_base must be an integer")

    generator = _load_generator()
    canonical = _canonical_row()
    n_demos = int(getattr(generator, "EXAMPLES_NEEDED", 3))
    if per_band < n_demos + 1:
        raise ValueError(
            f"per_band={per_band} is too small for {n_demos} demos plus one query"
        )

    report: dict[str, Any] = {
        "schema": f"{TASK_ID}-semantic-probe-v1",
        "task_id": TASK_ID,
        "source_binding": _source_binding(generator, canonical),
        "sampler": {
            "bands": list(BANDS),
            "per_band": per_band,
            "total_draws": per_band * len(BANDS),
            "seed_base": seed_base,
            "seed_formula": "seed_base + band_offset + sample_index",
            "band_seed_offsets": BAND_SEED_OFFSETS,
            "sample_index_range": [0, per_band - 1],
            "difficulty_argument": "band name",
            "overrides": {},
            "lesson_policy": (
                f"all {per_band} cyclic starts per band; {n_demos} demos followed "
                "by the next cyclic sample as query"
            ),
        },
        "declared_contract": {
            "axes": generator.AXES,
            "examples_needed": n_demos,
            "semantic_witnesses": sorted(generator.SEMANTIC_WITNESSES),
            "semantic_rivals": sorted(generator.SEMANTIC_RIVALS),
            "lesson_competitors": sorted(generator.LESSON_COMPETITORS),
            "canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
            "profile_limits": {
                name: {
                    "height": info[0],
                    "width": info[1],
                    "components": info[2],
                    "palette_size": info[3],
                }
                for name, info in generator._PROFILE_INFO.items()
            },
            "claim_limit": (
                "Finite generated-domain census only; this does not establish "
                "universal induction or correctness outside self_check."
            ),
        },
        "canonical_pairs": len(canonical.get("train", []))
        + len(canonical.get("test", [])),
        "canonical_shortcut_fit": _canonical_shortcut_fit(generator, canonical),
        "bands": {},
    }

    all_input_hashes: set[str] = set()
    all_output_hashes: set[str] = set()
    for band in BANDS:
        samples: list[dict[str, Any]] = []
        strict_pass = 0
        validation_errors: list[dict[str, Any]] = []
        witness_hits = Counter({name: 0 for name in generator.SEMANTIC_WITNESSES})
        rival_disagreements = Counter({name: 0 for name in generator.SEMANTIC_RIVALS})
        profile_counts: Counter[str] = Counter()
        axis_counts: dict[str, Counter[Any]] = {
            axis: Counter() for axis in generator.AXES
        }
        changed_cells: list[int] = []
        input_hashes: list[str] = []
        output_hashes: list[str] = []

        for sample_index in range(per_band):
            seed = seed_base + BAND_SEED_OFFSETS[band] + sample_index
            grid = generator.generate(seed, sample_index, difficulty=band)
            errors = generator.strict_canonical_like(grid)
            if errors:
                validation_errors.append(
                    {
                        "sample_index": sample_index,
                        "seed": seed,
                        "errors": list(errors),
                    }
                )
            else:
                strict_pass += 1
            output = generator.rule_mirror(grid)
            observed = generator.observe_overrides(grid)
            if observed.get("profile") is not None:
                profile_counts[str(observed["profile"])] += 1
            for axis in generator.AXES:
                axis_counts[axis][observed.get(axis, "<unobserved>")] += 1

            for name, witness in generator.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_hits[name] += 1
            for name, rival in generator.SEMANTIC_RIVALS.items():
                if rival(grid) != output:
                    rival_disagreements[name] += 1

            changed_cells.append(
                sum(
                    before != after
                    for before_row, after_row in zip(grid, output)
                    for before, after in zip(before_row, after_row)
                )
            )
            input_hash = _grid_sha(grid)
            output_hash = _grid_sha(output)
            input_hashes.append(input_hash)
            output_hashes.append(output_hash)
            samples.append({"input": grid, "output": output})

        lesson_failures: list[dict[str, Any]] = []
        for start in range(per_band):
            demos = _cyclic_window(samples, start, n_demos)
            query = samples[(start + n_demos) % per_band]
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({"start": start, "reasons": list(reasons)})

        unique_inputs = len(set(input_hashes))
        unique_outputs = len(set(output_hashes))
        all_input_hashes.update(input_hashes)
        all_output_hashes.update(output_hashes)
        report["bands"][band] = {
            "draws": per_band,
            "seed_range": [
                seed_base + BAND_SEED_OFFSETS[band],
                seed_base + BAND_SEED_OFFSETS[band] + per_band - 1,
            ],
            "sample_index_range": [0, per_band - 1],
            "strict_pass": strict_pass,
            "strict_fraction": strict_pass / per_band,
            "validation_errors": validation_errors,
            "unique_inputs": unique_inputs,
            "unique_input_fraction": unique_inputs / per_band,
            "unique_outputs": unique_outputs,
            "unique_output_fraction": unique_outputs / per_band,
            "profile_counts": dict(sorted(profile_counts.items())),
            "axis_counts": {
                axis: {str(key): value for key, value in sorted(counts.items(), key=lambda kv: str(kv[0]))}
                for axis, counts in axis_counts.items()
            },
            "changed_cells": {
                "minimum": min(changed_cells),
                "median": statistics.median(changed_cells),
                "maximum": max(changed_cells),
            },
            "witness_hits": dict(witness_hits),
            "rival_disagreements": dict(rival_disagreements),
            "lessons": {
                "checked_cyclic_starts": per_band,
                "identifiable": per_band - len(lesson_failures),
                "failures": lesson_failures,
            },
        }

    report["aggregate"] = {
        "draws": per_band * len(BANDS),
        "unique_inputs": len(all_input_hashes),
        "unique_outputs": len(all_output_hashes),
        "all_strict": all(
            row["strict_pass"] == row["draws"] for row in report["bands"].values()
        ),
        "all_lessons_identifiable": all(
            row["lessons"]["identifiable"] == row["lessons"]["checked_cyclic_starts"]
            for row in report["bands"].values()
        ),
        "all_declared_rivals_disagreed_every_draw": all(
            count == row["draws"]
            for row in report["bands"].values()
            for count in row["rival_disagreements"].values()
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=120)
    parser.add_argument("--seed-base", type=int, default=31_000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(per_band=args.per_band, seed_base=args.seed_base)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"semantic-probe: {report['aggregate']['draws']} draws, "
        f"{report['aggregate']['unique_inputs']} unique inputs, "
        f"strict={report['aggregate']['all_strict']}, "
        f"lessons={report['aggregate']['all_lessons_identifiable']} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
