#!/usr/bin/env python3
"""Isolated episode-level motion variant; canonical production remains top-right."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "3dc5b297cfa2"
GENERATOR_SHA256 = "bba8a758eeed3d632897a59bc11f4cc91199364ba7cd2a16c4c69a1bedf9c962"
CANONICAL_RULE_HASH = "69b3b2d19383"
MOVING_HALVES = ("top", "bottom")
DIRECTIONS = ("right", "left")
SETTINGS = tuple((half, direction) for half in MOVING_HALVES for direction in DIRECTIONS)


def _validate_setting(moving_half: Any, direction: Any) -> tuple[str, str]:
    if type(moving_half) is not str or moving_half not in MOVING_HALVES:
        raise ValueError(f"moving_half must be one of {MOVING_HALVES!r}")
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS!r}")
    return moving_half, direction


def choose_parameters(
    seed: int,
    *,
    moving_half: str | None = None,
    direction: str | None = None,
) -> dict[str, str]:
    """Choose both hidden rule parameters once for the entire episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal integer")
    digest = hashlib.sha256(f"{TASK_ID}:motion-v1:{seed}".encode()).digest()
    chosen_half = MOVING_HALVES[digest[0] % len(MOVING_HALVES)] if moving_half is None else moving_half
    chosen_direction = DIRECTIONS[digest[1] % len(DIRECTIONS)] if direction is None else direction
    chosen_half, chosen_direction = _validate_setting(chosen_half, chosen_direction)
    return {"moving_half": chosen_half, "direction": chosen_direction}


def _canonical_program(*, root: Path | None = None) -> str:
    root = Path(root) if root is not None else find_root(__file__)
    rows = []
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    programs = {row["program_solution"] for row in rows}
    if not rows or len(programs) != 1:
        raise ValueError(
            f"expected one selected canonical program for {TASK_ID}, "
            f"found {len(rows)} rows and {len(programs)} distinct programs"
        )
    return programs.pop()


def materialize_program(
    moving_half: str = "top",
    direction: str = "right",
    *,
    root: Path | None = None,
) -> str:
    """Return the exact Racket program for one setting.

    The canonical setting returns the selected authority text byte-for-byte.
    Nearby settings alter only the moved bbox half and horizontal sign.
    """
    moving_half, direction = _validate_setting(moving_half, direction)
    canonical = _canonical_program(root=root)
    if moving_half == "top" and direction == "right":
        return canonical

    condition_source = "(<= r rmid)"
    column_source = "(+ c shift)"
    if canonical.count(condition_source) != 1 or canonical.count(column_source) != 1:
        raise ValueError("canonical motion clauses changed; review the parametric adapter")
    condition = condition_source if moving_half == "top" else "(> r rmid)"
    column = column_source if direction == "right" else "(- c shift)"
    return canonical.replace(condition_source, condition, 1).replace(column_source, column, 1)


def python_transform(grid: Any, moving_half: str, direction: str) -> list[list[int]]:
    """Independent Python oracle for the bounded motion settings."""
    moving_half, direction = _validate_setting(moving_half, direction)
    source = normalize_grid(grid)
    height = len(source)
    width = len(source[0])
    counts = Counter(value for row in source for value in row)
    background = counts.most_common(1)[0][0]
    cells = [
        (row, column, value)
        for row, values in enumerate(source)
        for column, value in enumerate(values)
        if value != background
    ]
    if not cells:
        raise ValueError("input has no non-background shape")
    colors = list(dict.fromkeys(value for _row, _column, value in cells))
    if len(colors) != 2:
        raise ValueError(f"expected exactly two shape colors, got {colors!r}")
    first, second = colors
    rmin = min(row for row, _column, _value in cells)
    rmax = max(row for row, _column, _value in cells)
    cmin = min(column for _row, column, _value in cells)
    cmax = max(column for _row, column, _value in cells)
    rmid = (rmin + rmax) // 2
    nonblack = [cell for cell in cells if cell[2] != 0]
    shift = (
        max(column for _row, column, _value in nonblack)
        - min(column for _row, column, _value in nonblack)
        + 1
        if 0 in colors
        else cmax - cmin + 1
    )
    sign = 1 if direction == "right" else -1
    output = [[background for _column in range(width)] for _row in range(height)]
    for row, column, value in cells:
        swapped = second if value == first else first
        selected = row <= rmid if moving_half == "top" else row > rmid
        new_column = column + sign * shift if selected else column
        if 0 <= new_column < width:
            output[row][new_column] = swapped
    return output


