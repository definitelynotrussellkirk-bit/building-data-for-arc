"""Generator for ARC task 516502422f5c (legacy a78176bb).

A complete colored diagonal is accompanied by gray (5) marker cells on the
left, right, or both sides.  The Racket oracle keeps the original diagonal and
draws one parallel diagonal two offsets beyond the most distant marker on each
occupied side.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "516502422f5c"
TASK_ID = "516502422f5c"
VERSION = "3.0.0"
RULE_HASH = "06cb17eab76d"

SUMMARY = (
    "A complete non-gray colored diagonal lies on a black background (with a "
    "regular 10x10 canonical-scale anchor among varied sizes). Gray "
    "marker cells occupy one or more neighboring parallel diagonals on the "
    "left, right, or both sides. Keep the source diagonal and replace the gray "
    "region by a colored parallel diagonal exactly two diagonal offsets beyond "
    "the farthest gray marker on each occupied side."
)

INVARIANTS = [
    "exactly one color outside {0,5} fills one complete visible diagonal",
    "at least two gray markers lie strictly off the source diagonal",
    "markers occur on the left, right, or both sides and determine side-specific extreme offsets",
    "each requested output diagonal two offsets beyond an extreme remains visible",
]

DEGENERATE_TEXTURES = ("no_diagonal", "no_markers", "full_grid")
HELPFUL_TEXTURES: tuple[str, ...] = ()
MARKER_SIDES = ("left", "right", "both")
DIAGONAL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "difficulty-skewed", "valid": "10..22"},
    "diag_color": {
        "type": "color",
        "default": "rng excluding 0 and 5",
        "valid": "1..4|6..9",
    },
    "n_markers": {"type": "int", "default": "difficulty-skewed", "valid": "2..15"},
    "marker_sides": {
        "type": "str",
        "default": "rng",
        "valid": "left|right|both",
    },
}


def _diag_cells(k: int, h: int, w: int) -> list[tuple[int, int]]:
    return [(r, r + k) for r in range(h) if 0 <= r + k < w]


def _analyze(grid) -> tuple[dict, list[str]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return {}, ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    values = {value for row in grid for value in row}
    invalid = sorted(values - set(range(10)))
    if invalid:
        errors.append(f"ARC colors must be 0..9, found {invalid}")

    diag_colors = sorted(values - {0, 5})
    if len(diag_colors) != 1:
        errors.append(
            f"expected exactly one non-0/5 diagonal color, found {diag_colors}"
        )
        return {}, errors
    diag_color = diag_colors[0]
    diag_positions = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == diag_color
    ]
    offsets = {c - r for r, c in diag_positions}
    if len(offsets) != 1:
        errors.append("colored cells must all share one diagonal offset")
        return {}, errors
    k = next(iter(offsets))
    expected_diag = set(_diag_cells(k, h, w))
    if set(diag_positions) != expected_diag:
        missing = len(expected_diag - set(diag_positions))
        extra = len(set(diag_positions) - expected_diag)
        errors.append(
            f"colored diagonal must be complete (missing={missing}, extra={extra})"
        )
    if len(expected_diag) < 3:
        errors.append("colored diagonal must contain at least three cells")

    marker_positions = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == 5
    ]
    if len(marker_positions) < 2:
        errors.append("at least two gray markers are required")
    marker_offsets = [c - r - k for r, c in marker_positions]
    if any(offset == 0 for offset in marker_offsets):
        errors.append("gray markers must not lie on the source diagonal")
    left = [offset for offset in marker_offsets if offset < 0]
    right = [offset for offset in marker_offsets if offset > 0]
    if marker_positions and not (left or right):
        errors.append("gray markers must lie left or right of the source diagonal")

    target_offsets: list[int] = []
    if left:
        target_offsets.append(k + min(left) - 2)
    if right:
        target_offsets.append(k + max(right) + 2)
    for target in target_offsets:
        if len(_diag_cells(target, h, w)) < 2:
            errors.append(
                f"extreme marker implies nearly invisible output diagonal {target}"
            )

    marker_sides = "both" if left and right else "left" if left else "right"
    return {
        "grid_h": h,
        "grid_w": w,
        "diag_color": diag_color,
        "n_markers": len(marker_positions),
        "marker_sides": marker_sides,
        "diag_offset": k,
        "left_extreme": min(left) if left else None,
        "right_extreme": max(right) if right else None,
    }, errors


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    analysis, errors = _analyze(grid)
    if errors:
        return {}
    return {name: analysis[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete-diagonal plus off-diagonal marker grammar."""
    analysis, errors = _analyze(grid)
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be easy, medium, hard, or None")
    if not errors and isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        for name in AXES:
            if requested.get(name) is not None and requested[name] != analysis[name]:
                errors.append(
                    f"{name} requested {requested[name]!r}, observed {analysis[name]!r}"
                )
    return errors


def _scheduled_choice(ctx, label: str, values: tuple, desired):
    """Record an exact keyed draw while enforcing the lesson-slot schedule.

    ``random.choice`` selects an index from the option sequence.  We reproduce
    that stateless index with the same keyed RNG, rotate the complete option set
    so ``desired`` occupies it, then let ``draw_choice`` perform and record the
    real draw.  Explicit caller overrides still take precedence and every legal
    value remains in the option set.
    """
    index = ctx.draw_rng(label).randrange(len(values))
    options = [value for value in values if value != desired]
    options.insert(index, desired)
    return ctx.draw_choice(label, tuple(options))


