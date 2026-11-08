"""Generator for Recolor the Anchor's Neighbors (a4fb12580b3f).

The unique color-1 component is the anchor.  Every other monochromatic
component that touches the anchor by an edge is recolored to 4; all components
that do not touch the anchor stay unchanged.

The generated distribution varies canvas size, anchor shape, palette, touching
component count, component morphology, and non-neighbor count.  Every ordinary
draw contains at least one visibly changed neighbor and at least one preserved
non-neighbor.  Most draws also repeat a neighbor color on a disconnected
non-neighbor, ruling out color-global recoloring shortcuts.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4fb12580b3f"
TASK_ID = "a4fb12580b3f"
VERSION = "2.0.0"
RULE_HASH = "c58ce5ec72e9"
SUMMARY = (
    "Find the unique color-1 anchor component and recolor every non-background "
    "component that edge-touches it to 4; preserve the anchor and all non-neighbors."
)

INVARIANTS = [
    "background is 0",
    "there is exactly one connected color-1 anchor component",
    "two to four non-background components edge-touch the anchor",
    "at least one touching component is not already color 4",
    "at least one non-neighbor distractor component is separated from the anchor",
]

PALETTES = {
    "default": (3, 6, 8, 7, 2, 5, 9),
    "warm": (2, 3, 7, 9, 6, 5, 8),
    "cool": (8, 6, 5, 2, 3, 7, 9),
    "varied": (5, 9, 2, 8, 3, 7, 6),
}
ANCHOR_SHAPES = ("dot", "domino", "elbow")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw across 7..15",
        "valid": "7..15",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw across 8..16",
        "valid": "8..16",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng default|warm|cool|varied",
        "valid": "default|warm|cool|varied",
    },
    "anchor_shape": {
        "type": "str",
        "default": "rng dot|domino|elbow",
        "valid": "dot|domino|elbow",
    },
    "neighbor_count": {
        "type": "int",
        "default": "difficulty-aware draw across 2..4",
        "valid": "2..4",
    },
    "distractor_count": {
        "type": "int",
        "default": "difficulty-aware draw across 2..4",
        "valid": "2..4",
    },
}

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _inside(h: int, w: int, cell: tuple[int, int]) -> bool:
    r, c = cell
    return 0 <= r < h and 0 <= c < w


def _neighbors4(cell: tuple[int, int]):
    r, c = cell
    for dr, dc in CARDINAL:
        yield r + dr, c + dc


def _paint(grid, cells, color: int) -> None:
    for r, c in cells:
        grid[r][c] = color


def _shape_cells(name: str, rng) -> set[tuple[int, int]]:
    if name == "dot":
        return {(0, 0)}
    if name == "domino":
        return {(0, 0), (0, 1)} if rng.randrange(2) == 0 else {(0, 0), (1, 0)}

    # Four rotations of a three-cell elbow.
    variants = (
        {(0, 0), (1, 0), (1, 1)},
        {(0, 0), (0, 1), (1, 0)},
        {(0, 0), (0, 1), (1, 1)},
        {(0, 1), (1, 0), (1, 1)},
    )
    return set(variants[rng.randrange(len(variants))])


def _translated(cells, row: int, col: int) -> set[tuple[int, int]]:
    return {(r + row, c + col) for r, c in cells}


def _component_boundary(anchor: set[tuple[int, int]], h: int, w: int):
    """Return exterior cells grouped by their direction from the anchor."""
    groups: dict[tuple[int, int], list[tuple[int, int]]] = {
        delta: [] for delta in CARDINAL
    }
    for r, c in sorted(anchor):
        for dr, dc in CARDINAL:
            cell = (r + dr, c + dc)
            if _inside(h, w, cell) and cell not in anchor:
                groups[(dr, dc)].append(cell)
    for values in groups.values():
        # Deduplicate cells adjacent to two anchor cells while preserving order.
        values[:] = list(dict.fromkeys(values))
    return groups


def _grow_component(
    start: tuple[int, int],
    target_size: int,
    *,
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    reserved: set[tuple[int, int]],
    anchor: set[tuple[int, int]],
    rng,
) -> set[tuple[int, int]]:
    cells = {start}
    while len(cells) < target_size:
        candidates = {
            nxt
            for cell in cells
            for nxt in _neighbors4(cell)
            if _inside(h, w, nxt)
            and nxt not in cells
            and nxt not in forbidden
            and nxt not in reserved
        }
        if not candidates:
            break
        # Prefer growth away from the anchor, but retain stochastic morphology.
        def distance(cell):
            return min(abs(cell[0] - ar) + abs(cell[1] - ac) for ar, ac in anchor)

        ordered = sorted(candidates, key=lambda cell: (distance(cell), cell), reverse=True)
        top = ordered[: max(1, min(4, len(ordered)))]
        cells.add(top[rng.randrange(len(top))])
    return cells


def _place_distractor(
    grid,
    color: int,
    target_size: int,
    *,
    anchor: set[tuple[int, int]],
    occupied: set[tuple[int, int]],
    same_color_cells: set[tuple[int, int]],
    rng,
) -> set[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    anchor_halo = {nxt for cell in anchor for nxt in _neighbors4(cell)} | anchor

    starts = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in occupied
        and (r, c) not in anchor_halo
        and not any(nxt in same_color_cells for nxt in _neighbors4((r, c)))
    ]
    # Far cells make the non-neighbor relation visually explicit.
    starts.sort(
        key=lambda cell: (
            min(abs(cell[0] - ar) + abs(cell[1] - ac) for ar, ac in anchor),
            cell,
        ),
        reverse=True,
    )
    if not starts:
        raise ValueError("unable to place a non-neighbor distractor")

    # Try several starts because local growth can be blocked on the smallest canvas.
    for attempt in range(min(40, len(starts))):
        start = starts[(attempt + rng.randrange(len(starts))) % len(starts)]
        cells = {start}
        while len(cells) < target_size:
            candidates = []
            for cell in cells:
                for nxt in _neighbors4(cell):
                    if not _inside(h, w, nxt) or nxt in cells or nxt in occupied:
                        continue
                    if nxt in anchor_halo:
                        continue
                    # Same-colored components must remain disconnected.
                    if any(adj in same_color_cells for adj in _neighbors4(nxt)):
                        continue
                    candidates.append(nxt)
            candidates = list(dict.fromkeys(candidates))
            if not candidates:
                break
            candidates.sort()
            cells.add(candidates[rng.randrange(len(candidates))])
        if cells:
            return cells
    raise ValueError("unable to grow a non-neighbor distractor")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, set[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = {(r, c)}
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                cell = queue.popleft()
                for nxt in _neighbors4(cell):
                    nr, nc = nxt
                    if (
                        _inside(h, w, nxt)
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        cells.add(nxt)
                        queue.append(nxt)
            out.append((color, cells))
    return out


def _touches(left: set[tuple[int, int]], right: set[tuple[int, int]]) -> bool:
    return any(nxt in right for cell in left for nxt in _neighbors4(cell))


def _semantic_counts(grid) -> dict[str, int]:
    components = _components(grid)
    anchors = [cells for color, cells in components if color == 1]
    if len(anchors) != 1:
        return {
            "grid_h": len(grid),
            "grid_w": len(grid[0]) if grid else 0,
            "neighbor_count": -1,
            "distractor_count": -1,
        }
    anchor = anchors[0]
    others = [(color, cells) for color, cells in components if color != 1]
    neighbor_count = sum(_touches(anchor, cells) for _, cells in others)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "neighbor_count": neighbor_count,
        "distractor_count": len(others) - neighbor_count,
    }


def observe_overrides(grid) -> dict[str, int]:
    """Expose exact realized dimensions and component-role counts."""
    return _semantic_counts(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical component grammar, not merely palette/shape."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    errors: list[str] = []
    flat = [value for row in grid for value in row]
    if flat.count(0) <= len(flat) // 2:
        errors.append("background 0 must occupy a strict majority of the canvas")

    components = _components(grid)
    anchor_components = [cells for color, cells in components if color == 1]
    if len(anchor_components) != 1:
        errors.append("expected exactly one connected color-1 anchor component")
        return errors

    anchor = anchor_components[0]
    others = [(color, cells) for color, cells in components if color != 1]
    touching = [(color, cells) for color, cells in others if _touches(anchor, cells)]
    non_touching = [(color, cells) for color, cells in others if not _touches(anchor, cells)]
    if not 2 <= len(touching) <= 4:
        errors.append("expected two to four components edge-touching the anchor")
    if not non_touching:
        errors.append("expected at least one component separated from the anchor")
    if touching and all(color == 4 for color, _ in touching):
        errors.append("at least one touching component must visibly change to color 4")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 7, 15)
    w = ctx.draw_int_diff("grid_w", 8, 16)
    palette_kind = ctx.draw_choice("palette_kind", tuple(PALETTES))
    anchor_shape = ctx.draw_choice("anchor_shape", ANCHOR_SHAPES)
    neighbor_count = ctx.draw_int_diff("neighbor_count", 2, 4)
    distractor_count = ctx.draw_int_diff("distractor_count", 2, 4)
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    local_anchor = _shape_cells(anchor_shape, rng)
    anchor_h = max(r for r, _ in local_anchor) + 1
    anchor_w = max(c for _, c in local_anchor) + 1
    row = rng.randint(2, h - anchor_h - 2)
    col = rng.randint(2, w - anchor_w - 2)
    anchor = _translated(local_anchor, row, col)
    _paint(grid, anchor, 1)

    boundary = _component_boundary(anchor, h, w)
    directions = list(CARDINAL)
    rng.shuffle(directions)
    attachments: list[tuple[int, int]] = []
    # Prefer distinct sides first; then fill from remaining anchor boundary cells.
    for direction in directions:
        choices = [cell for cell in boundary[direction] if cell not in attachments]
        if choices:
            attachments.append(choices[rng.randrange(len(choices))])
        if len(attachments) == neighbor_count:
            break
    if len(attachments) < neighbor_count:
        remaining = sorted(
            {
                cell
                for values in boundary.values()
                for cell in values
                if cell not in attachments
            }
        )
        rng.shuffle(remaining)
        attachments.extend(remaining[: neighbor_count - len(attachments)])
    if len(attachments) != neighbor_count:
        raise ValueError("anchor shape does not expose enough neighbor attachment cells")

    palette = list(PALETTES[palette_kind])
    rng.shuffle(palette)
    # In every five-pair episode, the deterministic residue schedule includes at
    # least one already-4 touching component, mirroring the canonical test branch.
    include_output_neighbor = sample_index % 5 == 1
    neighbor_colors = palette[:neighbor_count]
    if include_output_neighbor:
        neighbor_colors[-1] = 4
    # Preserve at least one visibly changed neighbor even under all schedules.
    if all(color == 4 for color in neighbor_colors):
        neighbor_colors[0] = palette[0]

    occupied = set(anchor) | set(attachments)
    reserved = set(attachments)
    color_cells: dict[int, set[tuple[int, int]]] = {1: set(anchor)}
    neighbor_components: list[tuple[int, set[tuple[int, int]]]] = []
    max_neighbor_size = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
    for index, (start, color) in enumerate(zip(attachments, neighbor_colors)):
        size_rng = ctx.draw_rng(f"neighbor_size_{index}")
        target_size = size_rng.randint(1, max_neighbor_size)
        if index == 0:
            target_size = max(2, target_size)
        cells = _grow_component(
            start,
            target_size,
            h=h,
            w=w,
            forbidden=occupied - {start},
            reserved=reserved - {start},
            anchor=anchor,
            rng=size_rng,
        )
        if index == 0 and all(
            min(abs(cell[0] - ar) + abs(cell[1] - ac) for ar, ac in anchor) == 1
            for cell in cells
        ):
            outward = sorted(
                {
                    nxt
                    for cell in cells
                    for nxt in _neighbors4(cell)
                    if _inside(h, w, nxt)
                    and nxt not in cells
                    and nxt not in occupied
                    and nxt not in (reserved - {start})
                    and min(
                        abs(nxt[0] - ar) + abs(nxt[1] - ac)
                        for ar, ac in anchor
                    )
                    > 1
                }
            )
            if not outward:
                raise ValueError("unable to extend the first neighbor away from the anchor")
            cells.add(outward[size_rng.randrange(len(outward))])
        _paint(grid, cells, color)
        occupied.update(cells)
        color_cells.setdefault(color, set()).update(cells)
        neighbor_components.append((color, cells))

    changed_neighbor_colors = [color for color, _ in neighbor_components if color != 4]
    repeated_color = changed_neighbor_colors[0]
    distractor_colors = [repeated_color]
    remaining_colors = [color for color in palette if color != repeated_color]
    if sample_index % 5 == 2 and distractor_count > 1:
        distractor_colors.append(4)
    while len(distractor_colors) < distractor_count:
        distractor_colors.append(remaining_colors[(len(distractor_colors) - 1) % len(remaining_colors)])

    max_distractor_size = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
    for index, color in enumerate(distractor_colors):
        size_rng = ctx.draw_rng(f"distractor_size_{index}")
        target_size = size_rng.randint(1, max_distractor_size)
        cells = _place_distractor(
            grid,
            color,
            target_size,
            anchor=anchor,
            occupied=occupied,
            same_color_cells=color_cells.get(color, set()),
            rng=size_rng,
        )
        _paint(grid, cells, color)
        occupied.update(cells)
        color_cells.setdefault(color, set()).update(cells)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid
