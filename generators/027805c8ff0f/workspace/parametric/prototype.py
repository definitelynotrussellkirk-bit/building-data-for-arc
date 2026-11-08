"""Parametric transform-analogy episodes with an input-derived intermediate.

The canonical setting infers the A→B transform and applies it once to C.  The
alternate setting infers the same transform from the same input, then applies it
twice.  Inputs never depend on the hidden setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "027805c8ff0f"
HOME = Path(__file__).resolve().parent
APPLICATIONS = ("once", "twice")
COLORS = tuple(range(2, 10))
TRANSFORM_CODES = (2, 3, 4, 5, 6)
# Each tuple is (height, panel_width, direct-fixture transform code).  Generation
# uses a seed-keyed permutation instead, so dimensions do not reveal Step A.
# Width is 3*w+2.
DEMO_PROFILES = (
    (7, 5, 2),
    (9, 6, 3),
    (12, 7, 4),
    (16, 8, 5),
    (20, 9, 6),
    (30, 9, 5),
)
QUERY_PROFILES = (
    (6, 4, 3),
    (11, 7, 4),
    (18, 8, 6),
    (30, 9, 5),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"applications"}
            or type(settings["applications"]) is not str
            or settings["applications"] not in APPLICATIONS):
        raise ValueError("settings must contain exactly applications=once|twice")
    return {"applications": settings["applications"]}


def _strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a non-empty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must use rectangular exact integer colors 0..9")
    return grid


def program(settings):
    return (HOME / "rules" / f"{_settings(settings)['applications']}.rkt").read_text(
        encoding="utf-8"
    )


def _crop(grid):
    _strict_grid(grid)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not occupied:
        raise ValueError("panel content must be non-empty")
    r0 = min(r for r, _ in occupied)
    r1 = max(r for r, _ in occupied)
    c0 = min(c for _, c in occupied)
    c1 = max(c for _, c in occupied)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _xform(grid, code):
    _strict_grid(grid)
    _integer(code, 1, 6, "transform code")
    if code == 1:
        return deepcopy(grid)
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [row[::-1] for row in grid]
    return grid[::-1]


def _panels(grid):
    _strict_grid(grid)
    height, width = len(grid), len(grid[0])
    if (width - 2) % 3:
        raise ValueError("input width must be 3*panel_width+2")
    panel_width = (width - 2) // 3
    if not 1 <= panel_width <= 9:
        raise ValueError("panel width must be in 1..9")
    if any(row[panel_width] != 1 or row[2 * panel_width + 1] != 1 for row in grid):
        raise ValueError("input requires two full color-1 divider columns")
    panels = [
        [row[index * (panel_width + 1):index * (panel_width + 1) + panel_width] for row in grid]
        for index in range(3)
    ]
    cropped = [_crop(panel) for panel in panels]
    a_colors = {value for row in cropped[0] for value in row if value}
    b_colors = {value for row in cropped[1] for value in row if value}
    c_colors = {value for row in cropped[2] for value in row if value}
    if (len(a_colors) != 1 or a_colors != b_colors or len(c_colors) != 1
            or next(iter(a_colors)) == 1 or next(iter(c_colors)) == 1):
        raise ValueError("A/B need one shared non-divider color and C one color")
    return cropped


def infer_transform(grid):
    a, b, _ = _panels(grid)
    for code in range(1, 7):
        if _xform(a, code) == b:
            return code
    raise ValueError("A and B have no transform match")


def extract_query(grid):
    return deepcopy(_panels(grid)[2])


def transform(grid, settings):
    applications = _settings(settings)["applications"]
    code = infer_transform(grid)
    result = extract_query(grid)
    for _ in range(1 if applications == "once" else 2):
        result = _xform(result, code)
    return result


def _rng(seed, stream, index, attempt=0):
    key = json.dumps([TASK_ID, seed, stream, index, attempt], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _transform_schedule(seed, stream, count):
    """Seed-keyed non-identity codes; profile dimensions carry no code signal."""
    result = []
    cycle_index = 0
    while len(result) < count:
        block = list(TRANSFORM_CODES)
        _rng(seed, f"{stream}:transform_schedule", cycle_index).shuffle(block)
        result.extend(block)
        cycle_index += 1
    return result[:count]


def _pattern(rng, height, width, count, *, span=False):
    area = height * width
    count = max(5, min(count, area))
    required = {(0, 0), (height - 1, 0), (height - 1, width - 1), (0, min(1, width - 1))}
    if span and width > 2:
        required.add((height // 2, width - 1))
    remaining = [(r, c) for r in range(height) for c in range(width) if (r, c) not in required]
    rng.shuffle(remaining)
    cells = required | set(remaining[:max(0, count - len(required))])
    return [[1 if (r, c) in cells else 0 for c in range(width)] for r in range(height)]


def _orbit_unique(pattern):
    encodings = {
        json.dumps(_xform(pattern, code), separators=(",", ":"))
        for code in range(1, 7)
    }
    return len(encodings) == 6


def _colored(pattern, color):
    return [[color if value else 0 for value in row] for row in pattern]


def _place(panel, patch, row0, col0):
    if row0 < 0 or col0 < 0 or row0 + len(patch) > len(panel) or col0 + len(patch[0]) > len(panel[0]):
        raise ValueError("patch does not fit panel")
    for r, row in enumerate(patch):
        for c, value in enumerate(row):
            if value:
                panel[row0 + r][col0 + c] = value


def sample_input(seed, stream, index, height, panel_width, *, transform_code):
    """Construct one setting-independent analogy input.

    Every A and C pattern has six distinct transform images.  Thus the declared
    A→B code is the first match and applying that code once versus twice always
    changes the label.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 1000, "index")
    _integer(height, 3, 30, "height")
    _integer(panel_width, 3, 9, "panel_width")
    _integer(transform_code, 2, 6, "transform_code")
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a non-empty string")
    swaps_axes = transform_code in (2, 4)
    patch_h = min(height, panel_width if swaps_axes else max(4, height))
    patch_w = min(panel_width, patch_h if swaps_axes else max(3, panel_width))
    if height == 30 and panel_width == 9 and not swaps_axes:
        patch_h, patch_w = 30, 9
    for attempt in range(256):
        rng = _rng(seed, stream, index, attempt)
        a_binary = _pattern(
            rng, patch_h, patch_w,
            max(7, (patch_h * patch_w) // (3 if patch_h < 20 else 5)),
            span=height == 30,
        )
        c_binary = _pattern(
            rng, patch_h, patch_w,
            max(8, (patch_h * patch_w) // (4 if patch_h < 20 else 6)),
            span=height == 30,
        )
        if not _orbit_unique(a_binary) or not _orbit_unique(c_binary):
            continue
        b_binary = _xform(a_binary, transform_code)
        if len(b_binary) > height or len(b_binary[0]) > panel_width:
            continue
        color_a, color_c = rng.sample(COLORS, 2)
        panels = [[[0] * panel_width for _ in range(height)] for _ in range(3)]
        patches = (_colored(a_binary, color_a), _colored(b_binary, color_a), _colored(c_binary, color_c))
        for panel_index, (panel, patch) in enumerate(zip(panels, patches)):
            if height == 30 and swaps_axes:
                # Square patches cannot span 30 rows.  Put A/C high and B low;
                # the middle panel crosses the horizontal quadrant split, so
                # the full three-panel input has substantive content everywhere.
                row0 = height - len(patch) if panel_index == 1 else 0
            elif height == 30:
                row0 = 0
            else:
                row0 = rng.randrange(height - len(patch) + 1)
            col0 = rng.randrange(panel_width - len(patch[0]) + 1)
            _place(panel, patch, row0, col0)
        grid = [panels[0][r] + [1] + panels[1][r] + [1] + panels[2][r] for r in range(height)]
        if infer_transform(grid) != transform_code:
            continue
        if transform(grid, {"applications": "once"}) == transform(grid, {"applications": "twice"}):
            continue
        return grid
    raise ValueError("could not construct a six-way asymmetric analogy input")


def retarget_transform(grid, transform_code):
    """Keep A and C fixed while rebuilding B for a different inferred code."""
    _integer(transform_code, 1, 6, "transform_code")
    source = deepcopy(_strict_grid(grid))
    height, width = len(source), len(source[0])
    panel_width = (width - 2) // 3
    a, _, _ = _panels(source)
    replacement = _xform(a, transform_code)
    if len(replacement) > height or len(replacement[0]) > panel_width:
        raise ValueError("retargeted B does not fit")
    for r in range(height):
        for c in range(panel_width + 1, 2 * panel_width + 1):
            source[r][c] = 0
    row0 = (height - len(replacement)) // 2
    col0 = panel_width + 1 + (panel_width - len(replacement[0])) // 2
    for r, row in enumerate(replacement):
        for c, value in enumerate(row):
            source[row0 + r][col0 + c] = value
    if infer_transform(source) != transform_code:
        raise ValueError("retargeting did not create the requested first match")
    return source


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    chosen = _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [],
        "test": [],
        "program_solution": program(chosen),
        "settings": chosen,
        "seed": seed,
    }
    seen = set()
    for split, profiles, count in (
        ("train", DEMO_PROFILES, demos),
        ("test", QUERY_PROFILES, queries),
    ):
        codes = _transform_schedule(seed, split, len(profiles))
        for index, (height, panel_width, _fixture_code) in enumerate(profiles[:count]):
            grid = sample_input(
                seed, split, index, height, panel_width, transform_code=codes[index]
            )
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("sampler produced a duplicate input")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, chosen)})
    return result


def verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = _settings(episode.get("settings"))
    chosen = settings["applications"]
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution differs from the selected program")
    seen = set()
    for split, low, high in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not low <= len(pairs) <= high:
            raise ValueError(f"{split} count is outside supported limits")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("every pair needs input and output")
            _strict_grid(pair["input"])
            _strict_grid(pair["output"])
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate input")
            seen.add(key)
            if transform(pair["input"], settings) != pair["output"]:
                raise ValueError(f"{split} label differs from the selected rule")
    survivors = [
        value for value in APPLICATIONS
        if all(transform(pair["input"], {"applications": value}) == pair["output"]
               for pair in episode["train"])
    ]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the selected setting: {survivors}")
    return {
        "schema": "transform-application-self-review-v1",
        "survivors": survivors,
        "fit_uses": "demonstrations_only",
        "query_labels_checked": len(episode["test"]),
    }
