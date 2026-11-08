"""Generator for arc_puzzle_bank_21_set16_bundle:medium_p03 — crop cells of corner-marker color.

Rule: exactly one corner is a non-zero marker color. Crop the non-corner
object, if any, with that same color; if there is no body object of the marker
color, the corner marker itself is the selected object and the answer is 1x1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_corner_marker (no non-zero corner), no_body_cells (corner-only
selected object), corners_disagree (more than one non-zero corner color).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d94e8b169413"
VERSION = "2.3.0"
TASK_ID = "d94e8b169413"

SUMMARY = (
    "9x9 0-bg grid with exactly one non-zero corner marker. The marker color "
    "names the target color. Usually a same-color target object is placed in "
    "the body and 1-2 non-marker distractor objects are placed outside its "
    "bbox; sometimes the corner marker is the only cell of that color, yielding "
    "the canonical 1x1 fallback answer. Rule: choose the non-zero corner color "
    "and output the tight crop of cells with that color, excluding the corner "
    "when body cells exist."
)

INVARIANTS = [
    "background is 0",
    "exactly one corner cell is non-zero",
    "the non-zero corner's color is the marker/target color",
    "normal rows either contain a 1-5 cell body target of marker color or the canonical corner-only fallback",
    "distractor cells use non-marker colors and stay outside the target crop bbox",
]

AXES = {
    "grid_h": {"type": "int", "default": "9", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "9", "valid": "8..10"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
    "palette_size": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias": {"type": "str", "default": "single_corner_marker_plus_body_object", "valid": "single_corner_marker_plus_body_object"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "default|warm|cool|varied|no_corner_marker|no_body_cells|corners_disagree"},
}

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corner_marker", "no_body_cells", "corners_disagree")


def _connected_shape(rng, n: int) -> list[tuple[int, int]]:
    """Small connected-ish target shapes with canonical L-triomino support."""
    shapes_by_n = {
        1: [[(0, 0)]],
        2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)], [(0, 0), (1, 1)]],
        3: [
            [(0, 0), (0, 1), (1, 0)],
            [(0, 0), (0, 1), (1, 1)],
            [(0, 0), (1, 0), (1, 1)],
            [(0, 1), (1, 0), (1, 1)],
            [(0, 0), (0, 1), (0, 2)],
            [(0, 0), (1, 0), (2, 0)],
        ],
        4: [
            [(0, 0), (0, 1), (1, 0), (1, 1)],
            [(0, 0), (0, 1), (0, 2), (1, 1)],
            [(0, 1), (1, 0), (1, 1), (1, 2)],
            [(0, 0), (1, 0), (2, 0), (2, 1)],
            [(0, 1), (1, 1), (2, 1), (2, 0)],
        ],
        5: [
            [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
            [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
            [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
        ],
    }
    return list(rng.choice(shapes_by_n[n]))


def _motif(rng, n: int) -> list[tuple[int, int]]:
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            seen.add((nr, nc))
            cells.append((nr, nc))
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return [(r - min_r, c - min_c) for r, c in cells]


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _inside_bbox(cells: list[tuple[int, int]], r0: int, c0: int,
                 bbox: tuple[int, int, int, int]) -> bool:
    r1, c1, r2, c2 = bbox
    return any(r1 <= r0 + dr <= r2 and c1 <= c0 + dc <= c2 for dr, dc in cells)


def _free(g, r0: int, c0: int, shape: list[tuple[int, int]]) -> bool:
    h, w = len(g), len(g[0])
    for dr, dc in shape:
        r, c = r0 + dr, c0 + dc
        if not (1 <= r < h - 1 and 1 <= c < w - 1):
            return False
        if g[r][c] != 0:
            return False
    return True


def _place(g, cells: list[tuple[int, int]], r0: int, c0: int, color: int) -> None:
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def _choose_marker_palette(rng):
    marker = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    distractor_colors = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != marker]
    rng.shuffle(distractor_colors)
    return marker, distractor_colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 9, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    marker, distractor_colors = _choose_marker_palette(rng)
    corner = rng.choice([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
    g[corner[0]][corner[1]] = marker

    # The real task includes the corner-only fallback case; keep it as a normal
    # low-frequency case instead of banishing it to degenerate-only generation.
    corner_only = (difficulty == "easy" and rng.random() < 0.20) or rng.random() < 0.08
    target_cells: list[tuple[int, int]] = []
    target_bbox = None
    if not corner_only:
        if difficulty == "easy":
            n_target = rng.choice([1, 2, 3])
        elif difficulty == "hard":
            n_target = rng.choice([3, 4, 5])
        else:
            n_target = rng.choice([2, 3, 4])
        shape = _connected_shape(rng, n_target)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _ in range(100):
            r0 = rng.randint(1, h - sh - 1)
            c0 = rng.randint(1, w - sw - 1)
            if _free(g, r0, c0, shape):
                _place(g, shape, r0, c0, marker)
                target_cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                target_bbox = _bbox(target_cells)
                break
        if not target_cells:
            corner_only = True

    n_distract = rng.randint(1, 2)
    placed = 0
    for i in range(n_distract):
        color = distractor_colors[i % len(distractor_colors)]
        shape = _motif(rng, rng.randint(2, 3))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _ in range(100):
            r0 = rng.randint(1, h - sh - 1)
            c0 = rng.randint(1, w - sw - 1)
            if target_bbox and _inside_bbox(shape, r0, c0, target_bbox):
                continue
            if _free(g, r0, c0, shape):
                _place(g, shape, r0, c0, color)
                placed += 1
                break
    if placed == 0:
        # Small deterministic distractor that stays in the opposite body corner.
        color = distractor_colors[0]
        for r, c in [(1, 1), (1, 2)]:
            if g[r][c] == 0 and (not target_bbox or not (target_bbox[0] <= r <= target_bbox[2] and target_bbox[1] <= c <= target_bbox[3])):
                g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the single-corner marker crop task."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if not (8 <= h <= 10 and 9 <= w <= 10):
        errors.append(f"normal grid should be 8..10 by 9..10, got {h}x{w}")
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    marked = [(r, c, grid[r][c]) for r, c in corners if grid[r][c] != 0]
    if len(marked) != 1:
        errors.append(f"expected exactly one non-zero corner marker, found {marked}")
        return errors
    marker = marked[0][2]
    body = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == marker]
    if len(body) > 5:
        errors.append(f"expected at most 5 body marker cells, found {len(body)}")
    distractors = [(r, c, grid[r][c]) for r in range(1, h - 1) for c in range(1, w - 1)
                   if grid[r][c] not in (0, marker)]
    if not distractors:
        errors.append("expected at least one non-marker distractor object")
    if body and distractors:
        r1, c1, r2, c2 = _bbox(body)
        inside = [(r, c, v) for r, c, v in distractors if r1 <= r <= r2 and c1 <= c <= c2]
        if inside:
            errors.append(f"distractors must stay outside the selected crop bbox; first inside={inside[0]}")
    return errors


def _draw_from_degenerate(name: str):
    h = w = 9
    g = full_grid(h, w, 0)
    if name == "no_corner_marker":
        g[3][3] = 4
        g[3][4] = 4
        g[5][6] = 6
        g[6][6] = 6
        return g
    if name == "no_body_cells":
        g[0][0] = 4
        g[3][3] = 6
        g[3][4] = 6
        return g
    if name == "corners_disagree":
        g[0][0] = 2
        g[0][w - 1] = 4
        g[4][4] = 2
        g[6][6] = 4
        return g
    return g
