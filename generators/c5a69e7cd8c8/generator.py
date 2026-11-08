"""Generator for ARC task 25d487eb (review ID ``c5a69e7cd8c8``).

A color occurring exactly once sits on the open side of a monochrome support
shape.  The canonical rule finds the first open cardinal neighbour in
up/down/left/right order, then paints the singleton color through every zero
cell on the opposite ray.  Occupied support cells are skipped, not overwritten.

The selected Racket authority is unchanged.  This module samples observable,
constructive inputs and supplies a Python mirror only for tests and semantic
rivals.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c5a69e7cd8c8"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "bf2554f59664"

SUMMARY = (
    "A unique-color cell has exactly one open cardinal neighbour. Paint that "
    "singleton color through zero cells on the opposite ray, skipping the "
    "monochrome support shape rather than overwriting it."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 8

INVARIANTS = [
    "background is 0 and exactly two nonzero colors occur",
    "one nonzero color occurs once; every other nonzero cell uses one support color",
    "the singleton is interior with exactly one zero cardinal neighbour",
    "the other three cardinal neighbours are support cells",
    "a depth-2..3 triangular support core lies opposite the opening",
    "at least one zero cell remains beyond the support on the output ray",
]

DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}
OPENINGS = ("up", "down", "left", "right")

CANVAS_DIMS = {
    "12x12": (12, 12),
    "10x15": (10, 15),
    "15x12": (15, 12),
    "16x11": (16, 11),
    "14x14": (14, 14),
    "12x18": (12, 18),
    "18x12": (18, 12),
}
_DIMS_TO_CANVAS = {dims: name for name, dims in CANVAS_DIMS.items()}
_CANONICAL_DIMS = frozenset(((12, 12), (10, 15), (15, 12), (16, 11)))

# Values are (support_color, singleton_color).  The first four are the exact
# canonical palettes; the remaining four break palette-to-direction lookup.
PALETTES = {
    "8_3": (8, 3),
    "2_1": (2, 1),
    "3_2": (3, 2),
    "4_8": (4, 8),
    "6_9": (6, 9),
    "7_5": (7, 5),
    "1_7": (1, 7),
    "9_6": (9, 6),
}
_PALETTE_TO_NAME = {colors: name for name, colors in PALETTES.items()}
_CANONICAL_PALETTES = frozenset(((8, 3), (2, 1), (3, 2), (4, 8)))

ANCHORS = ("near_open", "middle", "near_support")
LATERALS = ("low", "middle", "high")

# Keep this a literal: the generator linter validates the advertised contract.
AXES = {
    "canvas": {
        "type": "str",
        "default": "eight-slot schedule with canonical and generalized canvases",
        "valid": "12x12|10x15|15x12|16x11|14x14|12x18|18x12",
    },
    "opening": {
        "type": "str",
        "default": "eight-slot schedule covering all four directions",
        "valid": "up|down|left|right",
    },
    "support_depth": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "palette": {
        "type": "str",
        "default": "canonical palettes interleaved with decoupled palettes",
        "valid": "8_3|2_1|3_2|4_8|6_9|7_5|1_7|9_6",
    },
    "anchor": {
        "type": "str",
        "default": "scheduled longitudinal position",
        "valid": "near_open|middle|near_support",
    },
    "lateral": {
        "type": "str",
        "default": "scheduled transverse position",
        "valid": "low|middle|high",
    },
    "n_extras": {
        "type": "int",
        "default": "scheduled 0..5 support decorations",
        "valid": "0..5",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Each four-example window contains multiple openings, a palette/direction
# mismatch, and a noncanonical support decoration.  Therefore every three-demo
# query rotation refutes the declared competitors instead of relying on a fixed
# fourth query position.
_ROLE_DEFAULTS = (
    {
        "canvas": "12x12", "opening": "down", "support_depth": 3,
        "palette": "8_3", "anchor": "middle", "lateral": "middle", "n_extras": 0,
    },
    {
        "canvas": "10x15", "opening": "up", "support_depth": 2,
        "palette": "2_1", "anchor": "near_open", "lateral": "low", "n_extras": 2,
    },
    {
        "canvas": "15x12", "opening": "right", "support_depth": 2,
        "palette": "3_2", "anchor": "near_support", "lateral": "high", "n_extras": 1,
    },
    {
        "canvas": "16x11", "opening": "left", "support_depth": 3,
        "palette": "4_8", "anchor": "middle", "lateral": "low", "n_extras": 3,
    },
    {
        "canvas": "14x14", "opening": "up", "support_depth": 2,
        "palette": "6_9", "anchor": "near_support", "lateral": "middle", "n_extras": 2,
    },
    {
        "canvas": "12x18", "opening": "right", "support_depth": 3,
        "palette": "7_5", "anchor": "near_open", "lateral": "high", "n_extras": 4,
    },
    {
        "canvas": "18x12", "opening": "down", "support_depth": 2,
        "palette": "1_7", "anchor": "middle", "lateral": "low", "n_extras": 1,
    },
    {
        "canvas": "12x12", "opening": "left", "support_depth": 3,
        "palette": "9_6", "anchor": "near_open", "lateral": "middle", "n_extras": 5,
    },
)


def _difficulty_band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the finite curriculum role used by an unoverridden draw."""
    del seed
    band = _difficulty_band(difficulty)
    offset = {"easy": 0, "medium": 2, "hard": 4}[band]
    return f"role_{(int(sample_index) + offset) % LESSON_SCHEDULE_PERIOD}"


