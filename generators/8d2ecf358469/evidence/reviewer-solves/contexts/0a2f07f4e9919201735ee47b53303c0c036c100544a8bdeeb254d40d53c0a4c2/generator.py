"""Semantic generator for ARC task ``8d2ecf358469``.

The input contains three mutually separated monochrome components on a zero
background.  The output is a bar chart: one row per component color in
increasing color order, with that row filled from the left for exactly the
component's area.  The output width is the largest component area.

The canonical task has one component per color.  In particular, this generator
does *not* teach the broader "sum all components of the same color" rule that an
older draft claimed: that rule is not identified by the published examples and
is not the selected Racket authority's safe grammar when differently-colored
cells touch.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8d2ecf358469"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "e8095729a5e6"

SUMMARY = (
    "Three separated monochrome components become horizontal bars. Rows are "
    "ordered by increasing component color; each bar length is that component's "
    "cell area, and the output width is the largest area."
)

INVARIANTS = [
    "background is 0 and there are exactly three nonzero colors",
    "each nonzero color forms exactly one 4-connected component",
    "differently-colored components do not touch orthogonally, so the selected Racket rule sees three components",
    "ordinary training draws use three distinct areas drawn from the canonical 2..5 range",
    "output rows are ordered by increasing color, never by component area or input position",
]

# Cycle five authority-safe curriculum signatures.  Two slots have maximum
# area 4, so every six-pair lesson still contains a width-4 witness after any
# single pair is rotated into the query position.  The unscheduled ``2-4-5``
# profile remains accepted as a backward-compatible explicit override.
_AREA_PROFILES: dict[str, tuple[int, int, int]] = {
    "2-3-4": (2, 3, 4),
    "3-2-4": (3, 2, 4),
    "3-4-5": (3, 4, 5),
    "2-4-5": (2, 4, 5),
    "4-3-5": (4, 3, 5),
    "2-5-4": (2, 5, 4),
}
_AREA_BY_SIGNATURE = {areas: name for name, areas in _AREA_PROFILES.items()}
_CANONICAL_AREA_SIGNATURES = set(_AREA_BY_SIGNATURE)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed draw within canonical height envelope",
        "valid": "9..11",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed draw within canonical width envelope",
        "valid": "12..14",
    },
    "area_profile": {
        "type": "str",
        "default": "five-slot deterministic lesson schedule",
        "valid": "2-3-4|3-2-4|3-4-5|2-4-5|4-3-5|2-5-4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 5
SCHEDULE_PROFILES = ("2-3-4", "3-2-4", "3-4-5", "4-3-5", "2-5-4")

# 4-connected shapes, grouped by exact area.  At least one non-solid-bbox
# choice exists for every size >=3, which lets the curriculum refute
# "bounding-box area" without relying on a special texture flag.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ),
}
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_sample_index(sample_index: Any) -> None:
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle the five canonical area signatures in every difficulty band."""
    del seed, difficulty
    _validate_sample_index(sample_index)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    return band


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"grid cells must be integer ARC colors 0..9, found {value!r}"]
    return []


