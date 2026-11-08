"""Generator for 18b:m125 — recolor nonzero components by ascending area rank.

The canonical task has two or three 4-connected nonzero components with
strictly distinct cell counts.  The input component colours are irrelevant;
the output is a fresh 0-background grid where the smallest component is 2,
the next is 3, and (when present) the largest is 4.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "996fc37f49d9"
TASK_ID = "996fc37f49d9"
VERSION = "2.1.0"
RULE_HASH = "b8683f5eb534"

SUMMARY = (
    "A 0-background grid contains either two or three separated, monochrome, "
    "4-connected components with strictly distinct cell counts. Rank all "
    "nonzero components by ascending area and repaint them on a blank grid: "
    "smallest to 2, next to 3, and (for three-component scenes) largest to 4. "
    "Input colour, position, and shape do not determine the rank."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

INVARIANTS = [
    "background is 0 and input cells never use output-rank colours 2, 3, or 4",
    "there are exactly two or three separated 4-connected nonzero components",
    "each component is monochrome and contains at least three cells",
    "component cell counts are strictly distinct, so ascending-area rank is unique",
    "the output preserves component geometry and depends only on area rank",
]

PUBLIC_PROFILES = (
    "canonical_train_0",
    "canonical_train_1",
    "canonical_train_2",
    "canonical_train_3",
    "canonical_test_0",
)
GENERAL_PROFILES = ("general_2", "general_3")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
COLOR_MODES = ("canonical7", "monochrome_other", "component_colors")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled canonical/general profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "color_mode": {
        "type": "str",
        "default": "scheduled monochrome/multicolour mode",
        "valid": "|".join(COLOR_MODES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_INPUT_COLORS = (1, 5, 6, 7, 8, 9)

# Exact public inputs, retained as canonical anchors.  The default schedule also
# emits generalized scenes, so these are a prior rather than the whole corpus.
_PUBLIC_ROWS = {
    "canonical_train_0": (
        "000000000000/077000070000/077000070000/000000077700/000000000000/"
        "000777000000/000700000000/000700000000/000777000000/000000000000"
    ),
    "canonical_train_1": (
        "00000000000/00000000000/07770000000/00000000000/00000077000/"
        "00000077000/00700070000/00700000000/00700000000/00777000000/"
        "00000000000"
    ),
    "canonical_train_2": (
        "000000000000/000000007700/000000007700/000000000000/070700000000/"
        "070700000000/077700777000/000000700000/000000700000/000000777000/"
        "000000000000/000000000000"
    ),
    "canonical_train_3": (
        "0000000000000/0000000000000/0007000000000/0077700000000/"
        "0007000000000/0000077700000/0000070000770/0000070000770/"
        "0000077700000/0000000000000"
    ),
    "canonical_test_0": (
        "000000000000/000000000000/000000077000/000000007000/"
        "000000007700/007000000000/007000000000/007000000000/"
        "077770000000/000000000000/000000000000"
    ),
}


def _decode(text: str) -> list[list[int]]:
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in _PUBLIC_ROWS.items()}

# Half the samples retain canonical morphology. A monochrome diagnostic scene
# appears every third index, with inverted box order and non-ascending scan
# order; any three consecutive default demonstrations refute all declared
# rivals. Two unrestricted slots retain ordinary geometry and fully independent
# per-component palettes. Overrides deliberately opt out of this lesson schedule.
_PROFILE_SCHEDULE = (
    "canonical_train", "general_3", "canonical_test_0", "general_2",
    "general_2", "canonical_train", "canonical_test_0", "general_3",
    "general_3", "canonical_train", "general_2", "canonical_test_0",
)
_COLOR_SCHEDULE = (
    "canonical7", "monochrome_other", "canonical7", "component_colors",
    "canonical7", "canonical7", "canonical7", "monochrome_other",
    "component_colors", "canonical7", "monochrome_other", "canonical7",
)
_DIAGNOSTIC_SLOTS = frozenset((1, 4, 7, 10))


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["grid dimensions must be between 7 and 30"]
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


def _component_signature(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    row0, col0, row1, col1 = _bbox(cells)
    height, width = row1 - row0 + 1, col1 - col0 + 1
    return len(cells), min(height, width), max(height, width), height * width - len(cells)


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
        return {"errors": errors, "components": [], "profile": None, "color_mode": None}

    assert isinstance(grid, list)
    components = _components(grid)
    if 0 not in {value for row in grid for value in row}:
        errors.append("background colour 0 must be present")
    forbidden = sorted({value for row in grid for value in row if value in (2, 3, 4)})
    if forbidden:
        errors.append(f"input uses output-rank colour(s): {forbidden}")
    if len(components) not in (2, 3):
        errors.append(f"expected exactly two or three nonzero components; found {len(components)}")

    sizes = [len(cells) for cells in components]
    if any(size < 3 for size in sizes):
        errors.append(f"every component must have at least three cells; found {sorted(sizes)}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"component cell counts must be strictly distinct; found {sorted(sizes)}")

    component_colors: list[int] = []
    for index, cells in enumerate(components):
        colors = {grid[row][col] for row, col in cells}
        if len(colors) != 1:
            errors.append(f"component {index} must be monochrome; found {sorted(colors)}")
        elif colors:
            component_colors.append(next(iter(colors)))

    profile = None
    if not errors:
        signature = _linked_signature(grid)
        profile = _PUBLIC_SIGNATURES.get(signature)
        if profile is None and 13 <= len(grid) <= 24 and 13 <= len(grid[0]) <= 24:
            profile = f"general_{len(components)}"
        if profile is None:
            errors.append("grid does not match a declared scene profile")

    color_mode = None
    if not errors:
        unique = set(component_colors)
        if unique == {7}:
            color_mode = "canonical7"
        elif len(unique) == 1:
            color_mode = "monochrome_other"
        elif len(unique) == len(components):
            color_mode = "component_colors"
        else:
            errors.append("component colours do not match a declared colour mode")

    return {
        "errors": errors,
        "components": components,
        "sizes": sizes,
        "component_colors": component_colors,
        "profile": profile,
        "color_mode": color_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural teaching-grammar check; accepts every canonical input."""
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "scene_profile": analysis["profile"],
        "color_mode": analysis["color_mode"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if analysis["color_mode"] != "canonical7":
        reasons.append("canonical inputs use one shared foreground colour 7")
    if _linked_signature(grid) not in _PUBLIC_SIGNATURES:
        reasons.append("linked dimensions and component morphology are not a canonical profile")
    height, width = len(grid), len(grid[0])
    if any(
        row in (0, height - 1) or col in (0, width - 1)
        for cells in analysis["components"]
        for row, col in cells
    ):
        reasons.append("canonical components retain a one-cell border margin")
    return reasons


def canonical_profile_signature(grid):
    return _linked_signature(grid) if not strict_canonical_like(grid) else None


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror used only for tests and lesson diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    for rank, cells in enumerate(sorted(analysis["components"], key=len)):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _flip_h(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_v(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in reversed(grid)]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _public_scene(profile: str, rng) -> list[list[int]]:
    source = _PUBLIC_INPUTS[profile]
    height, width = len(source), len(source[0])
    templates = [_normalize(cells) for cells in _components(source)]
    for _ in range(512):
        grid = full_grid(height, width, 0)
        used: set[tuple[int, int]] = set()
        order = list(range(len(templates)))
        rng.shuffle(order)
        placed = True
        for index in order:
            variants = list(_shape_variants(templates[index]))
            rng.shuffle(variants)
            chosen = None
            for shape in variants:
                shape_height = max(row for row, _ in shape) + 1
                shape_width = max(col for _, col in shape) + 1
                positions = [
                    (top, left)
                    for top in range(1, height - shape_height)
                    for left in range(1, width - shape_width)
                ]
                rng.shuffle(positions)
                for top, left in positions:
                    cells = {(top + row, left + col) for row, col in shape}
                    if any(
                        cell in used
                        or any((cell[0] + drow, cell[1] + dcol) in used for drow, dcol in _DIR4)
                        for cell in cells
                    ):
                        continue
                    chosen = cells
                    break
                if chosen is not None:
                    break
            if chosen is None:
                placed = False
                break
            for row, col in chosen:
                grid[row][col] = 7
            used.update(chosen)
        if placed and _linked_signature(grid) == _linked_signature(source):
            return grid
    raise AssertionError(f"could not place canonical profile {profile}")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    base = _normalize(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = base
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((row, -col) for row, col in current))
        current = _normalize((col, -row) for row, col in current)
    return tuple(sorted(variants))


def _random_shape(rng, size: int, max_height: int = 6, max_width: int = 6):
    """Grow exactly ``size`` connected cells with a finite frontier.

    Confining the frontier replaces the old rejection of overlarge random walks;
    every loop adds a new cell and no retry budget depends on the target size.
    """
    if not 1 <= size <= max_height * max_width:
        raise ValueError("shape size must fit its growth box")
    cells = {(rng.randrange(max_height), rng.randrange(max_width))}
    while len(cells) < size:
        frontier = {
            (row + dr, col + dc)
            for row, col in cells for dr, dc in _DIR4
            if 0 <= row + dr < max_height and 0 <= col + dc < max_width
            and (row + dr, col + dc) not in cells
        }
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def _box_area(cells: Iterable[tuple[int, int]]) -> int:
    row0, col0, row1, col1 = _bbox(cells)
    return (row1 - row0 + 1) * (col1 - col0 + 1)


def _compact_shape(size: int) -> tuple[tuple[int, int], ...]:
    width = next(w for w in range(1, size + 1) if w * w >= size)
    return tuple((index // width, index % width) for index in range(size))


def _bbox_counterexample_shapes(rng):
    """A sparse small L and a denser larger shape, with strictly reversed boxes.

    There are many areas/orientations/positions, not one memorized negative.
    The unrestricted half of generalized scenes prevents teaching an inverse-
    bounding-box heuristic instead of the intended cell-count comparison.
    """
    small_size = rng.randint(5, 13)
    height = (small_size + 1) // 2
    width = small_size + 1 - height
    sparse = tuple([(row, 0) for row in range(height)] +
                   [(height - 1, col) for col in range(1, width)])
    larger_sizes = [size for size in range(small_size + 1, min(18, small_size + 4) + 1)
                    if _box_area(_compact_shape(size)) < _box_area(sparse)]
    dense = _compact_shape(rng.choice(larger_sizes))
    return [sparse, dense]


def _place_general_shapes(shapes, height, width, rng, *, require_scan_inversion=False):
    # No rank-to-quadrant mapping: shuffle the objects, try arbitrary positions,
    # and admit edge-touching objects without clipping or merging components.
    for _ in range(128):
        grid = full_grid(height, width, 0)
        used: set[tuple[int, int]] = set()
        order = list(shapes)
        rng.shuffle(order)
        margin = rng.randrange(2)
        for template in order:
            shape = rng.choice(_shape_variants(template))
            shape_height = max(row for row, _ in shape) + 1
            shape_width = max(col for _, col in shape) + 1
            positions = [(row, col)
                         for row in range(margin, height - shape_height - margin + 1)
                         for col in range(margin, width - shape_width - margin + 1)]
            rng.shuffle(positions)
            chosen = None
            for top, left in positions:
                cells = {(top + row, left + col) for row, col in shape}
                if any(cell in used or any((cell[0] + dr, cell[1] + dc) in used
                                           for dr, dc in _DIR4) for cell in cells):
                    continue
                chosen = cells
                break
            if chosen is None:
                break
            used.update(chosen)
            for row, col in chosen:
                grid[row][col] = 7
        else:
            scan_sizes = [len(cells) for cells in _components(grid)]
            if not require_scan_inversion or scan_sizes != sorted(scan_sizes):
                return grid
    raise AssertionError("could not place generalized components in 128 attempts")


def _general_scene(profile: str, rng, *, diagnostic=False) -> list[list[int]]:
    count = 2 if profile == "general_2" else 3
    height, width = rng.randint(13, 24), rng.randint(13, 24)
    if diagnostic or rng.randrange(2) == 0:
        shapes = _bbox_counterexample_shapes(rng)
        if count == 3:
            used_sizes = {len(shape) for shape in shapes}
            size = rng.choice([n for n in range(3, 19) if n not in used_sizes])
            shapes.append(_random_shape(rng, size))
    else:
        sizes = rng.sample(range(3, 19), count)
        shapes = [_random_shape(rng, size) for size in sizes]
    return _place_general_shapes(shapes, height, width, rng,
                                 require_scan_inversion=diagnostic)


def _apply_color_mode(grid: list[list[int]], color_mode: str, rng) -> list[list[int]]:
    output = [row[:] for row in grid]
    components = sorted(_components(output), key=len)
    if color_mode == "canonical7":
        colors = [7] * len(components)
    elif color_mode == "monochrome_other":
        colors = [rng.choice((1, 5, 6, 8, 9))] * len(components)
    else:
        # Each input colour can occupy each area rank, including rank orders
        # that agree with or contradict numeric colour order.
        colors = rng.sample(_INPUT_COLORS, len(components))
    for cells, color in zip(components, colors):
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
    if "scene_profile" in overrides:
        profile_options = SCENE_PROFILES
    elif _PROFILE_SCHEDULE[schedule_index] == "canonical_train":
        profile_options = PUBLIC_PROFILES[:-1]
    else:
        profile_options = (_PROFILE_SCHEDULE[schedule_index],)
    if "color_mode" in overrides:
        color_options = COLOR_MODES
    elif _COLOR_SCHEDULE[schedule_index] == "mixed_noncanonical":
        color_options = ("component_colors", "monochrome_other")
    else:
        color_options = (_COLOR_SCHEDULE[schedule_index],)
    profile = ctx.draw_choice("scene_profile", profile_options)
    color_mode = ctx.draw_choice("color_mode", color_options)
    rng = ctx.draw_rng("scene")

    if profile in PUBLIC_PROFILES:
        grid = _public_scene(profile, rng)
    else:
        grid = _general_scene(
            profile, rng,
            diagnostic="scene_profile" not in overrides and schedule_index in _DIAGNOSTIC_SLOTS,
        )
    band_index = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    transform_code = (ctx.draw_rng("band_transform").randrange(4) + band_index) % 4
    if transform_code & 1:
        grid = _flip_h(grid)
    if transform_code & 2:
        grid = _flip_v(grid)
    if "scene_profile" not in overrides and schedule_index in _DIAGNOSTIC_SLOTS:
        if [len(cells) for cells in _components(grid)] == sorted(map(len, _components(grid))):
            # Reflections preserve the bbox witness. The pre-transform scene
            # is among these four and placement guaranteed its scan inversion.
            variants = (grid, _flip_h(grid), _flip_v(grid), _flip_v(_flip_h(grid)))
            grid = next(candidate for candidate in variants
                        if [len(cells) for cells in _components(candidate)] !=
                        sorted(map(len, _components(candidate))))
    grid = _apply_color_mode(grid, color_mode, ctx.draw_rng("colors"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def _witness_two_components(grid) -> bool:
    return not _analysis(grid)["errors"] and len(_components(grid)) == 2


def _witness_three_components(grid) -> bool:
    return not _analysis(grid)["errors"] and len(_components(grid)) == 3


def _witness_canonical_monochrome(grid) -> bool:
    return not _analysis(grid)["errors"] and observe_overrides(grid)["color_mode"] == "canonical7"


def _witness_other_monochrome(grid) -> bool:
    return not _analysis(grid)["errors"] and observe_overrides(grid)["color_mode"] == "monochrome_other"


def _witness_component_colors(grid) -> bool:
    return not _analysis(grid)["errors"] and observe_overrides(grid)["color_mode"] == "component_colors"


def _witness_area_not_scan_order(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    scan = sorted(analysis["components"], key=lambda cells: min(cells))
    return [len(cells) for cells in scan] != sorted(analysis["sizes"])


def _witness_canonical_morphology(grid) -> bool:
    return not _analysis(grid)["errors"] and _linked_signature(grid) in _PUBLIC_SIGNATURES


def _witness_generalized_morphology(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["profile"] in GENERAL_PROFILES


def _witness_bbox_inversion(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    boxes = [_box_area(cells) for cells in sorted(analysis["components"], key=len)]
    return boxes != sorted(boxes)


SEMANTIC_WITNESSES = {
    "two_components": _witness_two_components,
    "three_components": _witness_three_components,
    "canonical_colour_7": _witness_canonical_monochrome,
    "other_monochrome_colour": _witness_other_monochrome,
    "distinct_component_colours": _witness_component_colors,
    "area_order_differs_from_scan_order": _witness_area_not_scan_order,
    "canonical_linked_morphology": _witness_canonical_morphology,
    "generalized_linked_morphology": _witness_generalized_morphology,
    "bounding_box_order_differs_from_area_order": _witness_bbox_inversion,
}


def _competitor_scan_order(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = full_grid(len(grid), len(grid[0]), 0)
    for rank, cells in enumerate(sorted(analysis["components"], key=lambda cells: min(cells))):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_largest_first(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = full_grid(len(grid), len(grid[0]), 0)
    for rank, cells in enumerate(sorted(analysis["components"], key=len, reverse=True)):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_numeric_input_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    ordered = sorted(
        analysis["components"],
        key=lambda cells: (grid[cells[0][0]][cells[0][1]], min(cells)),
    )
    output = full_grid(len(grid), len(grid[0]), 0)
    for rank, cells in enumerate(ordered):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_bounding_box(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = full_grid(len(grid), len(grid[0]), 0)
    ordered = sorted(analysis["components"], key=lambda cells: (_box_area(cells), min(cells)))
    for rank, cells in enumerate(ordered):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_identity(grid):
    return [row[:] for row in grid]


_LESSON_COMPETITORS = {
    "rank by bounding-box area rather than occupied cells": _competitor_bounding_box,
    "rank by top-left scan order": _competitor_scan_order,
    "rank by descending rather than ascending area": _competitor_largest_first,
    "rank by numeric input colour": _competitor_numeric_input_color,
    "leave the input unchanged": _competitor_identity,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is outside the teaching grammar: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match ascending-area recolouring")
    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the teaching grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match ascending-area recolouring")
    for name, competitor in _LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query_answer:
                reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


# Feature-presence witnesses are branch coverage. Only the two order witnesses
# claim rival disagreement, and the semantic gate checks them against Racket.
SEMANTIC_RIVALS = {
    "bounding_box": _competitor_bounding_box,
    "scan_order": _competitor_scan_order,
}
WITNESS_RIVALS = {
    "bounding_box_order_differs_from_area_order": ["bounding_box"],
    "area_order_differs_from_scan_order": ["scan_order"],
}
BRANCH_WITNESSES = tuple(name for name in SEMANTIC_WITNESSES if name not in WITNESS_RIVALS)
LESSON_COMPETITORS = dict(_LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = {"bounding_box": _competitor_bounding_box}
