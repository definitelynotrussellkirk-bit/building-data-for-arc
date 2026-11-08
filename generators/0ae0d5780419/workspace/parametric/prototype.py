"""Parametric transform-matching family for 0ae0d5780419.

Every setting first crops the three divider-delimited panels. Step A compares
transformed A against B and produces an input-dependent transform code. Step B
applies that code to cropped C. The episode-fixed parameter changes only the
matching policy: first exact colored match (canonical), last exact colored
match, or first shape-only match.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

TASK_ID = "0ae0d5780419"
MATCH_POLICIES = ("first_exact", "last_exact", "first_shape")
DEFAULT_POLICY = "first_exact"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

_HERE = Path(__file__).resolve().parent
_RULES = {
    "first_exact": _HERE / "rules" / "canonical.rkt",
    "last_exact": _HERE / "rules" / "last_exact.rkt",
    "first_shape": _HERE / "rules" / "first_shape.rkt",
}
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_TRANSFORMS = (1, 2, 3, 4, 5, 6)
_PRIORITY_TEMPLATES = (
    (2, [[1, 0, 0], [1, 0, 0], [1, 1, 1]]),
    (5, [[0, 1], [1, 1], [1, 0]]),
)
_DEMO_SPECS = (
    ("priority", 5, 5),
    ("shape_recolored", 7, 7),
    ("color_sensitive_exact", 9, 6),
    ("no_match", 12, 7),
    ("exact_unique", 18, 8),
    ("priority", 24, 9),
)
_QUERY_SPECS = (
    ("priority", 8, 5),
    ("color_sensitive_exact", 14, 7),
    ("shape_recolored", 24, 9),
    ("large_priority", 30, 9),
)


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in [{low}, {high}]")
    return value


def _policy(value: str) -> str:
    if type(value) is not str or value not in MATCH_POLICIES:
        raise ValueError(f"match_policy must be one of {MATCH_POLICIES}")
    return value


def rule_text(match_policy: str) -> str:
    return _RULES[_policy(match_policy)].read_text()


def _tf(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    return [row[:] for row in grid]


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _mask(grid: list[list[int]]) -> list[list[int]]:
    return [[1 if value != 0 else 0 for value in row] for row in grid]


def _crop(grid: list[list[int]]) -> list[list[int]] | None:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return None
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [values[left : right + 1] for values in grid[top : bottom + 1]]


def _bbox(grid: list[list[int]]) -> tuple[int, int, int, int] | None:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return None
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _split_panels(grid: list[list[int]]) -> tuple[list[int], list[list[list[int]]]]:
    height = len(grid)
    width = len(grid[0])
    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    panels: list[list[list[int]]] = []
    start = 0
    for stop in dividers + [width]:
        if stop > start:
            panels.append([row[start:stop] for row in grid])
        start = stop + 1
    return dividers, panels


def analyse(grid: list[list[int]]) -> dict:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal ARC integers")
    dividers, panels = _split_panels(grid)
    if len(dividers) != 2 or len(panels) != 3:
        raise ValueError("expected exactly three panels and two full-height color-5 dividers")
    panel_widths = [len(panel[0]) for panel in panels]
    if len(set(panel_widths)) != 1:
        raise ValueError("panels must have equal width")
    divider_set = set(dividers)
    if any(
        grid[row][col] == 5 and col not in divider_set
        for row in range(len(grid))
        for col in range(width)
    ):
        raise ValueError("color 5 is reserved for dividers")
    crops = [_crop(panel) for panel in panels]
    if any(crop is None for crop in crops):
        raise ValueError("all panels must contain content")
    a, b, c = crops
    exact_matches = tuple(code for code in _TRANSFORMS if _tf(a, code) == b)
    shape_matches = tuple(code for code in _TRANSFORMS if _tf(_mask(a), code) == _mask(b))
    return {
        "panel_h": len(grid),
        "panel_n": panel_widths[0],
        "dividers": tuple(dividers),
        "panels": panels,
        "crops": crops,
        "bboxes": tuple(_bbox(panel) for panel in panels),
        "exact_matches": exact_matches,
        "shape_matches": shape_matches,
        "c_crop": c,
    }


def _selected_code(facts: dict, policy: str) -> int:
    if policy == "first_shape":
        matches = facts["shape_matches"]
        return matches[0] if matches else 1
    matches = facts["exact_matches"]
    if not matches:
        return 1
    return matches[0] if policy == "first_exact" else matches[-1]


def apply_policy(grid: list[list[int]], match_policy: str) -> list[list[int]]:
    policy = _policy(match_policy)
    facts = analyse(grid)
    return _tf(facts["c_crop"], _selected_code(facts, policy))


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:panel-match-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _pattern(
    rng: random.Random,
    height: int,
    width: int,
    *,
    density: float,
    colors: tuple[int, ...] | list[int],
    require_mask_unique: bool = False,
    require_color_unique: bool = True,
) -> list[list[int]]:
    colors = tuple(colors)
    if not colors or any(color in (0, 5) for color in colors):
        raise ValueError("pattern colors must be nonzero and exclude divider color 5")
    total = height * width
    count = max(len(colors), 4, min(total, int(round(total * density))))
    forced = {(0, 0), (height - 1, width - 1)}
    if width > 2:
        forced.add((0, width - 2))
    if height > 2:
        forced.add((height - 2, 0))
    count = max(count, len(forced))
    positions = [(row, col) for row in range(height) for col in range(width)]
    for _ in range(2048):
        chosen = set(forced)
        remaining = [position for position in positions if position not in chosen]
        chosen.update(rng.sample(remaining, count - len(chosen)))
        grid = [[0] * width for _ in range(height)]
        ordered = sorted(chosen)
        rng.shuffle(ordered)
        for index, (row, col) in enumerate(ordered):
            grid[row][col] = colors[index % len(colors)] if index < len(colors) else rng.choice(colors)
        colored_views = {_grid_key(_tf(grid, code)) for code in _TRANSFORMS}
        mask_views = {_grid_key(_tf(_mask(grid), code)) for code in _TRANSFORMS}
        if require_color_unique and len(colored_views) != 6:
            continue
        if require_mask_unique and len(mask_views) != 6:
            continue
        return grid
    raise RuntimeError("could not construct a sufficiently asymmetric pattern")


def _full_colored_pattern(rng: random.Random, side: int, colors: tuple[int, ...]) -> list[list[int]]:
    for _ in range(2048):
        grid = [[rng.choice(colors) for _ in range(side)] for _ in range(side)]
        for index, color in enumerate(colors):
            grid[index // side][index % side] = color
        if len({_grid_key(_tf(grid, code)) for code in _TRANSFORMS}) == 6:
            return grid
    raise RuntimeError("could not construct asymmetric full colored pattern")


def _recolor_mask(mask: list[list[int]], rng: random.Random, colors: tuple[int, ...]) -> list[list[int]]:
    cells = [(row, col) for row, values in enumerate(mask) for col, value in enumerate(values) if value]
    out = [[0] * len(mask[0]) for _ in mask]
    shuffled = cells[:]
    rng.shuffle(shuffled)
    for index, (row, col) in enumerate(shuffled):
        out[row][col] = colors[index % len(colors)] if index < len(colors) else rng.choice(colors)
    return out


def _embed(
    crop: list[list[int]], panel_h: int, panel_n: int, rng: random.Random, *, edge: bool = False
) -> list[list[int]]:
    crop_h, crop_w = len(crop), len(crop[0])
    if crop_h > panel_h or crop_w > panel_n:
        raise ValueError(f"crop {crop_h}x{crop_w} does not fit panel {panel_h}x{panel_n}")
    panel = [[0] * panel_n for _ in range(panel_h)]
    if edge:
        top = min(1, panel_h - crop_h)
        left = min(1, panel_n - crop_w)
    else:
        top_options = list(range(panel_h - crop_h + 1))
        left_options = list(range(panel_n - crop_w + 1))
        if len(top_options) > 1:
            top_options = [value for value in top_options if value != 0] or top_options
        if len(left_options) > 1:
            left_options = [value for value in left_options if value != 0] or left_options
        top = rng.choice(top_options)
        left = rng.choice(left_options)
    for row in range(crop_h):
        for col in range(crop_w):
            panel[top + row][left + col] = crop[row][col]
    return panel


def _assemble(
    panel_h: int,
    panel_n: int,
    a_crop: list[list[int]],
    b_crop: list[list[int]],
    c_crop: list[list[int]],
    rng: random.Random,
    *,
    edge: bool = False,
) -> list[list[int]]:
    panels = [
        _embed(a_crop, panel_h, panel_n, rng, edge=edge),
        _embed(b_crop, panel_h, panel_n, rng, edge=edge),
        _embed(c_crop, panel_h, panel_n, rng, edge=edge),
    ]
    d1, d2 = panel_n, 2 * panel_n + 1
    width = 3 * panel_n + 2
    grid = [[0] * width for _ in range(panel_h)]
    for row in range(panel_h):
        grid[row][d1] = 5
        grid[row][d2] = 5
    for panel, offset in zip(panels, (0, d1 + 1, d2 + 1)):
        for row in range(panel_h):
            for col in range(panel_n):
                if panel[row][col] != 0:
                    grid[row][offset + col] = panel[row][col]
    return grid


def _priority_scene(rng: random.Random, panel_h: int, panel_n: int, variant: int):
    code, template = _PRIORITY_TEMPLATES[variant % len(_PRIORITY_TEMPLATES)]
    color = rng.choice(_COLORS)
    a = [[color if value else 0 for value in row] for row in template]
    b = _tf(a, code)
    c = _pattern(
        rng,
        min(panel_h - 1, 5),
        min(panel_n - 1, 4),
        density=0.55,
        colors=(rng.choice([value for value in _COLORS if value != color]),),
        require_mask_unique=True,
    )
    grid = _assemble(panel_h, panel_n, a, b, c, rng)
    facts = analyse(grid)
    if len(facts["exact_matches"]) < 2 or facts["exact_matches"][0] != code:
        raise RuntimeError("priority scene failed to preserve its first match")
    if _tf(c, facts["exact_matches"][0]) == _tf(c, facts["exact_matches"][-1]):
        raise RuntimeError("priority scene does not distinguish first and last matches")
    return grid


def _shape_recolored_scene(rng: random.Random, panel_h: int, panel_n: int, code: int):
    height = min(panel_h - 2, 6)
    width = min(panel_n - 2, 5)
    if height == width:
        width = max(3, width - 1)
    a = _pattern(
        rng,
        height,
        width,
        density=0.55,
        colors=(1, 2),
        require_mask_unique=True,
    )
    transformed_mask = _tf(_mask(a), code)
    b = _recolor_mask(transformed_mask, rng, (6, 8))
    c = _pattern(
        rng,
        min(panel_h - 2, 7),
        min(panel_n - 2, 6),
        density=0.50,
        colors=(3, 7, 9),
        require_mask_unique=True,
    )
    grid = _assemble(panel_h, panel_n, a, b, c, rng)
    facts = analyse(grid)
    if facts["exact_matches"] or facts["shape_matches"] != (code,):
        raise RuntimeError("shape-recolored scene did not isolate its shape match")
    return grid


def _color_sensitive_exact_scene(rng: random.Random, panel_h: int, panel_n: int, code: int):
    side = min(5, panel_h - 2, panel_n - 2)
    a = _full_colored_pattern(rng, side, (1, 3, 7))
    b = _tf(a, code)
    c = _pattern(
        rng,
        min(panel_h - 2, 7),
        min(panel_n - 2, 6),
        density=0.58,
        colors=(2, 4, 8),
        require_mask_unique=True,
    )
    grid = _assemble(panel_h, panel_n, a, b, c, rng)
    facts = analyse(grid)
    if facts["exact_matches"] != (code,) or facts["shape_matches"][0] != 1:
        raise RuntimeError("color-sensitive scene did not separate shape and exact matching")
    return grid


def _no_match_scene(rng: random.Random, panel_h: int, panel_n: int):
    height = min(panel_h - 2, 6)
    width = min(panel_n - 2, 5)
    a = _pattern(
        rng,
        height,
        width,
        density=0.48,
        colors=(4,),
        require_mask_unique=True,
    )
    transformed_masks = {_grid_key(_tf(_mask(a), code)) for code in _TRANSFORMS}
    for _ in range(2048):
        b = _pattern(
            rng,
            height,
            width,
            density=0.67,
            colors=(4,),
            require_mask_unique=True,
        )
        if _grid_key(_mask(b)) not in transformed_masks:
            break
    else:
        raise RuntimeError("could not construct a no-match B crop")
    c = _pattern(
        rng,
        min(panel_h - 2, 7),
        min(panel_n - 2, 6),
        density=0.55,
        colors=(2, 6),
        require_mask_unique=True,
    )
    grid = _assemble(panel_h, panel_n, a, b, c, rng)
    facts = analyse(grid)
    if facts["exact_matches"] or facts["shape_matches"]:
        raise RuntimeError("no-match scene unexpectedly has a transform match")
    return grid


def _exact_unique_scene(rng: random.Random, panel_h: int, panel_n: int, code: int):
    height = min(panel_h - 2, 7)
    width = min(panel_n - 2, 6)
    a = _pattern(
        rng,
        height,
        width,
        density=0.52,
        colors=(1, 4, 8),
        require_mask_unique=True,
    )
    b = _tf(a, code)
    c = _pattern(
        rng,
        min(panel_h - 2, 8),
        min(panel_n - 2, 7),
        density=0.54,
        colors=(2, 6, 9),
        require_mask_unique=True,
    )
    grid = _assemble(panel_h, panel_n, a, b, c, rng)
    facts = analyse(grid)
    if facts["exact_matches"] != (code,) or facts["shape_matches"] != (code,):
        raise RuntimeError("unique scene did not isolate a common transform")
    return grid


def _large_priority_scene(rng: random.Random, panel_h: int, panel_n: int):
    height = panel_h - 2
    width = panel_n
    for _ in range(1024):
        a = [[0] * width for _ in range(height)]
        for row in range((height + 1) // 2):
            for col in range(width):
                rr, cc = height - 1 - row, width - 1 - col
                if rng.random() < 0.48 or (row, col) in {(0, 0), (0, width - 1)}:
                    color = rng.choice(_COLORS)
                    a[row][col] = color
                    a[rr][cc] = color
        if _crop(a) is None:
            continue
        if tuple(code for code in _TRANSFORMS if _tf(a, code) == a) == (1, 3):
            break
    else:
        raise RuntimeError("could not construct large 180-degree priority crop")
    b = copy.deepcopy(a)
    c = _pattern(
        rng,
        height,
        width,
        density=0.52,
        colors=(1, 2, 3, 4, 6, 7, 8, 9),
        require_mask_unique=True,
    )
    grid = _assemble(panel_h, panel_n, a, b, c, rng, edge=True)
    facts = analyse(grid)
    if facts["exact_matches"] != (1, 3):
        raise RuntimeError("large priority scene exact-match set drifted")
    if _tf(c, 1) == _tf(c, 3):
        raise RuntimeError("large priority C crop is 180-degree symmetric")
    return grid


def _make_input(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _DEMO_SPECS if split == "train" else _QUERY_SPECS
    profile, panel_h, panel_n = specs[index]
    rng = _rng(seed, split, index)
    variant = (seed + index) % 2
    if profile == "priority":
        return _priority_scene(rng, panel_h, panel_n, variant)
    if profile == "shape_recolored":
        code = (4, 6)[variant]
        return _shape_recolored_scene(rng, panel_h, panel_n, code)
    if profile == "color_sensitive_exact":
        code = (3, 4)[variant]
        return _color_sensitive_exact_scene(rng, panel_h, panel_n, code)
    if profile == "no_match":
        return _no_match_scene(rng, panel_h, panel_n)
    if profile == "exact_unique":
        code = (2, 5)[variant]
        return _exact_unique_scene(rng, panel_h, panel_n, code)
    if profile == "large_priority":
        return _large_priority_scene(rng, panel_h, panel_n)
    raise ValueError(profile)


def _fixed_transform(code: int) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: _tf(analyse(grid)["c_crop"], code)


def audit_rivals(match_policy: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    policy = _policy(match_policy)
    others = [candidate for candidate in MATCH_POLICIES if candidate != policy]

    def last_shape_match(grid):
        facts = analyse(grid)
        matches = facts["shape_matches"]
        return _tf(facts["c_crop"], matches[-1] if matches else 1)

    def rotate_cw_on_no_exact_match(grid):
        facts = analyse(grid)
        matches = facts["exact_matches"]
        code = matches[0] if matches else 2
        return _tf(facts["c_crop"], code)

    def transform_padded_c_without_crop(grid):
        facts = analyse(grid)
        return _tf(facts["panels"][2], _selected_code(facts, policy))

    return {
        "other_finite_policy_1": lambda grid: apply_policy(grid, others[0]),
        "other_finite_policy_2": lambda grid: apply_policy(grid, others[1]),
        "last_shape_match": last_shape_match,
        "rotate_cw_on_no_exact_match": rotate_cw_on_no_exact_match,
        "transform_padded_c_without_crop": transform_padded_c_without_crop,
        "always_identity": _fixed_transform(1),
        "always_rotate_cw": _fixed_transform(2),
    }


def public_projection(episode: dict) -> dict:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_challenge_bytes(episode: dict) -> bytes:
    return json.dumps(
        public_projection(episode),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode() + b"\n"


def public_challenge_id(episode: dict) -> str:
    return hashlib.sha256(public_challenge_bytes(episode)).hexdigest()


def generate_episode(
    seed: int,
    *,
    match_policy: str = DEFAULT_POLICY,
    demos: int = 3,
    queries: int = 4,
) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    policy = _policy(match_policy)
    _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _integer("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train_inputs = [_make_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_make_input(seed, "test", index) for index in range(queries)]
    train = [
        {"input": copy.deepcopy(grid), "output": apply_policy(grid, policy)}
        for grid in train_inputs
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": apply_policy(grid, policy)}
        for grid in test_inputs
    ]
    episode = {
        "schema": "panel-transform-match-policy-parametric-v1",
        "status": "proposed",
        "approved": False,
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"match_policy": policy},
        "demo_count": demos,
        "query_count": queries,
        "train": train,
        "test": test,
        "program_solution": rule_text(policy),
    }
    episode["public_challenge_id"] = public_challenge_id(episode)
    return episode
