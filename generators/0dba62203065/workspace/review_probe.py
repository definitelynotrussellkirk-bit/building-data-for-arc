#!/usr/bin/env python3
"""Focused, reusable contract probe for ARC generator 0dba62203065.

This deliberately uses only the generator's public review hooks plus the
canonical JSONL record.  It is faster and more diagnostic than the full
battery, so future reviewers can run it before launching expensive checks.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import product
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


WORKSPACE = Path(__file__).resolve().parent
TASK_DIR = WORKSPACE.parent
REPO_ROOT = TASK_DIR.parents[1]
SRC_ROOT = REPO_ROOT / "src"
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
for path in (REPO_ROOT, SRC_ROOT, RUNTIME_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _load_generator() -> Any:
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_0dba62203065_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_canonical(task_id: str) -> dict[str, Any]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == task_id:
                return record
    raise RuntimeError(f"canonical task {task_id!r} not found in {path}")


def _positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _failure(failures: list[str], message: str) -> None:
    failures.append(message)


def run_probe(samples_per_band: int = 12) -> dict[str, Any]:
    """Run focused canonical, randomized, semantic, and override checks."""
    if samples_per_band <= 0:
        raise ValueError("samples_per_band must be a positive integer")

    gen = _load_generator()
    canonical = _load_canonical(gen.TASK_ID)
    failures: list[str] = []

    public_pairs = [*canonical.get("train", []), *canonical.get("test", [])]
    parity_passed = 0
    public_inputs_valid = 0
    first_cell_train_fits = True
    first_cell_test_refuted = False
    size_shortcut_all_public_fits = True
    cycle_shortcut_all_public_fits = True

    for index, pair in enumerate(public_pairs):
        input_grid = pair["input"]
        expected = pair["output"]
        errors = gen.self_check(input_grid)
        if errors:
            _failure(failures, f"canonical pair {index} rejected: {errors[0]}")
        else:
            public_inputs_valid += 1

        actual = gen.rule_mirror(input_grid)
        if actual != expected:
            _failure(failures, f"canonical pair {index} mirror mismatch")
        else:
            parity_passed += 1

        first_prediction = gen.SEMANTIC_RIVALS["first_cell_column"](input_grid)
        if index < len(canonical.get("train", [])):
            first_cell_train_fits &= first_prediction == expected
        else:
            first_cell_test_refuted |= first_prediction != expected
        size_shortcut_all_public_fits &= (
            gen.SEMANTIC_RIVALS["size_at_most_three"](input_grid) == expected
        )
        cycle_shortcut_all_public_fits &= (
            gen.SEMANTIC_RIVALS["cycle_from_first_two"](input_grid) == expected
        )

    if parity_passed != len(public_pairs):
        _failure(failures, "not every canonical pair matches rule_mirror")
    if public_inputs_valid != len(public_pairs):
        _failure(failures, "not every canonical input satisfies the reviewed grammar")
    if not first_cell_train_fits:
        _failure(failures, "first-cell rival does not fit every canonical demonstration")
    if not first_cell_test_refuted:
        _failure(failures, "canonical query does not refute the first-cell rival")
    if not size_shortcut_all_public_fits:
        _failure(failures, "size<=3 shortcut no longer fits every public pair")
    if not cycle_shortcut_all_public_fits:
        _failure(failures, "cycle-from-first-two shortcut no longer fits every public pair")

    bands = ("easy", "medium", "hard")
    generated_by_band: dict[str, list[dict[str, Any]]] = {band: [] for band in bands}
    input_hashes_by_band: dict[str, set[str]] = {band: set() for band in bands}
    all_input_hashes: set[str] = set()
    legend_profile_counts = {name: 0 for name in gen.LEGEND_PROFILES}
    witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    rival_refutations = {name: 0 for name in gen.LESSON_COMPETITORS}
    random_cases = 0

    for band_index, band in enumerate(bands):
        for sample_index in range(samples_per_band):
            seed = 100_000 + band_index * 10_000 + sample_index
            label = f"{band}/seed={seed}/sample={sample_index}"
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:  # pragma: no cover - failure reporting path
                _failure(failures, f"{label}: generate raised {type(exc).__name__}: {exc}")
                continue
            random_cases += 1

            errors = gen.self_check(grid, difficulty=band)
            if errors:
                _failure(failures, f"{label}: self_check: {errors[0]}")
                continue

            try:
                observed = gen.observe_overrides(grid)
                legend_profile = gen.observe_legend_profile(grid)
            except Exception as exc:  # pragma: no cover - failure reporting path
                _failure(failures, f"{label}: observe_overrides raised: {exc}")
                continue

            expected_h, expected_w = gen._CANONICAL_DIMENSIONS[sample_index % 3]
            expected_schedule = {
                "grid_h": expected_h,
                "grid_w": expected_w,
                "body_origin": 2 if sample_index % 2 == 0 else 1,
                "blob_profile": gen.schedule_profile(seed, sample_index, band),
            }
            for axis, expected in expected_schedule.items():
                if observed.get(axis) != expected:
                    _failure(
                        failures,
                        f"{label}: scheduled {axis}={expected!r}, observed {observed.get(axis)!r}",
                    )
            expected_legend_profile = gen.schedule_legend_profile(seed, sample_index, band)
            if legend_profile != expected_legend_profile:
                _failure(
                    failures,
                    f"{label}: scheduled legend_profile={expected_legend_profile!r}, "
                    f"observed {legend_profile!r}",
                )

            encoded = json.dumps(grid, separators=(",", ":")).encode("utf-8")
            input_hash = hashlib.sha256(encoded).hexdigest()
            input_hashes_by_band[band].add(input_hash)
            all_input_hashes.add(input_hash)
            if legend_profile in legend_profile_counts:
                legend_profile_counts[legend_profile] += 1
            else:
                _failure(failures, f"{label}: unknown legend_profile {legend_profile!r}")

            truth = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_counts[name] += 1
            for name, rival in gen.LESSON_COMPETITORS.items():
                if rival(grid) != truth:
                    rival_refutations[name] += 1

            generated_by_band[band].append({"input": grid, "output": truth})

    expected_random_cases = len(bands) * samples_per_band
    if random_cases != expected_random_cases:
        _failure(
            failures,
            f"generated {random_cases}/{expected_random_cases} randomized cases",
        )

    easy_hard_contrasts = 0
    easy_hard_differences = 0
    for sample_index in range(samples_per_band):
        seed = 500_000 + sample_index
        easy = gen.generate(seed, sample_index, difficulty="easy")
        hard = gen.generate(seed, sample_index, difficulty="hard")
        easy_hard_contrasts += 1
        if easy != hard:
            easy_hard_differences += 1
        else:
            _failure(
                failures,
                f"difficulty dead control at seed={seed}, sample={sample_index}: easy == hard",
            )

    # Strong contract expectations, not merely descriptive counters.
    for rival in ("first_cell_column", "per_cell_column"):
        if rival_refutations[rival] != random_cases:
            _failure(
                failures,
                f"rival {rival!r} refuted on {rival_refutations[rival]}/{random_cases} cases",
            )
    expected_alternating = len(bands) * (samples_per_band // 2)
    for rival in ("skip_row_one", "size_at_most_three", "cycle_from_first_two"):
        if rival_refutations[rival] != expected_alternating:
            _failure(
                failures,
                f"rival {rival!r} refuted on {rival_refutations[rival]}/{expected_alternating} expected cases",
            )

    two_demo_windows = 0
    for band, pairs in generated_by_band.items():
        for start in range(max(0, len(pairs) - 1)):
            demos = pairs[start : start + 2]
            query = pairs[(start + 2) % len(pairs)]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                _failure(
                    failures,
                    f"{band} two-demo window {start}:{start + 2} not identifiable: {reasons[0]}",
                )
            two_demo_windows += 1

    boundary_values = {
        "grid_h": (8, 12),
        "grid_w": (10, 13),
        "header_start": (2, 8),
        "header_direction": ("ascending", "descending"),
        "body_origin": (1, 2),
        "blob_profile": ("canonical", "extended"),
    }
    axes = tuple(boundary_values)
    boundary_cases = 0
    for case_index, values in enumerate(product(*(boundary_values[name] for name in axes))):
        overrides = dict(zip(axes, values, strict=True))
        label = f"override-case={case_index}"
        try:
            grid = gen.generate(900_000 + case_index, case_index, **overrides)
            observed = gen.observe_overrides(grid)
        except Exception as exc:  # pragma: no cover - failure reporting path
            _failure(failures, f"{label}: raised {type(exc).__name__}: {exc}")
            continue
        boundary_cases += 1
        if any(observed.get(axis) != expected for axis, expected in overrides.items()):
            _failure(failures, f"{label}: expected {overrides}, observed {observed}")

    unknown_override_rejected = False
    try:
        gen.generate(1, 0, definitely_not_an_axis=True)
    except ValueError:
        unknown_override_rejected = True
    except Exception as exc:  # pragma: no cover - failure reporting path
        _failure(failures, f"unknown override raised {type(exc).__name__}, expected ValueError")
    if not unknown_override_rejected:
        _failure(failures, "unknown override was accepted")

    return {
        "status": "pass" if not failures else "fail",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "canonical": {
            "pairs_checked": len(public_pairs),
            "inputs_valid": public_inputs_valid,
            "parity_passed": parity_passed,
            "first_cell_rival_fits_all_train": first_cell_train_fits,
            "first_cell_rival_refuted_by_test": first_cell_test_refuted,
            "size_at_most_three_fits_all_public": size_shortcut_all_public_fits,
            "cycle_from_first_two_fits_all_public": cycle_shortcut_all_public_fits,
        },
        "randomized": {
            "bands": list(bands),
            "samples_per_band": samples_per_band,
            "cases_checked": random_cases,
            "sampler": {
                "seed_formula": "100000 + band_index*10000 + sample_index",
                "sample_index_range": f"0..{samples_per_band - 1}",
            },
            "unique_inputs_by_band": {
                band: len(input_hashes_by_band[band]) for band in bands
            },
            "overall_unique_inputs": len(all_input_hashes),
            "legend_profile_counts": legend_profile_counts,
            "witness_counts": witness_counts,
            "rival_refutations": rival_refutations,
            "two_demo_windows_checked": two_demo_windows,
            "easy_hard_contrasts_checked": easy_hard_contrasts,
            "easy_hard_differences": easy_hard_differences,
        },
        "overrides": {
            "boundary_cases_checked": boundary_cases,
            "unknown_override_rejected": unknown_override_rejected,
        },
        "failures": failures,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples-per-band",
        type=_positive_int,
        default=12,
        help="deterministic randomized cases per difficulty band (default: 12)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="also write the JSON report to this path",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = run_probe(samples_per_band=args.samples_per_band)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
