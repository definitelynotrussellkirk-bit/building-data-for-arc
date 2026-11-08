"""Generator for the local-frame quarter-turn task ``91ba253f9945``.

A source tripod (2/3/4) and a target tripod (5/6/7) define independent
orthonormal coordinate frames.  Nearby 8/9 markers are expressed in the
source frame; the canonical answer rotates each local coordinate 90 degrees
counterclockwise and paints it in the target frame.  Ordinary draws include
orientation changes, off-axis markers, irrelevant 8/9 decoys and spatially
spread color-1 distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "91ba253f9945"
TASK_ID = GENERATOR_ID
RULE_HASH = "b1e5584ad797"
VERSION = "2.0.0"
SUMMARY = "Rotate source-local 8/9 markers a quarter-turn into a second local frame."

INVARIANTS = [
    "exactly one orthogonal source frame 2/3/4 and target frame 5/6/7",
    "both 8 and 9 occur among source-local markers within Chebyshev radius 3",
    "canonical transformed target cells are in bounds and initially empty",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "11..30"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "15..30"},
    "marker_count": {"type": "int", "default": "difficulty band", "valid": "3..7"},
    "decoy_count": {"type": "int", "default": "difficulty band", "valid": "0..18"},
    "source_basis": {"type": "int", "default": "rng", "valid": "0..7"},
    "target_basis": {"type": "int", "default": "rng", "valid": "0..7"},
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BASES = tuple(
    (vx, vy)
    for vx in _CARDINAL
    for vy in _CARDINAL
    if vx[0] * vy[0] + vx[1] * vy[1] == 0
)
_FRAME_LOCAL = {(0, 0), (1, 0), (0, 1)}
# A point whose clockwise or counterclockwise image hits a target frame cell is
# deliberately excluded, so both family settings remain well-defined.
_TURN_FRAME_FORBIDDEN = _FRAME_LOCAL | {(-1, 0), (0, -1)}
_MARKER_CANDIDATES = tuple(
    (u, v)
    for u in range(-3, 4)
    for v in range(-3, 4)
    if (u, v) not in _TURN_FRAME_FORBIDDEN
)


def _gpos(origin, basis, u: int, v: int) -> tuple[int, int]:
    vx, vy = basis
    return (
        origin[0] + u * vx[0] + v * vy[0],
        origin[1] + u * vx[1] + v * vy[1],
    )


def _turn(u: int, v: int, clockwise: bool = False) -> tuple[int, int]:
    return (v, -u) if clockwise else (-v, u)


def _frame_options(h: int, w: int, basis, locals_) -> list[tuple[tuple[int, int], set[tuple[int, int]]]]:
    required = set(locals_) | _FRAME_LOCAL
    found = []
    for r in range(h):
        for c in range(w):
            origin = (r, c)
            cells = {_gpos(origin, basis, u, v) for u, v in required}
            if len(cells) != len(required):
                continue
            if all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                found.append((origin, cells))
    return found


def _find_frame(grid, colors: tuple[int, int, int]):
    positions = []
    for color in colors:
        matches = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one color-{color} frame cell")
        positions.append(matches[0])
    origin, px, py = positions
    vx = (px[0] - origin[0], px[1] - origin[1])
    vy = (py[0] - origin[0], py[1] - origin[1])
    if vx not in _CARDINAL or vy not in _CARDINAL or vx[0] * vy[0] + vx[1] * vy[1] != 0:
        raise ValueError(f"colors {colors!r} do not form an orthogonal unit frame")
    return origin, (vx, vy)


def _local(origin, basis, r: int, c: int) -> tuple[int, int]:
    dr, dc = r - origin[0], c - origin[1]
    vx, vy = basis
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of rows")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("ARC grids must not exceed 30x30")
    if any(
        type(row) is not list
        or len(row) != w
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return h, w


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the complete semantic domain used by ordinary generated inputs."""
    try:
        h, w = _validate_grid(grid)
        source = _find_frame(grid, (2, 3, 4))
        target = _find_frame(grid, (5, 6, 7))
    except ValueError as error:
        return [str(error)]

    markers = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (8, 9):
                continue
            u, v = _local(*source, r, c)
            if max(abs(u), abs(v)) <= 3:
                markers.append((u, v, grid[r][c]))
    errors = []
    if len(markers) < 3:
        errors.append("fewer than three source-local markers")
    if {color for _, _, color in markers} != {8, 9}:
        errors.append("source-local markers do not contain both colors 8 and 9")
    changed = False
    for u, v, color in markers:
        tu, tv = _turn(u, v)
        r, c = _gpos(*target, tu, tv)
        if not (0 <= r < h and 0 <= c < w):
            errors.append("canonical target position is out of bounds")
            continue
        if grid[r][c] in (5, 6, 7):
            errors.append("canonical marker would overwrite the target frame")
        changed |= grid[r][c] != color
    if markers and not changed:
        errors.append("canonical transformation changes no target cell")
    return errors


