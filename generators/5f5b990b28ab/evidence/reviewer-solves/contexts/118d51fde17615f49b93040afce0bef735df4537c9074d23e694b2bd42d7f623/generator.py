"""Generator for ARC task 5f5b990b28ab — rank cyan objects by bbox area.

The selected Racket rule extracts every 4-connected colour-8 object, sorts the
objects by bounding-box area (largest first), and recolours them with the fixed
palette ``[2, 4, 6, 7, 3, 5, 9]``.  Canonical examples use nested rectangular
outlines, which also admit several tempting shortcuts: nesting depth, scan
order, perimeter/cell count, or width all produce the same labels.

The five-role production schedule preserves canonical nested scenes while adding
two disconnected ranking-stress roles.  In those roles bbox area, scan order,
cell count and width induce different orders.  Every five consecutive samples
contains both stress roles, so holding out any one pair still leaves a decisive
demonstration.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "5f5b990b28ab"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d23e43212061"

PALETTE = (2, 4, 6, 7, 3, 5, 9)

CANONICAL_NESTED3 = "canonical_nested3"
NESTED2 = "nested2"
NESTED4 = "nested4"
AREA_STRESS3 = "area_stress3"
AREA_STRESS4 = "area_stress4"
SCENE_PROFILES = (
    CANONICAL_NESTED3,
    AREA_STRESS3,
    NESTED2,
    AREA_STRESS4,
    NESTED4,
)

SUMMARY = (
    "A zero-background grid contains two to four disconnected cyan (8) "
    "rectangular objects. Sort the objects by bounding-box area, largest first, "
    "then recolour them in the fixed order red(2), yellow(4), magenta(6), "
    "orange(7), green(3), gray(5), maroon(9). Canonical roles are nested; "
    "ranking-stress roles separate the objects so area must be distinguished "
    "from scan order, perimeter/cell count and width."
)

INVARIANTS = [
    "input cells are only background 0 and source colour 8",
    "there are two to four 4-connected source objects",
    "each source object is an exact rectangular perimeter, except canonical tiny solid centres",
    "all source-object bounding-box areas are distinct",
    "the output preserves shape and paints objects by descending bbox area with the fixed palette",
]

COUNTER_HYPOTHESES = [
    "colour components in scan order",
    "rank components by perimeter or number of cells",
    "rank components by bounding-box width",
    "infer colours solely from nesting depth",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-role semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact observable scene family: canonical 13x13 nested depth 3, "
            "nested depth 2/4, or disconnected bbox-area stress depth 3/4."
        ),
    },
}

# The sole exact axis is constructive in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the semantic role for this position in the five-pair cycle."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None and (type(profile) is not str or profile not in SCENE_PROFILES):
        raise ValueError(f"scene_profile must be one of {SCENE_PROFILES}")


def _dimension_range(profile: str, difficulty: Any) -> tuple[int, int]:
    if profile == CANONICAL_NESTED3:
        return 13, 13
    if profile == NESTED4:
        if difficulty == "easy":
            return 14, 16
        if difficulty == "hard":
            return 15, 18
        return 14, 18
    if profile in (AREA_STRESS3, AREA_STRESS4):
        if difficulty == "easy":
            return 13, 15
        if difficulty == "hard":
            return 15, 18
        return 13, 18
    if difficulty == "easy":
        return 10, 14
    if difficulty == "hard":
        return 13, 18
    return 10, 18


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, valid and semantically scheduled input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_profile = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (default_profile,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    rng = ctx.draw_rng(f"profile:{profile}")

    if profile == CANONICAL_NESTED3:
        grid = _draw_canonical_nested3(rng)
    elif profile == NESTED2:
        grid = _draw_nested(rng, 2, *_dimension_range(profile, difficulty))
    elif profile == NESTED4:
        grid = _draw_nested(rng, 4, *_dimension_range(profile, difficulty))
    elif profile == AREA_STRESS3:
        grid = _draw_area_stress(rng, 3, *_dimension_range(profile, difficulty))
    elif profile == AREA_STRESS4:
        grid = _draw_area_stress(rng, 4, *_dimension_range(profile, difficulty))
    else:  # defensive: draw_choice and validation make this unreachable
        raise AssertionError(f"unknown scene profile: {profile!r}")

    observed = observe_overrides(grid)
    requested = {"scene_profile": profile}
    if observed != requested:
        raise AssertionError(f"internal axis drift: requested={requested}, observed={observed}")
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal invalid scene: " + "; ".join(errors))
    return grid


def _draw_canonical_nested3(rng) -> list[list[int]]:
    """A 13x13 exact-profile anchor with varied lawful nested geometry."""
    grid = full_grid(13, 13, 0)
    outer_h = rng.randint(9, 13)
    outer_w = rng.randint(9, 13)
    top = rng.randint(0, 13 - outer_h)
    left = rng.randint(0, 13 - outer_w)
    _draw_nested_frames(grid, top, left, outer_h, outer_w, 3)
    return grid


def _draw_nested(rng, count: int, lo: int, hi: int) -> list[list[int]]:
    height = rng.randint(lo, hi)
    width = rng.randint(lo, hi)
    minimum_outer = 4 * (count - 1) + 1
    outer_h = rng.randint(minimum_outer, height)
    outer_w = rng.randint(minimum_outer, width)
    top = rng.randint(0, height - outer_h)
    left = rng.randint(0, width - outer_w)
    grid = full_grid(height, width, 0)
    _draw_nested_frames(grid, top, left, outer_h, outer_w, count)
    return grid


def _draw_nested_frames(
    grid: list[list[int]], top: int, left: int, height: int, width: int, count: int
) -> None:
    bottom = top + height - 1
    right = left + width - 1
    for depth in range(count):
        inset = 2 * depth
        draw_frame(
            grid,
            top + inset,
            left + inset,
            bottom - inset,
            right - inset,
            8,
        )


def _draw_area_stress(rng, count: int, lo: int, hi: int) -> list[list[int]]:
    """Draw disconnected frames whose plausible orderings disagree.

    Base bboxes and measures, in true area order, are:
      A 5x6 area 30 / 18 cells (bottom-left)
      B 7x4 area 28 / 18 cells (top-right)
      C 3x8 area 24 / 18 cells (top-left)
      D 4x3 area 12 / 10 cells (bottom-right, four-object profile only)

    Scan order is C,B,A,(D); cell-count order is C,B,A,(D) after the stable
    bbox tie-break; width order is C,A,B,(D).  Thus every stress scene is a
    direct counterexample to all declared shortcuts.
    """
    height = rng.randint(lo, hi)
    width = rng.randint(lo, hi)
    base = full_grid(13, 13, 0)
    templates = (
        (
            (8, 0, 12, 5),   # A: 5x6, area 30
            (0, 9, 6, 12),   # B: 7x4, area 28
            (0, 0, 2, 7),    # C: 3x8, area 24
            (9, 10, 12, 12), # D: 4x3, area 12
        ),
        (
            (8, 0, 12, 6),   # A: 5x7, area 35
            (0, 9, 7, 12),   # B: 8x4, area 32
            (0, 0, 2, 6),    # C: 3x7, area 21
            (9, 10, 12, 12), # D: 4x3, area 12
        ),
    )
    boxes = templates[rng.randrange(len(templates))]
    for r0, c0, r1, c1 in boxes[:count]:
        draw_frame(base, r0, c0, r1, c1, 8)
    if rng.randrange(2):
        base = [row[::-1] for row in base]

    top = rng.randint(0, height - 13)
    left = rng.randint(0, width - 13)
    grid = full_grid(height, width, 0)
    for row in range(13):
        for col in range(13):
            if base[row][col] == 8:
                grid[top + row][left + col] = 8
    return grid


def _rectangular_grid(grid: Any) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return 0, 0, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or value not in (0, 8):
                errors.append("input cells must be integer colours 0 or 8")
                return len(grid), width, errors
    return len(grid), width, errors


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    }
    components_found: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for neighbour in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    cells.add(neighbour)
                    queue.append(neighbour)
        components_found.append(cells)
    return sorted(components_found, key=min)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _box_area(cells: Iterable[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = _bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _box_width(cells: Iterable[tuple[int, int]]) -> int:
    _, c0, _, c1 = _bbox(cells)
    return c1 - c0 + 1


def _border_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }


def _is_lawful_rect_object(cells: set[tuple[int, int]]) -> bool:
    box = _bbox(cells)
    if cells == _border_cells(box):
        return True
    r0, c0, r1, c1 = box
    # One canonical query uses a solid 3x3 centre.  Retain that authoritative
    # tiny-centre variant without admitting arbitrary filled rectangles.
    full = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
    }
    return (r1 - r0 + 1) <= 3 and (c1 - c0 + 1) <= 3 and cells == full


def _is_nested(components_found: list[set[tuple[int, int]]]) -> bool:
    ordered = sorted(components_found, key=lambda cells: (-_box_area(cells), _bbox(cells)))
    if not ordered:
        return False
    for outer, inner in zip(ordered, ordered[1:]):
        ro0, co0, ro1, co1 = _bbox(outer)
        ri0, ci0, ri1, ci1 = _bbox(inner)
        if not (ro0 < ri0 and co0 < ci0 and ri1 < ro1 and ci1 < co1):
            return False
    return True


def _profile_from_grid(grid: list[list[int]]) -> str:
    height, width = len(grid), len(grid[0])
    components_found = _components(grid)
    count = len(components_found)
    nested = _is_nested(components_found)
    if (height, width, count, nested) == (13, 13, 3, True):
        return CANONICAL_NESTED3
    if count == 2 and nested:
        return NESTED2
    if count == 4 and nested:
        return NESTED4
    if count == 3 and not nested:
        return AREA_STRESS3
    if count == 4 and not nested:
        return AREA_STRESS4
    raise ValueError(
        f"grid is outside the declared profiles: shape={(height, width)} "
        f"objects={count} nested={nested}"
    )


def observe_overrides(grid):
    """Recover the exact public axis from returned pixels alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {"scene_profile": _profile_from_grid(grid)}


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or semantically ambiguous inputs without mutating them."""
    del difficulty, meta
    height, width, errors = _rectangular_grid(grid)
    if errors:
        return errors
    if not (9 <= height <= 18 and 9 <= width <= 18):
        errors.append(f"grid dimensions {(height, width)} must each be in 9..18")
    components_found = _components(grid)
    if not (2 <= len(components_found) <= 4):
        errors.append(f"expected 2..4 colour-8 objects, found {len(components_found)}")
    for index, cells in enumerate(components_found):
        if not _is_lawful_rect_object(cells):
            errors.append(f"object {index} is not an exact rectangular perimeter/tiny centre")
    areas = [_box_area(cells) for cells in components_found]
    if len(areas) != len(set(areas)):
        errors.append(f"object bounding-box areas must be distinct, found {sorted(areas)}")
    return errors


def strict_canonical_like(grid):
    """The generator's lawful task domain; [] means strict acceptance."""
    return self_check(grid)


