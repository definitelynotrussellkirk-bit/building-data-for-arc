"""Header-programmed square-cursor routes for public ARC task e87109e9."""
from __future__ import annotations

from collections import Counter, deque
import copy
import hashlib
from pathlib import Path
import random
from typing import NamedTuple

TASK_ID = "public_eval_e87109e9"
PARAMETERS = {"finish": ["trace_only", "highlight_shortest_route"]}
DEFAULT = {"finish": "trace_only"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))


class Obstacle(NamedTuple):
    color: int
    cells: frozenset[tuple[int, int]]
    bbox: tuple[int, int, int, int]


class Route(NamedTuple):
    color: int
    hand: str
    cells: set[tuple[int, int]]
    hits: list[Obstacle]
    fallback: bool


def _integer(value: object, lo: int, hi: int, label: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{label} must be an exact integer in {lo}..{hi}")
    return value


def _grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 7 <= len(value) <= 30 or type(value[0]) is not list
            or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0]) for row in value)
            or any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row)):
        raise ValueError("need a rectangular exact-integer ARC grid, height 7..30 and width 1..30")
    return [row[:] for row in value]


def _components(grid: list[list[int]], excluded: set[int]) -> list[Obstacle]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in excluded}
    result: list[Obstacle] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        todo = [start]
        unseen.remove(start)
        cells: set[tuple[int, int]] = set()
        while todo:
            r, c = todo.pop()
            cells.add((r, c))
            for dr, dc in DIRECTIONS:
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    todo.append(nxt)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        bbox = (min(rs), min(cs), max(rs), max(cs))
        if len(cells) != (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1):
            raise ValueError("every routing obstacle must be a solid monochrome rectangle")
        result.append(Obstacle(color, frozenset(cells), bbox))
    return result