def _difficulty_ranges(difficulty):
    if difficulty == "easy":
        return (11, 14), (15, 19), (3, 4), (0, 4)
    if difficulty == "hard":
        return (20, 30), (24, 30), (5, 7), (8, 18)
    # None and medium both cover the central domain.
    return (12, 20), (17, 25), (3, 6), (2, 10)


def _paint_frame(grid, origin, basis, colors):
    for local, color in zip(((0, 0), (1, 0), (0, 1)), colors):
        r, c = _gpos(origin, basis, *local)
        grid[r][c] = color


def _add_spread_distractors(grid, blocked: set[tuple[int, int]], rng) -> None:
    h, w = len(grid), len(grid[0])
    quadrants = (
        (range(0, h // 2), range(0, w // 2)),
        (range(0, h // 2), range(w // 2, w)),
        (range(h // 2, h), range(0, w // 2)),
        (range(h // 2, h), range(w // 2, w)),
    )
    for rows, cols in quadrants:
        options = [(r, c) for r in rows for c in cols if grid[r][c] == 0 and (r, c) not in blocked]
        if options:
            r, c = rng.choice(options)
            grid[r][c] = 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    hr, wr, mr, dr = _difficulty_ranges(difficulty)
    h = ctx.draw_int_strict("grid_h", *hr)
    w = ctx.draw_int_strict("grid_w", *wr)
    marker_count = ctx.draw_int_strict("marker_count", *mr)
    decoy_count = ctx.draw_int_strict("decoy_count", *dr)
    source_basis = _BASES[ctx.draw_int_strict("source_basis", 0, len(_BASES) - 1)]
    target_basis = _BASES[ctx.draw_int_strict("target_basis", 0, len(_BASES) - 1)]
    rng = ctx.draw_rng("layout")

    for _attempt in range(128):
        locals_ = rng.sample(_MARKER_CANDIDATES, marker_count)
        # Deterministically force both marker colors while retaining varied roles.
        colors = [8, 9] + [rng.choice((8, 9)) for _ in range(marker_count - 2)]
        rng.shuffle(colors)
        markers = tuple((u, v, color) for (u, v), color in zip(locals_, colors))

        source_options = _frame_options(h, w, source_basis, [(u, v) for u, v, _ in markers])
        target_locals = {
            turned
            for u, v, _ in markers
            for turned in (_turn(u, v, False), _turn(u, v, True))
        }
        target_options = _frame_options(h, w, target_basis, target_locals)
        if not source_options or not target_options:
            continue

        selected = None
        for _ in range(4096):
            source_origin, source_cells = rng.choice(source_options)
            target_origin, target_cells = rng.choice(target_options)
            if source_cells & target_cells:
                continue
            if abs(source_origin[0] - target_origin[0]) + abs(source_origin[1] - target_origin[1]) < 5:
                continue
            selected = (source_origin, source_cells, target_origin, target_cells)
            break
        if selected is None:
            continue

        source_origin, source_cells, target_origin, target_cells = selected
        grid = full_grid(h, w, 0)
        _paint_frame(grid, source_origin, source_basis, (2, 3, 4))
        for u, v, color in markers:
            r, c = _gpos(source_origin, source_basis, u, v)
            grid[r][c] = color
        _paint_frame(grid, target_origin, target_basis, (5, 6, 7))

        blocked = set(source_cells) | set(target_cells)
        _add_spread_distractors(grid, blocked, rng)

        decoy_candidates = []
        for r in range(h):
            for c in range(w):
                if grid[r][c] != 0 or (r, c) in blocked:
                    continue
                u, v = _local(source_origin, source_basis, r, c)
                if max(abs(u), abs(v)) > 3:
                    decoy_candidates.append((r, c))
        rng.shuffle(decoy_candidates)
        for index, (r, c) in enumerate(decoy_candidates[:decoy_count]):
            grid[r][c] = 8 if index % 2 == 0 else 9

        if not self_check(grid, difficulty=difficulty):
            return grid

    raise RuntimeError("failed to construct a valid local-frame scene")
