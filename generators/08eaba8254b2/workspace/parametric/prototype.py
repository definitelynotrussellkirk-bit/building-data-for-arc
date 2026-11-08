"""Native parametric family for stacked occupancy XOR.

The default is the byte-exact canonical cellwise XOR.  The nearby variant first
forms the same XOR mask, selects its largest four-connected component (row-major
bbox tie-break), then paints that component's bounding-box border.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

TASK_ID = "08eaba8254b2"
HERE = Path(__file__).resolve().parent
PROJECTIONS = ("cellwise_xor", "largest_component_bbox")
DEMO_WIDTHS = (8, 10, 12, 14, 16, 18)
QUERY_WIDTHS = (7, 21, 25, 30)
SHAPE_TEMPLATES = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 2), (3, 2)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (3, 4), (3, 5)),
)
PROFILE_TEMPLATE = (0, 1, 2, 3, 4, 5, 2, 4, 0, 5)
TIE_PROFILE = 8


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"projection"}:
        raise ValueError("settings must contain exactly projection")
    value = settings["projection"]
    if type(value) is not str or value not in PROJECTIONS:
        raise ValueError("projection must be cellwise_xor or largest_component_bbox")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    return (HERE / (_setting(settings) + ".rkt")).read_text(encoding="utf-8")


def xor_mask(grid):
    _grid(grid)
    if len(grid) != 9:
        raise ValueError("stacked XOR input must have exactly 9 rows")
    return [[int((grid[r][c] == 0) != (grid[5 + r][c] == 0))
             for c in range(len(grid[0]))] for r in range(4)]


def _components(mask):
    height, width = len(mask), len(mask[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if mask[r][c]}
    result = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component = set()
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            component.add((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    stack.append((nr, nc))
        result.append(component)
    return result


def transform(grid, settings):
    selected = _setting(settings)
    mask = xor_mask(grid)
    width = len(mask[0])
    if selected == "cellwise_xor":
        return [[3 if value else 0 for value in row] for row in mask]
    components = _components(mask)
    if not components:
        return [[0] * width for _ in range(4)]
    best = min(
        components,
        key=lambda cells: (
            -len(cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        ),
    )
    rows = [r for r, _ in best]
    cols = [c for _, c in best]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    return [[3 if r0 <= r <= r1 and c0 <= c <= c1 and
                 (r in (r0, r1) or c in (c0, c1)) else 0
             for c in range(width)] for r in range(4)]


def _rng(seed, stream, index):
    payload = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _template_shape(template, *, mirror):
    template_width = max(c for _, c in template) + 1
    if mirror:
        return tuple((r, template_width - 1 - c) for r, c in template)
    return template


def _place(mask, template, top, left):
    for r, c in template:
        mask[top + r][left + c] = 1


def _add_isolated_decoys(mask, rng, count):
    height, width = len(mask), len(mask[0])
    candidates = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(candidates)
    added = 0
    for r, c in candidates:
        if mask[r][c]:
            continue
        if any(
            0 <= nr < height and 0 <= nc < width and mask[nr][nc]
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        ):
            continue
        mask[r][c] = 1
        added += 1
        if added == count:
            return
    raise ValueError("could not place requested isolated XOR decoys")


def _xor_shape(width, rng, profile_index):
    mask = [[0] * width for _ in range(4)]
    profile_slot = profile_index % len(PROFILE_TEMPLATE)
    if profile_slot == TIE_PROFILE:
        template = SHAPE_TEMPLATES[0]
        _place(mask, template, 0, 2)
        _place(mask, template, 1, width - 5)
        _add_isolated_decoys(mask, rng, 1)
        return mask

    template = SHAPE_TEMPLATES[PROFILE_TEMPLATE[profile_slot]]
    template = _template_shape(template, mirror=bool(rng.randrange(2)))
    shape_height = max(r for r, _ in template) + 1
    shape_width = max(c for _, c in template) + 1
    origins = [
        (top, left)
        for top in range(5 - shape_height)
        for left in range(width - shape_width + 1)
    ]
    if not origins:
        raise ValueError("XOR component template does not fit the requested width")
    left_side = profile_slot % 2 == 0
    preferred = [
        origin
        for origin in origins
        if (origin[1] + shape_width <= (width + 1) // 2 + 1) == left_side
    ]
    top, left = rng.choice(preferred or origins)
    _place(mask, template, top, left)
    _add_isolated_decoys(mask, rng, 2 + int(profile_slot % 3 == 0))
    return mask


def sample_input(seed, split, index, width):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0, 1000)
    _integer(width, "width", 7, 30)
    if type(split) is not str or split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    rng = _rng(seed, split, index)
    profile_index = index if split == "train" else len(DEMO_WIDTHS) + index
    mask = _xor_shape(width, rng, profile_index)
    top_color, bottom_color, separator = rng.sample(range(1, 10), 3)
    grid = [[0] * width for _ in range(9)]
    grid[4] = [separator] * width
    for r in range(4):
        for c in range(width):
            if mask[r][c]:
                if (r + c + rng.randrange(2)) % 2:
                    grid[r][c] = top_color
                else:
                    grid[5 + r][c] = bottom_color
            elif rng.random() < 0.48:
                grid[r][c] = top_color
                grid[5 + r][c] = bottom_color
    top_has = any(grid[r][c] for r in range(4) for c in range(width))
    bottom_has = any(grid[5 + r][c] for r in range(4) for c in range(width))
    if not (top_has and bottom_has):
        for r in range(4):
            for c in range(width):
                if not mask[r][c]:
                    grid[r][c] = top_color
                    grid[5 + r][c] = bottom_color
                    return grid
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
    for split, widths in (("train", DEMO_WIDTHS[:demos]), ("test", QUERY_WIDTHS[:queries])):
        for index, width in enumerate(widths):
            grid = sample_input(seed, split, index, width)
            digest = json.dumps(grid, separators=(",", ":"))
            if digest in seen:
                raise ValueError("deterministic sampler produced a duplicate input")
            seen.add(digest)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
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
    for projection in PROJECTIONS:
        candidate = {"projection": projection}
        if all(transform(pair["input"], candidate) == pair["output"]
               for pair in episode.get("train", [])):
            survivors.append(candidate)
    if survivors != [settings]:
        raise ValueError(f"demonstrations do not identify one setting: {survivors}")
    for pair in episode.get("train", []) + episode.get("test", []):
        _grid(pair["input"])
        _grid(pair["output"])
        if transform(pair["input"], settings) != pair["output"]:
            raise ValueError("claimed label differs from selected transform")
    return {"schema": "stacked-xor-projection-teaching-v1",
            "fit_scope": "demonstrations_only", "survivors": survivors}


def execute_rule(source, grid, *, bridge=None):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    _grid(grid)
    owned = bridge is None
    bridge = RacketBridge(timeout=30) if owned else bridge
    try:
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return _grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
    finally:
        if owned:
            bridge.close()


def source_bindings():
    files = [HERE / name for name in (
        "prototype.py", "adapter.py", "promotion.json",
        "cellwise_xor.rkt", "largest_component_bbox.rkt")]
    files.append(HERE.parents[1] / "generator.py")
    root = HERE.parents[3]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files}
