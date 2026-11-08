"""Parametric episodes for 64bd7bc767bb.

The canonical setting keeps the exact bottom-aligned count bars.  The nearby
setting first selects the uniquely most frequent counted color, measures the
orientation of that color's input bounding box, and then uses that intermediate
to choose top- versus bottom-alignment for all four count bars.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import random
from typing import Any


TASK_ID = "64bd7bc767bb"
SETTINGS = (
    {"alignment_rule": "bottom"},
    {"alignment_rule": "winner_bbox"},
)
RIVALS = (
    "always_top",
    "color1_bbox",
    "largest_bbox",
    "rank_sorted_counts",
)

_ALTERNATE_PATH = Path(__file__).with_name("winner_bbox.rkt")


def _setting(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"alignment_rule"}:
        raise ValueError("settings must name exactly alignment_rule")
    value = settings["alignment_rule"]
    if value not in ("bottom", "winner_bbox"):
        raise ValueError("alignment_rule must be bottom or winner_bbox")
    return value


def program(settings: dict[str, Any]) -> str:
    value = _setting(settings)
    if value == "bottom":
        return Path(__file__).with_name("canonical.rkt").read_text()
    return _ALTERNATE_PATH.read_text()


def _rng(seed: int, domain: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(sha256(payload).digest(), "big"))


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")


def _validate_grid(grid: list[list[int]]) -> None:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 4 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and 4..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")


def _regions(h: int, w: int) -> list[tuple[int, int, int, int]]:
    split_r, split_c = h // 2, w // 2
    regions = [
        (1, split_r - 1, 1, split_c - 1),
        (1, split_r - 1, split_c + 1, w - 2),
        (split_r + 1, h - 2, 1, split_c - 1),
        (split_r + 1, h - 2, split_c + 1, w - 2),
    ]
    if any(r2 - r1 + 1 < 5 or c2 - c1 + 1 < 5 for r1, r2, c1, c2 in regions):
        raise ValueError("scene dimensions do not leave four 5x5 teaching regions")
    return regions


def _dense_shape(
    region: tuple[int, int, int, int],
    count: int,
    orientation: str,
    rng: random.Random,
) -> set[tuple[int, int]]:
    r1, r2, c1, c2 = region
    region_h, region_w = r2 - r1 + 1, c2 - c1 + 1
    # A four-cell shape would otherwise collapse to a 2x2 square and lose
    # the orientation that drives the alternate rule.  Reserve at least a
    # three-cell long axis, then sample exactly ``count`` cells inside it.
    long_axis = max(3, (count + 1) // 2)
    if orientation == "horizontal":
        box_h, box_w = 2, long_axis
    else:
        box_h, box_w = long_axis, 2
    if box_h > region_h or box_w > region_w or box_h == box_w:
        raise ValueError(f"cannot fit {count}-cell {orientation} shape in {region}")
    r0 = rng.randint(r1, r2 - box_h + 1)
    c0 = rng.randint(c1, c2 - box_w + 1)
    cells = [(r0 + dr, c0 + dc) for dr in range(box_h) for dc in range(box_w)]
    # Counts are even in this grammar, but retain both bbox extremes if that
    # ever changes.
    required = {(r0, c0), (r0 + box_h - 1, c0 + box_w - 1)}
    chosen = list(required)
    extras = [cell for cell in cells if cell not in required]
    rng.shuffle(extras)
    chosen.extend(extras[: count - len(chosen)])
    return set(chosen)


def _sparse_shape(
    region: tuple[int, int, int, int],
    count: int,
    orientation: str,
    rng: random.Random,
) -> set[tuple[int, int]]:
    r1, r2, c1, c2 = region
    if orientation == "horizontal":
        rows = (rng.randint(r1, r2 - 1), None)
        rows = (rows[0], rows[0] + 1)
        candidates = [(r, c) for r in rows for c in range(c1, c2 + 1)]
        required = {(rows[0], c1), (rows[0], c2), (rows[1], c1), (rows[1], c2)}
    else:
        cols = (rng.randint(c1, c2 - 1), None)
        cols = (cols[0], cols[0] + 1)
        candidates = [(r, c) for r in range(r1, r2 + 1) for c in cols]
        required = {(r1, cols[0]), (r2, cols[0]), (r1, cols[1]), (r2, cols[1])}
    if count < len(required) or count > len(candidates):
        raise ValueError("sparse shape count is outside its oriented box capacity")
    extras = [cell for cell in candidates if cell not in required]
    rng.shuffle(extras)
    return required | set(extras[: count - len(required)])


def _bbox(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"missing counted color {color}")
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows), max(cols)


def _orientation(grid: list[list[int]], color: int) -> str:
    r1, c1, r2, c2 = _bbox(grid, color)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if width == height:
        raise ValueError(f"color {color} has a square bounding box")
    return "horizontal" if width > height else "vertical"


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    counts_by_value = Counter(value for row in grid for value in row)
    counts = tuple(counts_by_value[color] for color in range(1, 5))
    if any(count <= 0 or count >= len(grid) for count in counts):
        raise ValueError("each counted color must occur 1..height-1 times")
    maximum = max(counts)
    winners = [color for color, count in enumerate(counts, 1) if count == maximum]
    if len(winners) != 1:
        raise ValueError("the most frequent counted color must be unique")
    winner = winners[0]
    bboxes = {color: _bbox(grid, color) for color in range(1, 5)}
    return {
        "counts": counts,
        "winner_color": winner,
        "winner_bbox": bboxes[winner],
        "winner_orientation": _orientation(grid, winner),
        "bboxes": bboxes,
    }


def _bars(grid: list[list[int]], counts: tuple[int, ...], *, top: bool) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    output = [[0 for _ in range(w)] for _ in range(h)]
    for column, (color, count) in enumerate(zip(range(1, 5), counts)):
        rows = range(count) if top else range(h - count, h)
        for row in rows:
            output[row][column] = color
    return output


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    rule = _setting(settings)
    analysis = analyze(grid)
    top = rule == "winner_bbox" and analysis["winner_orientation"] == "horizontal"
    return _bars(grid, analysis["counts"], top=top)


def _scene(seed: int, domain: str, index: int, h: int, w: int) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    regions = _regions(h, w)
    min_span = min(min(r2 - r1 + 1, c2 - c1 + 1) for r1, r2, c1, c2 in regions)
    maximum = min(22, h - 1, 2 * (min_span - 1))
    maximum -= maximum % 2
    if maximum < 10:
        raise ValueError("scene is too small for four distinct oriented counts")

    winner_schedule = (4, 3, 2, 1, 4, 2, 3, 1, 2, 4)
    winner = winner_schedule[index % len(winner_schedule)]
    decoy = 1 if winner != 1 else 2
    remaining = [color for color in range(1, 5) if color not in (winner, decoy)]
    counts = {
        winner: maximum,
        decoy: maximum - 2,
        remaining[0]: maximum - 6,
        remaining[1]: maximum - 4,
    }
    winner_orientation = "horizontal" if index % 2 == 0 else "vertical"
    opposite = "vertical" if winner_orientation == "horizontal" else "horizontal"
    orientations = {
        winner: winner_orientation,
        decoy: opposite,
        remaining[0]: "horizontal" if index % 3 else "vertical",
        remaining[1]: "vertical" if index % 3 else "horizontal",
    }

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for color in range(1, 5):
        region = regions[color - 1]
        shape_rng = _rng(seed, f"{domain}-shape-{color}", index)
        if color == decoy:
            cells = _sparse_shape(region, counts[color], orientations[color], shape_rng)
        else:
            cells = _dense_shape(region, counts[color], orientations[color], shape_rng)
        for r, c in cells:
            grid[r][c] = color

    # Add ignored colors across the remaining canvas.  Their density scales up
    # on the 30x30 stress case while never influencing either program.
    available = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    rng.shuffle(available)
    distractor_count = min(40, max(10, (h * w) // 20))
    for offset, (r, c) in enumerate(available[:distractor_count]):
        grid[r][c] = 5 + offset % 5

    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if rng.randrange(2):
        grid = grid[::-1]
    analyze(grid)  # assert the intended input grammar before returning
    return grid


def _alignment_from_color(grid: list[list[int]], color: int) -> bool:
    return _orientation(grid, color) == "horizontal"


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    analysis = analyze(grid)
    if name == "always_top":
        return _bars(grid, analysis["counts"], top=True)
    if name == "color1_bbox":
        return _bars(grid, analysis["counts"], top=_alignment_from_color(grid, 1))
    if name == "largest_bbox":
        areas = {
            color: (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
            for color, bbox in analysis["bboxes"].items()
        }
        selected = max(range(1, 5), key=lambda color: (areas[color], -color))
        return _bars(grid, analysis["counts"], top=_alignment_from_color(grid, selected))
    if name == "rank_sorted_counts":
        return _bars(grid, tuple(sorted(analysis["counts"])), top=False)
    raise ValueError(f"unknown rival {name}")


def teaching_check(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    _setting(settings)
    demos = episode["train"]
    survivors = [
        candidate
        for candidate in SETTINGS
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    surviving_rivals = [
        name
        for name in RIVALS
        if all(rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": surviving_rivals,
        "scope": "two declared settings and four named shortcut rules; demonstrations only",
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    _setting(settings)
    _validate_request(seed, demos, queries)
    demo_sizes = [(16, 18), (18, 16), (20, 22), (22, 20), (24, 26), (26, 24)]
    query_sizes = [(18, 20), (20, 18), (24, 28), (30, 30)]
    _rng(seed, "query-order", 0).shuffle(query_sizes)

    train = []
    for index, (h, w) in enumerate(demo_sizes[:demos]):
        grid = _scene(seed, "demo", index, h, w)
        train.append({"input": grid, "output": transform(grid, settings)})
    test = []
    for index, (h, w) in enumerate(query_sizes[:queries]):
        grid = _scene(seed, "query", index + 6, h, w)
        test.append({"input": grid, "output": transform(grid, settings)})

    episode = {"train": train, "test": test, "program_solution": program(settings)}
    check = teaching_check(episode, settings)
    if check["survivors"] != [settings] or check["surviving_rivals"]:
        raise ValueError(f"demonstrations do not identify the requested rule: {check}")
    return episode
