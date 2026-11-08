"""Generator for ARC task cc8c719680e6: outline each component's bbox.

For every non-zero, same-colour, 4-connected component, the authoritative
transformation draws the border of that component's axis-aligned bounding box
on a fresh zero background.  Interior source cells disappear; missing border
cells appear; disconnected components are processed separately even when they
share a colour.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc8c719680e6"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "8f9e53b42241"
SUMMARY = (
    "Replace every same-colour 4-connected component by the same-colour "
    "outline of its own axis-aligned bounding box on a fresh zero background."
)

INVARIANTS = [
    "background is 0 and all foreground values are ARC colours 1..9",
    "there are 2..4 non-rectangular same-colour 4-connected components",
    "every component spans at least two rows and two columns",
    "component bounding-box footprints are pairwise disjoint",
    "each component omits at least one cell of its bounding-box border",
]

SCENE_PROFILES = ("canonical_7", "canonical_9", "wide_9x13", "tall_13x9")
N_BLOBS = (2, 3, 4)
COLOR_RELATIONS = ("distinct", "one_repeat")
EDGE_MODES = ("interior", "touching")
PALETTE_KINDS = ("low", "high", "mixed")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled four-example cycle",
        "valid": "|".join(SCENE_PROFILES),
    },
    "n_blobs": {
        "type": "int",
        "default": "scheduled 2/3/4 cycle",
        "valid": "2..4",
    },
    "color_relation": {
        "type": "str",
        "default": "scheduled distinct/repeated cycle",
        "valid": "|".join(COLOR_RELATIONS),
    },
    "edge_mode": {
        "type": "str",
        "default": "scheduled interior/touching cycle",
        "valid": "|".join(EDGE_MODES),
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled low/high/mixed cycle",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Every advertised Cartesian combination is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Four consecutive sample indexes expose every task-relevant branch needed to
# distinguish component-wise bbox outlines from the named rival rules below.
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.4

_PROFILE_SCHEDULE = ("canonical_7", "wide_9x13", "canonical_9", "tall_13x9")
_N_BLOBS_SCHEDULE = (2, 4, 2, 3)
_COLOR_RELATION_SCHEDULE = ("distinct", "distinct", "distinct", "one_repeat")
_EDGE_MODE_SCHEDULE = ("touching", "touching", "interior", "interior")
_PALETTE_SCHEDULE = ("low", "high", "mixed", "low")

SCHEDULE_PROFILES = tuple(
    f"{_PROFILE_SCHEDULE[i]}|n{_N_BLOBS_SCHEDULE[i]}|"
    f"{_COLOR_RELATION_SCHEDULE[i]}|{_EDGE_MODE_SCHEDULE[i]}|"
    f"{_PALETTE_SCHEDULE[i]}"
    for i in range(4)
)

_PROFILE_DIMS = {
    "canonical_7": (7, 7),
    "canonical_9": (9, 9),
    "wide_9x13": (9, 13),
    "tall_13x9": (13, 9),
}
_DIMS_PROFILE = {dims: name for name, dims in _PROFILE_DIMS.items()}

# Generalized primary objects contain an interior source cell and omit border
# cells.  The canonical slots retain their own demonstrated morphologies.
_PRIMARY_SHAPES = (
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}),
    frozenset({(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)}),
    frozenset({(0, 2), (1, 1), (1, 2), (2, 0), (2, 1)}),
)

# Secondary 2x2 L-components are non-rectangular and force at least one border
# addition without introducing an interior cell.
_L_SHAPES = (
    frozenset({(0, 0), (0, 1), (1, 0)}),
    frozenset({(0, 0), (0, 1), (1, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 1), (1, 0), (1, 1)}),
)

# Two default schedule slots reproduce linked canonical morphology profiles.
# Exact coordinates are nuisance variables; these normalized shapes preserve
# the demonstrated cell count, bbox span, missing-area, and interior-cell facts.
_CANONICAL_7_SHAPES = (
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)}),
    frozenset({(0, 1), (1, 0), (1, 1), (2, 1)}),
)
_CANONICAL_9_SHAPES = (
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)}),
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
)
_CANONICAL_9_TRAIN_SHAPES = (
    frozenset({(0, 0), (0, 1), (1, 1), (2, 1)}),
    frozenset({(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)}),
)

Grid = list[list[int]]
Cell = tuple[int, int]

# The previous production sampler exposed only these exact component spans.
# Retain the set as an executable rival boundary so future edits cannot silently
# collapse back to a four-template morphology vocabulary.
_LEGACY_BBOX_SPANS = frozenset({(2, 2), (3, 2), (3, 3), (3, 4)})


def _normalize_shape(cells: frozenset[Cell]) -> frozenset[Cell]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _d4_variants(cells: frozenset[Cell]) -> set[frozenset[Cell]]:
    variants: set[frozenset[Cell]] = set()
    for transform in (
        lambda r, c: (r, c),
        lambda r, c: (r, -c),
        lambda r, c: (-r, c),
        lambda r, c: (-r, -c),
        lambda r, c: (c, r),
        lambda r, c: (c, -r),
        lambda r, c: (-c, r),
        lambda r, c: (-c, -r),
    ):
        variants.add(_normalize_shape(frozenset(transform(r, c) for r, c in cells)))
    return variants


def _shape_span(cells: frozenset[Cell]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _shape_has_interior(cells: frozenset[Cell]) -> bool:
    height, width = _shape_span(cells)
    return any(0 < r < height - 1 and 0 < c < width - 1 for r, c in cells)


_GENERALIZED_BASE_SHAPES = (
    # 2x3/3x2 zig-zags diversify the formerly all-2x2 secondary objects.
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    # Larger connected paths include interior source cells while omitting bbox
    # border cells, jointly teaching both deletion and addition.
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3), (2, 4)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 3)}),
)
_GENERALIZED_SHAPES = tuple(
    sorted(
        set().union(
            *(_d4_variants(shape) for shape in (*_L_SHAPES, *_PRIMARY_SHAPES, *_GENERALIZED_BASE_SHAPES))
        ),
        key=lambda shape: (_shape_span(shape), tuple(sorted(shape))),
    )
)
_GENERALIZED_SHAPES_BY_SPAN = {
    span: tuple(shape for shape in _GENERALIZED_SHAPES if _shape_span(shape) == span)
    for span in sorted({_shape_span(shape) for shape in _GENERALIZED_SHAPES})
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared four-cycle profile for replay/audit tooling."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], value: str) -> str:
    """Record a scheduled default while preserving the full override domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (value,))


