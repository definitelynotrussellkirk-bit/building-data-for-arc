"""Generator for ARC task ``c21f2ce8fb20``.

Gray walls partition the input into three or four rectangular chambers.  Red
cells are seeds.  The selected rule paints the complete chamber containing the
strictly greatest number of red seeds cyan on an otherwise blank output.

The canonical examples never exceed three seeds in a chamber, so a scheduled
four/five-seed case explicitly refutes the plausible ``prefer exactly three``
shortcut.  A second scheduled case makes the true winner neither the largest
nor the densest chamber.
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c21f2ce8fb20"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b86be3a37a68"
EXAMPLES_NEEDED = 4
LESSON_SAMPLE_STRIDE = 11
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A gray field contains three or four separated rectangular 0/2 chambers. "
    "Count red cells in each chamber; paint the unique maximum chamber cyan "
    "on a blank output. Scheduled examples refute exact-three, largest-room, "
    "and highest-density shortcuts."
)

INVARIANTS = [
    "colors are exactly wall gray 5, chamber blank 0, and red seed 2",
    "the outer border is gray and every chamber is a solid rectangle",
    "there are three or four separated chambers, each with seeds and blanks",
    "one chamber has a strict maximum of two to five red seeds",
]

SCHEDULE_PROFILES = (
    "canonical_three_room",
    "canonical_four_room",
    "count_above_three",
    "size_density_decoys",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-aware 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-aware 11..20",
        "valid": "11..20",
    },
    "n_chambers": {
        "type": "int",
        "default": "scheduled 3|4|4|4",
        "valid": "3..4",
    },
    "winner_seeds": {
        "type": "int",
        "default": "scheduled 2|3|4..5|3",
        "valid": "2..5",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

_CANONICAL_THREE_DIMS = ((8, 12), (9, 13))
_CANONICAL_FOUR_DIMS = ((10, 12), (9, 11), (10, 13))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

Grid = list[list[int]]
Cell = tuple[int, int]
Box = tuple[int, int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum slot for a draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _record_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Record a scheduled default while preserving exact full-domain overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = ctx.overrides[label]
        if type(value) is not int:
            raise ValueError(f"{label} override must be an integer, got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside [{lo}, {hi}]")
        ctx.draw_bounds_store[label] = (lo, hi)
        return int(ctx._record(label, value, from_override=True))
    if type(default) is not int or not lo <= default <= hi:
        raise ValueError(f"internal {label} default {default!r} outside [{lo}, {hi}]")
    ctx.draw_bounds_store[label] = (lo, hi)
    return int(ctx._record(label, default, from_override=False))


def _default_dims(ctx, profile: str, difficulty) -> tuple[int, int]:
    if profile == "canonical_three_room":
        return ctx.draw_rng("canonical_three_dims").choice(_CANONICAL_THREE_DIMS)
    if profile == "canonical_four_room":
        return ctx.draw_rng("canonical_four_dims").choice(_CANONICAL_FOUR_DIMS)

    if profile == "size_density_decoys":
        ranges = {
            None: ((10, 16), (14, 20)),
            "easy": ((10, 11), (14, 15)),
            "medium": ((10, 14), (14, 18)),
            "hard": ((12, 16), (16, 20)),
        }
    else:
        ranges = {
            None: ((8, 16), (11, 20)),
            "easy": ((8, 11), (11, 15)),
            "medium": ((10, 14), (13, 18)),
            "hard": ((12, 16), (15, 20)),
        }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[difficulty]
    return (
        ctx.draw_rng("grid_h_default").randint(h_lo, h_hi),
        ctx.draw_rng("grid_w_default").randint(w_lo, w_hi),
    )


def _default_controls(ctx, profile: str) -> tuple[int, int]:
    if profile == "canonical_three_room":
        return 3, 2
    if profile == "canonical_four_room":
        return 4, 3
    if profile == "count_above_three":
        return 4, ctx.draw_rng("winner_seeds_default").choice((4, 5))
    return 4, 3


def _slot_bounds(height: int, width: int, row_wall: int, col_wall: int) -> tuple[Box, ...]:
    return (
        (1, 1, row_wall - 1, col_wall - 1),
        (1, col_wall + 1, row_wall - 1, width - 2),
        (row_wall + 1, 1, height - 2, col_wall - 1),
        (row_wall + 1, col_wall + 1, height - 2, width - 2),
    )


def _box_shape(box: Box) -> tuple[int, int]:
    return box[2] - box[0] + 1, box[3] - box[1] + 1


def _place_sized_box(slot: Box, room_h: int, room_w: int, rng) -> Box:
    r0, c0, r1, c1 = slot
    slot_h, slot_w = _box_shape(slot)
    if not (2 <= room_h <= slot_h and 3 <= room_w <= slot_w):
        raise ValueError(
            f"room {room_h}x{room_w} does not fit slot {slot_h}x{slot_w}"
        )
    top = rng.randint(r0, r1 - room_h + 1)
    left = rng.randint(c0, c1 - room_w + 1)
    return (top, left, top + room_h - 1, left + room_w - 1)


def _ordinary_box(slot: Box, rng) -> Box:
    slot_h, slot_w = _box_shape(slot)
    room_h = rng.randint(2, min(slot_h, 4))
    room_w = rng.randint(3, min(slot_w, 5))
    return _place_sized_box(slot, room_h, room_w, rng)


def _cells(box: Box) -> list[Cell]:
    r0, c0, r1, c1 = box
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def _carve(grid: Grid, box: Box) -> None:
    for r, c in _cells(box):
        grid[r][c] = 0


def _seed_room(grid: Grid, box: Box, count: int, rng) -> None:
    cells = _cells(box)
    if not (1 <= count < len(cells)):
        raise ValueError(f"cannot place {count} seeds with a blank in area {len(cells)}")
    for r, c in rng.sample(cells, count):
        grid[r][c] = 2


def _generic_scene(
    height: int,
    width: int,
    n_chambers: int,
    winner_seeds: int,
    profile: str,
    ctx,
) -> Grid:
    layout_rng = ctx.draw_rng("layout")
    row_wall = layout_rng.randint(3, height - 4)
    col_wall = layout_rng.randint(4, width - 5)
    slots = _slot_bounds(height, width, row_wall, col_wall)

    selected = list(range(4))
    if n_chambers == 3:
        selected.remove(ctx.draw_rng("omitted_slot").randrange(4))
    winner_slot = ctx.draw_rng("winner_slot").choice(selected)

    boxes = {
        slot_index: _ordinary_box(slots[slot_index], ctx.draw_rng(f"room_{slot_index}"))
        for slot_index in selected
    }
    seed_counts = {slot_index: 1 for slot_index in selected}
    seed_counts[winner_slot] = winner_seeds
    losers = [slot_index for slot_index in selected if slot_index != winner_slot]

    if profile == "count_above_three" and winner_seeds > 3:
        three_seed_loser = ctx.draw_rng("three_seed_loser").choice(losers)
        seed_counts[three_seed_loser] = 3
        for slot_index in losers:
            if slot_index != three_seed_loser:
                seed_counts[slot_index] = ctx.draw_rng(
                    f"loser_seeds_{slot_index}"
                ).randint(1, min(2, winner_seeds - 1))
    elif profile == "canonical_four_room" and winner_seeds > 2:
        seed_counts[ctx.draw_rng("two_seed_loser").choice(losers)] = 2
    else:
        for slot_index in losers:
            seed_counts[slot_index] = ctx.draw_rng(
                f"loser_seeds_{slot_index}"
            ).randint(1, winner_seeds - 1)

    grid = full_grid(height, width, 5)
    for slot_index in selected:
        _carve(grid, boxes[slot_index])
        _seed_room(
            grid,
            boxes[slot_index],
            seed_counts[slot_index],
            ctx.draw_rng(f"seeds_{slot_index}"),
        )
    return grid


def _decoy_scene(
    height: int,
    width: int,
    n_chambers: int,
    winner_seeds: int,
    ctx,
) -> Grid | None:
    """Build a proof case where area and density both select losing rooms."""
    if height < 10 or width < 14 or winner_seeds < 3:
        return None

    # These walls guarantee every role shape below fits even at the minimum.
    slots = _slot_bounds(height, width, row_wall=4, col_wall=6)
    role_rng = ctx.draw_rng("decoy_roles")
    largest_candidates = [
        index for index, slot in enumerate(slots)
        if _box_shape(slot)[0] >= 4 and _box_shape(slot)[1] >= 4
    ]
    largest_slot = role_rng.choice(largest_candidates)
    winner_candidates = [
        index for index, slot in enumerate(slots)
        if index != largest_slot
        and _box_shape(slot)[0] >= 3
        and _box_shape(slot)[1] >= 4
    ]
    winner_slot = role_rng.choice(winner_candidates)
    tiny_candidates = [
        index for index in range(4) if index not in (largest_slot, winner_slot)
    ]
    tiny_slot = role_rng.choice(tiny_candidates)
    remaining = [
        index for index in range(4)
        if index not in (largest_slot, winner_slot, tiny_slot)
    ]
    selected = [largest_slot, winner_slot, tiny_slot]
    if n_chambers == 4:
        selected.extend(remaining)

    boxes: dict[int, Box] = {
        largest_slot: _place_sized_box(
            slots[largest_slot], 4, 4, ctx.draw_rng("largest_room")
        ),
        winner_slot: _place_sized_box(
            slots[winner_slot], 3, 4, ctx.draw_rng("winner_room")
        ),
        tiny_slot: _place_sized_box(
            slots[tiny_slot], 2, 3, ctx.draw_rng("tiny_room")
        ),
    }
    for slot_index in remaining:
        if slot_index in selected:
            boxes[slot_index] = _place_sized_box(
                slots[slot_index], 2, 4, ctx.draw_rng("extra_room")
            )

    seed_counts = {
        largest_slot: 1,
        winner_slot: winner_seeds,
        tiny_slot: winner_seeds - 1,
    }
    for slot_index in remaining:
        if slot_index in selected:
            seed_counts[slot_index] = 1

    grid = full_grid(height, width, 5)
    for slot_index in selected:
        _carve(grid, boxes[slot_index])
        _seed_room(
            grid,
            boxes[slot_index],
            seed_counts[slot_index],
            ctx.draw_rng(f"decoy_seeds_{slot_index}"),
        )
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _default_dims(ctx, profile, difficulty)
    default_chambers, default_winner = _default_controls(ctx, profile)
    height = _record_int(ctx, "grid_h", 8, 16, default_h)
    width = _record_int(ctx, "grid_w", 11, 20, default_w)
    n_chambers = _record_int(ctx, "n_chambers", 3, 4, default_chambers)
    winner_seeds = _record_int(ctx, "winner_seeds", 2, 5, default_winner)

    if profile == "size_density_decoys":
        decoy = _decoy_scene(height, width, n_chambers, winner_seeds, ctx)
        if decoy is not None:
            return decoy
    return _generic_scene(
        height,
        width,
        n_chambers,
        winner_seeds,
        profile,
        ctx,
    )


def _regions(grid: Grid) -> list[list[Cell]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return []
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    found: list[list[Cell]] = []
    for start_r in range(height):
        for start_c in range(width):
            start = (start_r, start_c)
            if start in seen or grid[start_r][start_c] not in (0, 2):
                continue
            queue = deque([start])
            seen.add(start)
            component: list[Cell] = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    point = (nr, nc)
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if point in seen or grid[nr][nc] not in (0, 2):
                        continue
                    seen.add(point)
                    queue.append(point)
            found.append(sorted(component))
    return found


def _region_stats(grid: Grid) -> list[dict]:
    result = []
    for cells in _regions(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        result.append(
            {
                "cells": cells,
                "seeds": sum(grid[r][c] == 2 for r, c in cells),
                "area": len(cells),
                "top_left": min(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            }
        )
    return result


def _cell_string(cell: Cell) -> str:
    return f"({cell[0]} {cell[1]})"


def _authority_key(stat: dict):
    return (-stat["seeds"], -stat["area"], _cell_string(stat["top_left"]))


def _paint_selected(grid: Grid, stat: dict | None) -> Grid:
    output = full_grid(len(grid), len(grid[0]) if grid else 0, 0)
    if stat is not None:
        for r, c in stat["cells"]:
            output[r][c] = 8
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror for focused tests; Racket remains label authority."""
    stats = _region_stats(grid)
    return _paint_selected(grid, min(stats, key=_authority_key) if stats else None)


