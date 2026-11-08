"""Constructive matched-input episodes for the chamber-count rule family.

The canonical setting paints the chamber whose red-seed count equals the
control.  The relay setting first finds that same cue chamber, reads its height,
then paints the distinct chamber whose red-seed count equals that height.
"""
from __future__ import annotations

import random
from typing import Iterable

MODES = ("direct", "height_relay")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

Rect = tuple[int, int, int, int]


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def validate_request(seed: int, settings: dict, demos: int, queries: int) -> str:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, *DEMO_LIMITS)
    _integer("queries", queries, *QUERY_LIMITS)
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _cells(rect: Rect) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = rect
    return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def _vertical_strips(rect: Rect, count: int, rng: random.Random) -> list[Rect]:
    r1, c1, r2, c2 = rect
    width = c2 - c1 + 1
    free = width - (count - 1)
    if count < 1 or free < count:
        raise ValueError("rectangle is too narrow for requested vertical strips")
    sizes = [1] * count
    for _ in range(free - count):
        sizes[rng.randrange(count)] += 1
    if rng.randrange(2):
        sizes.reverse()
    result = []
    c = c1
    for size in sizes:
        result.append((r1, c, r2, c + size - 1))
        c += size + 1
    return result


def _horizontal_strips(rect: Rect, count: int, rng: random.Random) -> list[Rect]:
    r1, c1, r2, c2 = rect
    height = r2 - r1 + 1
    free = height - (count - 1)
    if count < 1 or free < count:
        raise ValueError("rectangle is too short for requested horizontal strips")
    sizes = [1] * count
    for _ in range(free - count):
        sizes[rng.randrange(count)] += 1
    if rng.randrange(2):
        sizes.reverse()
    result = []
    r = r1
    for size in sizes:
        result.append((r, c1, r + size - 1, c2))
        r += size + 1
    return result


def _profile(pair_index: int, *, is_query: bool, query_index: int, queries: int) -> tuple[int, int, int, str]:
    if is_query and queries == 4 and query_index == 3:
        return 30, 30, 6, "horizontal"
    profiles = (
        (7, 9, 4, "horizontal"),
        (12, 16, 5, "vertical"),
        (16, 20, 6, "horizontal"),
        (18, 14, 5, "vertical"),
        (21, 23, 6, "horizontal"),
        (14, 19, 4, "vertical"),
    )
    return profiles[pair_index % len(profiles)]


