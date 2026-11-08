"""Parametric thick-cursor route family for public ARC parent e87109e9."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("header", "opposite")
DIRECTIONS = {
    "up": (-1, 0),
    "right": (0, 1),
    "down": (1, 0),
    "left": (0, -1),
}
VECTOR_NAMES = {value: key for key, value in DIRECTIONS.items()}


def integer(value, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def grid(value):
    if (type(value) is not list or not 7 <= len(value) <= 30
            or type(value[0]) is not list or len(value[0]) != 24):
        raise ValueError("expected a 7..30 by 24 exact-integer grid")
    for row in value:
        if (type(row) is not list or len(row) != 24
                or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)):
            raise ValueError("expected a 7..30 by 24 exact-integer grid")
    return value


def instructions(value) -> list[dict[str, object]]:
    value = grid(value)
    if any(cell != 5 for cell in value[0] + value[5]):
        raise ValueError("header top and bottom borders must be color 5")
    result = []
    seen = set()
    for box in range(4):
        base = 6 * box
        columns = []
        colors = []
        for r in range(1, 5):
            if value[r][base] != 5 or value[r][base + 5] != 5:
                raise ValueError("each header box must retain color-5 side borders")
            interior = value[r][base + 1:base + 5]
            marked = [(index, cell) for index, cell in enumerate(interior) if cell != 0]
            if len(marked) != 1:
                raise ValueError("each header row needs exactly one nonzero marker")
            column, color = marked[0]
            if column not in (0, 3) or color in (0, 5, 8):
                raise ValueError("header marker must use an outer interior column and task color")
            columns.append(column)
            colors.append(color)
        if len(set(columns)) != 1 or len(set(colors)) != 1 or colors[0] in seen:
            raise ValueError("each box needs one consistent, distinct target-color marker")
        seen.add(colors[0])
        result.append({"color": colors[0], "side": "left" if columns[0] == 0 else "right"})
    return result


def setting(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"turn_rule"}
            or type(settings["turn_rule"]) is not str
            or settings["turn_rule"] not in MODES):
        raise ValueError("settings must name exactly one declared turn_rule")
    return settings["turn_rule"]


def program(settings) -> str:
    mode = setting(settings)
    filename = "canonical.rkt" if mode == "header" else "opposite-turn.rkt"
    return (HERE / filename).read_text()


def _bbox(points: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in points),
        max(r for r, _ in points),
        min(c for _, c in points),
        max(c for _, c in points),
    )


def _field(value):
    value = grid(value)
    specs = instructions(value)
    field = [row[:] for row in value[6:]]
    h, w = len(field), len(field[0])
    cursor = [(r, c) for r in range(h) for c in range(w) if field[r][c] == 8]
    if not cursor:
        raise ValueError("field requires one solid color-8 square cursor")
    cr0, cr1, cc0, cc1 = _bbox(cursor)
    side = cr1 - cr0 + 1
    if side not in (2, 3) or cc1 - cc0 + 1 != side or len(cursor) != side * side:
        raise ValueError("cursor must be exactly one solid 2x2 or 3x3 square")
    if any(field[r][c] != 8 for r in range(cr0, cr1 + 1) for c in range(cc0, cc1 + 1)):
        raise ValueError("cursor bounding square must be solid")
    counts = Counter(cell for row in field for cell in row if cell != 8)
    if not counts:
        raise ValueError("field requires a background")
    ordered = counts.most_common()
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        raise ValueError("field background must be uniquely most frequent")
    background = ordered[0][0]
    if background in {spec["color"] for spec in specs}:
        raise ValueError("background cannot also be a header target color")
    return field, specs, background, (cr0, cc0, side)


def _target(field, color: int):
    points = [(r, c) for r, row in enumerate(field) for c, cell in enumerate(row) if cell == color]
    if not points:
        return None
    r0, r1, c0, c1 = _bbox(points)
    if len(points) != (r1 - r0 + 1) * (c1 - c0 + 1):
        raise ValueError("each present target color must form one solid rectangle")
    return {"bbox": (r0, r1, c0, c1), "cells": set(points)}


def _approach(target, cursor):
    if target is None:
        return None
    tr0, tr1, tc0, tc1 = target["bbox"]
    cr0, cc0, side = cursor
    cr1, cc1 = cr0 + side - 1, cc0 + side - 1
    candidates = []
    if tc1 < cc0 and max(tr0, cr0) <= min(tr1, cr1):
        candidates.append("left")
    if tc0 > cc1 and max(tr0, cr0) <= min(tr1, cr1):
        candidates.append("right")
    if tr1 < cr0 and max(tc0, cc0) <= min(tc1, cc1):
        candidates.append("up")
    if tr0 > cr1 and max(tc0, cc0) <= min(tc1, cc1):
        candidates.append("down")
    return candidates[0] if len(candidates) == 1 else None


def _block(top: tuple[int, int], side: int) -> set[tuple[int, int]]:
    r0, c0 = top
    return {(r, c) for r in range(r0, r0 + side) for c in range(c0, c0 + side)}


def _inside(top: tuple[int, int], side: int, h: int, w: int) -> bool:
    r, c = top
    return 0 <= r and 0 <= c and r + side <= h and c + side <= w


def _turn(vector: tuple[int, int], side: str) -> tuple[int, int]:
    dr, dc = vector
    if side == "left":
        return (-dc, dr)
    return (dc, -dr)


def _extend(field, background, start, side, vector):
    """Run straight until the brush reaches an edge or an original object."""
    h, w = len(field), len(field[0])
    cells = set(_block(start, side))
    top = start
    while True:
        nxt = (top[0] + vector[0], top[1] + vector[1])
        if not _inside(nxt, side, h, w):
            break
        block = _block(nxt, side)
        if any(field[r][c] not in (background, 8) for r, c in block):
            break
        top = nxt
        cells.update(block)
    return cells


def _bounce_vector(top, side, vector, obstacle):
    """Turn along the obstacle toward the side that protrudes farther."""
    r0, c0 = top
    r1, c1 = r0 + side - 1, c0 + side - 1
    or0, or1, oc0, oc1 = obstacle["bbox"]
    if vector[0] != 0:
        low = max(0, c0 - oc0)
        high = max(0, oc1 - c1)
        if low == high:
            raise ValueError("blocking rectangle has no unique farther horizontal extension")
        return DIRECTIONS["left"] if low > high else DIRECTIONS["right"]
    low = max(0, r0 - or0)
    high = max(0, or1 - r1)
    if low == high:
        raise ValueError("blocking rectangle has no unique farther vertical extension")
    return DIRECTIONS["up"] if low > high else DIRECTIONS["down"]


def _bounce_extend(field, background, start, side, vector):
    """Run to an edge, redirecting along each blocking rectangle's longer side."""
    h, w = len(field), len(field[0])
    cells = set(_block(start, side))
    top = start
    bounces = []
    seen = set()
    for _ in range(4 * h * w + 1):
        state = (top, vector)
        if state in seen:
            raise ValueError("turned route entered a bounce cycle")
        seen.add(state)
        nxt = (top[0] + vector[0], top[1] + vector[1])
        if not _inside(nxt, side, h, w):
            return cells, bounces
        block = _block(nxt, side)
        blockers = {
            field[r][c]
            for r, c in block
            if field[r][c] not in (background, 8)
        }
        if not blockers:
            top = nxt
            cells.update(block)
            continue
        if len(blockers) != 1:
            raise ValueError("turned route met multiple blocking rectangles at once")
        obstacle = _target(field, next(iter(blockers)))
        vector = _bounce_vector(top, side, vector, obstacle)
        bounces.append(VECTOR_NAMES[vector])
    raise ValueError("turned route exceeded bounded bounce search")


