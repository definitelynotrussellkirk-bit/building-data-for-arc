"""Parametric fill/project family with a causal opposite-border bridge stage.

``project_only`` is the byte-exact canonical rule. ``project_then_bridge`` first
fills every one-gap rectangular outline and projects color 2 from each gap to the
corresponding canvas edge.  It then reads the *new* color-2 border contacts from
that completed grid and paints color-3 connectors only where opposite contacts
share a row or column. Inputs are independent of the hidden setting.
"""
from __future__ import annotations

from collections import Counter, deque
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "bdcb4c9eb6bd"
HERE = Path(__file__).resolve().parent
FINISH_RULES = ("project_only", "project_then_bridge")
BACKGROUND_COLORS = (0, 4, 5, 6, 7, 8, 9)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"finish_rule"}:
        raise ValueError("settings must contain exactly finish_rule")
    value = settings["finish_rule"]
    if type(value) is not str or value not in FINISH_RULES:
        raise ValueError(f"finish_rule must be one of {FINISH_RULES}")
    return {"finish_rule": value}


def program(settings: dict[str, Any]) -> str:
    rule = normalize_settings(settings)["finish_rule"]
    name = "canonical.rkt" if rule == "project_only" else "project_then_bridge.rkt"
    return (HERE / name).read_text()


def background_color(grid: list[list[int]]) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _validate_grid(grid: Any) -> tuple[int, int, int]:
    if (
        type(grid) is not list
        or not 4 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 4 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be rectangular with dimensions in 4..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer ARC colors")
    bg = background_color(grid)
    if bg in (1, 2, 3):
        raise ValueError("background must differ from transformation colors 1,2,3")
    if any(value not in (bg, 1) for row in grid for value in row):
        raise ValueError("inputs may contain only background and color 1")
    return len(grid), width, bg


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] != color or (row, column) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(row, column)])
            seen.add((row, column))
            while queue:
                point = queue.popleft()
                component.append(point)
                for dr, dc in CARDINAL:
                    neighbor = point[0] + dr, point[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            result.append(component)
    return result


def _rectangle(component: list[tuple[int, int]], grid: list[list[int]]) -> dict[str, Any]:
    rows = [row for row, _ in component]
    columns = [column for _, column in component]
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)
    if bottom - top < 3 or right - left < 3:
        raise ValueError("each outline needs a strict interior")
    full = {
        "up": all(grid[top][column] == 1 for column in range(left, right + 1)),
        "down": all(grid[bottom][column] == 1 for column in range(left, right + 1)),
        "left": all(grid[row][left] == 1 for row in range(top, bottom + 1)),
        "right": all(grid[row][right] == 1 for row in range(top, bottom + 1)),
    }
    open_sides = [side for side, is_full in full.items() if not is_full]
    if len(open_sides) != 1:
        raise ValueError("each outline must have exactly one open side")
    side = open_sides[0]
    if side in ("up", "down"):
        edge_row = top if side == "up" else bottom
        gaps = [(edge_row, column) for column in range(left + 1, right) if grid[edge_row][column] != 1]
    else:
        edge_column = left if side == "left" else right
        gaps = [(row, edge_column) for row in range(top + 1, bottom) if grid[row][edge_column] != 1]
    if len(gaps) != 1:
        raise ValueError("each open side must have exactly one non-corner gap")
    expected = {
        (top, column) for column in range(left, right + 1)
    } | {
        (bottom, column) for column in range(left, right + 1)
    } | {
        (row, left) for row in range(top + 1, bottom)
    } | {
        (row, right) for row in range(top + 1, bottom)
    }
    expected.remove(gaps[0])
    if set(component) != expected:
        raise ValueError("color-1 component must be a one-gap rectangular outline")
    return {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "side": side,
        "gap": gaps[0],
    }


def _rectangles(grid: list[list[int]]) -> list[dict[str, Any]]:
    _validate_grid(grid)
    rectangles = [_rectangle(component, grid) for component in _components(grid, 1)]
    if len(rectangles) < 2:
        raise ValueError("parametric scenes require at least two rectangles")
    return sorted(rectangles, key=lambda item: (item["top"], item["left"]))