def _paint_by_order(grid, key: Callable[[set[tuple[int, int]]], Any]):
    height, width, errors = _rectangular_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(height, width, 0)
    for index, cells in enumerate(sorted(_components(grid), key=key)):
        for row, col in cells:
            out[row][col] = PALETTE[index]
    return out


def _solve(grid):
    return _paint_by_order(grid, lambda cells: (-_box_area(cells), _bbox(cells)))


def _scan_order_rival(grid):
    return _paint_by_order(grid, lambda cells: _bbox(cells))


def _perimeter_order_rival(grid):
    return _paint_by_order(grid, lambda cells: (-len(cells), _bbox(cells)))


def _width_order_rival(grid):
    return _paint_by_order(grid, lambda cells: (-_box_width(cells), _bbox(cells)))


def _differs_from(rival: Callable[[Any], Any], grid: Any) -> bool:
    try:
        return rival(deepcopy(grid)) != _solve(deepcopy(grid))
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "scan_order": _scan_order_rival,
    "perimeter_order": _perimeter_order_rival,
    "width_order": _width_order_rival,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "bbox_area_not_scan_order": lambda grid: _differs_from(_scan_order_rival, grid),
    "bbox_area_not_perimeter": lambda grid: _differs_from(_perimeter_order_rival, grid),
    "bbox_area_not_width": lambda grid: _differs_from(_width_order_rival, grid),
}
WITNESS_RIVALS = {
    "bbox_area_not_scan_order": ["scan_order"],
    "bbox_area_not_perimeter": ["perimeter_order"],
    "bbox_area_not_width": ["width_order"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when demonstrations fail to determine the selected rule."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = _solve(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with descending bbox-area ranking")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos):
            if rival(deepcopy(query["input"])) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
