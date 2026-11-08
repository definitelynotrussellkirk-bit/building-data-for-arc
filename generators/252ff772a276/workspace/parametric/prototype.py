"""Native matched-input parametric family for ARC task ``252ff772a276``.

``all_interior`` is the exact canonical rule. ``winner_seed_rows`` keeps the
canonical frame ranking, then uses the selected frame's input-derived set of
seed-bearing interior rows as a mask for the green fill.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "252ff772a276"
HERE = Path(__file__).resolve().parent
SETTINGS = ("all_interior", "winner_seed_rows")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

RIVALS = (
    "all_interior",
    "winner_seed_rows",
    "winner_seed_columns",
    "top_seed_row",
    "bottom_seed_row",
    "runner_up_seed_rows",
    "first_n_rows",
    "seed_rows_plus_neighbors",
    "all_except_seed_rows",
    "identity",
)

# Each profile is canvas height/width, three non-overlapping frame boxes
# (top, left, height, width), and seed counts. Fixed geometry makes all count
# boundaries constructive; seed columns vary with the seed.
_DEMO_PROFILES = (
    (11, 15, ((0, 0, 6, 7), (0, 9, 5, 6), (7, 4, 4, 8)), (5, 3, 2)),
    (13, 18, ((0, 1, 6, 7), (0, 10, 7, 8), (8, 4, 5, 9)), (3, 5, 2)),
    (15, 21, ((1, 0, 7, 8), (0, 11, 6, 10), (9, 5, 6, 10)), (4, 4, 2)),
    (17, 23, ((0, 1, 8, 8), (1, 12, 7, 11), (10, 6, 7, 11)), (2, 3, 5)),
    (19, 25, ((1, 0, 9, 9), (0, 13, 8, 12), (11, 7, 8, 12)), (5, 5, 3)),
    (21, 28, ((0, 2, 10, 10), (1, 16, 9, 12), (12, 7, 9, 14)), (4, 2, 6)),
)
_QUERY_PROFILES = (
    (10, 14, ((0, 0, 5, 6), (0, 8, 5, 6), (6, 3, 4, 8)), (3, 4, 2)),
    (16, 20, ((0, 1, 7, 8), (0, 11, 8, 9), (9, 5, 7, 10)), (5, 3, 4)),
    (24, 27, ((0, 0, 11, 11), (1, 16, 10, 11), (14, 7, 10, 13)), (4, 6, 3)),
    (30, 30, ((0, 0, 14, 12), (0, 17, 13, 13), (18, 6, 12, 18)), (5, 4, 7)),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _scope(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"fill_scope"}:
        raise ValueError("settings must contain only fill_scope")
    value = settings["fill_scope"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("fill_scope must be all_interior or winner_seed_rows")
    return value


def program(settings: Any) -> str:
    scope = _scope(settings)
    name = "canonical.rkt" if scope == "all_interior" else "winner_seed_rows.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _validate_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 1, 2) for cell in row)
        for row in value
    ):
        raise ValueError("input must be rectangular with exact colors 0, 1, or 2")
    return value


def _neighbors(row: int, col: int, height: int, width: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = {(row, col)}
            while pending:
                rr, cc = pending.pop()
                for point in _neighbors(rr, cc, height, width):
                    if point not in seen and grid[point[0]][point[1]] == color:
                        seen.add(point)
                        cells.add(point)
                        pending.append(point)
            result.append(cells)
    return result


def _frame(grid: list[list[int]], cells: set[tuple[int, int]]) -> dict[str, Any] | None:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 3 or width < 3:
        return None
    border = {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if row in (r1, r2) or col in (c1, c2)
    }
    if cells != border:
        return None
    seeds = sorted(
        (row, col)
        for row in range(r1 + 1, r2)
        for col in range(c1 + 1, c2)
        if grid[row][col] == 2
    )
    return {
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "height": height,
        "width": width,
        "seeds": seeds,
        "seed_count": len(seeds),
        "seed_rows": sorted({row - r1 for row, _ in seeds}),
        "seed_columns": sorted({col - c1 for _, col in seeds}),
        "interior_area": (height - 2) * (width - 2),
    }


def analyze(value: Any) -> dict[str, Any]:
    grid = _validate_grid(value)
    frames = []
    for cells in _components(grid, 1):
        frame = _frame(grid, cells)
        if frame is None:
            raise ValueError("every color-1 component must be a complete rectangular frame")
        frames.append(frame)
    frames.sort(key=lambda row: (row["r1"], row["c1"]))
    if len(frames) != 3:
        raise ValueError("parametric grammar requires exactly three frames")
    claimed = set()
    for frame in frames:
        if frame["seed_count"] < 1:
            raise ValueError("every frame requires at least one interior seed")
        claimed.update(
            (row, col)
            for row in range(frame["r1"], frame["r2"] + 1)
            for col in range(frame["c1"], frame["c2"] + 1)
            if row in (frame["r1"], frame["r2"]) or col in (frame["c1"], frame["c2"])
        )
        claimed.update(frame["seeds"])
    nonzero = {
        (row, col)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color != 0
    }
    if claimed != nonzero:
        raise ValueError("stray or overlapping nonzero cells are not allowed")
    ranked = sorted(frames, key=lambda row: (-row["seed_count"], row["r1"], row["c1"]))
    winner, runner = ranked[:2]
    touches = any(
        frame["r1"] == 0
        or frame["c1"] == 0
        or frame["r2"] == len(grid) - 1
        or frame["c2"] == len(grid[0]) - 1
        for frame in frames
    )
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "frames": frames,
        "winner": winner,
        "runner_up": runner,
        "winner_seed_rows": winner["seed_rows"],
        "runner_up_seed_rows": runner["seed_rows"],
        "winner_interior_rows": winner["height"] - 2,
        "winner_interior_area": winner["interior_area"],
        "nonzero_count": len(nonzero),
        "touches_boundary": touches,
    }


def _row_mask(summary: dict[str, Any], hypothesis: str) -> set[int]:
    winner = summary["winner"]
    interior_rows = set(range(1, winner["height"] - 1))
    seed_rows = set(winner["seed_rows"])
    if hypothesis == "all_interior":
        return interior_rows
    if hypothesis == "winner_seed_rows":
        return seed_rows
    if hypothesis == "top_seed_row":
        return {min(seed_rows)}
    if hypothesis == "bottom_seed_row":
        return {max(seed_rows)}
    if hypothesis == "runner_up_seed_rows":
        return set(summary["runner_up"]["seed_rows"]) & interior_rows
    if hypothesis == "first_n_rows":
        return set(range(1, 1 + len(seed_rows))) & interior_rows
    if hypothesis == "seed_rows_plus_neighbors":
        return {row + delta for row in seed_rows for delta in (-1, 0, 1)} & interior_rows
    if hypothesis == "all_except_seed_rows":
        return interior_rows - seed_rows
    if hypothesis == "identity":
        return set()
    if hypothesis == "winner_seed_columns":
        return interior_rows
    raise ValueError("unknown hypothesis")


def apply_rule(value: Any, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in RIVALS:
        raise ValueError("unknown declared hypothesis")
    grid = _validate_grid(value)
    summary = analyze(grid)
    winner = summary["winner"]
    crop = [row[winner["c1"] : winner["c2"] + 1] for row in grid[winner["r1"] : winner["r2"] + 1]]
    out = deepcopy(crop)
    if hypothesis == "identity":
        return out
    rows = _row_mask(summary, hypothesis)
    columns = set(winner["seed_columns"])
    for row in range(1, len(out) - 1):
        for col in range(1, len(out[0]) - 1):
            active = col in columns if hypothesis == "winner_seed_columns" else row in rows
            if active and out[row][col] == 0:
                out[row][col] = 3
    return out


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError("grids must have equal dimensions")
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r1, c1, height, width = box
    r2, c2 = r1 + height - 1, c1 + width - 1
    for col in range(c1, c2 + 1):
        grid[r1][col] = 1
        grid[r2][col] = 1
    for row in range(r1, r2 + 1):
        grid[row][c1] = 1
        grid[row][c2] = 1


def _rank_indices(boxes: tuple[tuple[int, int, int, int], ...], counts: tuple[int, int, int]) -> list[int]:
    return sorted(range(3), key=lambda i: (-counts[i], boxes[i][0], boxes[i][1]))


def _active_rows(height: int, rank: int) -> list[int]:
    interior = height - 2
    if rank == 0:
        if interior >= 8:
            return [1, max(2, interior // 2), interior]
        return [1, interior]
    if rank == 1:
        if interior >= 5:
            return [2, interior - 1]
        return [2] if interior >= 3 else [1]
    return [max(1, (interior + 1) // 2)]


def _place_seeds(
    grid: list[list[int]],
    box: tuple[int, int, int, int],
    count: int,
    active_rows: list[int],
    rng: random.Random,
) -> None:
    r1, c1, height, width = box
    if count < len(active_rows):
        raise ValueError("seed count cannot cover required active rows")
    positions: list[tuple[int, int]] = []
    used = set()
    for offset, row in enumerate(active_rows):
        choices = list(range(1, width - 1))
        rng.shuffle(choices)
        col = choices[(offset + count) % len(choices)]
        point = (r1 + row, c1 + col)
        used.add(point)
        positions.append(point)
    remaining = [
        (r1 + row, c1 + col)
        for row in active_rows
        for col in range(1, width - 1)
        if (r1 + row, c1 + col) not in used
    ]
    rng.shuffle(remaining)
    positions.extend(remaining[: count - len(positions)])
    if len(positions) != count:
        raise ValueError("frame cannot hold requested seeds on active rows")
    for row, col in positions:
        grid[row][col] = 2


def _stream_seed(seed: int, split: str, index: int) -> int:
    raw = f"{TASK_ID}:v1:{seed}:{split}:{index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, boxes, counts = profiles[index]
    rng = random.Random(_stream_seed(seed, split, index))
    grid = _blank(height, width)
    ranking = _rank_indices(boxes, counts)
    rank_of = {frame_index: rank for rank, frame_index in enumerate(ranking)}
    for frame_index, box in enumerate(boxes):
        _draw_frame(grid, box)
        rows = _active_rows(box[2], rank_of[frame_index])
        _place_seeds(grid, box, counts[frame_index], rows, rng)
    summary = analyze(grid)
    if summary["winner_seed_rows"] == summary["runner_up_seed_rows"]:
        raise RuntimeError("construction failed to distinguish winner and runner row intermediates")
    if summary["winner_interior_rows"] <= len(summary["winner_seed_rows"]):
        raise RuntimeError("winner must retain at least one seedless interior row")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    scope = _scope(settings)
    demos = _exact_int(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _exact_int(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [{"input": grid, "output": apply_rule(grid, scope)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_rule(grid, scope)} for grid in test_inputs],
        "program_solution": program({"fill_scope": scope}),
    }


def audit_episode(episode: dict[str, Any], selected_setting: str) -> dict[str, Any]:
    if selected_setting not in SETTINGS:
        raise ValueError("selected setting is undeclared")
    survivors = []
    for hypothesis in RIVALS:
        if all(apply_rule(pair["input"], hypothesis) == pair["output"] for pair in episode["train"]):
            survivors.append(hypothesis)
    harmful = [
        hypothesis
        for hypothesis in survivors
        if hypothesis != selected_setting
        and any(apply_rule(pair["input"], hypothesis) != pair["output"] for pair in episode["test"])
    ]
    return {
        "selected_setting": selected_setting,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "queries_checked": len(episode["test"]),
    }
