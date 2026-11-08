"""Reviewed generator for ARC task e9905db3a38d.

Two square templates, colored 1 and 2, appear above a two-row code grid.
Codes 1/2 paste the corresponding template and codes 3/4 paste its clockwise
rotation.  Decoded tiles are separated by one background row/column.

The four-profile schedule keeps a canonical-linked 3x3/three-column case in
one quarter of every difficulty band while also varying tile and mosaic size.
Every generated example exposes all four code branches, uses rotation-asymmetric
templates, and randomizes code positions so the mapping cannot be learned from
fixed corners.  Input dimensions are always strictly larger than the decoded
output, matching the canonical size relation.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e9905db3a38d"
TASK_ID = "e9905db3a38d"
VERSION = "4.0.0"
RULE_HASH = "7b04fc79d5f0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Two equal-size square templates (colors 1 and 2) sit above a two-row code "
    "grid. Codes 1/2 paste the templates, codes 3/4 paste clockwise rotations, "
    "and neighboring output tiles have a one-cell background gutter. A four-profile "
    "curriculum varies tile size and active code width while retaining 25% "
    "canonical-linked 3x3/three-column examples in every difficulty band."
)

INVARIANTS = [
    "the top area has exactly one 4-connected color-1 and one color-2 template",
    "both templates span the same square bbox and are changed by clockwise rotation",
    "the active two-row code block is contiguous and every active column is non-empty",
    "every generated example contains codes 1, 2, 3, and 4",
    "input height and width are both strictly larger than the decoded output",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "tile_size": {
        "type": "int",
        "default": "four-profile band schedule",
        "valid": "2..4",
    },
    "n_codecols": {
        "type": "int",
        "default": "four-profile band schedule",
        "valid": "2..4",
    },
}

SCHEDULE_PROFILES = ("canonical", "compact", "wide", "large")
_PROFILE_AXES = {
    None: {
        "canonical": (3, 3),
        "compact": (2, 2),
        "wide": (3, 4),
        "large": (4, 3),
    },
    "easy": {
        "canonical": (3, 3),
        "compact": (2, 2),
        "wide": (2, 4),
        "large": (3, 2),
    },
    "medium": {
        "canonical": (3, 3),
        "compact": (2, 3),
        "wide": (3, 4),
        "large": (4, 2),
    },
    "hard": {
        "canonical": (3, 3),
        "compact": (3, 2),
        "wide": (3, 4),
        "large": (4, 4),
    },
}
_CANONICAL_INPUT_DIMS = ((10, 12), (10, 13), (11, 12), (10, 14), (11, 13))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

Point = tuple[int, int]
Shape = frozenset[Point]
Grid = list[list[int]]


def _coerce_grid(grid: Any) -> Grid:
    if not isinstance(grid, list):
        raise ValueError("grid must be a list")
    result: Grid = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _norm(points: Iterable[Point]) -> Shape:
    cells = tuple(points)
    if not cells:
        return frozenset()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _rotate_shape_cw(shape: Shape) -> Shape:
    if not shape:
        return frozenset()
    height = max(row for row, _ in shape) + 1
    return _norm((col, height - 1 - row) for row, col in shape)


def _connected(shape: Shape) -> bool:
    if not shape:
        return False
    remaining = set(shape)
    start = min(remaining)
    remaining.remove(start)
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for drow, dcol in _CARDINAL:
            nxt = (row + drow, col + dcol)
            if nxt in remaining:
                remaining.remove(nxt)
                queue.append(nxt)
    return not remaining


@lru_cache(maxsize=None)
def _shape_candidates(tile_size: int, area: int) -> tuple[Shape, ...]:
    """Enumerate connected, bbox-spanning, rotation-observable square shapes."""
    cells = tuple((row, col) for row in range(tile_size) for col in range(tile_size))
    candidates: list[Shape] = []
    for chosen in combinations(cells, area):
        shape = frozenset(chosen)
        rows = {row for row, _ in shape}
        cols = {col for _, col in shape}
        if 0 not in rows or tile_size - 1 not in rows:
            continue
        if 0 not in cols or tile_size - 1 not in cols:
            continue
        if not _connected(shape):
            continue
        if _rotate_shape_cw(shape) == shape:
            continue
        candidates.append(shape)
    return tuple(candidates)


def _template_area(tile_size: int, canonical_profile: bool, rng) -> int:
    if tile_size == 2:
        return 3
    if canonical_profile and tile_size == 3:
        return 6
    choices = {
        3: (5, 6, 7),
        4: (7, 8, 9, 10),
    }[tile_size]
    return rng.choice(choices)


def _choose_templates(tile_size: int, area: int, rng) -> tuple[Shape, Shape]:
    candidates = _shape_candidates(tile_size, area)
    if len(candidates) < 2:
        raise RuntimeError(
            f"no distinct rotation-observable templates for tile_size={tile_size}, area={area}"
        )
    first = rng.choice(candidates)
    second_options = tuple(shape for shape in candidates if shape != first)
    second = rng.choice(second_options)
    return first, second


def _components_for_color(grid: Grid, color: int) -> list[tuple[Point, ...]]:
    remaining = {
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == color
    }
    components: list[tuple[Point, ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _CARDINAL:
                nxt = (row + drow, col + dcol)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        components.append(tuple(sorted(cells)))
    return components


def _bbox(cells: Iterable[Point]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(row for row, _ in points),
        min(col for _, col in points),
        max(row for row, _ in points),
        max(col for _, col in points),
    )


def _crop_component(grid: Grid, cells: Iterable[Point]) -> Grid:
    points = tuple(cells)
    row0, col0, row1, col1 = _bbox(points)
    keep = set(points)
    return [
        [grid[row][col] if (row, col) in keep else 0 for col in range(col0, col1 + 1)]
        for row in range(row0, row1 + 1)
    ]


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    if not values or not values[0]:
        return {"errors": ["grid must be non-empty"]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}
    height = len(values)
    if height < 5:
        errors.append("grid must leave a template area above two code rows")
    if height > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30x30")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in values
        for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}
    if height < 2:
        return {"errors": errors, "grid": values, "height": height, "width": width}

    top = values[:-2]
    code = values[-2:]
    bad_top = sorted({value for row in top for value in row if value not in (0, 1, 2)})
    if bad_top:
        errors.append(f"template area uses colors outside 0,1,2: {bad_top!r}")
    bad_codes = sorted({value for row in code for value in row if value not in (0, 1, 2, 3, 4)})
    if bad_codes:
        errors.append(f"code grid uses values outside 0..4: {bad_codes!r}")

    by_color = {color: _components_for_color(top, color) for color in (1, 2)}
    for color in (1, 2):
        if len(by_color[color]) != 1:
            errors.append(
                f"expected exactly one 4-connected color-{color} template, got {len(by_color[color])}"
            )
    templates: dict[int, tuple[Point, ...]] = {}
    shapes: dict[int, Shape] = {}
    crops: dict[int, Grid] = {}
    tile_size = None
    if all(len(by_color[color]) == 1 for color in (1, 2)):
        sizes: list[tuple[int, int]] = []
        for color in (1, 2):
            component = by_color[color][0]
            templates[color] = component
            row0, col0, row1, col1 = _bbox(component)
            sizes.append((row1 - row0 + 1, col1 - col0 + 1))
            shapes[color] = _norm(component)
            crops[color] = _crop_component(top, component)
        if sizes[0] != sizes[1] or sizes[0][0] != sizes[0][1]:
            errors.append(f"templates must span the same square bbox, got {sizes!r}")
        else:
            tile_size = sizes[0][0]
            if tile_size not in (2, 3, 4):
                errors.append(f"tile size must be 2..4, got {tile_size}")
        if shapes[1] == shapes[2]:
            errors.append("the two templates must have distinct shapes")
        for color in (1, 2):
            if shapes[color] and _rotate_shape_cw(shapes[color]) == shapes[color]:
                errors.append(f"color-{color} template is unchanged by clockwise rotation")

    active_columns = [
        col for col in range(width) if any(code[row][col] != 0 for row in range(2))
    ]
    code_start = code_end = None
    code_block: Grid = [[], []]
    n_codecols = 0
    if not active_columns:
        errors.append("code grid must contain a non-zero code")
    else:
        code_start, code_end = min(active_columns), max(active_columns)
        n_codecols = code_end - code_start + 1
        code_block = [row[code_start : code_end + 1] for row in code]
        if n_codecols not in (2, 3, 4):
            errors.append(f"active code width must be 2..4, got {n_codecols}")
        empty_inside = [
            col
            for col in range(n_codecols)
            if not any(code_block[row][col] for row in range(2))
        ]
        if empty_inside:
            errors.append(f"active code span contains empty columns: {empty_inside!r}")
        branches = {value for row in code_block for value in row if value}
        if branches != {1, 2, 3, 4}:
            errors.append(f"code block must expose all four branches, got {sorted(branches)!r}")

    output_height = output_width = None
    if tile_size is not None and n_codecols:
        output_height = 2 * tile_size + 1
        output_width = n_codecols * tile_size + (n_codecols - 1)
        if height <= output_height or width <= output_width:
            errors.append(
                "input must be strictly larger than output in both dimensions, "
                f"got input={height}x{width}, output={output_height}x{output_width}"
            )

    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "top": top,
        "code": code,
        "templates": templates,
        "shapes": shapes,
        "crops": crops,
        "tile_size": tile_size,
        "active_columns": tuple(active_columns),
        "code_start": code_start,
        "code_end": code_end,
        "code_block": code_block,
        "n_codecols": n_codecols,
        "output_height": output_height,
        "output_width": output_width,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = {
        "tile_size": analysis["tile_size"],
        "n_codecols": analysis["n_codecols"],
    }
    for name, actual in observed.items():
        expected = requested.get(name)
        if expected is not None and expected != actual:
            errors.append(f"meta {name} requested {expected!r}, observed {actual!r}")
    return errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "tile_size": analysis["tile_size"],
        "n_codecols": analysis["n_codecols"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["tile_size"] != 3:
        errors.append("canonical-linked examples use 3x3 templates")
    if analysis["n_codecols"] != 3:
        errors.append("canonical-linked examples use three active code columns")
    if analysis["height"] not in (10, 11) or not 12 <= analysis["width"] <= 14:
        errors.append("canonical-linked input dimensions are 10..11 by 12..14")
    if any(len(analysis["shapes"][color]) != 6 for color in (1, 2)):
        errors.append("canonical-linked templates contain six cells each")
    return errors


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _PROFILE_AXES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(
        name for name, value in overrides.items() if value is not None and name not in AXES
    )
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in AXES:
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not 2 <= value <= 4:
            raise ValueError(f"{name} must be in 2..4")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, 2, 4)
    return ctx.draw_int(name, default, default)


def _input_dimensions(
    profile: str,
    tile_size: int,
    n_codecols: int,
    rng,
) -> tuple[int, int]:
    if profile == "canonical" and (tile_size, n_codecols) == (3, 3):
        return rng.choice(_CANONICAL_INPUT_DIMS)
    output_height = 2 * tile_size + 1
    output_width = n_codecols * tile_size + (n_codecols - 1)
    return output_height + rng.randint(1, 3), output_width + rng.randint(1, 3)


def _place_templates(
    grid: Grid,
    first: Shape,
    second: Shape,
    tile_size: int,
    rng,
) -> None:
    height = len(grid)
    width = len(grid[0])
    top_height = height - 2
    gap = rng.randint(1, min(2, width - 2 * tile_size))
    left_room = width - (2 * tile_size + gap)
    if left_room < 0 or top_height < tile_size:
        raise RuntimeError("input dimensions do not fit both templates")
    top = rng.randint(0, top_height - tile_size)
    left = rng.randint(0, left_room)
    second_left = left + tile_size + gap
    for row, col in first:
        grid[top + row][left + col] = 1
    for row, col in second:
        grid[top + row][second_left + col] = 2


def _place_code_block(grid: Grid, n_codecols: int, rng) -> None:
    width = len(grid[0])
    start = rng.randint(0, width - n_codecols)
    positions = [(row, col) for row in range(2) for col in range(n_codecols)]
    rng.shuffle(positions)
    codes = [1, 2, 3, 4]
    rng.shuffle(codes)
    local = [[0 for _ in range(n_codecols)] for _ in range(2)]
    for (row, col), code in zip(positions[:4], codes):
        local[row][col] = code
    for row, col in positions[4:]:
        local[row][col] = rng.choice((0, 0, 1, 2, 3, 4))
    for col in range(n_codecols):
        if local[0][col] == 0 and local[1][col] == 0:
            row = rng.randrange(2)
            local[row][col] = rng.randint(1, 4)
    for row in range(2):
        for col in range(n_codecols):
            grid[len(grid) - 2 + row][start + col] = local[row][col]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    default_tile, default_codecols = _PROFILE_AXES[difficulty][profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    tile_size = _draw_axis(ctx, overrides, "tile_size", default_tile)
    n_codecols = _draw_axis(ctx, overrides, "n_codecols", default_codecols)

    shape_rng = ctx.draw_rng(
        f"templates|profile={profile}|tile={tile_size}|codecols={n_codecols}"
    )
    area = _template_area(
        tile_size,
        profile == "canonical" and (tile_size, n_codecols) == (3, 3),
        shape_rng,
    )
    first, second = _choose_templates(tile_size, area, shape_rng)

    layout_rng = ctx.draw_rng(
        f"layout|profile={profile}|tile={tile_size}|codecols={n_codecols}"
    )
    height, width = _input_dimensions(profile, tile_size, n_codecols, layout_rng)
    grid = full_grid(height, width, 0)
    _place_templates(grid, first, second, tile_size, layout_rng)
    _place_code_block(grid, n_codecols, layout_rng)

    errors = self_check(
        grid,
        meta={"tile_size": tile_size, "n_codecols": n_codecols},
    )
    if errors:
        raise AssertionError("generated invalid template mosaic: " + "; ".join(errors))
    return grid


def _rotate_grid_cw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _paste(output: Grid, tile: Grid, top: int, left: int) -> None:
    for row, line in enumerate(tile):
        for col, value in enumerate(line):
            if value:
                output[top + row][left + col] = value


def _render_with_decoder(
    grid: Any,
    decoder: Callable[[int, dict[int, Grid]], Grid | None],
) -> Grid:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid template-code input: " + "; ".join(analysis["errors"]))
    tile_size = analysis["tile_size"]
    n_codecols = analysis["n_codecols"]
    output = full_grid(2 * tile_size + 1, n_codecols * tile_size + n_codecols - 1, 0)
    templates = analysis["crops"]
    for row in range(2):
        for col, code in enumerate(analysis["code_block"][row]):
            if code == 0:
                continue
            tile = decoder(code, templates)
            if tile is not None:
                _paste(output, tile, row * (tile_size + 1), col * (tile_size + 1))
    return output


def _canonical_decoder(code: int, templates: dict[int, Grid]) -> Grid | None:
    if code == 1:
        return templates[1]
    if code == 2:
        return templates[2]
    if code == 3:
        return _rotate_grid_cw(templates[1])
    if code == 4:
        return _rotate_grid_cw(templates[2])
    return None


def rule_mirror(grid: Any) -> Grid:
    """Python mirror used only for semantic tests; Racket remains authoritative."""
    return _render_with_decoder(grid, _canonical_decoder)


def _rival_ignore_rotation(grid: Any) -> Grid:
    def decoder(code: int, templates: dict[int, Grid]) -> Grid | None:
        if code in (1, 3):
            return templates[1]
        if code in (2, 4):
            return templates[2]
        return None

    return _render_with_decoder(grid, decoder)


def _rival_swap_template_families(grid: Any) -> Grid:
    def decoder(code: int, templates: dict[int, Grid]) -> Grid | None:
        if code == 1:
            return templates[2]
        if code == 2:
            return templates[1]
        if code == 3:
            return _rotate_grid_cw(templates[2])
        if code == 4:
            return _rotate_grid_cw(templates[1])
        return None

    return _render_with_decoder(grid, decoder)


def _rival_fixed_corner_decode(grid: Any) -> Grid:
    """Wrong shortcut inherited from the old generator's forced corner codes."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid template-code input: " + "; ".join(analysis["errors"]))
    tile_size = analysis["tile_size"]
    n_codecols = analysis["n_codecols"]
    output = full_grid(2 * tile_size + 1, n_codecols * tile_size + n_codecols - 1, 0)
    for row in range(2):
        for col, observed_code in enumerate(analysis["code_block"][row]):
            code = observed_code
            if (row, col) == (0, 0):
                code = 1
            elif (row, col) == (1, n_codecols - 1):
                code = 4
            if code:
                tile = _canonical_decoder(code, analysis["crops"])
                if tile is not None:
                    _paste(output, tile, row * (tile_size + 1), col * (tile_size + 1))
    return output


