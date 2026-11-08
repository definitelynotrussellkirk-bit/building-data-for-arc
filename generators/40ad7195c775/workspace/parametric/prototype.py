#!/usr/bin/env python3
"""Proposed episode-level waypoint-choice parameter for ARC 40ad7195c775.

The selected canonical generator and Racket authority remain unchanged.  This
workspace prototype chooses one cell of every three-cell waypoint run—left,
middle, or right—once per episode and verifies every retained label with the
included Racket runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "40ad7195c775"
ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
ALLOWED_WAYPOINT_CHOICES = ("left", "middle", "right")
DEFAULT_WAYPOINT_CHOICE = "middle"
STATUS = "proposed prototype; not production-approved"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def _validate_choice(choice: str) -> None:
    if type(choice) is not str or choice not in ALLOWED_WAYPOINT_CHOICES:
        raise ValueError(f"waypoint_choice must be one of {ALLOWED_WAYPOINT_CHOICES}")


def program_for(choice: str = DEFAULT_WAYPOINT_CHOICE) -> str:
    """Materialize exact Racket for one setting; the default is byte-canonical."""
    _validate_choice(choice)
    source = canonical_program()
    if choice == DEFAULT_WAYPOINT_CHOICE:
        return source

    middle = "(else (nth cols (quotient (length cols) 2)))"
    replacement = {
        "left": "(else (first cols))",
        "right": "(else (nth cols (- (length cols) 1)))",
    }[choice]
    if source.count(middle) != 1:
        raise ValueError("canonical authority changed; waypoint prototype needs review")
    return source.replace(middle, replacement)


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _paint_segment(
    output: list[list[int]],
    row1: int,
    col1: int,
    row2: int,
    col2: int,
    color: int,
) -> None:
    if row1 == row2:
        for col in range(min(col1, col2), max(col1, col2) + 1):
            output[row1][col] = color
    elif col1 == col2:
        for row in range(min(row1, row2), max(row1, row2) + 1):
            output[row][col1] = color
    else:
        raise ValueError("route segments must be axis aligned")


def _selected_col(marker_cols: list[int], choice: str) -> int:
    if not marker_cols:
        raise ValueError("every stripe must contain waypoint cells")
    if choice == "left":
        return marker_cols[0]
    if choice == "middle":
        return marker_cols[len(marker_cols) // 2]
    return marker_cols[-1]


def _solve_normalized(
    grid: list[list[int]],
    endpoint_color: int,
    stripe_color: int,
    waypoint_color: int,
    choice: str,
) -> list[list[int]]:
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    endpoints = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == endpoint_color
    )
    if len(endpoints) != 2:
        raise ValueError("prototype requires exactly two endpoint cells")
    start, goal = endpoints
    stripe_rows = [
        row
        for row in range(height)
        if sum(grid[row][col] == stripe_color for col in range(width)) >= width - 5
    ]
    waypoint_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == waypoint_color
    ]

    current_row, current_col = start[0] + 1, start[1]
    for stripe_row in stripe_rows:
        marker_cols = sorted(col for row, col in waypoint_cells if row == stripe_row)
        marker_col = _selected_col(marker_cols, choice)
        _paint_segment(
            output,
            current_row,
            current_col,
            stripe_row - 1,
            current_col,
            endpoint_color,
        )
        _paint_segment(
            output,
            stripe_row - 1,
            current_col,
            stripe_row - 1,
            marker_col,
            endpoint_color,
        )
        output[stripe_row][marker_col] = endpoint_color
        current_row, current_col = stripe_row + 1, marker_col
    for row in range(current_row, goal[0]):
        output[row][current_col] = endpoint_color
    _paint_segment(output, goal[0], current_col, goal[0], goal[1], endpoint_color)
    return output


def apply_python(grid: list[list[int]], choice: str) -> list[list[int]]:
    """Apply one proposed setting without mutating the input."""
    _validate_choice(choice)
    errors = GENERATOR._valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    palette = GENERATOR._role_colors(grid)
    if palette is None:
        raise ValueError("could not infer semantic color roles")
    _, endpoint, stripe, waypoint = palette
    orientation = GENERATOR._orientation(grid, stripe)
    if orientation == GENERATOR.HORIZONTAL:
        return _solve_normalized(grid, endpoint, stripe, waypoint, choice)
    if orientation == GENERATOR.VERTICAL:
        return _transpose(
            _solve_normalized(_transpose(grid), endpoint, stripe, waypoint, choice)
        )
    raise ValueError("could not infer stripe orientation")


def choose_waypoint_choice(seed: int) -> str:
    if type(seed) is not int:
        raise ValueError("episode seed must be a literal integer")
    return ALLOWED_WAYPOINT_CHOICES[seed % len(ALLOWED_WAYPOINT_CHOICES)]


def build_inputs(seed: int, count: int) -> list[list[list[int]]]:
    """Build deterministic lawful inputs independent of the selected setting."""
    if type(seed) is not int:
        raise ValueError("episode seed must be a literal integer")
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive literal integer")

    inputs = []
    general_count = len(GENERATOR.GENERAL_GEOMETRIES)
    for index in range(count):
        geometry_index = len(GENERATOR.PUBLIC_GEOMETRIES) + (
            (7 * seed + 11 * index) % general_count
        )
        palette_index = (97 * seed + 131 * index) % GENERATOR.PALETTE_COUNT
        scene_code = geometry_index * GENERATOR.PALETTE_COUNT + palette_index
        grid = GENERATOR.generate(
            seed * 1009 + index,
            index,
            difficulty=("easy", "medium", "hard", None)[index % 4],
            scene_code=scene_code,
        )
        inputs.append(grid)
    return inputs


def build_episode(seed: int, *, n_train: int = 3, n_test: int = 1) -> dict[str, Any]:
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive literal integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive literal integer")
    choice = choose_waypoint_choice(seed)
    inputs = build_inputs(seed, n_train + n_test)
    pairs = [
        {"input": grid, "output": apply_python(grid, choice)}
        for grid in inputs
    ]
    program = program_for(choice)
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "private": {
            "seed": seed,
            "waypoint_choice": choice,
            "program": program,
            "program_sha256": _sha256(program.encode()),
            "generator_sha256": GENERATOR_SHA256,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must be one (rule! EXPR) form")
    expression = stripped[len("(rule!") : -1].strip()
    uncommented = "\n".join(
        line.split(";", 1)[0] for line in expression.splitlines()
    ).strip()
    if not uncommented.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(seeds: list[int], out_dir: Path) -> dict[str, Any]:
    """Write public/private episodes and source-bound Racket parity evidence."""
    from arc_repl.racket_bridge import RacketBridge

    if not seeds:
        raise ValueError("at least one seed is required")
    episodes = [build_episode(seed) for seed in seeds]
    represented = {episode["private"]["waypoint_choice"] for episode in episodes}
    if represented != set(ALLOWED_WAYPOINT_CHOICES):
        raise ValueError(
            "retained seeds must cover all settings; "
            f"observed {sorted(represented)}"
        )

    programs = {choice: program_for(choice) for choice in ALLOWED_WAYPOINT_CHOICES}
    checks = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        for episode_index, episode in enumerate(episodes):
            selected = episode["private"]["waypoint_choice"]
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    outputs = {}
                    applications = {}
                    for choice, source in programs.items():
                        application = _application(source, pair["input"])
                        output = bridge.eval_text(application)
                        expected = apply_python(pair["input"], choice)
                        if output != expected:
                            raise AssertionError(
                                f"Racket/Python mismatch: episode {episode_index} "
                                f"{split}[{pair_index}] choice {choice}"
                            )
                        outputs[choice] = output
                        applications[choice] = application
                    if outputs[selected] != pair["output"]:
                        raise AssertionError("selected Racket output disagrees with episode label")
                    distinct = len(
                        {json.dumps(output, separators=(",", ":")) for output in outputs.values()}
                    ) == len(ALLOWED_WAYPOINT_CHOICES)
                    if split == "train" and not distinct:
                        raise AssertionError("demonstration does not distinguish all settings")
                    checks.append(
                        {
                            "episode_index": episode_index,
                            "episode_seed": episode["private"]["seed"],
                            "selected_waypoint_choice": selected,
                            "split": split,
                            "pair_index": pair_index,
                            "input": pair["input"],
                            "outputs": outputs,
                            "settings_distinct": distinct,
                            "applications": applications,
                        }
                    )
    finally:
        bridge.shutdown()

    out_dir.mkdir(parents=True, exist_ok=True)
    for choice, source in programs.items():
        path = out_dir / "rules" / f"waypoint_choice_{choice}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    for index, episode in enumerate(episodes):
        _write_json(out_dir / "public" / f"episode-{index:03d}.json", public_challenge(episode))
        _write_json(out_dir / "private" / f"episode-{index:03d}.json", episode)

    source_path = Path(__file__).resolve()
    manifest = {
        "schema": "40ad7195c775-waypoint-choice-prototype-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "waypoint_choice",
            "allowed_values": list(ALLOWED_WAYPOINT_CHOICES),
            "default": DEFAULT_WAYPOINT_CHOICE,
            "chosen_once_per_episode": True,
            "input_constraints_depending_on_parameter": [
                "each stripe has one contiguous three-cell waypoint run"
            ],
            "meaning": "which cell of each ordered waypoint run the route punches through",
        },
        "invariant_reasoning": [
            "infer background, endpoint, stripe, and waypoint roles by frequency",
            "normalize vertical stripe scenes by transposition",
            "visit the stripes in order and draw an endpoint-colored staircase",
            "preserve all cells outside the route",
        ],
        "seeds": seeds,
        "programs": {
            choice: {
                "source": source,
                "sha256": _sha256(source.encode()),
                "normalized_sha256": _sha256(" ".join(source.split()).encode()),
            }
            for choice, source in programs.items()
        },
        "default_program_exactly_canonical": programs[DEFAULT_WAYPOINT_CHOICE] == canonical_program(),
        "generator_source": str(GENERATOR_PATH),
        "generator_sha256": GENERATOR_SHA256,
        "prototype_source_sha256": _sha256(source_path.read_bytes()),
        "racket_runtime": runtime_identity,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "counts": {
            "episodes": len(episodes),
            "train_pairs": sum(len(episode["train"]) for episode in episodes),
            "test_pairs": sum(len(episode["test"]) for episode in episodes),
            "racket_executions": len(checks) * len(programs),
            "distinguishing_train_pairs": sum(
                row["settings_distinct"] for row in checks if row["split"] == "train"
            ),
        },
        "checks": checks,
        "limitations": [
            "This task-local prototype is not selected, catalog-approved, or admitted for training.",
            "Evidence covers three bounded settings and the retained seeds, not all invented variants.",
            "The demonstrations eliminate only the declared left/middle/right parameter rivals.",
            "The hidden setting is inferred from demonstrations; it is not encoded in the query input.",
        ],
    }
    _write_json(out_dir / "private" / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    manifest = materialize(args.seeds, Path(args.out))
    print(json.dumps({"status": "passed", "counts": manifest["counts"], "out": args.out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