def _layout(h: int, w: int, n: int, cue_height: int, orientation: str,
            rng: random.Random) -> tuple[list[Rect], int]:
    top, left, bottom, right = 1, 1, h - 2, w - 2
    if orientation == "horizontal":
        cue_at_start = bool(rng.randrange(2))
        if cue_at_start:
            band = (top, left, top + cue_height - 1, right)
            rest = (top + cue_height + 1, left, bottom, right)
        else:
            band = (bottom - cue_height + 1, left, bottom, right)
            rest = (top, left, bottom - cue_height - 1, right)
        band_rooms = _vertical_strips(band, 2, rng)
        roomy = [i for i, rect in enumerate(band_rooms) if len(_cells(rect)) >= 6]
        cue_local = rng.choice(roomy or [max(range(2), key=lambda i: len(_cells(band_rooms[i])))])
        rest_rooms = _vertical_strips(rest, n - 2, rng)
    elif orientation == "vertical":
        interior_h = bottom - top + 1
        sibling_height = interior_h - cue_height - 1
        if sibling_height < 1:
            raise ValueError("vertical cue split has no sibling room")
        zone_width = min(max(2, 2 + rng.randrange(max(1, (w - 4) // 3))), w - 5)
        zone_at_start = bool(rng.randrange(2))
        if zone_at_start:
            zone = (top, left, bottom, left + zone_width - 1)
            rest = (top, left + zone_width + 1, bottom, right)
        else:
            zone = (top, right - zone_width + 1, bottom, right)
            rest = (top, left, bottom, right - zone_width - 1)
        cue_at_start = bool(rng.randrange(2))
        if cue_at_start:
            cue = (top, zone[1], top + cue_height - 1, zone[3])
            sibling = (top + cue_height + 1, zone[1], bottom, zone[3])
        else:
            sibling = (top, zone[1], bottom - cue_height - 1, zone[3])
            cue = (bottom - cue_height + 1, zone[1], bottom, zone[3])
        band_rooms = [cue, sibling]
        cue_local = 0
        rest_rooms = _horizontal_strips(rest, n - 2, rng)
    else:
        raise ValueError("unknown layout orientation")
    rooms = band_rooms + rest_rooms
    return rooms, cue_local


def _center(rect: Rect) -> tuple[float, float]:
    r1, c1, r2, c2 = rect
    return (r1 + r2) / 2, (c1 + c2) / 2


def _choose_destination(rects: list[Rect], cue_index: int, relay_count: int,
                        pair_index: int) -> int:
    cr, cc = _center(rects[cue_index])
    eligible = [i for i, rect in enumerate(rects)
                if i != cue_index and len(_cells(rect)) >= relay_count]
    if len(eligible) < 2:
        raise ValueError("relay lessons need at least two eligible destinations")
    ordered = sorted(eligible, key=lambda i: (
        abs(_center(rects[i])[0] - cr) + abs(_center(rects[i])[1] - cc), i))
    role = pair_index % 3
    if role == 0:
        # The first teaching scene reserves the cue's sibling chamber as the
        # relay target.  On the minimum 7x9 profile this leaves a guaranteed
        # six-cell-capacity chamber for the high-count distractor below.
        sibling = 1 - cue_index if cue_index in (0, 1) else None
        if sibling in eligible:
            return sibling
        return ordered[0]
    if role == 1:
        return ordered[-1]
    return ordered[len(ordered) // 2]


def _seed_positions(room: list[tuple[int, int]], count: int, rng: random.Random,
                    *, vertical_pair: bool = False) -> list[tuple[int, int]]:
    if not 0 <= count <= len(room):
        raise ValueError("seed count exceeds chamber capacity")
    chosen: list[tuple[int, int]] = []
    if vertical_pair and count >= 2:
        available = set(room)
        pairs = [(r, c) for r, c in room if (r + 1, c) in available]
        if pairs:
            r, c = rng.choice(pairs)
            chosen.extend([(r, c), (r + 1, c)])
    remaining = [cell for cell in room if cell not in chosen]
    chosen.extend(rng.sample(remaining, count - len(chosen)))
    return chosen


def _output(grid: list[list[int]], room: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for r, c in room:
        out[r][c] = 8
    return out


def _build_scene(seed: int, pair_index: int, *, is_query: bool,
                 query_index: int, queries: int) -> tuple[list[list[int]], list[tuple[int, int]], list[tuple[int, int]]]:
    h, w, n, orientation = _profile(pair_index, is_query=is_query,
                                     query_index=query_index, queries=queries)
    rng = random.Random((seed + 1) * 1_000_003 + (pair_index + 1) * 97_409)
    interior_h = h - 2
    max_cue_height = min(6, interior_h - 2)
    teaching_heights = (2, 4, 3)
    if not is_query and pair_index < len(teaching_heights):
        cue_height = teaching_heights[pair_index]
    else:
        cue_height = 2 + ((seed + pair_index * 3) % (max_cue_height - 1))
    rects, cue_index = _layout(h, w, n, cue_height, orientation, rng)
    rooms = [_cells(rect) for rect in rects]
    destination_index = _choose_destination(rects, cue_index, cue_height, pair_index)

    preferred_controls = (1, 6, 5, 2, 4, 3)
    teaching_controls = (5, 2, 6)
    control = (teaching_controls[pair_index]
               if not is_query and pair_index < len(teaching_controls)
               else preferred_controls[(seed + pair_index) % len(preferred_controls)])
    candidates = [value for value in preferred_controls
                  if value != cue_height and value <= len(rooms[cue_index])]
    if control not in candidates:
        control = candidates[0]

    counts: list[int] = []
    for i, room in enumerate(rooms):
        if i == cue_index:
            counts.append(control)
        elif i == destination_index:
            counts.append(cue_height)
        else:
            allowed = [value for value in range(min(7, len(room)) + 1)
                       if value not in {control, cue_height}]
            counts.append(allowed[rng.randrange(len(allowed))])
    if not is_query and pair_index == 0:
        # Six is strictly above the teaching control (5) and is the largest
        # distractor count guaranteed by the minimum 7x9 chamber geometry.
        high_count = 6
        high_rooms = [i for i, room in enumerate(rooms)
                      if i not in {cue_index, destination_index} and len(room) >= high_count]
        if not high_rooms:
            raise ValueError("teaching scene lacks the guaranteed six-seed distractor")
        counts[high_rooms[0]] = high_count


    grid = [[5] * w for _ in range(h)]
    for room in rooms:
        for r, c in room:
            grid[r][c] = 0
    for i, (room, count) in enumerate(zip(rooms, counts)):
        positions = _seed_positions(room, count, rng, vertical_pair=(i == cue_index))
        for r, c in positions:
            grid[r][c] = 2
    grid[0][0] = control
    return grid, rooms[cue_index], rooms[destination_index]


def generate_pairs(seed: int, demos: int, queries: int, mode: str) -> list[dict]:
    pairs = []
    for pair_index in range(demos + queries):
        is_query = pair_index >= demos
        query_index = pair_index - demos if is_query else -1
        grid, cue, destination = _build_scene(
            seed, pair_index, is_query=is_query, query_index=query_index, queries=queries)
        selected = cue if mode == "direct" else destination
        pairs.append({"input": grid, "output": _output(grid, selected)})
    return pairs
