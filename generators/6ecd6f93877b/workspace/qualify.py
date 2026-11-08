#!/usr/bin/env python3
"""Fast source-local qualification probe for generator 6ecd6f93877b.

This is intentionally cheaper than the Racket-backed battery.  It checks the
observable axis contract, alternating curriculum windows, all query rotations,
canonical-fitting declared shortcuts, replay determinism, and the canonical
shrink relation.  It uses the generator's Python mirror only; run the official
battery and lesson census for retained authority-backed evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import load_generator

TASK_ID = "6ecd6f93877b"
_BANDS = (None, "easy", "medium", "hard")
_EXACT_CASES = (
    {"grid_h": 5, "grid_w": 5, "n_colors": 2, "max_count": 1},
    {"grid_h": 7, "grid_w": 9, "n_colors": 3, "max_count": 3},
    {"grid_h": 10, "grid_w": 10, "n_colors": 5, "max_count": 4},
)


def _source_hash(module: Any) -> str | None:
    source = getattr(module, "__file__", None)
    if not source:
        return None
    path = Path(source)
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pair(module: Any, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": module.rule_mirror(grid)}


def _canonical_shortcut_results(module: Any) -> dict[str, Any]:
    try:
        from reviewer_support import canonical_pairs, find_root

        pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return {"status": "unavailable", "error": repr(exc)}

    fits: dict[str, bool] = {}
    for name, rival in module.CANONICAL_SHORTCUTS.items():
        fits[name] = all(rival(pair["input"]) == pair["output"] for pair in pairs)
    return {"status": "checked", "pair_count": len(pairs), "fits": fits}


def qualify_generator(module: Any, *, starts_per_band: int = 20) -> dict[str, Any]:
    if type(starts_per_band) is not int or starts_per_band < 1:
        raise ValueError("starts_per_band must be a positive integer")

    failures: list[dict[str, Any]] = []
    draws = 0
    canonical_anchors = 0
    shortcut_witnesses = 0
    rotation_checks = 0
    exact_checks = 0
    unique_inputs: set[str] = set()

    def fail(kind: str, **detail: Any) -> None:
        failures.append({"kind": kind, **detail})

    for band_index, band in enumerate(_BANDS):
        for window in range(starts_per_band):
            seed = 700_000 + band_index * 10_000 + window
            # Consecutive starts exercise both parity phases of the schedule.
            start = window
            grids: list[list[list[int]]] = []
            pairs: list[dict[str, list[list[int]]]] = []
            for sample_index in range(start, start + 4):
                grid = module.generate(seed, sample_index, difficulty=band)
                replay = module.generate(seed, sample_index, difficulty=band)
                draws += 1
                grids.append(grid)
                pairs.append(_pair(module, grid))
                unique_inputs.add(
                    hashlib.sha256(
                        json.dumps(grid, separators=(",", ":")).encode("utf-8")
                    ).hexdigest()
                )

                errors = module.self_check(grid)
                if errors:
                    fail(
                        "self_check",
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                        errors=errors,
                    )
                if grid != replay:
                    fail(
                        "nondeterministic_replay",
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                    )
                output = module.rule_mirror(grid)
                if len(output) != 1 or len(output[0]) > len(grid[0]):
                    fail(
                        "shape_relation",
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                        input_shape=[len(grid), len(grid[0])],
                        output_shape=[len(output), len(output[0]) if output else None],
                    )

                profile = module.schedule_profile(seed, sample_index, band)
                if profile == "canonical_anchor":
                    canonical_anchors += 1
                    strict_errors = module.strict_canonical_like(grid)
                    if strict_errors:
                        fail(
                            "canonical_anchor_off_profile",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            errors=strict_errors,
                        )
                elif profile == "shortcut_witness":
                    shortcut_witnesses += 1
                    for witness_name, predicate in module.SEMANTIC_WITNESSES.items():
                        if not predicate(grid):
                            fail(
                                "missing_witness",
                                witness=witness_name,
                                band=band,
                                seed=seed,
                                sample_index=sample_index,
                            )
                    for rival_name, rival in module.SEMANTIC_RIVALS.items():
                        if rival(grid) == output:
                            fail(
                                "unrefuted_rival",
                                rival=rival_name,
                                band=band,
                                seed=seed,
                                sample_index=sample_index,
                            )
                else:
                    fail(
                        "unknown_schedule_profile",
                        profile=profile,
                        band=band,
                        seed=seed,
                        sample_index=sample_index,
                    )

            for query_index, query in enumerate(pairs):
                rotation_checks += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    fail(
                        "ambiguous_rotation",
                        band=band,
                        seed=seed,
                        start=start,
                        query_index=query_index,
                        reasons=reasons,
                    )

    for band in _BANDS:
        for case_index, overrides in enumerate(_EXACT_CASES):
            grid = module.generate(
                900_000 + case_index,
                13,
                difficulty=band,
                **overrides,
            )
            exact_checks += 1
            observed = module.observe_overrides(grid)
            if observed != overrides:
                fail(
                    "override_mismatch",
                    band=band,
                    requested=overrides,
                    observed=observed,
                )
            errors = module.self_check(grid)
            if errors:
                fail(
                    "override_off_domain",
                    band=band,
                    requested=overrides,
                    errors=errors,
                )

    canonical_shortcuts = _canonical_shortcut_results(module)
    if canonical_shortcuts.get("status") == "checked":
        for name, fits in canonical_shortcuts["fits"].items():
            if not fits:
                fail("declared_shortcut_does_not_fit_canonical", rival=name)

    return {
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "source_sha256": _source_hash(module),
        "starts_per_band": starts_per_band,
        "start_indices": list(range(starts_per_band)),
        "bands": ["none" if band is None else band for band in _BANDS],
        "draws": draws,
        "unique_inputs": len(unique_inputs),
        "canonical_anchors": canonical_anchors,
        "shortcut_witnesses": shortcut_witnesses,
        "rotation_checks": rotation_checks,
        "exact_checks": exact_checks,
        "canonical_shortcuts": canonical_shortcuts,
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", help="alternate generator.py path")
    parser.add_argument("--starts-per-band", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    module = load_generator(args.generator)
    report = qualify_generator(module, starts_per_band=args.starts_per_band)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
