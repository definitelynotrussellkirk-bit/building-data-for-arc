"""Generator for ARC task ac0c5833 / content hash e7c4af96e258.

A connected red(2) source polyomino is accompanied by a connected,
D4-asymmetric yellow(4) marker constellation.  One to three transformed copies
of the marker constellation occur elsewhere with the corresponding red
footprint left blank.  The canonical rule finds every marker match under the
eight dihedral transforms and stamps the transformed red footprint there.

The override surface is deliberately small and fully observable.  Structural
variation inside the red polyomino, orientations, and positions remains keyed
local randomness rather than pretending to be caller-controlled axes.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components_cells

GENERATOR_ID = "e7c4af96e258"
TASK_ID = GENERATOR_ID
RULE_HASH = "ba639c9a8809"
VERSION = "3.1.0"

SUMMARY = (
    "A 0-background grid contains one connected red(2) source shape beside a "
    "connected D4-asymmetric yellow(4) marker constellation. One to three "
    "transformed copies of that marker constellation occur elsewhere while "
    "their corresponding red footprints are empty. Match the marker "
    "constellation under every D4 transform and stamp the correspondingly "
    "transformed red shape at every match; preserve all yellow cells."
)

INVARIANTS = [
    "the grid uses only colors 0, 2, and 4",
    "there is exactly one connected red source with at least two cells",
    "the source has exactly four nearby yellow marker cells forming a connected D4-asymmetric constellation",
    "at least one non-source D4 marker match has an empty red footprint",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-keyed", "valid": "13..20"},
    "grid_w": {"type": "int", "default": "difficulty-keyed", "valid": "15..22"},
    "marker_count": {"type": "int", "default": "difficulty-keyed", "valid": "1..3"},
    "texture": {"type": "str", "default": "standard", "valid": "standard"},
}

HELPFUL_TEXTURES = ("standard",)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_DIFFICULTIES = (None, "easy", "medium", "hard")
_RED_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name, lo, hi in (("grid_h", 13, 20), ("grid_w", 15, 22), ("marker_count", 1, 3)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError("texture override must be a string")
        if value != "standard":
            raise ValueError("texture must be 'standard'")


def _draw_axis(ctx, name: str, default_bounds: tuple[int, int], full_bounds: tuple[int, int]) -> int:
    """Honor every legal explicit value regardless of the difficulty band."""
    lo, hi = full_bounds if name in ctx.overrides and ctx.overrides[name] is not None else default_bounds
    return int(ctx.draw_int_strict(name, lo, hi))


def _transform_pos(r: int, c: int, index: int) -> tuple[int, int]:
    return (
        (r, c),
        (c, -r),
        (-r, -c),
        (-c, r),
        (r, -c),
        (-c, -r),
        (-r, c),
        (c, r),
    )[index]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform_unit(
    red: Sequence[tuple[int, int]],
    markers: Sequence[tuple[int, int]],
    index: int,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """Transform red and marker cells jointly, preserving their relative offset."""
    red_t = [_transform_pos(r, c, index) for r, c in red]
    marker_t = [_transform_pos(r, c, index) for r, c in markers]
    all_cells = red_t + marker_t
    min_r = min(r for r, _ in all_cells)
    min_c = min(c for _, c in all_cells)
    shift = lambda cells: tuple(sorted((r - min_r, c - min_c) for r, c in cells))
    return shift(red_t), shift(marker_t)


def _d4_distinct(cells: Sequence[tuple[int, int]]) -> bool:
    return len({_normalize(_transform_pos(r, c, index) for r, c in cells) for index in range(8)}) == 8


def _make_unit(rng) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """Return one small source and a connected four-cell chiral marker."""
    red = tuple(rng.choice(_RED_SHAPES))
    red_w = max(c for _, c in red) + 1
    # L tetromino: connected and has eight distinct D4 images.  Its nearest
    # column is one cell to the right of the red bbox and every marker remains
    # within the canonical bbox-expanded-by-two source window.
    marker = ((0, red_w), (1, red_w), (2, red_w), (2, red_w + 1))
    assert _d4_distinct(marker)
    return red, marker


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _canonical_red_relative(twos: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = _bbox(twos)
    raw = tuple((r - r0, c - c0) for r, c in twos)
    if r1 - r0 + 1 == 3 and c1 - c0 + 1 == 3 and len(raw) == 8:
        return ((0, 0), (0, 2), (1, 2), (2, 0), (2, 1), (2, 2))
    return raw


def _candidate_footprints(grid: Sequence[Sequence[int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Mirror the canonical match enumeration closely enough for validation.

    The canonical Racket program min-normalizes each transformed marker image,
    then tries every yellow anchor against every marker-relative cell.  This
    implementation returns the same set of sorted red footprints.
    """
    if not grid or not grid[0]:
        return ()
    h, w = len(grid), len(grid[0])
    twos = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    fours = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
    if not twos or not fours:
        return ()
    r0, c0, r1, c1 = _bbox(twos)
    red = _canonical_red_relative(twos)
    markers = tuple(
        (r - r0, c - c0)
        for r, c in fours
        if r0 - 2 <= r <= r1 + 2 and c0 - 2 <= c <= c1 + 2
    )
    if not markers:
        return ()

    found: set[tuple[tuple[int, int], ...]] = set()
    for index in range(8):
        spun_markers = [_transform_pos(r, c, index) for r, c in markers]
        spun_red = [_transform_pos(r, c, index) for r, c in red]
        min_r = min(r for r, _ in spun_markers)
        min_c = min(c for _, c in spun_markers)
        marker_rel = tuple((r - min_r, c - min_c) for r, c in spun_markers)
        red_rel = tuple((r - min_r, c - min_c) for r, c in spun_red)
        for anchor_r, anchor_c in fours:
            for rel_r, rel_c in marker_rel:
                tr, tc = anchor_r - rel_r, anchor_c - rel_c
                marker_pos = tuple((tr + r, tc + c) for r, c in marker_rel)
                red_pos = tuple((tr + r, tc + c) for r, c in red_rel)
                if not all(0 <= r < h and 0 <= c < w and grid[r][c] == 4 for r, c in marker_pos):
                    continue
                if not all(0 <= r < h and 0 <= c < w and grid[r][c] != 4 for r, c in red_pos):
                    continue
                found.add(tuple(sorted(red_pos)))
    return tuple(sorted(found))


