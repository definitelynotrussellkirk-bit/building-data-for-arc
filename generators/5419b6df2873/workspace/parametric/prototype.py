"""Episode-fixed contact-color relay family for ARC task 5419b6df2873.

The default setting is the exact canonical rule.  The alternate setting first
expands top-row markers into columns, then reads the marker color newly touching
a unique lower color-9 probe and fills only remote payload rows carrying that
selected color.  Inputs are sampled independently of the private setting.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from reviewer_support import public_challenge_bytes

TASK_ID = "5419b6df2873"
PARAMETER_NAME = "relay_mode"
MODES = ("columns_only", "contact_color_rows")
DEFAULT_MODE = "columns_only"
HERE = Path(__file__).resolve().parent
PROGRAM_FILES = {
    "columns_only": HERE / "canonical.rkt",
    "contact_color_rows": HERE / "contact_color_rows.rkt",
}
WRONG_ORDER_PROGRAM = (HERE / "wrong_order.rkt").read_text(encoding="utf-8")


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    markers: int
    probe_side: str
    selected_rows: int
    other_rows: int
    seeds_per_row: int = 1
    decoy_probes: int = 1
    boundary: bool = False


DEMO_PROFILES = (
    Profile(6, 8, 3, "right", 2, 1),
    Profile(7, 9, 3, "left", 2, 1),
    Profile(8, 10, 4, "right", 2, 1),
    Profile(9, 11, 4, "left", 2, 1),
    Profile(10, 12, 5, "right", 2, 1),
    Profile(10, 13, 5, "left", 2, 1),
)
QUERY_PROFILES = (
    Profile(11, 14, 3, "right", 2, 2, 1, 1),
    Profile(14, 18, 4, "left", 2, 2, 1, 2),
    Profile(22, 25, 5, "right", 3, 2, 2, 2),
    Profile(30, 30, 5, "right", 4, 3, 2, 3, True),
)


def _mode(value: Any) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {MODES}, found {value!r}")
    return value


def _validate_request(seed: Any, demos: Any, queries: Any) -> tuple[int, int, int]:
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must equal 4")
    return seed, demos, queries


def program_for(mode: str) -> str:
    return PROGRAM_FILES[_mode(mode)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _marker_layout(rng: random.Random, profile: Profile) -> tuple[list[int], int, int]:
    width = profile.width
    if profile.boundary:
        selected_col = width - 2
        probe_col = width - 1
        remaining = [0, 5, 12, 20]
        columns = [selected_col, *remaining[: profile.markers - 1]]
        return sorted(columns), selected_col, probe_col

    for _ in range(500):
        selected_col = rng.randrange(2, width - 2)
        probe_col = selected_col + (1 if profile.probe_side == "right" else -1)
        forbidden = {selected_col, probe_col}
        other_neighbor = probe_col + (1 if profile.probe_side == "right" else -1)
        if 0 <= other_neighbor < width:
            forbidden.add(other_neighbor)
        allowed = [c for c in range(width) if c not in forbidden]
        if len(allowed) < profile.markers - 1:
            continue
        others = rng.sample(allowed, profile.markers - 1)
        columns = sorted([selected_col, *others])
        free_decoys = _free_decoy_columns(width, set(columns), probe_col)
        nonselected_decoys = [
            c for c in free_decoys
            if min(columns, key=lambda marker: (abs(marker - c), marker)) != selected_col
        ]
        if selected_col != columns[0] and nonselected_decoys:
            return columns, selected_col, probe_col
    raise RuntimeError("could not construct marker layout")


def _free_decoy_columns(width: int, marker_columns: set[int], active_probe_col: int) -> list[int]:
    result = []
    for c in range(width):
        if c == active_probe_col or c in marker_columns:
            continue
        if c > 0 and c - 1 in marker_columns:
            continue
        if c + 1 < width and c + 1 in marker_columns:
            continue
        result.append(c)
    return result


def _payload_columns(rng: random.Random, width: int, marker_columns: set[int], probe_col: int, count: int) -> list[int]:
    candidates = [c for c in range(width) if c not in marker_columns and c != probe_col]
    rng.shuffle(candidates)
    if len(candidates) < count:
        raise RuntimeError("not enough payload columns")
    return candidates[:count]


def _build_grid(seed: int, split: str, index: int, profile: Profile) -> list[list[int]]:
    rng = _rng(seed, split, index)
    h, w = profile.height, profile.width
    marker_columns, selected_col, probe_col = _marker_layout(rng, profile)
    marker_set = set(marker_columns)

    palette = sorted(rng.sample(range(1, 9), profile.markers))
    selected_color = palette[len(palette) // 2]
    other_colors = [color for color in palette if color != selected_color]
    rng.shuffle(other_colors)
    color_by_column = {selected_col: selected_color}
    for column, color in zip([c for c in marker_columns if c != selected_col], other_colors):
        color_by_column[column] = color

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for column in marker_columns:
        grid[0][column] = color_by_column[column]

    # Keep the true probe after every decoy in row-major order.  This makes the
    # tempting "nearest marker to the first 9" policy observably wrong.
    probe_row = h - 1
    grid[probe_row][probe_col] = 9
    occupied: set[tuple[int, int]] = {(probe_row, probe_col)}

    decoy_columns = _free_decoy_columns(w, marker_set, probe_col)
    first_decoys = [
        c for c in decoy_columns
        if min(marker_columns, key=lambda marker: (abs(marker - c), marker)) != selected_col
    ]
    if not first_decoys:
        raise RuntimeError("profile lacks a nonselected nearest-marker decoy")
    rng.shuffle(first_decoys)
    first_decoy = (1, first_decoys[0])
    grid[first_decoy[0]][first_decoy[1]] = 9
    occupied.add(first_decoy)

    remaining_decoys = profile.decoy_probes - 1
    candidates = [
        (r, c)
        for r in range(1, h)
        for c in decoy_columns
        if (r, c) not in occupied
    ]
    rng.shuffle(candidates)
    placed_decoys = 0
    for row, column in candidates:
        if placed_decoys == remaining_decoys:
            break
        left_is_probe = column > 0 and grid[row][column - 1] == 9
        right_is_probe = column + 1 < w and grid[row][column + 1] == 9
        if left_is_probe or right_is_probe:
            continue
        grid[row][column] = 9
        occupied.add((row, column))
        placed_decoys += 1
        if placed_decoys == remaining_decoys:
            break
    if placed_decoys != remaining_decoys:
        raise RuntimeError("could not place all nonadjacent decoy probes")

    lower_rows = [r for r in range(1, h) if r != probe_row]
    rng.shuffle(lower_rows)
    requirements = [(selected_color, profile.selected_rows)] + [
        (color, profile.other_rows) for color in other_colors
    ]
    needed = sum(count for _, count in requirements)
    if needed > len(lower_rows):
        raise RuntimeError("profile lacks enough distinct payload rows")

    cursor = 0
    for color, row_count in requirements:
        for row in lower_rows[cursor : cursor + row_count]:
            forbidden = {probe_col}
            for c, value in enumerate(grid[row]):
                if value == 9:
                    forbidden.update({c - 1, c, c + 1})
            choices = [
                c for c in range(w)
                if c not in marker_set and c not in forbidden and grid[row][c] == 0
            ]
            rng.shuffle(choices)
            if len(choices) < profile.seeds_per_row:
                raise RuntimeError("not enough isolated payload columns")
            for column in choices[: profile.seeds_per_row]:
                grid[row][column] = color
                occupied.add((row, column))
        cursor += row_count

    if profile.boundary:
        # Marker at the top-left and the active probe at the bottom-right make
        # all four boundaries semantically populated rather than padded.
        assert grid[0][0] != 0 and grid[h - 1][w - 1] == 9
    return grid


def columns_only_output(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for c, color in enumerate(grid[0]):
        if color:
            for r in range(h):
                out[r][c] = color
    return out


def _active_contacts(grid: list[list[int]], base: list[list[int]]) -> list[dict[str, int]]:
    h, w = len(grid), len(grid[0])
    contacts = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] != 9:
                continue
            left = base[r][c - 1] if c > 0 else 0
            right = base[r][c + 1] if c + 1 < w else 0
            color = left if left else right
            if color:
                contacts.append({"row": r, "column": c, "left": left, "right": right, "color": color})
    return contacts


def dependency_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    base = columns_only_output(grid)
    contacts = _active_contacts(grid, base)
    selected = contacts[0]["color"] if contacts else 0
    selected_rows = sorted(
        r for r in range(1, len(grid)) if selected and any(value == selected for value in grid[r])
    )
    nonselected_rows = sorted(
        r
        for r in range(1, len(grid))
        if any(value not in (0, 9, selected) for value in grid[r])
    )
    return {
        "selected_color": selected,
        "active_probes": contacts,
        "selected_payload_rows": selected_rows,
        "nonselected_payload_rows": nonselected_rows,
    }


def _fill_rows(base: list[list[int]], rows: list[int], color: int) -> list[list[int]]:
    out = [row[:] for row in base]
    if color:
        for r in rows:
            out[r] = [color] * len(out[r])
    return out


def contact_color_rows_output(grid: list[list[int]]) -> list[list[int]]:
    base = columns_only_output(grid)
    info = dependency_intermediate(grid)
    return _fill_rows(base, info["selected_payload_rows"], info["selected_color"])


def output_for(grid: list[list[int]], mode: str) -> list[list[int]]:
    mode = _mode(mode)
    return columns_only_output(grid) if mode == "columns_only" else contact_color_rows_output(grid)


def wrong_order_output(grid: list[list[int]]) -> list[list[int]]:
    """Ablation: inspect probe neighbors before column expansion, yielding no selector."""
    base = columns_only_output(grid)
    h, w = len(grid), len(grid[0])
    selected = 0
    for r in range(1, h):
        for c in range(w):
            if selected or grid[r][c] != 9:
                continue
            left = grid[r][c - 1] if c > 0 else 0
            right = grid[r][c + 1] if c + 1 < w else 0
            selected = left if left else right
    rows = sorted(r for r in range(1, h) if selected and any(v == selected for v in grid[r]))
    return _fill_rows(base, rows, selected)


def _select_rows(grid: list[list[int]], selected: int) -> list[int]:
    return sorted(r for r in range(1, len(grid)) if selected and selected in grid[r])


def _preserve_lower(grid):
    out = [row[:] for row in grid]
    for c, color in enumerate(grid[0]):
        if color:
            for r in range(len(grid)):
                out[r][c] = color
    return out


def _copy_then_contact(grid):
    out = _preserve_lower(grid)
    info = dependency_intermediate(grid)
    return _fill_rows(out, info["selected_payload_rows"], info["selected_color"])


def _all_payload_rows(grid):
    base = columns_only_output(grid)
    out = [row[:] for row in base]
    for r in range(1, len(grid)):
        color = next((v for v in grid[r] if v not in (0, 9)), 0)
        if color:
            out[r] = [color] * len(out[r])
    return out


def _probe_rows_nine(grid):
    base = columns_only_output(grid)
    rows = [r for r in range(1, len(grid)) if 9 in grid[r]]
    return _fill_rows(base, rows, 9)


def _side_contact(grid, side: str):
    base = columns_only_output(grid)
    selected = 0
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r]):
            if selected or value != 9:
                continue
            if side == "left" and c > 0:
                selected = base[r][c - 1]
            if side == "right" and c + 1 < len(grid[0]):
                selected = base[r][c + 1]
    return _fill_rows(base, _select_rows(grid, selected), selected)


def _marker_selected(grid, selector: Callable[[list[tuple[int, int]]], tuple[int, int]]):
    markers = [(c, v) for c, v in enumerate(grid[0]) if v]
    selected = selector(markers)[1]
    return _fill_rows(columns_only_output(grid), _select_rows(grid, selected), selected)


def _nearest_first_probe(grid):
    probes = [(r, c) for r in range(1, len(grid)) for c, v in enumerate(grid[r]) if v == 9]
    markers = [(c, v) for c, v in enumerate(grid[0]) if v]
    if not probes:
        return columns_only_output(grid)
    _, pc = probes[0]
    selected = min(markers, key=lambda item: (abs(item[0] - pc), item[0]))[1]
    return _fill_rows(columns_only_output(grid), _select_rows(grid, selected), selected)


def _payload_columns_relay(grid):
    base = columns_only_output(grid)
    info = dependency_intermediate(grid)
    selected = info["selected_color"]
    out = [row[:] for row in base]
    for c in range(len(grid[0])):
        if any(grid[r][c] == selected for r in range(1, len(grid))):
            for r in range(len(grid)):
                out[r][c] = selected
    return out


def _relay_without_columns(grid):
    info = dependency_intermediate(grid)
    zero = [[0 for _ in row] for row in grid]
    return _fill_rows(zero, info["selected_payload_rows"], info["selected_color"])


def _first_payload_row_only(grid):
    base = columns_only_output(grid)
    info = dependency_intermediate(grid)
    rows = info["selected_payload_rows"][:1]
    return _fill_rows(base, rows, info["selected_color"])


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "preserve_lower_cells": _preserve_lower,
    "copy_then_contact_rows": _copy_then_contact,
    "all_payload_rows": _all_payload_rows,
    "probe_rows_color_9": _probe_rows_nine,
    "left_contact_only": lambda grid: _side_contact(grid, "left"),
    "right_contact_only": lambda grid: _side_contact(grid, "right"),
    "leftmost_marker_color": lambda grid: _marker_selected(grid, lambda rows: min(rows)),
    "largest_marker_color": lambda grid: _marker_selected(grid, lambda rows: max(rows, key=lambda x: x[1])),
    "smallest_marker_color": lambda grid: _marker_selected(grid, lambda rows: min(rows, key=lambda x: x[1])),
    "nearest_marker_to_first_probe": _nearest_first_probe,
    "payload_columns_not_rows": _payload_columns_relay,
    "relay_rows_without_columns": _relay_without_columns,
    "first_payload_row_only": _first_payload_row_only,
    "wrong_order": wrong_order_output,
}


def generate_episode(seed: int, mode: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed, demos, queries = _validate_request(seed, demos, queries)
    mode = _mode(mode)
    train_inputs = [_build_grid(seed, "demo", i, DEMO_PROFILES[i]) for i in range(demos)]
    test_inputs = [_build_grid(seed, "query", i, QUERY_PROFILES[i]) for i in range(queries)]
    pairs = lambda grids: [{"input": grid, "output": output_for(grid, mode)} for grid in grids]
    return {
        "train": pairs(train_inputs),
        "test": pairs(test_inputs),
        "program_solution": program_for(mode),
        "private": {"task_id": TASK_ID, PARAMETER_NAME: mode, "seed": seed},
    }


def audit_episode(episode: dict[str, Any], selected_mode: str) -> dict[str, Any]:
    selected_mode = _mode(selected_mode)
    train = episode["train"]
    test = episode["test"]
    settings = {mode: (lambda grid, mode=mode: output_for(grid, mode)) for mode in MODES}
    declared = [
        mode
        for mode, candidate in settings.items()
        if all(candidate(pair["input"]) == pair["output"] for pair in train)
    ]
    candidate_rows = []
    ambiguous = []
    for name, candidate in {**settings, **RIVALS}.items():
        fits = all(candidate(pair["input"]) == pair["output"] for pair in train)
        disagreements = [
            i for i, pair in enumerate(test) if candidate(pair["input"]) != pair["output"]
        ]
        candidate_rows.append({"name": name, "fits_demos": fits, "query_disagreements": disagreements})
        if name not in settings and fits and disagreements:
            ambiguous.append(name)
    return {
        "selected_mode": selected_mode,
        "declared_survivors": declared,
        "ambiguous_query_rivals": ambiguous,
        "tested_rivals": len(RIVALS),
        "candidates": candidate_rows,
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside the stored query range")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return public_challenge_bytes(public_turn(episode, query_index))


def public_turn_id(episode: dict[str, Any], query_index: int) -> str:
    return hashlib.sha256(public_turn_bytes(episode, query_index)).hexdigest()


def write_public_turns(episode: dict[str, Any], directory: Path) -> list[dict[str, Any]]:
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(len(episode["test"])):
        raw = public_turn_bytes(episode, index)
        digest = hashlib.sha256(raw).hexdigest()
        path = directory / f"{digest}.json"
        path.write_bytes(raw)
        rows.append({"query_index": index, "path": str(path), "sha256": digest, "bytes": len(raw)})
    return rows
