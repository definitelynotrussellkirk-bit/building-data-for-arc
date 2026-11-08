#!/usr/bin/env python3
"""Source-bound curriculum probe for ARC task 733c1bac8c45.

This is a reusable review tool, not a solve helper.  It loads the selected
``generator.py`` by path, checks an independent row-packing oracle against the
canonical labels, samples every schedule position in every difficulty band,
checks all held-out query rotations, and exercises literal override boundaries.
The optional expected SHA-256 prevents accidentally attaching a report to a
newer or older generator source.
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


TASK_ID = "733c1bac8c45"
HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
sys.dont_write_bytecode = True
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402

BANDS = (None, "easy", "medium", "hard")
CORE_WITNESSES = (
    "visible_leftward_motion",
    "multiple_moving_rows",
    "internal_gap_collapse",
    "multi_column_travel",
    "variable_row_cardinality",
)
TALL_WITNESSES = ("active_row_below_five", "more_than_four_active_rows")
EXPECTED_WITNESSES = frozenset(CORE_WITNESSES + TALL_WITNESSES)
EXPECTED_SHORTCUTS = frozenset({"fixed_five_rows", "first_four_active_rows_only"})
EXPECTED_COMPETITORS = frozenset({
    "identity",
    "right_pack",
    "translate_pattern_left_without_compacting",
    "move_each_cell_one_step_left",
    "pack_only_first_active_row",
    "fixed_five_rows",
    "first_four_active_rows_only",
})
OVERRIDE_CASES = (
    {"grid_h": 4, "grid_w": 5, "active_rows": 3},
    {"grid_h": 6, "grid_w": 8, "active_rows": 5},
    {"grid_h": 12, "grid_w": 14, "active_rows": 9},
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def load_generator(path: str | Path | None = None):
    """Load a generator candidate without importing a cached module."""
    source = Path(path) if path is not None else TASK_HOME / "generator.py"
    source = source.resolve()
    name = f"probe_{TASK_ID}_{_sha256(source)[:16]}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module, source


def independent_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Apply the row rule without calling any generator implementation helper."""
    output: list[list[int]] = []
    for row in grid:
        nonzero = [value for value in row if value != 0]
        if not nonzero:
            output.append([0] * len(row))
            continue
        output.append([nonzero[0]] * len(nonzero) + [0] * (len(row) - len(nonzero)))
    return output


def _failure(failures: list[dict[str, Any]], kind: str, **details: Any) -> None:
    failures.append({"kind": kind, **details})


