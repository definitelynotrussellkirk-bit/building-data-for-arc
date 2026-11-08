#!/usr/bin/env python3
"""Proposed episode-level diagonal-orientation extension for task 1d62131e83ca.

The selected production generator and canonical Racket rule remain unchanged.
This task-local prototype adds one hidden parameter, chosen once per complete
lesson: which diagonal axis the two source blocks extend along.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
for dependency in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

from reviewer_support import (  # noqa: E402
    load_selected_generator,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)


TASK_ID = "1d62131e83ca"
ALLOWED_RAY_ORIENTATIONS = ("nw_se", "ne_sw")
DEFAULT_RAY_ORIENTATION = "nw_se"
SETTINGS = ALLOWED_RAY_ORIENTATIONS


_CANONICAL_PROGRAM = """(rule! (lambda (g)
  ;; alt: paint two diagonal rays: blue up-left from the blue bbox, red down-right from the red bbox.
  (let* ((h (rows g))
         (w (cols g))
         (blue (find-color g 1))
         (red (find-color g 2))
         (blue-r0 (min-of fst blue))
         (blue-c0 (min-of snd blue))
         (red-r1 (max-of fst red))
         (red-c1 (max-of snd red)))
    (define (paint-ray out r c dr dc color)
      (if (in-bounds? r c h w)
          (paint-ray (set-cell out r c color) (+ r dr) (+ c dc) dr dc color)
          out))
    (paint-ray
      (paint-ray g (- blue-r0 1) (- blue-c0 1) -1 -1 1)
      (+ red-r1 1) (+ red-c1 1) 1 1 2))))"""

_ALTERNATIVE_PROGRAM = """(rule! (lambda (g)
  ;; Proposed variant: blue up-right from the blue bbox, red down-left from the red bbox.
  (let* ((h (rows g))
         (w (cols g))
         (blue (find-color g 1))
         (red (find-color g 2))
         (blue-r0 (min-of fst blue))
         (blue-c1 (max-of snd blue))
         (red-r1 (max-of fst red))
         (red-c0 (min-of snd red)))
    (define (paint-ray out r c dr dc color)
      (if (in-bounds? r c h w)
          (paint-ray (set-cell out r c color) (+ r dr) (+ c dc) dr dc color)
          out))
    (paint-ray
      (paint-ray g (- blue-r0 1) (+ blue-c1 1) -1 1 1)
      (+ red-r1 1) (- red-c0 1) 1 -1 2))))"""


_BASE_GENERATOR, BASE_SOURCE_PATH, BASE_SOURCE_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int or not 1 <= value <= 8:
        raise ValueError(f"{name} must be an exact integer from 1 through 8")


def _grid_hash(grid: Any) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def select_setting(seed: int) -> str:
    _validate_seed(seed)
    return random.Random(seed ^ 0x1D62131E).choice(SETTINGS)


def _validate_orientation(ray_orientation: str) -> None:
    if type(ray_orientation) is not str or ray_orientation not in SETTINGS:
        raise ValueError(
            "ray_orientation must be one of "
            f"{ALLOWED_RAY_ORIENTATIONS}, got {ray_orientation!r}"
        )


def _solid_2x2_origin(grid: list[list[int]], color: int) -> tuple[int, int] | None:
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    if len(cells) != 4:
        return None
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    expected = {
        (row0, col0),
        (row0 + 1, col0),
        (row0, col0 + 1),
        (row0 + 1, col0 + 1),
    }
    return (row0, col0) if cells == expected else None


def _ray_cells(
    origin: tuple[int, int],
    height: int,
    width: int,
    *,
    color: int,
    ray_orientation: str,
) -> tuple[tuple[int, int], ...]:
    _validate_orientation(ray_orientation)
    row, col = origin
    if ray_orientation == "nw_se":
        if color == 1:
            row, col, drow, dcol = row - 1, col - 1, -1, -1
        else:
            row, col, drow, dcol = row + 2, col + 2, 1, 1
    elif color == 1:
        row, col, drow, dcol = row - 1, col + 2, -1, 1
    else:
        row, col, drow, dcol = row + 2, col - 1, 1, -1

    cells = []
    while 0 <= row < height and 0 <= col < width:
        cells.append((row, col))
        row += drow
        col += dcol
    return tuple(cells)


def _analysis(grid: Any, *, ray_orientation: str) -> dict[str, Any]:
    _validate_orientation(ray_orientation)
    errors: list[str] = []
    if type(grid) is not list or not grid:
        return {"errors": ["grid must be a non-empty list"], "facts": {}}
    if type(grid[0]) is not list or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"], "facts": {}}
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": {}}
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {
            "errors": ["cells must be exact ARC color integers 0 through 9"],
            "facts": {},
        }

    height = len(grid)
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 2}:
        errors.append("input may contain only colors 0, 1, and 2")
    blue = _solid_2x2_origin(grid, 1)
    red = _solid_2x2_origin(grid, 2)
    if blue is None:
        errors.append("color 1 must form exactly one solid 2x2 block")
    if red is None:
        errors.append("color 2 must form exactly one solid 2x2 block")
    if blue is None or red is None:
        return {"errors": errors, "facts": {"height": height, "width": width}}

    blue_block = {
        (blue[0] + drow, blue[1] + dcol)
        for drow in (0, 1)
        for dcol in (0, 1)
    }
    red_block = {
        (red[0] + drow, red[1] + dcol)
        for drow in (0, 1)
        for dcol in (0, 1)
    }
    if blue_block & red_block:
        errors.append("the two source blocks overlap")

    blue_ray = set(
        _ray_cells(
            blue,
            height,
            width,
            color=1,
            ray_orientation=ray_orientation,
        )
    )
    red_ray = set(
        _ray_cells(
            red,
            height,
            width,
            color=2,
            ray_orientation=ray_orientation,
        )
    )
    if not blue_ray:
        errors.append("blue ray is empty for the selected orientation")
    if not red_ray:
        errors.append("red ray is empty for the selected orientation")
    if blue_ray & red_block:
        errors.append("blue ray crosses the red source block")
    if red_ray & blue_block:
        errors.append("red ray crosses the blue source block")
    if blue_ray & red_ray:
        errors.append("blue and red rays collide")

    return {
        "errors": errors,
        "facts": {
            "height": height,
            "width": width,
            "blue_origin": blue,
            "red_origin": red,
            "blue_ray": tuple(sorted(blue_ray)),
            "red_ray": tuple(sorted(red_ray)),
        },
    }


def input_is_valid(grid: Any, *, ray_orientation: str) -> bool:
    return not _analysis(grid, ray_orientation=ray_orientation)["errors"]


def solve(
    grid: Any,
    *,
    ray_orientation: str = DEFAULT_RAY_ORIENTATION,
) -> list[list[int]]:
    analysis = _analysis(grid, ray_orientation=ray_orientation)
    if analysis["errors"]:
        raise ValueError("invalid prototype input: " + "; ".join(analysis["errors"]))
    output = deepcopy(grid)
    for row, col in analysis["facts"]["blue_ray"]:
        output[row][col] = 1
    for row, col in analysis["facts"]["red_ray"]:
        output[row][col] = 2
    return output



def program_for(ray_orientation: str = DEFAULT_RAY_ORIENTATION) -> str:
    """Return the exact Racket reference for one proposed episode setting."""
    _validate_orientation(ray_orientation)
    if ray_orientation == DEFAULT_RAY_ORIENTATION:
        return _CANONICAL_PROGRAM
    return _ALTERNATIVE_PROGRAM


def normalized_program_hash(ray_orientation: str = DEFAULT_RAY_ORIENTATION) -> str:
    normalized = " ".join(program_for(ray_orientation).split()).encode()
    return hashlib.sha256(normalized).hexdigest()


def base_canonical_output(grid: Any) -> list[list[int]]:
    """Execute the selected generator's Python mirror of the canonical rule."""
    return _BASE_GENERATOR.rule_mirror(grid)


