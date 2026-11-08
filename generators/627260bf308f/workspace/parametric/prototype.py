"""Matched-input canonical rank recoloring and remote-payload relay family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "627260bf308f"
VERSION = "1.0.0"
RANK_ONLY = {"finish_mode": "rank_only"}
RANK_RELAY = {"finish_mode": "rank_relay"}
SETTINGS = (RANK_ONLY, RANK_RELAY)
_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "rank_only": _HOME / "canonical.rkt",
    "rank_relay": _HOME / "rank_relay.rkt",
}
_COUNTERFACTUAL = _HOME / "skip_rank.rkt"
_COLORS = (1, 2, 3, 4, 5, 6, 7)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DEMO_SPECS = (
    (10, 20, 3, 0),
    (12, 22, 4, 2),
    (14, 26, 5, 4),
    (16, 24, 4, 1),
    (18, 28, 5, 3),
    (20, 26, 4, 0),
)
_QUERY_SPECS = (
    (11, 21, 3, 2),
    (15, 25, 4, 3),
    (22, 29, 5, 1),
    (30, 30, 5, 4),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _mode(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"finish_mode"}
            or type(settings["finish_mode"]) is not str
            or settings["finish_mode"] not in _PROGRAMS):
        raise ValueError("settings must contain only finish_mode=rank_only|rank_relay")
    return settings["finish_mode"]


def program(settings: Any) -> str:
    return _PROGRAMS[_mode(settings)].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int, attempt: int) -> int:
    payload = f"{TASK_ID}|{seed}|{role}|{index}|{attempt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _partition(start: int, length: int, count: int) -> list[tuple[int, int]]:
    usable = length - (count - 1)
    if count < 1 or usable < 2 * count:
        raise ValueError("scene has insufficient room for separated component slots")
    base, remainder = divmod(usable, count)
    result = []
    cursor = start
    for index in range(count):
        size = base + (1 if index < remainder else 0)
        result.append((cursor, size))
        cursor += size + 1
    return result


def _grow(rng: random.Random, size: int, height: int, width: int) -> tuple[tuple[int, int], ...]:
    if not 1 <= size <= height * width:
        raise ValueError("shape size exceeds slot capacity")
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < size:
        frontier = {
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _CARDINAL
            if 0 <= r + dr < height and 0 <= c + dc < width
            and (r + dr, c + dc) not in cells
        }
        if not frontier:
            raise RuntimeError("connected-shape frontier exhausted")
        cells.add(rng.choice(sorted(frontier)))
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _slots(height: int, width: int, n: int) -> tuple[list[tuple[int, int, int, int]], list[int]]:
    swatch_start = width - (2 * n - 1)
    component_left = 2
    component_width = swatch_start - 3
    component_top = 2
    component_height = height - 4
    columns = n if n <= 3 else (n + 1) // 2
    rows = (n + columns - 1) // columns
    row_parts = _partition(component_top, component_height, rows)
    col_parts = _partition(component_left, component_width, columns)
    slots = [
        (top, left, slot_h, slot_w)
        for top, slot_h in row_parts
        for left, slot_w in col_parts
    ][:n]
    swatches = [swatch_start + 2 * index for index in range(n)]
    if max(swatches) >= width:
        raise AssertionError("swatch layout escaped grid")
    return slots, swatches


def _components(grid: list[list[int]], color: int = 8) -> list[set[tuple[int, int]]]:
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    groups = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        group = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                cell = r + dr, c + dc
                if cell in unseen:
                    unseen.remove(cell)
                    group.add(cell)
                    stack.append(cell)
        groups.append(group)
    return groups


def _bbox(group: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in group),
        min(c for _, c in group),
        max(r for r, _ in group),
        max(c for _, c in group),
    )


def _palette(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[0] if value != 0]


def _scene(seed: int, role: str, index: int, spec: tuple[int, int, int, int], attempt: int) -> list[list[int]]:
    height, width, n, target_rank = spec
    rng = random.Random(_mix_seed(seed, role, index, attempt))
    slots, swatch_columns = _slots(height, width, n)
    min_capacity = min(slot_h * slot_w for _, _, slot_h, slot_w in slots)
    step = max(1, (min_capacity - 2) // n)
    sizes = [2 + step * rank for rank in range(n)]
    if sizes[-1] > min_capacity:
        raise AssertionError("size schedule exceeds a slot")
    remaining_sizes = [size for rank, size in enumerate(sizes) if rank != target_rank]
    rng.shuffle(remaining_sizes)
    assigned_sizes = [sizes[target_rank], *remaining_sizes]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    placed: list[set[tuple[int, int]]] = []
    for (top, left, slot_h, slot_w), size in zip(slots, assigned_sizes):
        shape = _grow(rng, size, slot_h, slot_w)
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        row_offset = rng.randrange(slot_h - shape_h + 1)
        col_offset = rng.randrange(slot_w - shape_w + 1)
        cells = {(top + row_offset + r, left + col_offset + c) for r, c in shape}
        for r, c in cells:
            grid[r][c] = 8
        placed.append(cells)

    target = placed[0]
    target_left = min(c for _, c in target)
    marker_row = min(r for r, c in target if c == target_left)
    grid[marker_row][0] = 9

    palette = rng.sample(list(_COLORS), n)
    rng.shuffle(palette)
    header_columns = sorted(rng.sample(range(width), n))
    for column, color in zip(header_columns, palette):
        grid[0][column] = color

    swatch_palette = palette[:]
    rng.shuffle(swatch_palette)
    for column, color in zip(swatch_columns, swatch_palette):
        grid[-1][column] = color

    _validate_input(grid, expected_n=n)
    intermediate = relay_intermediate(grid)
    if intermediate["hit_color"] != palette[target_rank]:
        raise AssertionError("selector did not target the requested size rank")
    return grid


def _validate_input(grid: list[list[int]], *, expected_n: int | None = None) -> None:
    if (type(grid) is not list or not 8 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 10 <= len(grid[0]) <= 30 or any(type(row) is not list
            or len(row) != len(grid[0]) or any(type(value) is not int or not 0 <= value <= 9
            for value in row) for row in grid)):
        raise ValueError("expected a rectangular exact-integer grid within 8..30 by 10..30")
    if any(grid[1]):
        raise ValueError("row 1 must be blank")
    palette = _palette(grid)
    if not 2 <= len(palette) <= 5 or len(set(palette)) != len(palette) or any(v in (8, 9) for v in palette):
        raise ValueError("row-0 palette must contain 2..5 distinct colors excluding 8 and 9")
    groups = _components(grid)
    if len(groups) != len(palette) or (expected_n is not None and len(groups) != expected_n):
        raise ValueError("palette/component count mismatch")
    if len({len(group) for group in groups}) != len(groups):
        raise ValueError("placeholder component sizes must be distinct")
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(markers) != 1 or markers[0][0] < 2:
        raise ValueError("expected one body selector marker of color 9")
    body_payload = [value for value in grid[-1] if value not in (0, 8, 9)]
    if sorted(body_payload) != sorted(palette):
        raise ValueError("bottom payload swatches must be a permutation of the palette")
    marker_row, marker_col = markers[0]
    hit = next((grid[marker_row][c] for c in range(marker_col + 1, len(grid[0])) if grid[marker_row][c] != 0), None)
    if hit != 8:
        raise ValueError("selector ray must first hit a placeholder component")
    for column, value in enumerate(grid[-1]):
        if value not in (0, 8, 9):
            if any(grid[row][column] != 0 for row in range(2, len(grid) - 1)):
                raise ValueError("payload swatch column must be a clear vertical corridor")


def rank_output(grid: list[list[int]]) -> list[list[int]]:
    _validate_input(grid)
    out = deepcopy(grid)
    groups = sorted(_components(grid), key=lambda group: (len(group), _bbox(group)))
    for color, group in zip(_palette(grid), groups):
        for row, column in group:
            out[row][column] = color
    return out


def relay_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    ranked = rank_output(grid)
    marker = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
    row, column = marker
    hit_column = next(c for c in range(column + 1, len(grid[0])) if ranked[row][c] != 0)
    hit_color = ranked[row][hit_column]
    swatches = [c for c, value in enumerate(grid[-1]) if value == hit_color]
    if len(swatches) != 1:
        raise ValueError("relay color must select exactly one remote swatch")
    return {
        "marker": [row, column],
        "hit": [row, hit_column],
        "hit_color": hit_color,
        "swatch_column": swatches[0],
        "ranked_grid": ranked,
    }


def _paint_column(grid: list[list[int]], column: int) -> list[list[int]]:
    out = deepcopy(grid)
    for row in range(2, len(out)):
        out[row][column] = 9
    return out


def relay_output(grid: list[list[int]]) -> list[list[int]]:
    intermediate = relay_intermediate(grid)
    return _paint_column(intermediate["ranked_grid"], intermediate["swatch_column"])


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    return rank_output(grid) if _mode(settings) == "rank_only" else relay_output(grid)


def _relay_for_color(grid: list[list[int]], color: int) -> list[list[int]]:
    ranked = rank_output(grid)
    columns = [c for c, value in enumerate(grid[-1]) if value == color]
    if len(columns) != 1:
        return ranked
    return _paint_column(ranked, columns[0])


def _rivals(grid: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    palette = _palette(grid)
    swatch_columns = [c for c, value in enumerate(grid[-1]) if value not in (0, 8, 9)]
    if mode == "rank_only":
        groups = sorted(_components(grid), key=lambda group: (-len(group), _bbox(group)))
        reverse = deepcopy(grid)
        for color, group in zip(palette, groups):
            for r, c in group:
                reverse[r][c] = color
        return {
            "rank_relay": relay_output(grid),
            "reverse_size_rank": reverse,
        }
    return {
        "rank_only": rank_output(grid),
        "fixed_leftmost_swatch": _paint_column(rank_output(grid), min(swatch_columns)),
        "fixed_rightmost_swatch": _paint_column(rank_output(grid), max(swatch_columns)),
        "smallest_component_payload": _relay_for_color(grid, palette[0]),
        "largest_component_payload": _relay_for_color(grid, palette[-1]),
        "marker_column": _paint_column(rank_output(grid), 0),
    }


def lesson_report(episode: dict[str, Any], settings: Any) -> dict[str, Any]:
    mode = _mode(settings)
    train = episode["train"]
    test = episode["test"]
    setting_survivors = [
        candidate["finish_mode"]
        for candidate in SETTINGS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    names = sorted(_rivals(train[0]["input"], mode))
    survivors = set(names)
    rejected_at: dict[str, int] = {}
    for index, pair in enumerate(train):
        for name, output in _rivals(pair["input"], mode).items():
            if output != pair["output"]:
                survivors.discard(name)
                rejected_at.setdefault(name, index)
    query_disagreements = {
        name: any(_rivals(pair["input"], mode)[name] != pair["output"] for pair in test)
        for name in names
    }
    harmful = sorted(name for name in survivors if query_disagreements[name])
    return {
        "setting_survivors": setting_survivors,
        "harmful_shortcut_survivors": harmful,
        "rejected_at_demo": rejected_at,
        "query_disagreements": query_disagreements,
    }


def _candidate_bank(seed: int, attempt: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_scene(seed, "demo", index, spec, attempt) for index, spec in enumerate(_DEMO_SPECS)]
    queries = [_scene(seed, "query", index, spec, attempt) for index, spec in enumerate(_QUERY_SPECS)]
    return demos, queries


def select_inputs(seed: Any) -> dict[str, list[dict[str, list[list[int]]]]]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    for attempt in range(128):
        demos, queries = _candidate_bank(seed, attempt)
        frozen = {repr(grid) for grid in demos + queries}
        if len(frozen) != len(demos) + len(queries):
            continue
        good = True
        for settings in SETTINGS:
            episode = {
                "train": [{"input": grid, "output": solve(grid, settings)} for grid in demos[:2]],
                "test": [{"input": grid, "output": solve(grid, settings)} for grid in queries],
            }
            report = lesson_report(episode, settings)
            if report["setting_survivors"] != [settings["finish_mode"]] or report["harmful_shortcut_survivors"]:
                good = False
                break
        if good:
            return {
                "train": [{"input": deepcopy(grid)} for grid in demos],
                "test": [{"input": deepcopy(grid)} for grid in queries],
            }
    raise RuntimeError("failed to construct a two-demo distinguishing matched-input bank")


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    selected = select_inputs(seed)
    train_inputs = [row["input"] for row in selected["train"][:demos]]
    test_inputs = [row["input"] for row in selected["test"][:queries]]
    chosen = {"finish_mode": mode}
    return {
        "train": [{"input": deepcopy(grid), "output": solve(grid, chosen)} for grid in train_inputs],
        "test": [{"input": deepcopy(grid), "output": solve(grid, chosen)} for grid in test_inputs],
        "program_solution": program(chosen),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def causal_case(grid: list[list[int]]) -> dict[str, Any]:
    intermediate = relay_intermediate(grid)
    output = relay_output(grid)
    counterfactual_output = deepcopy(grid)
    return {
        "input": deepcopy(grid),
        "settings": deepcopy(RANK_RELAY),
        "intermediate_value": {
            key: deepcopy(value)
            for key, value in intermediate.items()
            if key != "ranked_grid"
        },
        "program": program(RANK_RELAY),
        "output": output,
        "counterfactual_program": _COUNTERFACTUAL.read_text(encoding="utf-8"),
        "counterfactual_output": counterfactual_output,
        "ablation": "skip_a",
        "step_a": "Sort the color-8 components by occupied size and recolor them in row-0 palette order.",
        "intermediate": "The ranked grid, especially the palette color assigned to the first component hit by the color-9 selector ray.",
        "step_b": "Use that assigned hit color to select the matching remote bottom-row swatch, then paint its clear vertical payload corridor color 9.",
        "why_b_depends_on_a": "Before rank recoloring the first ray hit is still color 8, which has no remote swatch; the payload column cannot be selected until step A assigns the hit component's input-dependent palette color.",
    }
