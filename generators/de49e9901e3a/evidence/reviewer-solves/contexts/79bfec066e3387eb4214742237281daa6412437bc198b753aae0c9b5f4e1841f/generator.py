"""Generator for bank puzzle M33: close every monochrome 4-connected object.

The selected Racket authority takes the Cartesian product of each object's
occupied rows and occupied columns.  Because ``objects`` is monochrome and
4-connected, both coordinate projections are contiguous, so this is exactly the
object's filled bounding rectangle.  The sampler keeps canonical-like cross
objects but guarantees a non-cross witness that refutes the strongest simple
canonical shortcut: "only complete objects made from one full row and one full
column".
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "de49e9901e3a"
TASK_ID = GENERATOR_ID
RULE_HASH = "1f198bb08b3a"
VERSION = "2.0.0"
SUMMARY = (
    "Replace every monochrome 4-connected object by its same-color filled "
    "bounding rectangle. This is equivalent to the authority's occupied-row × "
    "occupied-column closure because a 4-connected object's row and column "
    "projections cannot contain gaps."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "2..4 monochrome 4-connected objects on background 0",
    "one or two nonzero colors; same-color objects remain cardinally separate",
    "every object has a 2x2, 2x3, 3x2, or 3x3 bbox and is not already rectangular",
    "object bounding boxes are disjoint",
    "every generated input contains a non-cross object that refutes the canonical-fitting cross-only rival",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile curriculum; otherwise difficulty-weighted", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "canonical-profile curriculum; otherwise difficulty-weighted", "valid": "8..18"},
    "n_objects": {"type": "int", "default": "2 canonical/easy, 3 medium, 4 hard", "valid": "2..4"},
    "n_colors": {"type": "int", "default": "2 canonical-like; otherwise 1..2", "valid": "1..2"},
}
# Every advertised joint combination is constructive, including 8x8/4 objects.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CANONICAL_DIMS = ((9, 10), (10, 10), (8, 11), (9, 9))
_INT_AXES = {
    "grid_h": (8, 18),
    "grid_w": (8, 18),
    "n_objects": (2, 4),
    "n_colors": (1, 2),
}
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _validate_controls(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, string, or None)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_request(difficulty, overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = _INT_AXES[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name, lo, hi, preferred, *, weight):
    """Draw over the full public domain while strongly preserving a curriculum anchor."""
    options = list(range(lo, hi + 1)) + [preferred] * weight
    return ctx.draw_choice(name, options)


def _profile_defaults(sample_index, difficulty, ctx):
    # Four of every five sample positions preserve exact canonical dimension and
    # palette profiles in every difficulty band. The fifth is deliberately broad.
    canonical_profile = sample_index % 5 != 4
    if canonical_profile:
        h, w = _CANONICAL_DIMS[sample_index % len(_CANONICAL_DIMS)]
        return h, w, 2, 2, 256

    broad_h = {"easy": 9, "medium": 13, "hard": 17}.get(difficulty, 12)
    broad_w = {"easy": 9, "medium": 13, "hard": 17}.get(difficulty, 12)
    broad_objects = {"easy": 2, "medium": 3, "hard": 4}.get(difficulty, 3)
    broad_colors = ctx.draw_choice("broad_n_colors", (1, 2))
    return broad_h, broad_w, broad_objects, broad_colors, 12


def _zones(length):
    """Two bands of length >=3 separated by an unused middle coordinate."""
    gap = length // 2
    return ((0, gap - 1), (gap + 1, length - 1))


def _pick_bbox(rng, row_zone, col_zone, *, witness):
    if witness:
        box_h = box_w = 3
    else:
        box_h, box_w = rng.choice(((3, 3), (3, 2), (2, 3), (2, 2)))
    r0 = rng.randint(row_zone[0], row_zone[1] - box_h + 1)
    c0 = rng.randint(col_zone[0], col_zone[1] - box_w + 1)
    return r0, c0, box_h, box_w


def _cross_cells(height, width, rng):
    """One complete local row union one complete local column."""
    bar_row = rng.randrange(height)
    bar_col = rng.randrange(width)
    return ({(bar_row, c) for c in range(width)} |
            {(r, bar_col) for r in range(height)})


def _transform_square(cells, turn, reflect):
    transformed = set(cells)
    if reflect:
        transformed = {(r, 2 - c) for r, c in transformed}
    for _ in range(turn):
        transformed = {(c, 2 - r) for r, c in transformed}
    return transformed


def _stair_cells(rng):
    """A 3x3 connected witness not expressible as one full row plus one full column."""
    base = {(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}
    return _transform_square(base, rng.randrange(4), bool(rng.randrange(2)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index)
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_objects, default_colors, weight = _profile_defaults(
        sample_index, difficulty, ctx
    )
    h = _draw_axis(ctx, "grid_h", 8, 18, default_h, weight=weight)
    w = _draw_axis(ctx, "grid_w", 8, 18, default_w, weight=weight)
    n_objects = _draw_axis(ctx, "n_objects", 2, 4, default_objects, weight=weight)
    n_colors = _draw_axis(ctx, "n_colors", 1, 2, default_colors, weight=weight)

    layout_rng = ctx.draw_rng("layout")
    slots = [(rz, cz) for rz in _zones(h) for cz in _zones(w)]
    layout_rng.shuffle(slots)

    palette = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(palette)
    palette = palette[:n_colors]

    grid = full_grid(h, w, 0)
    for index, (row_zone, col_zone) in enumerate(slots[:n_objects]):
        witness = index == 0
        r0, c0, box_h, box_w = _pick_bbox(
            layout_rng, row_zone, col_zone, witness=witness
        )
        local_cells = _stair_cells(layout_rng) if witness else _cross_cells(
            box_h, box_w, layout_rng
        )
        color = palette[index % n_colors]
        for dr, dc in local_cells:
            grid[r0 + dr][c0 + dc] = color
    return grid


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, frozenset(cells)))
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cells(cells):
    r0, c0, r1, c1 = _bbox(cells)
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def _is_row_column_cross(cells):
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    for bar_row in rows:
        for bar_col in cols:
            candidate = ({(bar_row, c) for c in cols} |
                         {(r, bar_col) for r in rows})
            if candidate == set(cells):
                return True
    return False


def _rule_bbox_fill(grid):
    """Independent Python mirror of the selected row×column-closure authority."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        for r, c in _bbox_cells(cells):
            output[r][c] = color
    return output