def _role_defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, object]:
    role = int(schedule_profile(seed, sample_index, difficulty).split("_")[-1])
    return dict(_ROLE_DEFAULTS[role])


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    _difficulty_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {unknown}")

    string_domains = {
        "canvas": tuple(CANVAS_DIMS),
        "opening": OPENINGS,
        "palette": tuple(PALETTES),
        "anchor": ANCHORS,
        "lateral": LATERALS,
    }
    for name, options in string_domains.items():
        value = overrides.get(name)
        if value is None:
            continue
        if not isinstance(value, str) or value not in options:
            raise ValueError(f"{name} must be one of {options}, found {value!r}")

    integer_domains = {"support_depth": (2, 3), "n_extras": (0, 5)}
    for name, (lo, hi) in integer_domains.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}, found {value}")


def _draw_exact_choice(ctx, label: str, options: Sequence[str], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, tuple(options)))
    return str(ctx.draw_choice(label, (scheduled,)))


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return int(ctx.draw_int_strict(label, lo, hi))
    return int(ctx.draw_choice(label, (scheduled,)))


def _longitudinal_positions(length: int, depth: int, opening: str) -> dict[str, int]:
    if opening in ("up", "left"):
        near_open = 1
        near_support = length - depth - 2
    else:
        near_open = length - 2
        near_support = depth + 1
    middle = (near_open + near_support) // 2
    return {
        "near_open": near_open,
        "middle": middle,
        "near_support": near_support,
    }


