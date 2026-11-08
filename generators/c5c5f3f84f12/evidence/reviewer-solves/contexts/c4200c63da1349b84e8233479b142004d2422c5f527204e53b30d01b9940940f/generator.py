"""Source-bound generator for corner-coded object rotation.

A unique blue marker selects one of the four grid corners.  Reading corners
clockwise from top-left gives the quarter-turn code 0, 1, 2, 3.  The unique red
object is normalized, rotated clockwise by that code, cropped to its bounding
box, and recoloured cyan.  A second, non-blue singleton occupies a different
corner exactly as in the canonical task; it is a distractor, not a control.

The four-slot teaching schedule visits every blue-corner code in every four
consecutive default samples.  A separate five-slot anchor schedule repeatedly
emits canonical height/width/palette profiles in every difficulty band.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c5c5f3f84f12"
TASK_ID = GENERATOR_ID
RULE_HASH = "148139dec0ec"
VERSION = "2.0.0"

SUMMARY = (
    "The blue(1) corner encodes 0/1/2/3 clockwise quarter-turns for the red(2) "
    "object. Ignore the differently coloured corner singleton, rotate and "
    "normalize the red object, crop it, and recolour it cyan(8)."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the rectangular input is 8..20 cells on each side and uses exactly four colours",
    "there is exactly one blue control singleton in a corner",
    "there is exactly one differently coloured singleton (3..7) in another corner",
    "there is exactly one 4-connected red object of 3..8 cells away from both markers",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/weighted 8..20", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "scheduled/weighted 8..20", "valid": "8..20"},
    "corner_position": {
        "type": "str",
        "default": "sample_index mod 4",
        "valid": "tl|tr|br|bl",
    },
    "distractor_color": {
        "type": "int",
        "default": "scheduled/uniform 3..7",
        "valid": "3..7",
    },
    "blob_size": {
        "type": "int",
        "default": "difficulty-weighted 3..8",
        "valid": "3..8",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CORNER_ORDER = ("tl", "tr", "br", "bl")
SCHEDULE_PROFILES = _CORNER_ORDER

# (height, width, distractor colour, red-cell count).  The first three values
# are the complete profile used by canonical_profile_gate; the fourth keeps the
# anchors close to the actual source examples without replaying any grid.
_CANONICAL_ANCHORS = (
    (8, 8, 6, 3),
    (8, 9, 3, 4),
    (9, 8, 7, 3),
    (9, 9, 4, 3),
    (10, 10, 5, 4),
)

# Guaranteed connected fallbacks with four distinct quarter-turn signatures.
_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    3: ((0, 0), (0, 1), (1, 0)),
    4: ((0, 0), (0, 1), (0, 2), (1, 0)),
    5: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
    6: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    7: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Declared teaching profile: one blue-corner code per residue class."""
    del seed, difficulty
    return _CORNER_ORDER[int(sample_index) % len(_CORNER_ORDER)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    integer_bounds = {
        "grid_h": (8, 20),
        "grid_w": (8, 20),
        "distractor_color": (3, 7),
        "blob_size": (3, 8),
    }
    for name, value in overrides.items():
        if name == "corner_position":
            if type(value) is not str:
                raise TypeError(
                    f"corner_position must be a string, not {type(value).__name__}"
                )
            if value not in _CORNER_ORDER:
                raise ValueError(
                    f"corner_position={value!r} not in {_CORNER_ORDER}"
                )
            continue
        if type(value) is not int:  # bool is deliberately rejected.
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = integer_bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _normalize_cells(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple((int(r), int(c)) for r, c in cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot90_cells(cells) -> tuple[tuple[int, int], ...]:
    norm = _normalize_cells(cells)
    rmax = max(r for r, _ in norm)
    return _normalize_cells((c, rmax - r) for r, c in norm)


def _rotate_cells(cells, code: int) -> tuple[tuple[int, int], ...]:
    result = _normalize_cells(cells)
    for _ in range(int(code) % 4):
        result = _rot90_cells(result)
    return result


def _four_distinct_rotations(cells) -> bool:
    rotations = []
    current = _normalize_cells(cells)
    for _ in range(4):
        rotations.append(current)
        current = _rot90_cells(current)
    return len(set(rotations)) == 4


def _random_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Grow a connected <=4x4 polyomino whose rotation signal is observable."""
    for _ in range(256):
        cells = {(rng.randrange(4), rng.randrange(4))}
        while len(cells) < size:
            frontier = sorted(
                {
                    (nr, nc)
                    for r, c in cells
                    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                    if 0 <= nr < 4 and 0 <= nc < 4 and (nr, nc) not in cells
                }
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        shape = _normalize_cells(cells)
        if len(shape) == size and _four_distinct_rotations(shape):
            return shape
    return _FALLBACK_SHAPES[size]


def _broad_dimension(ctx, label: str, difficulty) -> int:
    pools = {
        "easy": tuple(range(8, 12)),
        "medium": tuple(range(10, 16)),
        "hard": tuple(range(14, 21)),
    }
    pool = pools.get(difficulty, tuple(range(8, 21)))
    return ctx.draw_rng(f"{label}_scheduled_default").choice(pool)


def _broad_blob_size(ctx, difficulty) -> int:
    pools = {
        "easy": (3, 4),
        "medium": (4, 5, 6),
        "hard": (6, 7, 8),
    }
    pool = pools.get(difficulty, tuple(range(3, 9)))
    return ctx.draw_rng("blob_size_scheduled_default").choice(pool)


def _scheduled_defaults(ctx, sample_index: int, difficulty) -> dict[str, Any]:
    index = int(sample_index)
    defaults: dict[str, Any] = {
        "corner_position": _CORNER_ORDER[index % 4],
    }
    if index % 5 == 0:
        h, w, distractor, blob_size = _CANONICAL_ANCHORS[(index // 5) % 5]
        defaults.update(
            grid_h=h,
            grid_w=w,
            distractor_color=distractor,
            blob_size=blob_size,
        )
    else:
        defaults.update(
            grid_h=_broad_dimension(ctx, "grid_h", difficulty),
            grid_w=_broad_dimension(ctx, "grid_w", difficulty),
            distractor_color=ctx.draw_rng("distractor_color_scheduled_default").choice(
                tuple(range(3, 8))
            ),
            blob_size=_broad_blob_size(ctx, difficulty),
        )
    return defaults


def _draw_axes(ctx, defaults: dict[str, Any], user_overrides: dict[str, Any]):
    # Schedule defaults are injected only for absent caller values.  Every axis
    # is still consumed by a typed GenCtx draw over its complete legal domain,
    # so override provenance and contract auditing remain exact.
    for name, value in defaults.items():
        if name not in user_overrides:
            ctx.overrides[name] = value
    h = ctx.draw_choice("grid_h", tuple(range(8, 21)))
    w = ctx.draw_choice("grid_w", tuple(range(8, 21)))
    corner = ctx.draw_choice("corner_position", _CORNER_ORDER)
    distractor = ctx.draw_choice("distractor_color", tuple(range(3, 8)))
    blob_size = ctx.draw_choice("blob_size", tuple(range(3, 9)))
    return h, w, corner, distractor, blob_size


def _corner_map(h: int, w: int) -> dict[str, tuple[int, int]]:
    return {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "br": (h - 1, w - 1),
        "bl": (h - 1, 0),
    }


def _place_red_object(grid, shape, markers, rng) -> None:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    positions = [
        (r, c)
        for r in range(h - sh + 1)
        for c in range(w - sw + 1)
        if all(
            grid[r + dr][c + dc] == 0
            and all(
                abs((r + dr) - mr) > 1 or abs((c + dc) - mc) > 1
                for mr, mc in markers
            )
            for dr, dc in shape
        )
    ]
    if not positions:
        raise ValueError("could not place red object away from both corner markers")
    row, col = rng.choice(positions)
    for dr, dc in shape:
        grid[row + dr][col + dc] = 2


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
    defaults = _scheduled_defaults(ctx, sample_index, difficulty)
    h, w, corner_name, distractor_color, blob_size = _draw_axes(
        ctx, defaults, overrides
    )

    grid = full_grid(h, w, 0)
    corners = _corner_map(h, w)
    control = corners[corner_name]
    other_names = tuple(name for name in _CORNER_ORDER if name != corner_name)
    distractor_name = ctx.draw_rng("distractor_corner").choice(other_names)
    distractor = corners[distractor_name]
    grid[control[0]][control[1]] = 1
    grid[distractor[0]][distractor[1]] = distractor_color

    shape = _random_shape(ctx.draw_rng("red_shape"), blob_size)
    _place_red_object(
        grid,
        shape,
        (control, distractor),
        ctx.draw_rng("red_position"),
    )
    return grid


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        r, c = todo.pop()
        for neighbour in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbour in cells and neighbour not in seen:
                seen.add(neighbour)
                todo.append(neighbour)
    return seen == cells


def _analyse(grid) -> tuple[list[str], dict[str, Any]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], {}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], {}
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"], {}
    h = len(grid)
    errors: list[str] = []
    if not 8 <= h <= 20:
        errors.append(f"grid_h={h} outside [8,20]")
    if not 8 <= w <= 20:
        errors.append(f"grid_w={w} outside [8,20]")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colours 0..9")
        return errors, {}

    corners = _corner_map(h, w)
    corner_by_position = {position: name for name, position in corners.items()}
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    control_name = None
    if len(blues) != 1:
        errors.append(f"expected exactly one blue marker, got {len(blues)}")
    elif blues[0] not in corner_by_position:
        errors.append(f"blue marker is not in a corner: {blues[0]}")
    else:
        control_name = corner_by_position[blues[0]]

    extras = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 2)
    ]
    distractor_color = None
    distractor_position = None
    if len(extras) != 1:
        errors.append(
            f"expected exactly one non-blue corner distractor cell, got {len(extras)}"
        )
    else:
        r, c, value = extras[0]
        distractor_color = value
        distractor_position = (r, c)
        if not 3 <= value <= 7:
            errors.append(f"distractor colour {value} outside [3,7]")
        if distractor_position not in corner_by_position:
            errors.append(f"distractor is not in a corner: {distractor_position}")
        if blues and distractor_position == blues[0]:
            errors.append("blue control and distractor occupy the same corner")

    red_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    if not 3 <= len(red_cells) <= 8:
        errors.append(f"red object has {len(red_cells)} cells (expect 3..8)")
    if red_cells and not _connected(red_cells):
        errors.append("red cells must form exactly one 4-connected object")

    marker_positions = []
    if len(blues) == 1:
        marker_positions.append(blues[0])
    if distractor_position is not None:
        marker_positions.append(distractor_position)
    touching = sorted(
        (r, c)
        for r, c in red_cells
        if any(abs(r - mr) <= 1 and abs(c - mc) <= 1 for mr, mc in marker_positions)
    )
    if touching:
        errors.append(f"red object touches a corner marker: {touching[:5]}")

    palette = {value for row in grid for value in row}
    if len(palette) != 4 or not {0, 1, 2}.issubset(palette):
        errors.append(f"expected palette {{0,1,2,distractor}}, got {sorted(palette)}")

    observed = {
        "grid_h": h,
        "grid_w": w,
        "corner_position": control_name,
        "distractor_color": distractor_color,
        "blob_size": len(red_cells),
    }
    return errors, observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate both canonical examples and the full constructive manifold."""
    del difficulty, meta
    errors, _ = _analyse(grid)
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    errors, observed = _analyse(grid)
    if errors:
        raise ValueError(f"grid is outside the declared manifold: {errors[0]}")
    return observed


def _control_code(grid) -> int:
    observed = observe_overrides(grid)
    return {"tl": 0, "tr": 1, "br": 2, "bl": 3}[
        observed["corner_position"]
    ]


def _distractor_code(grid) -> int:
    h, w = len(grid), len(grid[0])
    corners = _corner_map(h, w)
    by_position = {position: name for name, position in corners.items()}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 1, 2):
                return {"tl": 0, "tr": 1, "br": 2, "bl": 3}[
                    by_position[(r, c)]
                ]
    raise ValueError("missing distractor")


def _solve_with_code(grid, code: int, output_color: int = 8) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot solve malformed input: {errors[0]}")
    red = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    cells = _rotate_cells(red, code)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    output = full_grid(h, w, 0)
    for r, c in cells:
        output[r][c] = output_color
    return output


def _solve_official(grid) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket authority."""
    return _solve_with_code(grid, _control_code(grid), 8)


def _rival_distractor_corner(grid):
    return _solve_with_code(grid, _distractor_code(grid), 8)


def _rival_fixed_identity(grid):
    return _solve_with_code(grid, 0, 8)


def _rival_counterclockwise(grid):
    return _solve_with_code(grid, (-_control_code(grid)) % 4, 8)


def _rival_keep_red(grid):
    return _solve_with_code(grid, _control_code(grid), 2)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "use_distractor_corner": _rival_distractor_corner,
    "fixed_identity": _rival_fixed_identity,
    "counterclockwise": _rival_counterclockwise,
    "retain_red_color": _rival_keep_red,
}
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _differs_from(rival_name: str):
    def witness(grid) -> bool:
        return SEMANTIC_RIVALS[rival_name](grid) != _solve_official(grid)

    return witness


SEMANTIC_WITNESSES = {
    name: _differs_from(name) for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query) -> list[str]:
    """Require four corner codes and reject every declared shortcut rule."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demos, got {len(demos)}")

    observed_corners: set[str] = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        issues = self_check(grid)
        if issues:
            reasons.append(f"demo {index} is outside the manifold: {issues[0]}")
            continue
        observed_corners.add(observe_overrides(grid)["corner_position"])
        if _solve_official(grid) != output:
            reasons.append(f"demo {index} output disagrees with the pinned rule mirror")

    if observed_corners != set(_CORNER_ORDER):
        reasons.append(
            f"demos cover corners {sorted(observed_corners)}, expected {list(_CORNER_ORDER)}"
        )

    query_grid = query.get("input")
    query_output = query.get("output")
    query_issues = self_check(query_grid)
    if query_issues:
        reasons.append(f"query is outside the manifold: {query_issues[0]}")
        return reasons
    if _solve_official(query_grid) != query_output:
        reasons.append("query output disagrees with the pinned rule mirror")

    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = rival(query_grid) != query_output
        except Exception as exc:
            reasons.append(
                f"competitor {name!r} raised {type(exc).__name__}: {exc}"
            )
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons
