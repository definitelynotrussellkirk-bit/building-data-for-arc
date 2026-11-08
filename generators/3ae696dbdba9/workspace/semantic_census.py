#!/usr/bin/env python3
"""Source-bound lesson census for generator ``3ae696dbdba9``.

The probe imports the selected generator from an explicit prepared-runtime root,
uses the generator's own declarations instead of a copied rival list, and checks
consecutive four-demo lessons at every cyclic schedule start.  Outputs come from
the task-local Python mirror; official battery rule-smoke/authority stages are the
separate evidence that this mirror agrees with the selected Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

TASK_ID = "3ae696dbdba9"
BANDS = ("easy", "medium", "hard")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _grid_hash(grid: Any) -> str:
    return _sha256_bytes(_canonical_json(grid))


def _load_generator(runtime_root: Path):
    runtime_root = runtime_root.resolve()
    expected = (
        runtime_root
        / "puzzle_generators"
        / "per_puzzle"
        / TASK_ID
        / "generator.py"
    )
    if not expected.is_file():
        raise FileNotFoundError(
            f"prepared runtime generator not found: {expected}; pass --runtime-root"
        )
    root_text = str(runtime_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    importlib.invalidate_caches()
    module = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    loaded = Path(module.__file__).resolve()
    if loaded != expected.resolve():
        raise RuntimeError(
            f"generator import escaped requested runtime: loaded {loaded}, expected {expected}"
        )
    return module, expected


def _canonical_row(runtime_root: Path) -> tuple[dict[str, Any], Path]:
    path = runtime_root / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row, path
    raise RuntimeError(f"canonical row {TASK_ID} not found in {path}")


def _canonical_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    pairs = [*row.get("train", []), *test]
    usable = [pair for pair in pairs if isinstance(pair, dict) and {"input", "output"} <= pair.keys()]
    if not usable:
        raise RuntimeError("canonical row contains no labeled pairs")
    return usable


def _counterexample(
    *,
    band: str,
    seed: int,
    sample_index: int,
    profile: str | None,
    grid: Any,
    intended: Any,
    rival: Any,
) -> dict[str, Any]:
    return {
        "band": band,
        "seed": seed,
        "sample_index": sample_index,
        "schedule_profile": profile,
        "input_sha256": _grid_hash(grid),
        "input": deepcopy(grid),
        "intended_output": deepcopy(intended),
        "rival_output": deepcopy(rival),
    }


def run_census(
    *,
    runtime_root: Path,
    lessons_per_band: int = 100,
    bands: Sequence[str] = BANDS,
    base_seed: int = 930_000,
) -> dict[str, Any]:
    """Run a deterministic census and return a JSON-serializable report."""
    runtime_root = Path(runtime_root).resolve()
    if type(lessons_per_band) is not int or lessons_per_band < 1:
        raise ValueError("lessons_per_band must be a positive integer")
    bands = tuple(bands)
    if not bands or any(band not in BANDS for band in bands):
        raise ValueError(f"bands must be a nonempty subset of {BANDS!r}")
    if type(base_seed) is not int or base_seed < 0:
        raise ValueError("base_seed must be a nonnegative integer")

    gen, generator_path = _load_generator(runtime_root)
    row, canonical_path = _canonical_row(runtime_root)
    canonical_pairs = _canonical_pairs(row)
    normalized_rule = " ".join(row["program_solution"].split()).encode()
    canonical_rule_hash = _sha256_bytes(normalized_rule)[:12]

    declared_shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    lesson_competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    if not declared_shortcuts or not lesson_competitors:
        raise RuntimeError("generator must declare CANONICAL_SHORTCUTS and LESSON_COMPETITORS")

    canonical_mirror_mismatches: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical_pairs):
        actual = gen.rule_mirror(deepcopy(pair["input"]))
        if actual != pair["output"]:
            canonical_mirror_mismatches.append(
                {
                    "pair_index": index,
                    "expected_sha256": _grid_hash(pair["output"]),
                    "actual_sha256": _grid_hash(actual),
                }
            )

    shortcut_report: dict[str, dict[str, Any]] = {}
    for name, rival in declared_shortcuts.items():
        matches = [rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical_pairs]
        shortcut_report[name] = {
            "canonical_pairs_matched": sum(matches),
            "canonical_pairs_total": len(matches),
            "fits_all_canonical_pairs": all(matches),
            "generated_disagreements": 0,
            "first_generated_counterexample": None,
        }

    competitor_report: dict[str, dict[str, Any]] = {
        name: {
            "generated_inputs_checked": 0,
            "generated_input_disagreements": 0,
            "lessons_checked": 0,
            "lessons_refuted": 0,
            "first_generated_counterexample": None,
        }
        for name in lesson_competitors
    }

    cycle_len = len(getattr(gen, "SCHEDULE_PROFILES", ()))
    if cycle_len < 1:
        raise RuntimeError("SCHEDULE_PROFILES must be a nonempty finite cycle")
    examples_needed = int(getattr(gen, "EXAMPLES_NEEDED", 0))
    if examples_needed < 1:
        raise RuntimeError("EXAMPLES_NEEDED must be positive")

    failures: list[dict[str, Any]] = []
    global_unique_inputs: set[str] = set()
    invalid_inputs = 0
    ambiguous_lessons = 0
    band_reports: dict[str, dict[str, Any]] = {}

    for band_index, band in enumerate(bands):
        unique_inputs: set[str] = set()
        profile_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        start_counts: Counter[str] = Counter()
        strict_count = 0
        band_invalid = 0
        band_ambiguous = 0

        for lesson_index in range(lessons_per_band):
            cyclic_start = lesson_index % cycle_len
            start_counts[str(cyclic_start)] += 1
            seed = base_seed + band_index * 1_000_000 + lesson_index
            pairs: list[dict[str, Any]] = []

            for offset in range(examples_needed + 1):
                sample_index = cyclic_start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = list(gen.self_check(deepcopy(grid)))
                if errors:
                    invalid_inputs += 1
                    band_invalid += 1
                    failures.append(
                        {
                            "kind": "invalid_input",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                intended = gen.rule_mirror(deepcopy(grid))
                digest = _grid_hash(grid)
                unique_inputs.add(digest)
                global_unique_inputs.add(digest)
                profile = (
                    gen.schedule_profile(seed, sample_index, band)
                    if callable(getattr(gen, "schedule_profile", None))
                    else None
                )
                if profile is not None:
                    profile_counts[str(profile)] += 1
                strict_count += int(not gen.strict_canonical_like(deepcopy(grid)))
                for name, predicate in witnesses.items():
                    witness_counts[name] += int(bool(predicate(deepcopy(grid))))

                for name, rival in lesson_competitors.items():
                    rival_output = rival(deepcopy(grid))
                    row_for_rival = competitor_report[name]
                    row_for_rival["generated_inputs_checked"] += 1
                    if rival_output != intended:
                        row_for_rival["generated_input_disagreements"] += 1
                        if row_for_rival["first_generated_counterexample"] is None:
                            row_for_rival["first_generated_counterexample"] = _counterexample(
                                band=band,
                                seed=seed,
                                sample_index=sample_index,
                                profile=profile,
                                grid=grid,
                                intended=intended,
                                rival=rival_output,
                            )

                for name, rival in declared_shortcuts.items():
                    rival_output = rival(deepcopy(grid))
                    if rival_output != intended:
                        row_for_shortcut = shortcut_report[name]
                        row_for_shortcut["generated_disagreements"] += 1
                        if row_for_shortcut["first_generated_counterexample"] is None:
                            row_for_shortcut["first_generated_counterexample"] = _counterexample(
                                band=band,
                                seed=seed,
                                sample_index=sample_index,
                                profile=profile,
                                grid=grid,
                                intended=intended,
                                rival=rival_output,
                            )

                pairs.append(
                    {
                        "input": deepcopy(grid),
                        "output": intended,
                        "sample_index": sample_index,
                        "profile": profile,
                    }
                )

            demos = pairs[:examples_needed]
            query = pairs[examples_needed]
            survivors: list[str] = []
            for name, rival in lesson_competitors.items():
                row_for_rival = competitor_report[name]
                row_for_rival["lessons_checked"] += 1
                refuted = any(
                    rival(deepcopy(pair["input"])) != pair["output"]
                    for pair in demos
                )
                if refuted:
                    row_for_rival["lessons_refuted"] += 1
                else:
                    survivors.append(name)

            identifiability_errors = list(
                gen.lesson_identifiable(demos, query)
            )
            if survivors or identifiability_errors:
                ambiguous_lessons += 1
                band_ambiguous += 1
                failures.append(
                    {
                        "kind": "ambiguous_lesson",
                        "band": band,
                        "lesson_index": lesson_index,
                        "cyclic_start": cyclic_start,
                        "seed": seed,
                        "demo_sample_indices": [pair["sample_index"] for pair in demos],
                        "query_sample_index": query["sample_index"],
                        "surviving_competitors": survivors,
                        "lesson_identifiable_errors": identifiability_errors,
                    }
                )

        band_reports[band] = {
            "lessons": lessons_per_band,
            "inputs": lessons_per_band * (examples_needed + 1),
            "unique_inputs": len(unique_inputs),
            "invalid_inputs": band_invalid,
            "ambiguous_lessons": band_ambiguous,
            "strict_canonical_like_inputs": strict_count,
            "cyclic_start_counts": dict(sorted(start_counts.items())),
            "schedule_profile_counts": dict(sorted(profile_counts.items())),
            "witness_counts": dict(sorted(witness_counts.items())),
        }

    lessons_total = lessons_per_band * len(bands)
    inputs_total = lessons_total * (examples_needed + 1)
    expected_refutations = lessons_total
    missing_counterexamples = [
        name
        for name, item in shortcut_report.items()
        if item["first_generated_counterexample"] is None
    ]
    surviving_competitors = [
        name
        for name, item in competitor_report.items()
        if item["lessons_refuted"] != expected_refutations
    ]
    canonical_fit_failures = [
        name
        for name, item in shortcut_report.items()
        if not item["fits_all_canonical_pairs"]
    ]

    source_bound = (
        Path(gen.__file__).resolve() == generator_path.resolve()
        and getattr(gen, "RULE_HASH", None) == canonical_rule_hash
    )
    passed = not (
        failures
        or canonical_mirror_mismatches
        or missing_counterexamples
        or surviving_competitors
        or canonical_fit_failures
    ) and source_bound

    report = {
        "schema": "3ae696dbdba9-semantic-census-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "generator_path_in_runtime": str(generator_path.relative_to(runtime_root)),
        "probe_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "canonical_jsonl_sha256": _sha256_bytes(canonical_path.read_bytes()),
        "canonical_rule_hash_computed": canonical_rule_hash,
        "generator_rule_hash_declared": getattr(gen, "RULE_HASH", None),
        "source_bound": source_bound,
        "sampling": {
            "sampler": "direct selected generate(seed, sample_index, difficulty) from the prepared runtime",
            "labeler": "task-local rule_mirror; bind separately to Racket with authority_sync and rule_smoke",
            "bands": list(bands),
            "lessons_per_band": lessons_per_band,
            "base_seed": base_seed,
            "seed_formula": "base_seed + band_index*1000000 + lesson_index",
            "cyclic_start_formula": "lesson_index % len(SCHEDULE_PROFILES)",
            "demos_per_lesson": examples_needed,
            "queries_per_lesson": 1,
            "sample_indices": "cyclic_start through cyclic_start+EXAMPLES_NEEDED",
            "candidate_rejections": 0,
        },
        "domain_limits": {
            "axes": deepcopy(getattr(gen, "AXES", {})),
            "invariants": list(getattr(gen, "INVARIANTS", [])),
            "finite_schedule_profiles": list(getattr(gen, "SCHEDULE_PROFILES", [])),
            "claim_scope": (
                "Finite source-bound census over declared rivals and the selected generator domain; "
                "not universal ARC induction or model-performance evidence."
            ),
        },
        "counts": {
            "canonical_pairs": len(canonical_pairs),
            "lessons": lessons_total,
            "inputs": inputs_total,
            "unique_inputs": len(global_unique_inputs),
            "invalid_inputs": invalid_inputs,
            "ambiguous_lessons": ambiguous_lessons,
            "canonical_mirror_mismatches": len(canonical_mirror_mismatches),
        },
        "bands": band_reports,
        "canonical_shortcuts": shortcut_report,
        "lesson_competitors": competitor_report,
        "canonical_mirror_mismatches": canonical_mirror_mismatches,
        "failures": failures,
        "summary_findings": {
            "canonical_shortcuts_without_generated_counterexample": missing_counterexamples,
            "lesson_competitors_surviving_at_least_one_demo_window": surviving_competitors,
            "declared_canonical_shortcuts_not_fitting_all_canonical_pairs": canonical_fit_failures,
        },
        "passed": passed,
        "training_admitted": False,
    }
    return report


def _parse_bands(raw: str) -> tuple[str, ...]:
    bands = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not bands or any(band not in BANDS for band in bands):
        raise argparse.ArgumentTypeError(
            f"bands must be a comma-separated nonempty subset of {','.join(BANDS)}"
        )
    return bands


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path.cwd(),
        help="prepared runtime containing puzzle_generators/ and data/canonical/",
    )
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--bands", type=_parse_bands, default=BANDS)
    parser.add_argument("--base-seed", type=int, default=930_000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = run_census(
        runtime_root=args.runtime_root,
        lessons_per_band=args.lessons_per_band,
        bands=args.bands,
        base_seed=args.base_seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "generator_sha256": report["generator_sha256"],
                "counts": report["counts"],
                "source_bound": report["source_bound"],
                "passed": report["passed"],
                "out": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
