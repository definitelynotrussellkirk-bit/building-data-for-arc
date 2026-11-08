#!/usr/bin/env python3
"""Bounded family review for the ``eb3171637821`` native adapter.

This is deliberately a finite audit, not a proof over all integer seeds.  It
checks deterministic generation, matched inputs, declared-setting
identifiability, selected shortcut rivals, a 30x30 stress profile, and optional
protected-Racket agreement over explicitly reported seeds.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE.parent / "prototype.py"
MODULE_NAME = "parametric_eb3171637821_family_review_source"
DEMO_COUNTS = (2, 3, 6)
QUERY_COUNTS = (1, 4)
FINITE_LIMIT = (
    "Findings apply only to the enumerated seeds, counts, settings, and rivals."
)


def _load_prototype():
    module = sys.modules.get(MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(MODULE_NAME, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype from {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _racket_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _protected_racket_check(seeds: list[int], failures: list[dict[str, Any]]) -> int:
    if not seeds:
        return 0
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    evaluations = 0
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        for seed in seeds:
            for encoding in PROTOTYPE.ENCODINGS:
                episode = PROTOTYPE.generate_episode(
                    seed, encoding=encoding, demos=3, queries=4
                )
                wrapped = wrap_rule(episode["program_solution"])
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = bridge.eval_text(
                            f"({wrapped} {_racket_literal(pair['input'])})"
                        )
                        evaluations += 1
                        if actual != pair["output"]:
                            failures.append(
                                {
                                    "kind": "racket_mismatch",
                                    "seed": seed,
                                    "encoding": encoding,
                                    "split": split,
                                    "index": index,
                                }
                            )
    return evaluations


def review_family(
    *, seeds: Iterable[int], racket_seeds: Iterable[int] = (0, 17)
) -> dict[str, Any]:
    seed_list = list(seeds)
    racket_seed_list = list(racket_seeds)
    if any(type(seed) is not int or seed < 0 for seed in seed_list + racket_seed_list):
        raise ValueError("review seeds must be nonnegative literal integers")
    if len(seed_list) != len(set(seed_list)) or len(racket_seed_list) != len(
        set(racket_seed_list)
    ):
        raise ValueError("review seed lists must not contain duplicates")

    failures: list[dict[str, Any]] = []
    counts = {
        "episodes": 0,
        "examples": 0,
        "matched_setting_comparisons": 0,
        "stress_30x30": 0,
        "racket_evaluations": 0,
        "demo_identifiability_checks": 0,
        "shortcut_rivals_tested": 0,
    }
    dimension_bounds = {"min_rows": 31, "max_rows": 0, "min_cols": 31, "max_cols": 0}
    setting_examples = {encoding: 0 for encoding in PROTOTYPE.ENCODINGS}
    rival_names = {encoding: set() for encoding in PROTOTYPE.ENCODINGS}

    for seed in seed_list:
        for demos in DEMO_COUNTS:
            for queries in QUERY_COUNTS:
                episodes = {
                    encoding: PROTOTYPE.generate_episode(
                        seed, encoding=encoding, demos=demos, queries=queries
                    )
                    for encoding in PROTOTYPE.ENCODINGS
                }
                for encoding, episode in episodes.items():
                    counts["episodes"] += 1
                    duplicate = PROTOTYPE.generate_episode(
                        seed, encoding=encoding, demos=demos, queries=queries
                    )
                    if episode != duplicate:
                        failures.append(
                            {
                                "kind": "nondeterministic_episode",
                                "seed": seed,
                                "encoding": encoding,
                                "demos": demos,
                                "queries": queries,
                            }
                        )
                    examples = episode["train"] + episode["test"]
                    counts["examples"] += len(examples)
                    setting_examples[encoding] += len(examples)
                    keys = [_grid_key(pair["input"]) for pair in examples]
                    if len(keys) != len(set(keys)):
                        failures.append(
                            {
                                "kind": "duplicate_inputs",
                                "seed": seed,
                                "encoding": encoding,
                                "demos": demos,
                                "queries": queries,
                            }
                        )
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            height, width = len(pair["input"]), len(pair["input"][0])
                            dimension_bounds["min_rows"] = min(
                                dimension_bounds["min_rows"], height
                            )
                            dimension_bounds["max_rows"] = max(
                                dimension_bounds["max_rows"], height
                            )
                            dimension_bounds["min_cols"] = min(
                                dimension_bounds["min_cols"], width
                            )
                            dimension_bounds["max_cols"] = max(
                                dimension_bounds["max_cols"], width
                            )
                            expected = PROTOTYPE.output_for(pair["input"], encoding)
                            if pair["output"] != expected:
                                failures.append(
                                    {
                                        "kind": "oracle_label_mismatch",
                                        "seed": seed,
                                        "encoding": encoding,
                                        "split": split,
                                        "index": index,
                                    }
                                )
                            if height == width == 30:
                                counts["stress_30x30"] += 1

                    assessment = PROTOTYPE.assess_demos(
                        episode["train"], encoding
                    )
                    counts["demo_identifiability_checks"] += 1
                    rivals = assessment["tested_shortcuts"]
                    counts["shortcut_rivals_tested"] += len(rivals)
                    rival_names[encoding].update(rivals)
                    if assessment["declared_setting_survivors"] != [encoding]:
                        failures.append(
                            {
                                "kind": "declared_setting_not_identified",
                                "seed": seed,
                                "encoding": encoding,
                                "demos": demos,
                                "survivors": assessment[
                                    "declared_setting_survivors"
                                ],
                            }
                        )
                    if assessment["shortcut_survivors"]:
                        failures.append(
                            {
                                "kind": "shortcut_survived",
                                "seed": seed,
                                "encoding": encoding,
                                "demos": demos,
                                "survivors": assessment["shortcut_survivors"],
                            }
                        )

                left, right = (episodes[name] for name in PROTOTYPE.ENCODINGS)
                for split in ("train", "test"):
                    for index, (left_pair, right_pair) in enumerate(
                        zip(left[split], right[split])
                    ):
                        counts["matched_setting_comparisons"] += 1
                        if left_pair["input"] != right_pair["input"]:
                            failures.append(
                                {
                                    "kind": "setting_dependent_input",
                                    "seed": seed,
                                    "demos": demos,
                                    "queries": queries,
                                    "split": split,
                                    "index": index,
                                }
                            )
                        if left_pair["output"] == right_pair["output"]:
                            failures.append(
                                {
                                    "kind": "setting_outputs_equal",
                                    "seed": seed,
                                    "demos": demos,
                                    "queries": queries,
                                    "split": split,
                                    "index": index,
                                }
                            )

    counts["racket_evaluations"] = _protected_racket_check(
        racket_seed_list, failures
    )
    report = {
        "schema": "arcpuzzles-parametric-family-review-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "prototype_version": PROTOTYPE.PROTOTYPE_VERSION,
        "status": "pass" if not failures else "fail",
        "scope": {
            "seeds": seed_list,
            "racket_seeds": racket_seed_list,
            "demo_counts": list(DEMO_COUNTS),
            "query_counts": list(QUERY_COUNTS),
            "finite_limit": FINITE_LIMIT,
        },
        "settings": list(PROTOTYPE.ENCODINGS),
        "counts": counts,
        "setting_examples": setting_examples,
        "input_dimension_bounds": dimension_bounds,
        "rivals": {
            encoding: sorted(names) for encoding, names in rival_names.items()
        },
        "failures": failures,
    }
    return report


def _parse_seed_spec(spec: str) -> list[int]:
    values: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            first, last = part.split("-", 1)
            values.extend(range(int(first), int(last) + 1))
        else:
            values.append(int(part))
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        default="0-19",
        help="comma-separated integers and inclusive ranges (default: 0-19)",
    )
    parser.add_argument(
        "--racket-seeds",
        default="0,17",
        help="protected-Racket spot-check seeds; empty disables (default: 0,17)",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = review_family(
        seeds=_parse_seed_spec(args.seeds),
        racket_seeds=_parse_seed_spec(args.racket_seeds),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": report["task_id"],
        "status": report["status"],
        "counts": report["counts"],
        "failures": len(report["failures"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
