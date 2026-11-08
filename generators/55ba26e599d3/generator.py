"""Semantic generator for ARC task 55ba26e599d3.

Exactly two red (2) cells are endpoints of a digital differential analyzer
(DDA) line.  Visit ``max(abs(dr), abs(dc)) + 1`` evenly spaced rounded
coordinates from the first endpoint to the second.  On that path, replace
zero with red (2), replace blue (1) with green (3), and preserve every other
cell.  The published inputs contain only 0, 1, and 2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "55ba26e599d3"
TASK_ID = "55ba26e599d3"
VERSION = "3.0.1"
RULE_HASH = "bf0d32795830"
MIN_SYNTHETIC_CHANGE_RATE = 0.03
SUMMARY = "Draw the rounded DDA line between two red endpoints, mapping path zeros to red and path blues to green."
INVARIANTS = [
    "the input contains exactly two red (2) endpoints",
    "DDA uses max absolute row/column delta steps and round-to-even coordinates",
    "a path zero becomes red (2) and a path blue (1) becomes green (3)",
    "both endpoint cells remain red",
    "every cell outside the DDA path remains unchanged",
    "each synthetic scene witnesses both path mappings",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "border_horizontal",
    "border_vertical",
    "border_diagonal_down_right",
    "border_diagonal_down_left",
    "border_shallow_down_right",
    "border_shallow_down_left",
    "border_steep_down_right",
    "border_steep_down_left",
    "interior_horizontal",
    "interior_vertical",
    "interior_down_right",
    "interior_down_left",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve recoverable DDA-line lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = (
    "011010100000/001001001100/001000111110/000000010110/101001100011/110100011000/100100000000/000010000000/201110010012/010000010100/100010010111/001001011010",
    "2000000000001110/0000000111110010/0100000010010011/0000000000111011/0110110011110100/0001111101101111/0100000000101000/0001100010000110/1000100101010011/1111110010110100/0111010100010001/0001000001000001/0000000000110010/1001010100001101/0000010110000101/0100101000001002",
    "0111002001/1010111011/0000000010/0100001110/1110001001/1111110010/0110101010/1000101101/0111100111/0101002110",
    "110101011101111112/110010100010001011/011000010011010000/111000011000101001/010100101000000100/110110110011101011/100000000100110101/110011110010011111/001111100010111100/111010000101001110/000001100000010100/001110110001101111/111101101111101001/110010101111110000/100100011001101010/111111101001110100/110001010010010111/201100000111101000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return ["input dimensions must be between 5 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1, 2) for row in grid for value in row):
        return ["input cells must be literal integers from {0, 1, 2}"]
    return []


def _endpoints(grid):
    return tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 2)


def _line_cells(first, second):
    row1, col1 = first
    row2, col2 = second
    drow, dcol = row2 - row1, col2 - col1
    steps = max(abs(drow), abs(dcol))
    if steps == 0:
        return ((row1, col1),)
    return tuple(
        (round(row1 + index * drow / steps), round(col1 + index * dcol / steps))
        for index in range(steps + 1)
    )


def _apply_rule(grid, endpoints):
    output = [list(row) for row in grid]
    for row, col in _line_cells(*endpoints):
        if grid[row][col] == 0:
            output[row][col] = 2
        elif grid[row][col] == 1:
            output[row][col] = 3
    return output


def rule_mirror(grid):
    """Exact Python mirror of the canonical DDA and path-color rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    endpoints = _endpoints(grid)
    if len(endpoints) != 2:
        raise ValueError(f"expected exactly two red endpoints, got {len(endpoints)}")
    return _apply_rule(grid, endpoints)


def _on_border(point, height, width):
    row, col = point
    return row in (0, height - 1) or col in (0, width - 1)


def _geometry_profile(grid, endpoints):
    height, width = len(grid), len(grid[0])
    first, second = endpoints
    drow, dcol = second[0] - first[0], second[1] - first[1]
    borders = (_on_border(first, height, width), _on_border(second, height, width))
    if borders == (False, False):
        if drow == 0:
            return "interior_horizontal"
        if dcol == 0:
            return "interior_vertical"
        return "interior_down_right" if dcol > 0 else "interior_down_left"
    if borders != (True, True):
        return None
    if drow == 0:
        return "border_horizontal"
    if dcol == 0:
        return "border_vertical"
    direction = "down_right" if dcol > 0 else "down_left"
    if abs(drow) == abs(dcol):
        return f"border_diagonal_{direction}"
    if abs(drow) < abs(dcol):
        return f"border_shallow_{direction}"
    return f"border_steep_{direction}"