def _execute(bridge: RacketBridge, program: str, grid: Any) -> list[list[int]]:
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected a single (rule! <procedure>) program")
    procedure = program[len("(rule! ") : -1]
    bridge.define_grid("__motion_input__", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({procedure} __motion_input__)"))


def _recenter_for_bidirectional_motion(grid: Any) -> list[list[int]]:
    """Move the whole shape to a center column without changing its pixels."""
    source = normalize_grid(grid)
    height = len(source)
    width = len(source[0])
    counts = Counter(value for row in source for value in row)
    background = counts.most_common(1)[0][0]
    cells = [
        (row, column, value)
        for row, values in enumerate(source)
        for column, value in enumerate(values)
        if value != background
    ]
    cmin = min(column for _row, column, _value in cells)
    cmax = max(column for _row, column, _value in cells)
    bbox_w = cmax - cmin + 1
    target_left = (width - bbox_w) // 2
    delta = target_left - cmin
    result = [[background for _column in range(width)] for _row in range(height)]
    for row, column, value in cells:
        result[row][column + delta] = value
    return result


def _episode_inputs(seed: int, *, root: Path) -> tuple[list[list[list[int]]], str]:
    generator, _path, source_hash = load_selected_generator(TASK_ID, root=root)
    if source_hash != GENERATOR_SHA256:
        raise ValueError(
            "selected generator changed; update the source pin only after re-running prototype evidence"
        )
    grids: list[list[list[int]]] = []
    for index in range(4):
        grid = generator.generate(
            seed,
            index,
            difficulty="medium",
            grid_h=16,
            grid_w=24,
            bbox_h=8 if index % 2 == 0 else 6,
            bbox_w=5,
            background_color=8,
            black_shape=index % 2 == 0,
        )
        centered = _recenter_for_bidirectional_motion(grid)
        errors = generator.self_check(centered)
        if errors:
            raise ValueError(f"centered prototype input is outside canonical grammar: {errors}")
        grids.append(centered)
    return grids, source_hash


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return demonstrations plus masked query inputs, without hidden semantics."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def generate_episode(
    seed: int,
    *,
    moving_half: str | None = None,
    direction: str | None = None,
    bridge: RacketBridge,
    root: Path | None = None,
) -> dict[str, Any]:
    """Materialize one four-pair episode and score all parameter rivals."""
    chosen = choose_parameters(seed, moving_half=moving_half, direction=direction)
    root = Path(root) if root is not None else find_root(__file__)
    grids, source_hash = _episode_inputs(seed, root=root)

    programs = {
        f"{half}_{motion}": materialize_program(half, motion, root=root)
        for half, motion in SETTINGS
    }
    outputs: dict[str, list[list[list[int]]]] = {}
    for half, motion in SETTINGS:
        key = f"{half}_{motion}"
        racket_outputs = [_execute(bridge, programs[key], grid) for grid in grids]
        python_outputs = [python_transform(grid, half, motion) for grid in grids]
        if racket_outputs != python_outputs:
            raise AssertionError(f"Racket/Python mismatch for {key}")
        outputs[key] = racket_outputs

    separating_pair_indices: list[int] = []
    for index in range(len(grids)):
        rendered = {
            json.dumps(outputs[f"{half}_{motion}"][index], separators=(",", ":"))
            for half, motion in SETTINGS
        }
        if len(rendered) == len(SETTINGS):
            separating_pair_indices.append(index)
    if separating_pair_indices != list(range(len(grids))):
        raise ValueError(
            "every demonstration and query must distinguish all four parameter settings"
        )

    chosen_key = f"{chosen['moving_half']}_{chosen['direction']}"
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(outputs[chosen_key][index])}
        for index, grid in enumerate(grids)
    ]
    alternatives = {
        key: deepcopy(value)
        for key, value in outputs.items()
        if key != chosen_key
    }
    program = programs[chosen_key]
    return {
        "schema": "arcpuzzles-split-motion-prototype-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": chosen,
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "generator_sha256": source_hash,
        "train": pairs[:3],
        "test": pairs[3:],
        "alternative_outputs": alternatives,
        "separating_pair_indices": separating_pair_indices,
        "variant_approved": False,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _file_records(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    args.out.mkdir(parents=True, exist_ok=False)

    with RacketBridge(timeout=20, startup_timeout=60) as bridge:
        canonical = materialize_program(root=root)
        anchors = canonical_pairs(TASK_ID, root=root)
        for pair in anchors:
            if _execute(bridge, canonical, pair["input"]) != pair["output"]:
                raise AssertionError("canonical Racket authority failed a retained pair")

        explicit_settings = [
            (101, "top", "right"),
            (102, "top", "left"),
            (103, "bottom", "right"),
            (104, "bottom", "left"),
        ]
        episodes = [
            generate_episode(
                seed,
                moving_half=half,
                direction=motion,
                bridge=bridge,
                root=root,
            )
            for seed, half, motion in explicit_settings
        ]

    for index, episode in enumerate(episodes):
        _write_json(args.out / f"private/episode-{index:03d}.json", episode)
        _write_json(args.out / f"public/episode-{index:03d}.json", public_challenge(episode))
    for half, motion in SETTINGS:
        (args.out / "private/rules").mkdir(parents=True, exist_ok=True)
        (args.out / f"private/rules/{half}-{motion}.rkt").write_text(
            materialize_program(half, motion, root=root)
        )

    report = {
        "schema": "arcpuzzles-split-motion-prototype-verification-v1",
        "task_id": TASK_ID,
        "generator_sha256": GENERATOR_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_ledger_sha256": hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
        "parameters": {
            "moving_half": {"allowed": list(MOVING_HALVES), "default": "top"},
            "direction": {"allowed": list(DIRECTIONS), "default": "right"},
        },
        "invariants": [
            "unique modal background and one connected two-color shape",
            "floor midpoint split of the shape bounding box",
            "swap both shape colors",
            "canonical black/nonblack shift-magnitude rule",
            "selected half moves horizontally while the other half stays",
        ],
        "input_constraints": {
            "bidirectional_margin": "prototype inputs are recentered so every setting is unclipped",
            "both_halves_and_colors_visible": True,
        },
        "chosen_once_per_episode": True,
        "canonical_pairs_executed": len(anchors),
        "episodes": len(episodes),
        "settings_covered": [
            {"moving_half": half, "direction": motion} for half, motion in SETTINGS
        ],
        "pairs_per_episode": {"demonstrations": 3, "queries": 1},
        "racket_evaluations": len(anchors) + len(episodes) * len(SETTINGS) * 4,
        "all_pairs_separate_all_settings": True,
        "all_racket_labels_match_independent_python": True,
        "runtime": racket_runtime_status(),
        "variant_approved": False,
        "production_parametric_api": False,
        "limits": [
            "Four deterministic episodes and four settings are finite evidence, not universal identifiability.",
            "Prototype inputs use a centered canonical-grammar subset to keep left and right motion unclipped.",
            "No training-value or variant-approval claim is made.",
        ],
    }
    _write_json(args.out / "report.json", report)
    _write_json(
        args.out / "manifest.json",
        {
            "schema": "arcpuzzles-split-motion-prototype-manifest-v1",
            "files": _file_records(args.out),
        },
    )
    print(
        json.dumps(
            {
                "episodes": len(episodes),
                "settings": len(SETTINGS),
                "racket_evaluations": report["racket_evaluations"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
