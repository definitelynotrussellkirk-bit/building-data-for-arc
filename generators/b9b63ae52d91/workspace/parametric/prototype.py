#!/usr/bin/env python3
"""Task-local mirror-axis curriculum prototype for b9b63ae52d91.

The production task remains the canonical vertical-mirror rule.  This prototype
chooses one hidden rule parameter once per episode and materializes three
labeled demonstrations plus one unlabeled query.  Exact Racket programs produce
all retained labels; the Python implementation is only a parity oracle.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Callable, Iterable


TASK_ID = "b9b63ae52d91"
MIRROR_AXES = ("vertical", "horizontal")
DEFAULT_MIRROR_AXIS = "vertical"
BACKGROUND = 0
CYAN = 8
PAIR_COLOR = 2
SOLO_COLOR = 5

RACKET_RULES = {
    "vertical": """(rule!
  (let ((h (rows g)))
    (cellmap g (r c v)
      (if (= v 8)
          (if (= (at g (- (- h 1) r) c) 8) 2 5)
          0))))""",
    "horizontal": """(rule!
  (let ((w (cols g)))
    (cellmap g (r c v)
      (if (= v 8)
          (if (= (at g r (- (- w 1) c)) 8) 2 5)
          0))))""",
}


def _require_nonnegative_integer(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _validate_axis(axis: str) -> str:
    if axis not in MIRROR_AXES:
        raise ValueError(f"mirror_axis must be one of {MIRROR_AXES!r}")
    return axis


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    rows = [list(row) for row in grid]
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("grid must be a nonempty rectangular matrix")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in (BACKGROUND, CYAN)
        for row in rows
        for value in row
    ):
        raise ValueError("grid values must be exactly black(0) or cyan(8)")
    return rows


def choose_mirror_axis(seed: int) -> str:
    """Choose the episode parameter once; even seeds preserve the default."""
    _require_nonnegative_integer("seed", seed)
    return MIRROR_AXES[seed % len(MIRROR_AXES)]


def rival_axis(axis: str) -> str:
    axis = _validate_axis(axis)
    return "horizontal" if axis == "vertical" else "vertical"


def apply_python(grid: Iterable[Iterable[int]], axis: str) -> list[list[int]]:
    """Reference mirror-axis transform used only to check exact Racket parity."""
    rows = _copy_grid(grid)
    axis = _validate_axis(axis)
    height = len(rows)
    width = len(rows[0])
    output = [[BACKGROUND] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if rows[row][col] != CYAN:
                continue
            partner = (
                rows[height - 1 - row][col]
                if axis == "vertical"
                else rows[row][width - 1 - col]
            )
            output[row][col] = PAIR_COLOR if partner == CYAN else SOLO_COLOR
    return output


def racket_rule(axis: str) -> str:
    return RACKET_RULES[_validate_axis(axis)]


def callable_racket_rule(axis: str) -> str:
    """Convert this prototype's simple complete ``rule!`` source locally.

    The repository's general wrapper also supports historical syntax and
    therefore imports authoring-only parser helpers.  This task-local wrapper
    deliberately handles only the two complete body-form programs above, so
    the prototype remains runnable in the portable review runtime.
    """
    source = racket_rule(axis).strip()
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("expected a complete body-form (rule! ...) program")
    body = source[len("(rule!"): -1].strip()
    return (
        "(lambda (g) "
        "(let* ((h (rows g)) (w (cols g))) "
        f"{body}))"
    )


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def assemble_episode(
    grids: Iterable[Iterable[Iterable[int]]],
    axis: str,
    *,
    labeler: Callable[[Iterable[Iterable[int]], str], list[list[int]]] = apply_python,
) -> dict:
    """Build a 3-demo/1-query episode and verify its declared rival witnesses."""
    axis = _validate_axis(axis)
    rival = rival_axis(axis)
    selected = [_copy_grid(grid) for grid in grids]
    if len(selected) < 4:
        raise ValueError("need at least four inputs for three demos and one query")
    selected = selected[:4]

    chosen_outputs = [labeler(copy.deepcopy(grid), axis) for grid in selected]
    rival_outputs = [labeler(copy.deepcopy(grid), rival) for grid in selected]
    python_chosen = [apply_python(grid, axis) for grid in selected]
    python_rival = [apply_python(grid, rival) for grid in selected]
    if chosen_outputs != python_chosen or rival_outputs != python_rival:
        raise AssertionError("Racket/Python parity mismatch in mirror-axis prototype")

    demo_distinguishes = any(
        chosen_outputs[index] != rival_outputs[index] for index in range(3)
    )
    query_distinguishes = chosen_outputs[3] != rival_outputs[3]
    if not demo_distinguishes:
        raise ValueError("demonstrations do not distinguish the mirror-axis rival")
    if not query_distinguishes:
        raise ValueError("query does not distinguish the mirror-axis rival")

    train = [
        {"input": copy.deepcopy(selected[index]),
         "output": copy.deepcopy(chosen_outputs[index])}
        for index in range(3)
    ]
    test = [{"input": copy.deepcopy(selected[3])}]
    return {
        "parameter": {"mirror_axis": axis},
        "train": train,
        "test": test,
        "evidence": {
            "rival_axis": rival,
            "demo_distinguishes_rival": demo_distinguishes,
            "query_distinguishes_rival": query_distinguishes,
            "racket_python_parity": True,
            "query_output": copy.deepcopy(chosen_outputs[3]),
            "rival_query_output": copy.deepcopy(rival_outputs[3]),
        },
    }


class _RacketLabeler:
    """Reuse one exact bridge per parameter setting during evidence creation."""

    def __init__(self) -> None:
        from puzzle_generators.runner import _open_bridge_with_rule

        self._open = _open_bridge_with_rule
        self._bridges: dict[str, tuple[object, str]] = {}

    def __call__(self, grid: Iterable[Iterable[int]], axis: str) -> list[list[int]]:
        from puzzle_generators.runner import _apply_rule

        axis = _validate_axis(axis)
        if axis not in self._bridges:
            self._bridges[axis] = self._open(callable_racket_rule(axis))
        bridge, function_name = self._bridges[axis]
        return _apply_rule(bridge, function_name, _copy_grid(grid))

    def close(self) -> None:
        for bridge, _ in self._bridges.values():
            try:
                bridge.shutdown()
            except Exception:
                pass
        self._bridges.clear()


def _find_inputs(
    *, seed: int, start: int, difficulty: str, count: int = 4, limit: int = 500,
) -> tuple[list[list[list[int]]], list[int], str]:
    from reviewer_support import find_root, load_selected_generator

    _require_nonnegative_integer("seed", seed)
    _require_nonnegative_integer("start", start)
    generator, _, generator_sha = load_selected_generator(
        TASK_ID, root=find_root(__file__)
    )
    grids: list[list[list[int]]] = []
    indices: list[int] = []
    for sample_index in range(start, start + limit):
        grid = generator.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            scene_family="generalized",
        )
        if apply_python(grid, "vertical") == apply_python(grid, "horizontal"):
            continue
        grids.append(grid)
        indices.append(sample_index)
        if len(grids) == count:
            return grids, indices, generator_sha
    raise RuntimeError(
        f"found only {len(grids)} distinguishing inputs in {limit} attempts"
    )


def build_report(*, seed: int, start: int = 0, difficulty: str = "medium") -> dict:
    axis = choose_mirror_axis(seed)
    grids, indices, generator_sha = _find_inputs(
        seed=seed, start=start, difficulty=difficulty
    )
    labeler = _RacketLabeler()
    try:
        episode = assemble_episode(grids, axis, labeler=labeler)
    finally:
        labeler.close()

    from reviewer_support import public_challenge_bytes
    public_episode = json.loads(public_challenge_bytes(episode))
    return {
        "schema": "arcpuzzles-parametric-mirror-axis-evidence-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": difficulty,
        "requested_start": start,
        "accepted_sample_indices": indices,
        "generator_sha256": generator_sha,
        "parameter": episode["parameter"],
        "canonical_default": {"mirror_axis": DEFAULT_MIRROR_AXIS},
        "rule_sha256": {
            axis_name: _source_hash(source)
            for axis_name, source in RACKET_RULES.items()
        },
        "public_episode": public_episode,
        "private_evidence": episode["evidence"],
    }


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--out-public", type=Path)
    parser.add_argument("--out-evidence", type=Path)
    args = parser.parse_args(argv)

    report = build_report(
        seed=args.seed, start=args.start, difficulty=args.difficulty
    )
    if args.out_public:
        _write_json(args.out_public, report["public_episode"])
    if args.out_evidence:
        _write_json(args.out_evidence, report)
    if not args.out_public and not args.out_evidence:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