def _lateral_positions(length: int, depth: int) -> dict[str, int]:
    low = depth
    high = length - depth - 1
    return {"low": low, "middle": (low + high) // 2, "high": high}


def _singleton_position(
    h: int,
    w: int,
    opening: str,
    depth: int,
    anchor: str,
    lateral: str,
) -> tuple[int, int]:
    if opening in ("up", "down"):
        return (
            _longitudinal_positions(h, depth, opening)[anchor],
            _lateral_positions(w, depth)[lateral],
        )
    return (
        _lateral_positions(h, depth)[lateral],
        _longitudinal_positions(w, depth, opening)[anchor],
    )


def _triangle_cells(
    singleton: tuple[int, int], opening: str, depth: int
) -> frozenset[tuple[int, int]]:
    sr, sc = singleton
    odr, odc = DIRECTIONS[opening]
    inward = (-odr, -odc)
    perpendicular = (inward[1], -inward[0])
    cells: set[tuple[int, int]] = set()
    for distance in range(depth + 1):
        half_width = depth - distance
        for offset in range(-half_width, half_width + 1):
            if distance == 0 and offset == 0:
                continue
            cells.add(
                (
                    sr + distance * inward[0] + offset * perpendicular[0],
                    sc + distance * inward[1] + offset * perpendicular[1],
                )
            )
    return frozenset(cells)


def _extra_candidates(
    h: int,
    w: int,
    singleton: tuple[int, int],
    opening: str,
    depth: int,
    core: frozenset[tuple[int, int]],
) -> list[tuple[int, int]]:
    sr, sc = singleton
    odr, odc = DIRECTIONS[opening]
    inward = (-odr, -odc)
    open_cell = (sr + odr, sc + odc)

    # Never let decorations complete a deeper triangle: support_depth must be
    # recoverable from pixels.  Also keep the post-support ray free so every
    # generated input changes under the authority.
    deeper = set()
    for candidate_depth in range(depth + 1, 5):
        deeper.update(_triangle_cells(singleton, opening, candidate_depth))
    ray_tail = {
        (sr + step * inward[0], sc + step * inward[1])
        for step in range(depth + 1, max(h, w))
        if 0 <= sr + step * inward[0] < h and 0 <= sc + step * inward[1] < w
    }
    forbidden = set(core) | deeper | ray_tail | {singleton, open_cell}

    # Prefer local four-neighbour decorations so support remains one coherent
    # object.  The full safe fallback makes every advertised cross-product
    # constructive on every advertised canvas/depth cross-product.
    local = set()
    for r, c in core:
        for dr, dc in DIRECTIONS.values():
            point = (r + dr, c + dc)
            if 0 <= point[0] < h and 0 <= point[1] < w and point not in forbidden:
                local.add(point)
    fallback = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in forbidden
    }
    return sorted(local) + sorted(fallback - local)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    defaults = _role_defaults(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canvas = _draw_exact_choice(ctx, "canvas", tuple(CANVAS_DIMS), str(defaults["canvas"]))
    opening = _draw_exact_choice(ctx, "opening", OPENINGS, str(defaults["opening"]))
    depth = _draw_exact_int(ctx, "support_depth", 2, 3, int(defaults["support_depth"]))
    palette = _draw_exact_choice(ctx, "palette", tuple(PALETTES), str(defaults["palette"]))
    anchor = _draw_exact_choice(ctx, "anchor", ANCHORS, str(defaults["anchor"]))
    lateral = _draw_exact_choice(ctx, "lateral", LATERALS, str(defaults["lateral"]))
    n_extras = _draw_exact_int(ctx, "n_extras", 0, 5, int(defaults["n_extras"]))

    h, w = CANVAS_DIMS[canvas]
    support_color, singleton_color = PALETTES[palette]
    singleton = _singleton_position(h, w, opening, depth, anchor, lateral)
    core = _triangle_cells(singleton, opening, depth)
    candidates = _extra_candidates(h, w, singleton, opening, depth, core)
    if len(candidates) < n_extras:
        raise RuntimeError(
            f"constructive extras exhausted: need {n_extras}, have {len(candidates)}"
        )
    extras = ctx.draw_rng("support_extras").sample(candidates, n_extras)

    grid = full_grid(h, w, 0)
    for r, c in core:
        grid[r][c] = support_color
    for r, c in extras:
        grid[r][c] = support_color
    grid[singleton[0]][singleton[1]] = singleton_color
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an ARC integer color 0..9"]
    return []


def _infer_depth(
    support_cells: frozenset[tuple[int, int]],
    singleton: tuple[int, int],
    opening: str,
) -> int | None:
    matches = [
        depth
        for depth in range(2, 4)
        if _triangle_cells(singleton, opening, depth) <= support_cells
    ]
    return max(matches) if matches else None


def _analyze(grid: Sequence[Sequence[int]]) -> tuple[dict[str, Any], list[str]]:
    errors = _rectangular_errors(grid)
    if errors:
        return {}, errors
    h, w = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) != 2:
        return {}, [f"expected exactly two nonzero colors, found {len(counts)}"]
    singleton_colors = [color for color, count in counts.items() if count == 1]
    if len(singleton_colors) != 1:
        return {}, [f"expected exactly one singleton color, found {len(singleton_colors)}"]
    singleton_color = singleton_colors[0]
    support_colors = [color for color in counts if color != singleton_color]
    support_color = support_colors[0]
    singleton = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == singleton_color
    )
    sr, sc = singleton
    if not (0 < sr < h - 1 and 0 < sc < w - 1):
        return {}, ["singleton must be strictly inside the grid"]

    openings = []
    for name, (dr, dc) in DIRECTIONS.items():
        value = grid[sr + dr][sc + dc]
        if value == 0:
            openings.append(name)
        elif value != support_color:
            errors.append(f"{name} neighbour must be zero or support color")
    if len(openings) != 1:
        errors.append(f"expected exactly one open cardinal neighbour, found {len(openings)}")
    if errors:
        return {}, errors
    opening = openings[0]

    support_cells = frozenset(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == support_color
    )
    depth = _infer_depth(support_cells, singleton, opening)
    if depth is None:
        return {}, ["support does not contain a depth-2..3 triangular core"]
    core = _triangle_cells(singleton, opening, depth)
    extras = support_cells - core
    if len(extras) > 5:
        errors.append(f"expected at most 5 support extras, found {len(extras)}")

    odr, odc = DIRECTIONS[opening]
    inward = (-odr, -odc)
    ray_zero_cells = []
    for step in range(1, max(h, w)):
        r, c = sr + step * inward[0], sc + step * inward[1]
        if not (0 <= r < h and 0 <= c < w):
            continue
        if grid[r][c] == 0:
            ray_zero_cells.append((r, c))
    if not ray_zero_cells:
        errors.append("opposite ray must contain at least one zero cell")
    if errors:
        return {}, errors

    return {
        "height": h,
        "width": w,
        "singleton_color": singleton_color,
        "support_color": support_color,
        "singleton_position": singleton,
        "support_cells": support_cells,
        "opening": opening,
        "support_depth": depth,
        "core_cells": core,
        "extra_cells": extras,
        "ray_zero_cells": tuple(ray_zero_cells),
    }, []


