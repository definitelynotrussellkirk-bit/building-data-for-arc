"""Semantic curriculum for task 8a2e39528187: recolor objects by area rank.

The selected Racket authority finds monochromatic 4-connected nonzero objects,
sorts them by ``(cell_count, bounding_box)`` ascending, and repaints the first
four objects red/yellow/magenta/cyan (2/4/6/8) on a blank background.

The four-example schedule deliberately exposes two details missing from the
imported sampler: differently colored objects may touch, and equal-area objects
are ordered by bounding box.  It also breaks scan-order and input-palette
shortcuts while staying inside the canonical 9-10 by 10-12 envelope.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a2e39528187"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "76fcc8e7f591"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background 9-10 by 10-12 grid contains exactly four distinct-colored "
    "monochromatic 4-connected objects. Sort objects by cell count ascending, "
    "breaking equal-area ties by lexicographic bounding box, then repaint their "
    "unchanged cells 2, 4, 6, and 8 on a blank grid. Different input colors may "
    "touch; color, scan order, and the numeric input palette are distractors."
)

INVARIANTS = [
    "background is color 0 and the grid is 9..10 rows by 10..12 columns",
    "exactly four monochromatic 4-connected nonzero objects use distinct colors",
    "areas are either 2/3/4/5 or the canonical tied profile 2/2/4/5",
    "different-colored objects may touch and remain separate objects",
    "rank order is (cell count, lexicographic bounding box) ascending",
    "rank colors are exactly 2, 4, 6, 8 and object geometry is preserved",
]

SCHEDULE_PROFILES = (
    "canonical_strict",
    "tie_break",
    "touching_colors",
    "rank_palette",
)

AXES = {
    "grid_h": {"type": "int", "default": "uniform 9..10", "valid": "9..10"},
    "grid_w": {"type": "int", "default": "uniform 10..12", "valid": "10..12"},
    "lesson_profile": {
        "type": "str",
        "default": "four-slot cyclic semantic schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_RANK_PALETTE = (2, 4, 6, 8)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_SIZE_PROFILES = {(2, 3, 4, 5), (2, 2, 4, 5)}
_NON_RANK_COLORS = (1, 3, 5, 7, 9)
_RANK_DERANGEMENTS = (
    (4, 2, 8, 6),
    (6, 8, 2, 4),
    (8, 6, 4, 2),
    (4, 6, 8, 2),
)

# Compact bases; all dihedral transforms fit in one 3x3 placement slot.
_SHAPE_BASES = {
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """A length-four cyclic schedule; every consecutive four draws cover it."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _dihedral_shapes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    result: set[tuple[tuple[int, int], ...]] = set()
    for base in _SHAPE_BASES[size]:
        current = tuple(base)
        for _ in range(4):
            result.add(_normalize(current))
            result.add(_normalize((row, -col) for row, col in current))
            current = tuple((col, -row) for row, col in current)
    return tuple(sorted(result))


