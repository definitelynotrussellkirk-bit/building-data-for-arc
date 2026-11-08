"""Generate contour-cell-rank recolouring lessons for task 901c6034f67e.

The selected Racket authority finds monochrome 4-connected objects, counts the
cells on each object's 4-neighbour contour, sorts by that count ascending (then
by top-left position), and recolours the objects 2, 3, 4, ... on a blank grid.

The canonical rectangles make occupied area and bounding-box measurements look
equivalent to contour length.  The default three-slot schedule therefore emits
one canonical-profile anchor, one contour-vs-area inversion, and one
contour-vs-bounding-box inversion.  Any three consecutive default examples
contain all three roles.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "901c6034f67e"
TASK_ID = "901c6034f67e"
VERSION = "3.1.1"
RULE_HASH = "3646fc9eedbe"

SUMMARY = (
    "A 0-background grid contains exactly three monochrome 4-connected "
    "objects with distinct contour-cell counts. A contour cell is "
    "an object cell missing at least one 4-neighbour. Rank objects by contour "
    "length ascending, breaking ties by top-left position, and repaint them on "
    "a blank grid with 2, then 3, then 4. Canonical rectangle profiles are "
    "mixed with area- and bounding-box-inversion scenes so size proxies fail; "
    "non-shared canonical anchors include cross-colour contact so colour-blind "
    "connectivity also fails."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0",
    "exactly three monochrome 4-connected objects; different colors may touch",
    "object contour-cell counts are strictly distinct",
    "output geometry is unchanged and rank depends on contour cells, not area or bbox",
]

PUBLIC_PROFILES = (
    "canonical_train_0",
    "canonical_train_1",
    "canonical_train_2",
    "canonical_test_0",
)
DIAGNOSTIC_PROFILES = ("area_inversion", "bbox_inversion")
SCENE_PROFILES = PUBLIC_PROFILES + DIAGNOSTIC_PROFILES
PALETTE_MODES = ("shared", "distinct", "rank_colors")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled canonical/area-inversion/bbox-inversion profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_mode": {
        "type": "str",
        "default": "scheduled distinct/shared/rank-color input palette",
        "valid": "|".join(PALETTE_MODES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_RANK_COLORS = (2, 3, 4, 6, 7, 8, 9)
_DISTINCT_INPUT_COLORS = (1, 5, 6, 7, 8, 9)
_SHARED_INPUT_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
_TEMP_OBJECT_COLORS = (1, 5, 6)

_PUBLIC_ROWS = {
    "canonical_train_0": (
        "0000008880/0770008880/0770000000/0000000000/"
        "0000999000/0000999000/0000999000/0000000000"
    ),
    "canonical_train_1": (
        "33000000000/33000000000/00000006660/05500006660/"
        "05500006660/05500006660/00000000000"
    ),
    "canonical_train_2": (
        "000000000/000004400/000004400/000088880/000088880/"
        "777088880/777000000/000000000/000000000"
    ),
    "canonical_test_0": (
        "001100000000/001100000000/000000066660/999000066660/"
        "999000066660/000000000000/000000000000/000000000000"
    ),
}

_PROFILE_SCHEDULE = ("canonical", "area_inversion", "bbox_inversion")
_PALETTE_SCHEDULE = ("distinct", "shared", "rank_colors")


def _decode(text: str) -> list[list[int]]:
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in _PUBLIC_ROWS.items()}


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return ["grid dimensions must be between 5 and 30"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colours 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    """Return same-colour 4-connected components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            color = grid[row0][col0]
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(tuple(sorted(cells)))
    return result