def analyze(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return info


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def _label_for_position(mapping: dict[str, int], value: int, name: str) -> str:
    hits = [label for label, expected in mapping.items() if expected == value]
    if len(hits) != 1:
        raise ValueError(f"cannot recover {name} from coordinate {value}: {mapping}")
    return hits[0]


def observe_overrides(grid) -> dict[str, object]:
    info = analyze(grid)
    h, w = info["height"], info["width"]
    opening = info["opening"]
    depth = info["support_depth"]
    sr, sc = info["singleton_position"]
    canvas = _DIMS_TO_CANVAS.get((h, w))
    if canvas is None:
        raise ValueError(f"unrecognized canvas dimensions {(h, w)}")
    palette = _PALETTE_TO_NAME.get((info["support_color"], info["singleton_color"]))
    if palette is None:
        raise ValueError("unrecognized support/singleton palette")

    if opening in ("up", "down"):
        anchor = _label_for_position(
            _longitudinal_positions(h, depth, opening), sr, "anchor"
        )
        lateral = _label_for_position(_lateral_positions(w, depth), sc, "lateral")
    else:
        anchor = _label_for_position(
            _longitudinal_positions(w, depth, opening), sc, "anchor"
        )
        lateral = _label_for_position(_lateral_positions(h, depth), sr, "lateral")

    return {
        "canvas": canvas,
        "opening": opening,
        "support_depth": depth,
        "palette": palette,
        "anchor": anchor,
        "lateral": lateral,
        "n_extras": len(info["extra_cells"]),
    }


def strict_canonical_like(grid) -> list[str]:
    info, errors = _analyze(grid)
    if errors:
        return errors
    findings = []
    if (info["height"], info["width"]) not in _CANONICAL_DIMS:
        findings.append("dimensions are outside the four canonical profiles")
    if (info["support_color"], info["singleton_color"]) not in _CANONICAL_PALETTES:
        findings.append("palette is outside the four canonical support/singleton pairs")
    if info["support_depth"] not in (2, 3):
        findings.append("canonical support depth must be 2 or 3")
    if info["extra_cells"]:
        findings.append("canonical support is an exact triangle without extras")
    return findings


def _minority_position(grid: Sequence[Sequence[int]]) -> tuple[int, int, int]:
    counts = Counter(value for row in grid for value in row if value != 0)
    minority = next(color for color, count in counts.items() if count == 1)
    r, c = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == minority
    )
    return minority, r, c