def _analysis_ok(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _w_rotated_codes_are_observable(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and any(value in (3, 4) for row in analysis["code_block"] for value in row)
        and all(
            _rotate_shape_cw(analysis["shapes"][color]) != analysis["shapes"][color]
            for color in (1, 2)
        )
    )


def _w_template_families_are_observable(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and analysis["shapes"][1] != analysis["shapes"][2]
        and {value for row in analysis["code_block"] for value in row if value} == {1, 2, 3, 4}
    )


def _w_code_positions_are_not_fixed(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and not (
            analysis["code_block"][0][0] == 1
            and analysis["code_block"][1][-1] == 4
        )
    )


SEMANTIC_RIVALS = {
    "ignore_rotation": _rival_ignore_rotation,
    "swap_template_families": _rival_swap_template_families,
    "fixed_corner_decode": _rival_fixed_corner_decode,
}

SEMANTIC_WITNESSES = {
    "rotated_codes_are_observable": _w_rotated_codes_are_observable,
    "template_families_are_observable": _w_template_families_are_observable,
    "code_positions_are_not_fixed": _w_code_positions_are_not_fixed,
}

WITNESS_RIVALS = {
    "rotated_codes_are_observable": ["ignore_rotation"],
    "template_families_are_observable": ["swap_template_families"],
    "code_positions_are_not_fixed": ["fixed_corner_decode"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Verify that a lesson exposes rotation and family decoding without leakage."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    code_layouts: set[tuple[tuple[int, ...], ...]] = set()
    dimensions: set[tuple[int, int]] = set()
    rival_refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        analysis = _analyze(pair["input"])
        if analysis.get("errors"):
            errors.append(f"demo {index} input is malformed: {analysis['errors'][:2]!r}")
            continue
        try:
            actual = _coerce_grid(pair["output"])
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            errors.append(f"demo {index} could not be evaluated: {exc}")
            continue
        if actual != expected:
            errors.append(f"demo {index} output does not follow the template-code rule")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(pair["input"]) != actual:
                rival_refuted[name] = True
        code_layouts.add(tuple(tuple(row) for row in analysis["code_block"]))
        dimensions.add((analysis["height"], analysis["width"]))

    for name, refuted in rival_refuted.items():
        if not refuted:
            errors.append(f"demonstrations do not refute rival {name!r}")
    if len(code_layouts) < 2:
        errors.append("demonstrations repeat too few code layouts")
    if len(dimensions) < 2:
        errors.append("demonstrations vary too little in input size")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    else:
        query_analysis = _analyze(query["input"])
        if query_analysis.get("errors"):
            errors.append("query input is malformed")
    return errors