def _place_scene(h: int, w: int, n_targets: int, rng) -> list[list[int]] | None:
    red, markers = _make_unit(rng)
    unit = red + markers
    unit_h = max(r for r, _ in unit) + 1
    unit_w = max(c for _, c in unit) + 1
    if unit_h > h or unit_w > w:
        return None

    grid = full_grid(h, w, 0)
    occupied = [[False] * w for _ in range(h)]

    def reserve(cells: Sequence[tuple[int, int]], margin: int = 1) -> bool:
        cell_set = set(cells)
        if any(not (0 <= r < h and 0 <= c < w) or occupied[r][c] for r, c in cells):
            return False
        for r, c in cells:
            for dr in range(-margin, margin + 1):
                for dc in range(-margin, margin + 1):
                    rr, cc = r + dr, c + dc
                    if (rr, cc) in cell_set:
                        continue
                    if 0 <= rr < h and 0 <= cc < w and occupied[rr][cc]:
                        return False
        for r, c in cells:
            occupied[r][c] = True
        return True

    source_candidates = [(r, c) for r in range(h - unit_h + 1) for c in range(w - unit_w + 1)]
    rng.shuffle(source_candidates)
    source: tuple[int, int] | None = None
    for sr, sc in source_candidates:
        cells = tuple((sr + r, sc + c) for r, c in unit)
        if reserve(cells):
            source = (sr, sc)
            for r, c in red:
                grid[sr + r][sc + c] = 2
            for r, c in markers:
                grid[sr + r][sc + c] = 4
            break
    if source is None:
        return None

    sr, sc = source
    source_red = tuple((sr + r, sc + c) for r, c in red)
    br0, bc0, br1, bc1 = _bbox(source_red)
    source_window = (br0 - 2, bc0 - 2, br1 + 2, bc1 + 2)

    for target_index in range(n_targets):
        orientation = rng.randrange(8)
        red_t, marker_t = _transform_unit(red, markers, orientation)
        th = max(r for r, _ in red_t + marker_t) + 1
        tw = max(c for _, c in red_t + marker_t) + 1
        candidates = [(r, c) for r in range(h - th + 1) for c in range(w - tw + 1)]
        rng.shuffle(candidates)
        placed = False
        for tr, tc in candidates:
            marker_abs = tuple((tr + r, tc + c) for r, c in marker_t)
            red_abs = tuple((tr + r, tc + c) for r, c in red_t)
            wr0, wc0, wr1, wc1 = source_window
            if any(wr0 <= r <= wr1 and wc0 <= c <= wc1 for r, c in marker_abs):
                continue
            if reserve(red_abs + marker_abs):
                for r, c in marker_abs:
                    grid[r][c] = 4
                placed = True
                break
        if not placed:
            return None

    footprints = _candidate_footprints(grid)
    source_key = tuple(sorted(source_red))
    if source_key not in footprints or len(footprints) != n_targets + 1:
        return None
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        h_bounds, w_bounds, count_bounds = (13, 15), (15, 17), (1, 1)
    elif difficulty == "hard":
        h_bounds, w_bounds, count_bounds = (17, 20), (18, 22), (2, 3)
    else:
        h_bounds, w_bounds, count_bounds = (15, 18), (16, 20), (1, 2)

    h = _draw_axis(ctx, "grid_h", h_bounds, (13, 20))
    w = _draw_axis(ctx, "grid_w", w_bounds, (15, 22))
    n_targets = _draw_axis(ctx, "marker_count", count_bounds, (1, 3))
    texture_options = ("standard",) if "texture" not in ctx.overrides else HELPFUL_TEXTURES
    ctx.draw_choice("texture", texture_options)

    layout_rng = ctx.draw_rng("layout")
    for _ in range(256):
        grid = _place_scene(h, w, n_targets, layout_rng)
        if grid is not None and not self_check(grid):
            return grid
    raise RuntimeError(f"failed to place a valid {h}x{w} scene with {n_targets} targets")


