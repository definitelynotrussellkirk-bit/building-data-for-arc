"""Adversarial generator for marker-count selection by component area.

Count the maroon (9) cells.  Sort the three blue (1) components by area,
select the component at that one-indexed rank, crop its bounding box, upscale
by two, and recolor every nonzero cell cyan (8).

The canonical examples accidentally place component size ranks in reading
order.  Every generated sample deliberately deranges those ranks while keeping
all markers in one horizontal bar, so neither reading order nor marker-component
count can substitute for the intended cell-count / area-rank rule.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7ff231aab1a"
TASK_ID = GENERATOR_ID
RULE_HASH = "5c4099040cb4"
VERSION = "2.0.0"
SUMMARY = (
    "Count K maroon cells, select the K-th smallest of three blue components "
    "by area, tightly crop it, upscale 2x, and recolor nonzero cells cyan."
)

INVARIANTS = [
    "input colors are exactly the canonical roles 0, 1, and 9",
    "there are exactly three 4-connected blue components of distinct sizes",
    "the K marker cells form one contiguous horizontal maroon bar",
    "spatial order is a derangement of area rank in every generated sample",
    "component bounding boxes contain no foreign nonzero cells",
]

SIZE_PROFILES = {
    "sizes_234": (2, 3, 4),
    "sizes_235": (2, 3, 5),
    "sizes_245": (2, 4, 5),
    "sizes_345": (3, 4, 5),
    "sizes_268": (2, 6, 8),
    "sizes_379": (3, 7, 9),
    "sizes_4811": (4, 8, 11),
    "sizes_51013": (5, 10, 13),
    "sizes_61214": (6, 12, 14),
    "sizes_71315": (7, 13, 15),
}
RANK_LAYOUTS = {
    # Values are zero-based size ranks in reading-order slots.
    "medium_large_small": (1, 2, 0),
    "large_small_medium": (2, 0, 1),
}

AXES = {
    "grid_h": {"type": "int", "default": "two-value schedule", "valid": "11..12"},
    "grid_w": {"type": "int", "default": "three-value schedule", "valid": "15..17"},
    "marker_count": {"type": "int", "default": "1,2,3 curriculum", "valid": "1..3"},
    "size_profile": {
        "type": "str",
        "default": "five-profile schedule",
        "valid": "sizes_234|sizes_235|sizes_245|sizes_345|sizes_268|sizes_379|sizes_4811|sizes_51013|sizes_61214|sizes_71315",
    },
    "rank_layout": {
        "type": "str",
        "default": "alternating derangements",
        "valid": "medium_large_small|large_small_medium",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 30
MIN_STRICT_FRAC = 1.0
_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIFFICULTY_OFFSETS = {None: 0, "easy": 1, "medium": 2, "hard": 3}
_SIZE_PROFILE_BY_VALUE = {value: name for name, value in SIZE_PROFILES.items()}
_RANK_LAYOUT_BY_VALUE = {value: name for name, value in RANK_LAYOUTS.items()}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"unsupported difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "marker_count"}:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = {
                "grid_h": (11, 12),
                "grid_w": (15, 17),
                "marker_count": (1, 3),
            }[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "size_profile":
            if type(value) is not str:
                raise TypeError("size_profile must be a string")
            if value not in SIZE_PROFILES:
                raise ValueError(f"unknown size_profile {value!r}")
        elif name == "rank_layout":
            if type(value) is not str:
                raise TypeError("rank_layout must be a string")
            if value not in RANK_LAYOUTS:
                raise ValueError(f"unknown rank_layout {value!r}")


def _scheduled_defaults(seed: int, sample_index: int, difficulty=None) -> dict[str, Any]:
    """A 30-step exact curriculum with no pair of axes in lockstep."""
    index = int(sample_index)
    seed_offset = int(seed) + _DIFFICULTY_OFFSETS[difficulty]
    size_names = tuple(SIZE_PROFILES)
    layout_names = tuple(RANK_LAYOUTS)
    return {
        "grid_h": (11, 12)[((index // 5) + seed_offset) % 2],
        "grid_w": (15, 16, 17)[((index // 2) + seed_offset) % 3],
        "marker_count": (1, 2, 3)[index % 3],
        "size_profile": size_names[((index // 3) + seed_offset) % len(size_names)],
        "rank_layout": layout_names[(index + seed_offset) % len(layout_names)],
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> dict[str, Any]:
    """Return the deterministic public-axis defaults for one sample index."""
    _validate_difficulty(difficulty)
    return dict(_scheduled_defaults(seed, sample_index, difficulty))


def _normalized(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _polyomino(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Draw a connected size-N polyomino in a 3x5 bounding envelope."""
    for _ in range(128):
        cells = {(0, 0)}
        while len(cells) < size:
            boundary = sorted(
                {
                    (r + dr, c + dc)
                    for r, c in cells
                    for dr, dc in _NEIGHBORS
                    if (r + dr, c + dc) not in cells
                }
            )
            rng.shuffle(boundary)
            added = False
            for point in boundary:
                candidate = cells | {point}
                rows = [r for r, _ in candidate]
                cols = [c for _, c in candidate]
                if max(rows) - min(rows) + 1 <= 3 and max(cols) - min(cols) + 1 <= 5:
                    cells = candidate
                    added = True
                    break
            if not added:
                break
        if len(cells) == size:
            shape = _normalized(cells)
            # Random reflections keep the keyed draw diverse while preserving size.
            if rng.getrandbits(1):
                max_c = max(c for _, c in shape)
                shape = tuple(sorted((r, max_c - c) for r, c in shape))
            if rng.getrandbits(1):
                max_r = max(r for r, _ in shape)
                shape = tuple(sorted((max_r - r, c) for r, c in shape))
            return _normalized(set(shape))
    # Deterministic connected fallback, valid for every supported size <= 15.
    return tuple((index // 5, index % 5) for index in range(size))


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _paint(grid: list[list[int]], shape, origin: tuple[int, int], color: int) -> None:
    r0, c0 = origin
    for dr, dc in shape:
        if grid[r0 + dr][c0 + dc] != 0:
            raise RuntimeError("internal placement collision")
        grid[r0 + dr][c0 + dc] = color


def _components_of_color(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in _NEIGHBORS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(comp)
    return result


def _bbox(comp: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def _crop_and_scale(grid: list[list[int]], comp: list[tuple[int, int]]) -> list[list[int]]:
    r0, c0, r1, c1 = _bbox(comp)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    return [
        [8 if crop[r // 2][c // 2] != 0 else 0 for c in range(2 * len(crop[0]))]
        for r in range(2 * len(crop))
    ]


def _area_sorted(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    return sorted(
        _components_of_color(grid, 1),
        key=lambda comp: (len(comp), _bbox(comp)[0], _bbox(comp)[1]),
    )


def _reading_sorted(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    return sorted(
        _components_of_color(grid, 1),
        key=lambda comp: (_bbox(comp)[0], _bbox(comp)[1]),
    )


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket rule for diagnostics/tests."""
    comps = _area_sorted(grid)
    k = sum(value == 9 for row in grid for value in row)
    if not 1 <= k <= len(comps):
        raise ValueError("marker count does not name a component rank")
    return _crop_and_scale(grid, comps[k - 1])


def _reading_order_rival(grid: list[list[int]]) -> list[list[int]]:
    comps = _reading_sorted(grid)
    k = sum(value == 9 for row in grid for value in row)
    if not 1 <= k <= len(comps):
        raise ValueError("marker count does not name a component rank")
    return _crop_and_scale(grid, comps[k - 1])


def _fixed_rank_rival(rank: int):
    def rival(grid: list[list[int]]) -> list[list[int]]:
        return _crop_and_scale(grid, _area_sorted(grid)[rank])

    return rival


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input with exact observable axes."""
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    effective = _scheduled_defaults(int(seed), int(sample_index), difficulty)
    for name, value in overrides.items():
        if value is not None:
            effective[name] = value

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_strict("grid_h", 11, 12)
    w = ctx.draw_int_strict("grid_w", 15, 17)
    marker_count = ctx.draw_int_strict("marker_count", 1, 3)
    size_profile = ctx.draw_choice("size_profile", tuple(SIZE_PROFILES))
    rank_layout = ctx.draw_choice("rank_layout", tuple(RANK_LAYOUTS))

    sizes = SIZE_PROFILES[size_profile]
    slot_ranks = RANK_LAYOUTS[rank_layout]
    shapes = {
        rank: _polyomino(ctx.draw_rng(f"shape_rank_{rank}"), size)
        for rank, size in enumerate(sizes)
    }
    grid = full_grid(h, w, 0)

    slot_shapes = [shapes[rank] for rank in slot_ranks]
    left_shape, right_shape, lower_shape = slot_shapes
    _, right_w = _shape_size(right_shape)
    lower_h, lower_w = _shape_size(lower_shape)
    origins = (
        (1, 1),
        (1, w - right_w - 1),
        (h - lower_h - 3, (w - lower_w) // 2),
    )
    for shape, origin in zip(slot_shapes, origins, strict=True):
        _paint(grid, shape, origin, 1)

    marker_rng = ctx.draw_rng("marker_side")
    marker_row = h - 2
    marker_col = 1 if marker_rng.getrandbits(1) == 0 else w - marker_count - 1
    for offset in range(marker_count):
        grid[marker_row][marker_col + offset] = 9

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(findings))
    requested = {
        "grid_h": h,
        "grid_w": w,
        "marker_count": marker_count,
        "size_profile": size_profile,
        "rank_layout": rank_layout,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise RuntimeError(
            f"realized exact axes {observed!r} disagree with requested {requested!r}"
        )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical task grammar without requiring adversarial layout."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not 11 <= h <= 12:
        errors.append("grid height must be in 11..12")
    if not 15 <= w <= 17:
        errors.append("grid width must be in 15..17")
    if any(type(value) is not int for row in grid for value in row):
        errors.append("grid cells must be integers")
        return errors
    colors = {value for row in grid for value in row}
    if not colors <= {0, 1, 9}:
        errors.append("input colors must be a subset of {0,1,9}")

    blue = _components_of_color(grid, 1)
    if len(blue) != 3:
        errors.append("exactly three color-1 components are required")
    sizes = tuple(sorted(len(comp) for comp in blue))
    if len(sizes) != len(set(sizes)):
        errors.append("color-1 component sizes must be strictly distinct")
    if sizes not in _SIZE_PROFILE_BY_VALUE:
        errors.append(f"unsupported component-size profile {sizes!r}")

    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if not 1 <= len(marker_cells) <= 3:
        errors.append("marker-cell count must be in 1..3")
    marker_components = _components_of_color(grid, 9)
    if len(marker_components) != 1:
        errors.append("all marker cells must form one 4-connected component")
    if marker_cells:
        marker_rows = {r for r, _ in marker_cells}
        marker_cols = sorted(c for _, c in marker_cells)
        if len(marker_rows) != 1 or marker_cols != list(
            range(marker_cols[0], marker_cols[0] + len(marker_cols))
        ):
            errors.append("marker cells must form one contiguous horizontal bar")

    for comp in blue:
        r0, c0, r1, c1 = _bbox(comp)
        own = set(comp)
        foreign = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if grid[r][c] != 0 and (r, c) not in own
        ]
        if foreign:
            errors.append("component bounding boxes must contain no foreign nonzero cells")
            break
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, Any]:
    blue = _components_of_color(grid, 1)
    sizes = tuple(sorted(len(comp) for comp in blue))
    profile = _SIZE_PROFILE_BY_VALUE.get(sizes, "unrecognized")
    reading = sorted(blue, key=lambda comp: (_bbox(comp)[0], _bbox(comp)[1]))
    rank_by_size = {size: rank for rank, size in enumerate(sizes)}
    layout_value = tuple(rank_by_size[len(comp)] for comp in reading)
    layout = _RANK_LAYOUT_BY_VALUE.get(layout_value, "unrecognized")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "marker_count": sum(value == 9 for row in grid for value in row),
        "size_profile": profile,
        "rank_layout": layout,
    }


def _size_rank_not_position(grid) -> bool:
    try:
        return self_check(grid) == [] and _reading_order_rival(grid) != rule_mirror(grid)
    except Exception:
        return False


def _not_fixed_rank(rank: int):
    fixed = _fixed_rank_rival(rank)

    def witness(grid) -> bool:
        try:
            return self_check(grid) == [] and fixed(grid) != rule_mirror(grid)
        except Exception:
            return False

    return witness


SEMANTIC_RIVALS = {
    "reading_order_rank": _reading_order_rival,
    "always_smallest": _fixed_rank_rival(0),
    "always_middle": _fixed_rank_rival(1),
    "always_largest": _fixed_rank_rival(2),
}
SEMANTIC_WITNESSES = {
    "size_rank_not_position": _size_rank_not_position,
    "marker_count_not_always_smallest": _not_fixed_rank(0),
    "marker_count_not_always_middle": _not_fixed_rank(1),
    "marker_count_not_always_largest": _not_fixed_rank(2),
}
WITNESS_RIVALS = {
    "size_rank_not_position": ["reading_order_rank"],
    "marker_count_not_always_smallest": ["always_smallest"],
    "marker_count_not_always_middle": ["always_middle"],
    "marker_count_not_always_largest": ["always_largest"],
}
CANONICAL_SHORTCUTS = {"reading_order_rank": _reading_order_rival}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Check labels and require every declared rival to be refuted by demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"lesson has {len(demos)} demonstrations; requires at least {EXAMPLES_NEEDED}"
        )
    for index, pair in enumerate(demos):
        try:
            if self_check(pair["input"]):
                reasons.append(f"demonstration {index} has an invalid input")
            elif rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"demonstration {index} is mislabeled")
        except Exception as exc:
            reasons.append(
                f"demonstration {index} could not be checked: {type(exc).__name__}: {exc}"
            )
    try:
        if self_check(query["input"]):
            reasons.append("query input is invalid")
    except Exception as exc:
        reasons.append(f"query could not be checked: {type(exc).__name__}: {exc}")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"demonstrations do not refute competitor {name!r}")
    return reasons
