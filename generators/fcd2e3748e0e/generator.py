"""Generator for the controlled template-transform task ``fcd2e3748e0e``.

A connected asymmetric color-1 template, a reflection control (2/3), a
rotation control (4/5/6/7), and a color-9 anchor are placed on a zero
background.  The selected canonical rule reflects the normalized template
when the first control is 3, rotates it by 0/1/2/3 clockwise quarter-turns,
and stamps the result in color 8 with the anchor as its top-left cell.

Only controls that are actually honored are advertised.  Missing-control
fixtures remain callable diagnostics but are not part of the lawful axis
contract.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fcd2e3748e0e"
VERSION = "3.2.0"
TASK_ID = GENERATOR_ID

SUMMARY = (
    "A zero-background grid contains one connected asymmetric color-1 "
    "template, one reflection control 2/3, one rotation control 4/5/6/7, "
    "and one color-9 anchor.  The rule transforms the normalized template "
    "and adds a color-8 copy at the anchor while preserving the input."
)

INVARIANTS = [
    "exactly one reflection control (2 or 3)",
    "exactly one rotation control (4, 5, 6, or 7)",
    "exactly one color-9 anchor and one connected color-1 template",
    "the template has eight distinct dihedral images",
    "the complete transformed-stamp footprint is empty and in bounds",
    "the input contains no color 8",
]

DIAGNOSTIC_TEXTURES = ("no_reflect_ctrl", "no_rotate_ctrl", "no_anchor")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-dependent", "valid": "11..22"},
    "grid_w": {"type": "int", "default": "difficulty-dependent", "valid": "12..24"},
    "reflect_ctrl": {"type": "int", "default": "deterministic 2..3", "valid": "2..3"},
    "rotate_ctrl": {"type": "int", "default": "deterministic 4..7", "valid": "4..7"},
    "template_size": {"type": "int", "default": "difficulty-dependent", "valid": "4..7"},
}


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate(cells):
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _flip_lr(cells):
    width = max(c for _, c in cells) + 1
    return _normalize((r, width - 1 - c) for r, c in cells)


def _asymmetric(cells):
    """Return whether all eight dihedral images are distinct."""
    base = _normalize(cells)
    images = set()
    current = base
    for _ in range(4):
        images.add(current)
        current = _rotate(current)
    current = _flip_lr(base)
    for _ in range(4):
        images.add(current)
        current = _rotate(current)
    return len(images) == 8


def _rand_poly(rng, size, maxdim=5):
    """Draw an exact-size connected asymmetric polyomino."""
    for _ in range(1200):
        cells = {(0, 0)}
        while len(cells) < size:
            boundary = []
            for r, c in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    candidate = (r + dr, c + dc)
                    if candidate not in cells:
                        boundary.append(candidate)
            if not boundary:
                break
            cells.add(rng.choice(boundary))
        norm = _normalize(cells)
        if (
            len(norm) == size
            and max(r for r, _ in norm) + 1 <= maxdim
            and max(c for _, c in norm) + 1 <= maxdim
            and _asymmetric(norm)
        ):
            return list(norm)
    raise RuntimeError(f"failed to sample an asymmetric {size}-cell template")


# Sampling bands choose ordinary examples; explicit controls use the full AXES
# domain. Keeping the ordinary draw bounds and VERSION preserves seeded draws.
_INTEGER_DOMAINS = {'grid_h': (11, 22), 'grid_w': (12, 24), 'template_size': (4, 7), 'reflect_ctrl': (2, 3), 'rotate_ctrl': (4, 7)}

def _draw_int(ctx, name, lo, hi):
    if ctx.overrides.get(name) is not None:
        lo, hi = _INTEGER_DOMAINS[name]
    return ctx.draw_int_strict(name, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    texture = overrides.get("texture")
    if texture in DIAGNOSTIC_TEXTURES:
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        height = _draw_int(ctx, "grid_h", 11, 13)
        width = _draw_int(ctx, "grid_w", 12, 15)
        size_lo, size_hi = 4, 5
    elif difficulty == "hard":
        height = _draw_int(ctx, "grid_h", 15, 22)
        width = _draw_int(ctx, "grid_w", 16, 24)
        size_lo, size_hi = 5, 7
    else:
        height = _draw_int(ctx, "grid_h", 12, 17)
        width = _draw_int(ctx, "grid_w", 14, 19)
        size_lo, size_hi = 4, 6

    reflect_value = _draw_int(ctx, "reflect_ctrl", 2, 3)
    rotate_value = _draw_int(ctx, "rotate_ctrl", 4, 7)
    template_size = _draw_int(ctx, "template_size", size_lo, size_hi)
    rng = ctx.draw_rng("layout")

    template = _rand_poly(rng, template_size, maxdim=5)
    template_h = max(r for r, _ in template) + 1
    template_w = max(c for _, c in template) + 1
    footprint_side = max(template_h, template_w)

    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()

    def in_bounds(cell):
        r, c = cell
        return 0 <= r < height and 0 <= c < width

    def free(cells):
        return all(in_bounds(cell) and cell not in occupied for cell in cells)

    # Keep a one-cell halo so the template stays a single isolated object.
    placements = [
        (r, c)
        for r in range(1, height - template_h)
        for c in range(1, width - template_w)
    ]
    rng.shuffle(placements)
    template_cells = None
    for top, left in placements:
        cells = [(top + dr, left + dc) for dr, dc in template]
        halo = {
            (r + dr, c + dc)
            for r, c in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        }
        if free(halo):
            template_cells = cells
            occupied.update(cell for cell in halo if in_bounds(cell))
            break
    if template_cells is None:
        raise RuntimeError("failed to place isolated template")
    for r, c in template_cells:
        grid[r][c] = 1

    def place_control(value):
        candidates = [(r, c) for r in range(height) for c in range(width) if (r, c) not in occupied]
        rng.shuffle(candidates)
        if not candidates:
            raise RuntimeError("no free control cell")
        cell = candidates[0]
        grid[cell[0]][cell[1]] = value
        occupied.add(cell)
        return cell

    place_control(reflect_value)
    place_control(rotate_value)

    # Reserve a square covering every possible reflected/rotated bounding box,
    # so the color-8 stamp can never overwrite an input feature.
    anchors = []
    for top in range(height - footprint_side + 1):
        for left in range(width - footprint_side + 1):
            square = {
                (r, c)
                for r in range(top, top + footprint_side)
                for c in range(left, left + footprint_side)
            }
            if free(square):
                anchors.append((top, left, square))
    rng.shuffle(anchors)
    if not anchors:
        raise RuntimeError("no free transformed-stamp footprint for anchor")
    anchor_r, anchor_c, anchor_square = anchors[0]
    grid[anchor_r][anchor_c] = 9
    occupied.update(anchor_square)
    return grid


def _components_of(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != color or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be nonempty"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer colors 0..9"]

    values = [value for row in grid for value in row]
    messages = []
    if values.count(8):
        messages.append("input must not contain output color 8")
    reflect_count = sum(value in (2, 3) for value in values)
    rotate_count = sum(value in (4, 5, 6, 7) for value in values)
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if reflect_count != 1:
        messages.append(f"expected exactly one reflection control, found {reflect_count}")
    if rotate_count != 1:
        messages.append(f"expected exactly one rotation control, found {rotate_count}")
    if len(anchors) != 1:
        messages.append(f"expected exactly one anchor, found {len(anchors)}")

    components = _components_of(grid, 1)
    if len(components) != 1:
        messages.append(f"expected one connected color-1 template, found {len(components)}")
        return sorted(set(messages))
    template = _normalize(components[0])
    if not 4 <= len(template) <= 7:
        messages.append(f"expected template size 4..7, found {len(template)}")
    if not _asymmetric(template):
        messages.append("template must have eight distinct dihedral images")

    if len(anchors) == 1:
        anchor_r, anchor_c = anchors[0]
        template_h = max(r for r, _ in template) + 1
        template_w = max(c for _, c in template) + 1
        side = max(template_h, template_w)
        height = len(grid)
        if anchor_r + side > height or anchor_c + side > width:
            messages.append("anchor does not have room for transformed stamp")
        else:
            for r in range(anchor_r, anchor_r + side):
                for c in range(anchor_c, anchor_c + side):
                    if (r, c) != (anchor_r, anchor_c) and grid[r][c] != 0:
                        messages.append("transformed-stamp footprint overlaps an input cell")
                        break
                if messages and messages[-1] == "transformed-stamp footprint overlaps an input cell":
                    break
    return sorted(set(messages))


def _draw_from_degenerate(name):
    grid = full_grid(12, 15, 0)
    template = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    if name != "no_reflect_ctrl":
        grid[0][0] = 3
    if name != "no_rotate_ctrl":
        grid[0][2] = 5
    if name != "no_anchor":
        grid[3][6] = 9
    for dr, dc in template:
        grid[7 + dr][10 + dc] = 1
    return grid