def project_only(grid: list[list[int]]) -> list[list[int]]:
    height, width, bg = _validate_grid(grid)
    output = copy.deepcopy(grid)
    for facts in _rectangles(grid):
        top, bottom = facts["top"], facts["bottom"]
        left, right = facts["left"], facts["right"]
        for row in range(top + 1, bottom):
            for column in range(left + 1, right):
                if output[row][column] == bg:
                    output[row][column] = 2
        gap_row, gap_column = facts["gap"]
        if facts["side"] == "left":
            points = ((gap_row, column) for column in range(0, left + 1))
        elif facts["side"] == "right":
            points = ((gap_row, column) for column in range(right, width))
        elif facts["side"] == "up":
            points = ((row, gap_column) for row in range(0, top + 1))
        else:
            points = ((row, gap_column) for row in range(bottom, height))
        for row, column in points:
            if output[row][column] == bg:
                output[row][column] = 2
    return output


def _bridge(stage: list[list[int]], bg: int) -> list[list[int]]:
    height, width = len(stage), len(stage[0])
    output = copy.deepcopy(stage)
    for row in range(height):
        if stage[row][0] == stage[row][width - 1] == 2:
            for column in range(width):
                if output[row][column] == bg:
                    output[row][column] = 3
    for column in range(width):
        if stage[0][column] == stage[height - 1][column] == 2:
            for row in range(height):
                if output[row][column] == bg:
                    output[row][column] = 3
    return output


