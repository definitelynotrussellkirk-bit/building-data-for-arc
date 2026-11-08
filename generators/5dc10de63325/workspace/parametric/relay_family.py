"""Native parametric family for 5dc10de63325.

The exact canonical default counts cyan cells, floor-divides by four, and
repeats the corresponding 2x2 glyph around a zero cross.  The alternate keeps
that entire stage, then uses the resulting bucket as an input-dependent index
into four row-major marker cells and writes the selected marker color into the
center of the 5x5 output.

The marker order and colors vary per input, so the second operation cannot be
reduced to a fixed color or performed before the count-derived bucket exists.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "5dc10de63325"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "bucket_color_relay")
DEFAULT_MODE = "canonical"
HYPOTHESES = MODES + (
    "nearest_bucket_relay",
    "remainder_bucket_relay",
    "ceiling_bucket_relay",
    "reverse_marker_order_relay",
    "column_major_marker_order_relay",
    "constant_first",
    "constant_second",
    "constant_third",
    "constant_fourth",
)

DEMO_PROFILES = (
    (8, 8, 7, "scatter"),
    (9, 10, 11, "snake"),
    (10, 9, 15, "block"),
    (12, 12, 19, "diagonal"),
    (14, 13, 6, "scatter"),
    (16, 15, 10, "snake"),
)
QUERY_PROFILES = (
    (9, 11, 6, "block"),
    (11, 13, 10, "diagonal"),
    (14, 16, 14, "scatter"),
    (30, 30, 18, "snake"),
)


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    selected = _mode(mode)
    return _read("canonical.rkt" if selected == "canonical" else "bucket_color_relay.rkt")


def counterfactual_program() -> str:
    return _read("wrong_remainder_bucket.rkt")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(value: Any, *, hypothesis: bool = False) -> str:
    options = HYPOTHESES if hypothesis else MODES
    if type(value) is not str or value not in options:
        raise ValueError(f"mode must be one of {options}")
    return value


def validate_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _glyph(bucket: int) -> list[list[int]]:
    if bucket == 1:
        tile = ((0, 0), (0, 8))
    elif bucket == 2:
        tile = ((0, 0), (8, 8))
    elif bucket == 3:
        tile = ((0, 8), (8, 8))
    elif bucket == 4:
        tile = ((8, 8), (8, 8))
    else:
        tile = ((0, 0), (0, 0))
    out = _blank(5, 5)
    for top, left in ((0, 0), (0, 3), (3, 0), (3, 3)):
        for r in range(2):
            for c in range(2):
                out[top + r][left + c] = tile[r][c]
    return out


def _markers(grid: list[list[int]], ordering: str = "row_major") -> list[tuple[int, int, int]]:
    result = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    if ordering == "row_major":
        return sorted(result, key=lambda item: (item[0], item[1]))
    if ordering == "reverse":
        return list(reversed(sorted(result, key=lambda item: (item[0], item[1]))))
    if ordering == "column_major":
        return sorted(result, key=lambda item: (item[1], item[0]))
    raise ValueError(f"unknown marker ordering {ordering!r}")


def _bucket(grid: list[list[int]], hypothesis: str) -> int:
    count = sum(cell == 8 for row in grid for cell in row)
    if hypothesis == "nearest_bucket_relay":
        return min(4, (count + 2) // 4)
    if hypothesis == "remainder_bucket_relay":
        return (count % 4) + 1
    if hypothesis == "ceiling_bucket_relay":
        return min(4, (count + 3) // 4)
    if hypothesis == "constant_first":
        return 1
    if hypothesis == "constant_second":
        return 2
    if hypothesis == "constant_third":
        return 3
    if hypothesis == "constant_fourth":
        return 4
    return count // 4


def transform(value: Any, mode: str) -> list[list[int]]:
    grid = validate_grid(value)
    selected = _mode(mode, hypothesis=True)
    count = sum(cell == 8 for row in grid for cell in row)
    canonical_bucket = count // 4
    output = _glyph(canonical_bucket)
    if selected == "canonical":
        return output

    ordering = (
        "reverse"
        if selected == "reverse_marker_order_relay"
        else "column_major"
        if selected == "column_major_marker_order_relay"
        else "row_major"
    )
    markers = _markers(grid, ordering)
    selector = _bucket(grid, selected)
    if len(markers) != 4 or not 1 <= selector <= 4:
        raise ValueError("relay requires four markers and a selector in 1..4")
    output[2][2] = markers[selector - 1][2]
    return output


def explain_dependency(value: Any) -> dict[str, Any]:
    grid = validate_grid(value)
    markers = _markers(grid)
    count = sum(cell == 8 for row in grid for cell in row)
    selector = count // 4
    counterfactual = (count % 4) + 1
    if len(markers) != 4 or not 1 <= selector <= 4:
        raise ValueError("scene is outside the authored relay domain")
    return {
        "step_a": "count cyan cells and floor-divide the count by four",
        "intermediate": "the canonical glyph bucket in 1..4",
        "step_b": "select the bucket-indexed row-major marker and write its color into the center",
        "why_b_depends_on_a": "the marker color cannot be selected until the count-derived bucket is known, while marker order and colors vary independently",
        "cyan_count": count,
        "selector": selector,
        "counterfactual_selector": counterfactual,
        "markers": [
            {"row": r, "column": c, "color": color} for r, c, color in markers
        ],
        "selected_color": markers[selector - 1][2],
        "counterfactual_color": markers[counterfactual - 1][2],
        "output": transform(grid, "bucket_color_relay"),
        "counterfactual_output": transform(grid, "remainder_bucket_relay"),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"5dc10de63325-bucket-color-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _profile(split: str, index: int) -> tuple[int, int, int, str]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    return profiles[index]


def _marker_positions(height: int, width: int, index: int) -> list[tuple[int, int]]:
    # Two top-row and two bottom-row markers make row-major and column-major
    # ordering observably different at index two, while touching all four edges.
    if index % 2 == 0:
        return [(0, 0), (0, width - 1), (height - 1, 1), (height - 1, width - 2)]
    return [(0, 1), (0, width - 2), (height - 1, 0), (height - 1, width - 1)]


def _cyan_candidates(height: int, width: int, pattern: str) -> list[tuple[int, int]]:
    interior = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]
    if pattern == "block":
        return interior
    if pattern == "snake":
        return [
            (r, c)
            for r in range(1, height - 1)
            for c in (range(1, width - 1) if r % 2 else range(width - 2, 0, -1))
        ]
    if pattern == "diagonal":
        return sorted(interior, key=lambda p: ((p[0] - p[1]) % max(height, width), p[0], p[1]))
    if pattern == "scatter":
        return interior
    raise ValueError(f"unknown cyan pattern {pattern!r}")


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, cyan_count, pattern = _profile(split, index)
    rng = _rng(seed, split, index)
    grid = _blank(height, width)

    colors = list(range(1, 8))
    rng.shuffle(colors)
    marker_colors = colors[:4]
    positions = _marker_positions(height, width, index)
    # Rotate the independent color permutation by seed/index to prevent a fixed
    # marker-index-to-color mapping across episodes.
    shift = (seed + index + (0 if split == "train" else 2)) % 4
    marker_colors = marker_colors[shift:] + marker_colors[:shift]
    for (r, c), color in zip(positions, marker_colors):
        grid[r][c] = color

    candidates = _cyan_candidates(height, width, pattern)
    if pattern == "scatter":
        rng.shuffle(candidates)
    elif pattern == "diagonal":
        offset = rng.randrange(len(candidates))
        candidates = candidates[offset:] + candidates[:offset]
    for r, c in candidates[:cyan_count]:
        grid[r][c] = 8

    _validate_scene(grid, expected_count=cyan_count)
    return grid


def _validate_scene(value: Any, *, expected_count: int | None = None) -> None:
    grid = validate_grid(value)
    count = sum(cell == 8 for row in grid for cell in row)
    markers = _markers(grid)
    if expected_count is not None and count != expected_count:
        raise ValueError(f"scene contains {count} cyan cells, expected {expected_count}")
    if not 4 <= count <= 19 or not 1 <= count // 4 <= 4:
        raise ValueError("cyan count must produce a canonical bucket in 1..4")
    if len(markers) != 4:
        raise ValueError(f"scene must contain exactly four markers, found {len(markers)}")
    colors = [color for _, _, color in markers]
    if len(set(colors)) != 4:
        raise ValueError("marker colors must be distinct")
    if _markers(grid, "row_major")[1][2] == _markers(grid, "column_major")[1][2]:
        raise ValueError("scene must distinguish row-major from column-major marker order")


def certificate(train: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(transform(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    declared = [mode for mode in MODES if mode in survivors]
    selected = declared[0] if len(declared) == 1 else None
    query_changing = []
    if selected is not None:
        for hypothesis in survivors:
            if any(transform(grid, hypothesis) != transform(grid, selected) for grid in query_inputs):
                query_changing.append(hypothesis)
    return {
        "survivors": survivors,
        "selected_declared_mode": selected,
        "query_changing_survivors": query_changing,
        "hypotheses": list(HYPOTHESES),
    }


def build_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    selected = _mode(mode)
    seen: set[tuple[tuple[int, ...], ...]] = set()

    def collect(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        pairs = []
        for index in range(count):
            grid = _scene(seed, split, index)
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                raise RuntimeError("scene schedule produced a duplicate input")
            seen.add(key)
            pairs.append({"input": grid, "output": transform(grid, selected)})
        return pairs

    return {
        "train": collect("train", demos),
        "test": collect("test", queries),
        "program_solution": program_for(selected),
    }