def _color_blind_components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    """Return nonzero 4-connected components while deliberately ignoring colour."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(tuple(sorted(cells)))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    row0, col0, row1, col1 = _bbox(cells)
    return (row1 - row0 + 1) * (col1 - col0 + 1)


def _bbox_perimeter(cells: Iterable[tuple[int, int]]) -> int:
    row0, col0, row1, col1 = _bbox(cells)
    return 2 * ((row1 - row0 + 1) + (col1 - col0 + 1))


def _contour_length(cells: Iterable[tuple[int, int]]) -> int:
    """Count object cells with at least one absent 4-neighbour."""
    occupied = set(cells)
    return sum(
        any((row + drow, col + dcol) not in occupied for drow, dcol in _DIR4)
        for row, col in occupied
    )


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = _normalize(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((row, -col) for row, col in current))
        current = _normalize((col, -row) for row, col in current)
    return tuple(sorted(variants))


def _component_signature(cells: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    row0, col0, row1, col1 = _bbox(cells)
    height, width = row1 - row0 + 1, col1 - col0 + 1
    return (
        len(cells),
        _contour_length(cells),
        min(height, width),
        max(height, width),
        height * width - len(cells),
    )


def _linked_signature(grid: list[list[int]]) -> tuple[Any, ...]:
    return (
        len(grid),
        len(grid[0]),
        tuple(sorted(_component_signature(cells) for cells in _components(grid))),
    )


_PUBLIC_SIGNATURES = {
    _linked_signature(grid): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {
            "errors": errors,
            "components": [],
            "contours": [],
            "profile": None,
            "palette_mode": None,
        }

    assert isinstance(grid, list)
    components = _components(grid)
    if 0 not in {value for row in grid for value in row}:
        errors.append("background colour 0 must be present")
    if len(components) != 3:
        errors.append(f"expected exactly three nonzero objects; found {len(components)}")

    sizes = [len(cells) for cells in components]
    if any(size < 3 for size in sizes):
        errors.append(f"every object must contain at least three cells; found {sorted(sizes)}")
    contours = [_contour_length(cells) for cells in components]
    if len(contours) == 3 and len(set(contours)) != 3:
        errors.append(f"object contour lengths must be strictly distinct; found {sorted(contours)}")

    colors = [grid[cells[0][0]][cells[0][1]] for cells in components]
    profile = None
    palette_mode = None
    if not errors:
        signature = _linked_signature(grid)
        profile = _PUBLIC_SIGNATURES.get(signature)
        ranked = sorted(components, key=lambda cells: (_contour_length(cells), min(cells)))
        if profile is None:
            areas = [len(cells) for cells in ranked]
            box_areas = [_bbox_area(cells) for cells in ranked]
            box_perimeters = [_bbox_perimeter(cells) for cells in ranked]
            if areas != sorted(areas):
                profile = "area_inversion"
            elif box_areas != sorted(box_areas) and box_perimeters != sorted(box_perimeters):
                profile = "bbox_inversion"
            else:
                errors.append("grid does not match a declared scene profile")

    if not errors:
        unique = set(colors)
        if len(unique) == 1:
            palette_mode = "shared"
        elif unique == {2, 3, 4}:
            palette_mode = "rank_colors"
        elif len(unique) == 3:
            palette_mode = "distinct"
        else:
            errors.append("object colours do not match a declared palette mode")

    return {
        "errors": errors,
        "components": components,
        "sizes": sizes,
        "contours": contours,
        "colors": colors,
        "profile": profile,
        "palette_mode": palette_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's explicit three-object teaching grammar."""
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "scene_profile": analysis["profile"],
        "palette_mode": analysis["palette_mode"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if analysis["profile"] not in PUBLIC_PROFILES:
        reasons.append("geometry is not one of the four canonical dimension/morphology profiles")
    if analysis["palette_mode"] != "distinct":
        reasons.append("canonical inputs use three distinct object colours")
    return reasons


def canonical_profile_signature(grid):
    return _linked_signature(grid) if not strict_canonical_like(grid) else None


def _ranked_components(grid: list[list[int]]):
    return sorted(_components(grid), key=lambda cells: (_contour_length(cells), min(cells)))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror for tests, witnesses, and lesson diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    for rank, cells in enumerate(_ranked_components(grid)):
        for row, col in cells:
            output[row][col] = _RANK_COLORS[rank]
    return output


def _place_shapes(
    shapes: Iterable[Iterable[tuple[int, int]]],
    height: int,
    width: int,
    rng,
    *,
    require_scan_inversion: bool,
    require_cross_colour_contact: bool = False,
) -> list[list[int]]:
    templates = [tuple(shape) for shape in shapes]
    for _ in range(2048 if require_cross_colour_contact else 512):
        grid = full_grid(height, width, 0)
        used: set[tuple[int, int]] = set()
        order = list(enumerate(templates))
        rng.shuffle(order)
        for shape_index, template in order:
            variants = list(_shape_variants(template))
            rng.shuffle(variants)
            chosen = None
            for shape in variants:
                shape_height = max(row for row, _ in shape) + 1
                shape_width = max(col for _, col in shape) + 1
                positions = [
                    (top, left)
                    for top in range(0, height - shape_height + 1)
                    for left in range(0, width - shape_width + 1)
                ]
                rng.shuffle(positions)
                for top, left in positions:
                    cells = {(top + row, left + col) for row, col in shape}
                    if any(cell in used for cell in cells):
                        continue
                    if not require_cross_colour_contact and any(
                        any((cell[0] + drow, cell[1] + dcol) in used
                            for drow, dcol in _DIR4)
                        for cell in cells
                    ):
                        continue
                    chosen = cells
                    break
                if chosen is not None:
                    break
            if chosen is None:
                break
            color = _TEMP_OBJECT_COLORS[shape_index]
            for row, col in chosen:
                grid[row][col] = color
            used.update(chosen)
        else:
            components = _components(grid)
            if len(components) != 3:
                continue
            if require_cross_colour_contact and len(_color_blind_components(grid)) == 3:
                continue
            if require_scan_inversion:
                scan_contours = [_contour_length(cells) for cells in components]
                if scan_contours == sorted(scan_contours):
                    continue
            return grid
    contact = " touching" if require_cross_colour_contact else " separated"
    raise AssertionError(f"could not place three{contact} diagnostic shapes")

def _public_scene(profile: str, rng, palette_mode: str) -> list[list[int]]:
    source = _PUBLIC_INPUTS[profile]
    shapes = [_normalize(cells) for cells in _components(source)]
    require_contact = palette_mode != "shared"
    grid = _place_shapes(
        shapes,
        len(source),
        len(source[0]),
        rng,
        require_scan_inversion=True,
        require_cross_colour_contact=require_contact,
    )
    if _linked_signature(grid) != _linked_signature(source):
        raise AssertionError("public-profile placement changed canonical morphology")
    return grid


def _band_dimensions(difficulty, rng) -> tuple[int, int]:
    if difficulty == "easy":
        return rng.randint(10, 12), rng.randint(18, 21)
    if difficulty == "hard":
        return rng.randint(15, 19), rng.randint(24, 29)
    return rng.randint(12, 16), rng.randint(20, 25)


def _line(length: int) -> tuple[tuple[int, int], ...]:
    return tuple((0, col) for col in range(length))


def _rectangle(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple((row, col) for row in range(height) for col in range(width))


def _l_shape(span: int) -> tuple[tuple[int, int], ...]:
    return tuple([(row, 0) for row in range(span)] +
                 [(span - 1, col) for col in range(1, span)])


def _area_inversion_shapes(rng, difficulty) -> list[tuple[tuple[int, int], ...]]:
    choices = {
        "easy": ((3, 4), (3, 5)),
        "medium": ((3, 4), (3, 5), (4, 4)),
        "hard": ((3, 5), (4, 4), (4, 5)),
    }.get(difficulty, ((3, 4), (3, 5), (4, 4)))
    height, width = rng.choice(choices)
    dense = _rectangle(height, width)
    dense_contour = _contour_length(dense)
    sparse_size = rng.choice(range(dense_contour + 1, len(dense)))
    sparse = _line(sparse_size)
    small = _line(rng.randint(3, min(6, dense_contour - 1)))
    return [small, dense, sparse]


def _bbox_inversion_shapes(rng, difficulty) -> list[tuple[tuple[int, int], ...]]:
    max_span = {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 5)
    span = rng.randint(4, max_span)
    small = _line(rng.randint(3, min(5, 2 * span - 2)))
    sparse_large_box = _l_shape(span)
    dense_small_box = _rectangle(3, span)
    return [small, sparse_large_box, dense_small_box]


def _diagnostic_scene(profile: str, rng, difficulty) -> list[list[int]]:
    height, width = _band_dimensions(difficulty, rng)
    shapes = (
        _area_inversion_shapes(rng, difficulty)
        if profile == "area_inversion"
        else _bbox_inversion_shapes(rng, difficulty)
    )
    return _place_shapes(shapes, height, width, rng, require_scan_inversion=True)


def _apply_palette_mode(grid: list[list[int]], palette_mode: str, rng) -> list[list[int]]:
    output = [row[:] for row in grid]
    components = _components(output)
    if palette_mode == "rank_colors":
        ranked = sorted(components, key=lambda cells: (_contour_length(cells), min(cells)))
        colors = rng.choice(((3, 4, 2), (4, 2, 3)))
        assignments = zip(ranked, colors)
    else:
        colors = (
            [rng.choice(_SHARED_INPUT_COLORS)] * len(components)
            if palette_mode == "shared"
            else rng.sample(_DISTINCT_INPUT_COLORS, len(components))
        )
        assignments = zip(components, colors)
    for cells, color in assignments:
        for row, col in cells:
            output[row][col] = color
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    schedule_index = (seed + sample_index) % len(_PROFILE_SCHEDULE)
    scheduled_profile = _PROFILE_SCHEDULE[schedule_index]
    if "scene_profile" in overrides:
        profile_options = SCENE_PROFILES
    elif scheduled_profile == "canonical":
        profile_options = PUBLIC_PROFILES
    else:
        profile_options = (scheduled_profile,)
    profile = ctx.draw_choice("scene_profile", profile_options)

    palette_options = PALETTE_MODES if "palette_mode" in overrides else (
        _PALETTE_SCHEDULE[schedule_index],
    )
    palette_mode = ctx.draw_choice("palette_mode", palette_options)
    rng = ctx.draw_rng("scene")

    if profile in PUBLIC_PROFILES:
        grid = _public_scene(profile, rng, palette_mode)
    else:
        grid = _diagnostic_scene(profile, rng, difficulty)
    grid = _apply_palette_mode(grid, palette_mode, ctx.draw_rng("palette"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile, "palette_mode": palette_mode}:
        raise AssertionError(f"generated overrides are not observable: {observed}")
    return grid


def _recolor_by(grid, key: Callable) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    ranked = sorted(analysis["components"], key=lambda cells: (key(cells), min(cells)))
    for rank, cells in enumerate(ranked):
        for row, col in cells:
            output[row][col] = _RANK_COLORS[rank]
    return output


def _competitor_area(grid):
    return _recolor_by(grid, len)


def _competitor_bbox_area(grid):
    return _recolor_by(grid, _bbox_area)


def _competitor_bbox_perimeter(grid):
    return _recolor_by(grid, _bbox_perimeter)


def _competitor_scan_order(grid):
    return _recolor_by(grid, lambda cells: min(cells))


def _competitor_largest_contour_first(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    ranked = sorted(
        analysis["components"],
        key=lambda cells: (-_contour_length(cells), min(cells)),
    )
    for rank, cells in enumerate(ranked):
        for row, col in cells:
            output[row][col] = _RANK_COLORS[rank]
    return output


def _competitor_color_blind_connectivity(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    ranked = sorted(
        _color_blind_components(grid),
        key=lambda cells: (_contour_length(cells), min(cells)),
    )
    for rank, cells in enumerate(ranked):
        for row, col in cells:
            output[row][col] = _RANK_COLORS[rank]
    return output


def _competitor_identity(grid):
    return [row[:] for row in grid]


SEMANTIC_RIVALS = {
    "area": _competitor_area,
    "bbox_area": _competitor_bbox_area,
    "bbox_perimeter": _competitor_bbox_perimeter,
    "scan_order": _competitor_scan_order,
    "largest_contour_first": _competitor_largest_contour_first,
    "color_blind_connectivity": _competitor_color_blind_connectivity,
    "identity": _competitor_identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "area": _competitor_area,
    "bbox_area": _competitor_bbox_area,
    "bbox_perimeter": _competitor_bbox_perimeter,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is outside the teaching grammar: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match contour-rank recolouring")
    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the teaching grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match contour-rank recolouring")
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
            disagrees = competitor(query["input"]) != query_answer
        except Exception as exc:
            reasons.append(f"shortcut {name} failed to execute: {exc}")
            continue
        if fits and disagrees:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _valid(grid) -> bool:
    return not _analysis(grid)["errors"]


def _witness_area_inversion(grid) -> bool:
    if not _valid(grid):
        return False
    ranked = _ranked_components(grid)
    return [len(cells) for cells in ranked] != sorted(map(len, ranked))


def _witness_bbox_area_inversion(grid) -> bool:
    if not _valid(grid):
        return False
    ranked = _ranked_components(grid)
    values = [_bbox_area(cells) for cells in ranked]
    return values != sorted(values)


def _witness_bbox_perimeter_inversion(grid) -> bool:
    if not _valid(grid):
        return False
    ranked = _ranked_components(grid)
    values = [_bbox_perimeter(cells) for cells in ranked]
    return values != sorted(values)


def _witness_scan_inversion(grid) -> bool:
    if not _valid(grid):
        return False
    return _components(grid) != _ranked_components(grid)


def _witness_different_colours_touch(grid) -> bool:
    if not _valid(grid):
        return False
    return len(_color_blind_components(grid)) < len(_components(grid))


def _witness_public_profile(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["scene_profile"] in PUBLIC_PROFILES


def _witness_diagnostic_profile(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["scene_profile"] in DIAGNOSTIC_PROFILES


def _witness_shared_palette(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["palette_mode"] == "shared"


def _witness_distinct_palette(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["palette_mode"] == "distinct"


def _witness_rank_palette(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["palette_mode"] == "rank_colors"


SEMANTIC_WITNESSES = {
    "contour_order_differs_from_area_order": _witness_area_inversion,
    "contour_order_differs_from_bbox_area_order": _witness_bbox_area_inversion,
    "contour_order_differs_from_bbox_perimeter_order": _witness_bbox_perimeter_inversion,
    "contour_order_differs_from_scan_order": _witness_scan_inversion,
    "different_colours_touch": _witness_different_colours_touch,
    "canonical_morphology": _witness_public_profile,
    "diagnostic_morphology": _witness_diagnostic_profile,
    "shared_input_palette": _witness_shared_palette,
    "distinct_input_palette": _witness_distinct_palette,
    "rank_color_input_palette": _witness_rank_palette,
}
WITNESS_RIVALS = {
    "contour_order_differs_from_area_order": ["area"],
    "contour_order_differs_from_bbox_area_order": ["bbox_area"],
    "contour_order_differs_from_bbox_perimeter_order": ["bbox_perimeter"],
    "contour_order_differs_from_scan_order": ["scan_order"],
    "different_colours_touch": ["color_blind_connectivity"],
}
BRANCH_WITNESSES = tuple(
    name for name in SEMANTIC_WITNESSES if name not in WITNESS_RIVALS
)
