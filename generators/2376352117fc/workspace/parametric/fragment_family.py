"""Matched-input parametric family for ARC task ``2376352117fc``.

``translate_only`` is the exact selected canonical vector-translation rule.
``largest_visible_fragment`` first performs that translation with clipping,
then recomputes the four-connected visible fragments and recolors only the
unique largest fragment yellow.  The source is a connected U: its bridge is
translated just beyond one boundary, so clipping creates two fragments that
do not exist as separate objects before stage A.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "2376352117fc"
PARAMETER = "finish"
SETTINGS = ("translate_only", "largest_visible_fragment")
DEFAULT = {PARAMETER: SETTINGS[0]}
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1
HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    SETTINGS[0]: HOME / "canonical.rkt",
    SETTINGS[1]: HOME / "largest_visible_fragment.rkt",
}
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# h, w, clipped side, bridge offset, bridge span, endpoint leg A, endpoint leg B
TRAIN_PROFILES = (
    (12, 14, "top", 3, 7, 3, 5),
    (14, 12, "left", 3, 7, 6, 3),
    (16, 17, "bottom", 4, 9, 4, 7),
    (18, 16, "right", 4, 9, 8, 5),
    (22, 24, "top", 5, 12, 7, 10),
    (24, 22, "left", 5, 12, 11, 7),
)
QUERY_PROFILES = (
    (16, 18, "bottom", 4, 9, 5, 8),
    (18, 20, "right", 4, 10, 9, 5),
    (24, 26, "top", 5, 14, 8, 11),
    (30, 30, "left", 6, 20, 14, 10),
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
        or any(type(cell) is not int or cell not in (0, 1, 2, 3) for cell in row)
        for row in value
    ):
        raise ValueError("input must be rectangular with exact integer colors 0,1,2,3")
    return len(value), width


def _positions(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _components_from_cells(cells: Iterable[tuple[int, int]]) -> list[frozenset[tuple[int, int]]]:
    remaining = set(cells)
    result: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINALS:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(frozenset(component))
    result.sort(key=lambda component: min(component))
    return result


def analyze(value: Any) -> dict[str, Any]:
    h, w = _grid(value)
    one = sorted(_positions(value, 1))
    two = sorted(_positions(value, 2))
    source = _positions(value, 3)
    if len(one) != 1 or len(two) != 1:
        raise ValueError("scene must contain exactly one color-1 and color-2 marker")
    if not source or len(_components_from_cells(source)) != 1:
        raise ValueError("color-3 source must be one four-connected object")
    dr = two[0][0] - one[0][0]
    dc = two[0][1] - one[0][1]
    if dr == 0 and dc == 0:
        raise ValueError("translation vector must be nonzero")
    targets = {(r + dr, c + dc) for r, c in source if 0 <= r + dr < h and 0 <= c + dc < w}
    if not targets:
        raise ValueError("translation must leave at least one visible target cell")
    return {"height": h, "width": w, "p1": one[0], "p2": two[0], "dr": dr, "dc": dc, "source": source, "targets": targets}


def canonical_intermediate(value: Any) -> list[list[int]]:
    scene = analyze(value)
    out = [[0 for _ in range(scene["width"])] for _ in range(scene["height"])]
    for r, c in scene["targets"]:
        out[r][c] = 8
    return out


def _visible_components(value: Any) -> list[frozenset[tuple[int, int]]]:
    return _components_from_cells(_positions(canonical_intermediate(value), 8))


def _select(components: list[frozenset[tuple[int, int]]], mode: str) -> frozenset[tuple[int, int]]:
    if not components:
        raise ValueError("visible translation has no component")
    if mode == "largest":
        ordered = sorted(components, key=lambda cells: (-len(cells), min(cells)))
        if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
            raise ValueError("largest visible fragment must be unique")
        return ordered[0]
    if mode == "smallest":
        ordered = sorted(components, key=lambda cells: (len(cells), min(cells)))
        return ordered[0]
    if mode == "first":
        return components[0]
    if mode == "last":
        return components[-1]
    raise ValueError(mode)


def _recolor_selected(intermediate: list[list[int]], selected: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = deepcopy(intermediate)
    for r, c in selected:
        out[r][c] = 4
    return out


def solve(value: Any, settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    intermediate = canonical_intermediate(value)
    if finish == SETTINGS[0]:
        return intermediate
    return _recolor_selected(intermediate, _select(_components_from_cells(_positions(intermediate, 8)), "largest"))


def wrong_order_solve(value: Any) -> list[list[int]]:
    """Counterfactual: select the connected source before clipping splits it."""
    intermediate = canonical_intermediate(value)
    return [[4 if cell == 8 else cell for cell in row] for row in intermediate]


def _fragment_rival(value: Any, mode: str) -> list[list[int]]:
    intermediate = canonical_intermediate(value)
    components = _components_from_cells(_positions(intermediate, 8))
    return _recolor_selected(intermediate, _select(components, mode))


def _reverse_vector(value: Any, settings: Any) -> list[list[int]]:
    scene = analyze(value)
    out = [[0 for _ in range(scene["width"])] for _ in range(scene["height"])]
    for r, c in scene["source"]:
        rr, cc = r - scene["dr"], c - scene["dc"]
        if 0 <= rr < scene["height"] and 0 <= cc < scene["width"]:
            out[rr][cc] = 8
    if _finish(settings) == SETTINGS[0]:
        return out
    components = _components_from_cells(_positions(out, 8))
    if not components:
        return out
    selected = sorted(components, key=lambda cells: (-len(cells), min(cells)))[0]
    return _recolor_selected(out, selected)


def rival_outputs(value: Any, settings: Any) -> dict[str, list[list[int]]]:
    finish = _finish(settings)
    other = SETTINGS[1] if finish == SETTINGS[0] else SETTINGS[0]
    return {
        "other_setting": solve(value, {PARAMETER: other}),
        "select_before_clipping": wrong_order_solve(value),
        "first_visible_fragment": _fragment_rival(value, "first"),
        "last_visible_fragment": _fragment_rival(value, "last"),
        "smallest_visible_fragment": _fragment_rival(value, "smallest"),
        "reverse_vector": _reverse_vector(value, settings),
    }


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _finish(settings)
    train = episode.get("train")
    if type(train) is not list or not MIN_DEMOS <= len(train) <= MAX_DEMOS:
        raise ValueError("episode must contain two through six demonstrations")
    per_demo = []
    names: set[str] = set()
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations require input/output")
        if solve(pair["input"], settings) != pair["output"]:
            raise ValueError("demonstration label differs from selected rule")
        outputs = rival_outputs(pair["input"], settings)
        per_demo.append(outputs)
        names.update(outputs)
    survivors = sorted(
        name for name in names
        if all(outputs[name] == pair["output"] for outputs, pair in zip(per_demo, train, strict=True))
    )
    return {
        "status": "identified" if not survivors else "ambiguous",
        "surviving_rivals": survivors,
        "demonstrations": len(train),
        "used_query_answers": False,
        "limits": "Finite named rivals fitted to demonstrations only; not universal uniqueness.",
    }


def dependency_trace(value: Any, settings: Any) -> dict[str, Any]:
    finish = _finish(settings)
    scene = analyze(value)
    intermediate = canonical_intermediate(value)
    components = _components_from_cells(_positions(intermediate, 8))
    sizes = sorted((len(cells) for cells in components), reverse=True)
    return {
        "setting": {PARAMETER: finish},
        "step_a": "translate every green source cell by the marker vector and clip out-of-bounds targets",
        "intermediate": intermediate,
        "step_b": "recompute visible four-connected fragments and recolor only the unique largest fragment yellow",
        "why_b_depends_on_a": "the connected U source becomes two disconnected visible fragments only when stage A translates its bridge beyond the boundary",
        "vector": [scene["dr"], scene["dc"]],
        "visible_components": len(components),
        "largest_visible_cells": sizes[0],
        "smallest_visible_cells": sizes[-1],
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|visible-fragment-v2|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _profile_grid(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    h, w, side, offset, span, leg_a, leg_b = profiles[index]
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    source: set[tuple[int, int]] = set()

    if side in ("top", "bottom"):
        available = w - span - 4
        start = 2 + (rng.randrange(available + 1) if available >= 0 else 0)
        marker_col = 0 if rng.randrange(2) == 0 else w - 1
        if side == "top":
            bridge = offset
            source.update((bridge, c) for c in range(start, start + span))
            source.update((r, start) for r in range(bridge + 1, bridge + leg_a + 1))
            source.update((r, start + span - 1) for r in range(bridge + 1, bridge + leg_b + 1))
            p1 = (h - 1, marker_col)
            p2 = (h - 1 - (offset + 1), marker_col)
        else:
            bridge = h - 1 - offset
            source.update((bridge, c) for c in range(start, start + span))
            source.update((r, start) for r in range(bridge - 1, bridge - leg_a - 1, -1))
            source.update((r, start + span - 1) for r in range(bridge - 1, bridge - leg_b - 1, -1))
            p1 = (0, marker_col)
            p2 = (offset + 1, marker_col)
    else:
        available = h - span - 4
        start = 2 + (rng.randrange(available + 1) if available >= 0 else 0)
        marker_row = 0 if rng.randrange(2) == 0 else h - 1
        if side == "left":
            bridge = offset
            source.update((r, bridge) for r in range(start, start + span))
            source.update((start, c) for c in range(bridge + 1, bridge + leg_a + 1))
            source.update((start + span - 1, c) for c in range(bridge + 1, bridge + leg_b + 1))
            p1 = (marker_row, w - 1)
            p2 = (marker_row, w - 1 - (offset + 1))
        else:
            bridge = w - 1 - offset
            source.update((r, bridge) for r in range(start, start + span))
            source.update((start, c) for c in range(bridge - 1, bridge - leg_a - 1, -1))
            source.update((start + span - 1, c) for c in range(bridge - 1, bridge - leg_b - 1, -1))
            p1 = (marker_row, 0)
            p2 = (marker_row, offset + 1)

    if p1 in source or p2 in source or p1 == p2:
        raise RuntimeError("marker/source collision")
    for r, c in source:
        if not (0 <= r < h and 0 <= c < w):
            raise RuntimeError("profile source escaped grid")
        grid[r][c] = 3
    grid[p1[0]][p1[1]] = 1
    grid[p2[0]][p2[1]] = 2

    scene = analyze(grid)
    visible = _components_from_cells(scene["targets"])
    if len(visible) != 2 or len(visible[0]) == len(visible[1]):
        raise RuntimeError(f"profile did not create two unequal visible fragments: {list(map(len, visible))}")
    return grid


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    _exact_int("index", index, 0, len(profiles) - 1)
    return _profile_grid(seed, split, index)


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
    certificate = teaching_check(episode)
    if certificate["surviving_rivals"]:
        raise RuntimeError("constructed demonstrations leave declared rivals alive: " + ", ".join(certificate["surviving_rivals"]))
    episode["teaching"] = certificate
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _exact_int("query_index", query_index, 0, len(test) - 1)
    query = {"input": deepcopy(test[query_index]["input"])}
    if query_index == 0:
        return {
            "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
            "test": [query],
        }
    return {"test": [query]}


__all__ = [
    "DEFAULT", "SETTINGS", "analyze", "canonical_intermediate", "dependency_trace",
    "generate", "program", "public_turn", "rival_outputs", "sample_input", "solve",
    "teaching_check", "wrong_order_solve",
]
