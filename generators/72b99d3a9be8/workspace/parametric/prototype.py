"""Parametric reflector-color family for 72b99d3a9be8.

The canonical source treats color 2 as reflecting line walls and color 3 as a
pass-through distractor.  The alternative swaps that semantic role: color 3
reflects while color 2 is traversed and painted over.  Every generated input
contains both colors on the seed's backward ray with opposing orientations, so
the selected input-derived bounce-event sequence changes before rendering.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "72b99d3a9be8"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE, BASE_PATH, BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
REFLECTOR_COLORS = (2, 3)
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
_LIMIT = 2**63 - 1

_COLOR_NEEDLES = (
    "(= (at g (- r 1) c) 2)",
    "(= (at g (+ r 1) c) 2)",
    "((= (at g nr nc) 2)",
)

# The first two profiles deliberately cross diagonal and wall-orientation cues:
# a minimum lesson therefore demonstrates both reflection branches.
_PROFILES: tuple[dict[str, Any], ...] = (
    {"name": "demo_dr_h_12", "h": 12, "w": 12, "diagonal": "down_right", "wall_orientation": "horizontal", "n_bars": 2},
    {"name": "demo_dl_v_13x15", "h": 13, "w": 15, "diagonal": "down_left", "wall_orientation": "vertical", "n_bars": 3},
    {"name": "demo_dr_v_15x13", "h": 15, "w": 13, "diagonal": "down_right", "wall_orientation": "vertical", "n_bars": 4},
    {"name": "demo_dl_h_16x17", "h": 16, "w": 17, "diagonal": "down_left", "wall_orientation": "horizontal", "n_bars": 5},
    {"name": "demo_dr_h_18x16", "h": 18, "w": 16, "diagonal": "down_right", "wall_orientation": "horizontal", "n_bars": 4},
    {"name": "demo_dl_v_20x19", "h": 20, "w": 19, "diagonal": "down_left", "wall_orientation": "vertical", "n_bars": 5},
    {"name": "query_dr_v_21x23", "h": 21, "w": 23, "diagonal": "down_right", "wall_orientation": "vertical", "n_bars": 5},
    {"name": "query_dl_h_23x21", "h": 23, "w": 21, "diagonal": "down_left", "wall_orientation": "horizontal", "n_bars": 5},
    {"name": "query_dr_h_26x28", "h": 26, "w": 28, "diagonal": "down_right", "wall_orientation": "horizontal", "n_bars": 5},
    {"name": "query_dl_v_30", "h": 30, "w": 30, "diagonal": "down_left", "wall_orientation": "vertical", "n_bars": 5, "heavy": True},
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must lie in {low}..{high}")
    return value


def _reflector_color(value: Any) -> int:
    if type(value) is not int or value not in REFLECTOR_COLORS:
        raise ValueError(f"reflector_color must be one of {REFLECTOR_COLORS}")
    return value


def program_for(reflector_color: int) -> str:
    reflector_color = _reflector_color(reflector_color)
    if reflector_color == 2:
        return CANONICAL_PROGRAM
    result = CANONICAL_PROGRAM
    for needle in _COLOR_NEEDLES:
        if result.count(needle) != 1:
            raise RuntimeError(f"canonical source no longer contains exactly one {needle!r}")
        result = result.replace(needle, needle[:-2] + "3)")
    return result


def output_for(grid: list[list[int]], reflector_color: int) -> list[list[int]]:
    return BASE.trace_rule(deepcopy(grid), reflector_color=_reflector_color(reflector_color))["output"]


def dependency_intermediate(grid: list[list[int]], reflector_color: int) -> dict[str, Any]:
    reflector_color = _reflector_color(reflector_color)
    trace = BASE.trace_rule(deepcopy(grid), reflector_color=reflector_color)
    return {
        "reflector_color": reflector_color,
        "seed_direction": trace["direction"],
        "bounce_events": trace["bounce_events"],
        "crossed_colors": sorted(trace["crossed_colors"]),
    }


def _coerce_grid(grid: list[list[int]]) -> list[list[int]]:
    values, errors = BASE._coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    return values


def _trace_variant(grid: list[list[int]], reflector_color: int, mode: str) -> list[list[int]]:
    """Small declared rival family, independent from the selected renderer."""
    reflector_color = _reflector_color(reflector_color)
    values = _coerce_grid(grid)
    h, w = len(values), len(values[0])
    ones = [(r, c) for r, row in enumerate(values) for c, cell in enumerate(row) if cell == 1]
    direction = BASE._seed_direction(ones) or (1, 1)
    output = deepcopy(values)

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < h and 0 <= c < w

    def orientation(r: int, c: int) -> str:
        up = in_bounds(r - 1, c) and values[r - 1][c] == reflector_color
        down = in_bounds(r + 1, c) and values[r + 1][c] == reflector_color
        return "vertical" if up or down else "horizontal"

    def walk(start: tuple[int, int], dr: int, dc: int) -> None:
        nonlocal output
        r, c = start
        fuel = h * w * 4
        while fuel > 0:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                return
            cell = values[nr][nc]
            if cell == reflector_color:
                if mode == "stop_at_reflector":
                    return
                if mode == "straight":
                    output[nr][nc] = 1
                    r, c = nr, nc
                    fuel -= 1
                    continue
                wall = orientation(nr, nc)
                if mode == "wrong_axis":
                    if wall == "horizontal":
                        dc = -dc
                    else:
                        dr = -dr
                else:
                    if wall == "horizontal":
                        dr = -dr
                    else:
                        dc = -dc
                fuel -= 1
                continue
            output[nr][nc] = 1
            r, c = nr, nc
            fuel -= 1

    if not ones:
        raise ValueError("grid contains no color-1 seed")
    by_row = sorted(ones, key=lambda p: p[0])
    if mode != "backward_only":
        walk(by_row[-1], direction[0], direction[1])
    if mode != "forward_only":
        walk(by_row[0], -direction[0], -direction[1])
    return output


def _candidate_names() -> tuple[str, ...]:
    return (
        "setting:2",
        "setting:3",
        "shortcut:identity",
        "shortcut:straight",
        "shortcut:stop_at_reflector",
        "shortcut:wrong_axis",
        "shortcut:forward_only",
        "shortcut:backward_only",
    )


def _prediction(grid: list[list[int]], selected: int, candidate: str) -> list[list[int]]:
    selected = _reflector_color(selected)
    if candidate.startswith("setting:"):
        return output_for(grid, int(candidate.split(":", 1)[1]))
    if candidate == "shortcut:identity":
        return deepcopy(grid)
    mode = candidate.split(":", 1)[1]
    return _trace_variant(grid, selected, mode)


def audit_episode(episode: dict[str, Any], selected: int) -> dict[str, Any]:
    selected = _reflector_color(selected)
    survivors: list[str] = []
    refutations: dict[str, int | str] = {}
    for candidate in _candidate_names():
        first_failure = None
        try:
            for index, pair in enumerate(episode["train"]):
                if _prediction(pair["input"], selected, candidate) != pair["output"]:
                    first_failure = index
                    break
        except (KeyError, TypeError, ValueError) as exc:
            refutations[candidate] = f"invalid prediction: {exc}"
            continue
        if first_failure is None:
            survivors.append(candidate)
        else:
            refutations[candidate] = first_failure
    ambiguous = []
    for candidate in survivors:
        if candidate == f"setting:{selected}":
            continue
        if any(_prediction(pair["input"], selected, candidate) != pair["output"]
               for pair in episode["test"]):
            ambiguous.append(candidate)
    return {
        "selected": selected,
        "rivals": list(_candidate_names()),
        "survivors": survivors,
        "ambiguous_query_rivals": ambiguous,
        "refutations": refutations,
        "scope": "finite declared setting and shortcut family; not universal uniqueness",
    }


def _strong(grid: list[list[int]]) -> bool:
    serial: dict[int, str] = {}
    for color in REFLECTOR_COLORS:
        expected = output_for(grid, color)
        serial[color] = json.dumps(expected, separators=(",", ":"))
        intermediate = dependency_intermediate(grid, color)
        if not intermediate["bounce_events"]:
            return False
        # The earlier selected-color reflector legitimately redirects the ray
        # before it can cross the later other-color wall.  Require the selected
        # reflector to be exercised and both semantic colors to be present in
        # the input, rather than demanding an impossible post-bounce crossing.
        if color not in set(intermediate["crossed_colors"]):
            return False
        if not {2, 3} <= {cell for row in grid for cell in row}:
            return False
        for candidate in _candidate_names():
            if candidate == f"setting:{color}":
                continue
            try:
                if _prediction(grid, color, candidate) == expected:
                    return False
            except (TypeError, ValueError):
                continue
    return serial[2] != serial[3]


def _rng(seed: int, slot: int, attempt: int = 0) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{slot}|{attempt}|reflector-color-v1".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _add_heavy_decoys(grid: list[list[int]]) -> None:
    """Add a dense, distant two-color fixture without changing the rule class."""
    h, w = len(grid), len(grid[0])
    # Two 4x5 striped blocks in opposite corners add 40 foreground cells.  Fill
    # only zeros so the seed and causal reflectors always remain intact.
    regions = ((1, w - 6), (h - 5, 1))
    for top, left in regions:
        for dr in range(4):
            for dc in range(5):
                r, c = top + dr, left + dc
                if grid[r][c] == 0:
                    grid[r][c] = 2 if (dr + dc) % 2 == 0 else 3


def _scene(seed: int, slot: int, profile: dict[str, Any]) -> list[list[int]]:
    for attempt in range(512):
        rng = _rng(seed, slot, attempt)
        grid = BASE._construct_scene(
            profile["h"], profile["w"], profile["diagonal"],
            profile["wall_orientation"], profile["n_bars"], rng,
        )
        if profile.get("heavy"):
            _add_heavy_decoys(grid)
        if BASE.self_check(grid):
            continue
        if profile.get("heavy"):
            nonzero = sum(cell != 0 for row in grid for cell in row)
            changed = min(
                sum(a != b for row_a, row_b in zip(grid, output_for(grid, color)) for a, b in zip(row_a, row_b))
                for color in REFLECTOR_COLORS
            )
            if nonzero < 45 or changed < 20:
                continue
        if _strong(grid):
            return grid
    raise RuntimeError(f"could not construct strong scene {profile['name']}")


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _thaw(grid: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(row) for row in grid]


@lru_cache(maxsize=64)
def _episode_inputs(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(_freeze(_scene(seed, index, profile)) for index, profile in enumerate(_PROFILES))


def generate_episode(seed: int, reflector_color: int, demos: int, queries: int) -> dict[str, Any]:
    seed = _literal_int("seed", seed, 0, _LIMIT)
    reflector_color = _reflector_color(reflector_color)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    stored = _episode_inputs(seed)
    demo_inputs = [_thaw(grid) for grid in stored[:demos]]
    query_inputs = [_thaw(grid) for grid in stored[len(_PROFILES) - QUERY_COUNT:]]
    all_inputs = [*demo_inputs, *query_inputs]
    pairs = [
        {"input": deepcopy(grid), "output": output_for(grid, reflector_color)}
        for grid in all_inputs
    ]
    episode = {
        "train": pairs[:demos],
        "test": pairs[demos:demos + queries],
        "program_solution": program_for(reflector_color),
    }
    audit = audit_episode(episode, reflector_color)
    if audit["survivors"] != [f"setting:{reflector_color}"] or audit["ambiguous_query_rivals"]:
        raise RuntimeError(f"teaching audit failed: {audit}")
    return deepcopy(episode)