def _scheduled_extent(sample_index: int) -> int:
    """Cycle the answer-controlling marker extent across lesson slots.

    The first three sequential demonstrations therefore witness extents 2, 3,
    and 4 in addition to left, right, and two-sided marker branches.  This
    prevents a lesson from accidentally teaching a fixed-distance shortcut.
    """
    return (2, 3, 4)[sample_index % 3]


def _side_cells(k: int, h: int, w: int, sign: int, extent: int) -> list[tuple[int, int, int]]:
    cells: list[tuple[int, int, int]] = []
    for distance in range(1, extent + 1):
        relative = sign * distance
        for r, c in _diag_cells(k + relative, h, w):
            cells.append((r, c, relative))
    return cells


def _pick_markers(
    *, k: int, h: int, w: int, side: str, count: int, extent: int, rng
) -> list[tuple[int, int]]:
    signs = (-1, 1) if side == "both" else (-1,) if side == "left" else (1,)
    capacities = {
        sign: len(_side_cells(k, h, w, sign, extent)) for sign in signs
    }
    allocations: dict[int, int]
    if len(signs) == 2:
        low = max(1, count - capacities[1])
        high = min(capacities[-1], count - 1)
        if low > high:
            raise ValueError("insufficient two-sided marker capacity")
        left_count = rng.randint(low, high)
        allocations = {-1: left_count, 1: count - left_count}
    else:
        if capacities[signs[0]] < count:
            raise ValueError("insufficient one-sided marker capacity")
        allocations = {signs[0]: count}

    selected: list[tuple[int, int]] = []
    for sign, side_count in allocations.items():
        candidates = _side_cells(k, h, w, sign, extent)
        far = [(r, c) for r, c, rel in candidates if abs(rel) == extent]
        inner = [(r, c) for r, c, rel in candidates if abs(rel) < extent]
        rng.shuffle(far)
        rng.shuffle(inner)
        # Always expose the extreme that controls the answer.  When possible,
        # include an inner offset too so a single marker cannot act as the answer.
        chosen = [far.pop()]
        if side_count >= 2 and inner:
            chosen.append(inner.pop())
        remaining = far + inner
        rng.shuffle(remaining)
        chosen.extend(remaining[: side_count - len(chosen)])
        if len(chosen) != side_count:
            raise ValueError(
                f"cannot place {side_count} markers on {side} side in {h}x{w}"
            )
        selected.extend(chosen)
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_anchor = sample_index % 5 in (0, 1)
    if canonical_anchor:
        h = _scheduled_choice(ctx, "grid_h", tuple(range(10, 21)), 10)
        w = _scheduled_choice(ctx, "grid_w", tuple(range(10, 23)), 10)
    else:
        h = ctx.draw_int_diff("grid_h", 10, 20)
        w = ctx.draw_int_diff("grid_w", 10, 22)
    diag_color = ctx.draw_choice("diag_color", DIAGONAL_COLORS)
    n_markers = ctx.draw_int_diff("n_markers", 2, 15)
    marker_sides = _scheduled_choice(
        ctx,
        "marker_sides",
        MARKER_SIDES,
        MARKER_SIDES[sample_index % len(MARKER_SIDES)],
    )
    rng = ctx.draw_rng("layout")

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w, diag_color)
    if texture is not None:
        raise ValueError(f"unknown texture override {texture!r}")

    # Search a small central geometry set.  This keeps both the source and the
    # answer diagonals visible while guaranteeing every exact count/side override.
    preferred_extent = _scheduled_extent(sample_index)
    extents = [preferred_extent] + [value for value in (2, 3, 4) if value != preferred_extent]
    if marker_sides == "left":
        k_candidates = [1, 2, 3, 0, -1, -2, -3]
    elif marker_sides == "right":
        k_candidates = [-1, -2, -3, 0, 1, 2, 3]
    else:
        k_candidates = [-2, -1, 0, 1, 2]
    first = k_candidates[:3]
    rest = k_candidates[3:]
    rng.shuffle(first)
    rng.shuffle(rest)
    k_candidates = first + rest

    markers = None
    k = 0
    extent = preferred_extent
    for candidate_extent in extents:
        for candidate_k in k_candidates:
            try:
                candidate_markers = _pick_markers(
                    k=candidate_k,
                    h=h,
                    w=w,
                    side=marker_sides,
                    count=n_markers,
                    extent=candidate_extent,
                    rng=rng,
                )
            except ValueError:
                continue
            targets = []
            if marker_sides in ("left", "both"):
                targets.append(candidate_k - candidate_extent - 2)
            if marker_sides in ("right", "both"):
                targets.append(candidate_k + candidate_extent + 2)
            if all(len(_diag_cells(target, h, w)) >= 2 for target in targets):
                k = candidate_k
                extent = candidate_extent
                markers = candidate_markers
                break
        if markers is not None:
            break
    if markers is None:
        raise ValueError(
            f"no valid marker geometry for {h}x{w}, count={n_markers}, "
            f"sides={marker_sides}"
        )

    grid = full_grid(h, w, 0)
    for r, c in _diag_cells(k, h, w):
        grid[r][c] = diag_color
    for r, c in markers:
        grid[r][c] = 5
    return grid


def _draw_from_degenerate(name: str, h: int, w: int, diag_color: int):
    grid = full_grid(h, w, 0)
    k = 0
    for r, c in _diag_cells(k, h, w):
        grid[r][c] = diag_color
    grid[1][3] = 5
    grid[4][2] = 5
    if name == "no_diagonal":
        for r, c in _diag_cells(k, h, w):
            grid[r][c] = 0
    elif name == "no_markers":
        grid[1][3] = 0
        grid[4][2] = 0
    elif name == "full_grid":
        grid = full_grid(h, w, diag_color)
    return grid
