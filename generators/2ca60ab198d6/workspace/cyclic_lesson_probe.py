"""Exhaust cyclic lesson starts and exact-axis boundaries for task 2ca60ab198d6.

This is review tooling, not a label authority. It evaluates the selected Python
source against its own independent rule mirror and declared rivals, while the
repository battery remains responsible for Racket parity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from itertools import product
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs

TASK_ID = "2ca60ab198d6"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
BANDS = ("easy", "medium", "hard")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"cyclic_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest_grid(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _record(failures: list[dict], kind: str, **details) -> None:
    failures.append({"kind": kind, **details})


def audit(
    *,
    seeds: Iterable[int],
    starts: Iterable[int],
    check_axes: bool = True,
) -> dict:
    """Return a deterministic source-bound audit report.

    Every requested seed/start is crossed with all three public difficulty bands.
    A lesson is four consecutive demonstrations plus the following query. Exact
    axis checking crosses all low/high integer bounds and every categorical value.
    """
    gen = _load_generator()
    seed_values = tuple(int(value) for value in seeds)
    start_values = tuple(int(value) for value in starts)
    failures: list[dict] = []
    witness_counts = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
    profile_counts = Counter({name: 0 for name in gen.SCHEDULE_PROFILES})
    rival_refutations = Counter({name: 0 for name in gen.LESSON_COMPETITORS})
    unique_inputs: set[str] = set()
    windows = 0

    pairs = canonical_pairs(TASK_ID, root=REPO_ROOT)
    shortcut_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    for name, fits in shortcut_fit.items():
        if not fits:
            _record(failures, "declared_canonical_shortcut_does_not_fit", rival=name)

    expected_profiles = set(gen.SCHEDULE_PROFILES)
    for difficulty, seed, start in product(BANDS, seed_values, start_values):
        windows += 1
        examples = []
        profiles = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            sample_index = start + offset
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            profile = gen.schedule_profile(seed, sample_index, difficulty)
            profiles.append(profile)
            profile_counts[profile] += 1
            unique_inputs.add(_digest_grid(grid))
            errors = gen.self_check(grid)
            if errors:
                _record(
                    failures,
                    "self_check",
                    difficulty=difficulty,
                    seed=seed,
                    start=start,
                    offset=offset,
                    errors=errors,
                )
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_counts[name] += 1
            examples.append({"input": grid, "output": gen.rule_mirror(grid)})

        demo_profiles = set(profiles[: gen.EXAMPLES_NEEDED])
        if demo_profiles != expected_profiles:
            _record(
                failures,
                "profile_window",
                difficulty=difficulty,
                seed=seed,
                start=start,
                profiles=profiles[: gen.EXAMPLES_NEEDED],
            )

        demos = examples[: gen.EXAMPLES_NEEDED]
        query = examples[gen.EXAMPLES_NEEDED]
        reasons = gen.lesson_identifiable(demos, query)
        if reasons:
            _record(
                failures,
                "lesson_ambiguity",
                difficulty=difficulty,
                seed=seed,
                start=start,
                reasons=reasons,
            )
        for name, rival in gen.LESSON_COMPETITORS.items():
            refuted = any(rival(pair["input"]) != pair["output"] for pair in demos)
            rival_refutations[name] += int(refuted)
            if not refuted:
                _record(
                    failures,
                    "surviving_rival",
                    difficulty=difficulty,
                    seed=seed,
                    start=start,
                    rival=name,
                )

    axis_cases = 0
    if check_axes:
        for difficulty, values in product(
            BANDS,
            product(
                (6, 10),
                (7, 11),
                (2, 4),
                ("zero_only", "nonzero_only", "mixed"),
                ("sparse", "medium", "dense"),
                (2, 8),
            ),
        ):
            axis_cases += 1
            grid_h, grid_w, n_keep, selector_style, payload_density, n_colors = values
            requested = {
                "grid_h": grid_h,
                "grid_w": grid_w,
                "n_keep": n_keep,
                "selector_style": selector_style,
                "payload_density": payload_density,
                "n_payload_colors": n_colors,
            }
            try:
                grid = gen.generate(
                    900_000 + axis_cases,
                    700_000 + axis_cases,
                    difficulty=difficulty,
                    **requested,
                )
                observed = gen.observe_overrides(grid)
                errors = gen.self_check(grid)
                if observed != requested or errors:
                    _record(
                        failures,
                        "axis_mismatch",
                        difficulty=difficulty,
                        requested=requested,
                        observed=observed,
                        errors=errors,
                    )
            except Exception as exc:  # evidence should include constructive failures
                _record(
                    failures,
                    "axis_exception",
                    difficulty=difficulty,
                    requested=requested,
                    error=f"{type(exc).__name__}: {exc}",
                )

    report = {
        "schema": "2ca60ab198d6-cyclic-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sampling": {
            "difficulty_bands": list(BANDS),
            "seeds": list(seed_values),
            "cyclic_starts": list(start_values),
            "demonstrations_per_lesson": gen.EXAMPLES_NEEDED,
            "query_offset": gen.EXAMPLES_NEEDED,
        },
        "lesson_windows": windows,
        "materialized_inputs": windows * (gen.EXAMPLES_NEEDED + 1),
        "unique_inputs": len(unique_inputs),
        "axis_cases": axis_cases,
        "canonical_pairs": len(pairs),
        "canonical_shortcuts_checked": sorted(gen.CANONICAL_SHORTCUTS),
        "canonical_shortcuts_fit": dict(sorted(shortcut_fit.items())),
        "profile_counts": dict(sorted(profile_counts.items())),
        "witness_counts": dict(sorted(witness_counts.items())),
        "rival_refuted_windows": dict(sorted(rival_refutations.items())),
        "failures": failures,
        "limitations": (
            "Finite declared-rival and boundary checks do not prove universal "
            "identifiability; Python rule_mirror is supplementary to the Racket battery."
        ),
    }
    report["passed"] = not failures
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=32, help="use seeds 0..N-1")
    parser.add_argument("--starts", type=int, default=16, help="use starts 0..N-1")
    parser.add_argument("--skip-axes", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")
    if args.out.exists():
        parser.error(f"refusing to overwrite existing output: {args.out}")

    report = audit(
        seeds=range(args.seeds),
        starts=range(args.starts),
        check_axes=not args.skip_axes,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "lesson_windows": report["lesson_windows"],
                "unique_inputs": report["unique_inputs"],
                "axis_cases": report["axis_cases"],
                "failures": len(report["failures"]),
            },
            indent=2,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
