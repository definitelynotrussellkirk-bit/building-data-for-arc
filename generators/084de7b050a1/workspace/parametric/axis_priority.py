#!/usr/bin/env python3
"""Task-local prototype for a fixed-per-episode axis-priority parameter.

This file never changes the selected production generator or canonical rule.
It materializes two complete rules:

* ``column_first`` — the current canonical behavior (default/original).
* ``row_first`` — a proposed alternative that swaps only the two aligned-axis
  clauses when a colored dot shares both a blue column and a blue row.

The command-line probe executes both Racket programs, builds one complete
five-demonstration-plus-query episode for each setting, and requires the
settings to be distinguishable in the demonstrations before the query.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "084de7b050a1"
ALLOWED_AXIS_PRIORITIES = ("column_first", "row_first")
DEFAULT_AXIS_PRIORITY = "column_first"
DEMO_INDICES = (0, 1, 2, 3, 4)
QUERY_INDEX = 7
DIFFICULTY = "medium"


def normalized_hash(source: str) -> str:
    """Return the canonical 12-hex whitespace-normalized rule hash."""
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_source(*, root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK_ID}: canonical program_solution not found")


def _swap_axis_clauses(source: str) -> str:
    """Swap the complete h-blue and v-blue ``cond`` clauses exactly once."""
    cond_at = source.index("                        (cond")
    h_at = source.index("\n                          (h-blue", cond_at)
    v_at = source.index("\n                          (v-blue", h_at)
    else_at = source.index("\n                          (else acc)", v_at)
    h_clause = source[h_at:v_at]
    v_clause = source[v_at:else_at]
    swapped = source[:h_at] + v_clause + h_clause + source[else_at:]
    if swapped == source:
        raise AssertionError("axis-priority source swap had no effect")
    return swapped


def racket_source(axis_priority: str, *, root: Path | str) -> str:
    """Materialize the complete Racket rule for one bounded parameter value."""
    if axis_priority not in ALLOWED_AXIS_PRIORITIES:
        raise ValueError(
            "axis_priority must be one of "
            + ", ".join(repr(value) for value in ALLOWED_AXIS_PRIORITIES)
        )
    canonical = _canonical_source(root=Path(root))
    if axis_priority == "column_first":
        return canonical
    return _swap_axis_clauses(canonical)


def _python_output(module: Any, grid: list[list[int]], axis_priority: str):
    if axis_priority == "column_first":
        return module._mirror(grid)
    if axis_priority == "row_first":
        return module._mirror_variant(grid, row_priority=True)
    raise ValueError(f"unknown axis_priority: {axis_priority!r}")


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _callable_racket_source(source: str) -> str:
    """Peel this prototype's plain ``(rule! <lambda>)`` wrapper.

    Both retained programs use only prelude primitives and contain no comments,
    dictionary literals, or shorthand forms, so invoking the exact lambda avoids
    the legacy ``scripts.comment_solutions`` dependency of the general wrapper.
    """
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) program")
    callable_source = stripped[len(prefix):-1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def _racket_outputs(source: str, grids: list[list[list[int]]]):
    from arc_repl.racket_bridge import RacketBridge

    callable_source = _callable_racket_source(source)
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define prototype-rule {callable_source})")
        result = bridge.eval_text(
            f"(map prototype-rule '{_racket_literal(grids)})"
        )
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket result shape")
    return result


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _episode_inputs(module: Any, *, seed: int) -> list[list[list[int]]]:
    indices = (*DEMO_INDICES, QUERY_INDEX)
    return [
        module.generate(seed, index, difficulty=DIFFICULTY)
        for index in indices
    ]


def build_report(*, root: Path, seeds: dict[str, int]) -> dict[str, Any]:
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    sources = {
        setting: racket_source(setting, root=root)
        for setting in ALLOWED_AXIS_PRIORITIES
    }
    if normalized_hash(sources[DEFAULT_AXIS_PRIORITY]) != module.RULE_HASH:
        raise AssertionError("default prototype no longer matches selected RULE_HASH")

    on_disk = Path(__file__).resolve().parent / "racket"
    for setting, source in sources.items():
        retained = (on_disk / f"{setting}.rkt").read_text(encoding="utf-8")
        if retained != source:
            raise AssertionError(f"retained {setting}.rkt differs from materialized rule")

    episodes: dict[str, Any] = {}
    all_inputs: dict[str, list[list[list[int]]]] = {}
    for setting in ALLOWED_AXIS_PRIORITIES:
        inputs = _episode_inputs(module, seed=seeds[setting])
        all_inputs[setting] = inputs
        python_outputs = [_python_output(module, grid, setting) for grid in inputs]
        racket_outputs = _racket_outputs(sources[setting], inputs)
        if racket_outputs != python_outputs:
            raise AssertionError(f"{setting}: Python/Racket output mismatch")
        episodes[setting] = {
            "axis_priority": setting,
            "seed": seeds[setting],
            "difficulty": DIFFICULTY,
            "demonstration_indices": list(DEMO_INDICES),
            "query_index": QUERY_INDEX,
            "racket_rule_sha256": hashlib.sha256(sources[setting].encode()).hexdigest(),
            "racket_rule_hash": normalized_hash(sources[setting]),
            "demonstrations": [
                {
                    "sample_index": index,
                    "input": grid,
                    "output": output,
                    "input_sha256": _digest(grid),
                    "output_sha256": _digest(output),
                }
                for index, grid, output in zip(
                    DEMO_INDICES, inputs[:-1], racket_outputs[:-1]
                )
            ],
            "query": {
                "sample_index": QUERY_INDEX,
                "input": inputs[-1],
                "output": racket_outputs[-1],
                "input_sha256": _digest(inputs[-1]),
                "output_sha256": _digest(racket_outputs[-1]),
            },
        }

    # Compare each episode's inputs under both settings.  At least one demo and
    # the query must expose the parameter before the hidden answer is requested.
    distinction: dict[str, Any] = {}
    for setting, inputs in all_inputs.items():
        column = [_python_output(module, grid, "column_first") for grid in inputs]
        row = [_python_output(module, grid, "row_first") for grid in inputs]
        differing_demos = [
            index
            for index, left, right in zip(DEMO_INDICES, column[:-1], row[:-1])
            if left != right
        ]
        query_differs = column[-1] != row[-1]
        if not differing_demos or not query_differs:
            raise AssertionError(
                f"{setting}: episode does not teach and query axis_priority"
            )
        distinction[setting] = {
            "differing_demonstration_indices": differing_demos,
            "query_differs": query_differs,
        }

    return {
        "schema": "arcpuzzles-parametric-rule-prototype-v1",
        "status": "proposed_prototype_not_selected",
        "task_id": TASK_ID,
        "parameter": {
            "name": "axis_priority",
            "allowed_values": list(ALLOWED_AXIS_PRIORITIES),
            "default": DEFAULT_AXIS_PRIORITY,
            "chosen_once_per_episode": True,
            "input_constraint": (
                "To observe the parameter, at least one colored dot must share "
                "both a row and a column with blue cells."
            ),
        },
        "generator_source": str(source_path),
        "generator_sha256": source_sha256,
        "selected_rule_hash": module.RULE_HASH,
        "rules": {
            setting: {
                "path": f"racket/{setting}.rkt",
                "sha256": hashlib.sha256(source.encode()).hexdigest(),
                "normalized_hash": normalized_hash(source),
                "source": source,
            }
            for setting, source in sources.items()
        },
        "episodes": episodes,
        "distinguishability": distinction,
        "limitations": [
            "This is task-local authoring evidence, not a production parametric API.",
            "Only the two-clause axis precedence changes; anchor order, clipping, "
            "dot order, colors, and all input sampling remain fixed.",
            "Two deterministic medium-band episodes are bounded evidence, not an "
            "exhaustive statement over every lawful input or seed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--examples",
        type=Path,
        default=Path(__file__).resolve().parent / "examples.json",
    )
    args = parser.parse_args()

    root = find_root(__file__)
    report = build_report(
        root=root,
        seeds={"column_first": 17, "row_first": 71},
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    examples = {
        "schema": report["schema"],
        "status": report["status"],
        "task_id": TASK_ID,
        "parameter": report["parameter"],
        "rules": {
            key: {k: value[k] for k in ("path", "sha256", "normalized_hash")}
            for key, value in report["rules"].items()
        },
        "episodes": report["episodes"],
        "distinguishability": report["distinguishability"],
        "limitations": report["limitations"],
    }
    args.examples.parent.mkdir(parents=True, exist_ok=True)
    args.examples.write_text(json.dumps(examples, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "examples": str(args.examples),
                "generator_sha256": report["generator_sha256"],
                "rule_hashes": {
                    key: value["normalized_hash"]
                    for key, value in report["rules"].items()
                },
                "distinguishability": report["distinguishability"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
