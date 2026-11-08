"""Matched-input parametric family for b13481ce1294.

The canonical setting emits every exclusive nonzero panel cell. The alternate
first finds the unique same-color overlap, retains that input-derived agreement
color, and then emits only exclusive cells of that color. The second step cannot
be chosen before the overlap-derived selector is known.
"""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
from pathlib import Path
import random
from typing import Callable

HERE = Path(__file__).resolve().parent
POLICIES = ("all_exclusive", "agreement_color")
PROGRAMS = {
    "all_exclusive": (HERE / "canonical.rkt").read_text(encoding="utf-8"),
    "agreement_color": (HERE / "agreement_color.rkt").read_text(encoding="utf-8"),
}
Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def policy(settings) -> str:
    if type(settings) is not dict or set(settings) != {"xor_policy"}:
        raise ValueError("settings must contain exactly xor_policy")
    value = settings["xor_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"xor_policy must be one of {POLICIES!r}")
    return value


def program(settings) -> str:
    return PROGRAMS[policy(settings)]


def _parse(grid) -> dict[str, object]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    width = len(grid[0])
    if len(grid) > 30 or width > 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    separators = [c for c in range(width) if all(row[c] == 8 for row in grid)]
    if len(separators) != 1:
        raise ValueError("grid must contain exactly one full color-8 separator column")
    sep = separators[0]
    panel_w = sep
    if panel_w < 2 or width - sep - 1 != panel_w:
        raise ValueError("separator must divide equal nonempty panels")
    left = [row[:sep] for row in grid]
    right = [row[sep + 1:] for row in grid]
    if any(value == 8 for panel in (left, right) for row in panel for value in row):
        raise ValueError("color 8 is reserved for the separator")
    overlaps = []
    same = []
    different = []
    exclusives = []
    for r in range(len(grid)):
        for c in range(panel_w):
            lv, rv = left[r][c], right[r][c]
            if lv != 0 and rv != 0:
                overlaps.append((r, c, lv, rv))
                (same if lv == rv else different).append((r, c, lv, rv))
            elif (lv != 0) != (rv != 0):
                exclusives.append((r, c, lv if lv != 0 else rv, "left" if lv != 0 else "right"))
    if len(same) != 1 or len(different) < 2 or len(exclusives) < 8:
        raise ValueError("scene needs one same-color overlap, two different overlaps, and eight exclusives")
    anchor_color = same[0][2]
    if not any(color == anchor_color and side == "left" for _, _, color, side in exclusives):
        raise ValueError("scene needs a left anchor-color exclusive")
    if not any(color == anchor_color and side == "right" for _, _, color, side in exclusives):
        raise ValueError("scene needs a right anchor-color exclusive")
    exclusive_counts = Counter(color for _, _, color, _ in exclusives)
    most_frequent = max(sorted(exclusive_counts), key=lambda color: exclusive_counts[color])
    first_overlap = min(overlaps)
    first_different = min(different)
    overlap_colors = frozenset([value for _, _, lv, rv in overlaps for value in (lv, rv)])
    if not any(color not in overlap_colors for _, _, color, _ in exclusives):
        raise ValueError("scene needs an exclusive-only color")
    return {
        "height": len(grid),
        "width": width,
        "separator": sep,
        "panel_w": panel_w,
        "left": left,
        "right": right,
        "overlaps": overlaps,
        "same": same,
        "different": different,
        "exclusives": exclusives,
        "anchor_color": anchor_color,
        "first_overlap_kind": "same" if first_overlap[2] == first_overlap[3] else "different",
        "first_overlap_left_color": first_overlap[2],
        "first_different_left_color": first_different[2],
        "first_different_right_color": first_different[3],
        "most_frequent_exclusive_color": most_frequent,
        "overlap_colors": overlap_colors,
    }


def _render_selected(grid: Grid, selected_color: int | None, *, side: str | None = None, invert: bool = False, allowed_colors=None) -> Grid:
    parsed = _parse(grid)
    output = [[0 for _ in range(parsed["panel_w"])] for _ in range(parsed["height"])]
    for r, c, color, actual_side in parsed["exclusives"]:
        matches = selected_color is None or color == selected_color
        if allowed_colors is not None:
            matches = color in allowed_colors
        if invert:
            matches = not matches
        if side is not None:
            matches = matches and actual_side == side
        if matches:
            output[r][c] = color
    return output


def solve(grid: Grid, selected_policy: str) -> Grid:
    if selected_policy not in POLICIES:
        raise ValueError(f"unknown policy {selected_policy!r}")
    parsed = _parse(grid)
    selected = None if selected_policy == "all_exclusive" else int(parsed["anchor_color"])
    return _render_selected(grid, selected)


def solve_with_first_different_left_color(grid: Grid) -> Grid:
    return _render_selected(grid, int(_parse(grid)["first_different_left_color"]))


def describe_case(grid: Grid) -> dict[str, object]:
    parsed = _parse(grid)
    return {
        "height": parsed["height"],
        "width": parsed["width"],
        "panel_w": parsed["panel_w"],
        "anchor_color": parsed["anchor_color"],
        "same_overlap_count": len(parsed["same"]),
        "different_overlap_count": len(parsed["different"]),
        "exclusive_count": len(parsed["exclusives"]),
        "first_overlap_kind": parsed["first_overlap_kind"],
        "first_overlap_left_color": parsed["first_overlap_left_color"],
        "first_different_left_color": parsed["first_different_left_color"],
        "first_different_right_color": parsed["first_different_right_color"],
        "most_frequent_exclusive_color": parsed["most_frequent_exclusive_color"],
    }


def _selector_rival(key: str) -> Rival:
    return lambda grid: _render_selected(grid, int(_parse(grid)[key]))


def _any_overlap_color(grid: Grid) -> Grid:
    parsed = _parse(grid)
    return _render_selected(grid, None, allowed_colors=parsed["overlap_colors"])


def _anchor_side(side: str) -> Rival:
    return lambda grid: _render_selected(grid, int(_parse(grid)["anchor_color"]), side=side)


def _non_anchor(grid: Grid) -> Grid:
    parsed = _parse(grid)
    return _render_selected(grid, int(parsed["anchor_color"]), invert=True)


def rivals_for(selected_policy: str) -> dict[str, Rival]:
    if selected_policy not in POLICIES:
        raise ValueError(selected_policy)
    rivals: dict[str, Rival] = {
        "other_admitted_setting": lambda grid: solve(
            grid,
            "agreement_color" if selected_policy == "all_exclusive" else "all_exclusive",
        ),
        "first_overlap_left_color": _selector_rival("first_overlap_left_color"),
        "first_different_left_color": _selector_rival("first_different_left_color"),
        "first_different_right_color": _selector_rival("first_different_right_color"),
        "most_frequent_exclusive_color": _selector_rival("most_frequent_exclusive_color"),
        "any_overlap_color": _any_overlap_color,
        "left_anchor_only": _anchor_side("left"),
        "right_anchor_only": _anchor_side("right"),
        "all_non_anchor_exclusives": _non_anchor,
    }
    for color in (1, 2, 3, 4, 5, 6, 7, 9):
        rivals[f"fixed_color_{color}"] = lambda grid, color=color: _render_selected(grid, color)
    return rivals


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"b13481ce1294:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _colors(seed: int, split: str, index: int) -> dict[str, int]:
    palette = (1, 2, 3, 4, 5, 6, 7, 9)
    base = (seed * 5 + index * 2 + (0 if split == "demo" else 3)) % len(palette)
    rotated = [palette[(base + offset) % len(palette)] for offset in range(len(palette))]
    return {"A": rotated[0], "B": rotated[2], "C": rotated[4], "D": rotated[6], "E": rotated[1]}


def _small_scene(seed: int, split: str, index: int) -> Grid:
    rng = _rng(seed, split, index)
    colors = _colors(seed, split, index)
    height = 7 + ((index + (0 if split == "demo" else 1)) % 4)
    panel_w = 6 + ((2 * index + (0 if split == "demo" else 1)) % 3)
    left = [[0 for _ in range(panel_w)] for _ in range(height)]
    right = [[0 for _ in range(panel_w)] for _ in range(height)]
    if split == "demo" and index == 0:
        overlap_specs = [((0, 0), "B", "C"), ((1, 1), "A", "A"), ((2, 2), "C", "D")]
    elif split == "demo" and index == 1:
        overlap_specs = [((0, 0), "A", "A"), ((1, 1), "B", "C"), ((2, 2), "D", "B")]
    else:
        ar = 1 + (index % max(1, height - 2))
        ac = 1 + ((2 * index + 1) % max(1, panel_w - 2))
        overlap_specs = [((0, 0), "B", "C"), ((ar, ac), "A", "A"), ((height - 1, panel_w - 1), "C", "D")]
    occupied = set()
    for (r, c), lkey, rkey in overlap_specs:
        left[r][c] = colors[lkey]
        right[r][c] = colors[rkey]
        occupied.add((r, c))
    pool = [(r, c) for r in range(height) for c in range(panel_w) if (r, c) not in occupied]
    rng.shuffle(pool)

    def exclusive(side: str, label: str) -> None:
        if not pool:
            raise ValueError("not enough cells")
        r, c = pool.pop()
        (left if side == "left" else right)[r][c] = colors[label]

    exclusive("left", "A")
    exclusive("left", "A")
    exclusive("right", "A")
    exclusive("right", "A")
    for i in range(8):
        exclusive("left" if i % 2 == 0 else "right", "B")
    for i in range(3):
        exclusive("left" if i % 2 == 0 else "right", "C")
    for i in range(2):
        exclusive("right" if i % 2 == 0 else "left", "D")
    for i in range(2):
        exclusive("left" if i % 2 == 0 else "right", "E")
    grid = [left[r] + [8] + right[r] for r in range(height)]
    _parse(grid)
    return grid


def _large_scene(seed: int) -> Grid:
    colors = _colors(seed, "query", 3)
    height, panel_w = 30, 14
    left = [[0 for _ in range(panel_w)] for _ in range(height)]
    right = [[0 for _ in range(panel_w)] for _ in range(height)]
    for r in range(height):
        for c in range(panel_w):
            if (r, c) == (15, 7):
                left[r][c] = right[r][c] = colors["A"]
            elif (r + c) % 9 == 0:
                left[r][c], right[r][c] = colors["B"], colors["C"]
            elif (3 * r + c) % 5 == 0:
                left[r][c] = colors["B"]
            elif (r + 2 * c) % 5 == 0:
                right[r][c] = colors["B"]
            elif (r + c) % 4 == 0:
                left[r][c] = colors["E"]
            elif (2 * r + c) % 7 == 0:
                right[r][c] = colors["D"]
    for c in range(panel_w):
        left[0][c] = colors["B"]
        right[0][c] = 0
        left[29][c] = 0
        right[29][c] = colors["B"]
    left[14][7], right[14][7] = colors["A"], 0
    left[16][7], right[16][7] = 0, colors["A"]
    left[15][7] = right[15][7] = colors["A"]
    grid = [left[r] + [8] + right[r] for r in range(height)]
    _parse(grid)
    return grid


def _pair(seed: int, split: str, index: int, selected_policy: str) -> dict[str, Grid]:
    grid = _large_scene(seed) if split == "query" and index == 3 else _small_scene(seed, split, index)
    return {"input": grid, "output": solve(grid, selected_policy)}


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    selected_policy = policy(settings)
    return {
        "train": [_pair(seed, "demo", index, selected_policy) for index in range(demos)],
        "test": [_pair(seed, "query", index, selected_policy) for index in range(queries)],
        "program_solution": PROGRAMS[selected_policy],
    }


def public_turn(episode, query_index=0):
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative integer")
    if not isinstance(episode, dict) or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    if query_index >= len(episode["test"]):
        raise ValueError("query_index is outside the retained queries")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
