"""Semantic generator for ARC task 2c30a4753f6b.

The output is the input followed horizontally by its left-right reflection.
The original grid is preserved as the left half and the reflected grid is the
right half.  Generated lessons are deliberately left-right asymmetric so the
reflection is observable rather than confusable with simple duplication.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "2c30a4753f6b"
TASK_ID = "2c30a4753f6b"
VERSION = "3.0.0"
RULE_HASH = "692c01024e4b"
SUMMARY = "Append a horizontal reflection of the input to its right, producing an h by 2w grid."
INVARIANTS = [
    "the output left half equals the input exactly",
    "the output right half equals each input row reversed",
    "input width is at most 15 so doubled output width stays within ARC limits",
    "generated lessons are left-right asymmetric so reflection is visible",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "binary_sparse_3x3",
    "binary_dense_3x3",
    "single_marker",
    "connected_shape",
    "disconnected_markers",
    "multicolor_sparse",
    "dense_multicolor",
    "wide_asymmetric",
    "tall_asymmetric",
    "single_row",
    "near_symmetric",
    "edge_asymmetry",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve observable mirror lessons",
        "valid": "public_1|public_2|public_3|public_4|binary_sparse_3x3|binary_dense_3x3|single_marker|connected_shape|disconnected_markers|multicolor_sparse|dense_multicolor|wide_asymmetric|tall_asymmetric|single_row|near_symmetric|edge_asymmetry",
    }
}

_PUBLIC_ROWS = (
    "000/077/000",
    "070/007/077",
    "000/700/000",
    "770/070/007",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 2 <= width <= 15:
        return ["input dimensions must be h=1..30 and w=2..15"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [list(row) + list(reversed(row)) for row in grid]


def _is_lr_symmetric(grid):
    return all(list(row) == list(reversed(row)) for row in grid)


def _mismatch_pairs(grid):
    width = len(grid[0])
    return sum(
        grid[row][col] != grid[row][width - 1 - col]
        for row in range(len(grid))
        for col in range(width // 2)
    )


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    height, width = facts["height"], facts["width"]
    if facts["lr_symmetric"] or not facts["nonzero_count"]:
        return None
    if height == 1:
        return "single_row"
    if height == width == 3 and len(facts["nonzero_palette"]) == 1:
        if facts["nonzero_count"] == 1:
            return "single_marker"
        return "binary_sparse_3x3" if facts["nonzero_count"] <= 3 else "binary_dense_3x3"
    if facts["mismatch_pairs"] == 1:
        return "near_symmetric"
    if facts["edge_only"]:
        return "edge_asymmetry"
    if width >= 2 * height:
        return "wide_asymmetric"
    if height >= 2 * width:
        return "tall_asymmetric"
    if len(facts["nonzero_palette"]) >= 3 and facts["density"] >= 0.5:
        return "dense_multicolor"
    if len(facts["nonzero_palette"]) >= 2:
        return "multicolor_sparse"
    if facts["component_count"] >= 2:
        return "disconnected_markers"
    if facts["component_count"] == 1:
        return "connected_shape"
    return None


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    nonzero = [(row, col, value) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0]
    components = _components(grid)
    edge_only = bool(nonzero) and all(col in {0, width - 1} for _, col, _ in nonzero)
    solid_2x2 = bool(nonzero) and len(nonzero) == 4 and (
        max(row for row, _, _ in nonzero) - min(row for row, _, _ in nonzero) + 1 == 2
        and max(col for _, col, _ in nonzero) - min(col for _, col, _ in nonzero) + 1 == 2
    )
    flat = [value for row in grid for value in row]
    zero_is_mode = flat.count(0) > max((flat.count(color) for color in set(flat) if color != 0), default=0)
    facts = {
        "height": height,
        "width": width,
        "palette": sorted({value for row in grid for value in row}),
        "nonzero_palette": sorted({value for _, _, value in nonzero}),
        "nonzero_count": len(nonzero),
        "density": len(nonzero) / (height * width),
        "components": components,
        "component_count": len(components),
        "lr_symmetric": _is_lr_symmetric(grid),
        "mismatch_pairs": _mismatch_pairs(grid),
        "edge_only": edge_only,
        "solid_2x2": solid_2x2,
        "zero_is_mode": zero_is_mode,
        "output": rule_mirror(grid),
    }
    facts["scene_profile"] = _profile_for(grid, facts)
    return facts


def _profile_errors(facts):
    profile = facts["scene_profile"]
    if profile in PUBLIC_PROFILES:
        return []
    errors = []
    if facts["lr_symmetric"]:
        errors.append("generated lesson must make the left-right reflection observable")
    if not facts["zero_is_mode"]:
        errors.append("generated lesson requires zero to be the unique modal background")
    if 0 not in facts["palette"] or facts["nonzero_count"] == facts["height"] * facts["width"]:
        errors.append("generated lesson must retain zero background context")
    if profile == "binary_sparse_3x3" and not 2 <= facts["nonzero_count"] <= 3:
        errors.append("binary_sparse_3x3 requires two or three markers")
    if profile == "binary_sparse_3x3" and facts["solid_2x2"]:
        errors.append("binary_sparse_3x3 excludes the undeclared solid-2x2 impostor")
    if profile == "binary_dense_3x3" and facts["nonzero_count"] != 4:
        errors.append("binary_dense_3x3 requires four markers on a zero-modal field")
    if profile == "binary_dense_3x3" and facts["solid_2x2"]:
        errors.append("binary_dense_3x3 excludes the undeclared solid-2x2 impostor")
    if profile == "single_marker" and facts["nonzero_count"] != 1:
        errors.append("single_marker requires exactly one canonical-style marker")
    if profile == "connected_shape" and (facts["component_count"] != 1 or facts["nonzero_count"] < 5 or len(facts["nonzero_palette"]) != 1):
        errors.append("connected_shape requires one substantial monochrome component")
    if profile == "disconnected_markers" and not 2 <= facts["component_count"] <= 5:
        errors.append("disconnected_markers requires two to five components")
    if profile == "multicolor_sparse" and (len(facts["nonzero_palette"]) < 2 or facts["density"] >= 0.5):
        errors.append("multicolor_sparse requires at least two colors below half density")
    if profile == "dense_multicolor" and (len(facts["nonzero_palette"]) < 3 or facts["density"] < 0.5):
        errors.append("dense_multicolor requires at least three nonzero colors and half density")
    if profile in {"wide_asymmetric", "tall_asymmetric"} and facts["nonzero_count"] < 4:
        errors.append("aspect-ratio lessons require substantial content")
    if profile == "single_row" and (facts["width"] < 4 or facts["nonzero_count"] < 2):
        errors.append("single_row requires a nontrivial asymmetric sequence")
    if profile == "near_symmetric" and (facts["mismatch_pairs"] != 1 or facts["nonzero_count"] < 4):
        errors.append("near_symmetric requires exactly one opposing-pair mismatch")
    if profile == "edge_asymmetry" and (not facts["edge_only"] or facts["nonzero_count"] < 2):
        errors.append("edge_asymmetry requires at least two outer-column markers")
    return errors


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["scene_profile"] not in SCENE_PROFILES:
        errors.append("grid does not match a declared observable mirror profile")
    else:
        errors.extend(_profile_errors(facts))
    return {"errors": errors, "facts": facts, "scene_profile": facts["scene_profile"], "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _size_range(difficulty):
    if difficulty == "easy":
        return (3, 7), (3, 7)
    if difficulty == "medium":
        return (5, 12), (4, 10)
    if difficulty == "hard":
        return (9, 20), (7, 15)
    return (4, 14), (4, 12)


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _random_poly(rng, count):
    cells = {(0, 0)}
    while len(cells) < count:
        row, col = rng.choice(tuple(cells))
        dr, dc = rng.choice(_CARDINAL)
        cells.add((row + dr, col + dc))
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return sorted((row - top, col - left) for row, col in cells)


def _ensure_asymmetric(grid, color):
    if _is_lr_symmetric(grid):
        grid[0][0] = color if grid[0][0] == 0 else 0


def _candidate_scene(difficulty, profile, rng):
    (h_low, h_high), (w_low, w_high) = _size_range(difficulty)
    height, width = rng.randint(h_low, h_high), rng.randint(w_low, w_high)
    width = min(width, 15)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    if profile in {"binary_sparse_3x3", "binary_dense_3x3", "single_marker"}:
        grid = _blank(3, 3)
        count = 1 if profile == "single_marker" else rng.randint(2, 3) if profile == "binary_sparse_3x3" else 4
        cells = [(row, col) for row in range(3) for col in range(3)]
        rng.shuffle(cells)
        color = rng.choice(colors)
        for row, col in cells[:count]:
            grid[row][col] = color
        return grid
    if profile == "wide_asymmetric":
        height = rng.randint(2, 5)
        width = rng.randint(max(2 * height, 6), 15)
    elif profile == "tall_asymmetric":
        width = rng.randint(2, 6)
        height = rng.randint(max(2 * width, 6), min(30, max(2 * width, 20)))
    elif profile == "single_row":
        height, width = 1, rng.randint(4, 15)
    else:
        height, width = max(height, 4), max(width, 4)
    grid = _blank(height, width)

    if profile == "connected_shape":
        for _ in range(50):
            cells = _random_poly(rng, rng.randint(4, min(18, height * width // 2)))
            shape_h = max(row for row, _ in cells) + 1
            shape_w = max(col for _, col in cells) + 1
            if shape_h <= height and shape_w <= width:
                break
        top, left = rng.randint(0, height - shape_h), rng.randint(0, width - shape_w)
        color = rng.choice(colors)
        for row, col in cells:
            grid[top + row][left + col] = color
    elif profile == "disconnected_markers":
        count = rng.randint(2, min(5, max(2, height * width // 5)))
        choices = [(row, col) for row in range(height) for col in range(width) if (row + col) % 2 == 0]
        rng.shuffle(choices)
        color = rng.choice(colors)
        for row, col in choices[:count]:
            grid[row][col] = color
    elif profile == "multicolor_sparse":
        palette = rng.sample(colors, rng.randint(2, 5))
        choices = [(row, col) for row in range(height) for col in range(width)]
        rng.shuffle(choices)
        for index, (row, col) in enumerate(choices[:rng.randint(4, max(4, height * width // 3))]):
            grid[row][col] = palette[index % len(palette)]
    elif profile == "dense_multicolor":
        palette = rng.sample(colors, rng.randint(3, 7))
        cells = [(row, col) for row in range(height) for col in range(width)]
        rng.shuffle(cells)
        count = rng.randint((height * width + 1) // 2, height * width - 1)
        for index, (row, col) in enumerate(cells[:count]):
            grid[row][col] = palette[index % len(palette)]
    elif profile in {"wide_asymmetric", "tall_asymmetric"}:
        palette = rng.sample(colors, 2)
        for _ in range(rng.randint(4, max(4, height * width // 3))):
            row, col = rng.randrange(height), rng.randrange(width)
            grid[row][col] = rng.choice(palette)
    elif profile == "single_row":
        palette = rng.sample(colors, rng.randint(2, 4))
        for col in range(width):
            grid[0][col] = 0 if rng.random() < 0.25 else rng.choice(palette)
    elif profile == "near_symmetric":
        palette = rng.sample(colors, 2)
        for row in range(height):
            for col in range((width + 1) // 2):
                value = 0 if rng.random() < 0.45 else rng.choice(palette)
                grid[row][col] = grid[row][width - 1 - col] = value
        row, col = rng.randrange(height), rng.randrange(width // 2)
        grid[row][col] = palette[0] if grid[row][width - 1 - col] != palette[0] else 0
    elif profile == "edge_asymmetry":
        color = rng.choice(colors)
        rows = list(range(height))
        rng.shuffle(rows)
        side = rng.choice((0, width - 1))
        for row in rows[:rng.randint(2, max(2, height - 1))]:
            grid[row][side] = color
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    _ensure_asymmetric(grid, rng.choice(colors))
    return grid


def _general_scene(difficulty, profile, rng):
    for _ in range(200):
        try:
            grid = _candidate_scene(difficulty, profile, rng)
        except ValueError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    ordinary_profiles = (
        PUBLIC_PROFILES * 2
        + ("binary_sparse_3x3",) * 20
        + ("binary_dense_3x3",) * 15
        + ("single_marker",) * 8
        + ("connected_shape",) * 8
        + ("disconnected_markers",) * 6
        + ("multicolor_sparse",) * 4
        + ("dense_multicolor",) * 3
        + ("wide_asymmetric", "tall_asymmetric", "near_symmetric", "edge_asymmetry") * 4
        + ("single_row",) * 2
    )
    profile = ctx.draw_choice("scene_profile", ordinary_profiles)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("geometry"))
