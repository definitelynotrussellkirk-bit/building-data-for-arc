"""Matched-input native parametric family for exact 2x2 object filtering.

The exact canonical setting keeps every solid 2x2 magenta component.  The
alternative first identifies the unique largest non-square straight controller,
derives its row or column axis, then keeps only exact squares intersected by that
axis.  The controller-derived axis is the input-dependent intermediate consumed
by the filtering stage.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "2d4e8c8fa10e"
HERE = Path(__file__).resolve().parent
SELECTIONS = ("all_exact_squares", "controller_axis")
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_NEIGHBORS8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
_DISTRACTOR_SHAPES = (
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
)

_TRAIN_PROFILES: tuple[dict[str, Any], ...] = (
    {"shape": (10, 14), "orientation": "horizontal", "aligned": 1, "off": 2, "extra": 2, "length": 6},
    {"shape": (12, 16), "orientation": "vertical", "aligned": 2, "off": 1, "extra": 3, "length": 6},
    {"shape": (14, 18), "orientation": "horizontal", "aligned": 2, "off": 2, "extra": 3, "length": 7},
    {"shape": (18, 20), "orientation": "vertical", "aligned": 3, "off": 2, "extra": 4, "length": 7},
    {"shape": (22, 24), "orientation": "horizontal", "aligned": 3, "off": 3, "extra": 5, "length": 8},
    {"shape": (26, 28), "orientation": "vertical", "aligned": 4, "off": 3, "extra": 6, "length": 8},
)
_QUERY_PROFILES: tuple[dict[str, Any], ...] = (
    {"shape": (11, 15), "orientation": "vertical", "aligned": 1, "off": 2, "extra": 2, "length": 6},
    {"shape": (17, 19), "orientation": "horizontal", "aligned": 2, "off": 3, "extra": 4, "length": 7},
    {"shape": (24, 26), "orientation": "vertical", "aligned": 3, "off": 4, "extra": 6, "length": 8},
    {"shape": (30, 30), "orientation": "horizontal", "aligned": 4, "off": 4, "extra": 7, "length": 9},
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    selection = value["selection"]
    if type(selection) is not str or selection not in SELECTIONS:
        raise ValueError(f"selection must be one of {SELECTIONS}")
    return selection


def program(settings: Any) -> str:
    selection = _settings(settings)
    filename = "canonical.rkt" if selection == "all_exact_squares" else "controller_axis.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in value]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _components(value: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(value), len(value[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if value[r][c] == 6}
    result: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: min(cells))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _solid_square(cells: Iterable[tuple[int, int]]) -> bool:
    return _normalize(cells) == _SQUARE


def observe(value: Any) -> dict[str, Any]:
    source = _grid(value)
    colors = {cell for row in source for cell in row}
    if not colors <= {0, 6} or 6 not in colors:
        raise ValueError("scene must use only background 0 and magenta 6")
    components = _components(source)
    squares = [cells for cells in components if _solid_square(cells)]
    distractors = [cells for cells in components if not _solid_square(cells)]
    if len(squares) < 3 or not distractors:
        raise ValueError("scene needs at least three squares and a controller/distractor set")
    ranked = sorted(distractors, key=lambda cells: (-len(cells), min(cells)))
    if len(ranked) > 1 and len(ranked[0]) == len(ranked[1]):
        raise ValueError("controller must be the unique largest non-square component")
    controller = ranked[0]
    top, left, bottom, right = _bbox(controller)
    height, width = bottom - top + 1, right - left + 1
    if height == 1 and width == len(controller):
        orientation = "horizontal"
        axis = top
        aligned = [cells for cells in squares if any(r == axis for r, _ in cells)]
    elif width == 1 and height == len(controller):
        orientation = "vertical"
        axis = left
        aligned = [cells for cells in squares if any(c == axis for _, c in cells)]
    else:
        raise ValueError("controller must be a straight one-cell-thick bar")
    if not aligned or len(aligned) == len(squares):
        raise ValueError("controller axis must select a proper nonempty subset of squares")
    return {
        "height": len(source),
        "width": len(source[0]),
        "components": [[list(point) for point in cells] for cells in components],
        "squares": [[list(point) for point in cells] for cells in squares],
        "distractors": [[list(point) for point in cells] for cells in distractors],
        "controller": [list(point) for point in controller],
        "orientation": orientation,
        "axis": axis,
        "aligned_squares": [[list(point) for point in cells] for cells in aligned],
    }


def _paint(height: int, width: int, components: Iterable[Iterable[Iterable[int]]]) -> list[list[int]]:
    output = [[0 for _ in range(width)] for _ in range(height)]
    for cells in components:
        for point in cells:
            r, c = point
            output[r][c] = 6
    return output


def transform(value: Any, selection: Any) -> list[list[int]]:
    if selection not in SELECTIONS:
        raise ValueError(f"selection must be one of {SELECTIONS}")
    state = observe(value)
    chosen = state["squares"] if selection == "all_exact_squares" else state["aligned_squares"]
    return _paint(state["height"], state["width"], chosen)


def _perpendicular(value: Any) -> list[list[int]]:
    state = observe(value)
    controller = [tuple(point) for point in state["controller"]]
    top, left, bottom, right = _bbox(controller)
    squares = [[tuple(point) for point in cells] for cells in state["squares"]]
    if state["orientation"] == "horizontal":
        center_col = (left + right) // 2
        chosen = [cells for cells in squares if any(c == center_col for _, c in cells)]
    else:
        center_row = (top + bottom) // 2
        chosen = [cells for cells in squares if any(r == center_row for r, _ in cells)]
    return _paint(state["height"], state["width"], chosen)


def _first_aligned(value: Any) -> list[list[int]]:
    state = observe(value)
    return _paint(state["height"], state["width"], state["aligned_squares"][:1])


def _orientation_only(value: Any, orientation: str) -> list[list[int]]:
    state = observe(value)
    chosen = state["aligned_squares"] if state["orientation"] == orientation else []
    return _paint(state["height"], state["width"], chosen)


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    if hypothesis in SELECTIONS:
        return transform(value, hypothesis)
    state = observe(value)
    if hypothesis == "perpendicular_axis":
        return _perpendicular(value)
    if hypothesis == "first_aligned_only":
        return _first_aligned(value)
    if hypothesis == "horizontal_controller_only":
        return _orientation_only(value, "horizontal")
    if hypothesis == "vertical_controller_only":
        return _orientation_only(value, "vertical")
    if hypothesis == "empty":
        return [[0 for _ in range(state["width"])] for _ in range(state["height"])]
    if hypothesis == "copy_input":
        return _grid(value)
    if hypothesis == "keep_largest_component":
        return _paint(state["height"], state["width"], [state["controller"]])
    raise ValueError("unknown hypothesis")


_HYPOTHESES = (
    "all_exact_squares",
    "controller_axis",
    "perpendicular_axis",
    "first_aligned_only",
    "horizontal_controller_only",
    "vertical_controller_only",
    "empty",
    "copy_input",
    "keep_largest_component",
)


def teaching_audit(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain train and test lists")
    survivors: list[str] = []
    harmful: list[str] = []
    for name in _HYPOTHESES:
        if all(predict(pair["input"], name) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            if any(predict(pair["input"], name) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "policies_checked": len(_HYPOTHESES),
        "survivors": survivors,
        "query_disagreeing_survivors": harmful,
    }


def _blocked(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in _NEIGHBORS8
        if 0 <= r + dr < h and 0 <= c + dc < w
    }


def _translate(shape: Iterable[tuple[int, int]], top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + r, left + c) for r, c in shape)


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(shape)
    return max(r for r, _ in points) + 1, max(c for _, c in points) + 1


def _place_from_candidates(
    value: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    blocked: set[tuple[int, int]],
    candidates: list[tuple[int, int]],
    rng: random.Random,
) -> tuple[tuple[int, int], ...] | None:
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = _translate(shape, top, left)
        if any(point in blocked for point in cells):
            continue
        for r, c in cells:
            value[r][c] = 6
        blocked.update(_blocked(cells, len(value), len(value[0])))
        return cells
    return None


def _square_candidates(h: int, w: int, orientation: str, axis: int, aligned: bool) -> list[tuple[int, int]]:
    result = []
    for top in range(h - 1):
        for left in range(w - 1):
            hits = axis in (top, top + 1) if orientation == "horizontal" else axis in (left, left + 1)
            if hits == aligned:
                result.append((top, left))
    return result


def _variant(shape: tuple[tuple[int, int], ...], rng: random.Random) -> tuple[tuple[int, int], ...]:
    points = list(shape)
    for _ in range(rng.randrange(4)):
        points = [(c, -r) for r, c in points]
    if rng.randrange(2):
        points = [(r, -c) for r, c in points]
    return _normalize(points)


def _try_scene(seed: int, split: str, index: int, profile: dict[str, Any], attempt: int) -> list[list[int]] | None:
    h, w = profile["shape"]
    digest = hashlib.sha256(f"{TASK_ID}|axis-v1|{seed}|{split}|{index}|{attempt}".encode()).digest()
    rng = random.Random(digest)
    value = [[0 for _ in range(w)] for _ in range(h)]
    orientation = profile["orientation"]
    length = int(profile["length"])
    blocked: set[tuple[int, int]] = set()
    if orientation == "horizontal":
        axis = min(h - 3, max(2, h // 2 + rng.choice((-1, 0, 1))))
        start = max(2, min(w - length - 2, w // 2 - length // 2 + rng.choice((-1, 0, 1))))
        controller = tuple((axis, start + offset) for offset in range(length))
    else:
        axis = min(w - 3, max(2, w // 2 + rng.choice((-1, 0, 1))))
        start = max(2, min(h - length - 2, h // 2 - length // 2 + rng.choice((-1, 0, 1))))
        controller = tuple((start + offset, axis) for offset in range(length))
    for r, c in controller:
        value[r][c] = 6
    blocked.update(_blocked(controller, h, w))

    for aligned in (True, False):
        count = int(profile["aligned"] if aligned else profile["off"])
        for _ in range(count):
            placed = _place_from_candidates(
                value,
                _SQUARE,
                blocked,
                _square_candidates(h, w, orientation, axis, aligned),
                rng,
            )
            if placed is None:
                return None

    for distractor_index in range(int(profile["extra"])):
        base = _DISTRACTOR_SHAPES[(distractor_index + rng.randrange(len(_DISTRACTOR_SHAPES))) % len(_DISTRACTOR_SHAPES)]
        shape = _variant(base, rng)
        sh, sw = _shape_dims(shape)
        candidates = [(top, left) for top in range(h - sh + 1) for left in range(w - sw + 1)]
        placed = _place_from_candidates(value, shape, blocked, candidates, rng)
        if placed is None:
            return None

    state = observe(value)
    if state["orientation"] != orientation:
        return None
    if len(state["aligned_squares"]) != profile["aligned"]:
        return None
    if len(state["squares"]) != profile["aligned"] + profile["off"]:
        return None
    if len(state["distractors"]) != profile["extra"] + 1:
        return None
    return value


def _scene(seed: int, split: str, index: int, profile: dict[str, Any]) -> list[list[int]]:
    for attempt in range(80):
        value = _try_scene(seed, split, index, profile, attempt)
        if value is not None:
            return value
    raise RuntimeError(f"could not construct {split}[{index}] after bounded attempts")


def _inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train = [_scene(seed, "train", index, _TRAIN_PROFILES[index]) for index in range(demos)]
    test = [_scene(seed, "test", index, _QUERY_PROFILES[index]) for index in range(queries)]
    serial = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(serial) != len(set(serial)):
        raise AssertionError("generated inputs must be pairwise distinct")
    return train, test


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    selection = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    train_inputs, test_inputs = _inputs(seed, demos, queries)
    return {
        "program_solution": program(settings),
        "train": [{"input": grid, "output": transform(grid, selection)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selection)} for grid in test_inputs],
    }


def dependency_description() -> dict[str, str]:
    return {
        "step_a": "Identify the unique largest non-square magenta component and derive its one-cell-thick horizontal or vertical center axis.",
        "intermediate": "The input-dependent controller orientation and guide row or column.",
        "step_b": "Among exact solid 2x2 components, retain only those intersected by the derived guide axis.",
        "why_b_depends_on_a": "The input contains both aligned and off-axis exact squares, and the controller orientation/location varies; square eligibility cannot be fixed until the controller-derived axis is known.",
    }
