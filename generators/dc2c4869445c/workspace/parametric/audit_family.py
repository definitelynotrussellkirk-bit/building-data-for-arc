"""Bounded sampler, protected-Racket self-audit, causal witness, and exports.

Run through ``review.py run``.  The output is authoring/qualification evidence,
not owner acceptance and not training admission.  All public artifacts contain
one query only; settings, programs, answers, seeds, future queries, and totals
remain in the private side.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ADAPTER_PATH = HERE / "adapter.py"
MODES = ("all", "nearest_after_reflection")


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "_dc2c4869445c_audit_adapter", ADAPTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = _load_adapter()


def _raw(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_diff(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        left[row][col] != right[row][col]
        for row in range(len(left))
        for col in range(len(left[0]))
    )


def _profile(grid: list[list[int]]) -> dict[str, Any]:
    facts = adapter.candidates(grid)
    rows = [row for row, values in enumerate(grid) if any(values)]
    cols = [
        col
        for col in range(len(grid[0]))
        if any(grid[row][col] for row in range(len(grid)))
    ]
    selected = adapter.winner(grid)
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "groups": len({candidate["group"] for candidate in facts}),
        "candidates": len(facts),
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
        "occupied_row_span": max(rows) - min(rows),
        "occupied_col_span": max(cols) - min(cols),
        "selected_seed": selected["seed"],
        "selected_kind": selected["kind"],
        "selected_reflected_distance": selected["reflected_distance"],
    }


def write_examples(episodes: list[dict[str, Any]], destination: Path) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"choose a new export directory: {destination}")
    public: dict[str, bytes] = {}
    private: list[dict[str, Any]] = []
    for episode in episodes:
        identifiers = []
        for index in range(len(episode["test"])):
            challenge = adapter.public_turn(episode, index)
            payload = public_challenge_bytes(challenge)
            identifier = public_challenge_id(challenge)
            if identifier in public:
                raise ValueError("duplicate visible challenge")
            if _sha256(payload) != identifier:
                raise AssertionError("public ID is not exact visible-byte SHA-256")
            public[identifier] = payload
            identifiers.append(identifier)
        private.append({"episode": copy.deepcopy(episode), "public_ids": identifiers})
    (destination / "public").mkdir(parents=True, exist_ok=False)
    for identifier, payload in sorted(public.items()):
        (destination / "public" / f"{identifier}.json").write_bytes(payload)
    manifest = {
        "schema": "dc2c4869445c-reflection-selection-examples-v1",
        "private_episodes": private,
        "public_files": {
            f"public/{identifier}.json": _sha256(payload)
            for identifier, payload in sorted(public.items())
        },
        "owner_acceptance": "pending",
        "training_admitted": False,
        "consumer": (
            "Reveal exactly one hash-named public file per turn. Keep this "
            "private manifest, future queries, settings, programs, and answers controller-side."
        ),
    }
    (destination / "private.json").write_bytes(_raw(manifest))
    return manifest


def audit(destination: Path) -> dict[str, Any]:
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"choose a new evidence directory: {destination}")

    source_paths = sorted(
        [HERE / "adapter.py", HERE / "prototype.py", HERE / "canonical.rkt", HERE / "promotion.json", Path(__file__)]
    )
    source_hashes = {
        path.relative_to(ROOT).as_posix(): _sha256(path.read_bytes())
        for path in source_paths
    }

    sampling_records: list[dict[str, Any]] = []
    sampling_failures: list[dict[str, Any]] = []
    for seed in list(range(32)) + [2**63 - 1]:
        for demos in (2, 3, 6):
            baseline_inputs = None
            for mode in MODES:
                try:
                    episode = adapter.generate(
                        seed, {"copy_selection": mode}, demos, 4
                    )
                    inputs = [
                        pair["input"]
                        for split in ("train", "test")
                        for pair in episode[split]
                    ]
                    if baseline_inputs is not None and inputs != baseline_inputs:
                        raise AssertionError("setting-dependent input sampling")
                    baseline_inputs = inputs
                    report = adapter.teaching_report(
                        episode["train"], {"copy_selection": mode}
                    )
                    if report["surviving_rivals"]:
                        raise AssertionError(f"underidentified lesson: {report}")
                    short = adapter.generate(
                        seed, {"copy_selection": mode}, demos, 1
                    )
                    if adapter.public_turn(short, 0) != adapter.public_turn(episode, 0):
                        raise AssertionError("query-count-dependent first turn")
                    stress = _profile(episode["test"][-1]["input"])
                    if (
                        (stress["height"], stress["width"]) != (30, 30)
                        or stress["groups"] != 3
                        or stress["candidates"] != 9
                        or stress["occupied_row_span"] < 15
                        or stress["occupied_col_span"] < 10
                    ):
                        raise AssertionError(f"unsubstantive 30x30 stress scene: {stress}")
                    sampling_records.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "copy_selection": mode,
                            "teaching_candidates": episode["teaching_candidates"],
                            "query_profiles": [
                                _profile(pair["input"]) for pair in episode["test"]
                            ],
                        }
                    )
                except Exception as error:  # retained as exact bounded evidence
                    sampling_failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "copy_selection": mode,
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
    if sampling_failures:
        raise AssertionError(json.dumps({"sampling_failures": sampling_failures}))

    evaluations = 0
    executed_episodes: list[dict[str, Any]] = []
    rival_cases: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []
    runtime_identity: dict[str, Any]
    witness: dict[str, Any] | None = None

    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, runtime_identity, bridge = _real_evaluator(runtime)

        def run(program: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return apply(program, grid)

        try:
            for seed in (0, 17):
                for demos in (2, 3, 6):
                    for mode in MODES:
                        episode = adapter.generate(
                            seed, {"copy_selection": mode}, demos, 4
                        )
                        for split in ("train", "test"):
                            for index, pair in enumerate(episode[split]):
                                actual = run(
                                    episode["program_solution"], pair["input"]
                                )
                                if actual != pair["output"]:
                                    raise AssertionError(
                                        (mode, seed, demos, split, index, "Racket label mismatch")
                                    )
                        executed_episodes.append(
                            {
                                "seed": seed,
                                "copy_selection": mode,
                                "demos": demos,
                                "queries": 4,
                                "labels": demos + 4,
                                "program_sha256": _sha256(
                                    episode["program_solution"].encode()
                                ),
                            }
                        )
                        if seed == 0 and demos == 3:
                            examples.append(copy.deepcopy(episode))

                # Execute every declared wrong rule against the minimum visible lesson.
                for mode in MODES:
                    episode = adapter.generate(
                        seed, {"copy_selection": mode}, 2, 4
                    )
                    for rival in adapter.rival_names(mode):
                        rival_source = adapter.rival_program(mode, rival)
                        outputs = [
                            run(rival_source, pair["input"])
                            for pair in episode["train"]
                        ]
                        expected = [
                            adapter.rival_output(pair["input"], mode, rival)
                            for pair in episode["train"]
                        ]
                        if outputs != expected:
                            raise AssertionError(
                                (mode, seed, rival, "Racket/Python rival mismatch")
                            )
                        rejecting = [
                            index
                            for index, output in enumerate(outputs)
                            if output != episode["train"][index]["output"]
                        ]
                        if not rejecting:
                            raise AssertionError(
                                (mode, seed, rival, "rival survives two demonstrations")
                            )
                        case_index = rejecting[0]
                        rival_cases.append(
                            {
                                "seed": seed,
                                "copy_selection": mode,
                                "rival": rival,
                                "rival_program_sha256": _sha256(rival_source.encode()),
                                "rejecting_demo_indices": rejecting,
                                "case": {
                                    "input": episode["train"][case_index]["input"],
                                    "expected": episode["train"][case_index]["output"],
                                    "rival_output": outputs[case_index],
                                },
                            }
                        )

            causal_episode = adapter.generate(
                0, {"copy_selection": "nearest_after_reflection"}, 2, 4
            )
            causal_pair = causal_episode["test"][-1]
            state = adapter.causal_state(causal_pair["input"])
            intended_source = causal_episode["program_solution"]
            wrong_source = adapter.rival_program(
                "nearest_after_reflection", "nearest_cue_before_reflection"
            )
            intended_output = run(intended_source, causal_pair["input"])
            wrong_output = run(wrong_source, causal_pair["input"])
            if intended_output != causal_pair["output"]:
                raise AssertionError("causal intended program disagrees with retained label")
            if wrong_output != adapter.rival_output(
                causal_pair["input"],
                "nearest_after_reflection",
                "nearest_cue_before_reflection",
            ):
                raise AssertionError("causal wrong-intermediate program mismatch")
            changed = _grid_diff(intended_output, wrong_output)
            if changed <= 0 or changed != state["changed_output_cells"]:
                raise AssertionError("causal witness does not change final output")
            witness = {
                "schema": "arcpuzzles-parametric-causal-witness-v1",
                "task_id": "dc2c4869445c",
                "setting": {"copy_selection": "nearest_after_reflection"},
                "step_a": "reflect every main shape according to each cue direction",
                "intermediate": state["intermediate"],
                "step_b": (
                    "rank transformed bounding-box centres against the canvas centre "
                    "and paint only the nearest reflected copy"
                ),
                "why_b_depends_on_a": (
                    "the winning cue is selected from transformed copy coordinates; "
                    "ranking the original cue positions selects a different cue"
                ),
                "wrong_intermediate": state["wrong_intermediate"],
                "input": causal_pair["input"],
                "input_shape": [
                    len(causal_pair["input"]),
                    len(causal_pair["input"][0]),
                ],
                "selected_reflected_seed": state["selected_reflected_seed"],
                "selected_cue_seed": state["selected_cue_seed"],
                "intended_program": intended_source,
                "intended_program_sha256": _sha256(intended_source.encode()),
                "wrong_program": wrong_source,
                "wrong_program_sha256": _sha256(wrong_source.encode()),
                "intended_output": intended_output,
                "wrong_output": wrong_output,
                "changed_output_cells": changed,
                "backend": runtime_identity,
                "protected_racket_replayed": True,
            }
        finally:
            bridge.close()

    if witness is None:
        raise AssertionError("causal witness was not constructed")

    destination.mkdir(parents=True, exist_ok=False)
    examples_manifest = write_examples(examples, destination / "examples")
    (destination / "causal-witness.json").write_bytes(_raw(witness))
    result = {
        "schema": "dc2c4869445c-reflection-selection-audit-v1",
        "status": "passed",
        "command": " ".join(sys.argv),
        "source_sha256": source_hashes,
        "runtime": runtime_identity,
        "racket_evaluations": evaluations,
        "sampling": {
            "attempted": len(sampling_records),
            "succeeded": len(sampling_records),
            "failed": 0,
            "records": sampling_records,
        },
        "executed_episodes": executed_episodes,
        "self_review": {
            "cases": rival_cases,
            "surviving_rivals": [],
            "fit_scope": "first two visible demonstrations only; finite declared rivals",
            "uses_query_answers": False,
        },
        "causal_witness": "causal-witness.json",
        "public_examples": {
            "path": "examples/private.json",
            "turns": sum(
                len(row["public_ids"])
                for row in examples_manifest["private_episodes"]
            ),
        },
        "owner_acceptance": "pending",
        "training_admitted": False,
        "limits": (
            "Finite declared rivals and sampled seeds only. This does not establish "
            "universal identifiability or measured learning gain."
        ),
    }
    (destination / "audit.json").write_bytes(_raw(result))
    print(
        json.dumps(
            {
                "status": "passed",
                "sampling_episodes": len(sampling_records),
                "executed_episodes": len(executed_episodes),
                "rival_cases": len(rival_cases),
                "racket_evaluations": evaluations,
                "causal_changed_cells": witness["changed_output_cells"],
                "causal_shape": witness["input_shape"],
                "report": str(destination / "audit.json"),
            },
            sort_keys=True,
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    audit(parser.parse_args().out)
