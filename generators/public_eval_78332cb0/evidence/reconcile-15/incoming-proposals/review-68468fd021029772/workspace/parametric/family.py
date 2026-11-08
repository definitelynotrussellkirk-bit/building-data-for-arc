"""Boundary-port chain family for public task 78332cb0."""
from __future__ import annotations

import copy
import hashlib
import random
from collections import Counter
from functools import lru_cache

TASK_ID = "public_eval_78332cb0"
VERSION = "1.0.0"
SETTINGS = ("forward", "reverse")
DEPENDENCY = {
    "step_a": "Split on the repeated non-background divider color and infer the unique all-panels boundary-port path.",
    "intermediate": "An input-dependent ordered list of unchanged panels together with vertical or horizontal chain orientation.",
    "step_b": "Consume that ordered list to stack the panels with divider-colored separators, optionally reversing the declared episode direction.",
    "why_b_depends_on_a": "The output position of every panel is determined by the recovered port-matching path; input layout and color order do not provide the sequence.",
}


def _validate_grid(grid):
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("Expected a rectangular 1..30 exact-integer ARC grid")
    return grid


def _background(grid):
    counts = Counter(value for row in grid for value in row)
    return min(counts, key=lambda value: (-counts[value], value))


def _internal_lines(grid, background):
    h, w = len(grid), len(grid[0])
    lines = []
    for r in range(1, h - 1):
        if len(set(grid[r])) == 1 and grid[r][0] != background:
            lines.append(("row", r, grid[r][0]))
    for c in range(1, w - 1):
        values = {grid[r][c] for r in range(h)}
        if len(values) == 1:
            value = next(iter(values))
            if value != background:
                lines.append(("col", c, value))
    return lines


def _bands(size, cuts):
    answer, start = [], 0
    for cut in sorted(cuts):
        if start < cut:
            answer.append((start, cut - 1))
        start = cut + 1
    if start < size:
        answer.append((start, size - 1))
    return answer


def _edge(panel, side, background):
    h, w = len(panel), len(panel[0])
    if side == "top":
        return tuple(c for c in range(w) if panel[0][c] != background)
    if side == "bottom":
        return tuple(c for c in range(w) if panel[h - 1][c] != background)
    if side == "left":
        return tuple(r for r in range(h) if panel[r][0] != background)
    if side == "right":
        return tuple(r for r in range(h) if panel[r][w - 1] != background)
    raise ValueError("Unknown edge")


