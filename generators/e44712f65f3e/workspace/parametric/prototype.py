"""Native parametric family for nested-frame expansion.

The default is the byte-exact canonical centered expansion.  The nearby
variant computes the nearest edge of the source frame (ties: top, bottom,
left, right) and anchors the expanded motif to that edge while retaining the
canonical centered coordinate on the other axis.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

TASK_ID = "e44712f65f3e"
HERE = Path(__file__).resolve().parent
PLACEMENTS = ("centered", "nearest_edge")
DEMO_PROFILES = (
    (16, 20, ((4, "top", None),)),
    (20, 16, ((4, "left", None),)),
    (24, 24, ((5, "bottom", None), (3, "top", None))),
    (22, 24, ((5, "right", None),)),
    (26, 28, ((6, "top", "left"),)),
    (28, 26, ((7, "left", None), (3, "right", None))),
)
QUERY_PROFILES = (
    (16, 16, ((3, "bottom", "right"),)),
    (22, 26, ((5, "right", None), (3, "left", None))),
    (26, 28, ((7, "top", None),)),
    (30, 30, ((8, "left", None), (4, "bottom", None))),
)
EDGE_INDEX = {"top": 0, "bottom": 1, "left": 2, "right": 3}


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"placement"}:
        raise ValueError("settings must contain exactly placement")
    value = settings["placement"]
    if type(value) is not str or value not in PLACEMENTS:
        raise ValueError("placement must be centered or nearest_edge")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    return (HERE / (_setting(settings) + ".rkt")).read_text(encoding="utf-8")


def _components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = set()
        while stack:
            r, c = stack.pop()
            cells.add((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    stack.append((nr, nc))
        result.append(cells)
    return result


def _frame(component, grid):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    outer = grid[r0][c0]
    inner_values = [
        grid[r][c]
        for r, c in sorted(component)
        if grid[r][c] not in (0, outer)
    ]
    inner = inner_values[0] if inner_values else outer
    return r0, c0, r1, c1, outer, inner


def _placement(frame, height, width, selected):
    r0, c0, r1, c1, _, _ = frame
    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    half_h, half_w = frame_h // 2, frame_w // 2
    out_h = 2 * frame_h if frame_h % 2 == 0 else 2 * frame_h - 1
    out_w = 2 * frame_w if frame_w % 2 == 0 else 2 * frame_w - 1
    top, left = r0 - half_h, c0 - half_w
    if selected == "nearest_edge":
        gaps = (r0, height - 1 - r1, c0, width - 1 - c1)
        edge = min(range(4), key=lambda index: (gaps[index], index))
        if edge == 0:
            top = 0
        elif edge == 1:
            top = height - out_h
        elif edge == 2:
            left = 0
        else:
            left = width - out_w
    return top, left, out_h, out_w, half_h, half_w


def _paint(output, frame, selected):
    height, width = len(output), len(output[0])
    _, _, _, _, outer, inner = frame
    top, left, out_h, out_w, half_h, half_w = _placement(
        frame, height, width, selected
    )
    for rr in range(out_h):
        for cc in range(out_w):
            gr, gc = top + rr, left + cc
            if not (0 <= gr < height and 0 <= gc < width):
                continue
            in_inner = (
                half_h <= rr < out_h - half_h
                and half_w <= cc < out_w - half_w
            )
            inner_border = in_inner and (
                rr in (half_h, out_h - half_h - 1)
                or cc in (half_w, out_w - half_w - 1)
            )
            inner_core = in_inner and not inner_border
            outer_band = (
                (rr < half_h and half_w <= cc < out_w - half_w)
                or (rr >= out_h - half_h and half_w <= cc < out_w - half_w)
                or (cc < half_w and half_h <= rr < out_h - half_h)
                or (cc >= out_w - half_w and half_h <= rr < out_h - half_h)
            )
            if inner_border:
                output[gr][gc] = inner
            elif inner_core or outer_band:
                output[gr][gc] = outer


def transform(grid, settings):
    grid = _grid(grid)
    selected = _setting(settings)
    output = [[0] * len(grid[0]) for _ in range(len(grid))]
    for component in _components(grid):
        _paint(output, _frame(component, grid), selected)
    return output


def _rng(seed, stream, index):
    payload = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _position_candidates(height, width, size, edge, tie_with):
    half = size // 2
    out_size = 2 * size if size % 2 == 0 else 2 * size - 1
    expected = EDGE_INDEX.get(edge)
    if expected is None:
        raise ValueError(f"unknown edge profile: {edge}")
    tied_index = None if tie_with is None else EDGE_INDEX.get(tie_with)
    if tie_with is not None and tied_index is None:
        raise ValueError(f"unknown tied edge profile: {tie_with}")
    if tied_index == expected:
        raise ValueError("tie edge must differ from selected edge")

    candidates = []
    for r0 in range(half, height - size - half + 1):
        for c0 in range(half, width - size - half + 1):
            if out_size > height or out_size > width:
                continue
            gaps = (r0, height - r0 - size, c0, width - c0 - size)
            minimum = min(gaps)
            tied = {index for index, gap in enumerate(gaps) if gap == minimum}
            actual = min(tied)
            wanted_tied = {expected} if tied_index is None else {expected, tied_index}
            # Keep the canonical centered motif away from the selected edge so
            # edge anchoring changes the output rather than degenerating to it.
            if actual == expected and tied == wanted_tied and minimum > half:
                candidates.append((r0, c0))
    if not candidates:
        raise ValueError(
            f"no lawful source position for size={size}, edge={edge}, tie={tie_with}"
        )
    return candidates


def _rectangles_overlap(first, second):
    ar0, ac0, ar1, ac1 = first
    br0, bc0, br1, bc1 = second
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _source_components_touch(first, second):
    ar0, ac0, ar1, ac1 = first
    br0, bc0, br1, bc1 = second
    return not (
        ar1 + 1 < br0
        or br1 + 1 < ar0
        or ac1 + 1 < bc0
        or bc1 + 1 < ac0
    )


def _output_rect(source_rect, height, width, selected):
    r0, c0, r1, c1 = source_rect
    top, left, out_h, out_w, _, _ = _placement(
        (r0, c0, r1, c1, 1, 2), height, width, selected
    )
    return top, left, top + out_h - 1, left + out_w - 1


def _choose_source_rects(height, width, specs, rng):
    choices = []
    for size, edge, tie_with in specs:
        candidates = _position_candidates(height, width, size, edge, tie_with)
        rng.shuffle(candidates)
        choices.append(
            [
                (r0, c0, r0 + size - 1, c0 + size - 1)
                for r0, c0 in candidates
            ]
        )

    def search(index, selected):
        if index == len(choices):
            return selected
        for candidate in choices[index]:
            if any(_source_components_touch(candidate, prior) for prior in selected):
                continue
            if any(
                _rectangles_overlap(
                    _output_rect(candidate, height, width, placement),
                    _output_rect(prior, height, width, placement),
                )
                for prior in selected
                for placement in PLACEMENTS
            ):
                continue
            result = search(index + 1, selected + [candidate])
            if result is not None:
                return result
        return None

    result = search(0, [])
    if result is None:
        raise ValueError("could not place non-overlapping nested frames for profile")
    return result


def sample_input(seed, split, index, profile):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0, 1000)
    if type(split) is not str or split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    height, width, specs = profile
    rng = _rng(seed, split, index)
    source_rects = _choose_source_rects(height, width, specs, rng)
    colors = iter(rng.sample(range(1, 10), 2 * len(specs)))
    grid = [[0] * width for _ in range(height)]
    for (size, _, _), (r0, c0, r1, c1) in zip(specs, source_rects):
        outer, inner = next(colors), next(colors)
        for r in range(size):
            for c in range(size):
                grid[r0 + r][c0 + c] = (
                    outer if r in (0, size - 1) or c in (0, size - 1) else inner
                )
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    episode = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen = set()
    for split, profiles in (
        ("train", DEMO_PROFILES[:demos]),
        ("test", QUERY_PROFILES[:queries]),
    ):
        for index, profile in enumerate(profiles):
            grid = sample_input(seed, split, index, profile)
            digest = json.dumps(grid, separators=(",", ":"))
            if digest in seen:
                raise ValueError("deterministic sampler produced a duplicate input")
            seen.add(digest)
            episode[split].append(
                {"input": grid, "output": transform(grid, settings)}
            )
    episode["certificate"] = certify(episode)
    return episode


def certify(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = episode.get("settings")
    _setting(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("episode program differs from fixed settings")
    survivors = []
    for placement in PLACEMENTS:
        candidate = {"placement": placement}
        if all(
            transform(pair["input"], candidate) == pair["output"]
            for pair in episode.get("train", [])
        ):
            survivors.append(candidate)
    if survivors != [settings]:
        raise ValueError(f"demonstrations do not identify one setting: {survivors}")
    for pair in episode.get("train", []) + episode.get("test", []):
        _grid(pair["input"])
        _grid(pair["output"])
        if transform(pair["input"], settings) != pair["output"]:
            raise ValueError("claimed label differs from selected transform")
    return {
        "schema": "nested-frame-placement-teaching-v1",
        "fit_scope": "demonstrations_only",
        "survivors": survivors,
    }


def execute_rule(source, grid, *, bridge=None):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    _grid(grid)
    owned = bridge is None
    bridge = RacketBridge(timeout=30) if owned else bridge
    try:
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return _grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
    finally:
        if owned:
            bridge.close()


def source_bindings():
    files = [
        HERE / name
        for name in (
            "prototype.py",
            "adapter.py",
            "promotion.json",
            "centered.rkt",
            "nearest_edge.rkt",
        )
    ]
    files.append(HERE.parents[1] / "generator.py")
    root = HERE.parents[3]
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }
