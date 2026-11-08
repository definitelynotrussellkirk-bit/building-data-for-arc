"""Construct lawful zigzag channels for ARC task f1bcbc2c.

Orange cells are walls around a one-cell-wide orthogonal channel.  A maroon
marker selects that channel when present.  A straight marker causes the entire
channel (including the marker) to become cyan; a marker at a bend splits the
channel and only the larger side becomes cyan.  Without a marker, the authority
chooses the larger of its first two row-major adjacent-orange components.

The generator constructs the latent channel first and derives every orange wall
cell from it, including the outer-corner cell required at each turn.  It emits
all three authority branches on a three-example schedule and never generates
outputs here; the unchanged canonical Racket program remains label authority.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9e736518d82"
TASK_ID = GENERATOR_ID
RULE_HASH = "b8c560eed7ae"
VERSION = "4.0.0"
SUMMARY = (
    "A simple 2..6-turn orthogonal channel reaches two grid boundaries and is "
    "enclosed by exact orange side walls plus the outer corner at every bend. "
    "Examples cycle through no marker, a straight maroon marker, and a marker "
    "at a turn. The authority fills the selected channel cyan: all of it for "
    "no/straight markers, or only the larger side when a turn marker splits it."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the authority-selected 0/9 component is a simple cardinal path with both endpoints on the boundary",
    "the channel has 2..6 turns and every orange cell is exactly an expected side/outer-corner wall",
    "there are zero or one maroon markers, and any marker lies inside the selected channel",
    "turn markers have unequal channel halves so the larger-half answer is unambiguous",
    "three consecutive sample indexes cover no-marker, straight-marker, and turn-marker branches",
]

AXES = {
    "grid_h": {"type": "int", "default": "10 favored; otherwise 10..20", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "10 favored; otherwise 10..20", "valid": "10..20"},
    "turn_count": {"type": "int", "default": "difficulty-weighted 2..6", "valid": "2..6"},
    "marker_mode": {"type": "str", "default": "three-example cyclic schedule", "valid": "none|straight|turn"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_MARKER_MODES = ("none", "straight", "turn")


def _neighbors(point: tuple[int, int]) -> Iterable[tuple[int, int]]:
    r, c = point
    for dr, dc in _CARDINAL:
        yield r + dr, c + dc


def _bfs(start: tuple[int, int], pool: set[tuple[int, int]]) -> set[tuple[int, int]]:
    visited = {start}
    queue = deque([start])
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(point):
            if nxt in pool and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


def _adjacent_orange_band(grid) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] in (0, 9)
        and any(
            0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 7
            for nr, nc in _neighbors((r, c))
        )
    ]


def _authority_channel(grid) -> set[tuple[int, int]]:
    """Mirror the canonical component-selection semantics on a validated grid."""
    band = _adjacent_orange_band(grid)
    if not band:
        raise ValueError("no 0/9 cell is cardinally adjacent to orange")
    pool = set(band)
    marker = next((point for point in band if grid[point[0]][point[1]] == 9), None)
    if marker is not None:
        return _bfs(marker, pool)
    comp1 = _bfs(band[0], pool)
    remaining = [point for point in band if point not in comp1]
    if not remaining:
        return comp1
    comp2 = _bfs(remaining[0], pool)
    return comp1 if len(comp1) > len(comp2) else comp2


def _ordered_path(channel: set[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(channel) < 2:
        raise ValueError("selected channel is too short")
    adjacency = {
        point: sorted(nxt for nxt in _neighbors(point) if nxt in channel)
        for point in channel
    }
    bad = {point: len(nbrs) for point, nbrs in adjacency.items() if len(nbrs) not in (1, 2)}
    if bad:
        raise ValueError("selected channel is not a simple cardinal path")
    endpoints = sorted(point for point, nbrs in adjacency.items() if len(nbrs) == 1)
    if len(endpoints) != 2:
        raise ValueError(f"selected channel must have two endpoints, found {len(endpoints)}")
    path = [endpoints[0]]
    previous = None
    current = endpoints[0]
    while current != endpoints[1]:
        candidates = [point for point in adjacency[current] if point != previous]
        if len(candidates) != 1:
            raise ValueError("selected channel traversal is ambiguous")
        previous, current = current, candidates[0]
        path.append(current)
        if len(path) > len(channel):
            raise ValueError("selected channel traversal cycled")
    if set(path) != channel:
        raise ValueError("selected channel is disconnected")
    return path


def _turn_indices(path: list[tuple[int, int]]) -> list[int]:
    turns: list[int] = []
    for index in range(1, len(path) - 1):
        prev, cur, nxt = path[index - 1], path[index], path[index + 1]
        incoming = (cur[0] - prev[0], cur[1] - prev[1])
        outgoing = (nxt[0] - cur[0], nxt[1] - cur[1])
        if incoming != outgoing:
            turns.append(index)
    return turns


def _expected_walls(path: list[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    channel = set(path)
    walls = {
        point
        for cell in channel
        for point in _neighbors(cell)
        if 0 <= point[0] < h and 0 <= point[1] < w and point not in channel
    }
    for index in _turn_indices(path):
        prev, cur, nxt = path[index - 1], path[index], path[index + 1]
        incoming = (cur[0] - prev[0], cur[1] - prev[1])
        outgoing = (nxt[0] - cur[0], nxt[1] - cur[1])
        outer = (
            cur[0] + incoming[0] - outgoing[0],
            cur[1] + incoming[1] - outgoing[1],
        )
        if 0 <= outer[0] < h and 0 <= outer[1] < w and outer not in channel:
            walls.add(outer)
    return walls


def _marker_mode(grid, path: list[tuple[int, int]]) -> str:
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if not markers:
        return "none"
    if len(markers) != 1 or markers[0] not in set(path):
        raise ValueError("expected zero or one marker on the selected channel")
    index = path.index(markers[0])
    if index in (0, len(path) - 1):
        raise ValueError("marker may not be a channel endpoint")
    return "turn" if index in _turn_indices(path) else "straight"


def _composition(total: int, count: int, rng) -> list[int]:
    """A deterministic random composition with every part at least two."""
    if count == 0:
        if total != 0:
            raise ValueError("nonzero total cannot be split into zero parts")
        return []
    if total < 2 * count:
        raise ValueError(f"total {total} cannot supply {count} segments of length >=2")
    parts = [2] * count
    for _ in range(total - 2 * count):
        parts[rng.randrange(count)] += 1
    rng.shuffle(parts)
    return parts


def _base_path(h: int, w: int, turn_count: int, rng) -> list[tuple[int, int]]:
    """Build a monotone down/right staircase from top to bottom or right edge."""
    if turn_count % 2 == 0:
        vertical_count = turn_count // 2 + 1
        horizontal_count = turn_count // 2
        vertical = _composition(h - 1, vertical_count, rng)
        horizontal_total = rng.randint(2 * horizontal_count, w - 3)
        horizontal = _composition(horizontal_total, horizontal_count, rng)
        start_col = rng.randint(1, w - 2 - horizontal_total)
    else:
        vertical_count = (turn_count + 1) // 2
        horizontal_count = vertical_count
        start_col = rng.randint(1, w - 1 - 2 * horizontal_count)
        horizontal = _composition(w - 1 - start_col, horizontal_count, rng)
        vertical_total = rng.randint(2 * vertical_count, h - 2)
        vertical = _composition(vertical_total, vertical_count, rng)

    lengths: list[int] = []
    for index in range(max(len(vertical), len(horizontal))):
        if index < len(vertical):
            lengths.append(vertical[index])
        if index < len(horizontal):
            lengths.append(horizontal[index])
    directions = ((1, 0), (0, 1))
    point = (0, start_col)
    path = [point]
    for segment_index, length in enumerate(lengths):
        dr, dc = directions[segment_index % 2]
        for _ in range(length):
            point = point[0] + dr, point[1] + dc
            path.append(point)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in path):
        raise RuntimeError("constructive path escaped the grid")
    if len(_turn_indices(path)) != turn_count:
        raise RuntimeError("constructive path did not realize requested turn count")
    return path


def _transform_path(path: list[tuple[int, int]], h: int, w: int, code: int):
    result = list(path)
    hh, ww = h, w
    for _ in range(code % 4):
        result = [(c, hh - 1 - r) for r, c in result]
        hh, ww = ww, hh
    if code // 4:
        result = [(r, ww - 1 - c) for r, c in result]
    return result, hh, ww


def _grid_from_path(path: list[tuple[int, int]], h: int, w: int,
                    marker: tuple[int, int] | None = None) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    for r, c in _expected_walls(path, h, w):
        grid[r][c] = 7
    if marker is not None:
        grid[marker[0]][marker[1]] = 9
    return grid


def _draw_weighted_int(ctx, label: str, lo: int, hi: int, *, core: bool,
                       anchor: int, favored: tuple[int, ...] = ()) -> int:
    choices = list(range(lo, hi + 1))
    if core:
        choices += [anchor] * 80
    elif favored:
        choices += list(favored) * 5
    return ctx.draw_choice(label, choices)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "turn_count"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer, not {type(overrides[name]).__name__}")
    if "marker_mode" in overrides and overrides["marker_mode"] is not None:
        if type(overrides["marker_mode"]) is not str:
            raise ValueError("marker_mode must be a string")
        if overrides["marker_mode"] not in _MARKER_MODES:
            raise ValueError(f"marker_mode must be one of {_MARKER_MODES}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    core = ctx.draw_choice("curriculum_profile", ("core",) * 4 + ("broad",)) == "core"
    favored_turns = (
        (2, 3) if difficulty == "easy"
        else (5, 6) if difficulty == "hard"
        else (3, 4, 5)
    )
    h = _draw_weighted_int(ctx, "grid_h", 10, 20, core=core, anchor=10)
    w = _draw_weighted_int(ctx, "grid_w", 10, 20, core=core, anchor=10)
    turn_count = _draw_weighted_int(
        ctx, "turn_count", 2, 6, core=False, anchor=4, favored=favored_turns
    )
    if overrides.get("marker_mode") is not None:
        mode = ctx.draw_choice("marker_mode", _MARKER_MODES)
    else:
        mode = ctx.draw_choice("marker_mode", (_MARKER_MODES[sample_index % 3],))

    path_rng = ctx.draw_rng("path_geometry")
    orientation_rng = ctx.draw_rng("orientation")
    marker_rng = ctx.draw_rng("marker_position")

    if mode == "none":
        base_path = _base_path(h, w, turn_count, path_rng)
        codes = [0, 2, 4, 6]
        orientation_rng.shuffle(codes)
        chosen = None
        for code in codes:
            path, out_h, out_w = _transform_path(base_path, h, w, code)
            grid = _grid_from_path(path, out_h, out_w)
            if _authority_channel(grid) == set(path):
                chosen = grid
                break
        if chosen is None:
            raise RuntimeError("no-marker construction failed to make the latent path authoritative")
        return chosen

    code = orientation_rng.randrange(8)
    base_h, base_w = (w, h) if code % 2 else (h, w)
    base_path = _base_path(base_h, base_w, turn_count, path_rng)
    path, out_h, out_w = _transform_path(base_path, base_h, base_w, code)
    if (out_h, out_w) != (h, w):
        raise RuntimeError("dihedral transform did not preserve requested final dimensions")
    turns = set(_turn_indices(path))
    if mode == "straight":
        candidates = [index for index in range(1, len(path) - 1) if index not in turns]
    else:
        candidates = [
            index for index in sorted(turns)
            if index != len(path) - index - 1
        ]
    if not candidates:
        raise RuntimeError(f"constructive path has no valid {mode} marker position")
    marker = path[marker_rng.choice(candidates)]
    return _grid_from_path(path, h, w, marker)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors: list[str] = []
    if not (10 <= h <= 20 and 10 <= w <= 20):
        errors.append(f"grid dimensions {h}x{w} outside 10..20")
    invalid = sorted({value for row in grid for value in row if type(value) is not int or value not in (0, 7, 9)}, key=str)
    if invalid:
        errors.append(f"cells must be integer colors 0,7,9; found {invalid}")
        return errors
    marker_count = sum(value == 9 for row in grid for value in row)
    if marker_count > 1:
        errors.append(f"expected at most one color-9 marker, found {marker_count}")
    try:
        channel = _authority_channel(grid)
        path = _ordered_path(channel)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    endpoints = (path[0], path[-1])
    if not all(r in (0, h - 1) or c in (0, w - 1) for r, c in endpoints):
        errors.append("both channel endpoints must lie on the grid boundary")
    turns = _turn_indices(path)
    if not 2 <= len(turns) <= 6:
        errors.append(f"channel turn count {len(turns)} outside 2..6")
    actual_walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7}
    expected_walls = _expected_walls(path, h, w)
    if actual_walls != expected_walls:
        missing = len(expected_walls - actual_walls)
        extra = len(actual_walls - expected_walls)
        errors.append(f"orange walls do not exactly enclose channel (missing={missing}, extra={extra})")
    try:
        mode = _marker_mode(grid, path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if mode == "turn":
        marker = next(point for point in path if grid[point[0]][point[1]] == 9)
        index = path.index(marker)
        if index == len(path) - index - 1:
            errors.append("turn marker splits channel into equal halves")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    path = _ordered_path(_authority_channel(grid))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "turn_count": len(_turn_indices(path)),
        "marker_mode": _marker_mode(grid, path),
    }


def _authority_output(grid) -> list[list[int]]:
    out = deepcopy(grid)
    channel = _authority_channel(grid)
    marker = next((point for point in channel if grid[point[0]][point[1]] == 9), None)
    if marker is None:
        fill = channel
    else:
        neighbors = [point for point in _neighbors(marker) if point in channel]
        same_col = all(point[1] == marker[1] for point in neighbors)
        same_row = all(point[0] == marker[0] for point in neighbors)
        if same_col or same_row:
            fill = channel
        else:
            without = channel - {marker}
            half1 = _bfs(min(without), without)
            half2 = without - half1
            fill = half1 if len(half1) > len(half2) else half2
    for r, c in fill:
        out[r][c] = 8
    return out


def _rival_marker_required(grid):
    if not any(value == 9 for row in grid for value in row):
        return deepcopy(grid)
    return _authority_output(grid)


def _rival_fill_entire_channel(grid):
    out = deepcopy(grid)
    for r, c in _authority_channel(grid):
        out[r][c] = 8
    return out


def _rival_split_every_marker(grid):
    channel = _authority_channel(grid)
    marker = next((point for point in channel if grid[point[0]][point[1]] == 9), None)
    if marker is None:
        return _authority_output(grid)
    without = channel - {marker}
    half1 = _bfs(min(without), without)
    half2 = without - half1
    fill = half1 if len(half1) > len(half2) else half2
    out = deepcopy(grid)
    for r, c in fill:
        out[r][c] = 8
    return out


def _mode_witness(expected: str):
    def witness(grid):
        try:
            return observe_overrides(grid)["marker_mode"] == expected
        except ValueError:
            return False
    return witness


SEMANTIC_WITNESSES = {
    "none_branch": _mode_witness("none"),
    "straight_branch": _mode_witness("straight"),
    "turn_branch": _mode_witness("turn"),
}
SEMANTIC_RIVALS = {
    "marker_required": _rival_marker_required,
    "split_every_marker": _rival_split_every_marker,
    "fill_entire_channel": _rival_fill_entire_channel,
}
WITNESS_RIVALS = {
    "none_branch": ["marker_required"],
    "straight_branch": ["split_every_marker"],
    "turn_branch": ["fill_entire_channel"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict = {}


def schedule_profile(seed, sample_index, difficulty=None):
    return _MARKER_MODES[sample_index % 3]


SCHEDULE_PROFILES = _MARKER_MODES


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate each named branch shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output")
            continue
        if _authority_output(pair["input"]) != pair["output"]:
            errors.append(f"demo {index} output disagrees with canonical semantics")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        errors.append("query must contain input and output")
        return errors
    if _authority_output(query["input"]) != query["output"]:
        errors.append("query output disagrees with canonical semantics")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"demonstrations do not rule out {name}")
    return errors
