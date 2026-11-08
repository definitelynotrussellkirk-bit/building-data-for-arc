"""Native parametric family for divider-lattice matrix extraction.

The canonical setting preserves the selected source program byte-for-byte.
The alternative first derives the corner containing the uniquely largest
physical block, then flips the extracted matrix along the necessary axes so
that corner moves to the output's top-left.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "99601629ab88"
PARAMETER = "matrix_orientation"
CANONICAL = "mirror_left_right"
ALTERNATIVE = "largest_block_to_top_left"
SETTINGS = (CANONICAL, ALTERNATIVE)
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
HOME = Path(__file__).resolve().parent

# (matrix rows, matrix columns, input rows, input columns, largest corner)
DEMO_SPECS = (
    (2, 3, 10, 15, "top_left"),
    (3, 2, 16, 11, "bottom_right"),
    (3, 4, 20, 26, "bottom_left"),
    (4, 3, 25, 20, "top_right"),
    (4, 4, 29, 27, "top_left"),
    (2, 4, 14, 22, "bottom_right"),
)
QUERY_SPECS = (
    (3, 3, 17, 19, "top_right"),
    (4, 2, 25, 14, "bottom_left"),
    (2, 4, 15, 27, "bottom_right"),
    (4, 4, 30, 30, "top_left"),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}")
    return value


def program(settings: dict[str, Any]) -> str:
    orientation = _setting(settings)
    filename = "canonical.rkt" if orientation == CANONICAL else "largest_block_to_top_left.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def counterfactual_program(corner: str) -> str:
    """Return the alternative rule with Step A replaced by a forced corner."""
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    source = (HOME / "largest_block_to_top_left.rkt").read_text(encoding="utf-8")
    row_value = "#t" if corner.startswith("bottom") else "#f"
    col_value = "#t" if corner.endswith("right") else "#f"
    row_old = "(row-reverse? (= max-row-index (- nr 1)))"
    col_old = "(col-reverse? (= max-col-index (- nc 1)))"
    if source.count(row_old) != 1 or source.count(col_old) != 1:
        raise ValueError("alternative rule changed; review counterfactual materialization")
    return source.replace(row_old, f"(row-reverse? {row_value})").replace(
        col_old, f"(col-reverse? {col_value})"
    )


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be 1..30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors")
    return height, width


def _ranges(length: int, dividers: list[int]) -> list[tuple[int, int]]:
    bounds = [-1, *dividers, length]
    return [(bounds[i] + 1, bounds[i + 1]) for i in range(len(bounds) - 1)]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    candidates: list[tuple[int, list[int], list[int]]] = []
    for color in sorted({cell for row in grid for cell in row if cell != 0}):
        full_rows = [r for r, row in enumerate(grid) if all(cell == color for cell in row)]
        full_cols = [c for c in range(width) if all(grid[r][c] == color for r in range(height))]
        if full_rows and full_cols:
            candidates.append((color, full_rows, full_cols))
    if len(candidates) != 1:
        raise ValueError("exactly one nonzero divider color must form full rows and columns")
    divider, divider_rows, divider_cols = candidates[0]
    if divider_rows[0] == 0 or divider_rows[-1] == height - 1:
        raise ValueError("divider rows must be interior")
    if divider_cols[0] == 0 or divider_cols[-1] == width - 1:
        raise ValueError("divider columns must be interior")
    if any(b - a < 2 for a, b in zip(divider_rows, divider_rows[1:])):
        raise ValueError("divider rows must be nonadjacent")
    if any(b - a < 2 for a, b in zip(divider_cols, divider_cols[1:])):
        raise ValueError("divider columns must be nonadjacent")

    row_ranges = _ranges(height, divider_rows)
    col_ranges = _ranges(width, divider_cols)
    row_sizes = [end - start for start, end in row_ranges]
    col_sizes = [end - start for start, end in col_ranges]
    matrix: list[list[int]] = []
    for r0, r1 in row_ranges:
        row_values: list[int] = []
        for c0, c1 in col_ranges:
            value = grid[r0][c0]
            if value == divider:
                raise ValueError("block values must differ from the divider")
            if any(grid[r][c] != value for r in range(r0, r1) for c in range(c0, c1)):
                raise ValueError("every divider-bounded block must be uniform")
            row_values.append(0 if value == 0 else value)
        matrix.append(row_values)

    max_row = max(row_sizes)
    max_col = max(col_sizes)
    if row_sizes.count(max_row) != 1 or col_sizes.count(max_col) != 1:
        raise ValueError("largest row band and column band must each be unique")
    row_index = row_sizes.index(max_row)
    col_index = col_sizes.index(max_col)
    if row_index not in (0, len(row_sizes) - 1) or col_index not in (0, len(col_sizes) - 1):
        raise ValueError("the uniquely largest block must lie at a matrix corner")
    corner = (
        ("top" if row_index == 0 else "bottom")
        + "_"
        + ("left" if col_index == 0 else "right")
    )
    return {
        "divider_color": divider,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_ranges": row_ranges,
        "col_ranges": col_ranges,
        "row_sizes": row_sizes,
        "col_sizes": col_sizes,
        "matrix": matrix,
        "largest_corner": corner,
        "largest_block_area": max_row * max_col,
    }


def apply_corner(matrix: list[list[int]] | tuple[tuple[int, ...], ...], corner: str) -> tuple[tuple[int, ...], ...]:
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    rows = [list(row) for row in matrix]
    if corner.startswith("bottom"):
        rows.reverse()
    if corner.endswith("right"):
        rows = [list(reversed(row)) for row in rows]
    return tuple(tuple(row) for row in rows)


def transform(grid: list[list[int]], orientation: str) -> list[list[int]]:
    if orientation not in SETTINGS:
        raise ValueError(f"unknown orientation: {orientation!r}")
    analysis = analyze(grid)
    corner = "top_right" if orientation == CANONICAL else analysis["largest_corner"]
    return [list(row) for row in apply_corner(analysis["matrix"], corner)]


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "largest-corner-v1", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


@lru_cache(maxsize=None)
def _edge_partitions(total: int, count: int, edge: str) -> tuple[tuple[int, ...], ...]:
    content = total - (count - 1)
    if content < 2 * count:
        return ()
    index = 0 if edge in ("top", "left") else count - 1
    other_indices = [i for i in range(count) if i != index]
    candidates: list[tuple[int, ...]] = []
    upper = content - 2 * (count - 1)
    for others in product(range(2, upper + 1), repeat=count - 1):
        maximum = content - sum(others)
        if maximum < 2 or maximum <= max(others):
            continue
        values = [0] * count
        values[index] = maximum
        for i, value in zip(other_indices, others):
            values[i] = value
        candidates.append(tuple(values))
    return tuple(candidates)


def _choose_sizes(seed: int, index: int, total: int, count: int, edge: str, axis: str) -> list[int]:
    candidates = _edge_partitions(total, count, edge)
    if not candidates:
        raise ValueError(f"no legal {axis} partition for total={total}, count={count}, edge={edge}")
    rng = _rng(seed, index, "sizes", axis, total, count, edge)
    # Prefer visibly irregular partitions when available.
    varied = [candidate for candidate in candidates if len(set(candidate)) >= min(3, count)]
    pool = varied or list(candidates)
    return list(pool[rng.randrange(len(pool))])


def _episode_palette(seed: int) -> tuple[int, tuple[int, int, int, int]]:
    colors = list(range(1, 10))
    _rng(seed, "palette").shuffle(colors)
    return colors[0], tuple(colors[1:5])


def _matrix(seed: int, index: int, rows: int, cols: int, corner: str, *, dense: bool) -> list[list[int]]:
    divider, payload = _episode_palette(seed)
    del divider
    rng = _rng(seed, index, "matrix", rows, cols, corner, dense)
    choices = list(payload) if dense else [*payload, *payload, 0]
    matrix = [[choices[rng.randrange(len(choices))] for _ in range(cols)] for _ in range(rows)]
    positions = {
        "top_left": (0, 0),
        "top_right": (0, cols - 1),
        "bottom_left": (rows - 1, 0),
        "bottom_right": (rows - 1, cols - 1),
    }
    # The largest physical block uses one stable episode color; the remaining
    # corners use distinct colors so all four axis-flip outcomes stay visible.
    matrix[positions[corner][0]][positions[corner][1]] = payload[0]
    other_corners = [name for name in CORNERS if name != corner]
    for name, color in zip(other_corners, payload[1:]):
        r, c = positions[name]
        matrix[r][c] = color
    return matrix


def _lattice(matrix: list[list[int]], row_sizes: list[int], col_sizes: list[int], divider: int) -> list[list[int]]:
    height = sum(row_sizes) + len(row_sizes) - 1
    width = sum(col_sizes) + len(col_sizes) - 1
    grid = [[divider] * width for _ in range(height)]
    top = 0
    for i, row_height in enumerate(row_sizes):
        left = 0
        for j, col_width in enumerate(col_sizes):
            value = matrix[i][j]
            for r in range(top, top + row_height):
                grid[r][left : left + col_width] = [value] * col_width
            left += col_width + 1
        top += row_height + 1
    return grid


def sample_input(seed: int, index: int, spec: tuple[int, int, int, int, str], *, dense: bool = False) -> tuple[list[list[int]], dict[str, Any]]:
    rows, cols, height, width, corner = spec
    vertical, horizontal = corner.split("_")
    row_sizes = _choose_sizes(seed, index, height, rows, vertical, "row")
    col_sizes = _choose_sizes(seed, index, width, cols, horizontal, "column")
    divider, _ = _episode_palette(seed)
    matrix = _matrix(seed, index, rows, cols, corner, dense=dense)
    grid = _lattice(matrix, row_sizes, col_sizes, divider)
    analysis = analyze(grid)
    if analysis["largest_corner"] != corner:
        raise AssertionError("sampler failed to preserve requested largest corner")
    return grid, {
        "shape": [height, width],
        "matrix_shape": [rows, cols],
        "row_sizes": row_sizes,
        "col_sizes": col_sizes,
        "largest_corner": corner,
        "dense": dense,
    }


def _fixed_corner(grid: list[list[int]], corner: str) -> list[list[int]]:
    matrix = analyze(grid)["matrix"]
    return [list(row) for row in apply_corner(matrix, corner)]


def _row_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    corner = "bottom_left" if analysis["largest_corner"].startswith("bottom") else "top_left"
    return [list(row) for row in apply_corner(analysis["matrix"], corner)]


def _column_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    corner = "top_right" if analysis["largest_corner"].endswith("right") else "top_left"
    return [list(row) for row in apply_corner(analysis["matrix"], corner)]


def _opposite_corner(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    opposite = {
        "top_left": "bottom_right",
        "top_right": "bottom_left",
        "bottom_left": "top_right",
        "bottom_right": "top_left",
    }[analysis["largest_corner"]]
    return [list(row) for row in apply_corner(analysis["matrix"], opposite)]


def _smaller_edge_corner(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    row_edge = "top" if analysis["row_sizes"][0] < analysis["row_sizes"][-1] else "bottom"
    col_edge = "left" if analysis["col_sizes"][0] < analysis["col_sizes"][-1] else "right"
    corner = f"{row_edge}_{col_edge}"
    return [list(row) for row in apply_corner(analysis["matrix"], corner)]


def _divider_parity(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    corner = "top_left" if analysis["divider_color"] % 2 == 0 else "bottom_right"
    return [list(row) for row in apply_corner(analysis["matrix"], corner)]


def _anchor_color_parity(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    rows = len(analysis["matrix"])
    cols = len(analysis["matrix"][0])
    r = 0 if analysis["largest_corner"].startswith("top") else rows - 1
    c = 0 if analysis["largest_corner"].endswith("left") else cols - 1
    value = analysis["matrix"][r][c]
    corner = "top_left" if value % 2 == 0 else "bottom_right"
    return [list(row) for row in apply_corner(analysis["matrix"], corner)]


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_identity": lambda grid: _fixed_corner(grid, "top_left"),
    "fixed_horizontal": lambda grid: _fixed_corner(grid, "top_right"),
    "fixed_vertical": lambda grid: _fixed_corner(grid, "bottom_left"),
    "fixed_both": lambda grid: _fixed_corner(grid, "bottom_right"),
    "largest_row_only": _row_only,
    "largest_column_only": _column_only,
    "opposite_largest_corner": _opposite_corner,
    "smaller_edge_corner": _smaller_edge_corner,
    "divider_parity": _divider_parity,
    "largest_corner_color_parity": _anchor_color_parity,
}


def lesson_certificate(demos: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    if type(demos) is not list or not demos or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    for pair in demos:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("each demonstration needs input and output")
        analyze(pair["input"])
        _validate_grid(pair["output"])
    for grid in query_inputs:
        analyze(grid)

    surviving_values = [
        value
        for value in SETTINGS
        if all(transform(pair["input"], value) == pair["output"] for pair in demos)
    ]
    surviving_settings = [{PARAMETER: value} for value in surviving_values]
    intended_queries = (
        [transform(grid, surviving_values[0]) for grid in query_inputs]
        if len(surviving_values) == 1
        else []
    )
    surviving_rivals: list[str] = []
    ambiguous_rivals: list[dict[str, Any]] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            surviving_rivals.append(name)
            if intended_queries:
                disagreements = [
                    index
                    for index, (grid, intended) in enumerate(zip(query_inputs, intended_queries))
                    if rival(grid) != intended
                ]
                if disagreements:
                    ambiguous_rivals.append({"name": name, "query_indices": disagreements})
    return {
        "surviving_settings": surviving_settings,
        "surviving_rivals": surviving_rivals,
        "ambiguous_rivals": ambiguous_rivals,
        "query_count": len(query_inputs),
        "scope": "two declared settings and ten finite geometry/palette shortcuts; demonstrations fitted before query disagreement checks",
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    orientation = _setting(settings)
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    pairs: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    sampling: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    for split, count, specs, offset in (
        ("train", demos, DEMO_SPECS, 0),
        ("test", queries, QUERY_SPECS, 1000),
    ):
        for index in range(count):
            dense = split == "test" and index == 3
            grid, receipt = sample_input(seed, offset + index, specs[index], dense=dense)
            pairs[split].append({"input": grid, "output": transform(grid, orientation)})
            sampling[split].append(receipt)
    encoded = [json.dumps(pair["input"], separators=(",", ":")) for split in pairs.values() for pair in split]
    if len(encoded) != len(set(encoded)):
        raise ValueError("episode contains duplicate inputs")
    certificate = lesson_certificate(pairs["train"], [pair["input"] for pair in pairs["test"]])
    if certificate["surviving_settings"] != [copy.deepcopy(settings)]:
        raise ValueError("visible demonstrations do not uniquely teach the declared setting")
    if certificate["ambiguous_rivals"]:
        raise ValueError(f"finite shortcut ambiguity: {certificate['ambiguous_rivals']}")
    return {
        **pairs,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "certificate": certificate,
        "sampling": sampling,
        "status": "proposed",
        "training_admitted": False,
    }


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    index = _exact_int(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(
        public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})
    )
