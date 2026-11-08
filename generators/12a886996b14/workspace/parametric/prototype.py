"""Constructive matched-input episodes for a translation-to-cue relay family.

The canonical setting performs the exact source ARC rule: infer the red-to-green
bounding-box displacement and translate the yellow object onto a blank grid.
The alternate setting keeps that result, reads the unique colored cue adjacent
to the *translated* yellow footprint, and paints every cell of that cue color
(including a remote payload) cyan.  Source-yellow and green-marker cue decoys
make the translated footprint a necessary input-dependent intermediate.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
TASK_ID = "12a886996b14"
FINISHES = ("translate_only", "cue_payload")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
CUE_COLORS = (1, 5, 6)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Each shape contains (0, 0).  Partial-occlusion profiles use an interior cell.
MARKER_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
)
YELLOW_SHAPES = (
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (3, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2)),
)
PAYLOAD_SHAPES = {
    2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
    3: (((0, 0), (0, 1), (1, 0)), ((0, 0), (1, 0), (2, 0))),
    4: (((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0), (0, 1), (0, 2), (1, 1))),
    5: (((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)), ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))),
}

# First two demonstrations deliberately make the destination cue neither the
# lowest color nor the largest payload, so those shortcuts fail visibly.
ROLE_COLOR_SCHEDULE = (
    (5, 1, 6),
    (6, 5, 1),
    (1, 6, 5),
    (5, 6, 1),
    (6, 1, 5),
    (1, 5, 6),
)
# (destination payload size, source-decoy payload size, green-decoy payload size)
PAYLOAD_SIZE_SCHEDULE = (
    (2, 5, 3),
    (3, 5, 4),
    (5, 2, 4),
    (4, 3, 5),
    (2, 4, 5),
    (5, 4, 2),
)
VECTORS = (
    (3, 4),
    (-3, -4),
    (-4, 5),
    (4, -5),
    (0, 6),
    (-5, 0),
    (5, 0),
    (0, -6),
)
PROFILES = (
    (12, 16, True, None),
    (14, 18, False, None),
    (16, 20, True, "top"),
    (18, 22, False, None),
    (20, 24, True, "right"),
    (22, 26, False, None),
    (24, 28, True, "bottom"),
    (26, 30, False, "left"),
)


def _read_program(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def validate_request(seed: int, settings: dict[str, Any], demos: int, queries: int) -> str:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, *DEMO_LIMITS)
    _integer("queries", queries, *QUERY_LIMITS)
    if not isinstance(settings, dict) or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    finish = settings["finish"]
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return finish


def program_for(settings: dict[str, Any]) -> str:
    if not isinstance(settings, dict) or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    finish = settings["finish"]
    if finish == "translate_only":
        return _read_program("canonical.rkt")
    if finish == "cue_payload":
        return _read_program("cue_payload.rkt")
    raise ValueError(f"finish must be one of {FINISHES}")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _transform_shape(shape: tuple[tuple[int, int], ...], code: int) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    if code & 4:
        cells = [(r, -c) for r, c in cells]
    for _ in range(code & 3):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _shape_at(shape: Iterable[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox_anchor(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return min(r for r, _ in cells), min(c for _, c in cells)


def _translate(cells: Iterable[tuple[int, int]], dr: int, dc: int) -> set[tuple[int, int]]:
    return {(r + dr, c + dc) for r, c in cells}


def _in_bounds(cells: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _neighbors(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    cells = set(cells)
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in CARDINAL
        if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in cells
    }


def _touches(cells: Iterable[tuple[int, int]], h: int, w: int, border: str | None) -> bool:
    if border is None:
        return True
    if border == "top":
        return any(r == 0 for r, _ in cells)
    if border == "bottom":
        return any(r == h - 1 for r, _ in cells)
    if border == "left":
        return any(c == 0 for _, c in cells)
    if border == "right":
        return any(c == w - 1 for _, c in cells)
    raise ValueError(f"unknown border {border!r}")


def _profile(pair_index: int, *, is_query: bool, query_index: int, queries: int) -> tuple[int, int, bool, str | None]:
    if is_query and queries == 4 and query_index == 3:
        return 30, 30, False, "bottom"
    return PROFILES[pair_index % len(PROFILES)]


def _placement_candidates(h: int, w: int, shape: tuple[tuple[int, int], ...]) -> list[tuple[int, int]]:
    sh, sw = _shape_dims(shape)
    return [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]


def _choose_cue(candidates: set[tuple[int, int]], rng: random.Random, *, edge_bias: int) -> tuple[int, int] | None:
    if not candidates:
        return None
    rows = list(candidates)
    rng.shuffle(rows)
    if edge_bias % 3 == 0:
        rows.sort(key=lambda p: min(p[0], p[1]))
    elif edge_bias % 3 == 1:
        rows.sort(key=lambda p: -(p[0] + p[1]))
    return rows[0]


def _payload_shape(size: int, variant: int) -> tuple[tuple[int, int], ...]:
    choices = PAYLOAD_SHAPES[size]
    return _transform_shape(choices[variant % len(choices)], variant % 8)


def _place_payload(
    *,
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    forbidden: set[tuple[int, int]],
    rng: random.Random,
    preferred_corner: int,
) -> set[tuple[int, int]] | None:
    candidates = _placement_candidates(h, w, shape)
    rng.shuffle(candidates)
    corners = ((0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0))
    pr, pc = corners[preferred_corner % 4]
    candidates.sort(key=lambda p: abs(p[0] - pr) + abs(p[1] - pc))
    for top, left in candidates:
        cells = _shape_at(shape, top, left)
        if cells & forbidden:
            continue
        if _neighbors(cells, h, w) & forbidden:
            continue
        return cells
    return None


def _build_scene(
    seed: int,
    pair_index: int,
    *,
    is_query: bool,
    query_index: int,
    queries: int,
) -> list[list[int]]:
    h, w, partial, border = _profile(pair_index, is_query=is_query, query_index=query_index, queries=queries)
    mix = (seed + 1) * 1_000_003 + (pair_index + 1) * 97_409 + (271_828 if is_query else 0)
    rng = random.Random(mix)
    marker = _transform_shape(MARKER_SHAPES[(seed + pair_index) % len(MARKER_SHAPES)], (seed * 3 + pair_index) % 8)
    yellow_shape = _transform_shape(YELLOW_SHAPES[(seed * 5 + pair_index) % len(YELLOW_SHAPES)], (seed + pair_index * 3) % 8)
    dr, dc = VECTORS[(seed + pair_index) % len(VECTORS)]
    if border is not None:
        # A destination can only touch a border in the direction of its shift;
        # choose a reachable edge while retaining the scheduled boundary stress.
        if dr < 0:
            border = "top"
        elif dr > 0:
            border = "bottom"
        elif dc < 0:
            border = "left"
        else:
            border = "right"
    mh, mw = _shape_dims(marker)
    marker_anchors = [
        (r, c)
        for r in range(h - mh + 1)
        for c in range(w - mw + 1)
        if 0 <= r + dr <= h - mh and 0 <= c + dc <= w - mw
    ]
    rng.shuffle(marker_anchors)
    yellow_anchors = _placement_candidates(h, w, yellow_shape)
    rng.shuffle(yellow_anchors)

    for red_top, red_left in marker_anchors:
        red_full = _shape_at(marker, red_top, red_left)
        green = _shape_at(marker, red_top + dr, red_left + dc)
        if red_full & green:
            continue

        if partial:
            # Enumerate anchors that place at least one yellow cell over a non-anchor
            # source-marker cell, while preserving the visible red bbox anchor.
            overlap_anchors = {
                (rr - yr, rc - yc)
                for rr, rc in red_full
                if (rr, rc) != (red_top, red_left)
                for yr, yc in yellow_shape
            }
            candidate_yellow_anchors = list(overlap_anchors)
            rng.shuffle(candidate_yellow_anchors)
        else:
            candidate_yellow_anchors = yellow_anchors

        for yellow_top, yellow_left in candidate_yellow_anchors:
            yellow = _shape_at(yellow_shape, yellow_top, yellow_left)
            shifted = _translate(yellow, dr, dc)
            if not _in_bounds(yellow, h, w) or not _in_bounds(shifted, h, w):
                continue
            if yellow & green:
                continue
            overlap = yellow & red_full
            if partial:
                if not overlap or overlap == red_full:
                    continue
                red_visible = red_full - overlap
                if not red_visible or _bbox_anchor(red_visible) != (red_top, red_left):
                    continue
            else:
                if overlap:
                    continue
                red_visible = red_full
            if shifted & yellow:
                continue
            if not _touches(shifted, h, w, border):
                continue

            occupied = red_visible | green | yellow
            yellow_n = _neighbors(yellow, h, w)
            shifted_n = _neighbors(shifted, h, w)
            green_n = _neighbors(green, h, w)
            base_forbidden = occupied | shifted
            target_candidates = shifted_n - base_forbidden - yellow_n - green_n
            source_candidates = yellow_n - base_forbidden - shifted_n - green_n
            green_candidates = green_n - base_forbidden - shifted_n - yellow_n
            target_cue = _choose_cue(target_candidates, rng, edge_bias=pair_index)
            source_cue = _choose_cue(source_candidates, rng, edge_bias=pair_index + 1)
            green_cue = _choose_cue(green_candidates, rng, edge_bias=pair_index + 2)
            if None in (target_cue, source_cue, green_cue):
                continue
            cues = {target_cue, source_cue, green_cue}
            if len(cues) != 3:
                continue

            role_colors = ROLE_COLOR_SCHEDULE[pair_index % len(ROLE_COLOR_SCHEDULE)]
            role_sizes = PAYLOAD_SIZE_SCHEDULE[pair_index % len(PAYLOAD_SIZE_SCHEDULE)]
            role_cues = (target_cue, source_cue, green_cue)
            avoid_adjacency = yellow_n | shifted_n | green_n | occupied | shifted | cues
            payloads: list[set[tuple[int, int]]] = []
            forbidden = set(avoid_adjacency)
            okay = True
            for role, size in enumerate(role_sizes):
                shape = _payload_shape(size, seed + pair_index * 5 + role)
                payload = _place_payload(
                    h=h,
                    w=w,
                    shape=shape,
                    forbidden=forbidden,
                    rng=rng,
                    preferred_corner=pair_index + role,
                )
                if payload is None:
                    okay = False
                    break
                payloads.append(payload)
                forbidden |= payload | _neighbors(payload, h, w)
            if not okay:
                continue

            grid = [[0 for _ in range(w)] for _ in range(h)]
            for r, c in red_visible:
                grid[r][c] = 2
            for r, c in green:
                grid[r][c] = 3
            for r, c in yellow:
                grid[r][c] = 4
            for color, cue, payload in zip(role_colors, role_cues, payloads, strict=True):
                grid[cue[0]][cue[1]] = color
                for r, c in payload:
                    grid[r][c] = color

            # A final independent parse catches accidental adjacency introduced by
            # payload placement or occlusion before the scene enters an episode.
            info = intermediate(grid)
            if (
                info["destination_cue_color"] != role_colors[0]
                or info["source_cue_color"] != role_colors[1]
                or info["green_cue_color"] != role_colors[2]
            ):
                continue
            return grid
    raise ValueError(f"could not construct parametric scene seed={seed} pair={pair_index}")


def _grid_cells(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def intermediate(grid: list[list[int]]) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not grid
        or any(type(row) is not list for row in grid)
        or not grid[0]
        or any(len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("grid must be a nonempty rectangular integer ARC grid")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("grid dimensions must be at most 30")
    red = _grid_cells(grid, 2)
    green = _grid_cells(grid, 3)
    yellow = _grid_cells(grid, 4)
    if not red or not green or not yellow:
        raise ValueError("red, green and yellow roles must all be present")
    rr, rc = _bbox_anchor(red)
    gr, gc = _bbox_anchor(green)
    dr, dc = gr - rr, gc - rc
    if dr == 0 and dc == 0:
        raise ValueError("red-to-green displacement must be nonzero")
    shifted = _translate(yellow, dr, dc)
    if not _in_bounds(shifted, h, w):
        raise ValueError("translated yellow footprint leaves the grid")

    def role(cells: set[tuple[int, int]], name: str) -> tuple[int, set[tuple[int, int]]]:
        adjacent = _neighbors(cells, h, w)
        local = {(r, c) for r, c in adjacent if grid[r][c] in CUE_COLORS}
        colors = {grid[r][c] for r, c in local}
        if len(colors) != 1:
            raise ValueError(f"{name} must have exactly one adjacent cue color, got {sorted(colors)}")
        color = next(iter(colors))
        return color, {(r, c) for r, c in local if grid[r][c] == color}

    destination_color, destination_local = role(shifted, "destination")
    source_color, source_local = role(yellow, "source")
    green_color, green_local = role(green, "green")
    if len({destination_color, source_color, green_color}) != 3:
        raise ValueError("destination, source and green cues must use distinct colors")
    counts = {color: len(_grid_cells(grid, color)) for color in CUE_COLORS}
    if any(counts[color] < 3 for color in CUE_COLORS):
        raise ValueError("every cue color needs a singleton cue plus a remote payload")
    return {
        "shape": [h, w],
        "delta": [dr, dc],
        "yellow": [list(p) for p in sorted(yellow)],
        "translated_yellow": [list(p) for p in sorted(shifted)],
        "destination_cue_color": destination_color,
        "source_cue_color": source_color,
        "green_cue_color": green_color,
        "destination_local_cells": [list(p) for p in sorted(destination_local)],
        "source_local_cells": [list(p) for p in sorted(source_local)],
        "green_local_cells": [list(p) for p in sorted(green_local)],
        "cue_color_counts": counts,
    }


def _blank(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r, c in cells:
        out[r][c] = color
    return out


def _base_translation(grid: list[list[int]]) -> tuple[list[list[int]], dict[str, Any]]:
    info = intermediate(grid)
    out = _blank(grid)
    for r, c in info["translated_yellow"]:
        out[r][c] = 4
    return out, info


def transform(grid: list[list[int]], finish: str) -> list[list[int]]:
    if finish not in FINISHES:
        raise ValueError(f"unknown finish {finish!r}")
    out, info = _base_translation(grid)
    if finish == "translate_only":
        return out
    selected = _grid_cells(grid, info["destination_cue_color"])
    return _paint(out, selected, 8)


def wrong_order_transform(grid: list[list[int]]) -> list[list[int]]:
    out, info = _base_translation(grid)
    return _paint(out, _grid_cells(grid, info["source_cue_color"]), 8)


def green_cue_transform(grid: list[list[int]]) -> list[list[int]]:
    out, info = _base_translation(grid)
    return _paint(out, _grid_cells(grid, info["green_cue_color"]), 8)


def _color_payload_transform(grid: list[list[int]], color: int) -> list[list[int]]:
    out, _ = _base_translation(grid)
    return _paint(out, _grid_cells(grid, color), 8)


def _lowest_color_payload(grid: list[list[int]]) -> list[list[int]]:
    return _color_payload_transform(grid, min(CUE_COLORS))


def _largest_payload(grid: list[list[int]]) -> list[list[int]]:
    counts = {color: len(_grid_cells(grid, color)) for color in CUE_COLORS}
    color = min(CUE_COLORS, key=lambda value: (-counts[value], value))
    return _color_payload_transform(grid, color)


def _local_cue_only(grid: list[list[int]]) -> list[list[int]]:
    out, info = _base_translation(grid)
    return _paint(out, (tuple(p) for p in info["destination_local_cells"]), 8)


def _payload_only(grid: list[list[int]]) -> list[list[int]]:
    out, info = _base_translation(grid)
    selected = _grid_cells(grid, info["destination_cue_color"])
    local = {tuple(p) for p in info["destination_local_cells"]}
    return _paint(out, selected - local, 8)


CANDIDATES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "translate_only": lambda grid: transform(grid, "translate_only"),
    "cue_payload": lambda grid: transform(grid, "cue_payload"),
    "source_cue_payload": wrong_order_transform,
    "green_cue_payload": green_cue_transform,
    "lowest_color_payload": _lowest_color_payload,
    "largest_payload": _largest_payload,
    "local_cue_only": _local_cue_only,
    "payload_only": _payload_only,
}


def teaching_check(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    finish = validate_request(0, settings, len(episode.get("train", [])), len(episode.get("test", [])))
    demos = episode["train"]
    queries = episode["test"]
    declared_survivors = [
        name
        for name in FINISHES
        if all(CANDIDATES[name](pair["input"]) == pair["output"] for pair in demos)
    ]
    survivors = [
        name
        for name, candidate in CANDIDATES.items()
        if all(candidate(pair["input"]) == pair["output"] for pair in demos)
    ]
    harmful = [
        name
        for name in survivors
        if any(CANDIDATES[name](pair["input"]) != pair["output"] for pair in queries)
    ]
    return {
        "finish": finish,
        "declared_survivors": declared_survivors,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "tested_rivals": sorted(CANDIDATES),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    tests = episode.get("test")
    if type(query_index) is not int or not isinstance(tests, list) or not 0 <= query_index < len(tests):
        raise ValueError("query_index is outside the episode")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(tests[query_index]["input"])}],
    }


def generate_episode(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    finish = validate_request(seed, settings, demos, queries)
    pairs: list[dict[str, Any]] = []
    for demo_index in range(demos):
        grid = _build_scene(
            seed,
            demo_index,
            is_query=False,
            query_index=-1,
            queries=queries,
        )
        pairs.append({"input": grid, "output": transform(grid, finish)})
    for query_index in range(queries):
        pair_index = 6 + query_index
        grid = _build_scene(
            seed,
            pair_index,
            is_query=True,
            query_index=query_index,
            queries=queries,
        )
        pairs.append({"input": grid, "output": transform(grid, finish)})
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(settings),
    }


def episode_digest(episode: dict[str, Any]) -> str:
    raw = json.dumps(episode, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()
