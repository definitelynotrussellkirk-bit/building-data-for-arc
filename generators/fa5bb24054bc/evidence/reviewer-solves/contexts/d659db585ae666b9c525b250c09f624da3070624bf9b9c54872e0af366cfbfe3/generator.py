"""Constructive sampler for the area-and-hole relation-matrix task.

Each input contains 2..6 monochrome connected panels separated by blank
columns.  The unchanged canonical rule maps panel feature pairs (area, holes)
to an N x N relation matrix:

* 5 on the diagonal;
* 6 for equal area and equal hole count;
* 2 for equal area only;
* 3 for equal hole count only;
* 0 otherwise.

The canonical demonstrations never contain an equal-area/different-holes pair,
so this sampler uses a four-profile cyclic curriculum.  Every four consecutive
samples expose all off-diagonal labels, including the missing code-2 witness.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "fa5bb24054bc"
TASK_ID = GENERATOR_ID
RULE_HASH = "b6e6c6e2c73c"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A 0-background grid contains 2..6 connected monochrome panels separated "
    "by one or two blank columns.  For each panel compute (area, enclosed "
    "4-connected holes).  Output the N×N relation matrix: 5 on the diagonal, "
    "6 for equal area and holes, 2 for equal area only, 3 for equal holes "
    "only, and 0 otherwise.  A four-sample cyclic curriculum constructively "
    "teaches every relation, including equal-area/different-hole code 2."
)

INVARIANTS = [
    "background is 0 and all panels are separated by full blank columns",
    "each panel is one connected monochrome object",
    "ordinary panels are at most three columns wide, so every declared override fits the ARC 30-column limit",
    "every four consecutive samples expose off-diagonal labels 0, 2, 3, and 6",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 3..8; every seventh sample anchors canonical height 3 or 4",
        "valid": "3..8",
    },
    "n_panels": {
        "type": "int",
        "default": "difficulty-aware 2..6; every seventh sample anchors N=3",
        "valid": "2..6",
    },
    "sep_width": {
        "type": "int",
        "default": "one or two full blank columns",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = (
    "no_separators",
    "single_panel",
    "multicolor_panel",
    "disconnected_panel",
)

SCHEDULE_PROFILES = ("area_only", "holes_only", "both", "unrelated")

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_CANONICAL_PROFILES = {(3, 10, 4), (3, 12, 4), (4, 12, 4)}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _ladder(holes: int) -> tuple[tuple[int, int], ...]:
    """Width-3 connected frame with `holes` vertically stacked unit holes."""
    height = 2 * holes + 1
    cells = {(r, c) for r in range(height) for c in (0, 2)}
    cells.update((r, 1) for r in range(0, height, 2))
    return _normalize(cells)


def _solid_same_area_as_ladder(holes: int) -> tuple[tuple[int, int], ...]:
    """Connected no-hole solid with the same area as `_ladder(holes)`."""
    height = 2 * holes + 1
    cells = {(r, c) for r in range(height) for c in range(3)}
    removals = {
        1: {(0, 0)},
        2: {(0, 0), (0, 2)},
        3: {(0, 0), (0, 1), (0, 2)},
    }[holes]
    return _normalize(cells - removals)


_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    # Equal-area/different-hole witnesses.
    "solid8_corner": _solid_same_area_as_ladder(1),
    "solid8_edge": _normalize(
        {(r, c) for r in range(3) for c in range(3)} - {(0, 1)}
    ),
    "ring8": _ladder(1),
    # Same-feature but geometrically distinct area-5 solids.
    "cross5": _normalize({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    "ell5": _normalize({(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)}),
    # Compact nuisance/filler signatures.
    "square4": _normalize({(0, 0), (0, 1), (1, 0), (1, 1)}),
    "rect6": _normalize({(r, c) for r in range(3) for c in range(2)}),
    "tee6": _normalize({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2)}),
    # Hard-band multi-hole extensions; paired solids isolate area from holes.
    "solid13": _solid_same_area_as_ladder(2),
    "ladder2": _ladder(2),
    "solid18": _solid_same_area_as_ladder(3),
    "ladder3": _ladder(3),
}

_PROFILE_PAIR = {
    "area_only": ("solid8_corner", "ring8"),
    "holes_only": ("solid8_corner", "cross5"),
    "both": ("cross5", "ell5"),
    "unrelated": ("cross5", "ring8"),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic four-way teaching profile for audit tooling."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _shape_size(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All distinct D4 variants, normalized to their tight bounding box."""
    source = tuple(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        current = tuple((r, -c if reflected else c) for r, c in source)
        for _ in range(4):
            variants.add(_normalize(current))
            current = tuple((c, -r) for r, c in current)
    return tuple(sorted(variants))


def _oriented_shape(name: str, grid_h: int, rng, *, target_width: int | None = None):
    options = []
    for cells in _variants(_SHAPES[name]):
        height, width = _shape_size(cells)
        if height <= grid_h and width <= 3 and (target_width is None or width == target_width):
            options.append(cells)
    if not options:
        raise ValueError(
            f"shape {name!r} has no orientation fitting height={grid_h}, "
            f"target_width={target_width}"
        )
    return rng.choice(options)


def _draw_axis(ctx, name: str, lo: int, hi: int, *, core_value: int | None, difficulty_aware: bool):
    """Draw an exact axis while allowing deterministic canonical anchors.

    Explicit caller overrides always traverse the full declared domain.  A
    canonical-anchor draw with no override records its realized singleton value
    under the same keyed label, so provenance and pixel observation agree.
    """
    has_override = name in ctx.overrides and ctx.overrides[name] is not None
    if core_value is not None and not has_override:
        return ctx.draw_choice(name, (core_value,))
    if difficulty_aware:
        return ctx.draw_int_diff(name, lo, hi)
    return ctx.draw_int(name, lo, hi)


def _panel_names(profile_name: str, count: int, grid_h: int, rng, *, canonical_anchor: bool):
    pair = list(_PROFILE_PAIR[profile_name])
    if count == 2:
        return pair
    if count == 3:
        # Width 2 makes 3+3+2 plus separators exactly canonical width 10/12.
        if canonical_anchor:
            names = pair + ["square4"]
            rng.shuffle(names)
            return names
        fillers = ["square4", "rect6", "tee6", "solid8_edge"]
        return pair + [rng.choice(fillers)]

    # These four signatures jointly realize all four off-diagonal codes:
    # solid8/ring8 => 2, solid8/cross5 => 3, cross5/ell5 => 6,
    # ring8/cross5 => 0.  Shuffle to prevent fixed output-position shortcuts.
    names = ["solid8_corner", "ring8", "cross5", "ell5"]
    rng.shuffle(names)
    if count >= 5:
        names.append("ladder2" if grid_h >= 5 else rng.choice(("square4", "rect6", "tee6")))
    if count >= 6:
        if grid_h >= 5:
            names.append("solid13")
        else:
            names.append(rng.choice(("solid8_edge", "square4", "rect6", "tee6")))
    return names


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if difficulty is not None:
        if isinstance(difficulty, str) and difficulty not in {"easy", "medium", "hard"}:
            raise ValueError(f"unknown difficulty {difficulty!r}")
        if type(difficulty) in (int, float) and not 0 <= float(difficulty) <= 1:
            raise ValueError("numeric difficulty must lie in [0, 1]")
        if not isinstance(difficulty, str) and type(difficulty) not in (int, float):
            raise ValueError("difficulty must be easy/medium/hard, a number in [0,1], or None")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = schedule_profile(seed, sample_index, difficulty)
    canonical_anchor = sample_index % 7 == 0
    anchor_slot = (sample_index // 7) % 3
    anchor_h = 4 if anchor_slot == 2 else 3
    anchor_sep = 1 if anchor_slot == 0 else 2

    grid_h = _draw_axis(
        ctx,
        "grid_h",
        3,
        8,
        core_value=anchor_h if canonical_anchor else None,
        difficulty_aware=True,
    )
    n_panels = _draw_axis(
        ctx,
        "n_panels",
        2,
        6,
        core_value=3 if canonical_anchor else None,
        difficulty_aware=True,
    )
    sep_width = _draw_axis(
        ctx,
        "sep_width",
        1,
        2,
        core_value=anchor_sep if canonical_anchor else None,
        difficulty_aware=False,
    )

    layout_rng = ctx.draw_rng("panel_layout")
    exact_anchor = canonical_anchor and n_panels == 3 and grid_h in (3, 4)
    names = _panel_names(
        profile_name,
        n_panels,
        grid_h,
        layout_rng,
        canonical_anchor=exact_anchor,
    )
    colors = ctx.draw_distinct_colors("panel_colors", n=n_panels, exclude=(0,))

    panels = []
    for name in names:
        target_width = (2 if name == "square4" else 3) if exact_anchor else None
        cells = _oriented_shape(name, grid_h, layout_rng, target_width=target_width)
        height, width = _shape_size(cells)
        row_offset = layout_rng.randint(0, grid_h - height)
        panels.append((cells, row_offset, width))

    grid_w = sum(width for _, _, width in panels) + sep_width * (n_panels - 1)
    if grid_w > 30:
        raise RuntimeError(f"constructive width invariant broken: {grid_w} > 30")
    grid = full_grid(grid_h, grid_w, 0)
    col = 0
    for (cells, row_offset, width), color in zip(panels, colors):
        paint_at(grid, row_offset, col, cells, color)
        col += width + sep_width
    return grid


def _well_formed_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return [f"grid dimensions {len(grid)}x{width} are outside ARC bounds"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors in 0..9"]
    return []


def _blank_col(grid, col: int) -> bool:
    return all(row[col] == 0 for row in grid)


def _panel_spans(grid):
    spans = []
    col = 0
    width = len(grid[0])
    while col < width:
        while col < width and _blank_col(grid, col):
            col += 1
        if col >= width:
            break
        start = col
        while col < width and not _blank_col(grid, col):
            col += 1
        spans.append((start, col))
    return spans


def _split_blank_cols(grid):
    return [[list(row[start:stop]) for row in grid] for start, stop in _panel_spans(grid)]


def _panel_cells(panel):
    return [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0]


def _holes(cells: Iterable[tuple[int, int]]) -> int:
    cells = _normalize(cells)
    if not cells:
        return 0
    shape_h, shape_w = _shape_size(cells)
    height, width = shape_h + 2, shape_w + 2
    occupied = {(r + 1, c + 1) for r, c in cells}
    free = {(r, c) for r in range(height) for c in range(width) if (r, c) not in occupied}
    outside = {p for p in free if p[0] in (0, height - 1) or p[1] in (0, width - 1)}
    queue = deque(outside)
    seen = set(outside)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            point = (r + dr, c + dc)
            if point in free and point not in seen:
                seen.add(point)
                queue.append(point)
    enclosed = free - seen
    count = 0
    while enclosed:
        count += 1
        stack = [enclosed.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in enclosed:
                    enclosed.remove(point)
                    stack.append(point)
    return count


def _component_count(panel) -> int:
    cells = set(_panel_cells(panel))
    count = 0
    while cells:
        count += 1
        stack = [cells.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in cells:
                    cells.remove(point)
                    stack.append(point)
    return count


def _features(grid):
    return [(len(cells), _holes(cells)) for cells in map(_panel_cells, _split_blank_cols(grid))]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _well_formed_errors(grid)
    if errors:
        return errors
    spans = _panel_spans(grid)
    if not 2 <= len(spans) <= 6:
        errors.append(f"expected 2..6 panels separated by blank columns, saw {len(spans)}")
    panels = _split_blank_cols(grid)
    for index, panel in enumerate(panels):
        cells = _panel_cells(panel)
        if not cells:
            errors.append(f"panel {index} has no nonzero cells")
            continue
        colors = {panel[r][c] for r, c in cells}
        if len(colors) != 1:
            errors.append(f"panel {index} is not monochrome: {sorted(colors)}")
        components = _component_count(panel)
        if components != 1:
            errors.append(f"panel {index} has {components} disconnected components")
    return errors


def observe_overrides(grid):
    errors = _well_formed_errors(grid)
    if errors:
        return {}
    spans = _panel_spans(grid)
    gaps = [spans[index + 1][0] - spans[index][1] for index in range(len(spans) - 1)]
    if not gaps or len(set(gaps)) != 1:
        return {"grid_h": len(grid), "n_panels": len(spans)}
    return {"grid_h": len(grid), "n_panels": len(spans), "sep_width": gaps[0]}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}"]
    return []


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _features(grid)
    return [
        [
            5
            if i == j
            else 6
            if info[i] == info[j]
            else 2
            if info[i][0] == info[j][0]
            else 3
            if info[i][1] == info[j][1]
            else 0
            for j in range(len(info))
        ]
        for i in range(len(info))
    ]


def semantic_observables(grid):
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    info = _features(grid)
    output = rule_mirror(grid)
    offdiag = {value for r, row in enumerate(output) for c, value in enumerate(row) if r != c}
    panels = _split_blank_cols(grid)
    colors = [next(value for row in panel for value in row if value != 0) for panel in panels]
    return {
        **observe_overrides(grid),
        "features": tuple(info),
        "off_diagonal_codes": tuple(sorted(offdiag)),
        "max_holes": max(holes for _, holes in info),
        "distinct_panel_colors": len(set(colors)) == len(colors),
        "canonical_profile": strict_canonical_like(grid) == [],
    }


def _has_relation(grid, predicate) -> bool:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        return False
    info = obs["features"]
    return any(predicate(info[i], info[j]) for i in range(len(info)) for j in range(i + 1, len(info)))


def _same_area_different_holes(grid):
    return _has_relation(grid, lambda left, right: left[0] == right[0] and left[1] != right[1])


def _same_holes_different_area(grid):
    return _has_relation(grid, lambda left, right: left[1] == right[1] and left[0] != right[0])


def _same_features(grid):
    return _has_relation(grid, lambda left, right: left == right)


def _unrelated_features(grid):
    return _has_relation(grid, lambda left, right: left[0] != right[0] and left[1] != right[1])


def _rival_same_area_means_both(grid):
    """Canonical-fitting shortcut: collapse relation 2 into relation 6."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _features(grid)
    return [
        [
            5 if i == j else 6 if info[i][0] == info[j][0]
            else 3 if info[i][1] == info[j][1] else 0
            for j in range(len(info))
        ]
        for i in range(len(info))
    ]


def _rival_no_area_only(grid):
    """Canonical-fitting shortcut: omit relation 2 entirely."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _features(grid)
    return [
        [
            5 if i == j else 6 if info[i] == info[j]
            else 3 if info[i][1] == info[j][1] else 0
            for j in range(len(info))
        ]
        for i in range(len(info))
    ]


SEMANTIC_WITNESSES = {
    # A semantic witness is a counterexample to a declared alternative, not a
    # general coverage counter.  Broader observables stay in semantic_observables
    # and lesson_identifiable without being mislabeled as rival witnesses.
    "same_area_different_holes": _same_area_different_holes,
}


_RIVALS = {
    "same_area_means_both": _rival_same_area_means_both,
    "no_area_only_relation": _rival_no_area_only,
}
SEMANTIC_RIVALS = dict(_RIVALS)
CANONICAL_SHORTCUTS = dict(_RIVALS)
LESSON_COMPETITORS = dict(_RIVALS)
WITNESS_RIVALS = {
    "same_area_different_holes": ["same_area_means_both", "no_area_only_relation"],
}


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    seen_codes: set[int] = set()

    def inspect(pair, label):
        if not isinstance(pair, dict):
            reasons.append(f"{label} is not an input/output pair")
            return None
        grid = pair.get("input")
        errors = self_check(grid)
        if errors:
            reasons.append(f"{label} input is invalid: {errors[0]}")
            return None
        truth = rule_mirror(grid)
        if pair.get("output") != truth:
            reasons.append(f"{label} output disagrees with the area/hole relation rule")
            return None
        return truth

    for index, demo in enumerate(demos):
        truth = inspect(demo, f"demo {index}")
        if truth is not None:
            seen_codes.update(
                value
                for r, row in enumerate(truth)
                for c, value in enumerate(row)
                if r != c
            )
    query_truth = inspect(query, "query")

    descriptions = {
        0: "unrelated area and holes",
        2: "same-area/different-holes",
        3: "same-holes/different-area",
        6: "same area and holes",
    }
    for code in (0, 2, 3, 6):
        if code not in seen_codes:
            reasons.append(f"demos never teach off-diagonal label {code} ({descriptions[code]})")

    if reasons or query_truth is None:
        return reasons
    for name, rival in _RIVALS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with rival {name!r}, which changes the query"
                )
    return reasons


def make_degenerate(name: str):
    """Return a deterministic negative fixture outside the ordinary axis domain."""
    if name == "no_separators":
        return [
            [2, 2, 3, 3, 4, 4],
            [2, 2, 3, 3, 4, 4],
            [0, 0, 0, 0, 0, 0],
        ]
    if name == "single_panel":
        return [[2, 2], [2, 2], [0, 0]]
    if name == "multicolor_panel":
        return [
            [2, 3, 0, 4, 4],
            [2, 3, 0, 4, 4],
            [0, 0, 0, 0, 0],
        ]
    if name == "disconnected_panel":
        return [
            [2, 0, 2, 0, 4, 4],
            [0, 0, 0, 0, 4, 4],
            [0, 2, 0, 0, 0, 0],
        ]
    raise ValueError(f"unknown negative fixture {name!r}")
