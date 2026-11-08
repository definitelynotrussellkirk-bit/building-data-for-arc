"""Matched-input native parametric family for per-frame endpoint routing.

The exact canonical setting routes every local endpoint pair.  The alternative
adds a causal relay: route the unique pair in the largest controller frame,
read the singleton color overwritten by that route, then route only that color's
pair in every smaller frame.  The hit color is an input-dependent intermediate;
without the first route the second-stage choice is not available.
"""
from __future__ import annotations

from collections import defaultdict, deque
from itertools import combinations
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

TASK_ID = "2e02ca69563c"
HERE = Path(__file__).resolve().parent
MODES = ("all_local_pairs", "relay_hit_color")

# Inclusive frame boxes: (top, left, bottom, right).  The first box is the
# unique largest controller; the rest are target frames.
_TRAIN_PROFILES: tuple[dict[str, Any], ...] = (
    {"shape": (12, 16), "boxes": ((1, 1, 10, 7), (2, 10, 9, 15)), "relay_role": 0},
    {"shape": (14, 18), "boxes": ((1, 1, 12, 8), (1, 11, 6, 17), (8, 11, 13, 17)), "relay_role": 1},
    {"shape": (16, 20), "boxes": ((1, 1, 14, 9), (1, 12, 7, 19), (9, 12, 15, 19)), "relay_role": 0},
    {"shape": (18, 22), "boxes": ((1, 1, 16, 10), (1, 13, 8, 21), (10, 13, 17, 21)), "relay_role": 1},
    {"shape": (22, 24), "boxes": ((1, 1, 11, 11), (1, 14, 9, 23), (13, 1, 21, 10), (13, 14, 21, 23)), "relay_role": 0},
    {"shape": (26, 28), "boxes": ((1, 1, 13, 13), (1, 17, 11, 27), (15, 1, 25, 11), (15, 17, 25, 27)), "relay_role": 1},
)
_QUERY_PROFILES: tuple[dict[str, Any], ...] = (
    {"shape": (13, 17), "boxes": ((1, 1, 11, 7), (2, 10, 10, 16)), "relay_role": 1},
    {"shape": (18, 21), "boxes": ((1, 1, 16, 9), (1, 12, 8, 20), (10, 12, 17, 20)), "relay_role": 0},
    {"shape": (24, 27), "boxes": ((1, 1, 12, 12), (1, 16, 10, 26), (14, 1, 23, 11), (14, 16, 23, 26)), "relay_role": 1},
    {"shape": (30, 30), "boxes": ((1, 1, 14, 14), (1, 18, 13, 29), (17, 1, 29, 13), (17, 17, 29, 29)), "relay_role": 0},
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"rule_mode"}:
        raise ValueError("settings must contain exactly rule_mode")
    mode = value["rule_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"rule_mode must be one of {MODES}")
    return mode


def program(settings: Any) -> str:
    mode = _settings(settings)
    filename = "canonical.rkt" if mode == "all_local_pairs" else "relay_hit_color.rkt"
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


def _path(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    (r0, c0), (r1, c1) = sorted((a, b))
    cstep = 1 if c1 >= c0 else -1
    horizontal = tuple((r0, col) for col in range(c0, c1 + cstep, cstep))
    rstep = 1 if r1 >= r0 else -1
    vertical = tuple((row, c1) for row in range(r0 + rstep, r1 + rstep, rstep))
    return horizontal + vertical


def _components(value: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    h, w = len(value), len(value[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if value[r][c] != 0}
    result: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    while unseen:
        start = min(unseen)
        color = value[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and value[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
        result.append((color, tuple(sorted(cells))))
    return result


def _frames(value: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    found: list[tuple[int, int, int, int, int]] = []
    for color, cells in _components(value):
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        height, width = bottom - top + 1, right - left + 1
        border = {
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)
        }
        if height >= 3 and width >= 3 and set(cells) == border:
            found.append((top, left, bottom, right, color))
    return sorted(found)


def _inside(frame: tuple[int, int, int, int, int], value: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    top, left, bottom, right, border_color = frame
    groups: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            color = value[r][c]
            if color not in (0, border_color):
                groups[color].append((r, c))
    return dict(groups)


def _area(frame: tuple[int, int, int, int, int]) -> int:
    return (frame[2] - frame[0] + 1) * (frame[3] - frame[1] + 1)


def observe(value: Any) -> dict[str, Any]:
    source = _grid(value)
    frames = _frames(source)
    if not 2 <= len(frames) <= 4:
        raise ValueError("scene needs one controller frame and one to three target frames")
    ranked = sorted(frames, key=lambda frame: (-_area(frame), frame))
    if _area(ranked[0]) == _area(ranked[1]):
        raise ValueError("controller frame must be uniquely largest")
    controller = ranked[0]
    targets = sorted(ranked[1:])
    controller_groups = _inside(controller, source)
    singleton_colors = {color for color, points in controller_groups.items() if len(points) == 1}
    candidate_pairs: list[tuple[int, list[tuple[int, int]], tuple[tuple[int, int], ...], list[tuple[int, int, int]]]] = []
    for color, points in controller_groups.items():
        if len(points) != 2:
            continue
        route = _path(points[0], points[1])
        hits = [
            (r, c, source[r][c])
            for r, c in route
            if source[r][c] in singleton_colors and source[r][c] != color
        ]
        if hits:
            candidate_pairs.append((color, points, route, hits))
    if len(candidate_pairs) != 1:
        raise ValueError("controller must have one pair whose route hits one singleton cue")
    controller_color, controller_points, controller_route, hits = candidate_pairs[0]
    if len(hits) != 1:
        raise ValueError("controller route must hit exactly one singleton cue")
    relay_color = hits[0][2]
    if len(singleton_colors) != 2 or relay_color not in singleton_colors:
        raise ValueError("controller must expose exactly two singleton candidate colors")

    first_target_groups = _inside(targets[0], source)
    target_pair_colors = [color for color, points in first_target_groups.items() if len(points) == 2]
    if len(target_pair_colors) != 2 or set(target_pair_colors) != singleton_colors:
        raise ValueError("target frames must contain the two controller cue colors as pairs")
    ordered_colors = sorted(target_pair_colors)
    for frame in targets:
        groups = _inside(frame, source)
        if set(color for color, points in groups.items() if len(points) == 2) != set(ordered_colors):
            raise ValueError("every target frame must contain both candidate endpoint pairs")
    relay_role = ordered_colors.index(relay_color)
    return {
        "frames": [list(frame) for frame in frames],
        "controller_frame": list(controller),
        "target_frames": [list(frame) for frame in targets],
        "controller_color": controller_color,
        "controller_points": [list(point) for point in sorted(controller_points)],
        "controller_route": [list(point) for point in controller_route],
        "hit_cell": list(hits[0][:2]),
        "relay_color": relay_color,
        "candidate_colors": ordered_colors,
        "relay_role": relay_role,
    }


def _paint_route(output: list[list[int]], points: Iterable[tuple[int, int]], color: int) -> None:
    for r, c in points:
        output[r][c] = color


def transform(value: Any, mode: Any) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    source = _grid(value)
    if mode == "all_local_pairs":
        output = [row[:] for row in source]
        for frame in _frames(source):
            for color, points in _inside(frame, source).items():
                if len(points) == 2:
                    _paint_route(output, _path(points[0], points[1]), color)
        return output

    state = observe(source)
    output = [row[:] for row in source]
    controller_points = [tuple(point) for point in state["controller_points"]]
    _paint_route(output, _path(controller_points[0], controller_points[1]), state["controller_color"])
    relay_color = state["relay_color"]
    for raw_frame in state["target_frames"]:
        frame = tuple(raw_frame)
        points = _inside(frame, source).get(relay_color, [])
        if len(points) != 2:
            raise ValueError("relay color must be a pair in every target frame")
        _paint_route(output, _path(points[0], points[1]), relay_color)
    return output


def _route_role(value: Any, role: int, *, first_target_only: bool = False) -> list[list[int]]:
    source = _grid(value)
    state = observe(source)
    output = [row[:] for row in source]
    controller_points = [tuple(point) for point in state["controller_points"]]
    _paint_route(output, _path(controller_points[0], controller_points[1]), state["controller_color"])
    color = state["candidate_colors"][role]
    frames = state["target_frames"][:1] if first_target_only else state["target_frames"]
    for raw_frame in frames:
        points = _inside(tuple(raw_frame), source)[color]
        _paint_route(output, _path(points[0], points[1]), color)
    return output


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    if hypothesis in MODES:
        return transform(value, hypothesis)
    source = _grid(value)
    if hypothesis == "relay_role_0":
        return _route_role(source, 0)
    if hypothesis == "relay_role_1":
        return _route_role(source, 1)
    if hypothesis == "relay_first_target_only":
        return _route_role(source, observe(source)["relay_role"], first_target_only=True)
    if hypothesis == "controller_only":
        state = observe(source)
        output = [row[:] for row in source]
        points = [tuple(point) for point in state["controller_points"]]
        _paint_route(output, _path(points[0], points[1]), state["controller_color"])
        return output
    if hypothesis == "copy_input":
        return source
    if hypothesis == "relay_smaller_color":
        state = observe(source)
        role = state["candidate_colors"].index(min(state["candidate_colors"]))
        return _route_role(source, role)
    if hypothesis == "relay_larger_color":
        state = observe(source)
        role = state["candidate_colors"].index(max(state["candidate_colors"]))
        return _route_role(source, role)
    raise ValueError("unknown hypothesis")


_HYPOTHESES = (
    "all_local_pairs",
    "relay_hit_color",
    "relay_role_0",
    "relay_role_1",
    "relay_first_target_only",
    "controller_only",
    "copy_input",
    "relay_smaller_color",
    "relay_larger_color",
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


def _reflect_box(box: tuple[int, int, int, int], h: int, w: int, flip_v: bool, flip_h: bool) -> tuple[int, int, int, int]:
    top, left, bottom, right = box
    if flip_v:
        top, bottom = h - 1 - bottom, h - 1 - top
    if flip_h:
        left, right = w - 1 - right, w - 1 - left
    return top, left, bottom, right


def _draw_frame(value: list[list[int]], box: tuple[int, int, int, int], color: int) -> None:
    top, left, bottom, right = box
    for c in range(left, right + 1):
        value[top][c] = color
        value[bottom][c] = color
    for r in range(top, bottom + 1):
        value[r][left] = color
        value[r][right] = color


def _interior(box: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    top, left, bottom, right = box
    return [(r, c) for r in range(top + 1, bottom) for c in range(left + 1, right)]


def _controller_contents(
    value: list[list[int]],
    box: tuple[int, int, int, int],
    controller_color: int,
    cue_colors: tuple[int, int],
    relay_role: int,
    rng: random.Random,
) -> None:
    cells = _interior(box)
    candidates: list[tuple[tuple[int, int], tuple[int, int], tuple[tuple[int, int], ...]]] = []
    for a, b in combinations(cells, 2):
        route = _path(a, b)
        if len(route) >= 5 and len(set(route)) == len(route):
            candidates.append((a, b, route))
    rng.shuffle(candidates)
    for a, b, route in candidates:
        internal = [point for point in route[1:-1]]
        free = [point for point in cells if point not in route]
        if len(internal) < 2 or not free:
            continue
        hit = rng.choice(internal)
        miss = rng.choice(free)
        value[a[0]][a[1]] = controller_color
        value[b[0]][b[1]] = controller_color
        value[hit[0]][hit[1]] = cue_colors[relay_role]
        value[miss[0]][miss[1]] = cue_colors[1 - relay_role]
        return
    raise RuntimeError("could not construct controller route and cue")


def _target_contents(
    value: list[list[int]],
    box: tuple[int, int, int, int],
    cue_colors: tuple[int, int],
    rng: random.Random,
) -> None:
    top, left, bottom, right = box
    ih, iw = bottom - top - 1, right - left - 1
    orientations = []
    if ih >= 4:
        orientations.append("rows")
    if iw >= 4:
        orientations.append("cols")
    if not orientations:
        raise RuntimeError("target frame interior cannot separate two routes")
    orientation = rng.choice(orientations)
    if orientation == "rows":
        cut = ih // 2
        regions = (
            [(r, c) for r in range(top + 1, top + 1 + cut) for c in range(left + 1, right)],
            [(r, c) for r in range(top + 1 + cut, bottom) for c in range(left + 1, right)],
        )
    else:
        cut = iw // 2
        regions = (
            [(r, c) for r in range(top + 1, bottom) for c in range(left + 1, left + 1 + cut)],
            [(r, c) for r in range(top + 1, bottom) for c in range(left + 1 + cut, right)],
        )
    for color, region in zip(cue_colors, regions):
        choices = [(a, b) for a, b in combinations(region, 2) if len(_path(a, b)) >= 4]
        if not choices:
            raise RuntimeError("target strip has no substantive endpoint route")
        a, b = rng.choice(choices)
        value[a[0]][a[1]] = color
        value[b[0]][b[1]] = color


def _scene(seed: int, split: str, index: int, profile: dict[str, Any]) -> list[list[int]]:
    h, w = profile["shape"]
    digest = hashlib.sha256(f"{TASK_ID}|relay-v1|{seed}|{split}|{index}".encode()).digest()
    rng = random.Random(digest)
    boxes = [tuple(box) for box in profile["boxes"]]
    flip_v, flip_h = bool(rng.randrange(2)), bool(rng.randrange(2))
    boxes = [_reflect_box(box, h, w, flip_v, flip_h) for box in boxes]
    palette = list(range(1, 10))
    rng.shuffle(palette)
    frame_colors = palette[: len(boxes)]
    controller_color = palette[len(boxes)]
    cue_colors = tuple(sorted(palette[len(boxes) + 1 : len(boxes) + 3]))
    value = [[0 for _ in range(w)] for _ in range(h)]
    for box, color in zip(boxes, frame_colors):
        _draw_frame(value, box, color)
    _controller_contents(
        value,
        boxes[0],
        controller_color,
        cue_colors,
        int(profile["relay_role"]),
        rng,
    )
    for box in boxes[1:]:
        _target_contents(value, box, cue_colors, rng)
    state = observe(value)
    if state["relay_role"] != profile["relay_role"]:
        raise AssertionError(f"relay role drift: {state['relay_role']} != {profile['relay_role']}")
    return value


def _inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train = [_scene(seed, "train", index, _TRAIN_PROFILES[index]) for index in range(demos)]
    test = [_scene(seed, "test", index, _QUERY_PROFILES[index]) for index in range(queries)]
    serial = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(serial) != len(set(serial)):
        raise AssertionError("generated inputs must be pairwise distinct")
    return train, test


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    mode = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    train_inputs, test_inputs = _inputs(seed, demos, queries)
    return {
        "program_solution": program(settings),
        "train": [{"input": grid, "output": transform(grid, mode)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, mode)} for grid in test_inputs],
    }


def dependency_description() -> dict[str, str]:
    return {
        "step_a": "Route the unique endpoint pair in the largest rectangular controller frame using the canonical horizontal-then-vertical trace.",
        "intermediate": "The singleton cue color encountered and overwritten by that input-dependent controller route.",
        "step_b": "In every smaller frame, route only the local endpoint pair whose color equals the encountered cue.",
        "why_b_depends_on_a": "Both candidate colors occur as pairs in every target frame; only the first route reveals which singleton cue it crosses, so the second-stage color cannot be chosen from target frames alone.",
    }