def audit(
    module,
    source: Path,
    *,
    seeds_per_band: int = 32,
    expected_generator_sha256: str | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable source-bound contract and curriculum report."""
    if type(seeds_per_band) is not int or seeds_per_band <= 0:
        raise ValueError("seeds_per_band must be a positive integer (not bool)")

    generator_sha = _sha256(source)
    if expected_generator_sha256 is not None and expected_generator_sha256 != generator_sha:
        raise ValueError(
            "source hash mismatch: expected "
            f"{expected_generator_sha256}, observed {generator_sha}"
        )

    period = getattr(module, "LESSON_SCHEDULE_PERIOD", None)
    profiles = tuple(getattr(module, "SCHEDULE_PROFILES", ()))
    if type(period) is not int or period <= 0 or period != len(profiles):
        raise ValueError("invalid public lesson schedule declaration")

    failures: list[dict[str, Any]] = []
    declarations = (
        ("missing_witness_declaration", EXPECTED_WITNESSES, "SEMANTIC_WITNESSES"),
        ("missing_shortcut_declaration", EXPECTED_SHORTCUTS, "CANONICAL_SHORTCUTS"),
        ("missing_competitor_declaration", EXPECTED_COMPETITORS, "LESSON_COMPETITORS"),
    )
    for failure_kind, expected_names, attribute in declarations:
        observed_names = set(getattr(module, attribute, {}))
        for missing_name in sorted(expected_names - observed_names):
            _failure(failures, failure_kind, name=missing_name)

    counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    profile_counts: Counter[str] = Counter()
    witness_counts: Counter[str] = Counter()
    band_counts: dict[str, Counter[str]] = {}

    canonical = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    counts["canonical_pairs"] = len(canonical)
    canonical_shortcut_fit = {
        name: sum(solver(pair["input"]) == pair["output"] for pair in canonical)
        for name, solver in sorted(module.CANONICAL_SHORTCUTS.items())
    }
    for pair_index, pair in enumerate(canonical):
        expected = independent_oracle(pair["input"])
        if expected != pair["output"]:
            _failure(failures, "canonical_oracle_mismatch", pair_index=pair_index)
        if module.rule_mirror(pair["input"]) != pair["output"]:
            _failure(failures, "canonical_mirror_mismatch", pair_index=pair_index)
        errors = module.strict_canonical_like(pair["input"])
        if errors:
            _failure(
                failures,
                "canonical_input_rejected",
                pair_index=pair_index,
                errors=errors,
            )
    for name, fitted in canonical_shortcut_fit.items():
        if fitted != len(canonical):
            _failure(
                failures,
                "declared_shortcut_does_not_fit_canonical",
                rival=name,
                fitted=fitted,
                canonical_pairs=len(canonical),
            )

    for band_index, band in enumerate(BANDS):
        band_name = "default" if band is None else band
        local: Counter[str] = Counter()
        band_counts[band_name] = local
        for seed_offset in range(seeds_per_band):
            seed = 733000 + band_index * 10000 + seed_offset
            lesson: list[dict[str, list[list[int]]]] = []
            for sample_index in range(period):
                profile = module.schedule_profile(seed, sample_index, difficulty=band)
                expected_profile = profiles[sample_index]
                if profile != expected_profile:
                    _failure(
                        failures,
                        "schedule_profile_mismatch",
                        band=band_name,
                        seed=seed,
                        sample_index=sample_index,
                        expected=expected_profile,
                        observed=profile,
                    )
                profile_counts[profile] += 1
                try:
                    grid = module.generate(seed, sample_index, difficulty=band)
                    again = module.generate(seed, sample_index, difficulty=band)
                except Exception as exc:  # evidence should name the exact failing draw
                    _failure(
                        failures,
                        "generation_exception",
                        band=band_name,
                        seed=seed,
                        sample_index=sample_index,
                        exception_type=type(exc).__name__,
                        exception=str(exc),
                    )
                    continue

                counts["generated_grids"] += 1
                local["generated_grids"] += 1
                unique_inputs.add(_digest(grid))
                if grid != again:
                    _failure(
                        failures,
                        "nondeterministic_generation",
                        band=band_name,
                        seed=seed,
                        sample_index=sample_index,
                    )

                errors = module.self_check(grid, difficulty=band)
                if errors:
                    _failure(
                        failures,
                        "generated_input_rejected",
                        band=band_name,
                        seed=seed,
                        sample_index=sample_index,
                        errors=errors,
                    )

                expected = independent_oracle(grid)
                if module.rule_mirror(grid) != expected:
                    _failure(
                        failures,
                        "generated_mirror_mismatch",
                        band=band_name,
                        seed=seed,
                        sample_index=sample_index,
                    )

                observed = module.observe_overrides(grid)
                literal = {
                    "grid_h": len(grid),
                    "grid_w": len(grid[0]),
                    "active_rows": sum(any(value != 0 for value in row) for row in grid),
                }
                if observed != literal:
                    _failure(
                        failures,
                        "observer_mismatch",
                        band=band_name,
                        seed=seed,
                        sample_index=sample_index,
                        observed=observed,
                        literal=literal,
                    )

                required_witnesses = CORE_WITNESSES + (
                    TALL_WITNESSES if profile.startswith("tall_") else ()
                )
                for witness_name, witness in module.SEMANTIC_WITNESSES.items():
                    fired = bool(witness(grid))
                    if fired:
                        witness_counts[witness_name] += 1
                    if witness_name in required_witnesses and not fired:
                        _failure(
                            failures,
                            "missing_required_witness",
                            witness=witness_name,
                            profile=profile,
                            band=band_name,
                            seed=seed,
                            sample_index=sample_index,
                        )

                if profile.startswith("tall_"):
                    for rival_name, rival in module.CANONICAL_SHORTCUTS.items():
                        if rival(grid) == expected:
                            _failure(
                                failures,
                                "tall_profile_does_not_refute_shortcut",
                                rival=rival_name,
                                profile=profile,
                                band=band_name,
                                seed=seed,
                                sample_index=sample_index,
                            )

                lesson.append({"input": grid, "output": expected})

            if len(lesson) != period:
                continue
            for query_index, query in enumerate(lesson):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                reasons = module.lesson_identifiable(demos, query)
                counts["query_rotations"] += 1
                local["query_rotations"] += 1
                if reasons:
                    _failure(
                        failures,
                        "ambiguous_query_rotation",
                        band=band_name,
                        seed=seed,
                        query_index=query_index,
                        reasons=reasons,
                    )

    for case_index, overrides in enumerate(OVERRIDE_CASES):
        try:
            grid = module.generate(990000 + case_index, 17, difficulty="hard", **overrides)
        except Exception as exc:
            _failure(
                failures,
                "override_generation_exception",
                overrides=overrides,
                exception_type=type(exc).__name__,
                exception=str(exc),
            )
            continue
        counts["override_cases"] += 1
        observed = module.observe_overrides(grid)
        if observed != overrides:
            _failure(
                failures,
                "override_not_literal",
                overrides=overrides,
                observed=observed,
            )
        errors = module.self_check(grid, difficulty="hard")
        if errors:
            _failure(
                failures,
                "override_input_rejected",
                overrides=overrides,
                errors=errors,
            )

    try:
        module.generate(0, 0, grid_h=4, active_rows=5)
    except ValueError as exc:
        axes = set(getattr(exc, "incompatible_axes", ()))
        if axes != {"grid_h", "active_rows"}:
            _failure(
                failures,
                "incompatible_override_missing_axes",
                observed_axes=sorted(axes),
            )
    except Exception as exc:
        _failure(
            failures,
            "wrong_incompatible_override_exception",
            exception_type=type(exc).__name__,
            exception=str(exc),
        )
    else:
        _failure(failures, "incompatible_override_accepted")

    counts["unique_inputs"] = len(unique_inputs)
    return {
        "schema": "733c1bac8c45-workspace-probe-v1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_sha256": generator_sha,
        "probe_sha256": _sha256(Path(__file__)),
        "rule_hash": module.RULE_HASH,
        "schedule_period": period,
        "schedule_profiles": list(profiles),
        "seeds_per_band": seeds_per_band,
        "bands": {
            name: dict(sorted(values.items())) for name, values in band_counts.items()
        },
        "counts": dict(sorted(counts.items())),
        "profile_counts": dict(sorted(profile_counts.items())),
        "witness_counts": dict(sorted(witness_counts.items())),
        "canonical_shortcut_fit": canonical_shortcut_fit,
        "override_cases": list(OVERRIDE_CASES),
        "failures": failures,
        "passed": not failures,
        "authority_note": (
            "The independent Python oracle is diagnostic. The repository's canonical "
            "Racket rule remains label authority and must be checked separately."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=TASK_HOME / "generator.py")
    parser.add_argument("--expected-generator-sha256")
    parser.add_argument("--seeds-per-band", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    module, source = load_generator(args.generator)
    report = audit(
        module,
        source,
        seeds_per_band=args.seeds_per_band,
        expected_generator_sha256=args.expected_generator_sha256,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "failures": len(report["failures"]),
        "generated_grids": report["counts"].get("generated_grids", 0),
        "query_rotations": report["counts"].get("query_rotations", 0),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
