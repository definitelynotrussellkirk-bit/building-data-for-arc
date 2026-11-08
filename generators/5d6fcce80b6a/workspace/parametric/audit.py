#!/usr/bin/env python3
"""Bounded protected-Racket/self-review for the native 5d6fcce80b6a family.

Run from the extracted packet root::

    python3 review.py run python3 \
      generators/5d6fcce80b6a/workspace/parametric/audit.py \
      --out ../checks/5d6fcce80b6a/self-review

The audit replays true and declared-setting labels through protected Racket,
checks the finite shortcut family implemented by ``teaching_check``, and writes
strict one-query-at-a-time public projections.  It grants no owner acceptance.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "5d6fcce80b6a"
SETTINGS = (
    {"copy_diagonal": "main", "separator_policy": "through_last"},
    {"copy_diagonal": "anti", "separator_policy": "through_last"},
    {"copy_diagonal": "main", "separator_policy": "strict_between"},
    {"copy_diagonal": "anti", "separator_policy": "strict_between"},
)


def _load_adapter(home: Path):
    path = home / "adapter.py"
    spec = importlib.util.spec_from_file_location("_audit_5d6fcce80b6a_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    args = parser.parse_args(argv)
    seeds = args.seed if args.seed is not None else [0, 17]
    if (
        not 1 <= len(seeds) <= 4
        or len(set(seeds)) != len(seeds)
        or any(type(seed) is not int or not 0 <= seed < 2**63 for seed in seeds)
    ):
        parser.error("provide one to four distinct seeds in 0..2^63-1")
    if args.out.exists():
        parser.error("choose a fresh output directory")

    home = Path(__file__).resolve().parent
    root = find_root(__file__)
    adapter = _load_adapter(home)
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()

    source_files = [
        home / "adapter.py",
        home / "prototype.py",
        home / "promotion.json",
        home / "canonical.rkt",
        home / "audit.py",
        home.parents[1] / "generator.py",
        home.parents[1] / "tests/test_native_parametric_5d6fcce80b6a.py",
    ]
    source_binding = {
        path.relative_to(root).as_posix(): _sha256(path) for path in source_files
    }
    programs = {_key(setting): adapter.program(setting) for setting in SETTINGS}
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    cache: dict[tuple[str, str], list[list[int]]] = {}
    failures: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    public_rows: list[dict[str, Any]] = []
    causal_case = None

    def execute(program_text: str, grid: list[list[int]]) -> list[list[int]]:
        cache_key = (hashlib.sha256(program_text.encode()).hexdigest(), _key(grid))
        if cache_key not in cache:
            cache[cache_key] = apply(program_text, grid)
        return deepcopy(cache[cache_key])

    try:
        for seed in seeds:
            for demos in (2, 3, 6):
                input_sequences = []
                for setting in SETTINGS:
                    episode = adapter.generate(seed, setting, demos, 4)
                    pairs = episode["train"] + episode["test"]
                    input_sequences.append([pair["input"] for pair in pairs])
                    chosen_program = programs[_key(setting)]
                    for pair_index, pair in enumerate(pairs):
                        actual = execute(chosen_program, pair["input"])
                        if actual != pair["output"]:
                            failures.append(
                                {
                                    "failure": "chosen Racket label differs",
                                    "seed": seed,
                                    "demos": demos,
                                    "settings": setting,
                                    "pair_index": pair_index,
                                }
                            )
                    # Replay every declared setting on the first two teaching
                    # inputs and compare against the independent Python mirror.
                    for candidate in SETTINGS:
                        candidate_program = programs[_key(candidate)]
                        for pair in episode["train"][:2]:
                            actual = execute(candidate_program, pair["input"])
                            expected = adapter.transform(pair["input"], candidate)
                            if actual != expected:
                                failures.append(
                                    {
                                        "failure": "declared setting Racket/Python mismatch",
                                        "seed": seed,
                                        "candidate": candidate,
                                    }
                                )
                    certificate = adapter.teaching_check(episode)
                    if (
                        certificate["declared_survivors"] != [setting]
                        or certificate["harmful_survivors"]
                        or not all(certificate["query_identifiable"])
                    ):
                        failures.append(
                            {
                                "failure": "finite teaching ambiguity",
                                "seed": seed,
                                "demos": demos,
                                "settings": setting,
                                "certificate": certificate,
                            }
                        )
                    facts = [adapter.analyze(pair["input"]) for pair in pairs]
                    jobs.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "settings": setting,
                            "labels_checked": len(pairs),
                            "certificate": certificate,
                            "input_shapes": [
                                [row["height"], row["width"]] for row in facts
                            ],
                            "nonzero_cells": [row["nonzero_cells"] for row in facts],
                        }
                    )

                    if demos == 3:
                        one = adapter.generate(seed, setting, demos, 1)
                        first_bytes = public_challenge_bytes(adapter.model_view(one, 0))
                        for query_index in range(4):
                            view = adapter.model_view(episode, query_index)
                            body = public_challenge_bytes(view)
                            if query_index == 0 and body != first_bytes:
                                failures.append(
                                    {
                                        "failure": "first public turn depends on total query count",
                                        "seed": seed,
                                        "settings": setting,
                                    }
                                )
                            hidden = deepcopy(episode)
                            hidden.update(
                                seed=-1,
                                settings={"private": True},
                                program_solution="private",
                            )
                            hidden["train"][0]["private"] = "private"
                            for pair in hidden["test"]:
                                pair["output"] = [[9]]
                            if adapter.model_view(hidden, query_index) != view:
                                failures.append(
                                    {
                                        "failure": "private field changed public turn",
                                        "seed": seed,
                                        "settings": setting,
                                        "query_index": query_index,
                                    }
                                )
                            public_id = public_challenge_id(view)
                            path = public_dir / f"challenge-{public_id}.json"
                            if path.exists():
                                failures.append(
                                    {
                                        "failure": "duplicate visible public payload",
                                        "public_id": public_id,
                                    }
                                )
                            else:
                                path.write_bytes(body)
                            public_rows.append(
                                {
                                    "seed": seed,
                                    "settings": setting,
                                    "query_index": query_index,
                                    "public_id": public_id,
                                    "path": path.relative_to(args.out).as_posix(),
                                    "sha256": hashlib.sha256(body).hexdigest(),
                                }
                            )

                    if causal_case is None and seed == seeds[0] and demos == 2 and setting == SETTINGS[-1]:
                        pair = episode["test"][-1]
                        facts = adapter.analyze(pair["input"])
                        wrong = facts["first_colored"]
                        counterfactual = adapter.counterfactual_program(
                            setting, wrong_last_colored=wrong
                        )
                        counterfactual_output = execute(counterfactual, pair["input"])
                        if counterfactual_output == pair["output"]:
                            failures.append(
                                {"failure": "causal wrong-intermediate did not change output"}
                            )
                        causal_case = {
                            "settings": setting,
                            "program": chosen_program,
                            "input": pair["input"],
                            "output": pair["output"],
                            "intermediate_value": {
                                "first_colored": facts["first_colored"],
                                "last_colored": facts["last_colored"],
                                "wrong_last_colored": wrong,
                            },
                            "counterfactual_program": counterfactual,
                            "counterfactual_output": counterfactual_output,
                            "ablation": "wrong_intermediate",
                        }
                if any(sequence != input_sequences[0] for sequence in input_sequences[1:]):
                    failures.append(
                        {
                            "failure": "private setting changed sampled inputs",
                            "seed": seed,
                            "demos": demos,
                        }
                    )
    except Exception as exc:  # keep a compact source-bound failure record
        failures.append({"failure": type(exc).__name__, "message": str(exc)})
    finally:
        bridge.close()

    if causal_case is not None:
        (args.out / "causal-case.json").write_text(
            json.dumps(causal_case, indent=2, sort_keys=True) + "\n"
        )
    report = {
        "schema": "5d6fcce80b6a-native-self-review-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "source_binding": source_binding,
        "programs": {
            key: {
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "text": text,
            }
            for key, text in programs.items()
        },
        "racket": identity,
        "seeds": seeds,
        "episodes_checked": len(jobs),
        "label_claims_checked": sum(row["labels_checked"] for row in jobs),
        "distinct_protected_racket_evaluations": len(cache),
        "public_turns_written": len(public_rows),
        "jobs": jobs,
        "public_turns": public_rows,
        "causal_case_path": "causal-case.json" if causal_case is not None else None,
        "failures": failures,
        "limits": (
            "Finite seeds, four declared settings, and ten implemented shortcuts; "
            "true/declared labels are protected-Racket checked, not a universal induction proof."
        ),
    }
    (args.out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "episodes_checked",
                    "label_claims_checked",
                    "distinct_protected_racket_evaluations",
                    "public_turns_written",
                    "failures",
                )
            },
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