def _sample_input(
    seed: int,
    ordinal: int,
    *,
    difficulty: str,
    seen_hashes: set[str],
) -> list[list[int]]:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    for attempt in range(512):
        input_seed = (
            seed * 1_000_003
            + ordinal * 10_007
            + attempt * 7_919
            + 0x1D62131E
        ) & 0x7FFFFFFF
        sample_index = seed * 65_537 + ordinal * 521 + attempt
        grid = _BASE_GENERATOR.generate(
            input_seed, sample_index, difficulty=difficulty
        )
        digest = _grid_hash(grid)
        if digest in seen_hashes:
            continue
        if not all(
            input_is_valid(grid, ray_orientation=setting) for setting in SETTINGS
        ):
            continue
        outputs = {
            setting: solve(grid, ray_orientation=setting) for setting in SETTINGS
        }
        if outputs[SETTINGS[0]] == outputs[SETTINGS[1]]:
            continue
        return grid
    raise RuntimeError(
        f"could not sample distinct common-support input for pair {ordinal}"
    )


def generate_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    ray_orientation: str | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one lesson with a single ray orientation shared by all pairs."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    selected = select_setting(seed) if ray_orientation is None else ray_orientation
    _validate_orientation(selected)

    pairs = []
    seen_hashes: set[str] = set()
    rival = next(setting for setting in SETTINGS if setting != selected)
    for ordinal in range(demo_count + query_count):
        grid = _sample_input(
            seed, ordinal, difficulty=difficulty, seen_hashes=seen_hashes
        )
        digest = _grid_hash(grid)
        seen_hashes.add(digest)
        output = solve(grid, ray_orientation=selected)
        if solve(grid, ray_orientation=rival) == output:
            raise AssertionError("sampled pair does not distinguish ray orientations")
        pairs.append({"input": grid, "output": output})

    return {
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "parameters": {"ray_orientation": selected},
        "program": program_for(selected),
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "seed": seed,
            "difficulty": difficulty,
            "selection_scope": "once_per_episode",
            "demo_count": demo_count,
            "query_count": query_count,
            "allowed_ray_orientations": list(SETTINGS),
            "canonical_default": DEFAULT_RAY_ORIENTATION,
            "base_source_sha256": BASE_SOURCE_SHA256,
            "program_sha256": hashlib.sha256(program_for(selected).encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(selected),
            "input_constraint": (
                "every retained input is collision-free under both orientations "
                "and the two settings produce different outputs"
            ),
        },
    }



def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the explicit visible allowlist, omitting hidden rule data and answers."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a mapping")
    try:
        train = [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ]
        test = [{"input": deepcopy(pair["input"])} for pair in episode["test"]]
    except (KeyError, TypeError) as error:
        raise ValueError("episode requires train demonstrations and test inputs") from error
    return {"train": train, "test": test}


def public_bytes(episode: dict[str, Any]) -> bytes:
    return _public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return _public_challenge_id(public_challenge(episode))
