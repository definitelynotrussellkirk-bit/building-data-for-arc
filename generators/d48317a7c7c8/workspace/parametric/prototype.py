#!/usr/bin/env python3
"""Materialize bounded Racket-backed evidence for target-length variants.

The adjacent adapter is the only source of rule and input semantics.  This
writer executes every retained label through the bundled Racket bridge, checks
an independent Python mirror, verifies demonstration-only identification, and
writes strictly separated public/private artifacts.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d48317a7c7c8"
VERSION = "target-length-prototype-v1"
HERE = Path(__file__).resolve().parent


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location(f"{TASK_ID}_parametric_adapter", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = _load_adapter()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(payload))


def _execute(bridge: Any, source: str, grid: list[list[int]]) -> list[list[int]]:
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("expected a canonical rule! wrapper")
    # Canonical non-lambda rules refer to the conventional top-level binding
    # ``g`` directly; lambda rules are applied to that same bound grid.
    bridge.define_grid("g", grid)
    body = source[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    result = bridge.eval_text(expression)
    if (
        type(result) is not list
        or not result
        or type(result[0]) is not list
        or not result[0]
        or any(type(row) is not list or len(row) != len(result[0]) for row in result)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in result for cell in row)
    ):
        raise ValueError("Racket rule returned a non-ARC grid")
    return result


def _public(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _source_hashes(root: Path) -> dict[str, str]:
    paths = [
        HERE / "adapter.py",
        HERE / "prototype.py",
        HERE / "promotion.json",
        HERE / "README.md",
        HERE.parents[1] / "tests" / "test_parametric_target_length.py",
    ]
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
        if path.is_file()
    }


def materialize(output: str | Path, *, base_seed: int = 20261024) -> dict[str, Any]:
    """Write two complete episodes, one per supported target length."""
    if type(base_seed) is not int or base_seed < 0:
        raise ValueError("base_seed must be a nonnegative integer")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    settings = (3, 4)
    generated = {
        length: adapter.generate(
            base_seed,
            {"target_length": length},
            demos=3,
            queries=4,
        )
        for length in settings
    }
    input_matrix = {
        length: [pair["input"] for pair in generated[length]["train"] + generated[length]["test"]]
        for length in settings
    }
    if input_matrix[3] != input_matrix[4]:
        raise ValueError("input sampling depends on the private target_length setting")

    from arc_repl.racket_bridge import RacketBridge

    racket_outputs: dict[int, list[list[list[int]]]] = {}
    with RacketBridge() as bridge:
        for length in settings:
            episode = generated[length]
            pairs = episode["train"] + episode["test"]
            outputs = [
                _execute(bridge, episode["program_solution"], pair["input"])
                for pair in pairs
            ]
            python_outputs = [pair["output"] for pair in pairs]
            if outputs != python_outputs:
                raise ValueError(f"Racket/Python parity failure for target_length={length}")
            racket_outputs[length] = outputs
        runtime_identity = bridge.runtime_identity

    complete: list[dict[str, Any]] = []
    seen_public_ids: set[str] = set()
    all_teaching = True
    for length in settings:
        episode = generated[length]
        inputs = input_matrix[length]
        outputs = racket_outputs[length]
        train = [
            {"input": deepcopy(inputs[index]), "output": deepcopy(outputs[index])}
            for index in range(3)
        ]
        test = [
            {"input": deepcopy(inputs[index]), "output": deepcopy(outputs[index])}
            for index in range(3, 7)
        ]
        survivors = []
        rival_rows = []
        for candidate in settings:
            demo_differences = [
                index
                for index in range(3)
                if racket_outputs[candidate][index] != outputs[index]
            ]
            query_differences = [
                index
                for index in range(4)
                if racket_outputs[candidate][3 + index] != outputs[3 + index]
            ]
            if not demo_differences:
                survivors.append(candidate)
            rival_rows.append(
                {
                    "settings": {"target_length": candidate},
                    "demo_differences": demo_differences,
                    "query_differences": query_differences,
                }
            )
        teaching_pass = survivors == [length]
        all_teaching = all_teaching and teaching_pass
        private = {
            "schema": "arcpuzzles-parametric-evidence-v1",
            "task_id": TASK_ID,
            "version": VERSION,
            "seed": base_seed,
            "settings": {"target_length": length},
            "program": episode["program_solution"],
            "program_sha256": _sha256(episode["program_solution"].encode()),
            "train": train,
            "test": test,
            "rival_checks": rival_rows,
            "demo_only_survivors": [{"target_length": item} for item in survivors],
            "demo_only_teaching_pass": teaching_pass,
            "label_authority": "bundled Racket bridge executing the exact instantiated program",
        }
        public = _public(private)
        visible_id = public_challenge_id(public)
        if visible_id in seen_public_ids:
            raise ValueError("duplicate visible challenge across settings")
        seen_public_ids.add(visible_id)
        public_name = f"challenge-{visible_id}"
        private["public_id"] = visible_id
        private["public_file"] = f"public/{public_name}.json"
        _write_public_json(output / "public" / f"{public_name}.json", public)
        _write_json(output / "private" / "episodes" / f"{public_name}.json", private)
        rule_path = output / "private" / "rules" / f"target-length-{length}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(episode["program_solution"], encoding="utf-8")
        complete.append(private)

    query_shapes = [
        [len(pair["input"]), len(pair["input"][0])]
        for episode in complete
        for pair in episode["test"]
    ]
    max_query_shape = max(query_shapes, key=lambda shape: shape[0] * shape[1])
    report = {
        "schema": "d48317a7c7c8-target-length-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "parameters": {"target_length": list(settings)},
        "default": {"target_length": 3},
        "default_program_exact_canonical": adapter.program({"target_length": 3}) == adapter._canonical_program(),
        "complete_episodes": len(complete),
        "pairs_per_episode": {"train": 3, "test": 4},
        "input_sampling_independent_of_settings": input_matrix[3] == input_matrix[4],
        "all_labels_executed_in_racket": True,
        "all_racket_outputs_match_python_mirror": True,
        "all_demo_only_teaching_checks_pass": all_teaching,
        "max_query_shape": max_query_shape,
        "runtime_identity": runtime_identity,
        "source_sha256": _source_hashes(root),
        "bounded_adversarial_checks": [
            {
                "surface": "minimum-size sampler capacity",
                "result": "repaired",
                "detail": "12x12 scenes no longer demand redundant extra bars outside their legal candidate region",
            },
            {
                "surface": "public serialization and private query-answer separation",
                "result": "repaired",
                "detail": "public files now use exact reviewer_support.public_challenge_bytes and packet-conformant challenge-<full-SHA-256>.json filenames; private query-answer mutation leaves those bytes and IDs unchanged",
            },
        ],
        "limitations": [
            "This is task-local proposed evidence, not owner qualification, acceptance, or training admission.",
            "Only exact target lengths 3 and 4 are supported.",
            "Evidence covers one seed per setting and the one declared finite rival.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = materialize(args.out, base_seed=args.base_seed)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "all_demo_only_teaching_checks_pass": report["all_demo_only_teaching_checks_pass"],
                "out": str(args.out),
            }
        )
    )
    return 0 if report["all_demo_only_teaching_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
