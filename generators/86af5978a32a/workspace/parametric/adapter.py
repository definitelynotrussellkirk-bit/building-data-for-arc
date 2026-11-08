"""Native parametric family for the layout-times-shape-mask puzzle.

The default setting is the selected canonical program byte-for-byte.  The
alternative performs the same expansion, collapses the expanded mosaic to
binary occupancy, finds its unique largest four-connected component, and
recolors that post-expansion component to 9.  Different layout colors can join
only after the shape mask has been stamped, so the second step genuinely
consumes an input-dependent intermediate produced by the first.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from pathlib import Path
import random
from typing import Iterable


HOME = Path(__file__).resolve().parent
FINISHES = ("stamp_only", "highlight_largest_component")

# The finite profile bank is deliberately constructive.  Each template has a
# unique largest binary component after stamping, at least one smaller
# component, and mixed colors inside the selected component.
_TEMPLATES = {
    "h3": {
        "k": 3,
        "layout": (
            (0, 0, 0), (0, 1, 1),
            (2, 0, 2), (2, 2, 2),
        ),
        "shape": ((0, 0), (0, 1), (0, 2), (1, 1)),
    },
    "v4": {
        "k": 4,
        "layout": (
            (0, 0, 0), (1, 0, 1), (2, 0, 0),
            (2, 2, 2), (2, 3, 2), (3, 2, 1), (3, 3, 2),
            (0, 3, 1),
        ),
        "shape": ((0, 1), (1, 1), (2, 1), (3, 1), (1, 2)),
    },
    "h5": {
        "k": 5,
        "layout": (
            (0, 0, 0), (0, 1, 1), (0, 2, 0),
            (0, 4, 2), (1, 4, 2), (2, 4, 1), (3, 4, 2),
            (4, 0, 1),
        ),
        "shape": ((1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 2)),
    },
    "stress5": {
        "k": 5,
        "layout": (
            (0, 0, 0), (0, 1, 1), (0, 2, 2),
            (0, 4, 3), (1, 4, 3), (2, 4, 1), (3, 4, 3), (4, 4, 2),
            (2, 0, 1), (2, 1, 1),
            (4, 1, 2), (4, 2, 2),
        ),
        "shape": (
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
            (2, 2), (2, 3),
        ),
    },
}

_DEMO_PROFILES = (
    ("h3", "horizontal", "first", "layout_has_8", 0),
    ("v4", "vertical", "second", "shape_is_8", 1),
    ("h5", "horizontal", "second", "shape_is_8", 4),
    ("v4", "vertical", "first", "layout_has_8", 6),
    ("stress5", "horizontal", "first", "shape_is_8", 3),
    ("h3", "vertical", "second", "layout_has_8", 5),
)

_QUERY_PROFILES = (
    ("v4", "horizontal", "second", "layout_has_8", 2),
    ("h5", "vertical", "first", "shape_is_8", 7),
    ("h3", "vertical", "first", "shape_is_8", 3),
    ("stress5", "horizontal", "second", "layout_has_8", 0),
)


def _finish(settings) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly one finish")
    finish = settings["finish"]
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be one of the supported strings")
    return finish


def _integer(name: str, value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in [{lower}, {upper}]")
    return value


def program(settings) -> str:
    finish = _finish(settings)
    filename = (
        "canonical.rkt"
        if finish == "stamp_only"
        else "highlight_largest_component.rkt"
    )
    return (HOME / "rules" / filename).read_text(encoding="utf-8")


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or len(grid) > 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not grid[0] or len(grid[0]) > 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be a rectangular list of lists")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact ARC integers in 0..9")
    return len(grid), width


def _nonzero_colors(panel) -> set[int]:
    return {value for row in panel for value in row if value != 0}


def _split(grid):
    h, w = _validate_grid(grid)
    if w == 2 * h:
        k = h
        orientation = "horizontal"
        first = [list(row[:k]) for row in grid]
        second = [list(row[k:]) for row in grid]
    elif h == 2 * w:
        k = w
        orientation = "vertical"
        first = [list(row) for row in grid[:k]]
        second = [list(row) for row in grid[k:]]
    else:
        raise ValueError("input must be two equal square panels")
    if not 3 <= k <= 5:
        raise ValueError("half size must be in 3..5")
    first_colors = _nonzero_colors(first)
    second_colors = _nonzero_colors(second)
    if 2 <= len(first_colors) <= 4 and len(second_colors) == 1:
        layout_position, layout, shape = "first", first, second
        layout_colors, shape_colors = first_colors, second_colors
    elif 2 <= len(second_colors) <= 4 and len(first_colors) == 1:
        layout_position, layout, shape = "second", second, first
        layout_colors, shape_colors = second_colors, first_colors
    else:
        raise ValueError("one panel must have 2..4 colors and the other exactly one")
    if layout_colors & shape_colors:
        raise ValueError("layout and shape palettes must be disjoint")
    if int(8 in first_colors) + int(8 in second_colors) != 1:
        raise ValueError("color 8 must occur in exactly one panel")
    shape_positions = [
        (r, c)
        for r in range(k)
        for c in range(k)
        if shape[r][c] != 0
    ]
    layout_positions = [
        (r, c)
        for r in range(k)
        for c in range(k)
        if layout[r][c] != 0
    ]
    if len(shape_positions) < 3 or len(shape_positions) >= k * k:
        raise ValueError("shape must contain 3..k^2-1 cells")
    if len(layout_positions) < len(layout_colors) or len(layout_positions) >= k * k:
        raise ValueError("layout must use every color and retain background")
    return {
        "half_size": k,
        "orientation": orientation,
        "layout_position": layout_position,
        "layout": layout,
        "shape": shape,
        "layout_colors": layout_colors,
        "shape_color": next(iter(shape_colors)),
        "layout_positions": layout_positions,
        "shape_positions": shape_positions,
        "color_role": "shape_is_8" if 8 in shape_colors else "layout_has_8",
    }


def input_facts(grid) -> dict[str, object]:
    scene = _split(grid)
    return {
        "half_size": scene["half_size"],
        "orientation": scene["orientation"],
        "layout_position": scene["layout_position"],
        "color_role": scene["color_role"],
        "n_layout_colors": len(scene["layout_colors"]),
        "layout_cells": len(scene["layout_positions"]),
        "shape_cells": len(scene["shape_positions"]),
    }


def _stamp_scene(scene) -> list[list[int]]:
    k = scene["half_size"]
    output = [[0 for _ in range(k * k)] for _ in range(k * k)]
    for lr, lc in scene["layout_positions"]:
        color = scene["layout"][lr][lc]
        for sr, sc in scene["shape_positions"]:
            output[lr * k + sr][lc * k + sc] = color
    return output


def _components(grid, *, color_sensitive: bool) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < h and 0 <= cc < w) or (rr, cc) in seen:
                        continue
                    value = grid[rr][cc]
                    if value == 0 or (color_sensitive and value != color):
                        continue
                    seen.add((rr, cc))
                    queue.append((rr, cc))
            result.append(sorted(cells))
    return sorted(result, key=lambda cells: (-len(cells), cells[0]))


def component_intermediate(grid) -> dict[str, object]:
    stamped = _stamp_scene(_split(grid))
    binary = _components(stamped, color_sensitive=False)
    colored = _components(stamped, color_sensitive=True)
    if len(binary) < 2 or len(binary[0]) == len(binary[1]):
        raise ValueError("input must have a unique largest binary stamped component")
    return {
        "binary_component_sizes": [len(cells) for cells in binary],
        "color_component_sizes": [len(cells) for cells in colored],
        "selected_cells": binary[0],
    }


def _paint_cells(grid, cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = deepcopy(grid)
    for row, col in cells:
        out[row][col] = color
    return out


def solve(grid, finish):
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be a supported string")
    stamped = _stamp_scene(_split(grid))
    if finish == "stamp_only":
        return stamped
    return _paint_cells(stamped, component_intermediate(grid)["selected_cells"], 9)


def color_sensitive_solve(grid):
    """Plausible wrong intermediate: keep colors separate during components."""
    stamped = _stamp_scene(_split(grid))
    components = _components(stamped, color_sensitive=True)
    return _paint_cells(stamped, components[0], 9)


def most_frequent_color_solve(grid):
    """Plausible shortcut: highlight the most frequent layout color."""
    scene = _split(grid)
    stamped = _stamp_scene(scene)
    counts = Counter(scene["layout"][r][c] for r, c in scene["layout_positions"])
    color = min(counts, key=lambda value: (-counts[value], value))
    cells = [
        (r, c)
        for r, row in enumerate(stamped)
        for c, value in enumerate(row)
        if value == color
    ]
    return _paint_cells(stamped, cells, 9)


def _anchor_components(scene) -> list[list[tuple[int, int]]]:
    occupied = set(scene["layout_positions"])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for start in sorted(occupied):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in occupied and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: (-len(cells), cells[0]))


def layout_cluster_solve(grid):
    """Plausible shortcut: select the largest layout cluster before stamping."""
    scene = _split(grid)
    stamped = _stamp_scene(scene)
    anchors = _anchor_components(scene)[0]
    k = scene["half_size"]
    cells = [
        (lr * k + sr, lc * k + sc)
        for lr, lc in anchors
        for sr, sc in scene["shape_positions"]
    ]
    return _paint_cells(stamped, cells, 9)


def smallest_component_solve(grid):
    """Plausible rank error: highlight the smallest binary component."""
    stamped = _stamp_scene(_split(grid))
    components = _components(stamped, color_sensitive=False)
    smallest = sorted(components, key=lambda cells: (len(cells), cells[0]))[0]
    return _paint_cells(stamped, smallest, 9)


RIVALS = {
    "color_sensitive_components": color_sensitive_solve,
    "most_frequent_layout_color": most_frequent_color_solve,
    "largest_layout_cluster": layout_cluster_solve,
    "smallest_binary_component": smallest_component_solve,
}


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, code: int):
    out = [list(row) for row in grid]
    if code >= 4:
        out = [list(reversed(row)) for row in out]
        code -= 4
    for _ in range(code):
        out = _rotate_cw(out)
    return out


def _materialize_template(name: str, transform_code: int):
    spec = _TEMPLATES[name]
    k = spec["k"]
    layout = [[None for _ in range(k)] for _ in range(k)]
    for row, col, label in spec["layout"]:
        layout[row][col] = label
    shape = [[0 for _ in range(k)] for _ in range(k)]
    for row, col in spec["shape"]:
        shape[row][col] = 1
    # Encode empty layout as -1 while transforming so label 0 remains occupied.
    encoded = [[-1 if value is None else value for value in row] for row in layout]
    encoded = _transform(encoded, transform_code)
    shape = _transform(shape, transform_code)
    return encoded, shape


def _colorize(encoded_layout, binary_shape, color_role: str, rng: random.Random):
    labels = sorted({value for row in encoded_layout for value in row if value >= 0})
    pool = [1, 2, 3, 4, 5, 6, 7]
    rng.shuffle(pool)
    if color_role == "shape_is_8":
        mapping = {label: pool[index] for index, label in enumerate(labels)}
        shape_color = 8
    else:
        eight_label = labels[rng.randrange(len(labels))]
        remaining = iter(pool)
        mapping = {
            label: 8 if label == eight_label else next(remaining)
            for label in labels
        }
        used = set(mapping.values())
        shape_color = next(color for color in pool if color not in used)
    layout = [
        [0 if value < 0 else mapping[value] for value in row]
        for row in encoded_layout
    ]
    shape = [
        [shape_color if value else 0 for value in row]
        for row in binary_shape
    ]
    return layout, shape


def _compose(first, second, orientation: str):
    if orientation == "horizontal":
        return [list(left) + list(right) for left, right in zip(first, second)]
    return [list(row) for row in first] + [list(row) for row in second]


def _make_input(seed: int, stream: str, index: int, profile):
    name, orientation, layout_position, color_role, base_transform = profile
    rng = random.Random(f"86af5978a32a:parametric-v1:{seed}:{stream}:{index}")
    transform_code = (base_transform + rng.randrange(8)) % 8
    encoded_layout, binary_shape = _materialize_template(name, transform_code)
    layout, shape = _colorize(encoded_layout, binary_shape, color_role, rng)
    first, second = (layout, shape) if layout_position == "first" else (shape, layout)
    grid = _compose(first, second, orientation)

    facts = input_facts(grid)
    expected = {
        "half_size": len(layout),
        "orientation": orientation,
        "layout_position": layout_position,
        "color_role": color_role,
    }
    for key, value in expected.items():
        if facts[key] != value:
            raise RuntimeError(f"profile lost {key}: expected {value!r}, got {facts[key]!r}")
    intermediate = component_intermediate(grid)
    if len(intermediate["selected_cells"]) < 2 * facts["shape_cells"]:
        raise RuntimeError("largest component is not a substantive multi-stamp result")
    intended = solve(grid, "highlight_largest_component")
    for name, rival in RIVALS.items():
        if rival(grid) == intended and name in {
            "color_sensitive_components",
            "most_frequent_layout_color",
            "smallest_binary_component",
        }:
            raise RuntimeError(f"profile failed to refute required rival {name}")
    return grid


def generate(seed, settings, demos, queries):
    finish = _finish(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)

    demo_inputs = [
        _make_input(seed, "demo", index, profile)
        for index, profile in enumerate(_DEMO_PROFILES)
    ]
    query_inputs = [
        _make_input(seed, "query", index, profile)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    visible = demo_inputs + query_inputs
    keys = [tuple(tuple(row) for row in grid) for grid in visible]
    if len(keys) != len(set(keys)):
        raise RuntimeError("profile construction produced duplicate visible inputs")

    def pair(grid):
        return {"input": deepcopy(grid), "output": solve(grid, finish)}

    return {
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
        "program_solution": program(settings),
    }
