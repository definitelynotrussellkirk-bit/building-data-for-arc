"""Generator for ARC task ea763f9c5b1d — recolor components by area parity.

Every nonzero 4-connected component is recolored independently: odd area to
3, even area to 4.  Inputs use one foreground color on a zero background and
always contain both parities.

A default-only linked canonical prior retains the five demonstrated
height/width/color/component-morphology profiles.  The generalized branch
varies dimensions, foreground color, component count, size, shape, and
placement while keeping every declared override exact.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ea763f9c5b1d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "17fac2286cd5"
SUMMARY = (
    "Two to five separated same-color components on background 0; recolor "
    "each 4-connected component by its cell-count parity (odd -> 3, even -> 4)."
)

INVARIANTS = [
    "canvas is 7..14 rows by 8..14 columns and uses ARC colors 0..9",
    "0 is the strictly modal background and exactly one nonzero input color is used",
    "there are exactly 2..5 nonzero 4-connected components",
    "every component has area 2..7",
    "at least one component has odd area and at least one has even area",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted draw over the full valid range",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted draw over the full valid range",
        "valid": "8..14",
    },
    "n_blobs": {
        "type": "int",
        "default": "difficulty-weighted draw over the full valid range",
        "valid": "2..5",
    },
    "input_color": {
        "type": "color",
        "default": "one keyed nonzero ARC color",
        "valid": "1..9",
    },
}

_CANONICAL_PRIOR_P = 0.30

# Complete linked profiles extracted from all four train inputs plus the held-
# out test input.  Each entry is (height, width, component-cell tuples).  The
# prior keeps a whole entry together; it never recombines dimensions and
# morphologies from different official examples.  Translation within the
# one-cell interior margin and whole-grid reflections are nuisance variation.
_CANONICAL_PROFILES = (
    (
        10,
        12,
        (
            ((1, 1), (2, 1), (3, 1), (3, 2)),
            ((1, 7), (2, 6), (2, 7), (2, 8)),
            ((5, 4), (6, 3), (6, 4), (6, 5), (7, 4)),
        ),
    ),
    (
        9,
        11,
        (
            ((1, 1), (1, 2), (2, 1), (2, 2)),
            ((2, 6), (3, 6), (3, 7), (4, 7), (4, 8)),
            ((6, 2), (7, 2), (7, 3)),
        ),
    ),
    (
        10,
        10,
        (
            ((1, 4), (1, 5), (2, 4), (2, 5), (3, 4), (3, 5)),
            ((5, 7), (6, 6), (6, 7), (6, 8), (7, 7)),
            ((6, 1), (7, 1), (7, 2), (8, 2)),
        ),
    ),
    (
        9,
        12,
        (
            ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1)),
            ((2, 8), (2, 9), (3, 8), (3, 9)),
            ((6, 5), (6, 6), (6, 7)),
        ),
    ),
    (
        10,
        12,
        (
            ((1, 7), (1, 9), (2, 7), (2, 8), (2, 9)),
            ((5, 1), (6, 1), (7, 1), (7, 2)),
            ((6, 7), (7, 7), (7, 8), (8, 8), (8, 9)),
        ),
    ),
)

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _analyze(grid) -> dict | None:
    """Recover all rule-relevant facts from the returned grid itself."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return None
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None

    colors = sorted({value for row in grid for value in row if value != 0})
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in _DIR4:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < h
                        and 0 <= next_col < w
                        and grid[next_row][next_col] != 0
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(tuple(sorted(cells)))

    nonzero = sum(len(component) for component in components)
    zero_count = h * w - nonzero
    component_index = {
        cell: index
        for index, component in enumerate(components)
        for cell in component
    }
    diagonal_contacts = 0
    for (row, col), index in component_index.items():
        for delta_row, delta_col in _DIR8_DIAGONAL:
            neighbor = (row + delta_row, col + delta_col)
            other = component_index.get(neighbor)
            if other is not None and other != index:
                diagonal_contacts += 1
    diagonal_contacts //= 2

    return {
        "h": h,
        "w": w,
        "colors": tuple(colors),
        "components": tuple(components),
        "sizes": tuple(sorted(len(component) for component in components)),
        "nonzero": nonzero,
        "zero_count": zero_count,
        "background_modal": zero_count > nonzero,
        "all_interior": all(
            0 < row < h - 1 and 0 < col < w - 1
            for component in components
            for row, col in component
        ),
        "diagonal_contacts": diagonal_contacts,
    }