def analyze(grid):
    grid = _validate_grid(grid)
    background = _background(grid)
    lines = _internal_lines(grid, background)
    if not lines:
        raise ValueError("Expected at least one internal non-background divider")
    counts = Counter(color for _, _, color in lines)
    best = max(counts.values())
    candidates = sorted(color for color, count in counts.items() if count == best)
    if len(candidates) != 1:
        raise ValueError("Divider color is ambiguous")
    separator = candidates[0]
    row_cuts = [index for axis, index, color in lines if axis == "row" and color == separator]
    col_cuts = [index for axis, index, color in lines if axis == "col" and color == separator]
    row_bands = _bands(len(grid), row_cuts)
    col_bands = _bands(len(grid[0]), col_cuts)
    panels = [
        [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
        for r0, r1 in row_bands
        for c0, c1 in col_bands
    ]
    if len(panels) < 2:
        raise ValueError("Expected at least two panels")
    shape = (len(panels[0]), len(panels[0][0]))
    if any((len(panel), len(panel[0])) != shape for panel in panels):
        raise ValueError("All panels must share one shape")
    vertical_score = sum(len(_edge(panel, side, background)) for panel in panels for side in ("top", "bottom"))
    horizontal_score = sum(len(_edge(panel, side, background)) for panel in panels for side in ("left", "right"))
    if not ((vertical_score > 0 and horizontal_score == 0) or (horizontal_score > 0 and vertical_score == 0)):
        raise ValueError("Panels must expose ports on exactly one opposite-edge axis")
    vertical = vertical_score > 0
    incoming_side, outgoing_side = (("top", "bottom") if vertical else ("left", "right"))
    records = [
        {
            "index": index,
            "panel": panel,
            "incoming": _edge(panel, incoming_side, background),
            "outgoing": _edge(panel, outgoing_side, background),
        }
        for index, panel in enumerate(panels)
    ]
    starts = [record for record in records if not record["incoming"]]
    sinks = [record for record in records if not record["outgoing"]]
    if len(starts) != 1 or len(sinks) != 1:
        raise ValueError("Expected exactly one open source and one open sink")
    solutions = []

    def walk(path, remaining):
        if len(solutions) > 1:
            return
        outgoing = path[-1]["outgoing"]
        if not remaining:
            if not outgoing:
                solutions.append(path[:])
            return
        for candidate in remaining:
            if candidate["incoming"] == outgoing:
                walk(path + [candidate], [item for item in remaining if item is not candidate])

    start = starts[0]
    walk([start], [record for record in records if record is not start])
    if len(solutions) != 1:
        raise ValueError("Boundary-port chain is absent or ambiguous")
    order = [record["index"] for record in solutions[0]]
    return {
        "background": background,
        "separator": separator,
        "orientation": "vertical" if vertical else "horizontal",
        "panels": panels,
        "order": order,
        "ports": [{"incoming": record["incoming"], "outgoing": record["outgoing"]} for record in records],
    }


def solve(grid, chain_order="forward"):
    if chain_order not in SETTINGS:
        raise ValueError("Unknown chain order")
    info = analyze(grid)
    order = info["order"] if chain_order == "forward" else list(reversed(info["order"]))
    panels = [copy.deepcopy(info["panels"][index]) for index in order]
    separator = info["separator"]
    if info["orientation"] == "vertical":
        width = len(panels[0][0])
        output = []
        for index, panel in enumerate(panels):
            if index:
                output.append([separator] * width)
            output.extend(panel)
        return output
    height = len(panels[0])
    output = [[] for _ in range(height)]
    for index, panel in enumerate(panels):
        for r in range(height):
            if index:
                output[r].append(separator)
            output[r].extend(panel[r])
    return output


def _rng(seed, index):
    raw = hashlib.sha256(f"78332cb0-v1:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _signatures(tile):
    interior = list(range(1, tile - 1))
    values = []
    for mask in range(1, 1 << len(interior)):
        values.append(tuple(interior[i] for i in range(len(interior)) if mask & (1 << i)))
    return values


def _panel(tile, background, color, orientation, incoming, outgoing, rng):
    grid = [[background] * tile for _ in range(tile)]
    middle = tile // 2
    if orientation == "vertical":
        top = incoming or (rng.choice(range(1, tile - 1)),)
        bottom = outgoing or (rng.choice(range(1, tile - 1)),)
        for c in top:
            for r in range(0 if incoming else 1, middle + 1):
                grid[r][c] = color
        for c in bottom:
            for r in range(middle, tile if outgoing else tile - 1):
                grid[r][c] = color
        for c in range(min(top + bottom), max(top + bottom) + 1):
            grid[middle][c] = color
    else:
        left = incoming or (rng.choice(range(1, tile - 1)),)
        right = outgoing or (rng.choice(range(1, tile - 1)),)
        for r in left:
            for c in range(0 if incoming else 1, middle + 1):
                grid[r][c] = color
        for r in right:
            for c in range(middle, tile if outgoing else tile - 1):
                grid[r][c] = color
        for r in range(min(left + right), max(left + right) + 1):
            grid[r][middle] = color
    return grid


def _compose(panels, rows, cols, separator):
    tile_h, tile_w = len(panels[0]), len(panels[0][0])
    height = rows * tile_h + rows - 1
    width = cols * tile_w + cols - 1
    grid = [[separator] * width for _ in range(height)]
    for slot, panel in enumerate(panels):
        rr, cc = divmod(slot, cols)
        r0, c0 = rr * (tile_h + 1), cc * (tile_w + 1)
        for r, row in enumerate(panel):
            grid[r0 + r][c0 : c0 + tile_w] = row[:]
    return grid


@lru_cache(maxsize=4096)
def _sample_frozen(seed, index):
    if type(seed) is not int or seed < 0 or type(index) is not int or index < 0:
        raise ValueError("seed and index must be nonnegative exact integers")
    rng = _rng(seed, index)
    stress = index % 10 == 9
    if stress:
        n, tile = 5, 5
    else:
        n = 3 + index % 3
        tile = {3: 7, 4: 6, 5: 5}[n]
    orientation = "vertical" if index % 2 == 0 else "horizontal"
    palette = list(range(10))
    rng.shuffle(palette)
    background = palette.pop()
    separator = next(color for color in palette if color != background and color != 0)
    palette.remove(separator)
    colors = [palette[i % len(palette)] for i in range(n)]
    signatures = _signatures(tile)
    rng.shuffle(signatures)
    # One compact lesson mirrors the public trap: the middle panel has the
    # same singleton port on both sides, so its object forms a complete line.
    # With exactly three panels this still has one global chain; repeating a
    # link across four or five panels would make the internal order ambiguous.
    repeated_singleton = n == 3 and index % 10 == 0
    if repeated_singleton:
        links = [(tile // 2,)] * (n - 1)
    else:
        links = signatures[: n - 1]
    chain = [
        _panel(
            tile,
            background,
            colors[i],
            orientation,
            links[i - 1] if i else (),
            links[i] if i < n - 1 else (),
            rng,
        )
        for i in range(n)
    ]
    if n == 4:
        rows, cols = 2, 2
    elif n == 5:
        rows, cols = ((1, 5) if orientation == "vertical" else (5, 1))
    elif repeated_singleton:
        # Align this one three-panel scene with the port axis. It creates one
        # object-colored complete line, while the separator still appears
        # twice and remains the unique repeated divider color.
        rows, cols = ((1, 3) if orientation == "vertical" else (3, 1))
    else:
        # Lay panels along the chain axis. Distinct object colors then prevent
        # an individual object's complete line from spanning the whole scene.
        rows, cols = ((3, 1) if orientation == "vertical" else (1, 3))
    permutation = list(range(n))
    rng.shuffle(permutation)
    if permutation in (list(range(n)), list(reversed(range(n)))):
        permutation = permutation[1:] + permutation[:1]
    scrambled = [chain[i] for i in permutation]
    grid = _compose(scrambled, rows, cols, separator)
    info = analyze(grid)
    expected_input_order = [permutation.index(i) for i in range(n)]
    if info["order"] != expected_input_order:
        raise RuntimeError("Constructed chain order was not recovered")
    if max(len(grid), len(grid[0]), len(solve(grid))) > 30 or len(solve(grid)[0]) > 30:
        raise RuntimeError("Constructed scene exceeds ARC bounds")
    return tuple(tuple(row) for row in grid)


def sample(seed, split, index):
    if split not in ("train", "test"):
        raise ValueError("Unknown split")
    source_index = index if split == "train" else 6 + index
    return [list(row) for row in _sample_frozen(seed, source_index)]


def public_views(episode, *, presentation_seed, limit=4):
    if type(presentation_seed) is not int or type(limit) is not int or not 1 <= limit <= 4:
        raise ValueError("Invalid presentation request")
    if type(episode) is not dict or type(episode.get("test")) is not list or len(episode["test"]) != 4:
        raise ValueError("Shuffle the complete four-query bank before selecting a prefix")
    order = list(range(4))
    random.Random(presentation_seed).shuffle(order)
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    return [
        {"train": copy.deepcopy(train), "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}]}
        for index in order[:limit]
    ]
