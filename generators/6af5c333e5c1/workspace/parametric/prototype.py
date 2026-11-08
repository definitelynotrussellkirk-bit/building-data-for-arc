"""Matched-input parametric family for horizontal endpoint completion.

``all_pairs`` is the exact canonical rule. ``top_span_threshold`` first finds
A: the topmost row containing exactly two blue endpoints, produces the
input-dependent endpoint span as an intermediate, then B fills only exact-pair
rows whose span is at least that threshold. Singleton and three-endpoint rows
remain distractors under both settings.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "6af5c333e5c1"
PARAMETER = "fill_policy"
MODES = ("all_pairs", "top_span_threshold")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "all_pairs": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "top_span_threshold": (_DIR / "top_span_threshold.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((9, 12), (11, 15), (13, 18), (16, 22), (20, 26), (24, 30))
_QUERY_DIMS = ((8, 11), (14, 18), (22, 26), (30, 30))


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly fill_policy")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"fill_policy must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or value not in (0, 1) for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0 or 1")
    return grid


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    row_cells = [[c for c, value in enumerate(row) if value == 1] for row in grid]
    pair_rows = [
        {"row": r, "left": cells[0], "right": cells[1], "span": cells[1] - cells[0]}
        for r, cells in enumerate(row_cells)
        if len(cells) == 2
    ]
    singletons = [r for r, cells in enumerate(row_cells) if len(cells) == 1]
    triples = [r for r, cells in enumerate(row_cells) if len(cells) == 3]
    if not pair_rows:
        raise ValueError("scene requires at least one exact-pair row")
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "row_cells": row_cells,
        "pair_rows": pair_rows,
        "singleton_rows": singletons,
        "triple_rows": triples,
        "top_pair_row": pair_rows[0]["row"],
        "bottom_pair_row": pair_rows[-1]["row"],
        "threshold": pair_rows[0]["span"],
        "top_threshold": pair_rows[0]["span"],
        "bottom_threshold": pair_rows[-1]["span"],
    }


def validate_input(grid: Any) -> list[str]:
    try:
        facts = scene_facts(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if len(facts["pair_rows"]) < 4:
        errors.append("need at least four exact-pair rows")
    if not facts["singleton_rows"]:
        errors.append("need a singleton distractor row")
    if not facts["triple_rows"]:
        errors.append("need a three-endpoint distractor row")
    if facts["top_pair_row"] == 0:
        errors.append("top exact-pair row must follow a distractor")
    spans = [item["span"] for item in facts["pair_rows"]]
    if not min(spans) < facts["threshold"] < max(spans):
        errors.append("top-row span must be a strict interior threshold")
    if facts["top_threshold"] == facts["bottom_threshold"]:
        errors.append("bottom exact-pair row must provide a distinct counterfactual threshold")
    try:
        if solve(grid, {PARAMETER: "all_pairs"}) == solve(
            grid, {PARAMETER: "top_span_threshold"}
        ):
            errors.append("declared settings must change the output")
    except ValueError as exc:  # pragma: no cover - guarded by facts
        errors.append(str(exc))
    return errors


def _fill_pair_rows(grid: list[list[int]], predicate: Callable[[int, int], bool]) -> list[list[int]]:
    facts = scene_facts(grid)
    output = [row[:] for row in grid]
    for item in facts["pair_rows"]:
        if predicate(item["span"], item["row"]):
            for col in range(item["left"], item["right"] + 1):
                output[item["row"]][col] = 1
    return output


def solve_with_threshold(grid: list[list[int]], threshold: int) -> list[list[int]]:
    _integer("threshold", threshold, 1, 29)
    return _fill_pair_rows(grid, lambda span, _row: span >= threshold)


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    facts = scene_facts(grid)
    if mode == "all_pairs":
        return _fill_pair_rows(grid, lambda _span, _row: True)
    return solve_with_threshold(grid, facts["threshold"])


def intermediate(grid: list[list[int]]) -> dict[str, Any]:
    facts = scene_facts(grid)
    return {
        "top_pair_row": facts["top_pair_row"],
        "top_threshold": facts["top_threshold"],
        "bottom_pair_row": facts["bottom_pair_row"],
        "bottom_threshold": facts["bottom_threshold"],
        "pair_spans": [item["span"] for item in facts["pair_rows"]],
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _spans(width: int, count: int, rng: random.Random) -> list[int]:
    threshold = max(4, min(width - 4, width // 2))
    small = max(2, threshold - 3)
    medium_small = max(2, threshold - 1)
    large = min(width - 1, threshold + 3)
    larger = min(width - 1, threshold + 5)
    values = [threshold, small, large, medium_small, larger]
    while len(values) < count:
        delta = rng.choice((-4, -2, 1, 2, 4, 6))
        values.append(max(2, min(width - 1, threshold + delta)))
    values = values[:count]
    values[-1] = large
    if max(values) <= threshold:
        values[2 if count > 2 else 1] = large
    return values


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    if not 0 <= index < len(dims):
        raise ValueError(f"unsupported {split} index {index}")
    height, width = dims[index]
    rng = _rng(seed, split, index)
    grid = [[0] * width for _ in range(height)]

    # Rows 0 and 1 deliberately precede the first qualifying pair.
    grid[0][rng.randrange(width)] = 1
    triple = sorted(rng.sample(range(width), 3))
    for col in triple:
        grid[1][col] = 1

    pair_count = min(height - 2, max(4, 4 + height // 4))
    available = list(range(2, height))
    if pair_count == len(available):
        pair_rows = available
    else:
        # Cover top, middle and bottom of the canvas while retaining row order.
        pair_rows = sorted({
            round(2 + i * (height - 3) / (pair_count - 1))
            for i in range(pair_count)
        })
        for row in available:
            if len(pair_rows) >= pair_count:
                break
            if row not in pair_rows:
                pair_rows.append(row)
        pair_rows = sorted(pair_rows[:pair_count])

    spans = _spans(width, len(pair_rows), rng)
    for row, span in zip(pair_rows, spans):
        left = rng.randrange(0, width - span)
        right = left + span
        grid[row][left] = 1
        grid[row][right] = 1

    errors = validate_input(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train = []
    test = []
    seen: set[bytes] = set()
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _scene(seed, split, index)
            key = json.dumps(grid, separators=(",", ":")).encode()
            if key in seen:
                raise AssertionError("deterministic schedule emitted a duplicate input")
            seen.add(key)
            target.append({"input": grid, "output": solve(grid, {PARAMETER: mode})})
    return {"train": train, "test": test, "program_solution": program({PARAMETER: mode})}


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def _bottom_threshold(grid: list[list[int]]) -> list[list[int]]:
    facts = scene_facts(grid)
    return solve_with_threshold(grid, facts["bottom_threshold"])


def _longest_only(grid: list[list[int]]) -> list[list[int]]:
    facts = scene_facts(grid)
    return solve_with_threshold(grid, max(item["span"] for item in facts["pair_rows"]))


def _short_or_equal(grid: list[list[int]]) -> list[list[int]]:
    facts = scene_facts(grid)
    threshold = facts["threshold"]
    return _fill_pair_rows(grid, lambda span, _row: span <= threshold)


def _top_row_only(grid: list[list[int]]) -> list[list[int]]:
    facts = scene_facts(grid)
    top = facts["top_pair_row"]
    return _fill_pair_rows(grid, lambda _span, row: row == top)


def _two_or_more(grid: list[list[int]]) -> list[list[int]]:
    facts = scene_facts(grid)
    out = [row[:] for row in grid]
    for row, cells in enumerate(facts["row_cells"]):
        if len(cells) >= 2:
            for col in range(cells[0], cells[-1] + 1):
                out[row][col] = 1
    return out


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "all_pairs": lambda grid: solve(grid, {PARAMETER: "all_pairs"}),
    "top_span_threshold": lambda grid: solve(grid, {PARAMETER: "top_span_threshold"}),
    "bottom_span_threshold": _bottom_threshold,
    "longest_only": _longest_only,
    "short_or_equal": _short_or_equal,
    "top_row_only": _top_row_only,
    "fill_two_or_more": _two_or_more,
}


def audit_episode(seed: int, mode: str, *, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    survivors: list[str] = []
    harmful: list[str] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "rivals": sorted(RIVALS),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
        "intermediate": intermediate(episode["test"][0]["input"]),
    }
