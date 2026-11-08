"""Native parametric family for exact singleton-crop selection.

The canonical setting preserves the selected Racket source byte-for-byte.  The
alternative keeps the same exact singleton selection, then derives a unique
corner marker from the selected crop and flips only the required axes so that
marker moves to the upper-left.
"""
from __future__ import annotations

from collections import Counter, deque
import copy
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "7c2a3ec6c4fb"
PARAMETER = "crop_orientation"
CANONICAL = "as_found"
ALTERNATIVE = "marker_to_top_left"
SETTINGS = (CANONICAL, ALTERNATIVE)
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")
HOME = Path(__file__).resolve().parent

# canvas height, canvas width, crop height, crop width, repeated classes,
# singleton marker corner
DEMO_SPECS = (
    (11, 11, 3, 3, 2, "top_right"),
    (13, 15, 3, 4, 3, "bottom_left"),
    (17, 17, 4, 4, 4, "bottom_right"),
    (19, 21, 4, 5, 2, "top_left"),
    (23, 24, 5, 5, 3, "top_right"),
    (26, 28, 5, 6, 4, "bottom_left"),
)
QUERY_SPECS = (
    (12, 14, 3, 4, 2, "bottom_right"),
    (18, 20, 4, 5, 3, "top_left"),
    (24, 27, 5, 5, 4, "top_right"),
    (30, 30, 6, 6, 4, "bottom_left"),
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
    filename = "canonical.rkt" if orientation == CANONICAL else "marker_to_top_left.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def counterfactual_program(corner: str = "top_left") -> str:
    """Materialize the alternative with Step A replaced by a forced corner."""
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    source = (HOME / "marker_to_top_left.rkt").read_text(encoding="utf-8")
    row_old = "(define row-reverse? (= mr (- ph 1)))"
    col_old = "(define col-reverse? (= mc (- pw 1)))"
    row_value = "#t" if corner.startswith("bottom") else "#f"
    col_value = "#t" if corner.endswith("right") else "#f"
    if source.count(row_old) != 1 or source.count(col_old) != 1:
        raise ValueError("alternative rule changed; review counterfactual materialization")
    return source.replace(row_old, f"(define row-reverse? {row_value})").replace(
        col_old, f"(define col-reverse? {col_value})"
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


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = rr + dr, cc + dc
                        if (
                            (dr or dc)
                            and 0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            result.append(sorted(cells))
    return result


def _crop(grid: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    components = _components(grid)
    if not components:
        raise ValueError("at least one nonzero object is required")
    crops = [_crop(grid, cells) for cells in components]
    encoded = [tuple(tuple(row) for row in crop) for crop in crops]
    counts = Counter(encoded)
    unique_indices = [index for index, pattern in enumerate(encoded) if counts[pattern] == 1]
    if len(unique_indices) != 1:
        raise ValueError("exactly one object crop must occur once")
    selected_index = unique_indices[0]
    selected = crops[selected_index]
    ph, pw = len(selected), len(selected[0])
    frequencies = Counter(cell for row in selected for cell in row if cell != 0)
    corner_positions = {
        "top_left": (0, 0),
        "top_right": (0, pw - 1),
        "bottom_left": (ph - 1, 0),
        "bottom_right": (ph - 1, pw - 1),
    }
    marker_candidates = [
        (name, position, selected[position[0]][position[1]])
        for name, position in corner_positions.items()
        if selected[position[0]][position[1]] != 0
        and frequencies[selected[position[0]][position[1]]] == 1
    ]
    if len(marker_candidates) != 1:
        raise ValueError("selected crop must have exactly one singleton-colored corner marker")
    marker_corner, marker_position, marker_color = marker_candidates[0]
    return {
        "component_count": len(components),
        "crops": crops,
        "pattern_counts": {json.dumps(pattern): count for pattern, count in counts.items()},
        "selected_index": selected_index,
        "selected_crop": selected,
        "selected_shape": [ph, pw],
        "marker_color": marker_color,
        "marker_position": list(marker_position),
        "marker_corner": marker_corner,
    }


def apply_corner(crop: list[list[int]], corner: str) -> list[list[int]]:
    if corner not in CORNERS:
        raise ValueError(f"unknown corner: {corner!r}")
    rows = [list(row) for row in crop]
    if corner.startswith("bottom"):
        rows.reverse()
    if corner.endswith("right"):
        rows = [list(reversed(row)) for row in rows]
    return rows


def transform(grid: list[list[int]], orientation: str) -> list[list[int]]:
    if orientation not in SETTINGS:
        raise ValueError(f"unknown orientation: {orientation!r}")
    analysis = analyze(grid)
    if orientation == CANONICAL:
        return copy.deepcopy(analysis["selected_crop"])
    return apply_corner(analysis["selected_crop"], analysis["marker_corner"])


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "native-crop-v1", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _palette(seed: int) -> tuple[int, int, int]:
    colors = list(range(1, 10))
    _rng(seed, "palette").shuffle(colors)
    return colors[0], colors[1], colors[2]


def _candidate_patterns(
    height: int, width: int, base: int, accent: int, marker: int
) -> list[tuple[str, list[list[int]], tuple[tuple[int, int], ...]]]:
    corner_positions = {
        "top_left": (0, 0),
        "top_right": (0, width - 1),
        "bottom_left": (height - 1, 0),
        "bottom_right": (height - 1, width - 1),
    }
    all_positions = [(r, c) for r in range(height) for c in range(width)]
    candidates: list[tuple[str, list[list[int]], tuple[tuple[int, int], ...]]] = []
    for corner, marker_position in corner_positions.items():
        available = [position for position in all_positions if position != marker_position]
        for accent_positions in combinations(available, 2):
            pattern = [[base for _ in range(width)] for _ in range(height)]
            for r, c in accent_positions:
                pattern[r][c] = accent
            pattern[marker_position[0]][marker_position[1]] = marker
            candidates.append((corner, pattern, accent_positions))
    return candidates


def _slot_indices(count: int) -> list[int]:
    choices = {
        5: [0, 2, 4, 6, 8],
        7: [0, 1, 2, 4, 6, 7, 8],
        9: list(range(9)),
    }
    try:
        return choices[count]
    except KeyError as exc:
        raise ValueError(f"unsupported object count: {count}") from exc


def sample_input(
    seed: int,
    index: int,
    spec: tuple[int, int, int, int, int, str],
) -> tuple[list[list[int]], dict[str, Any]]:
    canvas_h, canvas_w, crop_h, crop_w, repeated_classes, singleton_corner = spec
    base, accent, marker = _palette(seed)
    candidates = _candidate_patterns(crop_h, crop_w, base, accent, marker)
    rng = _rng(seed, index, "patterns", spec)
    singleton_pool = [row for row in candidates if row[0] == singleton_corner]
    singleton = copy.deepcopy(singleton_pool[rng.randrange(len(singleton_pool))][1])
    singleton_key = tuple(tuple(row) for row in singleton)
    repeated_pool = [row for row in candidates if tuple(tuple(x) for x in row[1]) != singleton_key]
    rng.shuffle(repeated_pool)
    repeated = [copy.deepcopy(row[1]) for row in repeated_pool[:repeated_classes]]
    if len({tuple(tuple(row) for row in pattern) for pattern in repeated}) != repeated_classes:
        raise AssertionError("pattern sampler failed to create distinct repeated classes")
    objects: list[tuple[str, list[list[int]]]] = []
    for class_index, pattern in enumerate(repeated):
        objects.extend([(f"repeat_{class_index}", copy.deepcopy(pattern)) for _ in range(2)])
    rng.shuffle(objects)
    slot_indices = _slot_indices(len(objects) + 1)
    row_origins = [0, (canvas_h - crop_h) // 2, canvas_h - crop_h]
    col_origins = [0, (canvas_w - crop_w) // 2, canvas_w - crop_w]
    slots = [(row_origins[i // 3], col_origins[i % 3]) for i in slot_indices]
    singleton_slot = slots.index((row_origins[1], col_origins[1]))
    placed: list[tuple[str, list[list[int]]]] = []
    object_iter = iter(objects)
    for slot_index in range(len(slots)):
        if slot_index == singleton_slot:
            placed.append(("singleton", singleton))
        else:
            placed.append(next(object_iter))
    grid = [[0 for _ in range(canvas_w)] for _ in range(canvas_h)]
    receipts = []
    for (kind, pattern), (top, left) in zip(placed, slots):
        for r, row in enumerate(pattern):
            for c, value in enumerate(row):
                if grid[top + r][left + c] != 0:
                    raise AssertionError("sample objects overlap")
                grid[top + r][left + c] = value
        receipts.append({"kind": kind, "top": top, "left": left})
    analysis = analyze(grid)
    if analysis["marker_corner"] != singleton_corner:
        raise AssertionError("sampler failed to preserve singleton marker corner")
    return grid, {
        "shape": [canvas_h, canvas_w],
        "crop_shape": [crop_h, crop_w],
        "repeated_classes": repeated_classes,
        "object_count": len(placed),
        "singleton_corner": singleton_corner,
        "palette": [base, accent, marker],
        "placements": receipts,
    }


def _fixed_corner(grid: list[list[int]], corner: str) -> list[list[int]]:
    return apply_corner(analyze(grid)["selected_crop"], corner)


def _marker_opposite(grid: list[list[int]]) -> list[list[int]]:
    opposite = {
        "top_left": "bottom_right",
        "top_right": "bottom_left",
        "bottom_left": "top_right",
        "bottom_right": "top_left",
    }[analyze(grid)["marker_corner"]]
    return _fixed_corner(grid, opposite)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_horizontal_flip": lambda grid: _fixed_corner(grid, "top_right"),
    "fixed_vertical_flip": lambda grid: _fixed_corner(grid, "bottom_left"),
    "fixed_both_flips": lambda grid: _fixed_corner(grid, "bottom_right"),
    "opposite_marker_corner": _marker_opposite,
}


def lesson_certificate(
    demos: list[dict[str, Any]], query_inputs: list[list[list[int]]]
) -> dict[str, Any]:
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
        "scope": "two declared settings and four finite fixed/opposite-corner shortcuts; demonstrations fitted before query disagreement checks",
    }


def generate(
    seed: int, settings: dict[str, Any], demos: int, queries: int
) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    orientation = _setting(settings)
    demos = _exact_int(demos, 3, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    pairs: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    sampling: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    for split, count, specs, offset in (
        ("train", demos, DEMO_SPECS, 0),
        ("test", queries, QUERY_SPECS, 1000),
    ):
        for index in range(count):
            grid, receipt = sample_input(seed, offset + index, specs[index])
            pairs[split].append({"input": grid, "output": transform(grid, orientation)})
            sampling[split].append(receipt)
    encoded = [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in pairs.values()
        for pair in split
    ]
    if len(encoded) != len(set(encoded)):
        raise ValueError("episode contains duplicate inputs")
    certificate = lesson_certificate(
        pairs["train"], [pair["input"] for pair in pairs["test"]]
    )
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