def _scheduled_int(ctx, label: str, lo: int, hi: int, value: int) -> int:
    """Integer counterpart of :func:`_scheduled_choice`."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, value, value)


def _components(
    grid: Grid, *, diagonal: bool = False, ignore_color: bool = False
) -> list[dict[str, Any]]:
    """Row-major components; default to same-colour 4-connectivity.

    The two optional policies are used only by explicit semantic rivals.
    """
    h, w = len(grid), len(grid[0])
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen: set[Cell] = set()
    found: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: set[Cell] = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                        and (ignore_color or grid[nr][nc] == color)
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            found.append({"color": color, "cells": cells, "bbox": bbox})
    return found


def _bbox_cells(bbox: tuple[int, int, int, int]) -> set[Cell]:
    r0, c0, r1, c1 = bbox
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def _bbox_border(bbox: tuple[int, int, int, int]) -> set[Cell]:
    r0, c0, r1, c1 = bbox
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _analyze(grid: Any) -> dict[str, Any]:
    """Return structural errors and observable facts without mutating *grid*."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"], "facts": {}}
    if not all(isinstance(row, list) for row in grid) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"], "facts": {}}
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return {"errors": ["grid is ragged"], "facts": {}}
    if not (6 <= h <= 15 and 6 <= w <= 15):
        errors.append(f"grid dimensions must be within 6..15, observed {h}x{w}")
    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"grid contains non-ARC cell values: {bad_cells[:3]}")
        return {"errors": errors, "facts": {"height": h, "width": w}}

    components = _components(grid)
    n = len(components)
    if not 2 <= n <= 4:
        errors.append(f"expected 2..4 foreground components, observed {n}")

    footprints: list[set[Cell]] = []
    for index, component in enumerate(components):
        cells = component["cells"]
        r0, c0, r1, c1 = component["bbox"]
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        footprint = _bbox_cells(component["bbox"])
        border = _bbox_border(component["bbox"])
        footprints.append(footprint)
        if len(cells) < 3:
            errors.append(f"component {index} has fewer than three cells")
        if bh < 2 or bw < 2:
            errors.append(
                f"component {index} must span at least 2x2, observed {bh}x{bw}"
            )
        if cells == footprint:
            errors.append(f"component {index} is a solid rectangle")
        if border <= cells:
            errors.append(
                f"component {index} already contains its entire bbox border"
            )

    for i in range(len(footprints)):
        for j in range(i + 1, len(footprints)):
            if footprints[i] & footprints[j]:
                errors.append(f"component bbox footprints {i} and {j} overlap")

    color_counts = Counter(component["color"] for component in components)
    repeated = sorted(color_counts.values())
    lawful_relation = (
        len(color_counts) == n
        or (
            len(color_counts) == n - 1
            and repeated.count(2) == 1
            and all(count in (1, 2) for count in repeated)
        )
    )
    if n and not lawful_relation:
        errors.append(
            "component colours must be all distinct or contain exactly one "
            "disconnected repeated pair"
        )

    facts = {
        "height": h,
        "width": w,
        "components": components,
        "n_blobs": n,
        "color_counts": color_counts,
        "touching": any(
            r == 0 or c == 0 or r == h - 1 or c == w - 1
            for component in components
            for r, c in component["cells"]
        ),
    }
    return {"errors": errors, "facts": facts}