def _normalize_shape(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    """Canonicalize a component up to all D4 rotations/reflections."""
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    base = [(row - min_row, col - min_col) for row, col in cells]
    variants = []
    for swap in (False, True):
        for sign_row in (-1, 1):
            for sign_col in (-1, 1):
                transformed = []
                for row, col in base:
                    first, second = (col, row) if swap else (row, col)
                    transformed.append((sign_row * first, sign_col * second))
                top = min(row for row, _ in transformed)
                left = min(col for _, col in transformed)
                variants.append(
                    tuple(sorted((row - top, col - left) for row, col in transformed))
                )
    return min(variants)


def canonical_profile_signature(grid):
    """Return the linked empirical-manifold signature used by the audit.

    Absolute placement and orientation are nuisance variation because the rule
    is translation/D4 invariant.  Dimensions, palette, component count, exact
    component morphology (up to D4), interior placement, and absence of
    diagonal inter-component contact stay linked.
    """
    facts = _analyze(grid)
    if facts is None or len(facts["colors"]) != 1:
        return None
    return (
        facts["h"],
        facts["w"],
        facts["colors"][0],
        tuple(sorted(_normalize_shape(component) for component in facts["components"])),
        facts["all_interior"],
        facts["diagonal_contacts"],
    )


def _profile_grid(profile, color: int = 6) -> list[list[int]]:
    h, w, components = profile
    grid = full_grid(h, w, 0)
    for component in components:
        for row, col in component:
            grid[row][col] = color
    return grid


_CANONICAL_SIGNATURES = frozenset(
    canonical_profile_signature(_profile_grid(profile))
    for profile in _CANONICAL_PROFILES
)


def _canonical_variant(profile, rng) -> list[list[int]]:
    """Reflect and jointly translate one whole official linked profile."""
    h, w, components = profile
    transform = rng.randrange(4)
    transformed_components = []
    for component in components:
        transformed = []
        for row, col in component:
            if transform & 1:
                col = w - 1 - col
            if transform & 2:
                row = h - 1 - row
            transformed.append((row, col))
        transformed_components.append(transformed)

    all_cells = [cell for component in transformed_components for cell in component]
    min_row = min(row for row, _ in all_cells)
    max_row = max(row for row, _ in all_cells)
    min_col = min(col for _, col in all_cells)
    max_col = max(col for _, col in all_cells)
    box_h = max_row - min_row + 1
    box_w = max_col - min_col + 1

    row_lo = 1 if box_h <= h - 2 else 0
    row_hi = h - box_h - (1 if box_h <= h - 2 else 0)
    col_lo = 1 if box_w <= w - 2 else 0
    col_hi = w - box_w - (1 if box_w <= w - 2 else 0)
    target_top = rng.randint(row_lo, row_hi)
    target_left = rng.randint(col_lo, col_hi)
    row_shift = target_top - min_row
    col_shift = target_left - min_col

    grid = full_grid(h, w, 0)
    for component in transformed_components:
        for row, col in component:
            grid[row + row_shift][col + col_shift] = 6
    return grid


def _balanced_spans(length: int, parts: int, rng) -> list[tuple[int, int]]:
    """Partition an axis into positive spans separated by one blank line."""
    usable = length - (parts - 1)
    if usable < parts:
        raise ValueError(f"cannot partition length={length} into {parts} slots")
    base, remainder = divmod(usable, parts)
    sizes = [base] * parts
    order = list(range(parts))
    rng.shuffle(order)
    for index in order[:remainder]:
        sizes[index] += 1

    spans = []
    start = 0
    for size in sizes:
        spans.append((start, start + size))
        start += size + 1
    return spans


def _component_slots(h: int, w: int, count: int, rng) -> list[tuple[int, int, int, int]]:
    """Create `count` non-4-touching rectangular placement slots."""
    if count == 2:
        row_parts, col_parts = ((1, 2) if w >= h else (2, 1))
    elif count in (3, 4):
        row_parts, col_parts = 2, 2
    elif count == 5:
        row_parts, col_parts = ((2, 3) if w >= h else (3, 2))
    else:
        raise ValueError(f"unsupported component count {count}")

    row_spans = _balanced_spans(h, row_parts, rng)
    col_spans = _balanced_spans(w, col_parts, rng)
    slots = [
        (row_start, row_end, col_start, col_end)
        for row_start, row_end in row_spans
        for col_start, col_end in col_spans
    ]
    rng.shuffle(slots)
    return slots[:count]


def _choose_sizes(rng, capacities: list[int], canvas_area: int) -> list[int]:
    """Choose 2..7 cell areas with guaranteed mixed parity and sparse fill."""
    maxima = [min(7, capacity) for capacity in capacities]
    if any(maximum < 2 for maximum in maxima):
        raise ValueError(f"placement slot cannot hold a two-cell component: {capacities}")

    odd_candidates = [index for index, maximum in enumerate(maxima) if maximum >= 3]
    if not odd_candidates:
        raise ValueError("no placement slot can hold an odd component")
    odd_index = rng.choice(odd_candidates)
    even_index = rng.choice([index for index in range(len(maxima)) if index != odd_index])

    sizes = [2] * len(maxima)
    sizes[odd_index] = 3
    minimum_total = sum(sizes)
    maximum_total = min(sum(maxima), max(minimum_total, canvas_area // 4))
    target_total = rng.randint(minimum_total, maximum_total)

    while sum(sizes) < target_total:
        current_total = sum(sizes)
        choices = []
        for index, maximum in enumerate(maxima):
            step = 2 if index in (odd_index, even_index) else 1
            if sizes[index] + step <= maximum and current_total + step <= target_total:
                choices.append((index, step))
        if not choices:
            break
        index, step = rng.choice(choices)
        sizes[index] += step

    return sizes


def _connected_cells(rng, slot: tuple[int, int, int, int], size: int):
    """Grow an exact-size connected polyomino inside a rectangular slot."""
    row_start, row_end, col_start, col_end = slot
    start = (rng.randrange(row_start, row_end), rng.randrange(col_start, col_end))
    cells = {start}
    frontier: set[tuple[int, int]] = set()

    def add_frontier(row: int, col: int) -> None:
        for delta_row, delta_col in _DIR4:
            next_row = row + delta_row
            next_col = col + delta_col
            candidate = (next_row, next_col)
            if (
                row_start <= next_row < row_end
                and col_start <= next_col < col_end
                and candidate not in cells
            ):
                frontier.add(candidate)

    add_frontier(*start)
    while len(cells) < size:
        if not frontier:
            raise RuntimeError("connected slot growth exhausted before target size")
        cell = rng.choice(sorted(frontier))
        frontier.remove(cell)
        cells.add(cell)
        add_frontier(*cell)
    return tuple(sorted(cells))


def observe_overrides(grid) -> dict:
    """Recover every declared exact axis from the returned grid (KRF-0002)."""
    facts = _analyze(grid)
    if facts is None:
        return {}
    return {
        "grid_h": facts["h"],
        "grid_w": facts["w"],
        "n_blobs": len(facts["components"]),
        "input_color": facts["colors"][0] if len(facts["colors"]) == 1 else None,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full executable input grammar without mutating `grid`."""
    facts = _analyze(grid)
    if facts is None:
        return ["grid must be a nonempty rectangular ARC integer matrix"]

    errors: list[str] = []
    h, w = facts["h"], facts["w"]
    if not 7 <= h <= 14:
        errors.append(f"grid height {h} outside declared 7..14 range")
    if not 8 <= w <= 14:
        errors.append(f"grid width {w} outside declared 8..14 range")
    if len(facts["colors"]) != 1:
        errors.append(f"expected exactly one nonzero input color, found {facts['colors']}")
    if not facts["background_modal"]:
        errors.append("background 0 must be strictly more frequent than foreground cells")

    count = len(facts["components"])
    if not 2 <= count <= 5:
        errors.append(f"expected 2..5 separated components, found {count}")
    if any(size < 2 or size > 7 for size in facts["sizes"]):
        errors.append(f"component areas outside intended 2..7 range: {facts['sizes']}")
    if not any(size % 2 for size in facts["sizes"]):
        errors.append("no odd-area component present")
    if not any(size % 2 == 0 for size in facts["sizes"]):
        errors.append("no even-area component present")

    if isinstance(meta, dict):
        observed = observe_overrides(grid)
        for key in ("grid_h", "grid_w", "n_blobs", "input_color"):
            if key in meta and meta[key] is not None and observed.get(key) != meta[key]:
                errors.append(
                    f"meta override {key}={meta[key]!r} realized as {observed.get(key)!r}"
                )
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for focused tests and audits."""
    facts = _analyze(grid)
    if facts is None:
        raise ValueError("invalid ARC grid")
    output = full_grid(facts["h"], facts["w"], 0)
    for component in facts["components"]:
        color = 3 if len(component) % 2 else 4
        for row, col in component:
            output[row][col] = color
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    band = difficulty or "medium"
    if band not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=dict(overrides),
    )

    # Default-only complete linked-profile prior (KRF-0003).  Explicit caller
    # controls bypass it, so no prior branch can make an override inert.  Final
    # exact values are still recorded through each declared typed axis
    # (KRF-0004), and the observer recovers the same values from the grid.
    if not overrides and ctx.draw_rng(f"canonical_prior|{band}").random() < _CANONICAL_PRIOR_P:
        profile = ctx.draw_rng(f"canonical_profile|{band}").choice(_CANONICAL_PROFILES)
        h, w, _ = profile
        ctx.overrides.update(
            {"grid_h": h, "grid_w": w, "n_blobs": 3, "input_color": 6}
        )
        ctx.draw_int("grid_h", 7, 14)
        ctx.draw_int("grid_w", 8, 14)
        ctx.draw_int("n_blobs", 2, 5)
        ctx.draw_color("input_color", exclude={0})
        return _canonical_variant(profile, ctx.draw_rng(f"canonical_layout|{band}"))

    # Difficulty influences the default draw distribution while exact caller
    # overrides remain valid over the full declared range in every band.
    h = ctx.draw_int_diff("grid_h", 7, 14)
    w = ctx.draw_int_diff("grid_w", 8, 14)
    count = ctx.draw_int_diff("n_blobs", 2, 5)
    color = ctx.draw_color("input_color", exclude={0})

    layout_rng = ctx.draw_rng("layout")
    slots = _component_slots(h, w, count, layout_rng)
    capacities = [
        (row_end - row_start) * (col_end - col_start)
        for row_start, row_end, col_start, col_end in slots
    ]
    sizes = _choose_sizes(layout_rng, capacities, h * w)

    grid = full_grid(h, w, 0)
    for slot, size in zip(slots, sizes):
        for row, col in _connected_cells(layout_rng, slot, size):
            grid[row][col] = color
    return grid