def _shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty sequence of rows"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid rows must be nonempty sequences"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the actual source/marker grammar, not only color cardinality."""
    del difficulty, meta
    shape_error = _shape_error(grid)
    if shape_error:
        return [shape_error]
    errors: list[str] = []
    h, w = len(grid), len(grid[0])
    if not (13 <= h <= 30 and 13 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} are outside the task envelope 13..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    unexpected = sorted({value for row in grid for value in row} - {0, 2, 4})
    if unexpected:
        errors.append(f"unexpected colors outside 0,2,4: {unexpected}")

    red_components = components_cells(grid, colors={2}, same_color=True)
    if len(red_components) != 1:
        errors.append(f"expected exactly one connected red source shape, found {len(red_components)}")
        return errors
    if len(red_components[0]) < 2:
        errors.append("red source must contain at least two cells")

    twos = red_components[0]
    r0, c0, r1, c1 = _bbox(twos)
    nearby_markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4 and r0 - 2 <= r <= r1 + 2 and c0 - 2 <= c <= c1 + 2
    ]
    if len(nearby_markers) != 4:
        errors.append(
            "source marker constellation must contain exactly four nearby yellow cells"
        )
        return errors
    nearby_set = set(nearby_markers)
    frontier = [min(nearby_set)]
    reached = {frontier[0]}
    while frontier:
        r, c = frontier.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in nearby_set and neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    if reached != nearby_set:
        errors.append("source marker constellation must be 4-connected")
    if not _d4_distinct(nearby_markers):
        errors.append("source marker constellation must be D4-asymmetric")

    yellow_components = components_cells(grid, colors={4}, same_color=True)
    marker_orbit = {
        _normalize(_transform_pos(r, c, index) for r, c in nearby_markers)
        for index in range(8)
    }
    if not 2 <= len(yellow_components) <= 4:
        errors.append(
            "expected one source marker plus one to three separated target markers"
        )
    for component in yellow_components:
        if len(component) != 4 or _normalize(component) not in marker_orbit:
            errors.append(
                "every yellow component must be a four-cell D4 image of the source marker"
            )
            break

    footprints = _candidate_footprints(grid)
    if not footprints:
        errors.append("source marker constellation produces no lawful D4 stamp site")
        return errors
    source_key = tuple(sorted(twos))
    if source_key not in footprints:
        errors.append("red source is not reproduced by its nearby marker constellation")
    target_count = sum(footprint != source_key for footprint in footprints)
    if not 1 <= target_count <= 3:
        errors.append(
            f"marker constellation must expose one to three non-source targets, found {target_count}"
        )
    if len(footprints) != len(yellow_components):
        errors.append(
            "yellow marker components and lawful red stamp sites must correspond one-for-one"
        )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared control from a lawful generated input."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides from invalid grid: " + "; ".join(errors))
    twos = tuple(sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2))
    targets = [footprint for footprint in _candidate_footprints(grid) if footprint != twos]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "marker_count": len(targets),
        "texture": "standard",
    }
