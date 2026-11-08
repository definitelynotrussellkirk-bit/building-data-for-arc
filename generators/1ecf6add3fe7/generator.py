"""Generator for H107 — dispatch the query shape to its prototype label.

The input contains three equal-width panels separated by full-height color-5
columns.  The first two panels are labeled prototypes: their local (0, 0)
cell is a label color and their color-1 cells are shapes.  The third panel is
an unlabeled query shape.  Exactly one prototype is dihedrally equivalent to
the query.  The canonical Racket oracle returns the query panel with its shape
recolored to the matching prototype's label.

Normal draws deliberately include equal-area decoys, both match sides, varied
positions, varied canvas sizes, and all D4 orientations.  Equal-area decoys are
important: they make a count-only shortcut insufficient.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ecf6add3fe7"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9be86eb85768"

SUMMARY = (
    "Split the grid into three equal panels at the two full-height color-5 "
    "separators. Match the third panel's color-1 query shape to exactly one of "
    "the first two color-1 prototype shapes up to rotation/reflection, then "
    "recolor the query cells with that prototype's top-left label color."
)

INVARIANTS = [
    "background is 0; prototype/query shape cells are 1; separators are 5",
    "width is 3*panel_w+2 with full-height separators at panel_w and 2*panel_w+1",
    "the first two local (0,0) cells are distinct labels outside {0,1,5}",
    "all other row-0 panel cells are 0, including the query local (0,0)",
    "each panel contains one nonempty 4-connected shape below row 0",
    "exactly one prototype shape is D4-equivalent to the query",
]

# These are exact, recoverable properties of every returned default grid.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware; canonical prior", "valid": "5..9"},
    "panel_w": {"type": "int", "default": "difficulty-aware; canonical prior", "valid": "4..7"},
    "base_size": {"type": "int", "default": "difficulty-aware; canonical prior", "valid": "3..8"},
    "decoy_size": {"type": "int", "default": "difficulty-aware; canonical prior", "valid": "3..8"},
    "match_side": {"type": "int", "default": "balanced", "valid": "0|1"},
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_LABELS = (2, 3, 4, 6, 7, 8, 9)


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _orient(cells, code):
    transformed = []
    for r, c in cells:
        if code == 0:       # identity
            transformed.append((r, c))
        elif code == 1:     # rotate clockwise
            transformed.append((c, -r))
        elif code == 2:     # rotate 180
            transformed.append((-r, -c))
        elif code == 3:     # rotate counter-clockwise
            transformed.append((-c, r))
        elif code == 4:     # left-right reflection
            transformed.append((r, -c))
        elif code == 5:     # up-down reflection
            transformed.append((-r, c))
        elif code == 6:     # transpose
            transformed.append((c, r))
        elif code == 7:     # anti-transpose
            transformed.append((-c, -r))
        else:
            raise ValueError(f"orientation code outside 0..7: {code}")
    return _normalize(transformed)


def _d4_variants(cells):
    return {_orient(cells, code) for code in range(8)}


def _bbox_shape(cells):
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _fits(cells, max_h, max_w):
    shape_h, shape_w = _bbox_shape(cells)
    return shape_h <= max_h and shape_w <= max_w


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _random_polyomino(rng, size):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARDINAL)
        nxt = (r + dr, c + dc)
        if nxt not in seen:
            cells.append(nxt)
            seen.add(nxt)
    return _normalize(cells)


def _draw_shape(rng, size, max_h, max_w, *, forbidden_variants=frozenset()):
    """Draw a fitting connected shape outside a forbidden D4 orbit."""
    for _ in range(1200):
        shape = _random_polyomino(rng, size)
        # Prefer asymmetric shapes where possible so all eight transformations
        # are genuinely distinguishable. Size-three shapes necessarily have
        # symmetry, so their canonical L/line cases remain allowed.
        if size >= 4 and len(_d4_variants(shape)) < 8 and rng.random() < 0.9:
            continue
        if shape in forbidden_variants or not _fits(shape, max_h, max_w):
            continue
        return shape
    raise ValueError(
        f"could not draw a size-{size} shape fitting {max_h}x{max_w} "
        "outside the forbidden D4 orbit"
    )


def _panel_shape(grid, left, panel_w, *, reference):
    h = len(grid)
    label = grid[0][left] if reference else 0
    cells = []
    errors = []
    for r in range(h):
        for c in range(panel_w):
            value = grid[r][left + c]
            if reference and r == 0 and c == 0:
                continue
            if value == 1:
                cells.append((r, c))
            elif value != 0:
                errors.append(
                    f"unexpected color {value} at panel-local ({r},{c}); "
                    "only color-1 shape cells are allowed"
                )
    return label, tuple(cells), errors


def analyze_grid(grid):
    """Return a structural/semantic parse used by self_check and focused tests."""
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-grid value"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged grid"]}
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC limit: {h}x{w}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    if (w - 2) % 3:
        errors.append(f"width {w} is not 3*panel_w+2")
        return {"errors": errors}
    panel_w = (w - 2) // 3
    if panel_w < 1:
        errors.append(f"invalid panel width {panel_w}")
        return {"errors": errors}

    gap_cols = (panel_w, 2 * panel_w + 1)
    for gap_col in gap_cols:
        if any(grid[r][gap_col] != 5 for r in range(h)):
            errors.append(f"separator column {gap_col} is not full-height color 5")
    for r in range(h):
        for c in range(w):
            if c not in gap_cols and grid[r][c] == 5:
                errors.append(f"separator color 5 leaked outside gap columns at ({r},{c})")
                break

    bases = (0, panel_w + 1, 2 * panel_w + 2)
    labels = []
    shapes = []
    for index, left in enumerate(bases):
        label, cells, panel_errors = _panel_shape(
            grid, left, panel_w, reference=index < 2
        )
        labels.append(label)
        shapes.append(cells)
        errors.extend(f"panel {index}: {message}" for message in panel_errors)

    if labels[0] in {0, 1, 5} or labels[1] in {0, 1, 5}:
        errors.append(f"prototype labels must be outside {{0,1,5}}, got {labels[:2]}")
    if labels[0] == labels[1]:
        errors.append("prototype labels must be distinct")
    if grid[0][bases[2]] != 0:
        errors.append("query local (0,0) must be 0")
    for index, (left, cells) in enumerate(zip(bases, shapes)):
        if not cells:
            errors.append(f"panel {index} has no shape cells")
            continue
        if any(r == 0 for r, _ in cells):
            errors.append(f"panel {index} shape touches reserved label row 0")
        normalized = _normalize(cells)
        if not _connected(normalized):
            errors.append(f"panel {index} shape is not 4-connected")

    normalized_shapes = tuple(_normalize(cells) for cells in shapes)
    match_flags = (
        normalized_shapes[2] in _d4_variants(normalized_shapes[0]) if shapes[0] and shapes[2] else False,
        normalized_shapes[2] in _d4_variants(normalized_shapes[1]) if shapes[1] and shapes[2] else False,
    )
    if sum(match_flags) != 1:
        errors.append(
            "query must match exactly one prototype up to D4; "
            f"match flags are {match_flags}"
        )
    match_side = match_flags.index(True) if sum(match_flags) == 1 else None
    base_size = len(shapes[match_side]) if match_side is not None else None
    decoy_size = len(shapes[1 - match_side]) if match_side is not None else None
    transform_candidates = []
    if match_side is not None:
        transform_candidates = [
            code for code in range(8)
            if _orient(normalized_shapes[match_side], code) == normalized_shapes[2]
        ]

    selected_label = labels[match_side] if match_side is not None else None
    expected_output = full_grid(h, panel_w, 0)
    if selected_label is not None:
        for r, c in shapes[2]:
            expected_output[r][c] = selected_label

    return {
        "errors": errors,
        "grid_h": h,
        "panel_w": panel_w,
        "gap_cols": gap_cols,
        "labels": tuple(labels[:2]),
        "shapes": tuple(shapes),
        "normalized_shapes": normalized_shapes,
        "match_flags": match_flags,
        "match_side": match_side,
        "base_size": base_size,
        "decoy_size": decoy_size,
        "same_size_decoy": base_size == decoy_size if match_side is not None else None,
        "transform_candidates": tuple(transform_candidates),
        "expected_output": expected_output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(analyze_grid(grid)["errors"])


def observe_overrides(grid):
    info = analyze_grid(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": info["grid_h"],
        "panel_w": info["panel_w"],
        "base_size": info["base_size"],
        "decoy_size": info["decoy_size"],
        "match_side": info["match_side"],
    }


def rule_mirror(grid):
    """Independent Python transcription for tests; Racket remains authority."""
    info = analyze_grid(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["expected_output"]]


def _band_bounds(difficulty):
    if difficulty == "easy":
        return (5, 6), (4, 5), (3, 5)
    if difficulty == "hard":
        return (5, 9), (5, 7), (3, 8)
    return (5, 8), (4, 6), (3, 7)


def _draw_axis(ctx, label, default_bounds, global_bounds, overrides):
    bounds = global_bounds if overrides.get(label) is not None else default_bounds
    return ctx.draw_int(label, *bounds)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes are {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_bounds, pw_bounds, size_bounds = _band_bounds(difficulty)

    # A default-only prior preserves the official 5x17 presentation frequently,
    # while the general path supplies larger canvases and shapes. Every selected
    # value is still recorded as the exact keyed axis value.
    use_canonical_prior = (
        not overrides and ctx.draw_rng("canonical_prior").random() < 0.30
    )
    if use_canonical_prior:
        h = ctx.draw_int("grid_h", 5, 5)
        panel_w = ctx.draw_int("panel_w", 5, 5)
        base_size, decoy_size = ctx.draw_choice(
            "canonical_size_pair",
            ((3, 4), (4, 3), (4, 4), (5, 4)),
        )
        # Record the two recoverable axes under their declared labels.
        ctx.draw_int("base_size", base_size, base_size)
        ctx.draw_int("decoy_size", decoy_size, decoy_size)
    else:
        h = _draw_axis(ctx, "grid_h", h_bounds, (5, 9), overrides)
        panel_w = _draw_axis(ctx, "panel_w", pw_bounds, (4, 7), overrides)
        base_size = _draw_axis(ctx, "base_size", size_bounds, (3, 8), overrides)
        decoy_size = _draw_axis(ctx, "decoy_size", size_bounds, (3, 8), overrides)
    match_side = ctx.draw_int("match_side", 0, 1)

    max_shape_h, max_shape_w = h - 1, panel_w
    shape_rng = ctx.draw_rng("matching_shape")
    transform_rng = ctx.draw_rng("shape_orientations")
    decoy_rng = ctx.draw_rng("decoy_shape")

    for _ in range(240):
        base = _draw_shape(shape_rng, base_size, max_shape_h, max_shape_w)
        ref_shape = _orient(base, transform_rng.randrange(8))
        query_shape = _orient(ref_shape, transform_rng.randrange(8))
        if not (_fits(ref_shape, max_shape_h, max_shape_w)
                and _fits(query_shape, max_shape_h, max_shape_w)):
            continue
        decoy = _draw_shape(
            decoy_rng,
            decoy_size,
            max_shape_h,
            max_shape_w,
            forbidden_variants=frozenset(_d4_variants(ref_shape)),
        )
        decoy = _orient(decoy, transform_rng.randrange(8))
        if not _fits(decoy, max_shape_h, max_shape_w):
            continue
        if query_shape in _d4_variants(decoy):
            continue
        break
    else:
        raise ValueError(
            "could not realize a unique-match panel lesson for the requested "
            f"axes h={h}, panel_w={panel_w}, base_size={base_size}, "
            f"decoy_size={decoy_size}, match_side={match_side}"
        )

    grid = full_grid(h, 3 * panel_w + 2, 0)
    gap_cols = (panel_w, 2 * panel_w + 1)
    for r in range(h):
        for c in gap_cols:
            grid[r][c] = 5

    label_rng = ctx.draw_rng("labels")
    left_label, right_label = label_rng.sample(_LABELS, 2)
    labels = (left_label, right_label)
    bases = (0, panel_w + 1, 2 * panel_w + 2)
    reference_shapes = (
        ref_shape if match_side == 0 else decoy,
        ref_shape if match_side == 1 else decoy,
    )
    placement_rng = ctx.draw_rng("placements")

    def place(panel_left, shape, label=None):
        shape_h, shape_w = _bbox_shape(shape)
        top = placement_rng.randint(1, h - shape_h)
        left = placement_rng.randint(0, panel_w - shape_w)
        if label is not None:
            grid[0][panel_left] = label
        for r, c in shape:
            grid[top + r][panel_left + left + c] = 1

    place(bases[0], reference_shapes[0], labels[0])
    place(bases[1], reference_shapes[1], labels[1])
    place(bases[2], query_shape)

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"constructed invalid lesson: {errors}")
    return grid
