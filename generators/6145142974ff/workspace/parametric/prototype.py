"""Native parametric family for exact-match selection followed by bridges.

``canonical`` is the exact selected Racket authority. ``bridge_matches`` first
runs that selection into a blank Stage-A mask, then discovers the surviving
components in the intermediate and connects consecutive components with
horizontal-then-vertical Manhattan bridges.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "6145142974ff"
HERE = Path(__file__).resolve().parent
FINISHES = ("canonical", "bridge_matches")
CANONICAL_PROGRAM_SHA256 = "d5061c3b9df5b82102e0f236707adb449060773cb62b2ffa128a4045a210a6be"
HYPOTHESES = FINISHES + (
    "all_green_bridge",
    "same_size_bridge",
    "vertical_first_bridge",
    "first_match_only",
    "last_match_only",
    "bbox_bridge",
)

SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "l3": ((0, 0), (1, 0), (1, 1)),
    "corner3": ((0, 0), (0, 1), (1, 0)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "s4_vertical": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "s4_horizontal": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "long_l5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "zigzag5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
}
DISTRACTORS: dict[str, tuple[tuple[int, int], ...]] = {
    "l3": ((0, 0), (0, 1), (0, 2)),
    "corner3": ((0, 0), (1, 0), (2, 0)),
    "t4": SHAPES["square4"],
    "s4_vertical": SHAPES["t4"],
    "s4_horizontal": SHAPES["square4"],
    "square4": SHAPES["t4"],
    "long_l5": SHAPES["zigzag5"],
    "zigzag5": SHAPES["long_l5"],
}
MARKER_COLORS = (2, 4, 5, 6, 7, 8, 9)

# Separate, prefix-stable streams for demonstrations and queries.
TRAIN_PROFILES = (
    (12, 14, "l3", 2, 1),
    (14, 16, "t4", 3, 2),
    (16, 18, "long_l5", 3, 1),
    (18, 20, "s4_vertical", 4, 2),
    (20, 22, "square4", 4, 3),
    (22, 24, "zigzag5", 5, 3),
)
QUERY_PROFILES = (
    (13, 15, "corner3", 2, 2),
    (17, 21, "s4_horizontal", 3, 2),
    (24, 26, "long_l5", 5, 4),
    (30, 30, "zigzag5", 6, 5),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain only finish")
    value = settings["finish"]
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def program(settings: Any) -> str:
    finish = _finish(settings)
    name = "canonical.rkt" if finish == "canonical" else "bridge_matches.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
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


def _components(grid: list[list[int]], color: int | None = None) -> list[frozenset[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    cells = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (grid[r][c] != 0 if color is None else grid[r][c] == color)
    }
    result: list[frozenset[tuple[int, int]]] = []
    while cells:
        start = min(cells)
        cells.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in cells:
                    cells.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(frozenset(component))
    return sorted(result, key=min)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _marker_counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(cell for row in grid for cell in row if cell not in (0, 1, 3))


def observe(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    templates = _components(grid, 1)
    if len(templates) != 1:
        raise ValueError(f"expected exactly one color-1 template, found {len(templates)}")
    target = _normalize(templates[0])
    greens = _components(grid, 3)
    matches = [component for component in greens if _normalize(component) == target]
    distractors = [component for component in greens if _normalize(component) != target]
    if len(matches) < 2:
        raise ValueError("parametric grammar requires at least two exact matches")
    if not distractors:
        raise ValueError("parametric grammar requires at least one distractor")
    counts = _marker_counts(grid)
    if len(counts) < 2:
        raise ValueError("parametric grammar requires at least two marker colors")
    majority = max(counts, key=lambda color: (counts[color], color))
    if sum(count == counts[majority] for count in counts.values()) != 1:
        raise ValueError("marker majority must be strict")
    if any(count != 1 for color, count in counts.items() if color != majority):
        raise ValueError("non-majority marker colors must occur once")
    boundary = sum(
        cell in (1, 3) and (r in (0, len(grid) - 1) or c in (0, len(grid[0]) - 1))
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
    )
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "template": target,
        "template_cells": templates[0],
        "matches": matches,
        "distractors": distractors,
        "matching_components": len(matches),
        "distractor_components": len(distractors),
        "marker_counts": dict(counts),
        "majority_color": majority,
        "colored_cells": sum(cell != 0 for row in grid for cell in row),
        "boundary_contacts": boundary,
    }


def _blank(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def _paint(out: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for r, c in cells:
        out[r][c] = color


def _stage_a(grid: list[list[int]], selector: str = "exact") -> list[list[int]]:
    info = observe(grid)
    greens = info["matches"] + info["distractors"]
    if selector == "exact":
        chosen = info["matches"]
    elif selector == "all_green":
        chosen = greens
    elif selector == "same_size":
        size = len(info["template"])
        chosen = [component for component in greens if len(component) == size]
    elif selector == "first_match":
        chosen = info["matches"][:1]
    elif selector == "last_match":
        chosen = info["matches"][-1:]
    else:
        raise ValueError(f"unknown Stage-A selector: {selector}")
    out = _blank(grid)
    for component in chosen:
        _paint(out, component, info["majority_color"])
    return out


def _closest_pair(
    first: frozenset[tuple[int, int]], second: frozenset[tuple[int, int]]
) -> tuple[tuple[int, int], tuple[int, int]]:
    _, left, right = min(
        (abs(a[0] - b[0]) + abs(a[1] - b[1]), a, b)
        for a in first
        for b in second
    )
    return left, right


def _bridge_cells(
    first: tuple[int, int], second: tuple[int, int], *, orientation: str
) -> set[tuple[int, int]]:
    r1, c1 = first
    r2, c2 = second
    if orientation == "horizontal_first":
        horizontal = {(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
        vertical = {(r, c2) for r in range(min(r1, r2), max(r1, r2) + 1)}
    elif orientation == "vertical_first":
        vertical = {(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)}
        horizontal = {(r2, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
    else:
        raise ValueError(f"unknown bridge orientation: {orientation}")
    return horizontal | vertical


def _connect_stage(stage: list[list[int]], *, orientation: str = "horizontal_first") -> list[list[int]]:
    out = [row[:] for row in stage]
    parts = _components(stage)
    if len(parts) < 2:
        return out
    color = next(cell for row in stage for cell in row if cell != 0)
    for first, second in zip(parts, parts[1:]):
        left, right = _closest_pair(first, second)
        _paint(out, _bridge_cells(left, right, orientation=orientation), color)
    return out


def _bbox_bridge(stage: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in stage]
    parts = _components(stage)
    if len(parts) < 2:
        return out
    color = next(cell for row in stage for cell in row if cell != 0)
    for first, second in zip(parts, parts[1:]):
        cells = first | second
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        _paint(out, ((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)), color)
    return out


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    grid = _grid(value)
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis: {hypothesis!r}")
    if hypothesis == "canonical":
        return _stage_a(grid, "exact")
    if hypothesis == "bridge_matches":
        return _connect_stage(_stage_a(grid, "exact"), orientation="horizontal_first")
    if hypothesis == "all_green_bridge":
        return _connect_stage(_stage_a(grid, "all_green"), orientation="horizontal_first")
    if hypothesis == "same_size_bridge":
        return _connect_stage(_stage_a(grid, "same_size"), orientation="horizontal_first")
    if hypothesis == "vertical_first_bridge":
        return _connect_stage(_stage_a(grid, "exact"), orientation="vertical_first")
    if hypothesis == "first_match_only":
        return _stage_a(grid, "first_match")
    if hypothesis == "last_match_only":
        return _stage_a(grid, "last_match")
    return _bbox_bridge(_stage_a(grid, "exact"))


def _anchors(height: int, width: int) -> list[tuple[int, int]]:
    rows = list(range(0, height - 4, 5))
    cols = list(range(0, width - 2, 5))
    result = [(r, c) for r in rows for c in cols]
    if len(result) < 4:
        raise ValueError("profile has insufficient object slots")
    return result


def _paint_shape(
    grid: list[list[int]], shape: tuple[tuple[int, int], ...], anchor: tuple[int, int], color: int
) -> None:
    top, left = anchor
    for dr, dc in shape:
        r, c = top + dr, left + dc
        if not (0 <= r < len(grid) - 2 and 0 <= c < len(grid[0])):
            raise RuntimeError("shape escaped constructive slot")
        if grid[r][c] != 0:
            raise RuntimeError("constructive object overlap")
        grid[r][c] = color


def _choose_roles(
    rng: random.Random, slots: list[tuple[int, int]], n_matches: int, n_distractors: int
) -> tuple[tuple[int, int], list[tuple[int, int]], list[tuple[int, int]]]:
    template = slots[0]
    available = slots[1:]
    needed = n_matches + n_distractors
    if needed > len(available):
        raise ValueError("profile requests more objects than slots")
    for _ in range(256):
        order = available[:]
        rng.shuffle(order)
        matches = order[:n_matches]
        ordered = sorted(matches)
        if any(a[0] != b[0] and a[1] != b[1] for a, b in zip(ordered, ordered[1:])):
            return template, matches, order[n_matches:needed]
    raise RuntimeError("could not place a two-axis match chain")


def _profile(index: int, *, query: bool) -> tuple[int, int, str, int, int]:
    table = QUERY_PROFILES if query else TRAIN_PROFILES
    if not 0 <= index < len(table):
        raise ValueError("profile index out of range")
    return table[index]


def _scene(seed: int, index: int, *, query: bool) -> list[list[int]]:
    height, width, shape_name, n_matches, n_distractors = _profile(index, query=query)
    rng = random.Random((seed + 1) * 1_000_003 + (index + (10_000 if query else 0)) * 97_409)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    template_slot, match_slots, distractor_slots = _choose_roles(
        rng, _anchors(height, width), n_matches, n_distractors
    )
    shape = SHAPES[shape_name]
    distractor = DISTRACTORS[shape_name]
    _paint_shape(grid, shape, template_slot, 1)
    for anchor in match_slots:
        _paint_shape(grid, shape, anchor, 3)
    for anchor in distractor_slots:
        _paint_shape(grid, distractor, anchor, 3)

    majority = MARKER_COLORS[(seed + index + (3 if query else 0)) % len(MARKER_COLORS)]
    majority_count = 3 if (seed + index) % 3 == 0 else 2
    others = [color for color in MARKER_COLORS if color != majority]
    rng.shuffle(others)
    marker_plan = [majority] * majority_count + others[: 2 if index % 2 else 1]
    columns = list(range(0, width, 3))
    rng.shuffle(columns)
    rng.shuffle(marker_plan)
    for color, col in zip(marker_plan, columns):
        grid[height - 1][col] = color

    info = observe(grid)
    if info["matching_components"] != n_matches or info["distractor_components"] != n_distractors:
        raise RuntimeError("constructive profile changed object counts")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    finish = _finish(settings)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    train = []
    for index in range(demos):
        grid = _scene(seed, index, query=False)
        train.append({"input": grid, "output": predict(grid, finish)})
    test = []
    for index in range(queries):
        grid = _scene(seed, index, query=True)
        test.append({"input": grid, "output": predict(grid, finish)})
    return {"train": train, "test": test, "program_solution": program(settings)}


def teaching_certificate(train: Any, query_inputs: Any) -> dict[str, Any]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("train must contain 2..6 demonstrations")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("query_inputs must contain 1..4 grids")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration must contain only input and output")
        observe(pair["input"])
        _grid(pair["output"])
    for grid in query_inputs:
        observe(grid)
    survivors = [
        name
        for name in HYPOTHESES
        if all(predict(pair["input"], name) == pair["output"] for pair in train)
    ]
    intended = [name for name in FINISHES if name in survivors]
    target = intended[0] if len(intended) == 1 else None
    harmful = []
    if target is not None:
        harmful = [
            name
            for name in survivors
            if name != target and any(predict(grid, name) != predict(grid, target) for grid in query_inputs)
        ]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "harmful_query_survivors": harmful,
        "demos": len(train),
        "queries": len(query_inputs),
        "scope": "Finite declared rival bank only; not a proof of unique induction.",
    }


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    try:
        from reviewer_support import public_challenge_bytes

        return public_challenge_bytes(
            {"train": episode["train"], "test": [episode["test"][query_index]]}
        )
    except ImportError:
        public = {
            "train": episode["train"],
            "test": [{"input": episode["test"][query_index]["input"]}],
        }
        return json.dumps(public, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def causal_witness(seed: int = 0) -> dict[str, Any]:
    episode = generate(seed, {"finish": "bridge_matches"}, demos=2, queries=4)
    grid = episode["test"][0]["input"]
    stage_a = _stage_a(grid, "exact")
    wrong_stage_a = _stage_a(grid, "all_green")
    final = _connect_stage(stage_a, orientation="horizontal_first")
    wrong_final = _connect_stage(wrong_stage_a, orientation="horizontal_first")
    changed = sum(
        a != b
        for row_a, row_b in zip(final, wrong_final)
        for a, b in zip(row_a, row_b)
    )
    return {
        "schema": "arcpuzzles-parametric-sequential-witness-v1",
        "task_id": TASK_ID,
        "setting": {"finish": "bridge_matches"},
        "seed": seed,
        "step_a": "select exact color-3 template matches and recolor them with the majority marker color",
        "intermediate": "blank same-size grid containing only the Stage-A selected components",
        "step_b": "connect the Stage-A components in reading order with deterministic horizontal-then-vertical bridges",
        "why_b_depends_on_a": (
            "Stage B discovers its component chain from the Stage-A output; replacing that "
            "intermediate with all green components changes both endpoints and the final grid."
        ),
        "input": grid,
        "stage_a_output": stage_a,
        "wrong_stage_a_output": wrong_stage_a,
        "final_output": final,
        "wrong_final_output": wrong_final,
        "changed_cells": changed,
        "bridge_program_sha256": hashlib.sha256(program({"finish": "bridge_matches"}).encode()).hexdigest(),
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
    }
