"""Matched-input parametric family for rectangle-border topology.

The canonical setting completes every inferred rectangle border.  The alternate
setting first performs that exact completion, recomputes zero-cell connected
regions on the resulting grid, and fills only the uniquely largest region that
no longer touches the grid boundary.  Nested rectangles make that intermediate
a genuine topology result rather than a direct original-box selection.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
POLICIES = ("borders_only", "largest_enclosure")
FILL_COLOR = 8
CANONICAL_SHA256 = "486ca16c83e15864e35f8c366a80e1370c46ef77022e9d549af3cf4268193553"

# Boxes are inclusive: (r0, r1, c0, c1).  The first two lessons deliberately
# contain horizontal/vertical thin rectangles while their nested thick pair
# creates two enclosed regions.  The remaining scenes broaden topology, size,
# boundary contact, and which enclosed region wins.
_DEMO_SPECS = (
    (16, 24, ((1, 14, 1, 13), (4, 10, 4, 9), (2, 3, 17, 22))),
    (17, 24, ((2, 14, 10, 22), (4, 12, 12, 20), (1, 8, 2, 3))),
    (15, 22, ((1, 10, 1, 10), (3, 8, 3, 8), (2, 12, 14, 20))),
    (18, 20, ((1, 16, 1, 18), (4, 13, 5, 14))),
    (12, 18, ((0, 10, 0, 10), (3, 8, 3, 8), (1, 9, 13, 17))),
    (22, 25, ((1, 20, 1, 23), (4, 17, 5, 20), (8, 14, 9, 16))),
)
_QUERY_SPECS = (
    (14, 23, ((1, 11, 1, 10), (3, 9, 3, 8), (2, 12, 15, 22))),
    (20, 20, ((1, 18, 1, 18), (4, 16, 3, 16), (7, 13, 7, 12))),
    (24, 28, ((0, 23, 0, 15), (4, 19, 4, 12), (2, 21, 20, 27))),
    (30, 30, ((0, 29, 0, 29), (4, 25, 3, 26), (10, 20, 9, 21))),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(value: Any) -> str:
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"enclosure_policy must be one of {POLICIES}")
    return value


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid must have 1..30 rows and columns")
    if any(
        type(row) is not list
        or len(row) != w
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return h, w


def _border(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, r1, c0, c1 = box
    result = {(r0, c) for c in range(c0, c1 + 1)}
    result.update((r1, c) for c in range(c0, c1 + 1))
    result.update((r, c0) for r in range(r0, r1 + 1))
    result.update((r, c1) for r in range(r0, r1 + 1))
    return result


def rectangles(grid: list[list[int]]) -> list[dict[str, Any]]:
    _validate_grid(grid)
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    result = []
    for color in sorted(by_color):
        cells = by_color[color]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(cells) != 4 or len(rows) != 2 or len(cols) != 2:
            raise ValueError(f"color {color} must mark exactly four rectangle corners")
        expected = {(rows[0], cols[0]), (rows[0], cols[1]), (rows[1], cols[0]), (rows[1], cols[1])}
        if set(cells) != expected:
            raise ValueError(f"color {color} cells are not a Cartesian corner set")
        box = (rows[0], rows[1], cols[0], cols[1])
        result.append({"color": color, "box": box, "border": _border(box)})
    if not 2 <= len(result) <= 3:
        raise ValueError("expected two or three rectangle colors")
    for index, left in enumerate(result):
        for right in result[index + 1 :]:
            if left["border"] & right["border"]:
                raise ValueError("rectangle borders must not overlap")
    return result


def complete_borders(grid: list[list[int]]) -> list[list[int]]:
    output = deepcopy(grid)
    for rectangle in rectangles(grid):
        for r, c in rectangle["border"]:
            output[r][c] = rectangle["color"]
    return output


def zero_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = _validate_grid(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    result: list[list[tuple[int, int]]] = []
    for origin in [(r, c) for r in range(h) for c in range(w)]:
        if origin not in unseen:
            continue
        unseen.remove(origin)
        queue = deque([origin])
        region: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            region.append((r, c))
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(region)
    return result


def enclosed_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = _validate_grid(grid)
    return [
        region
        for region in zero_regions(grid)
        if not any(r in (0, h - 1) or c in (0, w - 1) for r, c in region)
    ]


def _largest(regions: list[list[tuple[int, int]]]) -> list[tuple[int, int]]:
    best: list[tuple[int, int]] = []
    for region in regions:
        if len(region) > len(best):
            best = region
    return best


def _paint(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> list[list[int]]:
    output = deepcopy(grid)
    for r, c in cells:
        output[r][c] = color
    return output


def solve(grid: list[list[int]], policy: str) -> list[list[int]]:
    policy = _policy(policy)
    framed = complete_borders(grid)
    if policy == "borders_only":
        return framed
    return _paint(framed, _largest(enclosed_regions(framed)), FILL_COLOR)


def skip_completion(grid: list[list[int]]) -> list[list[int]]:
    """Concrete skip-A rival: run the enclosure selector on the corner-only input."""
    return _paint(grid, _largest(enclosed_regions(grid)), FILL_COLOR)


def _bbox_area(cells: list[tuple[int, int]]) -> int:
    if not cells:
        return 0
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def analyze_after_borders(grid: list[list[int]]) -> dict[str, Any]:
    framed = complete_borders(grid)
    regions = enclosed_regions(framed)
    winner = _largest(regions)
    sizes = [len(region) for region in regions]
    return {
        "completed": framed,
        "enclosed_regions": regions,
        "region_sizes": sizes,
        "winner": winner,
        "winner_bbox_area": _bbox_area(winner),
        "unique_largest": bool(sizes) and sizes.count(max(sizes)) == 1,
    }


def _canonical_source() -> str:
    source = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if hashlib.sha256(source.encode()).hexdigest() != CANONICAL_SHA256:
        raise ValueError("canonical.rkt differs from the selected canonical program")
    return source


def program(policy: str) -> str:
    policy = _policy(policy)
    canonical = _canonical_source()
    if policy == "borders_only":
        return canonical
    prefix = "(rule! "
    if not canonical.startswith(prefix) or not canonical.endswith(")"):
        raise ValueError("canonical program does not have the expected rule! wrapper")
    body = canonical[len(prefix) : -1]
    return (
        "(rule! (let* ((framed "
        + body
        + ") (hh (rows framed)) (ww (cols framed)) "
        + "(regions (find-0-regions framed 0)) "
        + "(enclosed (filter (lambda (region) "
        + "(not (ormap (lambda (p) (let ((r (first p)) (c (second p))) "
        + "(or (= r 0) (= r (- hh 1)) (= c 0) (= c (- ww 1))))) region))) regions)) "
        + "(winner (for/fold ((best '())) ((region (in-list enclosed))) "
        + "(if (> (length region) (length best)) region best)))) "
        + "(if (null? winner) framed (paint-cells framed winner 8))))"
    )


def _seeded_rng(seed: int, stream: str, index: int = 0) -> random.Random:
    payload = f"5c577e82a07f-enclosure-v1:{seed}:{stream}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _transform_box(
    box: tuple[int, int, int, int], h: int, w: int, flip_v: bool, flip_h: bool
) -> tuple[int, int, int, int]:
    r0, r1, c0, c1 = box
    if flip_v:
        r0, r1 = h - 1 - r1, h - 1 - r0
    if flip_h:
        c0, c1 = w - 1 - c1, w - 1 - c0
    return r0, r1, c0, c1


def _scene(spec: tuple[Any, ...], seed: int, stream: str, index: int) -> list[list[int]]:
    h, w, boxes = spec
    rng = _seeded_rng(seed, stream, index)
    flip_v, flip_h = bool(rng.randrange(2)), bool(rng.randrange(2))
    transformed = [_transform_box(box, h, w, flip_v, flip_h) for box in boxes]
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], len(transformed))
    rng.shuffle(colors)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for color, (r0, r1, c0, c1) in zip(colors, transformed):
        for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
            if grid[r][c] != 0:
                raise ValueError("constructed rectangle corners overlap")
            grid[r][c] = color
    analysis = analyze_after_borders(grid)
    if len(analysis["enclosed_regions"]) < 2 or not analysis["unique_largest"]:
        raise ValueError("scene does not have a unique largest completed enclosure")
    if solve(grid, "borders_only") == solve(grid, "largest_enclosure"):
        raise ValueError("settings do not disagree on constructed scene")
    return grid


def episode_inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")

    # Keep the two decisive thin-profile lessons first (order may swap), then
    # shuffle the remaining lessons.  Query roles are independently permuted;
    # requesting fewer queries retains an exact prefix.
    first = [0, 1]
    if _seeded_rng(seed, "demo-prefix").randrange(2):
        first.reverse()
    rest = list(range(2, len(_DEMO_SPECS)))
    _seeded_rng(seed, "demo-rest").shuffle(rest)
    demo_order = first + rest
    query_order = list(range(len(_QUERY_SPECS)))
    _seeded_rng(seed, "query-order").shuffle(query_order)

    train = [
        _scene(_DEMO_SPECS[spec_index], seed, "train", spec_index)
        for spec_index in demo_order[:demos]
    ]
    test = [
        _scene(_QUERY_SPECS[spec_index], seed, "test", spec_index)
        for spec_index in query_order[:queries]
    ]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("episode inputs must be distinct")
    return train, test


def generate_episode(seed: int, policy: str, demos: int, queries: int) -> dict[str, Any]:
    policy = _policy(policy)
    train_inputs, test_inputs = episode_inputs(seed, demos, queries)
    return {
        "train": [{"input": grid, "output": solve(grid, policy)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, policy)} for grid in test_inputs],
        "program_solution": program(policy),
        "seed": seed,
        "settings": {"enclosure_policy": policy},
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


# ---------------------------------------------------------------------------
# Finite authoring rival bank.  These are executable Python semantics used for
# bounded teaching checks; native qualification independently fits the declared
# Racket settings from demonstrations.
# ---------------------------------------------------------------------------

def _identity(grid):
    return deepcopy(grid)


def _solid_boxes(grid):
    output = deepcopy(grid)
    for rectangle in rectangles(grid):
        r0, r1, c0, c1 = rectangle["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = rectangle["color"]
    return output


def _edges(grid, horizontal: bool):
    output = deepcopy(grid)
    for rectangle in rectangles(grid):
        r0, r1, c0, c1 = rectangle["box"]
        if horizontal:
            for c in range(c0, c1 + 1):
                output[r0][c] = rectangle["color"]
                output[r1][c] = rectangle["color"]
        else:
            for r in range(r0, r1 + 1):
                output[r][c0] = rectangle["color"]
                output[r][c1] = rectangle["color"]
    return output


def _first_n(grid, count: int):
    output = deepcopy(grid)
    for rectangle in rectangles(grid)[:count]:
        for r, c in rectangle["border"]:
            output[r][c] = rectangle["color"]
    return output


def _ignore_thin(grid, axis: str):
    output = deepcopy(grid)
    for rectangle in rectangles(grid):
        r0, r1, c0, c1 = rectangle["box"]
        height, width = r1 - r0 + 1, c1 - c0 + 1
        if (axis == "horizontal" and height == 2) or (axis == "vertical" and width == 2):
            continue
        for r, c in rectangle["border"]:
            output[r][c] = rectangle["color"]
    return output


def _fill_regions(grid, selector: Callable[[list[list[tuple[int, int]]]], list[list[tuple[int, int]]]]) -> list[list[int]]:
    framed = complete_borders(grid)
    selected = selector(enclosed_regions(framed))
    output = deepcopy(framed)
    for region in selected:
        for r, c in region:
            output[r][c] = FILL_COLOR
    return output


def _all_selector(regions):
    return regions


def _smallest_selector(regions):
    return [min(regions, key=len)] if regions else []


def _first_selector(regions):
    return regions[:1]


def _last_selector(regions):
    return regions[-1:] if regions else []


def _largest_rectangle_interior(grid):
    framed = complete_borders(grid)
    rectangle = max(
        rectangles(grid),
        key=lambda item: (item["box"][1] - item["box"][0] - 1)
        * (item["box"][3] - item["box"][2] - 1),
    )
    r0, r1, c0, c1 = rectangle["box"]
    output = deepcopy(framed)
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if output[r][c] == 0:
                output[r][c] = FILL_COLOR
    return output


def _wrong_fill_color(grid):
    framed = complete_borders(grid)
    return _paint(framed, _largest(enclosed_regions(framed)), 3)


RIVALS: dict[str, dict[str, Callable[[list[list[int]]], list[list[int]]]]] = {
    "borders_only": {
        "identity": _identity,
        "solid_boxes": _solid_boxes,
        "horizontal_edges_only": lambda grid: _edges(grid, True),
        "vertical_edges_only": lambda grid: _edges(grid, False),
        "first_color_only": lambda grid: _first_n(grid, 1),
        "first_two_colors_only": lambda grid: _first_n(grid, 2),
        "ignore_thin_horizontal": lambda grid: _ignore_thin(grid, "horizontal"),
        "ignore_thin_vertical": lambda grid: _ignore_thin(grid, "vertical"),
    },
    "largest_enclosure": {
        "borders_only": complete_borders,
        "fill_all_enclosures": lambda grid: _fill_regions(grid, _all_selector),
        "fill_smallest_enclosure": lambda grid: _fill_regions(grid, _smallest_selector),
        "fill_first_enclosure": lambda grid: _fill_regions(grid, _first_selector),
        "fill_last_enclosure": lambda grid: _fill_regions(grid, _last_selector),
        "fill_largest_rectangle_interior": _largest_rectangle_interior,
        "skip_border_completion": skip_completion,
        "fill_winner_with_color_3": _wrong_fill_color,
    },
}


def surviving_rivals(demos: list[dict[str, Any]], policy: str) -> list[str]:
    policy = _policy(policy)
    survivors = []
    for name, rival in RIVALS[policy].items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    return survivors
