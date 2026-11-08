"""Generator for arc_puzzle_bank_seventeenth_21_bundle:hard_118_overlay_transformed_prototype_stamps_into_count_map.

The color-8 object is the prototype.  Singleton code cells 1-4 ask the rule to
stamp transformed copies at those anchors and emit an overlap count map.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "398b42a1be77"
VERSION = "1.2.0"  # strengthen prototype/code-anchor self_check
TASK_ID = "398b42a1be77"

SUMMARY = "A corner color-8 prototype plus singleton transform-code anchors."

INVARIANTS = [
    "background is 0",
    "one connected color-8 prototype is the only 8 object",
    "singleton cells with colors 1-4 act as transformed stamp anchors",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 9..11", "valid": "7..13"},
    "grid_w": {"type": "int", "default": "rng 11..13", "valid": "9..15"},
    "n_codes": {"type": "int", "default": "rng 3..5", "valid": "2..7"},
}

PROTOTYPES = [
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
]


def _too_close(pos, blocked):
    r, c = pos
    return any(abs(r - br) <= 1 and abs(c - bc) <= 1 for br, bc in blocked)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one connected prototype and isolated singleton transform-code anchors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    eight_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    if not eight_cells:
        errors.append("no color-8 prototype cells found")
    else:
        stack = [next(iter(eight_cells))]
        seen = {stack[0]}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in eight_cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if seen != eight_cells:
            errors.append("color-8 prototype must be one connected object")
        if not (4 <= len(eight_cells) <= 5):
            errors.append(f"prototype should have 4-5 cells, found {len(eight_cells)}")
    code_cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if 1 <= grid[r][c] <= 4]
    if not (3 <= len(code_cells) <= 5):
        errors.append(f"expected 3-5 singleton code cells (colors 1-4), found {len(code_cells)}")
    for i, (r, c, _v) in enumerate(code_cells):
        for rr, cc, _vv in code_cells[i + 1:]:
            if abs(r - rr) <= 1 and abs(c - cc) <= 1:
                errors.append("code anchors should not touch each other, even diagonally")
        if any(abs(r - er) <= 1 and abs(c - ec) <= 1 for er, ec in eight_cells):
            errors.append("code anchors should not touch the prototype halo")
    return sorted(set(errors))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 9, 11)
    w = ctx.draw_int("grid_w", 11, 13)
    n_codes = ctx.draw_int("n_codes", 3, 5)
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    proto = rng.choice(PROTOTYPES)
    top = rng.choice([0, 1])
    left = rng.choice([0, 1])
    blocked = set()
    for dr, dc in proto:
        r = top + dr
        c = left + dc
        grid[r][c] = 8
        blocked.add((r, c))

    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and not _too_close((r, c), blocked)
    ]
    rng.shuffle(candidates)
    anchors = []
    for pos in candidates:
        if _too_close(pos, anchors):
            continue
        anchors.append(pos)
        if len(anchors) == n_codes:
            break
    if len(anchors) < n_codes:
        raise ValueError("could not place transform-code anchors")

    codes = [1, 2, 3, 4]
    for idx, (r, c) in enumerate(anchors):
        grid[r][c] = codes[idx % len(codes)]

    return grid
