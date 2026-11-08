"""Native matched-input parametric family for ``dbecc530afd0``.

``fill_only`` is the byte-exact canonical rectangle-interior fill.  The
``cue_selected_region`` setting performs that fill first, then uses a visible
color-3 edge cue to select one of the red components created by the fill and
recolors exactly that component color 8.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "dbecc530afd0"
PARAMETER = "finish"
SETTINGS = ("fill_only", "cue_selected_region")
DEFAULT = {PARAMETER: SETTINGS[0]}
MIN_DEMOS, MAX_DEMOS = 2, 6
MIN_QUERIES, MAX_QUERIES = 1, 4
MAX_SEED = 2**63 - 1
HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    SETTINGS[0]: HOME / "canonical.rkt",
    SETTINGS[1]: HOME / "cue_selected_region.rkt",
}
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# The first two demonstrations reverse both row-major selection and size rank.
TRAIN_PROFILES = (
    (14, 16, 0),
    (16, 18, 1),
    (18, 20, 0),
    (20, 22, 1),
    (22, 24, 0),
    (24, 26, 1),
)
QUERY_PROFILES = (
    (15, 19, 1),
    (19, 23, 0),
    (26, 28, 1),
    (30, 30, 0),
)


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: Any) -> str:
    return PROGRAM_FILES[_finish(settings)].read_text(encoding="utf-8")


def _grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(value[0])
    if len(value) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(value), width


def _components(value: list[list[int]], color: int) -> list[frozenset[tuple[int, int]]]:
    height, width = len(value), len(value[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if value[r][c] == color}
    result: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINALS:
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    cells.add(q)
                    stack.append(q)
        result.append(frozenset(cells))
    result.sort(key=min)
    return result


def _yellow_cells(value: list[list[int]]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(value) for c, cell in enumerate(row) if cell == 4}


def _all_rects(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    by_row: dict[int, set[int]] = {}
    for r, c in cells:
        by_row.setdefault(r, set()).add(c)
    rows = sorted(by_row)
    result: list[tuple[int, int, int, int]] = []
    for index, r1 in enumerate(rows):
        for r2 in rows[index + 1:]:
            common = sorted(by_row[r1] & by_row[r2])
            for left_index, c1 in enumerate(common):
                for c2 in common[left_index + 1:]:
                    result.append((r1, r2, c1, c2))
    return result


def canonical_intermediate(value: Any) -> list[list[int]]:
    _grid(value)
    rectangles = _all_rects(_yellow_cells(value))
    if len(rectangles) != 2:
        raise ValueError(f"scene must contain exactly two complete rectangles, found {len(rectangles)}")
    out = deepcopy(value)
    for r1, r2, c1, c2 in rectangles:
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                out[r][c] = 2
    return out


def _cue(value: list[list[int]]) -> tuple[int, int]:
    cues = [(r, c) for r, row in enumerate(value) for c, cell in enumerate(row) if cell == 3]
    if len(cues) != 1:
        raise ValueError("scene must contain exactly one color-3 cue")
    return cues[0]


def _touches(cells: Iterable[tuple[int, int]], point: tuple[int, int]) -> bool:
    pr, pc = point
    return any(abs(r - pr) + abs(c - pc) == 1 for r, c in cells)


def _selected(value: list[list[int]]) -> tuple[list[frozenset[tuple[int, int]]], int]:
    reds = _components(value, 2)
    cue = _cue(value)
    indices = [index for index, cells in enumerate(reds) if _touches(cells, cue)]
    if len(indices) != 1:
        raise ValueError("cue must touch exactly one red component")
    return reds, indices[0]


def _paint(value: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = deepcopy(value)
    for r, c in cells:
        out[r][c] = color
    return out


def solve(value: Any, settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    intermediate = canonical_intermediate(value)
    if finish == SETTINGS[0]:
        return intermediate
    reds, index = _selected(intermediate)
    return _paint(intermediate, reds[index], 8)


def skip_fill_solve(value: Any) -> list[list[int]]:
    """Causal ablation: skip the rectangle-fill intermediate entirely."""
    _grid(value)
    return deepcopy(value)


def _selector_output(value: Any, selector: str) -> list[list[int]]:
    intermediate = canonical_intermediate(value)
    reds = _components(intermediate, 2)
    if selector == "first":
        target = reds[0]
    elif selector == "last":
        target = reds[-1]
    elif selector == "largest":
        target = sorted(reds, key=lambda cells: (-len(cells), min(cells)))[0]
    elif selector == "smallest":
        target = sorted(reds, key=lambda cells: (len(cells), min(cells)))[0]
    elif selector == "all":
        return [[8 if cell == 2 else cell for cell in row] for row in intermediate]
    else:
        raise ValueError(selector)
    return _paint(intermediate, target, 8)


def rival_outputs(value: Any, settings: Any) -> dict[str, list[list[int]]]:
    chosen = _finish(settings)
    result = {"other_setting": solve(value, {PARAMETER: SETTINGS[1] if chosen == SETTINGS[0] else SETTINGS[0]})}
    if chosen == SETTINGS[1]:
        for selector in ("first", "last", "largest", "smallest", "all"):
            result[selector] = _selector_output(value, selector)
        result["skip_fill"] = skip_fill_solve(value)
    return result


def dependency_trace(value: Any) -> dict[str, Any]:
    intermediate = canonical_intermediate(value)
    reds, index = _selected(intermediate)
    sizes = [len(cells) for cells in reds]
    selected_size = sizes[index]
    return {
        "red_component_count": len(reds),
        "cue_touching_component_count": sum(_touches(cells, _cue(intermediate)) for cells in reds),
        "selected_order": index,
        "selected_is_largest": selected_size == max(sizes) and sizes.count(selected_size) == 1,
        "selected_size": selected_size,
        "unselected_size": sizes[1 - index],
        "component_sizes": sizes,
    }


def _draw_rect(grid: list[list[int]], rect: tuple[int, int, int, int]) -> None:
    r1, r2, c1, c2 = rect
    for r, c in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
        grid[r][c] = 4


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    _exact_int("index", index, 0, len(profiles) - 1)
    height, width, selected_order = profiles[index]
    left_end = width // 2 - 2
    right_start = left_end + 3
    left = (0, height - 1, 0, left_end)
    right = (1, height - 2, right_start, width - 1)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    _draw_rect(grid, left)
    _draw_rect(grid, right)
    selected = left if selected_order == 0 else right
    r1, r2, c1, c2 = selected
    cue_col = (c1 + c2) // 2
    # Alternate top/bottom edge to exercise boundary orientation without
    # changing which post-fill component is selected.
    bottom = bool((seed + index + (0 if split == "train" else 7)) & 1)
    cue_row = r2 if bottom else r1
    grid[cue_row][cue_col] = 3

    trace = dependency_trace(grid)
    if trace["red_component_count"] != 2 or trace["cue_touching_component_count"] != 1:
        raise RuntimeError(f"cue-selected construction failed: {trace}")
    if trace["selected_order"] != selected_order:
        raise RuntimeError(f"selected order changed: {trace}")
    if solve(grid, {PARAMETER: SETTINGS[1]}) == skip_fill_solve(grid):
        raise RuntimeError("skip-fill ablation did not change the final output")
    return grid


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a training list")
    train = episode["train"]
    settings = episode.get("settings")
    names = sorted({name for pair in train for name in rival_outputs(pair["input"], settings)})
    survivors = [
        name for name in names
        if all(rival_outputs(pair["input"], settings).get(name) == pair["output"] for pair in train)
    ]
    return {
        "status": "identified" if not survivors else "ambiguous",
        "surviving_rivals": survivors,
        "demonstrations": len(train),
    }


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int("seed", seed, 0, MAX_SEED)
    _finish(settings)
    _exact_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _exact_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        {"input": (grid := sample_input(seed, "train", index)), "output": solve(grid, settings)}
        for index in range(demos)
    ]
    test = [
        {"input": (grid := sample_input(seed, "test", index)), "output": solve(grid, settings)}
        for index in range(queries)
    ]
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "sampling": {"draws": demos + queries, "duplicate_rejections": 0},
    }
    episode["teaching"] = teaching_check(episode)
    if episode["teaching"]["surviving_rivals"]:
        raise RuntimeError("declared teaching rivals survived: " + ", ".join(episode["teaching"]["surviving_rivals"]))
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _exact_int("query_index", query_index, 0, len(test) - 1)
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }


__all__ = [
    "DEFAULT", "SETTINGS", "canonical_intermediate", "dependency_trace", "generate",
    "program", "public_turn", "rival_outputs", "sample_input", "skip_fill_solve", "solve",
    "teaching_check",
]
