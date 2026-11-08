"""Generator for ``ccbf7456811b`` — target-mask closure selection.

Canonical rule
--------------
Color 7 is a target mask.  For every other non-background color, close
that color horizontally on each occupied row, score the hypothetical closure
by target overlap (larger is better), then by extra cells (smaller is better),
then by color (smaller is better).  Crop the winning closure and repaint it 8.

The previous generator placed each color as an isolated connected motif.  A
motif's horizontal closure stayed inside its cleared bounding box, so it could
never intersect the separately placed target: the advertised overlap stage was
always zero.  This version constructs target-crossing marker pairs directly.
Every ordinary draw has two full-overlap candidates with different extras plus
additional distractors, so both overlap and extra-cell ranking are exercised.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ccbf7456811b"
TASK_ID = GENERATOR_ID
VERSION = "1.4.0"

SUMMARY = (
    "Color 7 is an irregular target mask; 3-5 other colors are sparse marker "
    "sets whose horizontal closures compete by overlap, extra cells, then color."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "color 7 is a nonempty target mask",
    "3-5 distinct non-{0,7} candidate colors",
    "at least two candidates have positive horizontal-closure overlap with target",
    "the best-overlap candidates have different extra-cell counts",
]

AXES = {
    "grid_h": {"type": "int", "default": "by difficulty", "valid": "10..30"},
    "grid_w": {"type": "int", "default": "by difficulty", "valid": "12..30"},
    "n": {"type": "int", "default": "by difficulty", "valid": "3..5"},
}


def _points(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _row_close(cells):
    closed = set()
    for row in {r for r, _ in cells}:
        cols = [c for r, c in cells if r == row]
        closed.update((row, col) for col in range(min(cols), max(cols) + 1))
    return closed


def _scores(grid):
    target = _points(grid, 7)
    rows = []
    for color in sorted({value for row in grid for value in row} - {0, 7}):
        closed = _row_close(_points(grid, color))
        overlap = len(closed & target)
        rows.append((color, overlap, len(closed) - overlap, closed))
    return sorted(rows, key=lambda item: (-item[1], item[2], item[0]))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer colors 0..9"]
    if not _points(grid, 7):
        return ["missing color-7 target"]
    candidates = {value for row in grid for value in row} - {0, 7}
    if not 3 <= len(candidates) <= 5:
        return ["expected 3-5 candidate colors"]
    scores = _scores(grid)
    if sum(overlap > 0 for _color, overlap, _extra, _closed in scores) < 2:
        return ["target-overlap ranking is not exercised"]
    if len(scores) < 2 or scores[0][1] != scores[1][1] or scores[0][2] >= scores[1][2]:
        return ["extra-cell tie-break is not exercised"]
    return []


def _bands(difficulty):
    if difficulty == "easy":
        return (10, 14), (12, 18), (3, 4)
    if difficulty == "medium":
        return (14, 22), (16, 24), (3, 5)
    if difficulty == "hard":
        return (20, 30), (22, 30), (4, 5)
    return (10, 30), (12, 30), (3, 5)


def _paint(grid, cells, color):
    for row, col in cells:
        if grid[row][col] != 0:
            raise AssertionError("constructed roles overlap")
        grid[row][col] = color


def _scene(height, width, n_candidates, rng):
    grid = full_grid(height, width, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], n_candidates)
    winner_color, wider_color, *noise_colors = colors

    # Central target with at least three free columns on both sides.  Its row
    # spans vary so the winning crop is not a fixed rectangle.
    target_h = min(max(2, height // 5), height - 6)
    target_w = min(max(3, width // 5), width - 8)
    row0 = max(3, (height - target_h) // 2)
    col0 = max(3, (width - target_w) // 2)
    row0 = min(row0, height - target_h - 3)
    col0 = min(col0, width - target_w - 3)

    profile = rng.randrange(4)
    target = set()
    winner = set()
    wider = set()
    for index in range(target_h):
        row = row0 + index
        left_trim = (index + profile) % 2
        right_trim = (index * 2 + profile) % 2
        left = col0 + left_trim
        right = col0 + target_w - 1 - right_trim
        if right < left:
            right = left
        target.update((row, col) for col in range(left, right + 1))
        winner.update({(row, left - 1), (row, right + 1)})
        wider.update({(row, left - 2), (row, right + 2)})

    _paint(grid, target, 7)
    _paint(grid, winner, winner_color)
    _paint(grid, wider, wider_color)

    # Remaining colors are honest distractors outside the target rows.  Their
    # closures vary in size and position but cannot outrank the two target
    # crossing candidates.
    outside_rows = [row for row in range(height) if not row0 <= row < row0 + target_h]
    rng.shuffle(outside_rows)
    for index, color in enumerate(noise_colors):
        row = outside_rows[index]
        span = 2 + ((profile + index) % max(2, min(6, width - 2)))
        if index % 2 == 0:
            left = 0 if width >= 20 and index == 0 else 1 + index
        else:
            left = max(0, width - span - 2 - index)
        right = min(width - 1, left + span)
        if right == left:
            right = min(width - 1, left + 1)
        _paint(grid, {(row, left), (row, right)}, color)

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _bands(difficulty)
    height = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    width = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    n_candidates = ctx.draw_int_strict("n", n_lo, n_hi)
    return _scene(height, width, n_candidates, ctx.draw_rng("layout"))
