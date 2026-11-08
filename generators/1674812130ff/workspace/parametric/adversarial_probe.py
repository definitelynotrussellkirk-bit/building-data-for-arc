#!/usr/bin/env python3
"""Bounded adversarial checks for the completion-transform prototype.

This is intentionally task-local and finite. It exercises the two surfaces named
in the review assignment without implying exhaustive semantic uniqueness.
"""
from __future__ import annotations

import argparse
import copy
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Iterable

import prototype

SCHEMA = "arcpuzzles-parametric-adversarial-probe-v1"
SURFACES = [
    "sampler_boundaries_and_parameter_racket_parity",
    "public_private_export_and_numeric_types",
]


def _is_exact_int_grid(grid: Any) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and all(isinstance(row, list) and bool(row) for row in grid)
        and all(type(cell) is int for row in grid for cell in row)
    )


def _record(findings: list[dict[str, Any]], *, seed: int, difficulty: str,
            check: str, detail: str) -> None:
    findings.append(
        {
            "seed": seed,
            "difficulty": difficulty,
            "check": check,
            "detail": detail,
        }
    )


def _validate_probe_inputs(seeds: Iterable[int], difficulties: Iterable[str]) -> tuple[list[int], list[str]]:
    seed_values = list(seeds)
    difficulty_values = list(difficulties)
    if not seed_values:
        raise ValueError("seeds must contain at least one value")
    if not difficulty_values:
        raise ValueError("difficulties must contain at least one value")
    for seed in seed_values:
        prototype._validate_seed(seed)
    allowed = {"easy", "medium", "hard"}
    if any(value not in allowed for value in difficulty_values):
        raise ValueError("difficulties may contain only easy, medium, or hard")
    if len(set(seed_values)) != len(seed_values):
        raise ValueError("seeds must be distinct")
    if len(set(difficulty_values)) != len(difficulty_values):
        raise ValueError("difficulties must be distinct")
    return seed_values, difficulty_values


