"""Native matched-input parametric family for normalized mask subtraction.

The canonical setting preserves the selected top-left normalization program
byte-for-byte.  The alternative derives the corner of the smaller object
relative to the larger object and uses that corner to align both normalized
masks before exact-mask subtraction.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "9de65c6eed00"
PARAMETER = "normalization_anchor"
CANONICAL = "top_left"
ALTERNATIVE = "relative_corner"
SETTINGS = (CANONICAL, ALTERNATIVE)
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
HOME = Path(__file__).resolve().parent
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
PALETTES = ((2, 3), (5, 7), (3, 5), (8, 4), (6, 1), (9, 2))

PROFILES: dict[int, tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]] = {
    0: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1)),
        ((0, 0), (0, 1)),
    ),
    1: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (3, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
    ),
    2: (
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ),
    3: (
        ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
    ),
}

# height, width, requested relative corner, profile id; first two are a
# constructive minimum lesson spanning both row and column decisions.
DEMO_SPECS = (
    (12, 16, "top_right", 0),
    (14, 18, "bottom_left", 2),
    (16, 20, "bottom_right", 3),
    (18, 22, "top_left", 1),
    (20, 24, "top_right", 2),
    (22, 26, "bottom_left", 3),
)
QUERY_SPECS = (
    (19, 23, "top_left", 2),
    (21, 25, "top_right", 3),
    (24, 28, "bottom_right", 1),
    (30, 30, "bottom_left", -1),
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
    value = _setting(settings)
    filename = "canonical.rkt" if value == CANONICAL else "relative_corner.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def counterfactual_program(corner: str) -> str:
    """Replace Step A's derived corner with one forced wrong intermediate."""
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    source = (HOME / "relative_corner.rkt").read_text(encoding="utf-8")
    row_old = "(bottom? (> (+ (first bb) (third bb))\n                       (+ (first ba) (third ba))))"
    col_old = "(right? (> (+ (second bb) (fourth bb))\n                      (+ (second ba) (fourth ba))))"
    if source.count(row_old) != 1 or source.count(col_old) != 1:
        raise ValueError("alternative rule changed; review counterfactual materialization")
    row_value = "#t" if corner.startswith("bottom") else "#f"
    col_value = "#t" if corner.endswith("right") else "#f"
    return source.replace(row_old, f"(bottom? {row_value})").replace(
        col_old, f"(right? {col_value})"
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


def _components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for sr in range(height):
        for sc in range(width):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            queue = [(sr, sc)]
            seen.add((sr, sc))
            for r, c in queue:
                for dr, dc in DIRS:
                    q = (r + dr, c + dc)
                    if (0 <= q[0] < height and 0 <= q[1] < width
                            and q not in seen and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        queue.append(q)
            result.append((color, tuple(queue)))
    return result


def _bbox(cells: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _normalize(cells: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _bbox_size(cells: tuple[tuple[int, int], ...] | list[tuple[int, int]]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 + 1, c1 - c0 + 1


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    parts = _components(grid)
    if len(parts) != 2:
        raise ValueError("exactly two nonzero four-connected objects are required")
    if len({color for color, _ in parts}) != 2:
        raise ValueError("objects must use distinct colors")
    ranked = sorted(parts, key=lambda item: (-len(item[1]), *_bbox(item[1])[:2]))
    (large_color, large_raw), (small_color, small_raw) = ranked
    if len(large_raw) == len(small_raw):
        raise ValueError("object sizes must be unequal")
    if any(max(abs(r1 - r2), abs(c1 - c2)) <= 1
           for r1, c1 in large_raw for r2, c2 in small_raw):
        raise ValueError("objects must be separated by at least one background cell")
    large_box, small_box = _bbox(large_raw), _bbox(small_raw)
    large_row_center2 = large_box[0] + large_box[2]
    small_row_center2 = small_box[0] + small_box[2]
    large_col_center2 = large_box[1] + large_box[3]
    small_col_center2 = small_box[1] + small_box[3]
    if large_row_center2 == small_row_center2 or large_col_center2 == small_col_center2:
        raise ValueError("object centers must define a strict relative quadrant")
    corner = (
        ("top" if small_row_center2 < large_row_center2 else "bottom")
        + "_"
        + ("left" if small_col_center2 < large_col_center2 else "right")
    )
    large = _normalize(large_raw)
    small = _normalize(small_raw)
    large_h, large_w = _bbox_size(large)
    small_h, small_w = _bbox_size(small)
    return {
        "object_count": 2,
        "large_color": large_color,
        "small_color": small_color,
        "large_raw": large_raw,
        "small_raw": small_raw,
        "large": large,
        "small": small,
        "large_size": len(large),
        "small_size": len(small),
        "large_bbox": list(large_box),
        "small_bbox": list(small_box),
        "large_shape": [large_h, large_w],
        "small_shape": [small_h, small_w],
        "relative_corner": corner,
    }


def _anchored(cells: tuple[tuple[int, int], ...], shape: list[int], height: int, width: int, corner: str) -> set[tuple[int, int]]:
    dr = height - shape[0] if corner.startswith("bottom") else 0
    dc = width - shape[1] if corner.endswith("right") else 0
    return {(r + dr, c + dc) for r, c in cells}


def transform_with_anchor(grid: list[list[int]], corner: str) -> list[list[int]]:
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    facts = analyze(grid)
    height = max(facts["large_shape"][0], facts["small_shape"][0])
    width = max(facts["large_shape"][1], facts["small_shape"][1])
    large = _anchored(facts["large"], facts["large_shape"], height, width, corner)
    small = _anchored(facts["small"], facts["small_shape"], height, width, corner)
    output = [[0] * width for _ in range(height)]
    for r, c in large - small:
        output[r][c] = facts["large_color"]
    return output


def transform(grid: list[list[int]], setting: str) -> list[list[int]]:
    if setting not in SETTINGS:
        raise ValueError(f"unknown normalization anchor: {setting!r}")
    facts = analyze(grid)
    corner = "top_left" if setting == CANONICAL else facts["relative_corner"]
    return transform_with_anchor(grid, corner)


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "relative-corner-v1", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _orient(cells: tuple[tuple[int, int], ...], orientation: int) -> tuple[tuple[int, int], ...]:
    current = set(cells)
    if orientation >= 4:
        current = {(r, -c) for r, c in current}
    for _ in range(orientation % 4):
        current = {(c, -r) for r, c in current}
    return _normalize(tuple(current))


def _ring(height: int, width: int, hole: tuple[int, int, int, int]) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = hole
    return tuple(
        (r, c)
        for r in range(height)
        for c in range(width)
        if not (r0 <= r <= r1 and c0 <= c <= c1)
    )


def _shapes(profile_id: int) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    if profile_id == -1:
        return _ring(11, 11, (3, 3, 7, 7)), _ring(9, 10, (2, 3, 6, 6))
    return PROFILES[profile_id]


def _place(grid: list[list[int]], cells: tuple[tuple[int, int], ...], color: int, top: int, left: int) -> None:
    for r, c in cells:
        rr, cc = top + r, left + c
        if grid[rr][cc] != 0:
            raise ValueError("sampler attempted overlapping objects")
        grid[rr][cc] = color


def sample_input(seed: int, index: int, spec: tuple[int, int, str, int]) -> tuple[list[list[int]], dict[str, Any]]:
    height, width, corner, profile_id = spec
    orientation = _rng(seed, index, "orientation").randrange(8)
    base_large, base_small = _shapes(profile_id)
    large = _orient(base_large, orientation)
    small = _orient(base_small, orientation)
    large_h, large_w = _bbox_size(large)
    small_h, small_w = _bbox_size(small)
    if height < large_h + small_h + 2 or width < large_w + small_w + 2:
        raise ValueError("spec canvas is too small for separated quadrant placement")
    large_top = 0 if corner.startswith("bottom") else height - large_h
    small_top = height - small_h if corner.startswith("bottom") else 0
    large_left = 0 if corner.endswith("right") else width - large_w
    small_left = width - small_w if corner.endswith("right") else 0
    colors = PALETTES[_rng(seed, index, "palette").randrange(len(PALETTES))]
    grid = [[0] * width for _ in range(height)]
    _place(grid, large, colors[0], large_top, large_left)
    _place(grid, small, colors[1], small_top, small_left)
    facts = analyze(grid)
    if facts["relative_corner"] != corner:
        raise AssertionError("sampler failed to preserve requested relative corner")
    return grid, {
        "source_index": index,
        "shape": [height, width],
        "profile_id": profile_id,
        "orientation": orientation,
        "palette": list(colors),
        "relative_corner": corner,
        "large_size": facts["large_size"],
        "small_size": facts["small_size"],
    }


def _relative_row_only(grid: list[list[int]]) -> list[list[int]]:
    corner = analyze(grid)["relative_corner"]
    return transform_with_anchor(grid, "bottom_left" if corner.startswith("bottom") else "top_left")


def _relative_column_only(grid: list[list[int]]) -> list[list[int]]:
    corner = analyze(grid)["relative_corner"]
    return transform_with_anchor(grid, "top_right" if corner.endswith("right") else "top_left")


def _opposite_relative(grid: list[list[int]]) -> list[list[int]]:
    opposite = {
        "top_left": "bottom_right", "top_right": "bottom_left",
        "bottom_left": "top_right", "bottom_right": "top_left",
    }[analyze(grid)["relative_corner"]]
    return transform_with_anchor(grid, opposite)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_top_left": lambda grid: transform_with_anchor(grid, "top_left"),
    "fixed_top_right": lambda grid: transform_with_anchor(grid, "top_right"),
    "fixed_bottom_left": lambda grid: transform_with_anchor(grid, "bottom_left"),
    "fixed_bottom_right": lambda grid: transform_with_anchor(grid, "bottom_right"),
    "relative_row_only": _relative_row_only,
    "relative_column_only": _relative_column_only,
    "opposite_relative_corner": _opposite_relative,
}


def lesson_certificate(demos: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    if type(demos) is not list or not demos or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    for pair in demos:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each demonstration needs input and output")
        analyze(pair["input"])
        _validate_grid(pair["output"])
    for grid in query_inputs:
        analyze(grid)
    surviving_values = [
        value for value in SETTINGS
        if all(transform(pair["input"], value) == pair["output"] for pair in demos)
    ]
    surviving_settings = [{PARAMETER: value} for value in surviving_values]
    intended_queries = (
        [transform(grid, surviving_values[0]) for grid in query_inputs]
        if len(surviving_values) == 1 else []
    )
    surviving_rivals: list[str] = []
    ambiguous_rivals: list[dict[str, Any]] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            surviving_rivals.append(name)
            if intended_queries:
                disagreements = [
                    i for i, (grid, intended) in enumerate(zip(query_inputs, intended_queries))
                    if rival(grid) != intended
                ]
                if disagreements:
                    ambiguous_rivals.append({"name": name, "query_indices": disagreements})
    return {
        "surviving_settings": surviving_settings,
        "surviving_rivals": surviving_rivals,
        "ambiguous_rivals": ambiguous_rivals,
        "query_count": len(query_inputs),
        "scope": "two declared settings and seven finite fixed/partial/opposite corner shortcuts; demonstrations fitted before query comparisons",
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    setting = _setting(settings)
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")

    train: list[dict[str, Any]] = []
    train_sampling: list[dict[str, Any]] = []
    for index, spec in enumerate(DEMO_SPECS[:demos]):
        grid, receipt = sample_input(seed, index, spec)
        train.append({"input": grid, "output": transform(grid, setting)})
        train_sampling.append(receipt)

    bank: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for source_index, spec in enumerate(QUERY_SPECS):
        grid, receipt = sample_input(seed, 1000 + source_index, spec)
        bank.append(({"input": grid, "output": transform(grid, setting)}, receipt))
    order = list(range(len(bank)))
    _rng(seed, "query-order").shuffle(order)
    selected = order[:queries]
    test = [bank[i][0] for i in selected]
    test_sampling = [dict(bank[i][1], source_query_index=i, presentation_index=j)
                     for j, i in enumerate(selected)]

    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(encoded) != len(set(encoded)):
        raise ValueError("episode contains duplicate inputs")
    certificate = lesson_certificate(train, [pair["input"] for pair in test])
    if certificate["surviving_settings"] != [copy.deepcopy(settings)]:
        raise ValueError("visible demonstrations do not uniquely teach the declared setting")
    if certificate["ambiguous_rivals"]:
        raise ValueError(f"finite shortcut ambiguity: {certificate['ambiguous_rivals']}")
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "certificate": certificate,
        "sampling": {"train": train_sampling, "test": test_sampling, "query_order": order},
        "status": "proposed",
        "training_admitted": False,
    }


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    index = _exact_int(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]}))