def _rival_cross_only(grid):
    """Canonical-fitting shortcut: complete only one-row/one-column crosses."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in _components(grid):
        painted = _bbox_cells(cells) if _is_row_column_cross(cells) else set(cells)
        for r, c in painted:
            output[r][c] = color
    return output


def _has_non_cross_object(grid):
    return any(not _is_row_column_cross(cells) for _, cells in _components(grid))


def observe_overrides(grid):
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(components),
        "n_colors": len({color for color, _ in components}),
    }


def _lawful_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors = []
    if not 8 <= height <= 18 or not 8 <= width <= 18:
        errors.append(f"grid shape {height}x{width} outside 8..18")
    bad = sorted({value for row in grid for value in row if type(value) is not int or not 0 <= value <= 9})
    if bad:
        errors.append(f"invalid colors: {bad}")
        return errors

    components = _components(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 objects, got {len(components)}")
    color_count = len({color for color, _ in components})
    if not 1 <= color_count <= 2:
        errors.append(f"expected 1..2 nonzero colors, got {color_count}")

    boxes = []
    for _, cells in components:
        r0, c0, r1, c1 = _bbox(cells)
        box_h, box_w = r1 - r0 + 1, c1 - c0 + 1
        if box_h not in (2, 3) or box_w not in (2, 3):
            errors.append(f"object bbox {box_h}x{box_w} outside 2..3")
        if len(cells) == box_h * box_w:
            errors.append("object is already a solid rectangle")
        box = (r0, c0, r1, c1)
        if any(not (r1 < or0 or or1 < r0 or c1 < oc0 or oc1 < c0)
               for or0, oc0, or1, oc1 in boxes):
            errors.append("object bounding boxes overlap")
        boxes.append(box)
    return errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _lawful_errors(grid)


def strict_canonical_like(grid):
    """Canonical legal manifold; canonical examples need not contain our extra witness."""
    return _lawful_errors(grid)


SEMANTIC_WITNESSES = {"non_cross_object": _has_non_cross_object}
SEMANTIC_RIVALS = {"complete_crosses_only": _rival_cross_only}
WITNESS_RIVALS = {"non_cross_object": ["complete_crosses_only"]}
CANONICAL_SHORTCUTS = {"complete_crosses_only": _rival_cross_only}
LESSON_COMPETITORS = {"complete_crosses_only": _rival_cross_only}
