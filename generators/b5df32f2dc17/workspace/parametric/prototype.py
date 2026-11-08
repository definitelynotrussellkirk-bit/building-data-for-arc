"""Source-bound row-run ordering family for ARC task b5df32f2dc17.

Both settings extract every nonzero horizontal run independently per row and
left-repack all runs with a one-cell gap.  The canonical setting sorts by
descending run length; the alternative sorts by ascending length.  Original
start position is the tie breaker in both settings.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from reviewer_support import public_challenge_bytes

TASK_ID = "b5df32f2dc17"
VERSION = "row-run-length-order-v1"
LENGTH_ORDERS = ("descending", "ascending")
DEFAULT_LENGTH_ORDER = "descending"
HERE = Path(__file__).resolve().parent


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"length_order"}:
        raise ValueError("settings must contain exactly length_order")
    value = settings["length_order"]
    if type(value) is not str or value not in LENGTH_ORDERS:
        raise ValueError("length_order must be descending or ascending")
    return value


def _count(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _seed(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    return value


def program_for(length_order: str) -> str:
    if length_order not in LENGTH_ORDERS:
        raise ValueError(f"unsupported length_order: {length_order!r}")
    filename = "canonical.rkt" if length_order == "descending" else "ascending.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def program(settings: Any) -> str:
    return program_for(validate_settings(settings))


def _strict_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return deepcopy(grid)


def _row_runs(row: list[int]) -> list[dict[str, int]]:
    runs = []
    col = 0
    while col < len(row):
        color = row[col]
        if color == 0:
            col += 1
            continue
        end = col
        while end + 1 < len(row) and row[end + 1] == color:
            end += 1
        runs.append({"start": col, "end": end, "length": end - col + 1, "color": color})
        col = end + 1
    return runs


def _row_role(runs: list[dict[str, int]]) -> str:
    if not runs:
        return "blank"
    if len(runs) == 1:
        return "single"
    lengths = [run["length"] for run in runs]
    if len(set(lengths)) < len(lengths):
        return "tie"
    if lengths == sorted(lengths, reverse=True):
        return "already_descending"
    if lengths == sorted(lengths):
        return "already_ascending"
    return "needs_reorder"


def analyze(grid: Any) -> dict[str, Any]:
    source = _strict_grid(grid)
    rows = []
    roles = set()
    for index, row in enumerate(source):
        runs = _row_runs(row)
        role = _row_role(runs)
        roles.add(role)
        rows.append({"row": index, "runs": runs, "role": role})
    return {"height": len(source), "width": len(source[0]), "rows": rows, "row_roles": roles}


def _sort_runs(runs: list[dict[str, int]], policy: str) -> list[dict[str, int]]:
    if policy == "descending":
        return sorted(runs, key=lambda run: (-run["length"], run["start"]))
    if policy == "ascending":
        return sorted(runs, key=lambda run: (run["length"], run["start"]))
    if policy == "keep_input_order":
        return sorted(runs, key=lambda run: run["start"])
    if policy == "reverse_input_order":
        return sorted(runs, key=lambda run: -run["start"])
    if policy == "color_ascending":
        return sorted(runs, key=lambda run: (run["color"], run["start"]))
    if policy == "color_descending":
        return sorted(runs, key=lambda run: (-run["color"], run["start"]))
    if policy == "descending_reverse_ties":
        return sorted(runs, key=lambda run: (-run["length"], -run["start"]))
    if policy == "ascending_reverse_ties":
        return sorted(runs, key=lambda run: (run["length"], -run["start"]))
    if policy == "longest_only":
        maximum = max((run["length"] for run in runs), default=0)
        return [run for run in runs if run["length"] == maximum]
    if policy == "shortest_only":
        minimum = min((run["length"] for run in runs), default=0)
        return [run for run in runs if run["length"] == minimum]
    raise ValueError(f"unknown run policy: {policy}")


def _repack(width: int, runs: list[dict[str, int]]) -> list[int]:
    row = [0] * width
    cursor = 0
    for index, run in enumerate(runs):
        for offset in range(run["length"]):
            if cursor + offset < width:
                row[cursor + offset] = run["color"]
        cursor += run["length"] + (0 if index == len(runs) - 1 else 1)
    return row


def _keep_positions(width: int, original: list[dict[str, int]], ordered: list[dict[str, int]]) -> list[int]:
    row = [0] * width
    starts = [run["start"] for run in sorted(original, key=lambda run: run["start"])]
    for start, run in zip(starts, ordered, strict=True):
        for offset in range(run["length"]):
            if start + offset < width:
                row[start + offset] = run["color"]
    return row


def _solve_row(source: list[int], policy: str) -> list[int]:
    runs = _row_runs(source)
    width = len(source)
    if policy == "descending_keep_positions":
        return _keep_positions(width, runs, _sort_runs(runs, "descending"))
    if policy == "ascending_keep_positions":
        return _keep_positions(width, runs, _sort_runs(runs, "ascending"))
    if policy == "descending_multi_run_only":
        return source[:] if len(runs) <= 1 else _repack(width, _sort_runs(runs, "descending"))
    if policy == "ascending_multi_run_only":
        return source[:] if len(runs) <= 1 else _repack(width, _sort_runs(runs, "ascending"))
    if policy == "descending_leave_ordered":
        lengths = [run["length"] for run in runs]
        return source[:] if lengths == sorted(lengths, reverse=True) else _repack(width, _sort_runs(runs, "descending"))
    if policy == "ascending_leave_ordered":
        lengths = [run["length"] for run in runs]
        return source[:] if lengths == sorted(lengths) else _repack(width, _sort_runs(runs, "ascending"))
    return _repack(width, _sort_runs(runs, policy))


RIVAL_POLICIES = (
    "keep_input_order",
    "reverse_input_order",
    "color_ascending",
    "color_descending",
    "descending_keep_positions",
    "ascending_keep_positions",
    "descending_multi_run_only",
    "ascending_multi_run_only",
    "descending_leave_ordered",
    "ascending_leave_ordered",
    "longest_only",
    "shortest_only",
    "descending_reverse_ties",
    "ascending_reverse_ties",
)


def solve_python(grid: Any, policy: str) -> list[list[int]]:
    if policy not in LENGTH_ORDERS and policy not in RIVAL_POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    source = _strict_grid(grid)
    return [_solve_row(row, policy) for row in source]


DEMO_SIZES = ((8, 14), (10, 16), (12, 18), (14, 20), (16, 24), (20, 26))
QUERY_SIZES = ((9, 15), (15, 21), (24, 28), (30, 30))
ROLE_CYCLE = ("needs_reorder", "already_descending", "already_ascending", "single", "tie", "blank")
ORDINARY_LENGTHS = {
    "needs_reorder": (2, 5, 3),
    "already_descending": (5, 3, 2),
    "already_ascending": (2, 3, 5),
    "single": (4,),
    "tie": (3, 2, 3),
    "blank": (),
}
STRESS_LENGTHS = {
    "needs_reorder": (3, 8, 5, 2),
    "already_descending": (8, 5, 3, 2),
    "already_ascending": (2, 3, 5, 8),
    "single": (14,),
    "tie": (6, 3, 6),
    "blank": (),
}
BASE_COLORS = {
    "needs_reorder": (2, 8, 5, 1),
    "already_descending": (9, 3, 7, 4),
    "already_ascending": (6, 1, 8, 2),
    "single": (4,),
    "tie": (7, 2, 6),
    "blank": (),
}


def _rng(seed: int, role: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}/{VERSION}/{seed}/{role}/{index}/{attempt}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _render_row(width: int, lengths: tuple[int, ...], colors: tuple[int, ...],
                *, offset: int, gaps: tuple[int, ...]) -> list[int]:
    if len(lengths) != len(colors) or len(gaps) != max(0, len(lengths) - 1):
        raise ValueError("row specification mismatch")
    occupied = sum(lengths) + sum(gaps)
    if not 0 <= offset <= width - occupied:
        raise ValueError("row does not fit")
    row = [0] * width
    cursor = offset
    for index, (length, color) in enumerate(zip(lengths, colors, strict=True)):
        for col in range(cursor, cursor + length):
            row[col] = color
        cursor += length
        if index < len(gaps):
            cursor += gaps[index]
    return row


def _scene(seed: int, role: str, index: int, attempt: int) -> list[list[int]]:
    sizes = DEMO_SIZES if role == "demo" else QUERY_SIZES
    height, width = sizes[index]
    stress = role == "query" and index == 3
    lengths_by_role = STRESS_LENGTHS if stress else ORDINARY_LENGTHS
    rng = _rng(seed, role, index, attempt)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    color_map = {source: palette[source - 1] for source in range(1, 10)}
    grid = []
    for row_index in range(height):
        row_role = ROLE_CYCLE[row_index % len(ROLE_CYCLE)]
        if row_index == height - 1 and row_role == "blank":
            row_role = "needs_reorder"
        lengths = lengths_by_role[row_role]
        base_colors = BASE_COLORS[row_role][:len(lengths)]
        colors = tuple(color_map[color] for color in base_colors)
        gaps = tuple(1 for _ in range(max(0, len(lengths) - 1)))
        occupied = sum(lengths) + sum(gaps)
        if not lengths:
            grid.append([0] * width)
            continue
        if row_index == 0:
            offset = 0
        elif row_index == height - 1:
            offset = width - occupied
        elif row_role in {"already_descending", "already_ascending", "single"}:
            offset = min(max(1, (row_index + attempt) % 4 + 1), width - occupied)
        elif row_index % 5 == 2:
            offset = width - occupied
        else:
            offset = rng.randrange(width - occupied + 1)
        grid.append(_render_row(width, lengths, colors, offset=offset, gaps=gaps))
    info = analyze(grid)
    required = {"blank", "single", "already_ascending", "already_descending", "needs_reorder", "tie"}
    if not info["row_roles"] >= required:
        raise RuntimeError("scene lost required row roles")
    if solve_python(grid, "descending") == solve_python(grid, "ascending"):
        raise RuntimeError("settings failed to separate")
    return grid


def _candidate_policies(length_order: str) -> tuple[str, ...]:
    other = "ascending" if length_order == "descending" else "descending"
    return (other, *RIVAL_POLICIES)


def teaching_check(episode: dict[str, Any], length_order: str) -> dict[str, Any]:
    if length_order not in LENGTH_ORDERS:
        raise ValueError("unknown length order")
    rows = []
    for policy in _candidate_policies(length_order):
        demo_differences = [
            index for index, pair in enumerate(episode["train"])
            if solve_python(pair["input"], policy) != pair["output"]
        ]
        query_differences = []
        if not demo_differences:
            query_differences = [
                index for index, pair in enumerate(episode["test"])
                if solve_python(pair["input"], policy) != pair["output"]
            ]
        rows.append({
            "policy": policy,
            "demo_differences": demo_differences,
            "demo_survives": not demo_differences,
            "query_differences": query_differences,
            "harmful": not demo_differences and bool(query_differences),
        })
    other = "ascending" if length_order == "descending" else "descending"
    return {
        "length_order": length_order,
        "rival_count": len(rows),
        "rivals": rows,
        "settings_disagree_on_demos": any(
            solve_python(pair["input"], other) != pair["output"] for pair in episode["train"]
        ),
        "demo_survivors": [row["policy"] for row in rows if row["demo_survives"]],
        "harmful_survivors": [row["policy"] for row in rows if row["harmful"]],
    }


def _minimal_episode(demos: list[list[list[int]]], queries: list[list[list[int]]], order: str) -> dict[str, Any]:
    return {
        "train": [{"input": grid, "output": solve_python(grid, order)} for grid in demos[:2]],
        "test": [{"input": grid, "output": solve_python(grid, order)} for grid in queries],
    }


@lru_cache(maxsize=256)
def _frozen_episode_inputs(seed: int) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    for attempt in range(64):
        demos = [_scene(seed, "demo", index, attempt) for index in range(6)]
        queries = [_scene(seed, "query", index, attempt) for index in range(4)]
        if not all(solve_python(grid, "descending") != solve_python(grid, "ascending") for grid in queries):
            continue
        reviews = [teaching_check(_minimal_episode(demos, queries, order), order)
                   for order in LENGTH_ORDERS]
        if all(not review["demo_survivors"] and not review["harmful_survivors"] for review in reviews):
            return (tuple(json.dumps(grid, separators=(",", ":")) for grid in demos),
                    tuple(json.dumps(grid, separators=(",", ":")) for grid in queries), attempt)
    raise RuntimeError("could not construct a two-demo identifiable episode")


def _episode_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]], int]:
    demos, queries, attempt = _frozen_episode_inputs(seed)
    return ([json.loads(value) for value in demos], [json.loads(value) for value in queries], attempt)


def generate_episode(seed: int, *, length_order: str, demos: int = 3,
                     queries: int = 4) -> dict[str, Any]:
    _seed(seed)
    if length_order not in LENGTH_ORDERS:
        raise ValueError("unsupported length_order")
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    demo_inputs, query_inputs, attempt = _episode_inputs(seed)
    episode = {
        "train": [{"input": grid, "output": solve_python(grid, length_order)}
                  for grid in demo_inputs[:demos]],
        "test": [{"input": grid, "output": solve_python(grid, length_order)}
                 for grid in query_inputs[:queries]],
        "program_solution": program_for(length_order),
        "settings": {"length_order": length_order},
        "seed": seed,
        "construction_attempt": attempt,
    }
    review = teaching_check(episode, length_order)
    if review["demo_survivors"] or review["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {review}")
    return episode


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    order = validate_settings(settings)
    episode = generate_episode(seed, length_order=order, demos=demos, queries=queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index outside retained test range")
    value = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(value))


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return public_challenge_bytes(public_view(episode, query_index))


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def derived_run_table(grid: Any) -> list[dict[str, Any]]:
    """Compact A-stage intermediate retained for the causal witness."""
    info = analyze(grid)
    return [
        {"row": row["row"], "role": row["role"],
         "runs": [dict(run) for run in row["runs"]]}
        for row in info["rows"]
    ]