def _components_by_color(grid: Sequence[Sequence[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    """Return 4-connected monochrome components."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((int(color), cells))
    return components


def _colorblind_components(grid: Sequence[Sequence[int]]) -> list[set[tuple[int, int]]]:
    """Return components under the selected Racket rule's nonzero connectivity."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height = len(grid)
    width = len(grid[0])
    components = _components_by_color(grid)
    colors = sorted({color for color, _ in components})
    by_color: dict[int, list[set[tuple[int, int]]]] = {color: [] for color in colors}
    for color, cells in components:
        by_color[color].append(cells)
    colorblind = _colorblind_components(grid)
    areas = tuple(
        sum(len(cells) for cells in by_color[color])
        for color in colors
    )
    area_profile = _AREA_BY_SIGNATURE.get(areas)
    return {
        "errors": [],
        "height": height,
        "width": width,
        "colors": tuple(colors),
        "components": components,
        "by_color": by_color,
        "colorblind_components": colorblind,
        "areas": areas,
        "area_profile": area_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-safe input grammar, including canonical inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    colors = analysis["colors"]
    if len(colors) != 3:
        errors.append(f"expected exactly 3 nonzero colors, got {len(colors)}")
    for color in colors:
        count = len(analysis["by_color"][color])
        if count != 1:
            errors.append(f"color {color} must form exactly one 4-connected component, got {count}")
    # The selected Racket authority floods all nonzero cells irrespective of
    # color.  Distinct colors touching orthogonally would therefore merge and
    # invoke an unintended modal-color branch, so such scenes are not lawful.
    if len(analysis["colorblind_components"]) != len(colors):
        errors.append(
            "differently-colored components must not touch orthogonally; "
            f"found {len(analysis['colorblind_components'])} nonzero components for {len(colors)} colors"
        )

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and name in observed and observed[name] != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed[name]!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the published canonical manifold and the ordinary curriculum."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if not 9 <= analysis["height"] <= 11:
        errors.append(f"height outside canonical 9..11 envelope: {analysis['height']}")
    if not 12 <= analysis["width"] <= 14:
        errors.append(f"width outside canonical 12..14 envelope: {analysis['width']}")
    if analysis["areas"] not in _CANONICAL_AREA_SIGNATURES:
        errors.append(
            "component areas by increasing color must match a canonical signature; "
            f"got {analysis['areas']}"
        )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact generated axis directly from the returned grid."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "area_profile": analysis["area_profile"],
    }


def _shape_dims(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _is_solid_bbox(shape: Sequence[tuple[int, int]]) -> bool:
    height, width = _shape_dims(shape)
    return len(shape) == height * width


def _free(grid: Sequence[Sequence[int]], shape: Sequence[tuple[int, int]], top: int, left: int) -> bool:
    """Require an in-bounds one-cell halo around every new component."""
    height = len(grid)
    width = len(grid[0])
    cells = {(top + dr, left + dc) for dr, dc in shape}
    if any(not (1 <= r < height - 1 and 1 <= c < width - 1) for r, c in cells):
        return False
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 0:
                    return False
    return True


def _place_component(grid, shape, color: int, rng) -> set[tuple[int, int]] | None:
    height, width = len(grid), len(grid[0])
    sh, sw = _shape_dims(shape)
    candidates = [
        (row, col)
        for row in range(1, height - sh)
        for col in range(1, width - sw)
        if _free(grid, shape, row, col)
    ]
    if not candidates:
        return None
    top, left = rng.choice(candidates)
    cells = {(top + dr, left + dc) for dr, dc in shape}
    for row, col in cells:
        grid[row][col] = color
    return cells


def _spatial_color_order(components: list[tuple[int, set[tuple[int, int]]]]) -> tuple[int, ...]:
    return tuple(
        color
        for color, _cells in sorted(
            components,
            key=lambda item: (
                min(r for r, _ in item[1]),
                min(c for _, c in item[1]),
                item[0],
            ),
        )
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_sample_index(sample_index)
    band = _validate_call(difficulty, overrides)
    scheduled_area = overrides.get("area_profile") or schedule_profile(seed, sample_index, band)
    if scheduled_area not in _AREA_PROFILES:
        raise ValueError(f"unknown area_profile: {scheduled_area!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = ctx.draw_int("grid_h", 9, 11)
    width = ctx.draw_int("grid_w", 12, 14)
    # The schedule is part of the pedagogy, so the un-overridden draw is a
    # one-option keyed choice; an explicit override becomes that one option.
    area_name = ctx.draw_choice("area_profile", (scheduled_area,))
    # Color identity is a nuisance variable rather than part of the semantic
    # curriculum.  Keep it richly stochastic, but do not expose it as an
    # override axis: that makes every declared axis exact/observable and avoids
    # an unnecessary Cartesian explosion in the override-contract battery.
    colors = tuple(sorted(ctx.draw_rng("palette").sample(range(1, 10), 3)))
    areas = _AREA_PROFILES[area_name]
    # Difficulty affects only presentation complexity, never the rule or axis
    # domains: hard prefers irregular silhouettes, while easy permits more
    # compact/linear shapes.  Band-specific RNG labels keep replay deterministic
    # while ensuring the public difficulty knob is not dead.
    shape_rng = ctx.draw_rng(f"shape:{band}")
    layout_rng = ctx.draw_rng(f"layout:{band}")

    # Retry complete layouts rather than accepting a failed placement.  Each
    # retry consumes only the task-local deterministic RNG streams.
    for _attempt in range(80):
        grid = full_grid(height, width, 0)
        selected_shapes = []
        for area in areas:
            options = _SHAPES[area]
            if band == "hard" and area >= 3:
                options = tuple(shape for shape in options if not _is_solid_bbox(shape))
            elif band == "easy":
                options = options[: max(1, len(options) // 2)]
            selected_shapes.append(shape_rng.choice(options))
        # Guarantee a bbox-area counterexample on every ordinary draw.
        if all(_is_solid_bbox(shape) for shape in selected_shapes):
            idx = max(range(3), key=lambda i: areas[i])
            irregular = [shape for shape in _SHAPES[areas[idx]] if not _is_solid_bbox(shape)]
            if irregular:
                selected_shapes[idx] = shape_rng.choice(irregular)

        placed: list[tuple[int, set[tuple[int, int]]]] = []
        ok = True
        for color, shape in zip(colors, selected_shapes):
            cells = _place_component(grid, shape, color, layout_rng)
            if cells is None:
                ok = False
                break
            placed.append((color, cells))
        if not ok:
            continue
        # The published examples happen to place components roughly in color
        # order.  Force a counterexample so "read components top-to-bottom" can
        # never masquerade as the intended color-order rule in generated data.
        if _spatial_color_order(placed) == tuple(sorted(colors)):
            continue
        if not self_check(grid):
            return grid
    raise RuntimeError("could not place three separated components after 80 deterministic attempts")


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains the output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    analysis = _analysis(grid)
    colors = analysis["colors"]
    areas = analysis["areas"]
    out_width = max(areas)
    return [
        [color if col < area else 0 for col in range(out_width)]
        for color, area in zip(colors, areas)
    ]


def _bbox_area(cells: set[tuple[int, int]]) -> int:
    return (
        max(r for r, _ in cells) - min(r for r, _ in cells) + 1
    ) * (
        max(c for _, c in cells) - min(c for _, c in cells) + 1
    )


def _rival_rows_by_area(grid):
    analysis = _analysis(grid)
    if analysis.get("errors") or len(analysis.get("colors", ())) != 3:
        return [list(row) for row in grid]
    entries = sorted(zip(analysis["areas"], analysis["colors"]))
    width = max(analysis["areas"])
    return [
        [color if col < area else 0 for col in range(width)]
        for area, color in entries
    ]


def _rival_bbox_area(grid):
    analysis = _analysis(grid)
    if analysis.get("errors") or len(analysis.get("colors", ())) != 3:
        return [list(row) for row in grid]
    by_color = {
        color: cells
        for color, comps in analysis["by_color"].items()
        for cells in comps[:1]
    }
    lengths = tuple(_bbox_area(by_color[color]) for color in analysis["colors"])
    width = max(lengths)
    return [
        [color if col < area else 0 for col in range(width)]
        for color, area in zip(analysis["colors"], lengths)
    ]


def _rival_spatial_order(grid):
    analysis = _analysis(grid)
    if analysis.get("errors") or len(analysis.get("components", ())) != 3:
        return [list(row) for row in grid]
    ordered = sorted(
        analysis["components"],
        key=lambda item: (
            min(r for r, _ in item[1]),
            min(c for _, c in item[1]),
            item[0],
        ),
    )
    width = max(len(cells) for _, cells in ordered)
    return [
        [color if col < len(cells) else 0 for col in range(width)]
        for color, cells in ordered
    ]


def _rival_fixed_width_five(grid):
    official = rule_mirror(grid)
    return [row + [0] * (5 - len(row)) if len(row) < 5 else row[:5] for row in official]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "sort_rows_by_area": _rival_rows_by_area,
    "use_component_bbox_area": _rival_bbox_area,
    "order_rows_by_input_position": _rival_spatial_order,
    "always_use_output_width_5": _rival_fixed_width_five,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _area_order_disagrees_with_color_order(grid) -> bool:
    analysis = _analysis(grid)
    if analysis.get("errors") or len(analysis.get("areas", ())) != 3:
        return False
    return tuple(sorted(analysis["areas"])) != analysis["areas"]


def _bbox_overstates_any_component(grid) -> bool:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return False
    return any(_bbox_area(cells) > len(cells) for _color, cells in analysis["components"])


def _spatial_order_disagrees(grid) -> bool:
    analysis = _analysis(grid)
    if analysis.get("errors") or len(analysis.get("components", ())) != 3:
        return False
    return _spatial_color_order(analysis["components"]) != analysis["colors"]


def _output_width_is_four(grid) -> bool:
    try:
        return len(rule_mirror(grid)[0]) == 4
    except (ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "color_order_not_area_order": _area_order_disagrees_with_color_order,
    "irregular_component_refutes_bbox_area": _bbox_overstates_any_component,
    "color_order_not_spatial_order": _spatial_order_disagrees,
    "output_width_four": _output_width_is_four,
}
WITNESS_RIVALS = {
    "color_order_not_area_order": ["sort_rows_by_area"],
    "irregular_component_refutes_bbox_area": ["use_component_bbox_area"],
    "color_order_not_spatial_order": ["order_rows_by_input_position"],
    "output_width_four": ["always_use_output_width_5"],
}



def mutation_fixtures() -> list[tuple[str, Any]]:
    """Targeted malformed scenes used by focused mutation-sensitivity tests."""
    base = generate(424242, 0, difficulty="medium")
    analysis = _analysis(base)

    blank = full_grid(len(base), len(base[0]), 0)

    dropped = [list(row) for row in base]
    drop_color = analysis["colors"][0]
    for row in range(len(dropped)):
        for col in range(len(dropped[0])):
            if dropped[row][col] == drop_color:
                dropped[row][col] = 0

    split = [list(row) for row in base]
    split_color = analysis["colors"][0]
    split_cells = next(cells for color, cells in analysis["components"] if color == split_color)
    row, col = next(iter(split_cells))
    split[row][col] = 0
    split[0][0] = split_color

    touching = full_grid(9, 12, 0)
    for row, col in ((2, 2), (2, 3)):
        touching[row][col] = 2
    for row, col in ((2, 4), (3, 4), (3, 5)):
        touching[row][col] = 4
    for row, col in ((6, 7), (6, 8), (7, 7), (7, 8)):
        touching[row][col] = 6

    fourth_color = [list(row) for row in base]
    used = set(analysis["colors"])
    extra_color = next(color for color in range(1, 10) if color not in used)
    fourth_color[0][0] = extra_color

    ragged = [list(row) for row in base]
    ragged[-1] = ragged[-1][:-1]

    return [
        ("blank_grid", blank),
        ("missing_color", dropped),
        ("split_same_color_component", split),
        ("touching_different_colors", touching),
        ("unexpected_fourth_color", fourth_color),
        ("ragged_grid", ragged),
    ]

def lesson_identifiable(demos, query) -> list[str]:
    """Require every five-demo sliding lesson to falsify all named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the component-area bar rule")
    try:
        query_expected = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        query_expected = None
    if query_expected is not None and query_expected != query["output"]:
        reasons.append("query disagrees with the component-area bar rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