def _route(field, background, cursor, spec, mode):
    cr0, cc0, side = cursor
    start = (cr0, cc0)
    target = _target(field, spec["color"])
    approach = _approach(target, cursor)
    if approach is None:
        cells = _extend(field, background, start, side, DIRECTIONS["up"])
        return cells, {
            "target_color": spec["color"],
            "marker_side": spec["side"],
            "approach": None,
            "contact_top_left": None,
            "turn_direction": "up_fallback",
        }

    vector = DIRECTIONS[approach]
    target_cells = target["cells"]
    h, w = len(field), len(field[0])
    top = start
    cells = set(_block(top, side))
    for _ in range(h + w + 1):
        nxt = (top[0] + vector[0], top[1] + vector[1])
        if not _inside(nxt, side, h, w):
            raise ValueError("aligned target was not reachable")
        nxt_block = _block(nxt, side)
        if nxt_block & target_cells:
            break
        if any(field[r][c] not in (background, 8) for r, c in nxt_block):
            raise ValueError("another original object blocks the aligned target")
        top = nxt
        cells.update(nxt_block)
    else:
        raise ValueError("aligned target route exceeded bounded search")

    marker = spec["side"]
    if mode == "opposite":
        marker = "right" if marker == "left" else "left"
    turn_vector = _turn(vector, marker)
    turned_cells, bounces = _bounce_extend(
        field, background, top, side, turn_vector
    )
    cells.update(turned_cells)
    return cells, {
        "target_color": spec["color"],
        "marker_side": spec["side"],
        "approach": approach,
        "contact_top_left": [top[0], top[1]],
        "turn_direction": VECTOR_NAMES[turn_vector],
        "bounce_directions": bounces,
    }


def _analyze(value, mode):
    if mode not in MODES:
        raise ValueError("unknown turn rule")
    field, specs, background, cursor = _field(value)
    painted = set()
    metadata = []
    for spec in specs:
        cells, row = _route(field, background, cursor, spec, mode)
        painted.update(cells)
        metadata.append(row)
    return field, background, painted, metadata, cursor


def intermediate(value, mode: str = "header") -> dict:
    _field_grid, background, painted, metadata, cursor = _analyze(value, mode)
    return {
        "background": background,
        "cursor_top_left": [cursor[0], cursor[1]],
        "brush_size": cursor[2],
        "instructions": metadata,
        "painted_cell_count": len(painted),
    }


