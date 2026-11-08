#!/usr/bin/env python3
"""Reproducible deep probe for generator 865e48425b05.

This task-local tool complements the shared battery.  It exhausts the complete
joint exact-axis cross-product, checks every query rotation for a caller-chosen
set of cyclic schedule starts, verifies the public canonical shortcut contract,
and can compare an independent Python oracle with the selected Racket authority.
It imports only public generator hooks plus ``reference_probe``'s independent
oracle, making it useful for later reviewers after this patch is integrated.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from reference_probe import (
    MASKS,
    TASK_ID,
    canonical_pairs,
    fixed_3x3_rival,
    load_generator,
    observed_axes,
    racket_outputs,
    reference_output,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _labelled(grid: list[list[int]]) -> dict:
    return {"input": deepcopy(grid), "output": reference_output(grid)}


def _bounded_append(rows: list[dict], row: dict, limit: int = 32) -> None:
    if len(rows) < limit:
        rows.append(row)


def _axis_matrix(gen, difficulties: Sequence[object]) -> dict:
    failures: list[dict] = []
    checked = 0
    for difficulty in difficulties:
        for h in range(7, 11):
            for w in range(9, 15):
                for n_palette in range(2, 5):
                    for mask_id in range(len(MASKS)):
                        requested = {
                            "grid_h": h,
                            "grid_w": w,
                            "n_palette": n_palette,
                            "mask_id": mask_id,
                        }
                        seed = 700_000 + checked
                        sample_index = checked % 97
                        checked += 1
                        try:
                            grid = gen.generate(
                                seed,
                                sample_index,
                                difficulty=difficulty,
                                **requested,
                            )
                            errors = gen.self_check(
                                grid,
                                difficulty=difficulty,
                                meta={"overrides": requested},
                            )
                            observed = observed_axes(grid)
                            public_observed = gen.observe_overrides(grid)
                            if errors or observed != requested or public_observed != requested:
                                _bounded_append(
                                    failures,
                                    {
                                        "difficulty": difficulty,
                                        "requested": requested,
                                        "errors": errors,
                                        "independent_observed": observed,
                                        "public_observed": public_observed,
                                    },
                                )
                        except Exception as exc:  # retained as evidence, not hidden
                            _bounded_append(
                                failures,
                                {
                                    "difficulty": difficulty,
                                    "requested": requested,
                                    "exception": f"{type(exc).__name__}: {exc}",
                                },
                            )
    return {
        "difficulties": list(difficulties),
        "checked": checked,
        "failures": failures,
    }


def _canonical_contract(gen) -> dict:
    failures: list[dict] = []
    pairs = canonical_pairs()
    shortcut_names = sorted(gen.CANONICAL_SHORTCUTS)
    for index, pair in enumerate(pairs):
        expected = reference_output(pair["input"])
        if expected != pair["output"]:
            _bounded_append(failures, {"pair": index, "failure": "independent oracle mismatch"})
        errors = gen.self_check(pair["input"])
        strict_errors = gen.strict_canonical_like(pair["input"])
        if errors or strict_errors:
            _bounded_append(
                failures,
                {
                    "pair": index,
                    "failure": "canonical input rejected",
                    "self_check": errors,
                    "strict": strict_errors,
                },
            )
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            original = deepcopy(pair["input"])
            rival_output = rival(original)
            if original != pair["input"] or rival_output != pair["output"]:
                _bounded_append(
                    failures,
                    {
                        "pair": index,
                        "rival": name,
                        "failure": "declared canonical shortcut is impure or does not fit",
                    },
                )
        if fixed_3x3_rival(pair["input"]) != pair["output"]:
            _bounded_append(
                failures,
                {"pair": index, "failure": "independent fixed-3x3 shortcut does not fit"},
            )
    return {
        "pairs_checked": len(pairs),
        "declared_shortcuts": shortcut_names,
        "failures": failures,
    }


def _cyclic_lessons(gen, starts: Iterable[int]) -> dict:
    starts = list(starts)
    failures: list[dict] = []
    starts_checked = 0
    rotations_checked = 0
    bands = ("easy", "medium", "hard")
    for band in bands:
        for start in starts:
            starts_checked += 1
            grids = [
                gen.generate(2_026_1005, start + offset, difficulty=band)
                for offset in range(4)
            ]
            pairs = [_labelled(grid) for grid in grids]
            for query_index, query in enumerate(pairs):
                rotations_checked += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                unrefuted = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if not any(rival(demo["input"]) != demo["output"] for demo in demos)
                    and rival(query["input"]) != query["output"]
                ]
                if reasons or unrefuted:
                    _bounded_append(
                        failures,
                        {
                            "difficulty": band,
                            "start": start,
                            "query_index": query_index,
                            "lesson_identifiable": reasons,
                            "unrefuted_query_disagreeing_rivals": unrefuted,
                        },
                    )
    return {
        "bands": list(bands),
        "requested_starts_per_band": len(starts),
        "starts_checked": starts_checked,
        "rotations_checked": rotations_checked,
        "failures": failures,
    }


def _racket_parity(gen) -> dict:
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(64_000, index, difficulty="hard") for index in range(24))
    expected = [reference_output(grid) for grid in grids]
    try:
        actual = racket_outputs(grids)
    except Exception as exc:
        return {
            "checked": 0,
            "failures": [{"exception": f"{type(exc).__name__}: {exc}"}],
        }
    mismatches = [index for index, (left, right) in enumerate(zip(expected, actual)) if left != right]
    return {"checked": len(grids), "mismatch_indices": mismatches, "failures": [] if not mismatches else [{"mismatch_indices": mismatches}]}


def run_probe(
    *,
    axis_difficulties: Sequence[object] = (None, "easy", "medium", "hard"),
    cyclic_starts: Iterable[int] = range(48),
    include_racket: bool = True,
) -> dict:
    gen = load_generator()
    source = Path(gen.__file__).resolve()
    report = {
        "schema": "865e48425b05-review-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(source),
        "rule_hash": gen.RULE_HASH,
        "axis_matrix": _axis_matrix(gen, tuple(axis_difficulties)),
        "canonical_contract": _canonical_contract(gen),
        "cyclic_lessons": _cyclic_lessons(gen, cyclic_starts),
    }
    if include_racket:
        report["racket_parity"] = _racket_parity(gen)
    failure_groups = [
        value.get("failures", [])
        for key, value in report.items()
        if isinstance(value, dict) and key not in {"schema"}
    ]
    report["status"] = "pass" if all(not rows for rows in failure_groups) else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cyclic-starts", type=int, default=48)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args()
    report = run_probe(
        cyclic_starts=range(args.cyclic_starts),
        include_racket=not args.no_racket,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "axis_checked": report["axis_matrix"]["checked"],
        "cyclic_starts_checked": report["cyclic_lessons"]["starts_checked"],
        "rotations_checked": report["cyclic_lessons"]["rotations_checked"],
        "out": str(args.out),
    }, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
