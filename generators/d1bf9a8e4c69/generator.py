"""Generator for ``arc_puzzle_bank_fourth21:M25``.

The output rule is shape-agnostic: for every separated nonzero connected
component, erase the component and paint the four corners of its bounding box
in that component's color.  The three canonical examples contain two separated, distinctly colored
components.  The teaching distribution broadens that evidence with L shapes,
zigzags, irregular components, and separated same-color objects so learners
must infer a per-component bounding-box operation rather than a per-color or
shape-template shortcut.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1bf9a8e4c69"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "dc30ef9952c0"

SUMMARY = (
    "For each separated nonzero connected component, erase all of its cells "
    "and paint exactly the four corners of that component's bounding box in "
    "its original color. Components are determined by connectivity rather than "
    "color, including when two separated components deliberately share a color."
)

INVARIANTS = [
    "background is 0; separated objects may deliberately reuse one nonzero color",
    "there are two to four orthogonally separated connected objects",
    "every object spans at least two rows and two columns",
    "the scene contains both a non-corner object cell to erase and an absent bbox corner to add",
    "every two-example lesson contains mixed shapes and a repeated-color pair, refuting shape-only and per-color shortcuts",
]

SHAPE_FAMILIES = ("l_shape", "zigzag", "irregular")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted with a one-in-two canonical-profile anchor",
        "valid": "8..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted with a one-in-two canonical-profile anchor",
        "valid": "9..14",
    },
    "object_count": {
        "type": "int",
        "default": "difficulty-weighted 2..4 with canonical-profile anchors",
        "valid": "2..4",
    },
    "shape_family": {
        "type": "str",
        "default": "sample-index schedule alternating mixed and single-family scenes",
        "valid": "l_shape|zigzag|irregular|mixed",
    },
    "palette_pattern": {
        "type": "str",
        "default": "sample-index schedule alternating distinct and repeat-pair scenes",
        "valid": "distinct|repeat_pair",
    },
}

PALETTE_PATTERNS = ("distinct", "repeat_pair")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Two consecutive examples always include both a mixed-family scene and a
# repeated-color scene.  The runner materializes a lesson with consecutive
# sample indexes, including when lesson starts are strided by the semantic gate.
EXAMPLES_NEEDED = 2
SCHEDULE_PROFILES = (
    "mixed_l_zigzag_distinct",
    "l_shape_repeat_pair",
    "mixed_zigzag_irregular_distinct",
    "irregular_repeat_pair",
)

_PROFILE_SPECS = {
    "mixed_l_zigzag_distinct": ("mixed", "distinct"),
    "l_shape_repeat_pair": ("l_shape", "repeat_pair"),
    "mixed_zigzag_irregular_distinct": ("mixed", "distinct"),
    "irregular_repeat_pair": ("irregular", "repeat_pair"),
}

# The canonical profiles are (height, width, number of foreground objects).
# A scheduled 50% anchor keeps every difficulty band on the canonical scale.
_CANONICAL_PROFILES = (
    (8, 9, 2),
    (8, 10, 2),
    (9, 11, 2),
)
MIN_STRICT_FRAC = 0.20

Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Grid = list[list[int]]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic family schedule profile for one draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[Cell]) -> Shape:
    points = tuple(cells)
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _rotate(cells: Shape) -> Shape:
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _reflect(cells: Shape) -> Shape:
    width = max(c for _, c in cells) + 1
    return _normalize((r, width - 1 - c) for r, c in cells)


def _all_transforms(cells: Iterable[Cell]) -> tuple[Shape, ...]:
    current = _normalize(cells)
    variants: set[Shape] = set()
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


_BASE_SHAPES: dict[str, tuple[Shape, ...]] = {
    "l_shape": (
        _normalize(((0, 0), (1, 0), (1, 1), (1, 2))),
        _normalize(((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))),
    ),
    "zigzag": (
        _normalize(((0, 0), (0, 1), (1, 1), (1, 2))),
        _normalize(((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3))),
    ),
    "irregular": (
        _normalize(((0, 0), (0, 1), (1, 0), (1, 1), (1, 2))),
        _normalize(((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1))),
    ),
}

_FAMILY_VARIANTS: dict[str, tuple[Shape, ...]] = {
    family: tuple(sorted({variant for base in bases for variant in _all_transforms(base)}))
    for family, bases in _BASE_SHAPES.items()
}
_VARIANT_FAMILY = {
    variant: family
    for family, variants in _FAMILY_VARIANTS.items()
    for variant in variants
}


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _shape_is_connected(shape: Shape) -> bool:
    remaining = set(shape)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen = {stack[0]}
    while stack:
        row, col = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (row + dr, col + dc)
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == remaining


def _is_irregular_shape(shape: Shape) -> bool:
    if not _shape_is_connected(shape):
        return False
    bbox_h, bbox_w = _shape_dims(shape)
    if bbox_h < 2 or bbox_w < 2:
        return False
    cell_set = set(shape)
    corners = _bbox_corners(shape)
    return bool(cell_set - corners) and bool(corners - cell_set)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers in 0..9"]
    return []


def _components(grid: Grid) -> list[tuple[int, list[Cell]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[Cell] = set()
    components: list[tuple[int, list[Cell]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_corners(cells: Iterable[Cell]) -> set[Cell]:
    r1, c1, r2, c2 = _bbox(cells)
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _family_of_cells(cells: Iterable[Cell]) -> str | None:
    shape = _normalize(cells)
    known_family = _VARIANT_FAMILY.get(shape)
    if known_family is not None:
        return known_family
    if _is_irregular_shape(shape):
        return "irregular"
    return None


def _palette_pattern(components: Iterable[tuple[int, list[Cell]]]) -> str:
    counts = sorted(Counter(color for color, _ in components).values())
    if counts and all(count == 1 for count in counts):
        return "distinct"
    if counts and counts.count(2) == 1 and all(count in (1, 2) for count in counts):
        return "repeat_pair"
    return "unknown"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes while accepting all canonicals."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    components = _components(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 objects, found {len(components)}")

    palette_pattern = _palette_pattern(components)
    if components and palette_pattern == "unknown":
        errors.append(
            "object colors must be all distinct or contain exactly one repeated pair"
        )

    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if nr < height and nc < width:
                    other = grid[nr][nc]
                    if other != 0 and other != color:
                        errors.append("different-colored objects may not touch orthogonally")
                        break

    saw_noncorner = False
    saw_missing_corner = False
    for color, cells in components:
        r1, c1, r2, c2 = _bbox(cells)
        bbox_h = r2 - r1 + 1
        bbox_w = c2 - c1 + 1
        if bbox_h < 2 or bbox_w < 2:
            errors.append(
                f"color {color} bbox is {bbox_h}x{bbox_w}, expected both axes >=2"
            )
            continue
        corners = _bbox_corners(cells)
        cell_set = set(cells)
        saw_noncorner |= bool(cell_set - corners)
        saw_missing_corner |= bool(corners - cell_set)
        if len(cell_set) == bbox_h * bbox_w:
            errors.append(f"color {color} fills its bbox and hides corner extraction")

    if components and not saw_noncorner:
        errors.append("scene has no non-corner object cell for the rule to erase")
    if components and not saw_missing_corner:
        errors.append("scene has no absent bbox corner for the rule to add")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact canonical dimension/palette profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    components = _components(grid)
    profile = (len(grid), len(grid[0]), len(components))
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the three canonical profiles"]
    if _palette_pattern(components) != "distinct":
        return ["canonical profiles use one distinct color per object"]
    return []


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact declared axis from the returned grid."""
    errors = self_check(grid)
    if errors:
        return {
            "grid_h": None,
            "grid_w": None,
            "object_count": None,
            "shape_family": None,
            "palette_pattern": None,
        }
    components = _components(grid)
    families = {_family_of_cells(cells) for _, cells in components}
    if None in families:
        shape_family: object = "unknown"
    elif len(families) == 1:
        shape_family = next(iter(families))
    else:
        shape_family = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_count": len(components),
        "shape_family": shape_family,
        "palette_pattern": _palette_pattern(components),
    }


