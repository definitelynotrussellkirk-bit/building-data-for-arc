#!/usr/bin/env python3
"""Bounded deterministic self-review for the 7e03da0eb439 family.

The probe pressure-tests the sampler, the finite rival certificate, matched
inputs, count invariance, and maximum geometry.  Protected Racket execution is
performed independently by the native authoring preflight retained alongside
this source-local receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "prototype.py"
SETTINGS = ("color_2", "center_cue")
DEMO_COUNTS = (2, 3, 4, 5, 6)
DEFAULT_SEEDS = (0, 1, 2, 9, 17, 23, 100)


def load_prototype():
    spec = importlib.util.spec_from_file_location("_7e03_probe_prototype", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load adjacent prototype")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(episode: dict[str, Any], split: str) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode[split]]


def _shape(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0])]


def _quadrant_nonzero(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    row_cuts = (0, h // 2, h)
    col_cuts = (0, w // 2, w)
    return [
        sum(
            grid[r][c] != 0
            for r in range(row_cuts[ri], row_cuts[ri + 1])
            for c in range(col_cuts[ci], col_cuts[ci + 1])
        )
        for ri in range(2)
        for ci in range(2)
    ]


def _teaching_pair_coordinate_certificate(prototype, seed: int) -> bool:
    first, second = prototype._all_train_inputs(seed)[:2]
    center = (len(first) // 2, len(first[0]) // 2)
    color_two_positions = []
    cue_positions = []
    for grid in (first, second):
        cue = grid[len(grid) // 2][len(grid[0]) // 2]
        color_two_positions.append(
            {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
        )
        cue_positions.append(
            {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == cue}
        )
    return (
        color_two_positions[0].isdisjoint(color_two_positions[1])
        and cue_positions[0] & cue_positions[1] == {center}
    )


def build_study(prototype=None, *, seeds: list[int] | tuple[int, ...] = DEFAULT_SEEDS) -> dict[str, Any]:
    p = prototype or load_prototype()
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    matched_inputs = True
    prefix_stable = True
    all_rivals_rejected = True
    max_input_shape = [0, 0]
    max_output_shape = [0, 0]
    teaching_pair_coordinate_certificate_passed = True

    for seed in seeds:
        teaching_pair_coordinate_certificate_passed = (
            teaching_pair_coordinate_certificate_passed
            and _teaching_pair_coordinate_certificate(p, seed)
        )
        for demos in DEMO_COUNTS:
            episodes: dict[str, dict[str, Any]] = {}
            for mode in SETTINGS:
                try:
                    settings = {"trigger_mode": mode}
                    episode = p.generate(seed, settings, demos, 4)
                    prefix = p.generate(seed, settings, demos, 1)
                    report = p.teaching_report(episode["train"], settings)
                    stable = (
                        prefix["train"] == episode["train"]
                        and prefix["test"] == episode["test"][:1]
                    )
                    rejected = (
                        report["setting_survivors"] == [mode]
                        and report["plausible_rival_survivors"] == []
                    )
                    prefix_stable = prefix_stable and stable
                    all_rivals_rejected = all_rivals_rejected and rejected
                    episodes[mode] = episode

                    for pair in episode["test"]:
                        input_shape = _shape(pair["input"])
                        output_shape = _shape(pair["output"])
                        if input_shape[0] * input_shape[1] > max_input_shape[0] * max_input_shape[1]:
                            max_input_shape = input_shape
                        if output_shape[0] * output_shape[1] > max_output_shape[0] * max_output_shape[1]:
                            max_output_shape = output_shape

                    final_pair = episode["test"][-1]
                    cue = final_pair["input"][len(final_pair["input"]) // 2][len(final_pair["input"][0]) // 2]
                    rows.append(
                        {
                            "seed": seed,
                            "trigger_mode": mode,
                            "demos": demos,
                            "queries": 4,
                            "query_input_shapes": [_shape(x["input"]) for x in episode["test"]],
                            "query_output_shapes": [_shape(x["output"]) for x in episode["test"]],
                            "final_query_center_cue": cue,
                            "final_output_quadrant_nonzero": _quadrant_nonzero(final_pair["output"]),
                            "setting_survivors": report["setting_survivors"],
                            "plausible_rival_survivors": report["plausible_rival_survivors"],
                            "query_prefix_stable": stable,
                            "status": "passed" if stable and rejected else "failed",
                        }
                    )
                except Exception as exc:
                    failures.append(
                        {
                            "seed": seed,
                            "trigger_mode": mode,
                            "demos": demos,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
            if set(episodes) == set(SETTINGS):
                same = all(
                    _inputs(episodes[SETTINGS[0]], split)
                    == _inputs(episodes[SETTINGS[1]], split)
                    for split in ("train", "test")
                )
                matched_inputs = matched_inputs and same

    successes = sum(row["status"] == "passed" for row in rows)
    return {
        "schema": "7e03da0eb439-parametric-self-review-v1",
        "scope": "Bounded Python sampler/teaching review; native preflight supplies protected-Racket execution.",
        "settings": list(SETTINGS),
        "seeds": list(seeds),
        "demo_counts": list(DEMO_COUNTS),
        "queries_per_job": 4,
        "jobs": len(seeds) * len(SETTINGS) * len(DEMO_COUNTS),
        "successes": successes,
        "failures": failures,
        "matched_inputs_across_settings": matched_inputs,
        "query_prefix_stable": prefix_stable,
        "all_declared_rivals_rejected": all_rivals_rejected,
        "declared_rival_count": len(p.RIVALS),
        "rival_family_counts": {
            "fixed_anchor_cue": len(p.ANCHOR_CUE_RIVALS),
            "fixed_color": sum(name.startswith("fixed_color_") for name in p.RIVALS),
            "global_or_line_mode": len(p.MODE_RIVALS),
            "other": len(p.RIVALS)
            - len(p.ANCHOR_CUE_RIVALS)
            - len(p.MODE_RIVALS)
            - sum(name.startswith("fixed_color_") for name in p.RIVALS),
        },
        "teaching_pair_coordinate_certificate_passed": teaching_pair_coordinate_certificate_passed,
        "max_input_shape": max_input_shape,
        "max_output_shape": max_output_shape,
        "source_sha256": {
            name: _sha256(HERE / name)
            for name in (
                "prototype.py",
                "adapter.py",
                "promotion.json",
                "canonical.rkt",
                "center_cue.rkt",
            )
        },
        "rows": rows,
        "limits": [
            "Finite rival bank and seven deterministic audit seeds by default; not a universal uniqueness proof.",
            "Python labels are claims here; protected Racket execution is delegated to review_base_preflight.",
            "Self-tile maps an n-by-n input to n-squared by n-squared, so the largest lawful odd input is 5-by-5 and yields 25-by-25 rather than 30-by-30.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_study(seeds=args.seeds or DEFAULT_SEEDS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        key: report[key]
        for key in ("jobs", "successes", "failures", "max_input_shape", "max_output_shape")
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if not failures_from(report) else 1


def failures_from(report: dict[str, Any]) -> list[Any]:
    if report["failures"]:
        return list(report["failures"])
    if report["successes"] != report["jobs"]:
        return ["not every bounded job passed"]
    if not report["matched_inputs_across_settings"]:
        return ["settings changed sampled inputs"]
    if not report["query_prefix_stable"]:
        return ["query prefix changed with requested count"]
    if not report["all_declared_rivals_rejected"]:
        return ["a declared rival survived"]
    if not report["teaching_pair_coordinate_certificate_passed"]:
        return ["the paired teaching-coordinate certificate failed"]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
