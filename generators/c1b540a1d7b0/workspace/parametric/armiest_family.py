"""Native parametric family for canonical arm classification plus a causal finish.

The default ``classify_only`` setting is the byte-exact selected Racket rule.
The composed setting first classifies every gray component into red arm cells
and cyan room cells, then counts red cells in each *classified* component and
highlights the cyan cells belonging to the unique armiest component.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "c1b540a1d7b0"
HERE = Path(__file__).resolve().parent
FINISH_RULES = ("classify_only", "classify_then_highlight_armiest")
DIRS4 = ((-1, 0), (0, -1), (1, 0), (0, 1))
DIRS8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))

_DEMO_SHAPES = ((14, 16), (18, 20), (22, 24), (24, 26), (26, 28), (28, 30))
_QUERY_SHAPES = ((15, 18), (19, 22), (25, 27), (30, 30))
# The first two rows are the minimum teaching lesson.  They deliberately
# reverse total-size ordering and include a bridge-arm object whose canonical
# red-arm count cannot be recovered from raw degree-one tips.
_COMPONENT_SPECS = (
    (("bridge", 2), ("room", 3, 3, ("right",))),
    (("room", 3, 3, ("up", "down", "left", "right")), ("bridge", 4)),
    (("room", 3, 3, ("up", "down", "left", "right")),
     ("room", 4, 5, ("up", "left", "right"))),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"finish_rule"}:
        raise ValueError("settings must contain exactly finish_rule")
    value = settings["finish_rule"]
    if type(value) is not str or value not in FINISH_RULES:
        raise ValueError(f"finish_rule must be one of {FINISH_RULES}")
    return {"finish_rule": value}


def program(settings: Any) -> str:
    value = normalize_settings(settings)["finish_rule"]
    filename = "canonical.rkt" if value == "classify_only" else "highlight_armiest.rkt"
    return (HERE / filename).read_text()


def classify(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror of the selected canonical Racket rule."""
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30 or any(
        type(row) is not list or len(row) != width
        or any(type(value) is not int or value not in (0, 5) for value in row)
        for row in grid
    ):
        raise ValueError("arm-family inputs must be rectangular 0/5 grids up to 30x30")

    def gray(row: int, column: int) -> bool:
        return 0 <= row < height and 0 <= column < width and grid[row][column] == 5

    def thick(row: int, column: int) -> bool:
        for dr in (-1, 0):
            for dc in (-1, 0):
                if (
                    gray(row + dr, column + dc)
                    and gray(row + dr, column + dc + 1)
                    and gray(row + dr + 1, column + dc)
                    and gray(row + dr + 1, column + dc + 1)
                ):
                    return True
        return False

    red: set[tuple[int, int]] = set()

    def add_arm(row: int, column: int, dr: int, dc: int) -> None:
        for step in range(3):
            point = row + dr * step, column + dc * step
            if gray(*point):
                red.add(point)

    for row in range(height):
        for column in range(width):
            if gray(row, column):
                neighbors = [(dr, dc) for dr, dc in DIRS4 if gray(row + dr, column + dc)]
                if len(neighbors) == 1:
                    add_arm(row, column, *neighbors[0])
    for row in range(height):
        for column in range(width):
            if gray(row, column) and not thick(row, column) and (row, column) not in red:
                for dr, dc in DIRS4:
                    if gray(row + dr, column + dc) and thick(row + dr, column + dc):
                        add_arm(row, column, dr, dc)
                        break
    return [
        [2 if (row, column) in red else 8 if grid[row][column] == 5 else grid[row][column]
         for column in range(width)]
        for row in range(height)
    ]