def _prefer_exactly_three(grid: Grid) -> Grid:
    stats = _region_stats(grid)
    if not stats:
        return _paint_selected(grid, None)
    exact_three = [stat for stat in stats if stat["seeds"] == 3]
    exact_two = [stat for stat in stats if stat["seeds"] == 2]
    pool = exact_three or exact_two or stats
    return _paint_selected(grid, min(pool, key=_authority_key))


def _largest_room(grid: Grid) -> Grid:
    stats = _region_stats(grid)
    if not stats:
        return _paint_selected(grid, None)
    chosen = min(
        stats,
        key=lambda stat: (-stat["area"], _cell_string(stat["top_left"])),
    )
    return _paint_selected(grid, chosen)


def _densest_room(grid: Grid) -> Grid:
    stats = _region_stats(grid)
    if not stats:
        return _paint_selected(grid, None)
    chosen = min(
        stats,
        key=lambda stat: (
            -(stat["seeds"] / stat["area"]),
            -stat["seeds"],
            -stat["area"],
            _cell_string(stat["top_left"]),
        ),
    )
    return _paint_selected(grid, chosen)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "prefer_exactly_three": _prefer_exactly_three,
    "largest_room": _largest_room,
    "densest_room": _densest_room,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All five canonical winners contain two or three seeds; no canonical pair
    # contains a four/five-seed chamber that can falsify this priority rule.
    "prefer_exactly_three": _prefer_exactly_three,
}