def _weighted_options(full: range, preferred: range, repeats: int = 4) -> tuple[int, ...]:
    return tuple(preferred) * repeats + tuple(full)


def _draw_axes(ctx, seed: int, sample_index: int, difficulty, overrides):
    exact_dim_override = any(
        key in overrides and overrides[key] is not None
        for key in ("grid_h", "grid_w", "object_count")
    )
    if not exact_dim_override and sample_index % 2 == 0:
        profile = _CANONICAL_PROFILES[(seed + sample_index // 2) % len(_CANONICAL_PROFILES)]
        height = ctx.draw_choice("grid_h", (profile[0],))
        width = ctx.draw_choice("grid_w", (profile[1],))
        object_count = ctx.draw_choice("object_count", (profile[2],))
    else:
        if difficulty == "easy":
            preferred_h, preferred_w, preferred_n = range(8, 10), range(9, 11), range(2, 3)
        elif difficulty == "hard":
            preferred_h, preferred_w, preferred_n = range(10, 14), range(11, 15), range(3, 5)
        else:
            preferred_h, preferred_w, preferred_n = range(8, 12), range(9, 13), range(2, 4)
        height = ctx.draw_choice("grid_h", _weighted_options(range(8, 14), preferred_h))
        width = ctx.draw_choice("grid_w", _weighted_options(range(9, 15), preferred_w))
        object_count = ctx.draw_choice(
            "object_count", _weighted_options(range(2, 5), preferred_n, repeats=5)
        )

    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_shape_family, scheduled_palette_pattern = _PROFILE_SPECS[profile]

    if "shape_family" in overrides and overrides["shape_family"] is not None:
        shape_family = ctx.draw_choice("shape_family", SHAPE_FAMILIES + ("mixed",))
    else:
        shape_family = ctx.draw_choice("shape_family", (scheduled_shape_family,))

    if "palette_pattern" in overrides and overrides["palette_pattern"] is not None:
        palette_pattern = ctx.draw_choice("palette_pattern", PALETTE_PATTERNS)
    else:
        palette_pattern = ctx.draw_choice(
            "palette_pattern", (scheduled_palette_pattern,)
        )
    return height, width, object_count, shape_family, palette_pattern, profile


def _families_for_scene(
    shape_family: str, profile: str, object_count: int, seed: int, sample_index: int
) -> list[str]:
    if shape_family != "mixed":
        return [shape_family] * object_count
    if profile.startswith("mixed_l_zigzag"):
        cycle = ("l_shape", "zigzag", "irregular")
    elif profile.startswith("mixed_zigzag_irregular"):
        cycle = ("zigzag", "irregular", "l_shape")
    else:
        offset = (seed + sample_index) % len(SHAPE_FAMILIES)
        cycle = SHAPE_FAMILIES[offset:] + SHAPE_FAMILIES[:offset]
    return [cycle[index % len(cycle)] for index in range(object_count)]


def _slots(height: int, width: int, object_count: int) -> list[tuple[int, int, int, int]]:
    if object_count == 2:
        gap_col = width // 2
        return [(0, height, 0, gap_col), (0, height, gap_col + 1, width)]
    gap_row = height // 2
    gap_col = width // 2
    slots = [
        (0, gap_row, 0, gap_col),
        (0, gap_row, gap_col + 1, width),
        (gap_row + 1, height, 0, gap_col),
        (gap_row + 1, height, gap_col + 1, width),
    ]
    return slots[:object_count]


def _grow_irregular_shape(slot_h: int, slot_w: int, rng) -> Shape:
    """Grow a connected non-template polyomino that exposes bbox semantics."""
    for _ in range(128):
        bbox_h = rng.randint(2, min(slot_h, 6))
        bbox_w = rng.randint(2, min(slot_w, 7))
        area = bbox_h * bbox_w
        min_size = min(area - 1, max(5, max(bbox_h, bbox_w) + 1))
        max_size = min(area - 1, max(min_size, min(14, (area + 2) // 2 + 4)))
        if max_size < min_size:
            continue

        target_size = rng.randint(min_size, max_size)
        cells = {(rng.randrange(bbox_h), rng.randrange(bbox_w))}
        while len(cells) < target_size:
            frontier: set[Cell] = set()
            for row, col in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (row + dr, col + dc)
                    if (
                        0 <= neighbor[0] < bbox_h
                        and 0 <= neighbor[1] < bbox_w
                        and neighbor not in cells
                    ):
                        frontier.add(neighbor)
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))

        shape = _normalize(cells)
        if _VARIANT_FAMILY.get(shape) in ("l_shape", "zigzag"):
            continue
        if _is_irregular_shape(shape):
            return shape

    fitting = [
        shape
        for shape in _FAMILY_VARIANTS["irregular"]
        if _shape_dims(shape)[0] <= slot_h and _shape_dims(shape)[1] <= slot_w
    ]
    if not fitting:
        raise ValueError(f"no irregular shape fits a {slot_h}x{slot_w} slot")
    return rng.choice(fitting)


def _pick_shape(family: str, slot_h: int, slot_w: int, rng) -> Shape:
    if family == "irregular":
        return _grow_irregular_shape(slot_h, slot_w, rng)
    fitting = [
        shape
        for shape in _FAMILY_VARIANTS[family]
        if _shape_dims(shape)[0] <= slot_h and _shape_dims(shape)[1] <= slot_w
    ]
    if not fitting:
        raise ValueError(f"no {family} shape fits a {slot_h}x{slot_w} slot")
    return rng.choice(fitting)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; the Racket rule owns outputs."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, object_count, shape_family, palette_pattern, profile = _draw_axes(
        ctx, seed, sample_index, difficulty, overrides
    )
    if palette_pattern == "distinct":
        colors = list(ctx.draw_distinct_colors("colors", n=object_count, exclude={0}))
    else:
        colors = list(
            ctx.draw_distinct_colors("colors", n=object_count - 1, exclude={0})
        )
        palette_rng = ctx.draw_rng("palette_layout")
        colors.append(palette_rng.choice(colors))
        palette_rng.shuffle(colors)
    families = _families_for_scene(shape_family, profile, object_count, seed, sample_index)
    slots = _slots(height, width, object_count)
    rng = ctx.draw_rng("layout")
    rng.shuffle(slots)

    grid = full_grid(height, width, 0)
    for color, family, (r0, r1, c0, c1) in zip(colors, families, slots, strict=True):
        slot_h, slot_w = r1 - r0, c1 - c0
        shape = _pick_shape(family, slot_h, slot_w, rng)
        shape_h, shape_w = _shape_dims(shape)
        top = rng.randint(r0, r1 - shape_h)
        left = rng.randint(c0, c1 - shape_w)
        for dr, dc in shape:
            grid[top + dr][left + dc] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid bbox-corner scene: {errors}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract and plausible wrong rules
# ---------------------------------------------------------------------------


def rule_mirror(grid: Grid) -> Grid:
    """Python test mirror only; generation never uses this as output authority."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        for row, col in _bbox_corners(cells):
            out[row][col] = color
    return out


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _keep_existing_corners(grid: Grid) -> Grid:
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        cell_set = set(cells)
        for row, col in _bbox_corners(cells) & cell_set:
            out[row][col] = color
    return out


def _bbox_outline(grid: Grid) -> Grid:
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        for col in range(c1, c2 + 1):
            out[r1][col] = color
            out[r2][col] = color
        for row in range(r1, r2 + 1):
            out[row][c1] = color
            out[row][c2] = color
    return out


def _solid_bbox(grid: Grid) -> Grid:
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                out[row][col] = color
    return out


def _per_color_bbox(grid: Grid) -> Grid:
    """Wrong rival: merge disconnected objects whenever their colors match."""
    out = full_grid(len(grid), len(grid[0]), 0)
    cells_by_color: dict[int, list[Cell]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                cells_by_color[color].append((row, col))
    for color, cells in cells_by_color.items():
        for row, col in _bbox_corners(cells):
            out[row][col] = color
    return out


def _l_shapes_only(grid: Grid) -> Grid:
    """Wrong rival: apply bbox corners only to recognizable L objects."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        if _family_of_cells(cells) == "l_shape":
            for row, col in _bbox_corners(cells):
                out[row][col] = color
        else:
            for row, col in cells:
                out[row][col] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _identity,
    "keep_existing_corners": _keep_existing_corners,
    "bbox_outline": _bbox_outline,
    "solid_bbox": _solid_bbox,
    "l_shapes_only": _l_shapes_only,
    "per_color_bbox": _per_color_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"per_color_bbox": _per_color_bbox}


def _has_missing_corner(grid: Grid) -> bool:
    return any(_bbox_corners(cells) - set(cells) for _, cells in _components(grid))


def _has_noncorner_cell(grid: Grid) -> bool:
    return any(set(cells) - _bbox_corners(cells) for _, cells in _components(grid))


def _has_repeated_color_components(grid: Grid) -> bool:
    return _palette_pattern(_components(grid)) == "repeat_pair"


def _has_family(name: str) -> Callable[[Grid], bool]:
    return lambda grid: any(_family_of_cells(cells) == name for _, cells in _components(grid))


def _perimeter_exceeds_corners(grid: Grid) -> bool:
    return any(
        2 * ((r2 - r1 + 1) + (c2 - c1 + 1)) - 4 > 4
        for _, cells in _components(grid)
        for r1, c1, r2, c2 in (_bbox(cells),)
    )


SEMANTIC_WITNESSES = {
    "absent_bbox_corner_must_be_added": _has_missing_corner,
    "noncorner_object_cells_must_be_erased": _has_noncorner_cell,
    "bbox_perimeter_is_not_the_answer": _perimeter_exceeds_corners,
    "l_shape_branch": _has_family("l_shape"),
    "zigzag_branch": _has_family("zigzag"),
    "irregular_branch": _has_family("irregular"),
    "separated_same_color_objects": _has_repeated_color_components,
}
WITNESS_RIVALS = {
    "absent_bbox_corner_must_be_added": ["identity", "keep_existing_corners"],
    "noncorner_object_cells_must_be_erased": ["identity"],
    "bbox_perimeter_is_not_the_answer": ["bbox_outline", "solid_bbox"],
    "l_shape_branch": ["identity", "keep_existing_corners"],
    "zigzag_branch": ["l_shapes_only"],
    "irregular_branch": ["l_shapes_only"],
    "separated_same_color_objects": ["per_color_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require consecutive demos to eliminate every named plausible shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the bbox-corner teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the bbox-corner teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the exact bbox-corner transformation")
            continue
        valid_demos.append(demo)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