def _profile_for(grid, endpoints):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    return public or _geometry_profile(grid, endpoints)


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    endpoints = _endpoints(grid)
    if len(endpoints) != 2:
        return {"errors": [f"expected exactly two red endpoints, got {len(endpoints)}"], "scene_profile": None, "facts": None, "output": None}
    path = _line_cells(*endpoints)
    interior = path[1:-1]
    profile = _profile_for(grid, endpoints)
    if len(interior) < 2:
        errors.append("endpoint separation must leave at least two interior path cells")
    if not any(grid[row][col] == 0 for row, col in interior):
        errors.append("DDA interior must witness the zero-to-red mapping")
    if not any(grid[row][col] == 1 for row, col in interior):
        errors.append("DDA interior must witness the blue-to-green mapping")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared DDA geometry profile")
    output = _apply_rule(grid, endpoints)
    if output == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    facts = {
        "endpoints": endpoints,
        "path": path,
        "interior": interior,
        "drow": endpoints[1][0] - endpoints[0][0],
        "dcol": endpoints[1][1] - endpoints[0][1],
        "scene_profile": profile,
    }
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _band_limits(difficulty):
    if difficulty == "easy":
        return 8, 12
    if difficulty == "medium":
        return 12, 18
    if difficulty == "hard":
        return 18, 24
    return 10, 20


def _shape_for(profile, difficulty, rng):
    low, high = _band_limits(difficulty)
    if "diagonal" in profile:
        size = rng.randint(low, high)
        return size, size
    if "shallow" in profile:
        height = rng.randint(low, high - 3)
        return height, rng.randint(height + 3, high)
    if "steep" in profile:
        width = rng.randint(low, high - 3)
        return rng.randint(width + 3, high), width
    return rng.randint(low, high), rng.randint(low, high)


def _general_endpoints(profile, height, width, rng):
    if profile == "border_horizontal":
        row = rng.randint(0, height - 1)
        return (row, 0), (row, width - 1)
    if profile == "border_vertical":
        col = rng.randint(0, width - 1)
        return (0, col), (height - 1, col)
    if profile.endswith("down_right") and profile.startswith("border_"):
        return (0, 0), (height - 1, width - 1)
    if profile.endswith("down_left") and profile.startswith("border_"):
        return (0, width - 1), (height - 1, 0)
    if profile == "interior_horizontal":
        row = rng.randint(1, height - 2)
        return (row, 1), (row, width - 2)
    if profile == "interior_vertical":
        col = rng.randint(1, width - 2)
        return (1, col), (height - 2, col)
    upper_row = rng.randint(1, max(1, height // 4))
    lower_row = rng.randint(min(height - 2, 3 * height // 4), height - 2)
    if profile == "interior_down_right":
        return (upper_row, rng.randint(1, max(1, width // 4))), (lower_row, rng.randint(min(width - 2, 3 * width // 4), width - 2))
    return (upper_row, rng.randint(min(width - 2, 3 * width // 4), width - 2)), (lower_row, rng.randint(1, max(1, width // 4)))


def _general_scene(profile, difficulty, rng):
    for _ in range(100):
        height, width = _shape_for(profile, difficulty, rng)
        endpoints = _general_endpoints(profile, height, width, rng)
        path = _line_cells(*endpoints)
        if len(path) < 4:
            continue
        density_low, density_high = {
            "easy": (0.28, 0.40),
            "medium": (0.34, 0.48),
            "hard": (0.40, 0.56),
        }.get(difficulty, (0.30, 0.52))
        density = rng.uniform(density_low, density_high)
        grid = [[1 if rng.random() < density else 0 for _ in range(width)] for _ in range(height)]
        zero_witness, one_witness = rng.sample(path[1:-1], 2)
        grid[zero_witness[0]][zero_witness[1]] = 0
        grid[one_witness[0]][one_witness[1]] = 1
        for row, col in endpoints:
            grid[row][col] = 2
        analysis = _analysis(grid)
        changed = sum(
            before != after
            for input_row, output_row in zip(grid, analysis["output"] or ())
            for before, after in zip(input_row, output_row)
        )
        change_rate = changed / (height * width)
        if not analysis["errors"] and analysis["scene_profile"] == profile and change_rate >= MIN_SYNTHETIC_CHANGE_RATE:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(profile, difficulty, ctx.draw_rng("scene"))
