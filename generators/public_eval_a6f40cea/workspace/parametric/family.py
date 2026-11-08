"""Amodal completion of rectangular wires hidden by the largest green box.

The public parent contains a frontmost color-3 rectangular occluder.  Other
monochrome or two-color striped rectangle outlines remain visible outside it.
Stage A recovers each complete wire rectangle from those visible fragments and
its parity texture.  Stage B renders the hidden boundary cells into the strict
interior window.

The immutable third training label contains one known phase inconsistency: its
wide 8/9 striped frame is inverted only behind the occluder.  The canonical
extension below is therefore explicit and input-derived rather than grid-bound:
striped frames wider than tall invert their visible checkerboard phase in the
hidden slice; tall/square striped frames preserve it.  Generated episodes teach
both the occlusion rule and this orientation branch.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

SCOPES = ("all_frames", "largest_frame")
RIVALS = (
    "other_setting",
    "all_frames",
    "largest_frame",
    "smallest_frame",
    "first_frame",
    "last_frame",
    "monochrome_only",
    "preserve_phase",
    "fill_only",
)


def _rng(seed: int, tag: str) -> random.Random:
    raw = hashlib.sha256(f"a6f40cea:{seed}:{tag}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("rectangular grid required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer colors 0..9 required")
    return tuple(tuple(row) for row in grid)


def _bbox(cells):
    rs = [p[0] for p in cells]
    cs = [p[1] for p in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _boundary(bbox):
    r1, c1, r2, c2 = bbox
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def _components_of_color(grid, color):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        out.append(tuple(sorted(cells)))
    return tuple(out)


def _target(grid):
    components = _components_of_color(grid, 3)
    if not components:
        raise ValueError("color-3 occluder is missing")
    cells = max(components, key=lambda comp: (len(comp), -comp[0][0], -comp[0][1]))
    bbox = _bbox(cells)
    r1, c1, r2, c2 = bbox
    if r2 - r1 < 2 or c2 - c1 < 2:
        raise ValueError("largest green component has no strict interior")
    perimeter = _boundary(bbox)
    if not perimeter <= set(cells):
        raise ValueError("largest green component must contain a complete rectangular border")
    return cells, bbox


def _inside_box(point, bbox):
    r, c = point
    r1, c1, r2, c2 = bbox
    return r1 <= r <= r2 and c1 <= c <= c2


def _inside_strict(point, bbox):
    r, c = point
    r1, c1, r2, c2 = bbox
    return r1 < r < r2 and c1 < c < c2


def _modal(values):
    counts = Counter(values)
    if not counts:
        raise ValueError("cannot take mode of empty values")
    return min(counts, key=lambda value: (-counts[value], value))


def _record(bbox, colors, parity, visible, target_bbox):
    r1, c1, r2, c2 = bbox
    hidden = sorted(p for p in _boundary(bbox) if _inside_strict(p, target_bbox))
    height, width = r2 - r1 + 1, c2 - c1 + 1
    striped = len(set(colors)) == 2
    return {
        "bbox": bbox,
        "colors": tuple(sorted(colors)),
        "even_color": parity[0],
        "odd_color": parity[1],
        "striped": striped,
        "phase_flipped": bool(striped and width > height),
        "height": height,
        "width": width,
        "area": height * width,
        "visible_cells": len(visible),
        "hidden_cells": tuple(hidden),
    }


def analyze(grid):
    g = validate_grid(grid)
    target_cells, target_bbox = _target(g)
    tr1, tc1, tr2, tc2 = target_bbox
    outside_values = [
        g[r][c]
        for r in range(len(g))
        for c in range(len(g[0]))
        if not _inside_box((r, c), target_bbox)
    ]
    background = _modal(outside_values)
    fill = _modal(g[r][c] for r in range(tr1 + 1, tr2) for c in range(tc1 + 1, tc2))

    positions = defaultdict(set)
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if not _inside_box((r, c), target_bbox) and value not in {background, 3, fill}:
                positions[value].add((r, c))

    boxes = {color: _bbox(cells) for color, cells in positions.items() if cells}
    frames = []

    # Monochrome wires.
    for color in sorted(positions):
        cells = positions[color]
        bbox = boxes[color]
        r1, c1, r2, c2 = bbox
        if r2 - r1 < 2 or c2 - c1 < 2:
            continue
        visible = {p for p in _boundary(bbox) if not _inside_box(p, target_bbox)}
        hidden = {p for p in _boundary(bbox) if _inside_strict(p, target_bbox)}
        if hidden and cells == visible and all(g[r][c] == color for r, c in visible):
            frames.append(_record(bbox, (color,), {0: color, 1: color}, visible, target_bbox))

    # Two-color checkerboard wires.  Each color independently reaches the same
    # rectangle extrema; their union is the entire unoccluded perimeter.
    colors = sorted(positions)
    for i, first in enumerate(colors):
        for second in colors[i + 1 :]:
            if boxes[first] != boxes[second]:
                continue
            bbox = boxes[first]
            r1, c1, r2, c2 = bbox
            if r2 - r1 < 2 or c2 - c1 < 2:
                continue
            visible = {p for p in _boundary(bbox) if not _inside_box(p, target_bbox)}
            hidden = {p for p in _boundary(bbox) if _inside_strict(p, target_bbox)}
            if not hidden or positions[first] | positions[second] != visible:
                continue
            parity = {}
            valid = True
            for r, c in visible:
                value = g[r][c]
                if value not in {first, second}:
                    valid = False
                    break
                key = (r + c) & 1
                if key in parity and parity[key] != value:
                    valid = False
                    break
                parity[key] = value
            if valid and set(parity) == {0, 1} and parity[0] != parity[1]:
                frames.append(_record(bbox, (first, second), parity, visible, target_bbox))

    frames.sort(key=lambda frame: (frame["bbox"][0], frame["bbox"][1], frame["bbox"][2], frame["bbox"][3], frame["colors"]))
    if not frames:
        raise ValueError("no reconstructable rectangle wires cross the target interior")
    return {
        "grid": g,
        "background": background,
        "fill": fill,
        "target_cells": target_cells,
        "target_bbox": target_bbox,
        "frames": tuple(frames),
    }


def _selected(info, scope, rival=None):
    if scope not in SCOPES:
        raise ValueError("unknown scope")
    effective = scope
    if rival == "other_setting":
        effective = SCOPES[1 - SCOPES.index(scope)]
    elif rival in SCOPES:
        effective = rival
    frames = list(info["frames"])
    if effective == "all_frames":
        selected = frames
    else:
        selected = [max(frames, key=lambda f: (f["area"], -f["bbox"][0], -f["bbox"][1]))]
    if rival == "smallest_frame":
        selected = [min(frames, key=lambda f: (f["area"], f["bbox"][0], f["bbox"][1]))]
    elif rival == "first_frame":
        selected = [frames[0]]
    elif rival == "last_frame":
        selected = [frames[-1]]
    elif rival == "monochrome_only":
        selected = [f for f in selected if not f["striped"]]
    elif rival == "fill_only":
        selected = []
    return selected


def _render(info, selected, *, preserve_phase=False):
    tr1, tc1, tr2, tc2 = info["target_bbox"]
    output = [[info["fill"] for _ in range(tc2 - tc1 - 1)] for _ in range(tr2 - tr1 - 1)]
    for frame in selected:
        even, odd = frame["even_color"], frame["odd_color"]
        if frame["phase_flipped"] and not preserve_phase:
            even, odd = odd, even
        for r, c in frame["hidden_cells"]:
            output[r - tr1 - 1][c - tc1 - 1] = even if (r + c) % 2 == 0 else odd
    return output


def solve(grid, scope="all_frames", *, rival=None):
    if rival is not None and rival not in RIVALS:
        raise ValueError("unknown rival")
    info = analyze(grid)
    selected = _selected(info, scope, rival)
    return _render(info, selected, preserve_phase=(rival == "preserve_phase"))


def _paint_boundary(grid, bbox, even_color, odd_color):
    for r, c in _boundary(bbox):
        grid[r][c] = even_color if (r + c) % 2 == 0 else odd_color


def _paint_target(grid, bbox, fill):
    r1, c1, r2, c2 = bbox
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            grid[r][c] = 3 if r in (r1, r2) or c in (c1, c2) else fill


def _add_green_distractor(grid, top, left, height, width):
    bbox = (top, left, top + height - 1, left + width - 1)
    for r, c in _boundary(bbox):
        grid[r][c] = 3


def _scene(seed, tag, *, profile=0, stress=False, attempt=0):
    rng = _rng(seed, f"{tag}:{profile}:{stress}:{attempt}")
    size = 30 if stress else rng.choice((25, 26, 27, 28))
    height = width = size
    if stress:
        target = (4, 6, 25, 23)  # 20x16 strict interior
    else:
        top = 4 + rng.randrange(0, 2)
        left = 6 + rng.randrange(0, 2)
        bottom = size - 5
        right = size - 6
        target = (top, left, bottom, right)
    tr1, tc1, tr2, tc2 = target
    interior_rows = list(range(tr1 + 1, tr2))
    if len(interior_rows) < 14:
        raise ValueError("target interior too short")

    # Three non-overlapping horizontal wire intervals.  The profile moves the
    # unique largest-area wire between the first two reading-order positions,
    # defeating fixed-position selectors in the minimum two demonstrations.
    if profile % 3 == 0:
        row_pairs = [(interior_rows[1], interior_rows[6]), (interior_rows[8], interior_rows[10]), (interior_rows[-3], interior_rows[-1])]
    elif profile % 3 == 1:
        row_pairs = [(interior_rows[1], interior_rows[3]), (interior_rows[5], interior_rows[11]), (interior_rows[-3], interior_rows[-1])]
    else:
        row_pairs = [(interior_rows[1], interior_rows[3]), (interior_rows[5], interior_rows[7]), (interior_rows[9], interior_rows[-1])]

    margins = [(2, width - 3), (1, width - 2), (3, width - 4)]
    # Small deterministic jitter leaves every vertical side outside the target.
    jitter = rng.choice((0, 1))
    boxes = []
    for index, ((r1, r2), (c1, c2)) in enumerate(zip(row_pairs, margins)):
        if index == 0:
            c1 += jitter
        elif index == 2:
            c2 -= jitter
        boxes.append((r1, c1, r2, c2))

    palette = [color for color in range(10) if color != 3]
    bg, fill, mono, a, b, c, d = rng.sample(palette, 7)
    # Frame 0 and 1 are striped; frame 2 is monochrome.  The largest frame in
    # profiles 0 and 1 is therefore striped, forcing the alternate lesson to
    # expose both selection and the orientation-dependent phase branch.
    styles = [((a, b),), ((c, d),), ((mono, mono),)]
    grid = [[bg for _ in range(width)] for _ in range(height)]
    for bbox, style in zip(boxes, styles):
        pair = style[0]
        _paint_boundary(grid, bbox, pair[0], pair[1])
    _paint_target(grid, target, fill)
    if (seed + profile + attempt) % 2 == 0:
        _add_green_distractor(grid, 1, 1, 3, 4)

    info = analyze(grid)
    if len(info["frames"]) != 3:
        raise ValueError("scene must recover exactly three wires")
    largest = max(info["frames"], key=lambda f: f["area"])
    expected_index = profile % 3
    if info["frames"].index(largest) != expected_index:
        raise ValueError("profile did not move the largest frame as intended")
    if not largest["striped"] and profile % 3 in (0, 1):
        raise ValueError("minimum lesson largest frame must be striped")
    if solve(grid, "all_frames") == solve(grid, "largest_frame"):
        raise ValueError("settings collapsed")
    return grid


def _lesson_refutes(grids):
    for scope in SCOPES:
        correct = [solve(grid, scope) for grid in grids]
        for rival in RIVALS:
            if rival == scope:
                continue
            if all(solve(grid, scope, rival=rival) == want for grid, want in zip(grids, correct)):
                return False
    return True


@lru_cache(maxsize=128)
def _inputs(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2^63)")
    first = None
    for attempt in range(256):
        try:
            pair = [
                _scene(seed, "demo:0", profile=0, attempt=attempt),
                _scene(seed, "demo:1", profile=1, attempt=attempt),
            ]
        except ValueError:
            continue
        if _lesson_refutes(pair):
            first = pair
            break
    if first is None:
        raise ValueError("bounded distinguishing demonstration search exhausted")
    used = {json.dumps(grid, separators=(",", ":")) for grid in first}
    demos = list(first)
    for index in range(2, 6):
        for attempt in range(256):
            try:
                grid = _scene(seed, f"demo:{index}", profile=index % 3, attempt=attempt)
            except ValueError:
                continue
            key = json.dumps(grid, separators=(",", ":"))
            if key not in used:
                used.add(key)
                demos.append(grid)
                break
        else:
            raise ValueError("bounded distinct demonstration search exhausted")
    queries = []
    for index in range(4):
        for attempt in range(256):
            try:
                grid = _scene(seed, f"query:{index}", profile=(index + 1) % 3, stress=(index == 3), attempt=attempt)
            except ValueError:
                continue
            key = json.dumps(grid, separators=(",", ":"))
            if key not in used:
                used.add(key)
                queries.append(grid)
                break
        else:
            raise ValueError("bounded distinct query search exhausted")
    return tuple(tuple(tuple(row) for row in grid) for grid in demos), tuple(tuple(tuple(row) for row in grid) for grid in queries)


def _request(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2^63)")
    if type(settings) is not dict or set(settings) != {"scope"} or settings["scope"] not in SCOPES:
        raise ValueError("one declared scope setting required")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be 1..4")
    return settings["scope"]


def program(settings):
    scope = _request(0, settings, 2, 4)
    name = "canonical.rkt" if scope == "all_frames" else "largest-frame.rkt"
    return Path(__file__).with_name(name).read_text()


def generate(seed, settings, demos, queries):
    scope = _request(seed, settings, demos, queries)
    demo_inputs, query_inputs = _inputs(seed)
    pair = lambda grid: {"input": [list(row) for row in grid], "output": solve([list(row) for row in grid], scope)}
    return {
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
        "program_solution": program(settings),
    }


def present(seed, settings, demos, queries, presentation_seed=0):
    _request(seed, settings, demos, queries)
    if type(presentation_seed) is not int:
        raise ValueError("integer presentation seed required")
    episode = generate(seed, settings, demos, 4)
    order = list(range(4))
    _rng(seed, f"presentation:{presentation_seed}").shuffle(order)
    views = []
    for index in order[:queries]:
        views.append({
            "train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(episode["test"][index]["input"])}],
        })
    return {
        "public": views,
        "private": {
            "seed": seed,
            "settings": deepcopy(settings),
            "presentation_seed": presentation_seed,
            "source_indices": order[:queries],
            "program": episode["program_solution"],
            "source_pairs": deepcopy(episode["test"]),
        },
    }


def intermediate(grid, settings):
    scope = _request(0, settings, 2, 4)
    info = analyze(grid)
    chosen = _selected(info, scope)
    counter = _selected(info, scope, "other_setting")
    serial = lambda frame: {
        "bbox": list(frame["bbox"]),
        "colors": list(frame["colors"]),
        "area": frame["area"],
        "phase_flipped": frame["phase_flipped"],
        "hidden_cells": [list(p) for p in frame["hidden_cells"]],
    }
    return {
        "target_bbox": list(info["target_bbox"]),
        "fill": info["fill"],
        "recovered_frames": [serial(frame) for frame in info["frames"]],
        "selected_frame": [serial(frame) for frame in chosen],
        "counterfactual_frame": [serial(frame) for frame in counter],
    }


def dependency():
    return {
        "step_a": "Select the largest four-connected green rectangular occluder, recover every partially visible rectangle wire outside it, and infer each wire's monochrome/checkerboard texture and dimensions.",
        "intermediate": "The ordered recovered wire records, including input-derived bounding boxes, parity colors, orientation phase branch, area rank, and hidden boundary cells inside the green window.",
        "step_b": "Render either all recovered wires or only the unique largest-area wire into the occluder's strict interior over its fill color.",
        "why_b_depends_on_a": "Neither the hidden cell coordinates nor the alternate setting's selected wire are fixed. Changing only the recovered/selected wire intermediate changes the final interior while leaving the renderer and source grid unchanged.",
    }


def self_check(grid, **_):
    try:
        info = analyze(grid)
        if len(info["frames"]) < 2:
            return ["at least two recovered wires required"]
        if len({frame["area"] for frame in info["frames"]}) != len(info["frames"]):
            return ["wire areas must be distinct"]
        if solve(grid, "all_frames") == solve(grid, "largest_frame"):
            return ["settings must disagree"]
        return []
    except (TypeError, ValueError) as exc:
        return [str(exc)]


def ordinary(seed, sample_index, *, stress=False):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError("nonnegative exact integer seed and sample_index required")
    for attempt in range(256):
        try:
            grid = _scene(seed, f"ordinary:{sample_index}", profile=sample_index % 3, stress=stress, attempt=attempt)
        except ValueError:
            continue
        if not self_check(grid):
            return grid
    raise ValueError("bounded ordinary generation exhausted")
