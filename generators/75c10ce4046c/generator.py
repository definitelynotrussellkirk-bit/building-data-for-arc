"""Generator for 75c10ce4046c — source/candidate congruence indicator.

One color-2 source polyomino is compared with scan-ordered candidate
components in colors 3..6.  The reference emits one cyan cell for each
candidate congruent to the source (translation only), otherwise black.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75c10ce4046c"
VERSION = "2.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "One color-2 tetromino or pentomino source plus 3–7 isolated candidate "
    "components in colors 3..6; an exact requested subset matches the source's "
    "normalized offsets and the rest are distinct distractors."
)

INVARIANTS = [
    "background is 0",
    "exactly one connected color-2 source of size 4 or 5",
    "3–7 isolated candidate components in colors 3..6",
    "at least one candidate matches the source and at least one does not",
]

TETROMINOES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
)
PENTOMINOES = (
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
)
SHAPES_BY_SIZE = {4: TETROMINOES, 5: PENTOMINOES}
ALL_SHAPES = TETROMINOES + PENTOMINOES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "height": {"type": "int", "default": "rng 14..22", "valid": "14..22"},
    "width": {"type": "int", "default": "rng 18..26", "valid": "18..26"},
    "candidate_count": {"type": "int", "default": "rng 3..7", "valid": "3..7"},
    "matching_candidates": {
        "type": "int", "default": "rng 1..candidate_count-1", "valid": "1..6"
    },
    "source_size": {"type": "int", "default": "rng 4|5", "valid": "4|5"},
}


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _norm(shape):
    r0 = min(r for r, _ in shape)
    c0 = min(c for _, c in shape)
    return tuple(sorted((r - r0, c - c0) for r, c in shape))


def _free_box(grid, row0, col0, shape_h, shape_w, pad=1):
    height, width = len(grid), len(grid[0])
    if row0 < 0 or col0 < 0 or row0 + shape_h > height or col0 + shape_w > width:
        return False
    for row in range(max(0, row0 - pad), min(height, row0 + shape_h + pad)):
        for col in range(max(0, col0 - pad), min(width, col0 + shape_w + pad)):
            if grid[row][col] != 0:
                return False
    return True


def _paint(grid, row0, col0, shape, color):
    for dr, dc in shape:
        grid[row0 + dr][col0 + dc] = color


def _place(grid, rng, shape, color):
    shape_h, shape_w = _size(shape)
    height, width = len(grid), len(grid[0])
    positions = [
        (row0, col0)
        for row0 in range(height - shape_h + 1)
        for col0 in range(width - shape_w + 1)
        if _free_box(grid, row0, col0, shape_h, shape_w)
    ]
    if not positions:
        raise ValueError(
            f"could not place {len(shape)}-cell component in {height}x{width}; "
            "increase height/width or reduce candidate_count"
        )
    row0, col0 = rng.choice(positions)
    _paint(grid, row0, col0, shape, color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    allowed = set(AXES)
    unknown = set(overrides) - allowed
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_strict("height", 14, 22)
    width = ctx.draw_int_strict("width", 18, 26)
    candidate_count = ctx.draw_int_strict("candidate_count", 3, 7)
    source_size = ctx.draw_choice("source_size", (4, 5))
    matching_candidates = ctx.draw_int_strict(
        "matching_candidates", 1, candidate_count - 1
    )
    rng = ctx.draw_rng("layout")

    source = rng.choice(SHAPES_BY_SIZE[source_size])
    source_signature = _norm(source)
    distractors = [shape for shape in ALL_SHAPES if _norm(shape) != source_signature]
    candidate_shapes = [source] * matching_candidates + [
        rng.choice(distractors) for _ in range(candidate_count - matching_candidates)
    ]
    rng.shuffle(candidate_shapes)

    grid = full_grid(height, width, 0)
    _place(grid, rng, source, 2)
    for shape in candidate_shapes:
        _place(grid, rng, shape, rng.choice((3, 4, 5, 6)))
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator constructed an invalid grid: {errors}")
    return grid


def _components(grid, colors=None):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (colors is not None and color not in colors) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, cells))
    return result


def _norm_cells(cells):
    row0 = min(r for r, _ in cells)
    col0 = min(c for _, c in cells)
    return tuple(sorted((r - row0, c - col0) for r, c in cells))


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be exact integer colors 0..9"]
    messages = []
    sources = _components(grid, colors={2})
    if len(sources) != 1:
        return [f"expected exactly one color-2 source component, got {len(sources)}"]
    source_cells = sources[0][1]
    if len(source_cells) not in (4, 5):
        messages.append(f"expected source size 4 or 5, got {len(source_cells)}")
    source_shape = _norm_cells(source_cells)
    candidates = _components(grid, colors={3, 4, 5, 6})
    if not 3 <= len(candidates) <= 7:
        messages.append(f"expected 3-7 candidate components, got {len(candidates)}")
    if any(len(cells) not in (4, 5) for _, cells in candidates):
        messages.append("candidate components must be tetrominoes or pentominoes")
    matches = sum(_norm_cells(cells) == source_shape for _, cells in candidates)
    if matches == 0:
        messages.append("expected at least one matching candidate")
    if matches == len(candidates):
        messages.append("expected at least one non-matching candidate")
    extras = [value for row in grid for value in row if value not in (0, 2, 3, 4, 5, 6)]
    if extras:
        messages.append("unexpected colors outside 0,2,3,4,5,6")
    return messages


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid congruence input: " + "; ".join(errors))
    source = _components(grid, colors={2})[0][1]
    signature = _norm_cells(source)
    candidates = sorted(
        _components(grid, colors={3, 4, 5, 6}),
        key=lambda item: (min(r for r, _ in item[1]), min(c for _, c in item[1])),
    )
    return [[8 if _norm_cells(cells) == signature else 0 for _, cells in candidates]]
