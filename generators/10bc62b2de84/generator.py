"""Constructive input sampler for 10bc62b2de84.

The selected Racket authority extracts nonzero 4-connected objects, sorts them
by bounding-box left edge, crops each bounding box, and packs the crops from
left to right with one zero column between them.  Crops are bottom-aligned in
an output whose height is the tallest crop.

The canonical pairs contain only equal-height crops, so a top-aligned packer is
answer-equivalent on every public example.  Every ordinary generated input
therefore contains unequal object heights, making bottom alignment observable.
"""
from __future__ import annotations

from collections.abc import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "10bc62b2de84"
TASK_ID = GENERATOR_ID
RULE_HASH = "eb9f505d4c6b"
VERSION = "3.0.0"
SUMMARY = (
    "Constructive 0-background object galleries. Generate 2-6 distinct-color "
    "4-connected objects in a 6-14 by 9-22 grid, keep objects disjoint under "
    "4-connectivity, and give every object a unique left bounding-box column. "
    "The selected rule sorts by that left edge, crops each object, packs crops "
    "left-to-right with one zero column between them, and bottom-aligns them. "
    "Every generated input has unequal crop heights so the canonical-only "
    "top-alignment shortcut is visibly wrong."
)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "canonical_7x9",
    "canonical_7x10",
    "canonical_9x10",
    "broad",
)

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors",
    "2-6 nonzero 4-connected objects use distinct colors and sizes 2-7",
    "objects do not touch orthogonally and have unique left bbox columns",
    "ordinary generated inputs contain at least two different bbox heights",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 6..14", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "scheduled 9..22", "valid": "9..22"},
    "n_objects": {"type": "int", "default": "scheduled 2..6", "valid": "2..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

# Shapes are normalized, 4-connected, and use their top/left bbox edges.  The
# compact fallback is exhaustively checked by task tests at both axis corners.
Shape = tuple[tuple[int, int], ...]
_V2: Shape = ((0, 0), (1, 0))
_V3: Shape = ((0, 0), (1, 0), (2, 0))
_V4: Shape = ((0, 0), (1, 0), (2, 0), (3, 0))
_H2: Shape = ((0, 0), (0, 1))
_H3: Shape = ((0, 0), (0, 1), (0, 2))
_L3_A: Shape = ((0, 0), (1, 0), (1, 1))
_L3_B: Shape = ((0, 0), (0, 1), (1, 1))
_L3_C: Shape = ((0, 1), (1, 0), (1, 1))
_L3_D: Shape = ((0, 0), (0, 1), (1, 0))
_SQUARE: Shape = ((0, 0), (0, 1), (1, 0), (1, 1))
_T_UP: Shape = ((0, 0), (0, 1), (0, 2), (1, 1))
_T_LEFT: Shape = ((0, 0), (1, 0), (1, 1), (2, 0))
_ZIG: Shape = ((0, 0), (0, 1), (1, 1), (1, 2))
_L4: Shape = ((0, 0), (1, 0), (2, 0), (2, 1))
_PENT: Shape = ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2))

_TALL_SHAPES: tuple[Shape, ...] = (_V3, _V4, _T_LEFT, _L4, _PENT)
_SHORT_SHAPES: tuple[Shape, ...] = (_H2, _H3, _L3_A, _L3_B, _L3_C, _L3_D, _SQUARE, _T_UP, _ZIG)
_SHAPE_BANK: tuple[Shape, ...] = _TALL_SHAPES + _SHORT_SHAPES + (_V2,)
_COMPACT_FALLBACK: tuple[Shape, ...] = (_V3, _V2, _H2, _V2, _H2, _V2)


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic four-step curriculum with three canonical profile anchors."""
    del seed
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(sample_index + offset) % len(SCHEDULE_PROFILES)]


def _scheduled_axes(ctx, profile: str, difficulty) -> tuple[int, int, int]:
    anchors = {
        "canonical_7x9": (7, 9, 3),
        "canonical_7x10": (7, 10, 3),
        "canonical_9x10": (9, 10, 3),
    }
    if profile in anchors:
        return anchors[profile]

    band = difficulty or "medium"
    ranges = {
        "easy": ((6, 8), (9, 13), (2, 3)),
        "medium": ((7, 11), (10, 17), (3, 5)),
        "hard": ((10, 14), (16, 22), (4, 6)),
    }[band]
    rng = ctx.draw_rng("broad_axes")
    return tuple(rng.randint(lo, hi) for lo, hi in ranges)  # type: ignore[return-value]


def _draw_scheduled_int(ctx, overrides, label: str, scheduled: int, lo: int, hi: int) -> int:
    """Record an exact axis while allowing every advertised explicit override."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _cells_at(shape: Shape, top: int, left: int) -> frozenset[tuple[int, int]]:
    return frozenset((top + r, left + c) for r, c in shape)


def _candidate_positions(shape: Shape, h: int, w: int, rng) -> list[tuple[int, int]]:
    ph, pw = _shape_dims(shape)
    positions = [(r, c) for r in range(h - ph + 1) for c in range(w - pw + 1)]
    rng.shuffle(positions)
    return positions