def _witness_count_above_three(grid: Grid) -> bool:
    stats = _region_stats(grid)
    return bool(
        stats
        and max(stat["seeds"] for stat in stats) > 3
        and any(stat["seeds"] == 3 for stat in stats)
        and rule_mirror(grid) != _prefer_exactly_three(grid)
    )


def _witness_not_largest(grid: Grid) -> bool:
    return bool(_region_stats(grid)) and rule_mirror(grid) != _largest_room(grid)


def _witness_not_densest(grid: Grid) -> bool:
    return bool(_region_stats(grid)) and rule_mirror(grid) != _densest_room(grid)


SEMANTIC_WITNESSES = {
    "count_above_three": _witness_count_above_three,
    "winner_not_largest": _witness_not_largest,
    "winner_not_densest": _witness_not_densest,
}
WITNESS_RIVALS = {
    "count_above_three": ["prefer_exactly_three"],
    "winner_not_largest": ["largest_room"],
    "winner_not_densest": ["densest_room"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name every rival still compatible with a complete four-demo lesson."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with selected rule")
    if query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but answers the query differently"
                )
            else:
                reasons.append(f"{name} survives every demonstration and the query")
    return reasons


def observe_overrides(grid: Grid) -> dict[str, int]:
    stats = _region_stats(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_chambers": len(stats),
        "winner_seeds": max((stat["seeds"] for stat in stats), default=0),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and structural impostors without raising."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 16 and 11 <= width <= 20):
        errors.append(f"grid dimensions {height}x{width} outside 8..16 by 11..20")
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            return errors + ["grid must be rectangular"]
        for value in row:
            if type(value) is not int or value not in (0, 2, 5):
                return errors + [f"invalid cell value {value!r}; expected only 0, 2, 5"]

    palette = {value for row in grid for value in row}
    if palette != {0, 2, 5}:
        errors.append(f"expected palette {{0, 2, 5}}, found {sorted(palette)}")
    if any(value != 5 for value in grid[0] + grid[-1]):
        errors.append("top and bottom borders must be gray wall 5")
    if any(row[0] != 5 or row[-1] != 5 for row in grid):
        errors.append("left and right borders must be gray wall 5")

    stats = _region_stats(grid)
    if not 3 <= len(stats) <= 4:
        errors.append(f"expected three or four chambers, found {len(stats)}")

    for index, stat in enumerate(stats):
        r0, c0, r1, c1 = stat["bbox"]
        bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if stat["area"] != bbox_area:
            errors.append(f"chamber {index} is not a solid axis-aligned rectangle")
        if stat["area"] < 6:
            errors.append(f"chamber {index} area {stat['area']} is below six cells")
        values = [grid[r][c] for r, c in stat["cells"]]
        if 2 not in values:
            errors.append(f"chamber {index} has no red seed")
        if 0 not in values:
            errors.append(f"chamber {index} has no blank chamber cell")

    seed_counts = [stat["seeds"] for stat in stats]
    if seed_counts:
        maximum = max(seed_counts)
        if not 2 <= maximum <= 5:
            errors.append(f"winning seed count {maximum} outside 2..5")
        if seed_counts.count(maximum) != 1:
            errors.append(f"expected a strict maximum seed count, found {seed_counts}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)
