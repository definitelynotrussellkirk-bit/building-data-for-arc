"""Bounded protected-Racket audit for the native phase-anchor family.

Run from a review packet through ``review.py run`` and choose a new output
folder.  The artifact is finite reviewer evidence, not owner acceptance or
training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes, public_challenge_id


_spec = importlib.util.spec_from_file_location(
    "_audit_f1c8ea826b10_native_family", HOME / "native_family.py"
)
if _spec is None or _spec.loader is None:
    raise ImportError("cannot load adjacent native_family.py")
family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(family)


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def checked_episode(episode: object, demos: int, queries: int) -> dict:
    if (
        type(episode) is not dict
        or type(episode.get("train")) is not list
        or type(episode.get("test")) is not list
        or len(episode["train"]) != demos
        or len(episode["test"]) != queries
        or not isinstance(episode.get("program_solution"), str)
    ):
        raise ValueError("wrong episode shape/counts")
    inputs: list[str] = []
    for pair in episode["train"] + episode["test"]:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each private pair needs exactly input/output")
        _grid(pair["input"])
        _grid(pair["output"])
        inputs.append(json.dumps(pair["input"], separators=(",", ":")))
    if len(inputs) != len(set(inputs)):
        raise ValueError("demonstration/query inputs must all differ")
    return episode


def first_bytes(episode: object) -> bytes:
    """Return the exact one-query public view after validating private labels."""
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    checked_episode(episode, len(episode.get("train", [])), len(episode.get("test", [])))
    return public_challenge_bytes(
        {"train": episode["train"], "test": episode["test"][:1]}
    )


def _multi_color_intermediates(grid: object) -> list[dict]:
    source = family._grid(grid)
    rows: list[dict] = []
    for region in family._regions(source):
        markers = sorted(
            (row, col, source[row][col])
            for row, col in region
            if source[row][col] not in (0, 5)
        )
        colors = sorted({value for _row, _col, value in markers})
        if len(colors) < 2:
            continue
        minimum = next(item for item in markers if item[2] == colors[0])
        maximum = next(item for item in markers if item[2] == colors[-1])
        top = min(row for row, _col in region)
        left = min(col for _row, col in region)
        rows.append(
            {
                "colors": colors,
                "cell_count": len(region),
                "bbox_top_left": [top, left],
                "minimum_marker": list(minimum),
                "maximum_marker": list(maximum),
                "minimum_marker_parity": (minimum[0] + minimum[1]) % 2,
                "maximum_marker_parity": (maximum[0] + maximum[1]) % 2,
                "minimum_marker_bbox_parity": (
                    minimum[0] - top + minimum[1] - left
                )
                % 2,
                "maximum_marker_bbox_parity": (
                    maximum[0] - top + maximum[1] - left
                )
                % 2,
            }
        )
    return rows


def causal_case(seed: int = 0) -> dict:
    """Build an exact qualification-match candidate for the wrong anchor witness."""
    settings = {"phase_anchor": "minimum_marker"}
    episode = checked_episode(family.generate(seed, settings, 2, 4), 2, 4)
    counterfactual = family.rival_program(settings, "maximum_marker")
    for pair in episode["test"]:
        alternative = family.rival_reference(pair["input"], settings, "maximum_marker")
        if alternative != pair["output"]:
            intermediates = _multi_color_intermediates(pair["input"])
            return {
                "settings": settings,
                "program": episode["program_solution"],
                "input": pair["input"],
                "output": pair["output"],
                "counterfactual_program": counterfactual,
                "counterfactual_output": alternative,
                "intermediate_value": {
                    "selected": "minimum-color marker coordinate in each multi-color region",
                    "counterfactual": "maximum-color marker coordinate in each multi-color region",
                    "multi_color_regions": intermediates,
                    "changed_output_cells": sum(
                        left != right
                        for left_row, right_row in zip(pair["output"], alternative)
                        for left, right in zip(left_row, right_row)
                    ),
                },
                "ablation": "wrong_intermediate",
            }
    raise RuntimeError("no query distinguishes minimum-marker from maximum-marker")


def facts(grid: object) -> dict:
    source = family._grid(grid)
    height, width = len(source), len(source[0])
    markers = [
        (row, col, value)
        for row, values in enumerate(source)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]
    return {
        "shape": [height, width],
        "wall_cells": sum(value == 5 for row in source for value in row),
        "marker_cells": len(markers),
        "marker_quadrants": [
            sum(
                (row >= height // 2) == bottom and (col >= width // 2) == right
                for row, col, _value in markers
            )
            for bottom, right in (
                (False, False),
                (False, True),
                (True, False),
                (True, True),
            )
        ],
        "scene": family.scene_summary(source),
    }


def negative_cases() -> list[dict]:
    records: list[dict] = []

    def reject(name: str, action) -> None:
        try:
            action()
        except (TypeError, ValueError) as error:
            records.append({"case": name, "rejected": True, "error": str(error)})
        else:
            raise AssertionError("invalid request accepted: " + name)

    for key, value in (
        ("seed", True),
        ("seed", -1),
        ("demos", True),
        ("demos", 1),
        ("demos", 7),
        ("queries", False),
        ("queries", 0),
        ("queries", 5),
    ):
        args = dict(seed=0, settings=deepcopy(family.DEFAULT), demos=2, queries=4)
        args[key] = value
        reject(f"{key}={value!r}", lambda args=args: family.generate(**args))
    for setting in (
        {},
        {"phase_anchor": True},
        {"phase_anchor": "unknown"},
        {"phase_anchor": "bbox_top_left", "extra": 1},
    ):
        reject(
            "invalid settings: " + repr(setting),
            lambda setting=setting: family.generate(0, setting, 2, 4),
        )
    for bad in ([], [[True]], [[10]], [[-1]], [[1], [1, 2]], [[0] * 31]):
        reject(
            "invalid reference grid: " + repr(bad),
            lambda bad=bad: family.reference(bad, family.DEFAULT),
        )
    for bad in ([[True]], [[1.0]], [[10]], [[-1]], [[1], []], [], [[0] * 31]):
        episode = {
            "train": [{"input": [[0]], "output": bad}],
            "test": [{"input": [[1]], "output": [[0]]}],
            "program_solution": "private",
        }
        reject(
            "invalid visible output: " + repr(bad),
            lambda episode=episode: first_bytes(episode),
        )
    return records


def run(out: Path) -> dict:
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()

    source_files = [
        HOME / name
        for name in (
            "audit_native.py",
            "native_family.py",
            "adapter.py",
            "canonical.rkt",
            "promotion.json",
        )
    ] + [
        ROOT / "generators/f1c8ea826b10/tests/test_native_parametric.py",
        ROOT / "src/arcpuzzles/parametric_worker.py",
        RUNTIME / "reviewer_support.py",
        RUNTIME / "arc_repl/racket_bridge.py",
        RUNTIME / "puzzle_generators/rule_wrap.py",
    ]
    source_binding = {
        str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in source_files
    }
    report: dict = {
        "schema": "f1c8ea826b10-native-finite-audit-v1",
        "status": "running",
        "source_files_sha256": source_binding,
        "seeds": [0, 17],
        "counts": {"demos": 2, "queries": 4},
        "episodes": [],
        "scope": (
            "Finite declared settings/rivals and bounded seeds only; no universal "
            "uniqueness, owner acceptance, measured learning benefit, or training admission."
        ),
        "negative_cases": negative_cases(),
    }
    executions = 0

    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        report["racket"] = identity

        def execute(program: str, grid: object, expected: object) -> list[list[int]]:
            nonlocal executions
            source = _grid(grid)
            result = _grid(apply(program, deepcopy(source)))
            executions += 1
            if result != _grid(expected):
                raise AssertionError("protected Racket output differs from Python claim")
            return result

        try:
            for seed in (0, 17):
                shared_inputs = None
                for settings in family.SETTINGS:
                    settings = deepcopy(settings)
                    episode = checked_episode(family.generate(seed, settings, 2, 4), 2, 4)
                    program = family.program(settings)
                    if episode["program_solution"] != program:
                        raise AssertionError("episode program differs from selected setting")
                    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                    if shared_inputs is None:
                        shared_inputs = inputs
                    elif inputs != shared_inputs:
                        raise AssertionError("setting-dependent input sampler")
                    for pair in episode["train"] + episode["test"]:
                        execute(program, pair["input"], pair["output"])

                    visible = first_bytes(episode)
                    single = family.generate(seed, settings, 2, 1)
                    if visible != first_bytes(single):
                        raise AssertionError("single-query first turn differs")
                    decoded = json.loads(visible)
                    expected_public = {
                        "train": episode["train"],
                        "test": [{"input": episode["test"][0]["input"]}],
                    }
                    if decoded != expected_public:
                        raise AssertionError("public projection differs from exact one-query view")
                    changed = deepcopy(episode)
                    changed["settings"] = {"private": "changed"}
                    changed["program_solution"] = "PRIVATE"
                    changed["sampling"] = {"private": "changed"}
                    changed["test"] = [dict(pair, output=[[9]]) for pair in changed["test"]]
                    if first_bytes(changed) != visible:
                        raise AssertionError("query answers leaked into public bytes")
                    changed["test"][1:] = [{"input": [[8]], "output": [[7]]}]
                    if first_bytes(changed) != visible:
                        raise AssertionError("future queries leaked into first-turn public bytes")
                    public_id = public_challenge_id(
                        {"train": episode["train"], "test": episode["test"][:1]}
                    )
                    if digest(visible) != public_id:
                        raise AssertionError("public challenge ID is not exact byte SHA-256")
                    public_path = out / "public" / f"{public_id}.json"
                    if public_path.exists():
                        if public_path.read_bytes() != visible:
                            raise AssertionError("public ID collision")
                    else:
                        public_path.write_bytes(visible)

                    rival_records = []
                    survivors = []
                    for name in family.rivals(settings):
                        rival_program = family.rival_program(settings, name)
                        outputs = [
                            execute(
                                rival_program,
                                pair["input"],
                                family.rival_reference(pair["input"], settings, name),
                            )
                            for pair in episode["train"] + episode["test"]
                        ]
                        rejects = [
                            index
                            for index, (actual, pair) in enumerate(
                                zip(outputs[:2], episode["train"])
                            )
                            if actual != pair["output"]
                        ]
                        disagreements = [
                            index
                            for index, (actual, pair) in enumerate(
                                zip(outputs[2:], episode["test"])
                            )
                            if actual != pair["output"]
                        ]
                        if not rejects:
                            survivors.append(name)
                            if disagreements:
                                raise AssertionError(
                                    "harmful rival survives demonstrations: " + name
                                )
                        if not rejects:
                            raise AssertionError(
                                "declared rival is not identified by two demos: " + name
                            )
                        rival_records.append(
                            {
                                "name": name,
                                "program": rival_program,
                                "program_sha256": digest(rival_program.encode("utf-8")),
                                "demo_outputs": outputs[:2],
                                "query_outputs": outputs[2:],
                                "rejected_by_demo_indices": rejects,
                                "query_disagreement_indices": disagreements,
                            }
                        )

                    query_facts = [facts(pair["input"]) for pair in episode["test"]]
                    if [row["shape"] for row in query_facts] != [
                        [9, 11],
                        [15, 17],
                        [23, 27],
                        [30, 30],
                    ]:
                        raise AssertionError("query profile drift")
                    if not all(query_facts[-1]["marker_quadrants"]):
                        raise AssertionError("30x30 stress lacks distributed markers")
                    if query_facts[-1]["scene"]["checker_regions"] < 1:
                        raise AssertionError("30x30 stress lacks checker branch")

                    private = {
                        "seed": seed,
                        "settings": settings,
                        "program": program,
                        "program_sha256": digest(program.encode("utf-8")),
                        "train": episode["train"],
                        "test": episode["test"],
                        "sampling": episode["sampling"],
                        "rivals": rival_records,
                        "surviving_extra_rivals": survivors,
                        "public_id": public_id,
                        "query_facts": query_facts,
                    }
                    private_name = f"episode-{len(report['episodes']):02d}.json"
                    write_json(out / "private" / private_name, private)
                    report["episodes"].append(
                        {
                            "seed": seed,
                            "settings": settings,
                            "public_id": public_id,
                            "private_path": "private/" + private_name,
                            "declared_rivals": len(rival_records),
                            "surviving_extra_rivals": survivors,
                            "per_demo_rejections": [
                                [
                                    row["name"]
                                    for row in rival_records
                                    if index in row["rejected_by_demo_indices"]
                                ]
                                for index in range(2)
                            ],
                            "query_facts": query_facts,
                        }
                    )
                    print(
                        json.dumps(
                            {
                                "seed": seed,
                                "settings": settings,
                                "executions": executions,
                            }
                        ),
                        flush=True,
                    )

            boundaries = []
            for demos in (3, 6):
                episode = checked_episode(
                    family.generate(0, deepcopy(family.DEFAULT), demos, 4), demos, 4
                )
                boundaries.append(
                    {
                        "seed": 0,
                        "settings": family.DEFAULT,
                        "demos": len(episode["train"]),
                        "queries": len(episode["test"]),
                        "execution": "not re-executed; count/prefix generation check",
                    }
                )
            one_query = checked_episode(
                family.generate(0, deepcopy(family.DEFAULT), 2, 1), 2, 1
            )
            boundaries.append(
                {
                    "seed": 0,
                    "settings": family.DEFAULT,
                    "demos": 2,
                    "queries": len(one_query["test"]),
                    "execution": "not re-executed; one-query public boundary check",
                }
            )
            report["count_boundaries"] = boundaries

            successes, failures = [], []
            for seed in range(32):
                try:
                    episodes = [
                        checked_episode(family.generate(seed, deepcopy(settings), 2, 4), 2, 4)
                        for settings in family.SETTINGS
                    ]
                    left = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
                    right = [pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]]
                    if left != right:
                        raise ValueError("settings do not share inputs")
                except (RuntimeError, TypeError, ValueError) as error:
                    failures.append({"seed": seed, "error": str(error)})
                else:
                    successes.append(seed)
            report["bounded_python_sampling"] = {
                "attempts": 32,
                "successes": len(successes),
                "successful_seeds": successes,
                "failures": failures,
                "scope": "Python generation for both settings, 2 demos/4 queries; inputs compared exactly.",
            }
            if failures:
                raise AssertionError("bounded Python sampling failures")

            witness = causal_case(0)
            execute(witness["program"], witness["input"], witness["output"])
            actual_counterfactual = execute(
                witness["counterfactual_program"],
                witness["input"],
                witness["counterfactual_output"],
            )
            if actual_counterfactual == witness["output"]:
                raise AssertionError("causal counterfactual does not change final output")
            write_json(out / "private" / "causal-case.json", witness)

            if not all(
                digest(path.read_bytes()) == source_binding[str(path.relative_to(ROOT))]
                for path in source_files
            ):
                raise AssertionError("source changed during audit")
            report.update(
                status="passed",
                racket_evaluations=executions,
                public_files=len(list((out / "public").glob("*.json"))),
                causal_case_path="private/causal-case.json",
                first_turn_public_only=True,
                matched_inputs_across_settings=True,
            )
        except BaseException as error:
            report.update(
                status="failed",
                racket_evaluations=executions,
                failure={"type": type(error).__name__, "message": str(error)},
            )
            write_json(out / "audit.json", report)
            raise
        finally:
            bridge.close()

    write_json(out / "audit.json", report)
    summary = {
        "status": report["status"],
        "episodes": len(report["episodes"]),
        "racket_evaluations": executions,
        "negative_cases": len(report["negative_cases"]),
        "python_sampling_successes": len(successes),
        "public_files": report["public_files"],
        "out": str(out),
    }
    print(json.dumps(summary, sort_keys=True), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
