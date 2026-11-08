"""Generator for highlighting walls around color-2 seeded rooms.

The canonical rule treats colors 1, 7, and 9 as walls, extracts every connected
non-wall room, and paints the color-1/color-7 boundary cells of rooms containing
color 2.  This repaired source covers the authoritative single-row, nonuniform,
and off-center-seed geometries while making advertised full-grid dimensions
observable and strict.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = "e5ec1ac39df5"
VERSION = "3.0.0"
SUMMARY = (
    "A one- to four-row by one- to four-column lattice of rectangular rooms is "
    "separated by color-1 walls, optionally with color-7 door cells. One or more "
    "rooms contain a color-2 seed, centered or off center. Paint on a blank grid "
    "the color-1/color-7 wall cells immediately adjacent to every seeded room."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "outer boundary is wall-colored",
    "non-wall connected components are rectangular rooms",
    "each seeded room contains exactly one color-2 cell",
    "room sizes may be nonuniform and seeds need not be centered",
]
WALLS = {1, 7, 9}
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 9..30", "valid": "7..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 9..30", "valid": "7..30"},
    "rooms_r": {"type": "int", "default": "rng subject to grid", "valid": "1..4"},
    "rooms_c": {"type": "int", "default": "rng subject to grid", "valid": "1..4"},
    "seed_count": {"type": "int", "default": "rng 1..half rooms", "valid": "1..rooms"},
    "off_center_seeds": {"type": "bool", "default": "rng", "valid": "true|false"},
    "door_count": {"type": "int", "default": "rng 0..4 subject to adjacency", "valid": "0..24"},
}


def _strict_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    for name in ("grid_h", "grid_w", "rooms_r", "rooms_c", "seed_count", "door_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an exact integer")
    value = overrides.get("off_center_seeds")
    if value is not None and type(value) is not bool:
        raise TypeError("off_center_seeds override must be an exact bool")


def _provided(overrides: dict, name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _partition(total: int, count: int, rng) -> list[int]:
    if count < 1 or total < 3 * count:
        raise ValueError("grid dimension cannot fit requested room count")
    sizes = [3] * count
    for _ in range(total - 3 * count):
        sizes[rng.randrange(count)] += 1
    # Where the arithmetic permits variation, avoid making every ordinary draw
    # uniform; authoritative examples explicitly include nonuniform rooms.
    if count > 1 and len(set(sizes)) == 1:
        donor = next((i for i, value in enumerate(sizes) if value > 3), None)
        if donor is not None:
            receiver = (donor + 1) % count
            sizes[donor] -= 1
            sizes[receiver] += 1
    rng.shuffle(sizes)
    return sizes


def _draw_dimension(ctx, overrides: dict, name: str) -> int:
    if _provided(overrides, name):
        return ctx.draw_int_strict(name, 7, 30)
    return ctx.draw_int_diff(name, 9, 30)


def _draw_counts(ctx, overrides: dict, h: int, w: int) -> tuple[int, int]:
    max_r = min(4, (h - 1) // 4)
    max_c = min(4, (w - 1) // 4)
    if max_r < 1 or max_c < 1:
        raise ValueError("grid is too small for a rectangular room")

    if _provided(overrides, "rooms_r"):
        nr = ctx.draw_int_strict("rooms_r", 1, 4)
        if nr > max_r:
            raise ValueError("rooms_r does not fit grid_h with 3-cell interiors")
    else:
        nr = None
    if _provided(overrides, "rooms_c"):
        nc = ctx.draw_int_strict("rooms_c", 1, 4)
        if nc > max_c:
            raise ValueError("rooms_c does not fit grid_w with 3-cell interiors")
    else:
        nc = None

    if nr is None and nc is None:
        nr = ctx.draw_int("rooms_r", 1, max_r)
        nc = ctx.draw_int("rooms_c", 2 if nr == 1 and max_c >= 2 else 1, max_c)
    elif nr is None:
        nr = ctx.draw_int("rooms_r", 2 if nc == 1 and max_r >= 2 else 1, max_r)
    elif nc is None:
        nc = ctx.draw_int("rooms_c", 2 if nr == 1 and max_c >= 2 else 1, max_c)
    return nr, nc


def _rooms(row_sizes: list[int], col_sizes: list[int]):
    result = []
    r0 = 1
    for rh in row_sizes:
        row = []
        c0 = 1
        for cw in col_sizes:
            row.append((r0, c0, rh, cw))
            c0 += cw + 1
        result.append(row)
        r0 += rh + 1
    return result


def _adjacency_doors(rooms):
    nr, nc = len(rooms), len(rooms[0])
    doors = []
    for ri in range(nr):
        for ci in range(nc - 1):
            r, c, h, w = rooms[ri][ci]
            doors.append((r + h // 2, c + w))
    for ri in range(nr - 1):
        for ci in range(nc):
            r, c, h, w = rooms[ri][ci]
            doors.append((r + h, c + w // 2))
    return doors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_dimension(ctx, overrides, "grid_h")
    w = _draw_dimension(ctx, overrides, "grid_w")
    nr, nc = _draw_counts(ctx, overrides, h, w)
    row_sizes = _partition(h - nr - 1, nr, ctx.draw_rng("row_partition"))
    col_sizes = _partition(w - nc - 1, nc, ctx.draw_rng("col_partition"))
    rooms = _rooms(row_sizes, col_sizes)

    grid = [[1 for _ in range(w)] for _ in range(h)]
    for row in rooms:
        for r0, c0, rh, cw in row:
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + cw):
                    grid[r][c] = 0

    doors = _adjacency_doors(rooms)
    if _provided(overrides, "door_count"):
        door_count = ctx.draw_int_strict("door_count", 0, 24)
        if door_count > len(doors):
            raise ValueError("door_count exceeds room-lattice adjacencies")
    else:
        door_count = ctx.draw_int("door_count", 0, min(4, len(doors)))
    door_rng = ctx.draw_rng("doors")
    door_rng.shuffle(doors)
    for r, c in doors[:door_count]:
        grid[r][c] = 7

    room_ids = [(ri, ci) for ri in range(nr) for ci in range(nc)]
    if _provided(overrides, "seed_count"):
        seed_count = ctx.draw_int_strict("seed_count", 1, 16)
        if seed_count > len(room_ids):
            raise ValueError("seed_count exceeds room count")
    else:
        seed_count = ctx.draw_int("seed_count", 1, max(1, len(room_ids) // 2))
    off_center = ctx.draw_choice("off_center_seeds", (False, True))
    seed_rng = ctx.draw_rng("seed_rooms")
    chosen = seed_rng.sample(room_ids, seed_count)
    for ri, ci in chosen:
        r0, c0, rh, cw = rooms[ri][ci]
        center = (r0 + rh // 2, c0 + cw // 2)
        if off_center:
            candidates = [
                (r, c)
                for r in range(r0, r0 + rh)
                for c in range(c0, c0 + cw)
                if (r, c) != center
            ]
            r, c = seed_rng.choice(candidates)
        else:
            r, c = center
        grid[r][c] = 2
    return grid


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] in WALLS or (sr, sc) in seen:
                continue
            todo = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = set()
            while todo:
                r, c = todo.popleft()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] not in WALLS
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return result


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    messages = []
    if h > 30 or w > 30:
        messages.append("grid exceeds 30x30")
    if any(type(value) is not int or value not in {0, 1, 2, 7, 9} for row in grid for value in row):
        messages.append("room task uses floor 0, seed 2, and wall colors 1/7/9")
        return sorted(set(messages))
    if any(grid[0][c] not in WALLS or grid[h - 1][c] not in WALLS for c in range(w)):
        messages.append("outer horizontal boundary must be wall-colored")
    if any(grid[r][0] not in WALLS or grid[r][w - 1] not in WALLS for r in range(h)):
        messages.append("outer vertical boundary must be wall-colored")

    rooms = _components(grid)
    if not rooms:
        messages.append("at least one non-wall room is required")
        return sorted(set(messages))
    cell_to_room = {}
    seeded = 0
    for room_id, cells in enumerate(rooms):
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        rectangle = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if cells != rectangle:
            messages.append("non-wall connected components must be rectangular rooms")
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            messages.append("room interiors must be at least 3x3")
        seeds = [(r, c) for r, c in cells if grid[r][c] == 2]
        if len(seeds) > 1:
            messages.append("a room may contain at most one color-2 seed")
        seeded += bool(seeds)
        for cell in cells:
            cell_to_room[cell] = room_id
    if seeded < 1:
        messages.append("at least one room must contain a color-2 seed")

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 7:
                continue
            adjacent = {
                cell_to_room[(nr, nc)]
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                if (nr, nc) in cell_to_room
            }
            if len(adjacent) != 2:
                messages.append("each color-7 door must connect exactly two rooms")
    return sorted(set(messages))
