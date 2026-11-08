"""Parametric template stamping with an input-derived marker selector.

``marker_selection=all`` is the byte-exact canonical rule.  Under
``template_width``, the unique color-2 template's bounding-box width chooses
marker color ``width + 5``; the same normalized template is then stamped at
every marker of that color.  Input sampling is independent of the setting.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Callable

TASK_ID = "06b4c496c6cf"
VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
TEMPLATE_WIDTH = (HERE / "template_width.rkt").read_text(encoding="utf-8")
SETTINGS = (
    {"marker_selection": "all"},
    {"marker_selection": "template_width"},
)
ALL = SETTINGS[0]
WIDTH = SETTINGS[1]
_ALLOWED = ("all", "template_width")
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _setting(settings: dict) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"marker_selection"}
        or type(settings["marker_selection"]) is not str
        or settings["marker_selection"] not in _ALLOWED
    ):
        raise ValueError(
            "settings must be exactly marker_selection=all|template_width"
        )
    return settings["marker_selection"]


def program(settings: dict) -> str:
    return CANONICAL if _setting(settings) == "all" else TEMPLATE_WIDTH


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_count(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value: list[list[int]]) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 3 <= len(value[0]) <= 30
    ):
        raise ValueError("expected a rectangular 3..30 by 3..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return deepcopy(value)


def _components(cells: set[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = []
        while queue:
            cell = queue.popleft()
            component.append(cell)
            r, c = cell
            for dr, dc in _DIRS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        result.append(tuple(sorted(component)))
    return result


def analyze(value: list[list[int]]) -> dict:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    invalid = sorted({cell for row in grid for cell in row if cell not in {0, 2, 3, 4, 5, 6, 7, 8, 9}})
    if invalid:
        raise ValueError(f"unsupported foreground colors: {invalid}")
    template_cells = {
        (r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == 2
    }
    components = _components(template_cells)
    if len(components) != 1:
        raise ValueError("expected exactly one connected color-2 template")
    template = components[0]
    if len(template) < 3:
        raise ValueError("template needs at least three cells")
    r0 = min(r for r, _ in template)
    c0 = min(c for _, c in template)
    r1 = max(r for r, _ in template)
    c1 = max(c for _, c in template)
    template_width = c1 - c0 + 1
    template_height = r1 - r0 + 1
    if not 1 <= template_width <= 4:
        raise ValueError("template bounding-box width must be in 1..4")
    offsets = tuple(sorted((r - r0, c - c0) for r, c in template))
    markers = tuple(
        sorted(
            (r, c, grid[r][c])
            for r in range(h)
            for c in range(w)
            if 3 <= grid[r][c] <= 9
        )
    )
    if not 2 <= len(markers) <= 6:
        raise ValueError("expected 2..6 marker cells")
    target_color = template_width + 5
    counts = Counter(color for _r, _c, color in markers)
    if counts[target_color] < 1:
        raise ValueError("input must contain at least one width-selected marker")
    return {
        "grid": grid,
        "height": h,
        "width": w,
        "template_cells": tuple(template),
        "template_offsets": offsets,
        "template_width": template_width,
        "template_height": template_height,
        "template_cell_count": len(template),
        "target_color": target_color,
        "markers": markers,
        "marker_cells": tuple((r, c) for r, c, _color in markers),
        "marker_count": len(markers),
        "marker_color_counts": dict(sorted(counts.items())),
    }


def _stamped_cells_from_facts(
    facts: dict, *, target_colors: set[int], first_only: bool = False, last_only: bool = False
) -> set[tuple[int, int]]:
    h, w = facts["height"], facts["width"]
    selected = [marker for marker in facts["markers"] if marker[2] in target_colors]
    if first_only:
        selected = selected[:1]
    if last_only:
        selected = selected[-1:]
    result: set[tuple[int, int]] = set()
    for r, c, _color in selected:
        for dr, dc in facts["template_offsets"]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                result.add((rr, cc))
    return result


def stamped_cells(grid: list[list[int]], *, target_color: int) -> set[tuple[int, int]]:
    if type(target_color) is not int or not 3 <= target_color <= 9:
        raise ValueError("target_color must be an exact marker color 3..9")
    return _stamped_cells_from_facts(analyze(grid), target_colors={target_color})


def _solve_selection(
    grid: list[list[int]],
    selector: Callable[[dict], set[int]],
    *,
    first_only: bool = False,
    last_only: bool = False,
    marker_only: bool = False,
) -> list[list[int]]:
    facts = analyze(grid)
    out = [[0] * facts["width"] for _ in range(facts["height"])]
    colors = selector(facts)
    selected = sorted(
        (marker for marker in facts["markers"] if marker[2] in colors),
        key=lambda marker: (marker[2], marker[0], marker[1]),
    )
    if first_only:
        selected = selected[:1]
    if last_only:
        selected = selected[-1:]
    for r, c, color in selected:
        offsets = ((0, 0),) if marker_only else facts["template_offsets"]
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < facts["height"] and 0 <= cc < facts["width"]:
                out[rr][cc] = color
    return out


def solve(grid: list[list[int]], settings: dict) -> list[list[int]]:
    mode = _setting(settings)
    if mode == "all":
        return _solve_selection(grid, lambda _facts: set(range(3, 10)))
    return _solve_selection(grid, lambda facts: {facts["target_color"]})


def _shape(width: int, height: int, style: str) -> tuple[tuple[int, int], ...]:
    if not (1 <= width <= 4 and 2 <= height <= 12):
        raise ValueError("unsupported template dimensions")
    if style == "demo_width2":
        cells = {(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)}
    elif style == "demo_width3":
        cells = {(0, 0), (0, 1), (0, 2), (1, 1)}
    elif style == "dense":
        cells = {(r, c) for r in range(height) for c in range(width)}
    elif style == "frame" and width >= 2 and height >= 3:
        cells = {
            (r, c)
            for r in range(height)
            for c in range(width)
            if r in (0, height - 1) or c in (0, width - 1)
        }
    else:
        cells = {(r, 0) for r in range(height)} | {(0, c) for c in range(width)}
        cells |= {(height - 1, c) for c in range(width)}
        for r in range(1, height - 1):
            for c in range(0, min(width - 1, r % width) + 1):
                cells.add((r, c))
    if max(c for _r, c in cells) + 1 != width or max(r for r, _c in cells) + 1 != height:
        raise AssertionError("template shape does not span declared dimensions")
    if len(_components(set(cells))) != 1:
        raise AssertionError("template shape must be connected")
    return tuple(sorted(cells))


_DEMOS = (
    {"size": (12, 14), "template": (2, 3, "demo_width2"), "colors": (7, 7, 6, 9)},
    {"size": (14, 17), "template": (3, 2, "demo_width3"), "colors": (8, 6, 9, 7)},
    {"size": (16, 18), "template": (1, 6, "dense"), "colors": (6, 6, 7, 8, 9)},
    {"size": (18, 22), "template": (4, 4, "frame"), "colors": (9, 6, 7, 8, 4)},
    {"size": (20, 24), "template": (2, 8, "frame"), "colors": (7, 6, 8, 9, 3, 7)},
    {"size": (22, 26), "template": (3, 7, "stair"), "colors": (8, 6, 7, 9, 5, 8)},
)

_QUERIES = (
    {"size": (18, 22), "template": (1, 10, "dense"), "colors": (6, 7, 8, 9, 3)},
    {"size": (22, 24), "template": (4, 6, "frame"), "colors": (9, 6, 7, 8, 4, 9)},
    {"size": (26, 28), "template": (2, 12, "dense"), "colors": (7, 6, 8, 9, 5, 7)},
    {"size": (30, 30), "template": (3, 10, "dense"), "colors": (8, 6, 7, 9, 5, 8)},
)


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:8], "big"))


def _marker_candidates(h: int, w: int) -> list[tuple[int, int]]:
    return [
        (0, 0),
        (0, w - 1),
        (h // 3, w // 2),
        (h // 2, w - 1),
        (h - 1, 0),
        (h - 1, w - 1),
        (h // 2, 0),
        (1, w // 3),
        (max(0, h - 2), w // 2),
    ]


def _build_input(seed: int, split: str, index: int, spec: dict) -> list[list[int]]:
    rng = _rng(seed, split, index)
    h, w = spec["size"]
    template_w, template_h, style = spec["template"]
    offsets = _shape(template_w, template_h, style)
    max_top = h - template_h - 1
    max_left = w - template_w - 1
    top = 1 + rng.randrange(max(1, max_top))
    left = 1 + rng.randrange(max(1, max_left))
    template_cells = {(top + r, left + c) for r, c in offsets}
    grid = [[0] * w for _ in range(h)]
    for r, c in template_cells:
        grid[r][c] = 2

    candidates = []
    for cell in _marker_candidates(h, w):
        if cell not in template_cells and cell not in candidates:
            candidates.append(cell)
    if len(candidates) < len(spec["colors"]):
        for r in range(h):
            for c in range(w):
                if (r, c) not in template_cells and (r, c) not in candidates:
                    candidates.append((r, c))
    # Rotate positions by seed while keeping boundary-rich candidate membership.
    shift = rng.randrange(len(candidates))
    candidates = candidates[shift:] + candidates[:shift]
    chosen = candidates[: len(spec["colors"])]
    colors = list(spec["colors"])
    rng.shuffle(colors)

    # The minimum curriculum must visibly demonstrate a template stamp rather
    # than permitting the shortcut "keep only the selected marker cell".
    # Preserve the boundary-rich placement whenever one chosen cell can host
    # the full template; otherwise replace one selected-color position with a
    # deterministic full-fit anchor.
    target_color = template_w + 5

    def full_fit(cell: tuple[int, int]) -> bool:
        r, c = cell
        return all(0 <= r + dr < h and 0 <= c + dc < w for dr, dc in offsets)

    placements = list(zip(chosen, colors, strict=True))
    if not any(color == target_color and full_fit(cell) for cell, color in placements):
        target_index = next(i for i, (_cell, color) in enumerate(placements) if color == target_color)
        safe_index = next(
            (
                i
                for i, (cell, color) in enumerate(placements)
                if color != target_color and full_fit(cell)
            ),
            None,
        )
        if safe_index is not None:
            target_cell, target_value = placements[target_index]
            safe_cell, safe_value = placements[safe_index]
            placements[target_index] = (target_cell, safe_value)
            placements[safe_index] = (safe_cell, target_value)
        else:
            occupied = {cell for cell, _color in placements}
            anchors = [
                (r, c)
                for r in range(h)
                for c in range(w)
                if (r, c) not in template_cells
                and (r, c) not in occupied
                and full_fit((r, c))
            ]
            if not anchors:
                raise AssertionError("no full-fit anchor for width-selected marker")
            placements[target_index] = (anchors[rng.randrange(len(anchors))], target_color)

    for (r, c), color in placements:
        grid[r][c] = color
    facts = analyze(grid)
    if facts["template_width"] != template_w:
        raise AssertionError("constructed template width drifted")
    return grid


def _inputs(seed: int, demos: int, queries: int) -> tuple[list, list]:
    train = [_build_input(seed, "train", i, spec) for i, spec in enumerate(_DEMOS[:demos])]
    test = [_build_input(seed, "test", i, spec) for i, spec in enumerate(_QUERIES[:queries])]
    serial = [repr(grid) for grid in train + test]
    if len(serial) != len(set(serial)):
        raise AssertionError("generated inputs must be distinct")
    return train, test


def _fixed(color: int) -> Callable[[dict], set[int]]:
    return lambda _facts: {color}


def _height_color(facts: dict) -> set[int]:
    return {5 + min(4, facts["template_height"])}


def _cell_count_color(facts: dict) -> set[int]:
    return {3 + min(6, facts["template_cell_count"])}


_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "canonical_all": lambda grid: _solve_selection(grid, lambda _facts: set(range(3, 10))),
    "template_width": lambda grid: _solve_selection(grid, lambda facts: {facts["target_color"]}),
    "fixed_color_6": lambda grid: _solve_selection(grid, _fixed(6)),
    "fixed_color_7": lambda grid: _solve_selection(grid, _fixed(7)),
    "fixed_color_8": lambda grid: _solve_selection(grid, _fixed(8)),
    "fixed_color_9": lambda grid: _solve_selection(grid, _fixed(9)),
    "highest_marker_color": lambda grid: _solve_selection(
        grid, lambda facts: {max(color for _r, _c, color in facts["markers"])}
    ),
    "lowest_marker_color": lambda grid: _solve_selection(
        grid, lambda facts: {min(color for _r, _c, color in facts["markers"])}
    ),
    "template_height_color": lambda grid: _solve_selection(grid, _height_color),
    "template_cell_count_color": lambda grid: _solve_selection(grid, _cell_count_color),
    "first_width_marker_only": lambda grid: _solve_selection(
        grid, lambda facts: {facts["target_color"]}, first_only=True
    ),
    "last_width_marker_only": lambda grid: _solve_selection(
        grid, lambda facts: {facts["target_color"]}, last_only=True
    ),
    "selected_marker_cells_only": lambda grid: _solve_selection(
        grid, lambda facts: {facts["target_color"]}, marker_only=True
    ),
}


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {name: solver(grid) for name, solver in _RIVALS.items()}


def lesson_report(episode: dict, settings: dict) -> dict:
    chosen = _setting(settings)
    official_name = "canonical_all" if chosen == "all" else "template_width"
    rivals = {name: solver for name, solver in _RIVALS.items() if name != official_name}
    surviving = []
    disagreements = []
    for name, solver in rivals.items():
        if all(solver(pair["input"]) == pair["output"] for pair in episode["train"]):
            surviving.append(name)
            if any(solver(pair["input"]) != pair["output"] for pair in episode["test"]):
                disagreements.append(name)
    return {
        "setting": deepcopy(settings),
        "rivals_tested": sorted(rivals),
        "surviving_rivals": sorted(surviving),
        "query_disagreements": sorted(disagreements),
        "limits": "Finite authored rivals only; not a proof of unique induction.",
    }


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    _validate_seed(seed)
    _validate_count(demos, 2, 6, "demos")
    _validate_count(queries, 1, 4, "queries")
    _setting(settings)
    train_inputs, test_inputs = _inputs(seed, demos, queries)
    episode = {
        "train": [{"input": grid, "output": solve(grid, settings)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, settings)} for grid in test_inputs],
        "program_solution": program(settings),
    }
    report = lesson_report(episode, settings)
    if report["surviving_rivals"]:
        raise AssertionError(f"teaching hole: {report}")
    return deepcopy(episode)


def sequential_witness() -> dict:
    episode = generate(17, WIDTH, 2, 4)
    grid = episode["test"][2]["input"]
    facts = analyze(grid)
    target = facts["target_color"]
    wrong = 6 + ((target - 5) % 4)
    if wrong == target:
        wrong = 6 + ((wrong - 5) % 4)
    correct = solve(grid, WIDTH)
    counterfactual = _solve_selection(grid, _fixed(wrong))
    if correct == counterfactual:
        raise AssertionError("sequential witness counterfactual must change the output")
    return {
        "settings": deepcopy(WIDTH),
        "step_a": "measure the bounding-box width of the unique color-2 template",
        "intermediate_name": "target marker color = template width + 5",
        "intermediate_value": target,
        "step_b": "stamp the normalized template at every marker of the selected color",
        "why_b_depends_on_a": (
            "the eligible marker cells cannot be chosen until the template width determines "
            "which of colors 6 through 9 is selected"
        ),
        "input": deepcopy(grid),
        "correct_output": correct,
        "wrong_intermediate_value": wrong,
        "wrong_intermediate_output": counterfactual,
    }
