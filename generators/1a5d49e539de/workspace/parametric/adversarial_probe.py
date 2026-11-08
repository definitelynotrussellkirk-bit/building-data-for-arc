#!/usr/bin/env python3
"""Bounded adversarial probe for the proposed symmetry-axis prototype.

Attacks the two review-requested surfaces that are easiest to regress:
(1) count/retry/search-boundary behavior and (2) public/private projection,
identifier provenance, numeric types, and verifier rejection paths.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import prototype
from reviewer_support import public_challenge_bytes, public_challenge_id


def _expect_error(label: str, function: Callable[[], Any], allowed: tuple[type[BaseException], ...]) -> str:
    try:
        function()
    except allowed as exc:
        return f"{type(exc).__name__}: {exc}"
    raise AssertionError(f"{label}: expected one of {[kind.__name__ for kind in allowed]}")


def _mutate_visible_input(episode: dict[str, Any]) -> dict[str, Any]:
    changed = copy.deepcopy(episode)
    cell = changed["test"][0]["input"][0][0]
    changed["test"][0]["input"][0][0] = (cell + 1) % 10
    return changed


def run_probe() -> dict[str, Any]:
    sampler_cases = []
    max_search_attempt = 0
    total_pairs = 0
    for axis, seed in (("left-right", 1), ("top-bottom", 0)):
        for difficulty in ("easy", "medium", "hard"):
            for start_index in (0, 1, 11, 97):
                episode = prototype.build_episode(
                    seed=seed,
                    symmetry_axis=axis,
                    difficulty=difficulty,
                    start_index=start_index,
                    n_train=3,
                    n_test=4,
                    max_attempts_per_pair=128,
                )
                pairs = [*episode["train"], *episode["test"]]
                assert len(pairs) == 7
                assert len({pair["input_sha256"] for pair in pairs}) == 7
                assert prototype.parameter_rival_findings(episode) == []
                rival = prototype.other_axis(axis)
                for ordinal, pair in enumerate(pairs):
                    assert prototype.validate_input(pair["input"], axis) == []
                    assert pair["output"] == prototype.apply_python(pair["input"], axis)
                    assert pair["output"] != prototype.apply_python(pair["input"], rival)
                    assert pair["source_sample_index"] % 3 == (start_index + ordinal) % 3
                    max_search_attempt = max(max_search_attempt, pair["search_attempt"])
                total_pairs += len(pairs)
                sampler_cases.append(
                    {
                        "axis": axis,
                        "difficulty": difficulty,
                        "start_index": start_index,
                        "accepted_sample_indices": episode["meta"]["accepted_sample_indices"],
                        "max_search_attempt": max(pair["search_attempt"] for pair in pairs),
                    }
                )

    reference = prototype.build_episode(seed=1, symmetry_axis="left-right", n_train=3, n_test=4)
    public = prototype.public_challenge(reference)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    visible_bytes = public_challenge_bytes(public)
    visible_id = public_challenge_id(public)
    assert hashlib.sha256(visible_bytes).hexdigest() == visible_id

    private_mutation = copy.deepcopy(reference)
    private_mutation["meta"]["seed"] = 2**62
    private_mutation["meta"]["parameters"]["symmetry_axis"] = "top-bottom"
    private_mutation["test"][0]["output"] = [[9]]
    private_mutation["racket_source"] = "private mutation"
    assert public_challenge_id(prototype.public_challenge(private_mutation)) == visible_id
    assert public_challenge_id(prototype.public_challenge(_mutate_visible_input(reference))) != visible_id

    rejection_checks = {
        "bool_seed": _expect_error(
            "bool_seed", lambda: prototype.build_episode(seed=True), (TypeError, ValueError)
        ),
        "bool_start_index": _expect_error(
            "bool_start_index",
            lambda: prototype.build_episode(seed=1, start_index=True),
            (TypeError, ValueError),
        ),
        "float_demo_count": _expect_error(
            "float_demo_count",
            lambda: prototype.build_episode(seed=1, n_train=3.0),
            (TypeError, ValueError),
        ),
        "zero_query_count": _expect_error(
            "zero_query_count",
            lambda: prototype.build_episode(seed=1, n_test=0),
            (TypeError, ValueError),
        ),
        "bounded_search_exhaustion": _expect_error(
            "bounded_search_exhaustion",
            lambda: prototype.build_episode(
                seed=1,
                symmetry_axis="left-right",
                start_index=0,
                n_train=1,
                n_test=1,
                max_attempts_per_pair=1,
            ),
            (RuntimeError,),
        ),
        "labeler_disagreement": _expect_error(
            "labeler_disagreement",
            lambda: prototype.build_episode(
                seed=1,
                symmetry_axis="left-right",
                n_train=1,
                n_test=1,
                labeler=lambda _grid, _axis: [[0]],
            ),
            (RuntimeError,),
        ),
        "missing_public_query": _expect_error(
            "missing_public_query",
            lambda: prototype.public_challenge({"train": reference["train"], "test": []}),
            (ValueError,),
        ),
    }

    return {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "status": "passed",
        "task_id": prototype.TASK_ID,
        "prototype_version": prototype.VERSION,
        "surfaces": [
            "sampler/count/retry boundaries",
            "public/private export, numeric types, and verifier rejection",
        ],
        "sampler": {
            "episode_cases": len(sampler_cases),
            "pair_cases": total_pairs,
            "max_search_attempt": max_search_attempt,
            "cases": sampler_cases,
        },
        "projection": {
            "visible_id": visible_id,
            "visible_byte_count": len(visible_bytes),
            "private_mutation_preserved_id": True,
            "visible_mutation_changed_id": True,
            "query_answers_absent": True,
        },
        "rejection_checks": rejection_checks,
        "limits": [
            "bounded deterministic cases, not exhaustive over all seeds or start indices",
            "Racket parity is covered by the separate retained writer evidence and task tests",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    result = run_probe()
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