def _place_shapes(shapes: Sequence[Shape], h: int, w: int, rng):
    """Finite backtracking placement; returns one exact placement or None.

    Candidate cells may not overlap an existing object or any orthogonal
    neighbor of one.  Diagonal proximity is allowed because the rule's objects
    are 4-connected.  Left bbox columns are globally unique so sort order is
    unambiguous.
    """
    candidates = [_candidate_positions(shape, h, w, rng) for shape in shapes]
    order = sorted(
        range(len(shapes)),
        key=lambda i: (-len(shapes[i]), -_shape_dims(shapes[i])[0], len(candidates[i])),
    )
    placement: list[tuple[int, int] | None] = [None] * len(shapes)

    def search(depth: int, blocked: frozenset[tuple[int, int]], lefts: frozenset[int]):
        if depth == len(order):
            return tuple(placement)
        index = order[depth]
        shape = shapes[index]
        for top, left in candidates[index]:
            if left in lefts:
                continue
            cells = _cells_at(shape, top, left)
            if cells & blocked:
                continue
            newly_blocked = set(cells)
            for r, c in cells:
                newly_blocked.update(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
            placement[index] = (top, left)
            answer = search(
                depth + 1,
                blocked | frozenset(newly_blocked),
                lefts | frozenset((left,)),
            )
            if answer is not None:
                return answer
        placement[index] = None
        return None

    return search(0, frozenset(), frozenset())


def _choose_shapes(ctx, n_objects: int) -> tuple[Shape, ...]:
    rng = ctx.draw_rng("shapes")
    # The first crop is always tall and the second is always shorter.  Other
    # objects vary independently and may share geometry but never color.
    shapes = [rng.choice(_TALL_SHAPES), rng.choice(_SHORT_SHAPES)]
    shapes.extend(rng.choice(_SHAPE_BANK) for _ in range(n_objects - 2))
    return tuple(shapes)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_n = _scheduled_axes(ctx, profile, difficulty)
    h = _draw_scheduled_int(ctx, overrides, "grid_h", scheduled_h, 6, 14)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", scheduled_w, 9, 22)
    n_objects = _draw_scheduled_int(ctx, overrides, "n_objects", scheduled_n, 2, 6)

    shapes = _choose_shapes(ctx, n_objects)
    placement = _place_shapes(shapes, h, w, ctx.draw_rng("placement"))
    if placement is None:
        # Rich shapes can be too wide in the 6x9, six-object corner.  The
        # compact family preserves the unequal-height witness and has a lawful
        # construction for every advertised axis combination.
        shapes = _COMPACT_FALLBACK[:n_objects]
        placement = _place_shapes(shapes, h, w, ctx.draw_rng("compact_placement"))
    if placement is None:
        raise AssertionError(
            f"constructive placement failed unexpectedly for grid={h}x{w}, n={n_objects}"
        )

    colors = ctx.draw_rng("palette").sample(range(1, 10), n_objects)
    grid = full_grid(h, w, 0)
    for color, shape, position in zip(colors, shapes, placement):
        assert position is not None
        top, left = position
        for r, c in shape:
            grid[top + r][left + c] = color
    return grid


def _components(grid) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: min(c for _, c in cells))


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def observe_overrides(grid):
    """Recover every exact advertised axis from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(_components(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer ARC colors 0..9"]

    h, w = len(grid), width
    errors = []
    if not 6 <= h <= 14:
        errors.append(f"grid height {h} outside [6,14]")
    if not 9 <= w <= 22:
        errors.append(f"grid width {w} outside [9,22]")

    components = _components(grid)
    if not 2 <= len(components) <= 6:
        errors.append(f"need 2-6 nonzero 4-connected objects, got {len(components)}")
        return errors

    left_edges = []
    object_colors = []
    for index, cells in enumerate(components):
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            errors.append(f"object {index} mixes colors {sorted(colors)}")
        else:
            object_colors.append(next(iter(colors)))
        if not 2 <= len(cells) <= 7:
            errors.append(f"object {index} size {len(cells)} outside [2,7]")
        left_edges.append(_bbox(cells)[1])
    if len(set(object_colors)) != len(object_colors):
        errors.append("objects must use distinct nonzero colors")
    if len(set(left_edges)) != len(left_edges):
        errors.append("object left bbox columns must be unique")
    return errors


def strict_canonical_like(grid):
    """Lawful instances of the selected object/crop/pack task manifold."""
    return self_check(grid)


def _pack(grid, *, alignment: str) -> list[list[int]]:
    pieces = []
    for cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        pieces.append([list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]])
    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(out_h, out_w, 0)
    left = 0
    for piece in pieces:
        top = 0 if alignment == "top" else out_h - len(piece)
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def _top_aligned_rival(grid):
    """Plausible WRONG rule: pack crops at the top instead of the bottom."""
    return _pack(grid, alignment="top")


def _has_unequal_heights(grid) -> bool:
    heights = {_bbox(cells)[2] - _bbox(cells)[0] + 1 for cells in _components(grid)}
    return len(heights) >= 2


SEMANTIC_WITNESSES = {"unequal_heights": _has_unequal_heights}
SEMANTIC_RIVALS = {"top_aligned": _top_aligned_rival}
WITNESS_RIVALS = {"unequal_heights": ["top_aligned"]}
CANONICAL_SHORTCUTS = {"top_aligned": _top_aligned_rival}
LESSON_COMPETITORS = {"top_aligned": _top_aligned_rival}
