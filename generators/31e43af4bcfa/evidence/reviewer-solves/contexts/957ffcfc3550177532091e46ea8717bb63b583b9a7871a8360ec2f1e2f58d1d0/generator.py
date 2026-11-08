"""Generator for 31e43af4bcfa — rank, recolor, crop, and pack objects.

The first row is a left-aligned palette.  The remaining rows contain the same
number of 4-connected color-1 objects.  Objects are ordered by
``(area, top row, left column)``, recolored by the palette in that order,
tightly cropped, and packed left-to-right with one zero column between pieces.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "31e43af4bcfa"
VERSION = "3.1.0"
TASK_ID = "31e43af4bcfa"
RULE_HASH = "82a777a1969e"
# Six consecutive pairs contain two of each profile. Five demonstrations plus
# one query therefore keep every decisive witness under any single holdout.
EXAMPLES_NEEDED = 5

SUMMARY = (
    "Row 0 is a left-aligned palette of K distinct colors. Rows 1+ contain "
    "K separate 4-connected color-1 objects. Sort the objects by "
    "(cell count ascending, top row ascending, left column ascending), "
    "recolor them with the palette in that order, crop each object to its "
    "bounding box, and pack the crops left-to-right with one zero column "
    "between adjacent pieces. Equal-size objects are intentional: top row, "
    "then left column, resolves ties. Five demonstrations preserve the "
    "scheduled area, connectivity, and tie witnesses under query rotation."
)

INVARIANTS = [
    "row 0 has K distinct palette colors in a nonzero left prefix",
    "rows 1+ contain exactly K separate color-1 4-connected objects",
    "K is in 2..4 and palette colors are chosen from 2..9",
    "object ordering is (area, top row, left column), including equal-area ties",
    "output crops each ranked object and packs crops with one zero-column gap",
]

AXES = {
    "K": {
        "type": "int",
        "default": "difficulty-weighted choice across the full lawful domain",
        "valid": "2..4",
        "doc": "Palette and body-object count.",
    },
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted choice with canonical-size anchors",
        "valid": "5..9",
        "doc": "Total input height including the palette row.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted choice with canonical-size anchors",
        "valid": "7..13",
        "doc": "Input width.",
    },
}

# Every cross-product combination is constructible.  Exact overrides use the
# full public domain in every difficulty band; difficulty changes only default
# sampling mass.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "distinct_rank",
    "row_tie_cross_order",
    "same_row_column_tie",
)

_BAND_DEFAULTS = {
    None: {
        "K": (2, 3, 3, 4),
        "grid_h": (5, 6, 6, 7, 8, 9),
        "grid_w": (7, 8, 8, 9, 10, 11, 12, 13),
    },
    "easy": {
        "K": (2, 2, 3, 3, 4),
        "grid_h": (5, 5, 5, 6, 6, 7, 8, 9),
        "grid_w": (7, 7, 8, 8, 9, 10, 11, 12, 13),
    },
    "medium": {
        "K": (2, 3, 3, 4, 4),
        "grid_h": (5, 5, 6, 6, 7, 8, 9),
        "grid_w": (7, 8, 8, 9, 10, 11, 12, 13),
    },
    "hard": {
        "K": (2, 3, 4, 4, 4),
        "grid_h": (5, 5, 7, 8, 8, 9, 9),
        "grid_w": (7, 8, 10, 11, 12, 12, 13, 13),
    },
}

# Connected polyomino seeds.  D4 transforms below provide orientation variety.
_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every consecutive three-example window contains all decisive branches."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _normalize_shape(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variants(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    for base in _BASE_SHAPES[size]:
        for reflect in (False, True):
            for turns in range(4):
                transformed: list[tuple[int, int]] = []
                for r, c in base:
                    x, y = r, (-c if reflect else c)
                    for _ in range(turns):
                        x, y = y, -x
                    transformed.append((x, y))
                variants.add(_normalize_shape(transformed))
    return tuple(sorted(variants))


_SHAPE_VARIANTS = {size: _shape_variants(size) for size in _BASE_SHAPES}


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


def _candidate_placements(
    shape: tuple[tuple[int, int], ...], h: int, w: int
) -> list[tuple[int, int, tuple[tuple[int, int], ...]]]:
    sh, sw = _shape_dims(shape)
    return [
        (r0, c0, tuple((r0 + r, c0 + c) for r, c in shape))
        for r0 in range(1, h - sh + 1)
        for c0 in range(0, w - sw + 1)
    ]


def _can_place(grid: list[list[int]], cells: tuple[tuple[int, int], ...]) -> bool:
    h, w = len(grid), len(grid[0])
    own = set(cells)
    for r, c in cells:
        if grid[r][c] != 0:
            return False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 1 <= nr < h and 0 <= nc < w:
                if grid[nr][nc] != 0 and (nr, nc) not in own:
                    return False
    return True


def _write_cells(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], value: int
) -> None:
    for r, c in cells:
        grid[r][c] = value


def _reading_key(cells: tuple[tuple[int, int], ...] | list[tuple[int, int]]):
    return min(r for r, _ in cells), min(c for _, c in cells)


def _relation_ok(profile: str, a, b) -> bool:
    ar, ac = a[0], a[1]
    br, bc = b[0], b[1]
    if profile == "distinct_rank":
        return (ar, ac) < (br, bc)
    if profile == "row_tie_cross_order":
        return ar < br and ac > bc
    if profile == "same_row_column_tie":
        return ar == br and ac < bc
    raise ValueError(profile)


def _target_sizes(rng, k: int, profile: str) -> list[int]:
    if profile == "distinct_rank":
        # The square-4 precedes the L-3 spatially, but not by cell count.
        # Both have perimeter 8 and bounding-box area 4: one small witness
        # distinguishes area from all three measures even when K is only 2.
        return [4, 3, *range(1, k - 1)]

    tie_size = rng.choice((2, 3, 4))
    remaining = [size for size in (1, 2, 3, 4) if size != tie_size]
    rng.shuffle(remaining)
    return [tie_size, tie_size, *remaining[: max(0, k - 2)]]


def _choose_shapes(rng, sizes: list[int], profile: str, h: int, w: int):
    choices: list[tuple[tuple[int, int], ...]] = []
    for index, size in enumerate(sizes):
        fitting = [
            shape
            for shape in _SHAPE_VARIANTS[size]
            if _shape_dims(shape)[0] <= h - 1 and _shape_dims(shape)[1] <= w
        ]
        if not fitting:
            raise ValueError(f"no shape of size {size} fits {h}x{w}")
        if profile == "distinct_rank" and index < 2:
            fitting = [shape for shape in fitting if _shape_dims(shape) == (2, 2)]
        if index == 1 and profile != "distinct_rank":
            first = choices[0]
            distinct = [shape for shape in fitting if shape != first]
            if not distinct:
                raise ValueError("tie profile needs two geometrically distinct shapes")
            choices.append(rng.choice(distinct))
        else:
            choices.append(rng.choice(fitting))
    return choices


def _diagonal_contact(a, b) -> bool:
    other = set(b)
    return any((r + dr, c + dc) in other for r, c in a
               for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))


def _place_profile(
    rng, h: int, w: int, sizes: list[int], profile: str
) -> list[list[int]]:
    for _shape_attempt in range(120):
        shapes = _choose_shapes(rng, sizes, profile, h, w)
        candidates = [_candidate_placements(shape, h, w) for shape in shapes]
        for pool in candidates:
            rng.shuffle(pool)

        grid = full_grid(h, w, 0)
        pair_candidates = [
            (a, b)
            for a in candidates[0]
            for b in candidates[1]
            if _relation_ok(profile, a, b)
            and (profile != "distinct_rank" or _diagonal_contact(a[2], b[2]))
        ]
        rng.shuffle(pair_candidates)

        for a, b in pair_candidates:
            if not _can_place(grid, a[2]):
                continue
            _write_cells(grid, a[2], 1)
            if not _can_place(grid, b[2]):
                _write_cells(grid, a[2], 0)
                continue
            _write_cells(grid, b[2], 1)

            def place_rest(index: int) -> bool:
                if index == len(shapes):
                    return True
                for placement in candidates[index]:
                    cells = placement[2]
                    if not _can_place(grid, cells):
                        continue
                    _write_cells(grid, cells, 1)
                    if place_rest(index + 1):
                        return True
                    _write_cells(grid, cells, 0)
                return False

            if place_rest(2):
                return grid
            _write_cells(grid, b[2], 0)
            _write_cells(grid, a[2], 0)
    raise ValueError(
        f"could not realize {profile} layout for sizes={sizes} in {h}x{w}"
    )


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
    rng = ctx.draw_rng("layout")
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _BAND_DEFAULTS[difficulty]

    # Pinned canonical-size anchors occur twice per eight ordinary samples in
    # every band.  Exact overrides always take precedence and remain valid over
    # the complete public domain.
    canonical_anchor = int(sample_index) % 8 in (0, 4)
    if "K" in overrides:
        k = ctx.draw_int_strict("K", 2, 4)
    elif canonical_anchor:
        k = int(ctx.draw_choice("K", (3, 4)))
    else:
        k = int(ctx.draw_choice("K", defaults["K"]))

    if "grid_h" in overrides:
        h = ctx.draw_int_strict("grid_h", 5, 9)
    elif canonical_anchor:
        h = int(ctx.draw_choice("grid_h", (5,)))
    else:
        h = int(ctx.draw_choice("grid_h", defaults["grid_h"]))

    if "grid_w" in overrides:
        w = ctx.draw_int_strict("grid_w", 7, 13)
    elif canonical_anchor:
        w = int(ctx.draw_choice("grid_w", (8,)))
    else:
        w = int(ctx.draw_choice("grid_w", defaults["grid_w"]))

    palette = rng.sample(list(range(2, 10)), k)
    sizes = _target_sizes(rng, k, profile)
    grid = _place_profile(rng, h, w, sizes, profile)
    for c, color in enumerate(palette):
        grid[0][c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    if not SEMANTIC_WITNESSES[profile](grid):
        raise AssertionError(f"generated scene missed scheduled profile {profile}")
    return grid


def _coerce_grid(grid: Any) -> list[list[Any]]:
    if not isinstance(grid, list):
        return []
    return [list(row) if isinstance(row, (list, tuple, str)) else [] for row in grid]


def _components_ones(
    grid: list[list[int]], *, diagonal: bool = False
) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diagonal:
        neighbors += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in neighbors:
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == 1
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _palette(grid: list[list[int]]) -> list[int]:
    out: list[int] = []
    for value in grid[0]:
        if value == 0:
            break
        out.append(value)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural authority-valid input grammar; accepts every canonical input."""
    del difficulty, meta
    rows = _coerce_grid(grid)
    if not rows or not rows[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return ["grid must be rectangular"]

    errors: list[str] = []
    height = len(rows)
    if not 5 <= height <= 9:
        errors.append(f"grid height must be 5..9, got {height}")
    if not 7 <= width <= 13:
        errors.append(f"grid width must be 7..13, got {width}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC colors at {invalid[:3]}")
        return errors

    row0 = rows[0]
    k = 0
    while k < width and row0[k] != 0:
        k += 1
    if not 2 <= k <= 4:
        errors.append(f"expected 2..4 palette entries in row 0, got {k}")
    if any(value != 0 for value in row0[k:]):
        errors.append("palette must be a contiguous nonzero left prefix")
    palette = row0[:k]
    if any(value not in range(2, 10) for value in palette):
        errors.append("palette colors must be in 2..9 (never background 0 or object color 1)")
    if len(set(palette)) != len(palette):
        errors.append("palette colors must be pairwise distinct")

    bad_body = [
        (r, c, value)
        for r, row in enumerate(rows[1:], start=1)
        for c, value in enumerate(row)
        if value not in (0, 1)
    ]
    if bad_body:
        errors.append(f"body must contain only 0 and 1, found {bad_body[:3]}")
        return errors

    comps = _components_ones(rows)
    if len(comps) != k:
        errors.append(f"expected {k} body components, got {len(comps)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate for the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    rows = _coerce_grid(grid)
    return {"K": len(_palette(rows)), "grid_h": len(rows), "grid_w": len(rows[0])}


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _crop_component(cells: list[tuple[int, int]]) -> list[list[int]]:
    top, left, bottom, right = _bbox(cells)
    crop = full_grid(bottom - top + 1, right - left + 1, 0)
    for r, c in cells:
        crop[r - top][c - left] = 1
    return crop


def _pack_ordered(
    grid: list[list[int]], ordered: list[list[tuple[int, int]]],
    *, palette: list[int] | None = None,
) -> list[list[int]]:
    if palette is None:
        palette = _palette(grid)
    pieces: list[list[list[int]]] = []
    for cells, color in zip(ordered, palette, strict=True):
        crop = _crop_component(cells)
        pieces.append([[color if value else 0 for value in row] for row in crop])
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    output[r][left + c] = value
        left += len(piece[0]) + 1
    return output


def _component_record(cells: list[tuple[int, int]]):
    top, left, _, _ = _bbox(cells)
    return len(cells), top, left


def _solve_with_key(grid, key: Callable[[list[tuple[int, int]]], tuple]) -> list[list[int]]:
    rows = _coerce_grid(grid)
    errors = self_check(rows)
    if errors:
        raise ValueError("solver requires lawful input: " + "; ".join(errors))
    return _pack_ordered(rows, sorted(_components_ones(rows), key=key))


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror for tests only; the Racket rule remains output authority."""
    return _solve_with_key(grid, _component_record)


def _solve_reading_order(grid):
    return _solve_with_key(grid, lambda cells: _reading_key(cells))


def _solve_size_left_top(grid):
    return _solve_with_key(
        grid,
        lambda cells: (len(cells), _reading_key(cells)[1], _reading_key(cells)[0]),
    )


def _solve_size_reverse_ties(grid):
    return _solve_with_key(
        grid,
        lambda cells: (len(cells), -_reading_key(cells)[0], -_reading_key(cells)[1]),
    )


def _perimeter(cells) -> int:
    occupied = set(cells)
    return sum((r + dr, c + dc) not in occupied for r, c in occupied
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def _solve_capped_area_three(grid):
    return _solve_with_key(grid, lambda cells: (min(len(cells), 3), *_reading_key(cells)))


def _solve_perimeter(grid):
    return _solve_with_key(grid, lambda cells: (_perimeter(cells), *_reading_key(cells)))


def _solve_bbox_area(grid):
    def key(cells):
        top, left, bottom, right = _bbox(cells)
        return (bottom - top + 1) * (right - left + 1), top, left

    return _solve_with_key(grid, key)


def _solve_eight_connected(grid):
    rows = _coerce_grid(grid)
    errors = self_check(rows)
    if errors:
        raise ValueError("solver requires lawful input: " + "; ".join(errors))
    ordered = sorted(_components_ones(rows, diagonal=True), key=_component_record)
    # This rival treats corner-touching pieces as one inventory item and uses
    # the matching palette prefix. It returns a prediction, not an exception,
    # when its extraction rule finds fewer pieces than the intended rule.
    return _pack_ordered(rows, ordered, palette=_palette(rows)[:len(ordered)])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "reading_order_only": _solve_reading_order,
    "size_left_then_top": _solve_size_left_top,
    "size_reverse_ties": _solve_size_reverse_ties,
    "capped_area_three": _solve_capped_area_three,
    "perimeter_order": _solve_perimeter,
    "bounding_box_area": _solve_bbox_area,
    "eight_connected_objects": _solve_eight_connected,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# Only these rivals fit every canonical labeled pair. The remaining rivals
# still belong in lesson checks, because generated demonstrations must teach
# the relevant distinction independently of the canonical examples.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("capped_area_three", "perimeter_order", "eight_connected_objects")
}


def _analysis(grid) -> dict[str, Any]:
    rows = _coerce_grid(grid)
    errors = self_check(rows)
    if errors:
        return {"errors": errors}
    comps = sorted(_components_ones(rows), key=_reading_key)
    records = [_component_record(cells) for cells in comps]
    distinct_rank = (
        len({size for size, _, _ in records}) == len(records)
        and [size for size, _, _ in records] != sorted(size for size, _, _ in records)
    )
    row_tie = any(
        size_a == size_b and top_a < top_b and left_a > left_b
        for i, (size_a, top_a, left_a) in enumerate(records)
        for size_b, top_b, left_b in records[i + 1 :]
    )
    same_row_tie = any(
        size_a == size_b and top_a == top_b and left_a < left_b
        for i, (size_a, top_a, left_a) in enumerate(records)
        for size_b, top_b, left_b in records[i + 1 :]
    )
    return {
        "errors": [],
        "distinct_rank": distinct_rank,
        "row_tie_cross_order": row_tie,
        "same_row_column_tie": same_row_tie,
        "records": records,
    }


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid):
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])

    return predicate


def _metric_witness(grid) -> bool:
    if self_check(grid):
        return False
    reference = rule_mirror(grid)
    return all(SEMANTIC_RIVALS[name](grid) != reference
               for name in ("capped_area_three", "perimeter_order", "bounding_box_area"))


def _connectivity_witness(grid) -> bool:
    if self_check(grid):
        return False
    return len(_components_ones(grid, diagonal=True)) < len(_components_ones(grid))


SEMANTIC_WITNESSES = {
    "distinct_rank": _witness("distinct_rank"),
    "row_tie_cross_order": _witness("row_tie_cross_order"),
    "same_row_column_tie": _witness("same_row_column_tie"),
    "area_metric_conflict": _metric_witness,
    "four_connected_objects": _connectivity_witness,
}
WITNESS_RIVALS = {
    "distinct_rank": ["reading_order_only"],
    "row_tie_cross_order": ["size_left_then_top"],
    "same_row_column_tie": ["size_reverse_ties"],
    "area_metric_conflict": ["capped_area_three", "perimeter_order", "bounding_box_area"],
    "four_connected_objects": ["eight_connected_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible extraction or ordering rival survives."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits_demos and rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but "
                    "predicts a different query output"
                )
        except Exception as exc:
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