def _components(stage: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(stage), len(stage[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if stage[row][column] == 0 or (row, column) in seen:
                continue
            cells: list[tuple[int, int]] = []
            queue = deque([(row, column)])
            seen.add((row, column))
            while queue:
                current = queue.popleft()
                cells.append(current)
                for dr, dc in DIRS8:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and stage[nxt[0]][nxt[1]] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(cells)
    return result


def _component_score(stage: list[list[int]], cells: list[tuple[int, int]], selector: str) -> tuple[int, ...]:
    red = sum(stage[row][column] == 2 for row, column in cells)
    cyan = sum(stage[row][column] == 8 for row, column in cells)
    top = min(row for row, _ in cells)
    left = min(column for _, column in cells)
    if selector == "armiest":
        return red, -top, -left
    if selector == "largest_total":
        return len(cells), -top, -left
    if selector == "largest_cyan":
        return cyan, -top, -left
    if selector == "smallest_total":
        return -len(cells), -top, -left
    if selector == "top_left":
        return -top, -left
    if selector == "bottom_right":
        return top, left
    raise ValueError(f"unknown selector {selector}")


def highlight_by(stage: list[list[int]], selector: str) -> list[list[int]]:
    components = _components(stage)
    if not components:
        return copy.deepcopy(stage)
    winner = max(components, key=lambda cells: _component_score(stage, cells, selector))
    output = copy.deepcopy(stage)
    for row, column in winner:
        if output[row][column] == 8:
            output[row][column] = 4
    return output


def finish_python(grid: list[list[int]], settings: Any) -> list[list[int]]:
    value = normalize_settings(settings)["finish_rule"]
    stage = classify(grid)
    return stage if value == "classify_only" else highlight_by(stage, "armiest")


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    stage = classify(grid)
    components = _components(stage)
    red_counts = [sum(stage[r][c] == 2 for r, c in cells) for cells in components]
    cyan_counts = [sum(stage[r][c] == 8 for r, c in cells) for cells in components]
    totals = [len(cells) for cells in components]
    height, width = len(grid), len(grid[0])

    def raw_tip_count(cells: list[tuple[int, int]]) -> int:
        return sum(
            grid[row][column] == 5
            and sum(
                0 <= row + dr < height
                and 0 <= column + dc < width
                and grid[row + dr][column + dc] == 5
                for dr, dc in DIRS4
            ) == 1
            for row, column in cells
        )

    raw_tip_counts = [raw_tip_count(cells) for cells in components]
    if len(components) != 2:
        raise ValueError(f"expected exactly two classified components, found {len(components)}")
    return {
        "red_counts": red_counts,
        "cyan_counts": cyan_counts,
        "totals": totals,
        "raw_tip_counts": raw_tip_counts,
        "armiest_index": max(range(len(components)), key=lambda i: red_counts[i]),
        "largest_total_index": max(range(len(components)), key=lambda i: totals[i]),
        "smallest_total_index": min(range(len(components)), key=lambda i: totals[i]),
        "largest_cyan_index": max(range(len(components)), key=lambda i: cyan_counts[i]),
        "most_raw_tips_index": max(range(len(components)), key=lambda i: raw_tip_counts[i]),
    }


def _component(room_h: int, room_w: int, sides: tuple[str, ...]) -> set[tuple[int, int]]:
    room_top = room_left = 3
    cells = {
        (row, column)
        for row in range(room_top, room_top + room_h)
        for column in range(room_left, room_left + room_w)
    }
    middle_row = room_top + room_h // 2
    middle_column = room_left + room_w // 2
    for side in sides:
        if side == "up":
            cells.update((room_top - step, middle_column) for step in range(1, 4))
        elif side == "down":
            cells.update((room_top + room_h - 1 + step, middle_column) for step in range(1, 4))
        elif side == "left":
            cells.update((middle_row, room_left - step) for step in range(1, 4))
        elif side == "right":
            cells.update((middle_row, room_left + room_w - 1 + step) for step in range(1, 4))
        else:
            raise ValueError(side)
    return _normalize(cells)


def _bridge_component(gap: int) -> set[tuple[int, int]]:
    """Two 2x2 rooms joined by a one-cell-wide bridge.

    The canonical classifier colors the bridge as red arms even though the raw
    object has no degree-one tip.  This is the key witness that Stage B must
    consume Stage A rather than a raw-input tip heuristic.
    """
    right_left = 2 + gap
    cells = {
        (row, column)
        for row in (1, 2)
        for column in (0, 1, right_left, right_left + 1)
    }
    cells.update((1, column) for column in range(2, right_left))
    return _normalize(cells)


def _make_component(spec: tuple[Any, ...]) -> set[tuple[int, int]]:
    if spec[0] == "bridge":
        return _bridge_component(int(spec[1]))
    if spec[0] == "room":
        return _component(int(spec[1]), int(spec[2]), tuple(spec[3]))
    raise ValueError(f"unknown component spec {spec!r}")


def _normalize(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    top = min(row for row, _ in cells)
    left = min(column for _, column in cells)
    return {(row - top, column - left) for row, column in cells}


def _transform(cells: set[tuple[int, int]], code: int) -> set[tuple[int, int]]:
    result = set(cells)
    if code >= 4:
        width = max(column for _, column in result)
        result = {(row, width - column) for row, column in result}
    for _ in range(code % 4):
        result = {(column, -row) for row, column in result}
        result = _normalize(result)
    return _normalize(result)


def _shape(cells: set[tuple[int, int]]) -> tuple[int, int]:
    return max(row for row, _ in cells) + 1, max(column for _, column in cells) + 1


def _place(grid: list[list[int]], cells: set[tuple[int, int]], top: int, left: int) -> None:
    height, width = len(grid), len(grid[0])
    for row, column in cells:
        row += top
        column += left
        if not (0 <= row < height and 0 <= column < width) or grid[row][column] != 0:
            raise ValueError("component placement collision or overflow")
        grid[row][column] = 5


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:armiest-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width = (_DEMO_SHAPES if split == "train" else _QUERY_SHAPES)[index]
    spec_index = 2 if split == "test" and index == 3 else index % len(_COMPONENT_SPECS)
    winner_spec, larger_spec = _COMPONENT_SPECS[spec_index]
    rng = _rng(seed, split, index)
    winner = _transform(_make_component(winner_spec), rng.randrange(8))
    larger = _transform(_make_component(larger_spec), rng.randrange(8))
    wh, ww = _shape(winner)
    lh, lw = _shape(larger)
    corners = [
        ((0, 0), (height - lh, width - lw)),
        ((height - wh, width - ww), (0, 0)),
        ((0, width - ww), (height - lh, 0)),
        ((height - wh, 0), (0, width - lw)),
    ]
    winner_pos, larger_pos = corners[(seed + index + (0 if split == "train" else 1)) % 4]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    _place(grid, winner, *winner_pos)
    _place(grid, larger, *larger_pos)
    facts = analyze_input(grid)
    if len(set(facts["red_counts"])) != 2:
        raise AssertionError(f"scene lost the unique arm-count winner: {facts}")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    normalized = normalize_settings(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("episode inputs must be distinct")
    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": copy.deepcopy(grid), "output": finish_python(grid, normalized)}
    episode = {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(normalized),
        "settings": copy.deepcopy(normalized),
        "metadata": {
            "schema": "c1b540a1d7b0-armiest-v1",
            "seed": seed,
            "sequential_dependency": {
                "step_a": "classify gray cells into canonical red arm and cyan room cells",
                "intermediate": "the complete classified multicolor grid and per-component red-arm counts",
                "step_b": "highlight cyan cells in the unique component with the most red arm cells",
            },
        },
    }
    return copy.deepcopy(episode)


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or len(episode["train"]) < 2:
        raise ValueError("episode needs at least two demonstrations")
    rows = []
    for pair in episode["train"]:
        grid = pair["input"]
        facts = analyze_input(grid)
        canonical = classify(grid)
        composed = highlight_by(canonical, "armiest")
        rows.append({
            **facts,
            "settings_differ": canonical != composed,
            "largest_total_rival_differs": composed != highlight_by(canonical, "largest_total"),
            "largest_cyan_rival_differs": composed != highlight_by(canonical, "largest_cyan"),
        })
    # The two-example minimum lesson refutes each declared shortcut somewhere;
    # no single example is required to reverse every ordering simultaneously.
    ok = (
        all(row["settings_differ"] and len(set(row["red_counts"])) == 2 for row in rows)
        and any(row["largest_total_rival_differs"] for row in rows)
        and any(row["largest_cyan_rival_differs"] for row in rows)
        and any(row["armiest_index"] != row["smallest_total_index"] for row in rows)
        and any(row["armiest_index"] != row["most_raw_tips_index"] for row in rows)
    )
    return {"ok": ok, "demonstrations": rows, "finite_scope": True}


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("invalid private episode")
    query_index = _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
