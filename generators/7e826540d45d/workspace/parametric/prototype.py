"""Deterministic parametric lessons for orthogonal object halos."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "7e826540d45d"
HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text()
SELECTED_EXPANSION_PROGRAM = (HOME / "selected_expansion.rkt").read_text()
SETTINGS = ("one_ring", "selected_two_step")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

_DEMO_PROFILES = ((10, 14), (12, 16), (14, 18), (18, 20), (20, 22), (22, 24))
_QUERY_PROFILES = ((11, 15), (16, 21), (23, 29), (30, 30))
_SQUARE3 = tuple((r, c) for r in range(3) for c in range(3))
_SQUARE4 = tuple((r, c) for r in range(4) for c in range(4))
_LINE6_H = tuple((0, c) for c in range(6))
_LINE6_V = tuple((r, 0) for r in range(6))
_LINE8_H = tuple((0, c) for c in range(8))
_LINE8_V = tuple((r, 0) for r in range(8))


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _c in cells)
    left = min(c for _r, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate_shape(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize_shape((c, -r) for r, c in shape)


_L6_BASE = ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2))
_L6_VARIANTS = []
_shape = _normalize_shape(_L6_BASE)
for _ in range(4):
    if _shape not in _L6_VARIANTS:
        _L6_VARIANTS.append(_shape)
    _shape = _rotate_shape(_shape)
_L6_VARIANTS = tuple(_L6_VARIANTS)

_SMALL_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _settings(value: dict[str, Any] | None) -> dict[str, str]:
    selected = {"halo_mode": "one_ring"} if value is None else value
    if not isinstance(selected, dict) or set(selected) != {"halo_mode"}:
        raise ValueError("settings must name exactly halo_mode")
    mode = selected["halo_mode"]
    if mode not in SETTINGS:
        raise ValueError("halo_mode must be one_ring or selected_two_step")
    return {"halo_mode": mode}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _grid(value: list[list[int]]) -> list[list[int]]:
    if (
        type(value) is not list
        or not value
        or type(value[0]) is not list
        or not value[0]
        or len(value) > 30
        or len(value[0]) > 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular with exact integer colors")
    return [row[:] for row in value]


def program(settings: dict[str, Any] | None = None) -> str:
    mode = _settings(settings)["halo_mode"]
    return CANONICAL_PROGRAM if mode == "one_ring" else SELECTED_EXPANSION_PROGRAM


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    source = _grid(grid)
    h, w = len(source), len(source[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = source[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and source[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def one_ring_halo(grid: list[list[int]]) -> list[list[int]]:
    source = _grid(grid)
    h, w = len(source), len(source[0])
    out = [[0] * w for _ in range(h)]
    for color, cells in _components(source):
        halo: set[tuple[int, int]] = set()
        own = set(cells)
        for r, c in cells:
            for dr, dc in CARDINAL:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and source[nr][nc] == 0 and (nr, nc) not in own:
                    halo.add((nr, nc))
        for r, c in halo:
            out[r][c] = color
    return out


def selected_color(grid: list[list[int]]) -> int:
    counts = {color: sum(cell == color for row in grid for cell in row) for color in range(1, 10)}
    return min(range(1, 10), key=lambda color: (-counts[color], color))


def expand_selected_halo(intermediate: list[list[int]]) -> list[list[int]]:
    source = _grid(intermediate)
    selected = selected_color(source)
    h, w = len(source), len(source[0])
    out = [row[:] for row in source]
    for r in range(h):
        for c in range(w):
            if source[r][c] != selected:
                continue
            for dr, dc in CARDINAL:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and source[nr][nc] == 0:
                    out[nr][nc] = selected
    return out


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _settings(settings)["halo_mode"]
    intermediate = one_ring_halo(grid)
    if mode == "one_ring":
        return intermediate
    return expand_selected_halo(intermediate)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|{seed}|{split}|{index}|v5".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8], "big"))


def _translated(shape: Iterable[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _corner_anchor(
    shape: Iterable[tuple[int, int]], h: int, w: int, corner: str
) -> tuple[int, int]:
    cells = tuple(shape)
    max_r = max(r for r, _c in cells)
    max_c = max(c for _r, c in cells)
    top = 1 if corner.startswith("top") else h - 2 - max_r
    left = 1 if corner.endswith("left") else w - 2 - max_c
    return top, left


def _clear(cells: set[tuple[int, int]], occupied: set[tuple[int, int]], h: int, w: int) -> bool:
    if not cells or any(not (1 <= r < h - 1 and 1 <= c < w - 1) for r, c in cells):
        return False
    return all(
        abs(r - rr) > 2 or abs(c - cc) > 2
        for r, c in cells
        for rr, cc in occupied
    )


def _place(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    shape: Iterable[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    h, w = len(grid), len(grid[0])
    cells = _translated(shape, top, left)
    if not _clear(cells, occupied, h, w):
        raise ValueError(f"invalid planned placement at {(top, left)} for {h}x{w}")
    for r, c in cells:
        grid[r][c] = color
    occupied.update(cells)


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    if split not in {"demo", "query"} or not 0 <= index < len(profiles):
        raise ValueError("unknown split/index")
    h, w = profiles[index]
    rng = _rng(seed, split, index)
    colors = rng.sample(range(1, 10), 8)
    competitor, focus = colors[:2]
    grid = [[0] * w for _ in range(h)]
    occupied: set[tuple[int, int]] = set()

    # Each focus has fewer source cells but a larger one-ring halo than its
    # compact competitor, so A reverses the input-frequency winner.  Varying
    # straight/bent topology and source size prevents a fixed six-cell-line cue.
    variant = index % 3
    if variant == 0:
        focus_shape = _LINE6_H if (seed + index) % 2 == 0 else _LINE6_V
        competitor_shape = _SQUARE3
    elif variant == 1:
        focus_shape = _L6_VARIANTS[(seed + index) % len(_L6_VARIANTS)]
        competitor_shape = _SQUARE3
    else:
        # Use the opposite orientation from the first demonstration so every
        # three-example lesson rejects a fixed-orientation / widest-object cue.
        focus_shape = _LINE8_H if (seed + index + 1) % 2 == 0 else _LINE8_V
        competitor_shape = _SQUARE4
    layouts = (
        ("top_left", "bottom_right"),
        ("bottom_right", "top_left"),
        ("top_right", "bottom_left"),
        ("bottom_left", "top_right"),
    )
    competitor_corner, focus_corner = layouts[
        (seed + index + (0 if split == "demo" else 2)) % len(layouts)
    ]
    competitor_top, competitor_left = _corner_anchor(
        competitor_shape, h, w, competitor_corner
    )
    focus_top, focus_left = _corner_anchor(focus_shape, h, w, focus_corner)
    _place(grid, occupied, competitor_shape, competitor_top, competitor_left, competitor)
    _place(grid, occupied, focus_shape, focus_top, focus_left, focus)

    # In the bent-L lesson, add a second compact competitor with more source
    # cells but a smaller first halo.  This makes the selected object third by
    # raw source size instead of baking in a fixed second-largest cue.
    color_index = 2
    if variant == 1:
        corners = ("top_left", "top_right", "bottom_left", "bottom_right")
        remaining = [
            corner
            for corner in corners
            if corner not in {competitor_corner, focus_corner}
        ]
        second_corner = remaining[(seed + index) % len(remaining)]
        second_top, second_left = _corner_anchor(_SQUARE3, h, w, second_corner)
        _place(
            grid,
            occupied,
            _SQUARE3,
            second_top,
            second_left,
            colors[color_index],
        )
        color_index += 1

    anchors = [
        (1, max(1, w // 2 - 1)),
        (h - 5, max(1, w // 2 - 1)),
        (max(1, h // 2 - 1), 1),
        (max(1, h // 2 - 1), w - 5),
        (1, 1),
        (1, w - 5),
        (h - 5, 1),
        (h - 5, w - 5),
        (max(1, h // 2 - 1), max(1, w // 2 - 1)),
    ]
    target_objects = 3 if h < 14 else 4 if h < 20 else 6 if h < 30 else 8
    for top, left in anchors:
        if len(_components(grid)) >= target_objects:
            break
        choices = list(_SMALL_SHAPES)
        rng.shuffle(choices)
        placed = False
        for shape in choices:
            max_r = max(r for r, _ in shape)
            max_c = max(c for _, c in shape)
            candidate_top = min(max(1, top + rng.choice((0, 0, 1))), h - 2 - max_r)
            candidate_left = min(max(1, left + rng.choice((0, 0, 1))), w - 2 - max_c)
            cells = _translated(shape, candidate_top, candidate_left)
            if _clear(cells, occupied, h, w):
                color = colors[color_index % len(colors)]
                _place(grid, occupied, shape, candidate_top, candidate_left, color)
                color_index += 1
                placed = True
                break
        if not placed:
            continue

    if len(_components(grid)) < target_objects:
        # Deterministic bounded fallback search for large layouts.
        for r in range(1, h - 3):
            for c in range(1, w - 3):
                if len(_components(grid)) >= target_objects:
                    break
                shape = _SMALL_SHAPES[(r + c + seed + index) % len(_SMALL_SHAPES)]
                cells = _translated(shape, r, c)
                if _clear(cells, occupied, h, w):
                    color = colors[color_index % len(colors)]
                    _place(grid, occupied, shape, r, c, color)
                    color_index += 1
            if len(_components(grid)) >= target_objects:
                break
    if len(_components(grid)) < target_objects:
        raise ValueError(f"could not place {target_objects} separated objects")
    return grid


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer("demos", demos, 3, 6)
    queries = _integer("queries", queries, 1, 4)
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
