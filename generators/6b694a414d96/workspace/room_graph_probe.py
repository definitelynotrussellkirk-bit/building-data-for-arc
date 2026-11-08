#!/usr/bin/env python3
"""Bounded source-bound probe for the 6b694a414d96 room-graph curriculum.

The probe loads the selected generator bytes from this repository, checks every
labeled canonical pair, then exercises complete three-example schedule windows
across all difficulty bands.  It records exact denominators and exits nonzero
when validation, parity, schedule coverage, shortcut refutation, or finite-rival
lesson identifiability fails.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from reviewer_support import canonical_pairs, load_selected_generator  # noqa: E402


TASK_ID = "6b694a414d96"
BANDS = ("easy", "medium", "hard")


def _digest_grid(grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(body).hexdigest()


def _failure(kind: str, **details: Any) -> dict[str, Any]:
    return {"kind": kind, **details}


def run_probe(*, seeds_per_band: int = 40) -> dict[str, Any]:
    if type(seeds_per_band) is not int or seeds_per_band < 1:
        raise ValueError("seeds_per_band must be a positive integer")

    gen, source_path, source_sha256 = load_selected_generator(
        TASK_ID,
        root=REPO_ROOT,
    )
    failures: list[dict[str, Any]] = []
    canonical = canonical_pairs(TASK_ID, root=REPO_ROOT, labeled_only=True)
    accepted = 0
    for pair in canonical:
        errors = gen.self_check(pair["input"])
        mirrored = None
        try:
            mirrored = gen.rule_mirror(pair["input"])
        except Exception as exc:  # pragma: no cover - retained diagnostic path
            failures.append(
                _failure(
                    "canonical_mirror_exception",
                    split=pair["split"],
                    pair_index=pair["pair_index"],
                    exception=f"{type(exc).__name__}: {exc}",
                )
            )
        if errors:
            failures.append(
                _failure(
                    "canonical_rejected",
                    split=pair["split"],
                    pair_index=pair["pair_index"],
                    errors=errors,
                )
            )
        elif mirrored != pair["output"]:
            failures.append(
                _failure(
                    "canonical_parity_mismatch",
                    split=pair["split"],
                    pair_index=pair["pair_index"],
                )
            )
        else:
            accepted += 1

    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        if not all(shortcut(pair["input"]) == pair["output"] for pair in canonical):
            failures.append(_failure("invalid_canonical_shortcut", rival=name))

    profile_counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    generated = 0
    windows_checked = 0
    second_hop_witnesses = 0

    for difficulty in BANDS:
        for seed in range(seeds_per_band):
            demos = []
            window_profiles = []
            for sample_index in range(gen.EXAMPLES_NEEDED):
                profile = gen.schedule_profile(seed, sample_index, difficulty)
                window_profiles.append(profile)
                profile_counts[profile] += 1
                try:
                    grid = gen.generate(seed, sample_index, difficulty=difficulty)
                    errors = gen.self_check(grid)
                    output = gen.rule_mirror(grid)
                except Exception as exc:  # pragma: no cover - retained diagnostic path
                    failures.append(
                        _failure(
                            "generation_exception",
                            difficulty=difficulty,
                            seed=seed,
                            sample_index=sample_index,
                            exception=f"{type(exc).__name__}: {exc}",
                        )
                    )
                    continue
                generated += 1
                unique_inputs.add(_digest_grid(grid))
                if errors:
                    failures.append(
                        _failure(
                            "generated_rejected",
                            difficulty=difficulty,
                            seed=seed,
                            sample_index=sample_index,
                            errors=errors,
                        )
                    )
                demos.append({"input": grid, "output": output})
                if profile == "second_hop":
                    if (
                        gen.SEMANTIC_RIVALS["transitive_closure"](grid)
                        == output
                    ):
                        failures.append(
                            _failure(
                                "missing_second_hop_witness",
                                difficulty=difficulty,
                                seed=seed,
                                sample_index=sample_index,
                            )
                        )
                    else:
                        second_hop_witnesses += 1

            expected_profiles = set(gen.SCHEDULE_PROFILES)
            if set(window_profiles) != expected_profiles:
                failures.append(
                    _failure(
                        "incomplete_schedule_window",
                        difficulty=difficulty,
                        seed=seed,
                        profiles=window_profiles,
                    )
                )
            if len(demos) != gen.EXAMPLES_NEEDED:
                continue

            surviving = [
                name
                for name, rival in gen.LESSON_COMPETITORS.items()
                if all(rival(pair["input"]) == pair["output"] for pair in demos)
            ]
            if surviving:
                failures.append(
                    _failure(
                        "lesson_competitor_survived",
                        difficulty=difficulty,
                        seed=seed,
                        rivals=surviving,
                    )
                )

            query_index = gen.EXAMPLES_NEEDED
            query_grid = gen.generate(seed, query_index, difficulty=difficulty)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            generated += 1
            unique_inputs.add(_digest_grid(query_grid))
            query_errors = gen.self_check(query_grid)
            if query_errors:
                failures.append(
                    _failure(
                        "query_rejected",
                        difficulty=difficulty,
                        seed=seed,
                        sample_index=query_index,
                        errors=query_errors,
                    )
                )
            identifiable_errors = gen.lesson_identifiable(demos, query)
            if identifiable_errors:
                failures.append(
                    _failure(
                        "lesson_not_identifiable",
                        difficulty=difficulty,
                        seed=seed,
                        errors=identifiable_errors,
                    )
                )
            windows_checked += 1

    result = {
        "schema": "6b694a414d96-room-graph-probe-v1",
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(REPO_ROOT)),
        "source_sha256": source_sha256,
        "seeds_per_band": seeds_per_band,
        "bands": list(BANDS),
        "canonical_pairs": {"accepted": accepted, "total": len(canonical)},
        "canonical_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
        "lesson_competitors": sorted(gen.LESSON_COMPETITORS),
        "windows_checked": windows_checked,
        "generated_grids": generated,
        "unique_inputs": len(unique_inputs),
        "profile_counts": dict(sorted(profile_counts.items())),
        "second_hop_witnesses": second_hop_witnesses,
        "failures": failures,
        "passed": not failures,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-band", type=int, default=40)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    result = run_probe(seeds_per_band=args.seeds_per_band)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(args.output)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
