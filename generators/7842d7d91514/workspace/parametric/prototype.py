"""Native two-setting parametric family for ARC task 7842d7d91514.

The canonical setting keeps the accepted rule byte-for-byte: compare every
color-2 candidate with the translation-normalized color-5 template in its
original orientation.  The nearby setting adds a visible color-8 selector and
uses its cell count to derive an intermediate rotation (2 cells -> clockwise,
4 cells -> counterclockwise) before candidate matching.  Inputs are sampled
without consulting the hidden setting.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from itertools import combinations
from pathlib import Path
from typing import Callable, Iterable, Sequence

TASK_ID = "7842d7d91514"
PARAMETERS = {"target_rule": ("exact", "selector_rotation")}
DEFAULT_SETTINGS = {"target_rule": "exact"}

# (height, width, candidate_count, template_size, selector_size)
DEMO_PROFILES = (
    (11, 12, 4, 4, 2),
    (12, 13, 5, 5, 4),
    (13, 15, 6, 6, 2),
    (14, 16, 7, 5, 4),
    (17, 19, 9, 6, 2),
    (20, 22, 12, 6, 4),
)
QUERY_PROFILES = (
    (13, 15, 6, 5, 2),
    (18, 22, 10, 6, 4),
    (24, 27, 14, 6, 2),
    (30, 30, 20, 6, 4),
)

Grid = list[list[int]]
Shape = tuple[tuple[int, int], ...]
Settings = dict[str, str]
_NEIGHBORS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: object) -> Settings:
    if type(settings) is not dict or set(settings) != {"target_rule"}:
        raise ValueError("settings must contain exactly target_rule")
    value = settings["target_rule"]
    if type(value) is not str or value not in PARAMETERS["target_rule"]:
        raise ValueError("target_rule must be exact or selector_rotation")
    return {"target_rule": value}


def settings_space() -> list[Settings]:
    return [{"target_rule": value} for value in PARAMETERS["target_rule"]]


def _selector_program() -> str:
    return """(rule! (lambda (grid)
  (define (shape-grid obj)
    (recolor
      (crop-to-content
        (subgrid (keep-only grid (obj-color obj))
                 (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
      (obj-color obj) 1))
  (define (rotate-n g turns)
    (if (= turns 0) g (rotate-n (rotate-cw g) (- turns 1))))
  (let* ((objects-list (objects grid 0))
         (template (first (filter (lambda (obj) (= (obj-color obj) 5)) objects-list)))
         (selector (first (filter (lambda (obj) (= (obj-color obj) 8)) objects-list)))
         (selector-count (length (obj-cells selector)))
         (quarter-turns (if (= selector-count 2) 1 3))
         (template-shape (rotate-n (shape-grid template) quarter-turns)))
    (reduce (lambda (acc obj)
      (if (= (obj-color obj) 2)
          (recolor-cells acc (obj-cells obj)
            (if (= (shape-grid obj) template-shape) 4 1))
          acc))
      grid objects-list))))"""


def program(settings: object) -> str:
    setting = normalize_settings(settings)
    if setting == DEFAULT_SETTINGS:
        return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    return _selector_program()


def _validate_grid(grid: object) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have dimensions in 1..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _connected(shape: Sequence[tuple[int, int]]) -> bool:
    points = set(shape)
    if not points:
        return False
    start = next(iter(points))
    seen = {start}
    pending = [start]
    while pending:
        row, col = pending.pop()
        for dr, dc in _NEIGHBORS:
            point = (row + dr, col + dc)
            if point in points and point not in seen:
                seen.add(point)
                pending.append(point)
    return seen == points


def _rotate_cw(shape: Iterable[tuple[int, int]]) -> Shape:
    normalized = _normalize(shape)
    if not normalized:
        return ()
    height = max(row for row, _ in normalized) + 1
    return _normalize((col, height - 1 - row) for row, col in normalized)


def _rotate_n(shape: Iterable[tuple[int, int]], turns: int) -> Shape:
    result = _normalize(shape)
    for _ in range(turns % 4):
        result = _rotate_cw(result)
    return result


def _reflect_lr(shape: Iterable[tuple[int, int]]) -> Shape:
    normalized = _normalize(shape)
    if not normalized:
        return ()
    width = max(col for _, col in normalized) + 1
    return _normalize((row, width - 1 - col) for row, col in normalized)


def _rotations(shape: Iterable[tuple[int, int]]) -> tuple[Shape, ...]:
    result: list[Shape] = []
    current = _normalize(shape)
    for _ in range(4):
        result.append(current)
        current = _rotate_cw(current)
    return tuple(result)


def _dihedral(shape: Iterable[tuple[int, int]]) -> tuple[Shape, ...]:
    rotations = _rotations(shape)
    return tuple(sorted(set(rotations) | {_reflect_lr(item) for item in rotations}))


def _shape_banks() -> tuple[dict[int, tuple[Shape, ...]], dict[int, tuple[Shape, ...]]]:
    cells = tuple((row, col) for row in range(3) for col in range(3))
    all_shapes: dict[int, tuple[Shape, ...]] = {}
    chiral: dict[int, tuple[Shape, ...]] = {}
    for size in range(4, 8):
        shapes = tuple(
            sorted(
                {
                    _normalize(candidate)
                    for candidate in combinations(cells, size)
                    if _connected(candidate)
                }
            )
        )
        chiral_shapes = tuple(
            shape
            for shape in shapes
            if len(set(_rotations(shape))) == 4 and len(_dihedral(shape)) == 8
        )
        if len(chiral_shapes) < 4:
            raise RuntimeError(f"chiral shape bank for size {size} is too small")
        all_shapes[size] = shapes
        chiral[size] = chiral_shapes
    return all_shapes, chiral


_ALL_SHAPES, _CHIRAL_SHAPES = _shape_banks()


def _components(grid: Grid, color: int) -> list[list[tuple[int, int]]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            pending = [(r0, c0)]
            seen.add((r0, c0))
            component: list[tuple[int, int]] = []
            while pending:
                row, col = pending.pop()
                component.append((row, col))
                for dr, dc in _NEIGHBORS:
                    point = (row + dr, col + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        pending.append(point)
            result.append(sorted(component))
    return result


def _scene_parts(grid: Grid) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[list[tuple[int, int]]]]:
    templates = _components(grid, 5)
    selectors = _components(grid, 8)
    candidates = _components(grid, 2)
    if len(templates) != 1 or len(selectors) != 1 or not candidates:
        raise ValueError("scene needs one color-5 template, one color-8 selector, and candidates")
    if len(selectors[0]) not in {2, 4}:
        raise ValueError("selector must contain exactly 2 or 4 connected cells")
    return templates[0], selectors[0], candidates


def _recolor_candidates(
    grid: Grid,
    predicate: Callable[[list[tuple[int, int]]], bool],
) -> Grid:
    result = copy.deepcopy(grid)
    for component in _components(grid, 2):
        color = 4 if predicate(component) else 1
        for row, col in component:
            result[row][col] = color
    return result


def transform_with_turns(grid: Grid, turns: int) -> Grid:
    _integer(turns, 0, 3, "quarter turns")
    template, _, _ = _scene_parts(grid)
    target = _rotate_n(template, turns)
    return _recolor_candidates(grid, lambda component: _normalize(component) == target)


def transform(grid: Grid, settings: object) -> Grid:
    setting = normalize_settings(settings)
    _, selector, _ = _scene_parts(grid)
    if setting["target_rule"] == "exact":
        turns = 0
    else:
        turns = 1 if len(selector) == 2 else 3
    return transform_with_turns(grid, turns)


def causal_trace(grid: Grid) -> dict[str, object]:
    template, selector, _ = _scene_parts(grid)
    turns = 1 if len(selector) == 2 else 3
    template_shape = _normalize(template)
    target = _rotate_n(template_shape, turns)
    return {
        "step_a": "count the connected color-8 selector",
        "selector_cells": len(selector),
        "quarter_turns": turns,
        "intermediate": "clockwise" if turns == 1 else "counterclockwise",
        "step_b": "rotate the normalized color-5 template, then exact-match color-2 candidates",
        "template_shape": [list(point) for point in template_shape],
        "target_shape": [list(point) for point in target],
    }


def _all_candidates(grid: Grid, color: int) -> Grid:
    return _recolor_candidates(grid, lambda _component: color == 4)


def _dihedral_output(grid: Grid) -> Grid:
    template, _, _ = _scene_parts(grid)
    orbit = set(_dihedral(template))
    return _recolor_candidates(grid, lambda component: _normalize(component) in orbit)


def _same_cell_count_output(grid: Grid) -> Grid:
    template, _, _ = _scene_parts(grid)
    size = len(template)
    return _recolor_candidates(grid, lambda component: len(component) == size)


def _topmost_output(grid: Grid) -> Grid:
    _, _, candidates = _scene_parts(grid)
    chosen = min(candidates, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    chosen_set = set(chosen)
    return _recolor_candidates(grid, lambda component: set(component) == chosen_set)


def shortcut_outputs(grid: Grid, settings: object) -> dict[str, Grid]:
    """Finite plausible wrong rules fitted on demonstrations only."""
    normalize_settings(settings)
    _, selector, _ = _scene_parts(grid)
    reversed_turns = 3 if len(selector) == 2 else 1
    return {
        "identity": copy.deepcopy(grid),
        "all_candidates_yellow": _all_candidates(grid, 4),
        "all_candidates_blue": _all_candidates(grid, 1),
        "same_cell_count": _same_cell_count_output(grid),
        "dihedral_match": _dihedral_output(grid),
        "fixed_clockwise": transform_with_turns(grid, 1),
        "fixed_counterclockwise": transform_with_turns(grid, 3),
        "fixed_half_turn": transform_with_turns(grid, 2),
        "reversed_selector_mapping": transform_with_turns(grid, reversed_turns),
        "topmost_candidate_only": _topmost_output(grid),
    }


def _rng(seed: int, stream: str, index: int) -> random.Random:
    payload = json.dumps(
        [TASK_ID, "selector-rotation-input-v1", seed, stream, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _blank(height: int, width: int) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def _axis_origins(length: int) -> list[int]:
    if length < 3:
        raise ValueError("slot axis must be at least 3")
    boundary = length - 3
    result = list(range(0, boundary + 1, 4))
    if result[-1] != boundary:
        if boundary - result[-1] < 4:
            result[-1] = boundary
        else:
            result.append(boundary)
    if any(b - a < 4 for a, b in zip(result, result[1:])):
        raise AssertionError(f"overlapping slot axis for length {length}: {result}")
    return result


def _slots(height: int, width: int) -> list[tuple[int, int]]:
    return [(row, col) for row in _axis_origins(height) for col in _axis_origins(width)]


def _shape_extent(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _paint_shape(
    grid: Grid,
    shape: Shape,
    color: int,
    slot: tuple[int, int],
    rng: random.Random,
    *,
    touch: frozenset[str] = frozenset(),
) -> None:
    height, width = len(grid), len(grid[0])
    shape = _normalize(shape)
    shape_h, shape_w = _shape_extent(shape)
    max_dr, max_dc = 3 - shape_h, 3 - shape_w
    dr = rng.randrange(max_dr + 1)
    dc = rng.randrange(max_dc + 1)
    if "top" in touch:
        dr = 0
    if "bottom" in touch:
        dr = max_dr
    if "left" in touch:
        dc = 0
    if "right" in touch:
        dc = max_dc
    for row, col in shape:
        point = (slot[0] + dr + row, slot[1] + dc + col)
        if not (0 <= point[0] < height and 0 <= point[1] < width):
            raise AssertionError(f"shape outside {height}x{width}: {point}")
        if grid[point[0]][point[1]] != 0:
            raise AssertionError(f"scene overlap at {point}")
        grid[point[0]][point[1]] = color


def _selector_shape(size: int, rng: random.Random) -> Shape:
    if size == 2:
        shape: Shape = ((0, 0), (0, 1))
    elif size == 4:
        shape = ((0, 0), (1, 0), (1, 1), (1, 2))
    else:
        raise ValueError("selector size must be 2 or 4")
    return _rotate_n(shape, rng.randrange(4))


def _candidate_shapes(template: Shape, count: int, rng: random.Random) -> list[Shape]:
    size = len(template)
    required = list(_rotations(template))
    reflected = [_reflect_lr(shape) for shape in required]
    ordered: list[Shape] = []
    for shape in required + reflected:
        if shape not in ordered:
            ordered.append(shape)
    extras = [shape for shape in _ALL_SHAPES[size] if shape not in ordered]
    rng.shuffle(extras)
    ordered.extend(extras)
    if count > len(ordered):
        raise ValueError(f"only {len(ordered)} distinct candidate shapes available")
    chosen = ordered[:count]
    rng.shuffle(chosen)
    return chosen


def _reserve_roles(
    height: int,
    width: int,
    slots: list[tuple[int, int]],
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int], list[tuple[int, int]]]:
    center = ((height - 3) / 2, (width - 3) / 2)
    ordered = sorted(
        slots,
        key=lambda slot: (
            abs(slot[0] - center[0]) + abs(slot[1] - center[1]),
            slot,
        ),
    )
    template_slot = ordered[0]
    selector_slot = ordered[1]
    candidates = [slot for slot in slots if slot not in {template_slot, selector_slot}]
    rng.shuffle(candidates)
    return template_slot, selector_slot, candidates


def _edge_slots(
    height: int,
    width: int,
    slots: list[tuple[int, int]],
) -> list[tuple[tuple[int, int], frozenset[str]]]:
    conditions = (
        (lambda slot: slot[0] == 0, frozenset({"top"})),
        (lambda slot: slot[0] == height - 3, frozenset({"bottom"})),
        (lambda slot: slot[1] == 0, frozenset({"left"})),
        (lambda slot: slot[1] == width - 3, frozenset({"right"})),
    )
    selected: list[tuple[tuple[int, int], frozenset[str]]] = []
    used: set[tuple[int, int]] = set()
    for predicate, touch in conditions:
        choices = [slot for slot in slots if predicate(slot) and slot not in used]
        if not choices:
            raise AssertionError("unable to reserve distinct edge slots")
        slot = min(choices)
        selected.append((slot, touch))
        used.add(slot)
    return selected


def _build_scene(
    seed: int,
    stream: str,
    index: int,
    profile: tuple[int, int, int, int, int],
    *,
    force_edges: bool,
) -> Grid:
    height, width, candidate_count, shape_size, selector_size = profile
    rng = _rng(seed, stream, index)
    grid = _blank(height, width)
    all_slots = _slots(height, width)
    if candidate_count + 2 > len(all_slots):
        raise ValueError("profile requests more objects than isolated slots")
    template_slot, selector_slot, candidate_slots = _reserve_roles(height, width, all_slots, rng)

    template = rng.choice(_CHIRAL_SHAPES[shape_size])
    candidates = _candidate_shapes(template, candidate_count, rng)

    # The topmost candidate is deliberately a half-turn, defeating a stable
    # location shortcut for both declared targets (identity and +/-90 degrees).
    topmost_slot = min(candidate_slots[:candidate_count])
    half_turn = _rotate_n(template, 2)
    half_index = candidates.index(half_turn)
    top_index = candidate_slots[:candidate_count].index(topmost_slot)
    candidates[half_index], candidates[top_index] = candidates[top_index], candidates[half_index]

    touch_by_slot: dict[tuple[int, int], frozenset[str]] = {}
    if force_edges:
        available = [slot for slot in candidate_slots if slot not in {template_slot, selector_slot}]
        edges = _edge_slots(height, width, available)
        edge_only = [slot for slot, _ in edges]
        remaining = [slot for slot in candidate_slots if slot not in edge_only]
        candidate_slots = edge_only + remaining
        touch_by_slot.update(edges)
        # Reassert the topmost rival witness after edge slots are promoted.
        topmost_slot = min(candidate_slots[:candidate_count])
        half_index = candidates.index(half_turn)
        top_index = candidate_slots[:candidate_count].index(topmost_slot)
        candidates[half_index], candidates[top_index] = candidates[top_index], candidates[half_index]

    _paint_shape(grid, template, 5, template_slot, rng)
    _paint_shape(grid, _selector_shape(selector_size, rng), 8, selector_slot, rng)
    for shape, slot in zip(candidates, candidate_slots[:candidate_count]):
        _paint_shape(grid, shape, 2, slot, rng, touch=touch_by_slot.get(slot, frozenset()))
    return grid


def sample_inputs(seed: int, demos: int, queries: int) -> dict[str, list[Grid]]:
    """Sample inputs only; the hidden episode setting is not an argument."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    train = [
        _build_scene(seed, "demo", index, DEMO_PROFILES[index], force_edges=False)
        for index in range(demos)
    ]
    test = [
        _build_scene(seed, "query", index, profile, force_edges=index >= 2)
        for index, profile in enumerate(QUERY_PROFILES)
    ]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(encoded) != len(set(encoded)):
        raise ValueError("sampler produced duplicate inputs")
    return {"train": train, "test": test}


def lesson_certificate(demos: object, query_inputs: object) -> dict[str, object]:
    """Fit declared settings and named shortcut competitors on demos only."""
    if type(demos) is not list or not demos:
        raise ValueError("at least one demonstration is required")
    if type(query_inputs) is not list or not query_inputs:
        raise ValueError("at least one query input is required")
    normalized_demos: list[dict[str, Grid]] = []
    for pair in demos:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each demonstration needs input and output")
        _validate_grid(pair["input"])
        _validate_grid(pair["output"])
        normalized_demos.append(pair)
    for grid in query_inputs:
        _validate_grid(grid)

    survivors = [
        setting
        for setting in settings_space()
        if all(transform(pair["input"], setting) == pair["output"] for pair in normalized_demos)
    ]
    shortcut_survivors: list[dict[str, object]] = []
    for setting in settings_space():
        names = shortcut_outputs(normalized_demos[0]["input"], setting)
        for name in names:
            if all(
                shortcut_outputs(pair["input"], setting)[name] == pair["output"]
                for pair in normalized_demos
            ):
                shortcut_survivors.append({"settings": setting, "name": name})

    hypotheses: list[Callable[[Grid], Grid]] = [
        lambda grid, setting=setting: transform(grid, setting) for setting in survivors
    ]
    hypotheses.extend(
        lambda grid, setting=row["settings"], name=str(row["name"]): shortcut_outputs(grid, setting)[name]
        for row in shortcut_survivors
    )
    ambiguous_queries: list[int] = []
    for index, grid in enumerate(query_inputs):
        predictions = [hypothesis(grid) for hypothesis in hypotheses]
        if predictions and any(prediction != predictions[0] for prediction in predictions[1:]):
            ambiguous_queries.append(index)
    return {
        "surviving_settings": copy.deepcopy(survivors),
        "surviving_shortcuts": copy.deepcopy(shortcut_survivors),
        "ambiguous_queries": ambiguous_queries,
        "query_count": len(query_inputs),
        "query_outputs_consulted": False,
        "scope": (
            "finite two-setting family plus identity, constant-color, cell-count, "
            "dihedral, fixed-turn, reversed-selector, and location rivals"
        ),
    }


def generate_episode(
    seed: int,
    settings: object,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, object]:
    _integer(seed, 0, 2**63 - 1, "seed")
    setting = normalize_settings(settings)
    sampled = sample_inputs(seed, demos, queries)
    train = [
        {"input": copy.deepcopy(grid), "output": transform(grid, setting)}
        for grid in sampled["train"]
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": transform(grid, setting)}
        for grid in sampled["test"]
    ]
    certificate = lesson_certificate(train, [pair["input"] for pair in test])
    if certificate["surviving_settings"] != [setting] or certificate["surviving_shortcuts"]:
        raise ValueError("demonstrations do not uniquely teach the requested setting")
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(setting),
        "train": train,
        "test": test,
        "program_solution": program(setting),
        "certificate": certificate,
        "status": "proposed",
        "training_admitted": False,
    }


def public_projection(episode: object) -> dict[str, object]:
    from reviewer_support import public_challenge_bytes

    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    return json.loads(public_challenge_bytes(episode))


def visible_turn_bytes(episode: object, index: int) -> bytes:
    from reviewer_support import public_challenge_bytes

    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode needs a test list")
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes(
        {"train": episode.get("train"), "test": [episode["test"][index]]}
    )


def visible_turn(episode: object, index: int) -> dict[str, object]:
    return json.loads(visible_turn_bytes(episode, index))


def visible_turn_id(episode: object, index: int) -> str:
    return hashlib.sha256(visible_turn_bytes(episode, index)).hexdigest()


def episode_id(episode: object) -> str:
    from reviewer_support import public_challenge_id

    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    return public_challenge_id(episode)