def solve_python(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    rule = normalize_settings(settings)["finish_rule"]
    stage = project_only(grid)
    return stage if rule == "project_only" else _bridge(stage, background_color(grid))


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    rectangles = _rectangles(grid)
    stage = project_only(grid)
    horizontal = [row for row in range(len(stage)) if stage[row][0] == stage[row][-1] == 2]
    vertical = [column for column in range(len(stage[0])) if stage[0][column] == stage[-1][column] == 2]
    return {
        "rectangles": len(rectangles),
        "open_sides": [item["side"] for item in rectangles],
        "gaps": [list(item["gap"]) for item in rectangles],
        "bridge_axes": {"rows": horizontal, "columns": vertical},
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:projection-bridge-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _draw_outline(
    grid: list[list[int]],
    *,
    top: int,
    left: int,
    height: int,
    width: int,
    side: str,
    gap_offset: int,
) -> None:
    bottom, right = top + height - 1, left + width - 1
    if not (0 <= top < bottom < len(grid) and 0 <= left < right < len(grid[0])):
        raise ValueError("rectangle does not fit")
    for column in range(left, right + 1):
        grid[top][column] = 1
        grid[bottom][column] = 1
    for row in range(top + 1, bottom):
        grid[row][left] = 1
        grid[row][right] = 1
    if side == "left":
        gap = top + gap_offset, left
    elif side == "right":
        gap = top + gap_offset, right
    elif side == "up":
        gap = top, left + gap_offset
    elif side == "down":
        gap = bottom, left + gap_offset
    else:
        raise ValueError(f"unknown side {side}")
    if gap[0] in (top, bottom) and gap[1] in (left, right):
        raise ValueError("gap cannot be a corner")
    grid[gap[0]][gap[1]] = background_color(grid)


def _horizontal_pair(grid: list[list[int]], row: int, *, touch: bool, rng: random.Random) -> None:
    width = len(grid[0])
    # Fixed 5x5 pair members keep cross layouts separated under every seed;
    # diversity comes from canvas, placement, background, axis, and distractors.
    left_h = left_w = right_h = right_w = 5
    left_top = row - 2
    right_top = row - 2
    left_column = 0 if touch else 2
    right_column = width - right_w if touch else width - right_w - 2
    _draw_outline(grid, top=left_top, left=left_column, height=left_h, width=left_w,
                  side="left", gap_offset=2)
    _draw_outline(grid, top=right_top, left=right_column, height=right_h, width=right_w,
                  side="right", gap_offset=2)


def _vertical_pair(grid: list[list[int]], column: int, *, touch: bool, rng: random.Random) -> None:
    height = len(grid)
    top_h = top_w = bottom_h = bottom_w = 5
    top_row = 0 if touch else 2
    bottom_row = height - bottom_h if touch else height - bottom_h - 2
    top_left = column - 2
    bottom_left = column - 2
    _draw_outline(grid, top=top_row, left=top_left, height=top_h, width=top_w,
                  side="up", gap_offset=2)
    _draw_outline(grid, top=bottom_row, left=bottom_left, height=bottom_h, width=bottom_w,
                  side="down", gap_offset=2)


def _distractor(grid: list[list[int]], kind: str) -> None:
    height, width = len(grid), len(grid[0])
    if kind == "top":
        _draw_outline(grid, top=1, left=max(1, width // 2 - 2), height=4, width=5,
                      side="up", gap_offset=2)
    elif kind == "left":
        _draw_outline(grid, top=max(1, height // 2 - 1), left=1, height=5, width=4,
                      side="left", gap_offset=2)
    elif kind == "inner_left":
        _draw_outline(grid, top=17, left=6, height=5, width=5,
                      side="left", gap_offset=2)
    elif kind == "inner_up":
        _draw_outline(grid, top=6, left=3, height=5, width=5,
                      side="up", gap_offset=2)
    else:
        raise ValueError(kind)


_TRAIN_PROFILES = (
    ("horizontal", 17, 25, False),
    ("vertical", 25, 17, False),
    ("cross", 19, 21, False),
    ("horizontal", 21, 25, True),
    ("vertical", 25, 21, True),
    ("cross", 27, 29, False),
)
_TEST_PROFILES = (
    ("horizontal", 15, 23, False),
    ("vertical", 23, 17, False),
    ("cross", 27, 29, True),
    ("cross30", 30, 30, True),
)


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    table = _TRAIN_PROFILES if split == "train" else _TEST_PROFILES
    kind, height, width, touch = table[index]
    rng = _rng(seed, split, index)
    bg = BACKGROUND_COLORS[(seed + index + (0 if split == "train" else 3)) % len(BACKGROUND_COLORS)]
    grid = [[bg for _ in range(width)] for _ in range(height)]
    if kind in ("cross", "cross30"):
        # The center placement leaves a full background moat between all four
        # outlines; independent jitter can otherwise join diagonal arms.
        row, column = height // 2, width // 2
    else:
        row = height // 2 + rng.choice((-1, 0, 1))
        column = width // 2 + rng.choice((-1, 0, 1))
    if kind in ("horizontal", "cross", "cross30"):
        _horizontal_pair(grid, row, touch=touch, rng=rng)
    if kind in ("vertical", "cross", "cross30"):
        _vertical_pair(grid, column, touch=touch, rng=rng)
    # The two minimum-prefix demonstrations each contain an unpaired projection
    # on the orthogonal axis.  This makes "bridge any border contact" visibly
    # wrong while preserving one clean opposite-border pair to teach Stage B.
    if split == "train" and index == 0:
        _distractor(grid, "top")
    elif split == "train" and index == 1:
        _distractor(grid, "left")
    if kind == "cross30":
        _distractor(grid, "inner_left")
        _distractor(grid, "inner_up")
    # Construction must stay valid and informative for both settings.
    facts = analyze_input(grid)
    if not facts["bridge_axes"]["rows"] and not facts["bridge_axes"]["columns"]:
        raise RuntimeError("constructed scene lacks an opposite-border projection pair")
    return grid


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        return {"ok": False, "reason": "episode needs a training list"}
    survivors = []
    for name in FINISH_RULES:
        candidate = {"finish_rule": name}
        try:
            if all(solve_python(pair["input"], candidate) == pair["output"] for pair in episode["train"]):
                survivors.append(name)
        except (KeyError, TypeError, ValueError):
            return {"ok": False, "reason": "malformed demonstration"}
    selected = normalize_settings(episode.get("settings", {}))["finish_rule"]
    return {
        "ok": survivors == [selected],
        "survivors": survivors,
        "expected": [selected],
        "finite_family": list(FINISH_RULES),
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    normalized = normalize_settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    used: set[str] = set()
    splits: dict[str, list[dict[str, list[list[int]]]]] = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = _input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in used:
                raise RuntimeError("constructed duplicate input")
            used.add(key)
            canonical = solve_python(grid, {"finish_rule": "project_only"})
            bridge = solve_python(grid, {"finish_rule": "project_then_bridge"})
            if canonical == bridge:
                raise RuntimeError("constructed input does not distinguish settings")
            pairs.append({"input": grid, "output": solve_python(grid, normalized)})
        splits[split] = pairs
    episode = {
        "train": splits["train"],
        "test": splits["test"],
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    certificate = teaching_check(episode)
    if not certificate["ok"]:
        raise RuntimeError(f"demonstrations failed finite identification: {certificate}")
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