def self_check(grid: Grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, ambiguous, and off-grammar scenes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if overrides and not errors:
        observed = observe_overrides(grid)
        for axis, requested in overrides.items():
            if axis in AXES and observed.get(axis) != requested:
                errors.append(
                    f"override {axis}={requested!r} realized as {observed.get(axis)!r}"
                )
    return errors


def _morphology_signature(component: dict[str, Any]) -> tuple[int, int, int, int, int]:
    """D4-quotiented, rule-relevant component morphology signature."""
    cells = component["cells"]
    r0, c0, r1, c1 = component["bbox"]
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    border = _bbox_border(component["bbox"])
    return (
        len(cells),
        min(bh, bw),
        max(bh, bw),
        bh * bw - len(cells),
        len(cells - border),
    )


_CANONICAL_JOINT_PROFILES = {
    (
        7,
        7,
        True,
        (
            (4, 2, 3, 2, 0),
            (6, 3, 3, 3, 0),
        ),
    ),
    (
        9,
        9,
        False,
        (
            (4, 2, 3, 2, 0),
            (5, 2, 3, 1, 0),
        ),
    ),
    (
        9,
        9,
        False,
        (
            (5, 3, 3, 4, 1),
            (7, 3, 4, 5, 0),
        ),
    ),
}


def strict_canonical_like(grid: Grid) -> list[str]:
    """Match a joint canonical input profile, not merely the broad grammar.

    Profiles link dimensions, two distinct components, edge contact, and the
    multiset of D4-quotiented component morphologies observed across every
    canonical train/test input.  Generalized 3/4-component teaching scenes are
    intentionally valid under :func:`self_check` but are not counted here.
    """
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    facts = analysis["facts"]
    if facts["n_blobs"] != 2 or len(facts["color_counts"]) != 2:
        return ["strict canonical profile requires two distinct-colour components"]
    morphology = tuple(
        sorted(_morphology_signature(component) for component in facts["components"])
    )
    profile = (
        facts["height"],
        facts["width"],
        bool(facts["touching"]),
        morphology,
    )
    if profile not in _CANONICAL_JOINT_PROFILES:
        return [f"joint canonical profile mismatch: {profile!r}"]
    return []


def _palette(kind: str, unique_count: int, rng) -> list[int]:
    if kind == "low":
        values = rng.sample([1, 2, 3, 4], unique_count)
    elif kind == "high":
        values = rng.sample([6, 7, 8, 9], unique_count)
    elif kind == "mixed":
        # Colour 5 is an unambiguous observer sentinel; the remaining colours
        # vary across low/high ranges to prevent a fixed-palette shortcut.
        values = [5] + rng.sample([1, 2, 3, 4, 6, 7, 8, 9], unique_count - 1)
        rng.shuffle(values)
    else:  # guarded by draw_choice; retained as a fail-loud internal check.
        raise ValueError(f"unknown palette kind {kind!r}")
    return values


def _anchors(h: int, w: int, edge_mode: str, rng) -> list[Cell]:
    """Choose disjoint quadrant anchors while making output geometry vary.

    Slot 0 holds a 3x3 primary object; slots 1..3 hold 2x2 objects.  The
    quadrant ranges keep bbox footprints disjoint, but their cells can touch
    at a split boundary.  Touching layouts pin each
    object to one of its quadrant's outer borders; interior layouts keep every
    object one cell away from the canvas boundary.
    """
    row_split, col_split = h // 2, w // 2

    def draw(lo: int, hi: int) -> int:
        if hi < lo:
            raise RuntimeError(f"empty anchor range {lo}..{hi} for {h}x{w}")
        return rng.randint(lo, hi)

    if edge_mode == "interior":
        return [
            (draw(1, row_split - 2), draw(1, col_split - 2)),
            (draw(1, row_split - 1), draw(col_split + 1, w - 3)),
            (draw(row_split + 1, h - 3), draw(1, col_split - 1)),
            (draw(row_split + 1, h - 3), draw(col_split + 1, w - 3)),
        ]
    if edge_mode == "touching":
        primary = (
            (0, draw(0, col_split - 2))
            if rng.randrange(2) == 0
            else (draw(0, row_split - 2), 0)
        )
        top_right = (
            (0, draw(col_split + 1, w - 2))
            if rng.randrange(2) == 0
            else (draw(0, row_split - 1), w - 2)
        )
        bottom_left = (
            (h - 2, draw(0, col_split - 1))
            if rng.randrange(2) == 0
            else (draw(row_split + 1, h - 2), 0)
        )
        bottom_right = (
            (h - 2, draw(col_split + 1, w - 2))
            if rng.randrange(2) == 0
            else (draw(row_split + 1, h - 2), w - 2)
        )
        return [primary, top_right, bottom_left, bottom_right]
    raise ValueError(f"unknown edge mode {edge_mode!r}")


def _canonical_profile_layout(scene_profile: str, rng) -> tuple[list[Cell], tuple[frozenset[Cell], ...]]:
    """Return a position-varied layout for one observed canonical joint profile."""
    if scene_profile == "canonical_7":
        # The first bbox touches the top edge; the second occupies the opposite
        # quadrant.  Both retain the canonical 7x7 morphology multiset.
        return [
            (0, rng.randint(0, 1)),
            (4, rng.randint(4, 5)),
        ], _CANONICAL_7_SHAPES
    if scene_profile == "canonical_9":
        # Exercise both distinct 9x9 canonical morphology multisets.  The held-
        # out branch contains an interior source cell; the training branch does
        # not, so generalized lessons retain the independent deletion witness.
        shapes = rng.choice((_CANONICAL_9_TRAIN_SHAPES, _CANONICAL_9_SHAPES))
        return [
            (rng.randint(1, 2), rng.randint(1, 2)),
            (5, 5),
        ], shapes
    raise ValueError(f"no canonical morphology layout for {scene_profile!r}")


def _contact_layout(
    h: int, w: int, n_blobs: int, edge_mode: str, rng
) -> tuple[list[Cell], tuple[frozenset[Cell], ...]]:
    """Construct observable connectivity witnesses with disjoint bbox footprints.

    A primary component ends at (2,2); the last component begins at (3,3).
    They are diagonal neighbours, and receive the repeated colour when one is
    requested.  The second component touches the primary orthogonally and has
    a different colour.  Random D4 orientation and translation preserve both
    witnesses.  An optional fourth component can occupy any free 2x2 footprint.
    """
    primary = frozenset(rng.choice(_PRIMARY_SHAPES) | {(2, 2)})
    side = rng.choice(tuple(shape for shape in _L_SHAPES if (1, 0) in shape))
    diagonal = rng.choice(tuple(shape for shape in _L_SHAPES if (0, 0) in shape))
    shapes = [primary, frozenset((r + 1, c + 3) for r, c in side)]
    if n_blobs == 4:
        shapes.append(frozenset((r + 3, c) for r, c in rng.choice(_L_SHAPES)))
    shapes.append(frozenset((r + 3, c + 3) for r, c in diagonal))

    turns, reflected = rng.randrange(4), bool(rng.randrange(2))

    def orient(cell: Cell) -> Cell:
        r, c = cell
        if reflected:
            c = 4 - c
        for _ in range(turns):
            r, c = c, 4 - r
        return r, c

    shapes = [frozenset(orient(cell) for cell in shape) for shape in shapes]
    margin = 1 if edge_mode == "interior" else 0
    ar = rng.randint(margin, h - 5 - margin)
    ac = rng.randint(margin, w - 5 - margin)
    if edge_mode == "touching":
        edge = rng.randrange(4)
        if edge == 0:
            ar = 0
        elif edge == 1:
            ar = h - 5
        elif edge == 2:
            ac = 0
        else:
            ac = w - 5
    shapes = [frozenset((r + ar, c + ac) for r, c in shape) for shape in shapes]

    if n_blobs == 4:
        # Keep a freely placed satellite instead of confining every object to
        # the contact cluster. Its colour differs from each other component.
        occupied = set()
        for index, shape in enumerate(shapes):
            if index != 2:
                rows, cols = zip(*shape)
                occupied.update(_bbox_cells((min(rows), min(cols), max(rows), max(cols))))
        candidates = [
            (r, c)
            for r in range(margin, h - 1 - margin)
            for c in range(margin, w - 1 - margin)
            if not ({(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} & occupied)
        ]
        sr, sc = rng.choice(candidates)
        shapes[2] = frozenset((r + sr, c + sc) for r, c in rng.choice(_L_SHAPES))
    return [(0, 0)] * n_blobs, tuple(shapes)


def _slot_region(h: int, w: int, slot: int) -> tuple[int, int, int, int]:
    """Inclusive region bounds with a one-cell separator between quadrants."""
    row_split, col_split = h // 2, w // 2
    regions = (
        (0, 0, row_split - 1, col_split - 1),
        (0, col_split + 1, row_split - 1, w - 1),
        (row_split + 1, 0, h - 1, col_split - 1),
        (row_split + 1, col_split + 1, h - 1, w - 1),
    )
    return regions[slot]


def _anchor_bounds(
    h: int,
    w: int,
    slot: int,
    shape: frozenset[Cell],
    edge_mode: str,
) -> tuple[int, int, int, int] | None:
    r0, c0, r1, c1 = _slot_region(h, w, slot)
    shape_h, shape_w = _shape_span(shape)
    row_lo, row_hi = r0, r1 - shape_h + 1
    col_lo, col_hi = c0, c1 - shape_w + 1
    if edge_mode == "interior":
        row_lo, row_hi = max(row_lo, 1), min(row_hi, h - shape_h - 1)
        col_lo, col_hi = max(col_lo, 1), min(col_hi, w - shape_w - 1)
    if row_lo > row_hi or col_lo > col_hi:
        return None
    return row_lo, row_hi, col_lo, col_hi


def _draw_region_anchor(
    h: int,
    w: int,
    slot: int,
    shape: frozenset[Cell],
    edge_mode: str,
    rng,
) -> Cell:
    bounds = _anchor_bounds(h, w, slot, shape, edge_mode)
    if bounds is None:
        raise RuntimeError(
            f"shape {_shape_span(shape)} does not fit slot {slot} in {h}x{w} {edge_mode} scene"
        )
    row_lo, row_hi, col_lo, col_hi = bounds
    if edge_mode == "interior":
        return rng.randint(row_lo, row_hi), rng.randint(col_lo, col_hi)

    shape_h, shape_w = _shape_span(shape)
    outer_sides = {
        0: (("top", 0), ("left", 0)),
        1: (("top", 0), ("right", w - shape_w)),
        2: (("bottom", h - shape_h), ("left", 0)),
        3: (("bottom", h - shape_h), ("right", w - shape_w)),
    }[slot]
    lawful = [
        (side, fixed)
        for side, fixed in outer_sides
        if (
            side in ("top", "bottom")
            and row_lo <= fixed <= row_hi
            or side in ("left", "right")
            and col_lo <= fixed <= col_hi
        )
    ]
    if not lawful:
        raise RuntimeError(f"no border-touching anchor for slot {slot} and shape {_shape_span(shape)}")
    side, fixed = rng.choice(lawful)
    if side in ("top", "bottom"):
        return fixed, rng.randint(col_lo, col_hi)
    return rng.randint(row_lo, row_hi), fixed


def _generalized_layout(
    scene_profile: str,
    n_blobs: int,
    edge_mode: str,
    sample_index: int,
    difficulty: Any,
    rng,
) -> list[tuple[Cell, frozenset[Cell]]]:
    """Place morphology-diverse objects in separated wide/tall scene regions."""
    h, w = _PROFILE_DIMS[scene_profile]
    slots_by_count = {2: [0, 3], 3: [0, 1, 3], 4: [0, 1, 2, 3]}
    slots = slots_by_count[n_blobs]
    primary_spans = {
        ("wide_9x13", "touching"): ((3, 5), (4, 4), (4, 3)),
        ("wide_9x13", "interior"): ((3, 5),),
        ("tall_13x9", "touching"): ((5, 3), (4, 4), (4, 3)),
        ("tall_13x9", "interior"): ((5, 3), (4, 3)),
    }[(scene_profile, edge_mode)]
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    desired_span = primary_spans[(int(sample_index) // 4 + band_offset) % len(primary_spans)]

    layout: list[tuple[Cell, frozenset[Cell]]] = []
    for position, slot in enumerate(slots):
        if position == 0:
            candidates = [
                shape
                for shape in _GENERALIZED_SHAPES_BY_SPAN[desired_span]
                if _shape_has_interior(shape)
                and _anchor_bounds(h, w, slot, shape, edge_mode) is not None
            ]
        else:
            candidates = [
                shape
                for shape in _GENERALIZED_SHAPES
                if _anchor_bounds(h, w, slot, shape, edge_mode) is not None
            ]
        if not candidates:
            raise RuntimeError(
                f"no generalized shape for {scene_profile} slot {slot} under {edge_mode}"
            )
        shape = rng.choice(candidates)
        anchor = _draw_region_anchor(h, w, slot, shape, edge_mode, rng)
        layout.append((anchor, shape))
    return layout


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides) -> Grid:
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
    cycle = int(sample_index) % 4
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, _PROFILE_SCHEDULE[cycle]
    )
    n_blobs = _scheduled_int(ctx, "n_blobs", 2, 4, _N_BLOBS_SCHEDULE[cycle])
    color_relation = _scheduled_choice(
        ctx, "color_relation", COLOR_RELATIONS, _COLOR_RELATION_SCHEDULE[cycle]
    )
    edge_mode = _scheduled_choice(
        ctx, "edge_mode", EDGE_MODES, _EDGE_MODE_SCHEDULE[cycle]
    )
    palette_kind = _scheduled_choice(
        ctx, "palette_kind", PALETTE_KINDS, _PALETTE_SCHEDULE[cycle]
    )

    h, w = _PROFILE_DIMS[scene_profile]
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng(f"layout_and_shape:{difficulty or 'default'}")
    unique_count = n_blobs if color_relation == "distinct" else n_blobs - 1
    palette = _palette(palette_kind, unique_count, rng)
    if color_relation == "distinct":
        colors = palette
    else:
        colors = [palette[0]] + palette[1:] + [palette[0]]

    use_canonical_profile = (
        n_blobs == 2
        and color_relation == "distinct"
        and (
            (scene_profile == "canonical_7" and edge_mode == "touching")
            or (scene_profile == "canonical_9" and edge_mode == "interior")
        )
    )
    if use_canonical_profile:
        selected_anchors, selected_shapes = _canonical_profile_layout(scene_profile, rng)
        placements = zip(selected_anchors, selected_shapes, colors)
    elif n_blobs >= 3 and color_relation == "one_repeat":
        # Preserve diagonal same-color and orthogonal different-color witnesses.
        selected_anchors, selected_shapes = _contact_layout(h, w, n_blobs, edge_mode, rng)
        placements = zip(selected_anchors, selected_shapes, colors)
    elif scene_profile in ("wide_9x13", "tall_13x9"):
        selected_layout = _generalized_layout(
            scene_profile,
            n_blobs,
            edge_mode,
            int(sample_index),
            difficulty,
            rng,
        )
        placements = (
            (anchor, shape, color)
            for (anchor, shape), color in zip(selected_layout, colors)
        )
    elif n_blobs >= 3:
        selected_anchors, selected_shapes = _contact_layout(h, w, n_blobs, edge_mode, rng)
        placements = zip(selected_anchors, selected_shapes, colors)
    else:
        slots_by_count = {2: [0, 3], 3: [0, 1, 3], 4: [0, 1, 2, 3]}
        anchors = _anchors(h, w, edge_mode, rng)
        selected = slots_by_count[n_blobs]
        shapes = [rng.choice(_PRIMARY_SHAPES)] + [
            rng.choice(_L_SHAPES) for _ in range(n_blobs - 1)
        ]
        placements = (
            (anchors[slot], shape, color)
            for slot, shape, color in zip(selected, shapes, colors)
        )

    for (ar, ac), shape, color in placements:
        for dr, dc in shape:
            grid[ar + dr][ac + dc] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "scene_profile": scene_profile,
        "n_blobs": n_blobs,
        "color_relation": color_relation,
        "edge_mode": edge_mode,
        "palette_kind": palette_kind,
    }
    if observed != expected:
        raise RuntimeError(
            f"internal observable-axis mismatch: expected {expected}, observed {observed}"
        )
    return grid


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Infer every exact semantic axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    profile = _DIMS_PROFILE.get((facts["height"], facts["width"]))
    if profile is None:
        return {}
    counts = facts["color_counts"]
    n_blobs = facts["n_blobs"]
    if len(counts) == n_blobs:
        relation = "distinct"
    elif len(counts) == n_blobs - 1 and sorted(counts.values()).count(2) == 1:
        relation = "one_repeat"
    else:
        return {}
    colors = set(counts)
    if colors and all(1 <= color <= 4 for color in colors):
        palette_kind = "low"
    elif colors and all(6 <= color <= 9 for color in colors):
        palette_kind = "high"
    else:
        palette_kind = "mixed"
    return {
        "scene_profile": profile,
        "n_blobs": n_blobs,
        "color_relation": relation,
        "edge_mode": "touching" if facts["touching"] else "interior",
        "palette_kind": palette_kind,
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the selected canonical Racket rule."""
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for component in _components(grid):
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = component["color"]
    return output


def semantic_signature(grid: Grid) -> dict[str, Any]:
    """Compact, deterministic evidence used by focused tests and reports."""
    observed = observe_overrides(grid)
    output = rule_mirror(grid)
    return {
        **observed,
        "adds": sum(
            grid[r][c] == 0 and output[r][c] != 0
            for r in range(len(grid))
            for c in range(len(grid[0]))
        ),
        "deletes": sum(
            grid[r][c] != 0 and output[r][c] == 0
            for r in range(len(grid))
            for c in range(len(grid[0]))
        ),
    }


# ---------------------------------------------------------------------------
# Named rival rules and task-linked witnesses
# ---------------------------------------------------------------------------


def _identity(grid: Grid) -> Grid:
    return deepcopy(grid)


def _fill_each_bbox(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        for r, c in _bbox_cells(component["bbox"]):
            output[r][c] = component["color"]
    return output


def _preserve_source_then_frame(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for component in _components(grid):
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = component["color"]
    return output


def _existing_bbox_border_only(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        border = _bbox_border(component["bbox"])
        for r, c in component["cells"] & border:
            output[r][c] = component["color"]
    return output


def _one_global_bbox(grid: Grid) -> Grid:
    components = _components(grid)
    output = full_grid(len(grid), len(grid[0]), 0)
    if not components:
        return output
    cells = set().union(*(component["cells"] for component in components))
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    color = components[0]["color"]
    for r, c in _bbox_border(bbox):
        output[r][c] = color
    return output


def _one_bbox_per_color(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    grouped: dict[int, set[Cell]] = defaultdict(set)
    for component in _components(grid):
        grouped[component["color"]].update(component["cells"])
    for color, cells in grouped.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        for r, c in _bbox_border(bbox):
            output[r][c] = color
    return output


def _fixed_color_8(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = 8
    return output


def _same_color_8_connected(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid, diagonal=True):
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = component["color"]
    return output

def _color_blind_4_connected(grid: Grid) -> Grid:
    """Merge touching foreground colours; use the first source cell's colour."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid, ignore_color=True):
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = component["color"]
    return output

def _legacy_bbox_span_lookup(grid: Grid) -> Grid:
    """Fit the former four-span distribution; preserve unseen shapes unchanged."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        r0, c0, r1, c1 = component["bbox"]
        span = (r1 - r0 + 1, c1 - c0 + 1)
        cells = (
            _bbox_border(component["bbox"])
            if span in _LEGACY_BBOX_SPANS
            else component["cells"]
        )
        for r, c in cells:
            output[r][c] = component["color"]
    return output

def _drop_border_touching_components(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for component in _components(grid):
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in component["cells"]):
            continue
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = component["color"]
    return output


def _drop_interior_components(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for component in _components(grid):
        if not any(r in (0, h - 1) or c in (0, w - 1) for r, c in component["cells"]):
            continue
        for r, c in _bbox_border(component["bbox"]):
            output[r][c] = component["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _identity,
    "solid_bbox": _fill_each_bbox,
    "preserve_source_then_frame": _preserve_source_then_frame,
    "existing_bbox_border_only": _existing_bbox_border_only,
    "one_global_bbox": _one_global_bbox,
    "one_bbox_per_color": _one_bbox_per_color,
    "fixed_color_8": _fixed_color_8,
    "same_color_8_connected": _same_color_8_connected,
    "color_blind_4_connected": _color_blind_4_connected,
    "legacy_bbox_span_lookup": _legacy_bbox_span_lookup,
    "drop_border_touching_components": _drop_border_touching_components,
    "drop_interior_components": _drop_interior_components,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Canonical components have distinct colours and are spatially separated.
# Generated contact scenes teach the distinctions absent from those examples.
CANONICAL_SHORTCUTS = {
    "one_bbox_per_color": _one_bbox_per_color,
    "same_color_8_connected": _same_color_8_connected,
    "color_blind_4_connected": _color_blind_4_connected,
}


def _witness_adds_missing_border(grid: Grid) -> bool:
    output = rule_mirror(grid)
    return any(
        grid[r][c] == 0 and output[r][c] != 0
        for r in range(len(grid))
        for c in range(len(grid[0]))
    )


def _witness_erases_interior(grid: Grid) -> bool:
    output = rule_mirror(grid)
    return any(
        grid[r][c] != 0 and output[r][c] == 0
        for r in range(len(grid))
        for c in range(len(grid[0]))
    )


def _witness_multiple_components(grid: Grid) -> bool:
    return len(_components(grid)) >= 2


def _witness_repeated_color(grid: Grid) -> bool:
    counts = Counter(component["color"] for component in _components(grid))
    return any(count >= 2 for count in counts.values())


def _witness_novel_bbox_span(grid: Grid) -> bool:
    return any(
        (
            component["bbox"][2] - component["bbox"][0] + 1,
            component["bbox"][3] - component["bbox"][1] + 1,
        )
        not in _LEGACY_BBOX_SPANS
        for component in _components(grid)
    )


def _witness_touches_border(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["facts"]["touching"])


def _witness_fully_interior(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and not analysis["facts"]["touching"]


def _witness_same_color_diagonal_contact(grid: Grid) -> bool:
    return _same_color_8_connected(grid) != rule_mirror(grid)


def _witness_different_color_orthogonal_contact(grid: Grid) -> bool:
    return _color_blind_4_connected(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "adds_missing_bbox_border_cells": _witness_adds_missing_border,
    "erases_source_cells_inside_bbox": _witness_erases_interior,
    "frames_components_separately": _witness_multiple_components,
    "same_color_components_stay_separate": _witness_repeated_color,
    "component_bbox_spans_generalize": _witness_novel_bbox_span,
    "border_touching_components_are_processed": _witness_touches_border,
    "interior_components_are_processed": _witness_fully_interior,
    "diagonal_same_color_components_stay_separate": _witness_same_color_diagonal_contact,
    "touching_different_colors_stay_separate": _witness_different_color_orthogonal_contact,
}

WITNESS_RIVALS = {
    "adds_missing_bbox_border_cells": ["identity", "existing_bbox_border_only"],
    "erases_source_cells_inside_bbox": ["preserve_source_then_frame", "solid_bbox"],
    "frames_components_separately": ["one_global_bbox"],
    "same_color_components_stay_separate": ["one_bbox_per_color"],
    "component_bbox_spans_generalize": ["legacy_bbox_span_lookup"],
    "border_touching_components_are_processed": ["drop_border_touching_components"],
    "interior_components_are_processed": ["drop_interior_components"],
    "diagonal_same_color_components_stay_separate": ["same_color_8_connected"],
    "touching_different_colors_stay_separate": ["color_blind_4_connected"],
}


def lesson_identifiable(demos: list[dict[str, Grid]], query: dict[str, Grid]) -> list[str]:
    """Require a four-demo lesson that falsifies every declared competitor."""
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        errors.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, observed {len(demos)}"
        )

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        structural = self_check(pair["input"])
        if structural:
            errors.append(f"demo {index} input rejected: {structural[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            errors.append(f"demo {index} output does not match the bbox-outline rule")

    if isinstance(query, dict) and "input" in query and "output" in query:
        query_errors = self_check(query["input"])
        if query_errors:
            errors.append(f"query input rejected: {query_errors[0]}")
        elif query["output"] != rule_mirror(query["input"]):
            errors.append("query output does not match the bbox-outline rule")
    else:
        errors.append("query must contain input and output grids")

    # Validation errors must not flow into rivals. Schedule-axis coverage is a
    # sampler property, not a requirement for an otherwise identifying lesson.
    # In particular, self_check accepts lawful sizes outside observe_overrides.
    if errors:
        return errors
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} survives every demonstration")

    return errors