def _canonical_opening(grid: Sequence[Sequence[int]], r: int, c: int) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    if r > 0 and grid[r - 1][c] == 0:
        return -1, 0
    if r < h - 1 and grid[r + 1][c] == 0:
        return 1, 0
    if c > 0 and grid[r][c - 1] == 0:
        return 0, -1
    return 0, 1


def _paint_zero_ray(
    grid: Sequence[Sequence[int]],
    direction: tuple[int, int],
    *,
    overwrite: bool = False,
) -> list[list[int]]:
    color, r, c = _minority_position(grid)
    result = [list(row) for row in grid]
    h, w = len(result), len(result[0])
    dr, dc = direction
    for step in range(1, max(h, w)):
        nr, nc = r + dr * step, c + dc * step
        if 0 <= nr < h and 0 <= nc < w:
            if overwrite or result[nr][nc] == 0:
                result[nr][nc] = color
    return result


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    _, r, c = _minority_position(grid)
    opening = _canonical_opening(grid, r, c)
    return _paint_zero_ray(grid, (-opening[0], -opening[1]))


def _rival_through_open_side(grid):
    _, r, c = _minority_position(grid)
    return _paint_zero_ray(grid, _canonical_opening(grid, r, c))


def _rival_stop_at_support(grid):
    return [list(row) for row in grid]


def _rival_overwrite_support(grid):
    _, r, c = _minority_position(grid)
    opening = _canonical_opening(grid, r, c)
    return _paint_zero_ray(grid, (-opening[0], -opening[1]), overwrite=True)


def _rival_always_up(grid):
    return _paint_zero_ray(grid, (-1, 0))


def _rival_canonical_triangle_only(grid):
    if strict_canonical_like(grid) == []:
        return rule_mirror(grid)
    return [list(row) for row in grid]


def _rival_palette_direction_lookup(grid):
    color, _, _ = _minority_position(grid)
    direction = {
        3: (-1, 0),  # canonical 8/3 example
        1: (0, 1),   # canonical 2/1 example
        2: (1, 0),   # canonical 3/2 example
        8: (-1, 0),  # canonical 4/8 example
    }.get(color)
    if direction is None:
        return [list(row) for row in grid]
    return _paint_zero_ray(grid, direction)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "canonical_triangle_only": _rival_canonical_triangle_only,
    "palette_direction_lookup": _rival_palette_direction_lookup,
    "through_open_side": _rival_through_open_side,
    "stop_at_support": _rival_stop_at_support,
    "overwrite_support": _rival_overwrite_support,
    "always_up": _rival_always_up,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_triangle_only": _rival_canonical_triangle_only,
    "palette_direction_lookup": _rival_palette_direction_lookup,
}


def _differs_from(name: str):
    rival = SEMANTIC_RIVALS[name]
    return lambda grid: rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "noncanonical_support_refutes_exact_triangle_only": _differs_from(
        "canonical_triangle_only"
    ),
    "palette_is_decoupled_from_direction": _differs_from(
        "palette_direction_lookup"
    ),
    "ray_is_opposite_the_open_side": _differs_from("through_open_side"),
    "ray_skips_support_and_continues": lambda grid: (
        _rival_stop_at_support(grid) != rule_mirror(grid)
        and _rival_overwrite_support(grid) != rule_mirror(grid)
    ),
}

WITNESS_RIVALS = {
    "noncanonical_support_refutes_exact_triangle_only": [
        "canonical_triangle_only"
    ],
    "palette_is_decoupled_from_direction": ["palette_direction_lookup"],
    "ray_is_opposite_the_open_side": ["through_open_side"],
    "ray_skips_support_and_continues": [
        "stop_at_support",
        "overwrite_support",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            differs_on_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} failed: {exc!r}")
            continue
        if fits_demos and differs_on_query:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return reasons