def solve(value, mode: str = "header") -> list[list[int]]:
    field, background, painted, _metadata, _cursor = _analyze(value, mode)
    out = [row[:] for row in field]
    for r, c in painted:
        if field[r][c] in (background, 8):
            out[r][c] = 8
    return out


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"public_eval_e87109e9:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _header(specs) -> list[list[int]]:
    rows = [[5] * 24 for _ in range(6)]
    for box, (color, side) in enumerate(specs):
        base = 6 * box
        for r in range(1, 5):
            rows[r][base + 1:base + 5] = [0, 0, 0, 0]
            rows[r][base + (1 if side == "left" else 4)] = color
    return rows


def _paint(field, color, r0, r1, c0, c1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            field[r][c] = color


def scene(seed: int, index: int, *, stress: bool = False) -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    if type(stress) is not bool:
        raise ValueError("stress must be boolean")
    profile = index % 10
    heights = (14, 15, 16, 17, 18, 19, 20, 21, 22, 24)
    height = 24 if stress else heights[profile]
    brush = 3 if profile % 3 == 0 else 2
    rng = _rng(seed, f"scene:{index}:{int(stress)}")
    palette = [1, 2, 3, 4, 6, 7, 9]
    rng.shuffle(palette)
    background = palette[0]
    colors = palette[1:5]
    directions = ["left", "right", "up", "down"]
    color_for = dict(zip(directions, colors))
    field = [[background] * 24 for _ in range(height)]
    cursor_r = max(6, min(height - brush - 6, height // 2 - brush // 2))
    cursor_c = 10 + ((profile + seed) % 3) - 1
    boxes = {
        "left": (3, height - 4, 0, 2),
        "right": (3, height - 4, 21, 23),
        "up": (0, 2, 3, 20),
        "down": (height - 3, height - 1, 3, 20),
    }
    # Four long edge bars form a closed racetrack under the bounce rule.  Keep
    # one aligned target short in the all-present profile so every route has an
    # escape to an edge while the other three bars still exercise bounces.
    short_boxes = {
        # Stay on the cursor axis, but leave both side corridors open for a
        # brush of the selected size.  This is the escape gap that prevents a
        # four-obstacle bounce cycle.
        "left": (cursor_r, cursor_r + brush - 2, 0, 2),
        "right": (cursor_r, cursor_r + brush - 2, 21, 23),
        "up": (0, 2, cursor_c, cursor_c + brush - 2),
        "down": (height - 3, height - 1, cursor_c, cursor_c + brush - 2),
    }
    special = directions[(profile + rng.randrange(4)) % 4]
    for direction in directions:
        if profile % 3 == 1 and direction == special:
            continue
        if profile % 3 == 2 and direction == special:
            # Retain the target but move it one cell diagonally off both cursor
            # axes, away from the standard edge-running bounce corridors.
            _paint(field, color_for[direction], cursor_r - 1, cursor_r - 1,
                   cursor_c - 1, cursor_c - 1)
            continue
        target_box = short_boxes[direction] if profile % 3 == 0 and direction == special else boxes[direction]
        _paint(field, color_for[direction], *target_box)
    _paint(field, 8, cursor_r, cursor_r + brush - 1, cursor_c, cursor_c + brush - 1)
    order = directions[:]
    rng.shuffle(order)
    # A symmetric union of four routes can hide every individual turn.  Search
    # the 16 header-side patterns in a deterministic rotated order and retain
    # the first valid one whose canonical and opposite interpretations differ.
    start_mask = rng.randrange(16)
    for offset in range(16):
        mask = (start_mask + offset) % 16
        specs = [
            (color_for[direction], "right" if mask & (1 << position) else "left")
            for position, direction in enumerate(order)
        ]
        value = _header(specs) + field
        try:
            canonical = solve(value, "header")
            opposite = solve(value, "opposite")
        except ValueError:
            continue
        if canonical != opposite:
            return value
    raise ValueError("could not construct an identifiable finite cursor-route scene")


def generate(seed: int, settings, demos: int = 2, queries: int = 4) -> dict:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    mode = setting(settings)

    def pair(index: int) -> dict:
        inp = scene(seed, index)
        return {"input": inp, "output": solve(inp, mode)}

    return {
        "train": [pair(i) for i in range(demos)],
        "test": [pair(i) for i in range(6, 6 + queries)],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def query_order(presentation_seed: int = 0) -> list[int]:
    integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    _rng(presentation_seed, "presentation").shuffle(order)
    return order


def public_turn(episode, turn: int, *, presentation_seed: int = 0) -> dict:
    integer(turn, 0, 3, "turn")
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or not 2 <= len(episode["train"]) <= 6
            or type(episode.get("test")) is not list or len(episode["test"]) != 4):
        raise ValueError("project from a complete episode with four private queries")
    index = query_order(presentation_seed)[turn]
    train = [
        {"input": copy.deepcopy(grid(pair["input"])),
         "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    return {
        "train": train,
        "test": [{"input": copy.deepcopy(grid(episode["test"][index]["input"]))}],
    }