_SHAPES = {size: _dihedral_shapes(size) for size in _SHAPE_BASES}


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _rank_key(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    return len(cells), _bbox(cells)


def _monochrome_components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
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
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            components.append(tuple(sorted(cells)))
    return components


def _color_blind_components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
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
            components.append(tuple(sorted(cells)))
    return components


def _component_color(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> int:
    row, col = next(iter(cells))
    return grid[row][col]


def _has_cross_color_contact(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for drow, dcol in ((1, 0), (0, 1)):
                rr, cc = row + drow, col + dcol
                if 0 <= rr < height and 0 <= cc < width:
                    other = grid[rr][cc]
                    if other != 0 and other != color:
                        return True
    return False


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if not (9 <= len(grid) <= 10 and 10 <= width <= 12):
        return [f"grid dimensions must be 9..10 by 10..12; found {len(grid)}x{width}"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {
            "errors": errors,
            "components": [],
            "ranked": [],
            "sizes": (),
            "colors_by_rank": (),
            "lesson_profile": None,
            "cross_color_contact": False,
        }

    components = _monochrome_components(grid)
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must be present")
    if len(components) != 4:
        errors.append(f"expected exactly four monochromatic objects; found {len(components)}")

    colors = [_component_color(grid, cells) for cells in components]
    if len(colors) == 4 and len(set(colors)) != 4:
        errors.append(f"object input colors must be distinct; found {sorted(colors)}")

    ranked = sorted(components, key=_rank_key)
    sizes = tuple(len(cells) for cells in ranked)
    if len(components) == 4 and sizes not in _ALLOWED_SIZE_PROFILES:
        errors.append(
            "sorted object areas must be 2/3/4/5 or 2/2/4/5; "
            f"found {sizes}"
        )

    colors_by_rank = tuple(_component_color(grid, cells) for cells in ranked)
    cross_color_contact = _has_cross_color_contact(grid)
    lesson_profile = None
    if len(components) == 4 and sizes in _ALLOWED_SIZE_PROFILES and len(set(colors)) == 4:
        if sizes == (2, 2, 4, 5):
            lesson_profile = "tie_break"
        elif cross_color_contact:
            lesson_profile = "touching_colors"
        elif set(colors_by_rank) == set(_RANK_PALETTE):
            if colors_by_rank == _RANK_PALETTE:
                errors.append("input colors already equal every output rank color")
            else:
                lesson_profile = "rank_palette"
        else:
            lesson_profile = "canonical_strict"

    return {
        "errors": errors,
        "components": components,
        "ranked": ranked,
        "sizes": sizes,
        "colors_by_rank": colors_by_rank,
        "lesson_profile": lesson_profile,
        "cross_color_contact": cross_color_contact,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["lesson_profile"] is None:
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "lesson_profile": analysis["lesson_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    """The full generated manifold stays within observed canonical dimensions."""
    return self_check(grid)


def _shape_in_slot(size: int, slot: int, height: int, width: int, rng) -> tuple[tuple[int, int], ...]:
    shape = rng.choice(_SHAPES[size])
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    row_base = (0, 0, height - 3, height - 3)[slot]
    col_base = (0, width - 3, 0, width - 3)[slot]
    row_offset = rng.randint(0, 3 - shape_h)
    col_offset = rng.randint(0, 3 - shape_w)
    return tuple(
        sorted((row_base + row_offset + row, col_base + col_offset + col) for row, col in shape)
    )


def _separated_objects(ctx, profile: str, height: int, width: int, band_tag: str):
    if profile == "tie_break":
        slot_sizes = (2, 2, 4, 5)
    elif profile == "rank_palette":
        # Descending scan order is a guaranteed counterexample to scan-order rank.
        slot_sizes = (5, 4, 3, 2)
    else:
        layouts = (
            (2, 3, 4, 5),
            (3, 5, 2, 4),
            (4, 2, 5, 3),
            (5, 3, 4, 2),
        )
        slot_sizes = ctx.draw_rng(f"slot_size_order:{band_tag}").choice(layouts)
    return [
        _shape_in_slot(size, slot, height, width, ctx.draw_rng(f"shape_slot_{slot}:{band_tag}"))
        for slot, size in enumerate(slot_sizes)
    ]


def _touching_objects(ctx, height: int, width: int, band_tag: str):
    variant = ctx.draw_rng(f"touching_variant:{band_tag}").randrange(4)
    if variant % 2 == 0:
        first = {(0, 0), (0, 1)}
        second = {(1, 0), (1, 1), (1, 2)}
        pair_h, pair_w = 2, 3
    else:
        first = {(0, 0), (1, 0)}
        second = {(0, 1), (1, 1), (2, 1)}
        pair_h, pair_w = 3, 2
    if variant >= 2:
        first = {(row, pair_w - 1 - col) for row, col in first}
        second = {(row, pair_w - 1 - col) for row, col in second}

    anchor_rng = ctx.draw_rng(f"touching_anchor:{band_tag}")
    row0 = anchor_rng.randint(0, 1)
    col0 = anchor_rng.randint(1, width - pair_w - 1)
    first = tuple(sorted((row0 + row, col0 + col) for row, col in first))
    second = tuple(sorted((row0 + row, col0 + col) for row, col in second))

    third = _shape_in_slot(4, 2, height, width, ctx.draw_rng(f"touching_shape_2:{band_tag}"))
    fourth = _shape_in_slot(5, 3, height, width, ctx.draw_rng(f"touching_shape_3:{band_tag}"))
    return [first, second, third, fourth]


def _colors_by_rank(ctx, profile: str, band_tag: str) -> tuple[int, ...]:
    if profile == "rank_palette":
        return ctx.draw_rng(f"rank_palette_permutation:{band_tag}").choice(_RANK_DERANGEMENTS)
    return tuple(ctx.draw_rng(f"input_colors:{band_tag}").sample(_NON_RANK_COLORS, 4))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"difficulty must be easy/medium/hard/None, found {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int("grid_h", 9, 10)
    width = ctx.draw_int("grid_w", 10, 12)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    options = SCHEDULE_PROFILES if overrides.get("lesson_profile") is not None else (scheduled,)
    profile = ctx.draw_choice("lesson_profile", options)

    band_tag = difficulty or "unbanded"
    if profile == "touching_colors":
        component_cells = _touching_objects(ctx, height, width, band_tag)
    else:
        component_cells = _separated_objects(ctx, profile, height, width, band_tag)

    ranked = sorted(component_cells, key=_rank_key)
    colors = _colors_by_rank(ctx, profile, band_tag)
    grid = full_grid(height, width, 0)
    for cells, color in zip(ranked, colors):
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("constructive object placement overlapped")
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator produced invalid grid: {errors}")
    observed = observe_overrides(grid)
    if observed.get("lesson_profile") != profile:
        raise RuntimeError(
            f"profile realization drift: requested {profile!r}, observed {observed!r}"
        )
    return grid


def _paint_ranked(grid, components) -> list[list[int]]:
    output = full_grid(len(grid), len(grid[0]), 0)
    for cells, color in zip(components, _RANK_PALETTE):
        for row, col in cells:
            output[row][col] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests/probes; Racket remains label authority."""
    components = sorted(_monochrome_components(grid), key=_rank_key)
    return _paint_ranked(grid, components)


def _rival_color_blind_components(grid):
    return _paint_ranked(grid, sorted(_color_blind_components(grid), key=_rank_key))


def _rival_reverse_bbox_ties(grid):
    components = _monochrome_components(grid)
    components = sorted(
        components,
        key=lambda cells: (len(cells), tuple(-value for value in _bbox(cells))),
    )
    return _paint_ranked(grid, components)


def _rival_scan_order_only(grid):
    return _paint_ranked(grid, sorted(_monochrome_components(grid), key=_bbox))


def _rival_numeric_input_color_order(grid):
    components = sorted(
        _monochrome_components(grid),
        key=lambda cells: (_component_color(grid, cells), _bbox(cells)),
    )
    return _paint_ranked(grid, components)


def _rival_descending_area(grid):
    components = sorted(_monochrome_components(grid), key=_rank_key, reverse=True)
    return _paint_ranked(grid, components)


def _witness_equal_area_bbox_tie(grid) -> bool:
    return _analysis(grid)["sizes"] == (2, 2, 4, 5)


def _witness_different_colors_touch(grid) -> bool:
    return bool(_analysis(grid)["cross_color_contact"])


def _witness_rank_palette_distractor(grid) -> bool:
    analysis = _analysis(grid)
    return (
        set(analysis["colors_by_rank"]) == set(_RANK_PALETTE)
        and analysis["colors_by_rank"] != _RANK_PALETTE
    )


def _witness_scan_order_conflict(grid) -> bool:
    components = _monochrome_components(grid)
    return sorted(components, key=_bbox) != sorted(components, key=_rank_key)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "equal_area_bbox_tie": _witness_equal_area_bbox_tie,
    "different_colors_touch": _witness_different_colors_touch,
    "rank_palette_distractor": _witness_rank_palette_distractor,
    "scan_order_conflict": _witness_scan_order_conflict,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "color_blind_components": _rival_color_blind_components,
    "reverse_bbox_ties": _rival_reverse_bbox_ties,
    "scan_order_only": _rival_scan_order_only,
    "numeric_input_color_order": _rival_numeric_input_color_order,
    "descending_area": _rival_descending_area,
}
WITNESS_RIVALS = {
    "equal_area_bbox_tie": ["reverse_bbox_ties"],
    "different_colors_touch": ["color_blind_components"],
    "rank_palette_distractor": ["numeric_input_color_order"],
    "scan_order_conflict": ["scan_order_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def lesson_identifiable(train_pairs, query_pair) -> list[str]:
    """Require every declared rival to lose on at least one visible demo."""
    del query_pair
    errors: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in train_pairs):
            errors.append(f"lesson does not refute rival {name}")
    return errors