def parse(grid: list[list[int]]) -> dict:
    grid = _grid(grid)
    h, w = len(grid), len(grid[0])
    if h < 13 or w % 6 or w < 18:
        raise ValueError("need a six-row header of 6-column instruction boxes")
    header = grid[:6]
    if any(value != 5 for value in header[0] + header[5]):
        raise ValueError("header top and bottom borders must be color 5")
    instructions: list[tuple[int, str]] = []
    for start in range(0, w, 6):
        box = [row[start:start + 6] for row in header]
        if any(len(row) != 6 for row in box):
            raise ValueError("incomplete instruction box")
        if any(box[r][c] != 5 for r in range(6) for c in (0, 5)):
            raise ValueError("instruction boxes need color-5 side borders")
        colored = [(r, c, box[r][c]) for r in range(1, 5) for c in range(1, 5)
                   if box[r][c] != 0]
        colors = {v for _, _, v in colored}
        cols = {c for _, c, _ in colored}
        if len(colors) != 1 or len(colored) != 4 or len(cols) != 1:
            raise ValueError("each instruction needs one four-cell vertical color bar")
        col = next(iter(cols))
        if col not in (1, 4):
            raise ValueError("instruction bar must be at the left or right interior edge")
        instructions.append((next(iter(colors)), "left" if col == 1 else "right"))
    body = [row[:] for row in grid[6:]]
    frequencies = Counter(cell for row in body for cell in row)
    background, background_count = frequencies.most_common(1)[0]
    if len(frequencies) > 1 and background_count == frequencies.most_common(2)[1][1]:
        raise ValueError("body background must be the unique modal color")
    source_cells = {(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value == 8}
    if not source_cells:
        raise ValueError("body needs a color-8 square cursor")
    rs = [r for r, _ in source_cells]
    cs = [c for _, c in source_cells]
    source_bbox = (min(rs), min(cs), max(rs), max(cs))
    size = source_bbox[2] - source_bbox[0] + 1
    if (size < 1 or source_bbox[3] - source_bbox[1] + 1 != size
            or source_cells != {(r, c) for r in range(source_bbox[0], source_bbox[2] + 1)
                               for c in range(source_bbox[1], source_bbox[3] + 1)}):
        raise ValueError("color 8 must form one solid square cursor")
    obstacles = _components(body, {background, 8})
    instruction_colors = {color for color, _ in instructions}
    if any(obstacle.color not in instruction_colors for obstacle in obstacles):
        raise ValueError("every body obstacle color must occur in the header")
    return {
        "grid": grid,
        "header": header,
        "body": body,
        "background": background,
        "instructions": instructions,
        "source_bbox": source_bbox,
        "source_size": size,
        "source_cells": source_cells,
        "obstacles": obstacles,
    }


def _footprint(pos: tuple[int, int], size: int) -> set[tuple[int, int]]:
    r, c = pos
    return {(rr, cc) for rr in range(r, r + size) for cc in range(c, c + size)}


def _inside(pos: tuple[int, int], size: int, h: int, w: int) -> bool:
    r, c = pos
    return 0 <= r and 0 <= c and r + size <= h and c + size <= w


def _collision(pos: tuple[int, int], size: int, obstacles: list[Obstacle]) -> Obstacle | None:
    cells = _footprint(pos, size)
    hits = [obstacle for obstacle in obstacles if cells & obstacle.cells]
    if len(hits) > 1:
        raise ValueError("cursor footprint collides with multiple obstacles at once")
    return hits[0] if hits else None


def _seek(pos: tuple[int, int], direction: tuple[int, int], size: int, h: int, w: int,
          obstacles: list[Obstacle]) -> tuple[set[tuple[int, int]], tuple[int, int], Obstacle | None]:
    cells = set(_footprint(pos, size))
    current = pos
    while True:
        nxt = (current[0] + direction[0], current[1] + direction[1])
        if not _inside(nxt, size, h, w):
            return cells, current, None
        hit = _collision(nxt, size, obstacles)
        if hit is not None:
            return cells, current, hit
        current = nxt
        cells.update(_footprint(current, size))


def _turn(direction: tuple[int, int], hand: str) -> tuple[int, int]:
    dr, dc = direction
    if hand == "left":
        return (-dc, dr)
    if hand == "right":
        return (dc, -dr)
    raise ValueError("hand must be left or right")


def _bounce(direction: tuple[int, int], pos: tuple[int, int], size: int,
            obstacle: Obstacle) -> tuple[int, int]:
    r, c = pos
    r1, c1, r2, c2 = obstacle.bbox
    dr, dc = direction
    if dr:
        toward_min = c - c1
        toward_max = c2 - (c + size - 1)
        return (0, -1) if toward_min > toward_max else (0, 1)
    toward_min = r - r1
    toward_max = r2 - (r + size - 1)
    return (-1, 0) if toward_min > toward_max else (1, 0)


def _post_turn(pos: tuple[int, int], direction: tuple[int, int], size: int, h: int, w: int,
               obstacles: list[Obstacle]) -> tuple[set[tuple[int, int]], list[Obstacle]]:
    cells = set(_footprint(pos, size))
    hits: list[Obstacle] = []
    current = pos
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for _ in range(8 * h * w):
        state = (current, direction)
        if state in seen:
            return cells, hits
        seen.add(state)
        nxt = (current[0] + direction[0], current[1] + direction[1])
        if not _inside(nxt, size, h, w):
            return cells, hits
        hit = _collision(nxt, size, obstacles)
        if hit is not None:
            hits.append(hit)
            direction = _bounce(direction, current, size, hit)
            continue
        current = nxt
        cells.update(_footprint(current, size))
    raise ValueError("route exceeded bounded cursor-state budget")


def trace(grid: list[list[int]]) -> dict:
    state = parse(grid)
    body = state["body"]
    h, w = len(body), len(body[0])
    source_pos = (state["source_bbox"][0], state["source_bbox"][1])
    size = state["source_size"]
    obstacles = state["obstacles"]
    routes: list[Route] = []
    all_cells = set(state["source_cells"])
    for color, hand in state["instructions"]:
        candidates = []
        for direction in DIRECTIONS:
            cells, pos, hit = _seek(source_pos, direction, size, h, w, obstacles)
            if hit is not None and hit.color == color:
                candidates.append((direction, cells, pos, hit))
        if len(candidates) > 1:
            raise ValueError("instruction target is aligned in more than one direction")
        if not candidates:
            cells, _, _ = _seek(source_pos, (-1, 0), size, h, w, obstacles)
            route = Route(color, hand, cells, [], True)
        else:
            direction, cells, pos, target = candidates[0]
            tail_cells, tail_hits = _post_turn(pos, _turn(direction, hand), size, h, w, obstacles)
            route = Route(color, hand, cells | tail_cells, [target] + tail_hits, False)
        routes.append(route)
        all_cells.update(route.cells)
    return {**state, "routes": routes, "trail_cells": all_cells}


def solve(grid: list[list[int]], finish: str = "trace_only") -> list[list[int]]:
    if finish not in PARAMETERS["finish"]:
        raise ValueError("finish must be trace_only or highlight_shortest_route")
    state = trace(grid)
    out = [row[:] for row in state["body"]]
    background = state["background"]
    for r, c in state["trail_cells"]:
        if out[r][c] == background or out[r][c] == 8:
            out[r][c] = 8
    if finish == "highlight_shortest_route":
        candidates = [route for route in state["routes"] if route.hits]
        if not candidates:
            raise ValueError("alternate grammar needs at least one target-contacting route")
        selected_route = min(candidates, key=lambda route: (len(route.cells), len(route.hits), route.color))
        selected = selected_route.hits[0]
        for r, c in selected.cells:
            out[r][c] = 9
    return out


def solve_wrong_first_route(grid: list[list[int]]) -> list[list[int]]:
    state = trace(grid)
    out = solve(grid, "trace_only")
    route = next((route for route in state["routes"] if route.hits), None)
    if route is not None:
        for r, c in route.hits[0].cells:
            out[r][c] = 9
    return out


def _header(instructions: list[tuple[int, str]]) -> list[list[int]]:
    rows = [[] for _ in range(6)]
    for color, hand in instructions:
        box = [[5] * 6] + [[5, 0, 0, 0, 0, 5] for _ in range(4)] + [[5] * 6]
        col = 1 if hand == "left" else 4
        for r in range(1, 5):
            box[r][col] = color
        for r in range(6):
            rows[r].extend(box[r])
    return rows


def _paint_rect(grid: list[list[int]], bbox: tuple[int, int, int, int], color: int) -> None:
    r1, c1, r2, c2 = bbox
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if grid[r][c] != grid[0][0]:
                raise ValueError("overlapping constructed rectangles")
            grid[r][c] = color


def _rotate(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _make_scene(seed: int, index: int) -> list[list[int]]:
    rng = random.Random((seed + 1) * 1000003 + index * 9176)
    profiles = [
        (18, 24, 2), (20, 24, 2), (21, 24, 3), (22, 24, 2), (24, 30, 3),
        (19, 24, 2), (23, 24, 2), (24, 24, 3), (20, 24, 2), (24, 30, 3),
    ]
    h, w, size = profiles[index]
    background_choices = [0, 3, 7]
    background = background_choices[(seed + index) % len(background_choices)]
    colors = [color for color in (1, 2, 4, 6) if color != background]
    rng.shuffle(colors)
    west, east, north, south = colors
    body = [[background] * w for _ in range(h)]
    sr = max(7, min(h - size - 7, h // 2 - size // 2 + rng.choice((-1, 0, 1))))
    sc = max(8, min(w - size - 8, w // 2 - size // 2 + rng.choice((-1, 0, 1))))
    for r in range(sr, sr + size):
        for c in range(sc, sc + size):
            body[r][c] = 8
    obj_w = 3 if size == 2 else 4
    west_box = (sr - 2, 2, sr + size + 2, 2 + obj_w - 1)
    east_box = (sr - 2, w - obj_w - 2, sr + size + 2, w - 3)
    west_beam_c = west_box[3] + 1
    north_width = max(size + 4, 7)
    north_c1 = sc - 1
    north_c2 = min(w - 4, north_c1 + north_width - 1)
    north_box = (2, north_c1, 2 + obj_w - 1, north_c2)
    south_r2 = h - 3
    south_r1 = south_r2 - obj_w + 1
    south_c1 = west_beam_c
    south_c2 = min(sc + size + 3, east_box[1] - size - 2)
    if south_c2 - south_c1 + 1 < size + 5:
        south_c2 = south_c1 + size + 5
    south_box = (south_r1, south_c1, south_r2, south_c2)
    for bbox, color in ((west_box, west), (east_box, east), (north_box, north), (south_box, south)):
        _paint_rect(body, bbox, color)
    hands = {west: "left", east: "left", north: "left", south: "left"}
    # On selected profiles, remove the north target while retaining its instruction;
    # this exercises the official straight-to-header fallback.
    if index in (1, 6):
        for r in range(north_box[0], north_box[2] + 1):
            for c in range(north_box[1], north_box[3] + 1):
                body[r][c] = background
    instructions = [(west, hands[west]), (east, hands[east]),
                    (north, hands[north]), (south, hands[south])]
    if w == 30:
        # A fifth absent instruction preserves the official fallback behavior
        # while making a substantive exact 30x30 input lawful.
        extra = next(color for color in (7, 3, 2, 1, 4, 6) if color not in {background, west, east, north, south})
        instructions.append((extra, "right" if (seed + index) % 2 else "left"))
    rng.shuffle(instructions)
    # Square 24x24 bodies receive rotational diversity.  Header width and body
    # width must remain equal, so rectangular scenes stay in their native frame.
    turns = 0
    for _ in range(turns):
        body = _rotate(body)
    grid = _header(instructions) + body
    state = trace(grid)
    candidates = [route for route in state["routes"] if route.hits]
    if not candidates:
        raise AssertionError((index, "no target-contacting route"))
    selected_route = min(candidates, key=lambda route: (len(route.cells), len(route.hits), route.color))
    selected_object_color = selected_route.hits[0].color
    # Keep a source-order proxy from fitting the two-demo teaching prefix: put
    # a target whose color differs from the selected target first and the
    # selected route's instruction last.  Route geometry is unchanged.
    first = next(item for item in instructions
                 if item[0] != selected_route.color and item[0] != selected_object_color
                 and any(obstacle.color == item[0] for obstacle in state["obstacles"]))
    middle = [item for item in instructions if item != first and item[0] != selected_route.color]
    selected_item = next(item for item in instructions if item[0] == selected_route.color)
    instructions = [first] + middle + [selected_item]
    grid = _header(instructions) + body
    return grid


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    grids = [_make_scene(seed, index) for index in range(10)]
    # Keep teaching profiles in the first six but independently permute the four
    # query profiles so source ordinal does not determine presentation order.
    query_rng = random.Random(seed ^ 0xE87109E9)
    queries = grids[6:]
    query_rng.shuffle(queries)
    return grids[:6], queries


def _finish(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {"finish"}
            or settings["finish"] not in PARAMETERS["finish"]):
        raise ValueError("settings must be exactly finish=trace_only or highlight_shortest_route")
    return settings["finish"]


def canonical_source() -> str:
    return Path(__file__).with_name("canonical.rkt").read_text()


def program(settings: dict) -> str:
    finish = _finish(settings)
    source = canonical_source()
    if finish == "trace_only":
        return source
    marker = "(define highlight-shortest #f)"
    if source.count(marker) != 1:
        raise RuntimeError("canonical highlight marker drift")
    return source.replace(marker, "(define highlight-shortest #t)", 1)


def wrong_program() -> str:
    source = program({"finish": "highlight_shortest_route"})
    marker = "(define wrong-first #f)"
    if source.count(marker) != 1:
        raise RuntimeError("canonical wrong-selector marker drift")
    return source.replace(marker, "(define wrong-first #t)", 1)


def generate(seed: int = 0, settings: dict | None = None, demos: int = 3,
             queries: int = 4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"finish": PARAMETERS["finish"][seed % 2]}
    finish = _finish(settings)
    demo_inputs, query_inputs = input_bank(seed)
    return {
        "train": [{"input": copy.deepcopy(grid), "output": solve(grid, finish)}
                  for grid in demo_inputs[:demos]],
        "test": [{"input": copy.deepcopy(grid), "output": solve(grid, finish)}
                 for grid in query_inputs[:queries]],
        "program_solution": program(settings),
    }