def run_probe(
    *,
    seeds: Iterable[int],
    difficulties: Iterable[str],
    root: Path = prototype.ROOT,
    bridge=None,
) -> dict[str, Any]:
    """Exercise count boundaries, Racket parity, privacy, and exact cell types."""
    seed_values, difficulty_values = _validate_probe_inputs(seeds, difficulties)
    root = Path(root).resolve()
    findings: list[dict[str, Any]] = []
    counts = {
        "seed_difficulty_cases": 0,
        "episodes": 0,
        "racket_labeled_pairs": 0,
        "distinct_inputs_checked": 0,
        "public_ids_checked": 0,
    }

    context = nullcontext(bridge) if bridge is not None else prototype.RacketBridge()
    with context as active_bridge:
        for seed in seed_values:
            for difficulty in difficulty_values:
                counts["seed_difficulty_cases"] += 1
                episodes = {
                    transform: prototype.make_episode(
                        seed,
                        completion_transform=transform,
                        difficulty=difficulty,
                        train_count=1,
                        query_count=8,
                        root=root,
                        bridge=active_bridge,
                    )
                    for transform in prototype.ALLOWED_TRANSFORMS
                }
                counts["episodes"] += len(episodes)

                input_lists = {
                    transform: [
                        pair["input"] for pair in episode["train"] + episode["test"]
                    ]
                    for transform, episode in episodes.items()
                }
                canonical_inputs = input_lists[prototype.DEFAULT_TRANSFORM]
                if any(inputs != canonical_inputs for inputs in input_lists.values()):
                    _record(
                        findings,
                        seed=seed,
                        difficulty=difficulty,
                        check="parameter_independent_inputs",
                        detail="changing completion_transform changed sampled inputs",
                    )

                unique_inputs = {prototype.grid_sha256(grid) for grid in canonical_inputs}
                counts["distinct_inputs_checked"] += len(unique_inputs)
                if len(canonical_inputs) != 9 or len(unique_inputs) != 9:
                    _record(
                        findings,
                        seed=seed,
                        difficulty=difficulty,
                        check="boundary_counts_and_distinctness",
                        detail=f"expected 9 distinct inputs, got {len(unique_inputs)} of {len(canonical_inputs)}",
                    )

                public_ids: dict[str, str] = {}
                for transform, episode in episodes.items():
                    pairs = episode["train"] + episode["test"]
                    counts["racket_labeled_pairs"] += len(pairs)
                    counts["public_ids_checked"] += 1
                    if episode["ambiguities"]:
                        _record(
                            findings,
                            seed=seed,
                            difficulty=difficulty,
                            check="demonstration_identifiability",
                            detail=f"{transform} retained ambiguities: {episode['ambiguities']!r}",
                        )
                    rival = episode["parameter_rivals"][0]
                    if rival["demonstration_mismatch_indices"] != [0] or rival[
                        "query_mismatch_indices"
                    ] != list(range(8)):
                        _record(
                            findings,
                            seed=seed,
                            difficulty=difficulty,
                            check="declared_rival_witnesses",
                            detail=f"{transform} mismatch indices were {rival!r}",
                        )
                    if not all(
                        _is_exact_int_grid(pair["input"])
                        and _is_exact_int_grid(pair["output"])
                        for pair in pairs
                    ):
                        _record(
                            findings,
                            seed=seed,
                            difficulty=difficulty,
                            check="exact_integer_grid_types",
                            detail=f"{transform} emitted a non-int or bool grid cell",
                        )

                    public = prototype.public_challenge(episode)
                    if any("output" in pair for pair in public["test"]):
                        _record(
                            findings,
                            seed=seed,
                            difficulty=difficulty,
                            check="query_answer_privacy",
                            detail=f"{transform} leaked a public query answer",
                        )
                    public_id = prototype.public_id(episode)
                    public_ids[transform] = public_id

                    private_change = copy.deepcopy(episode)
                    private_change["seed"] = seed + 1_000_000
                    private_change["program"] = "private probe mutation"
                    private_change["test"][0]["output"][0][0] = (
                        private_change["test"][0]["output"][0][0] + 1
                    ) % 10
                    if prototype.public_id(private_change) != public_id:
                        _record(
                            findings,
                            seed=seed,
                            difficulty=difficulty,
                            check="private_metadata_stability",
                            detail=f"{transform} public ID depended on private material",
                        )

                    visible_change = copy.deepcopy(episode)
                    visible_change["train"][0]["output"][0][0] = (
                        visible_change["train"][0]["output"][0][0] + 1
                    ) % 10
                    if prototype.public_id(visible_change) == public_id:
                        _record(
                            findings,
                            seed=seed,
                            difficulty=difficulty,
                            check="visible_content_binding",
                            detail=f"{transform} public ID ignored a visible label mutation",
                        )

                if len(set(public_ids.values())) != len(public_ids):
                    _record(
                        findings,
                        seed=seed,
                        difficulty=difficulty,
                        check="setting_visible_in_demonstration",
                        detail="both settings produced the same public challenge ID",
                    )

    return {
        "schema": SCHEMA,
        "status": "bounded_no_findings" if not findings else "findings",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.PROTOTYPE_VERSION,
        "surfaces": SURFACES,
        "probe": {
            "seeds": seed_values,
            "difficulties": difficulty_values,
            "train_count": 1,
            "query_count": 8,
            "settings": list(prototype.ALLOWED_TRANSFORMS),
        },
        "counts": counts,
        "findings": findings,
        "limits": [
            "Finite seeds and three declared difficulty bands only.",
            "Identifiability is checked against the single declared alternate transform, not every possible program.",
            "Racket/Python parity is exercised by make_episode for every counted labeled pair.",
        ],
    }


def main(argv: list[str] | None = None, *, bridge=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", dest="seeds", action="append", type=int)
    parser.add_argument(
        "--difficulty",
        dest="difficulties",
        action="append",
        choices=("easy", "medium", "hard"),
    )
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args(argv)
    seeds = options.seeds if options.seeds is not None else [0, 17, 31]
    difficulties = (
        options.difficulties
        if options.difficulties is not None
        else ["easy", "medium", "hard"]
    )
    if options.out.exists():
        raise FileExistsError(f"output file already exists: {options.out}")
    report = run_probe(
        seeds=seeds,
        difficulties=difficulties,
        bridge=bridge,
    )
    options.out.parent.mkdir(parents=True, exist_ok=True)
    options.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"out": str(options.out), **report["counts"], "status": report["status"]}, sort_keys=True))
    return 0 if not report["findings"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
