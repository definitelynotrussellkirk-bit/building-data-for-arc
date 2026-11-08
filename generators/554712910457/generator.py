"""Semantic generator for ARC task 554712910457.

Red and green are the two Manhattan-distance seeds.  Every zero cell becomes
the color of its strictly nearer seed, while equal-distance zeros remain zero.
Every original nonzero cell—including multi-cell distractor objects—remains
unchanged and does not obstruct the distance calculation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "554712910457"
TASK_ID = "554712910457"
VERSION = "3.0.0"
RULE_HASH = "71fde72d5413"
SUMMARY = "Fill each zero with its nearer red or green Manhattan seed, preserving equal-distance zeros and all nonzero distractors."
INVARIANTS = [
    "there is exactly one red seed and one green seed",
    "only original zero cells are eligible to change",
    "a zero becomes red when its Manhattan distance to red is smaller",
    "a zero becomes green when its Manhattan distance to green is smaller",
    "a zero remains zero exactly when the two distances tie",
    "all nonzero markers and distractor objects remain unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "horizontal_even_tie",
    "horizontal_odd_no_tie",
    "vertical_even_tie",
    "vertical_odd_no_tie",
    "down_right_equal",
    "down_right_unequal",
    "down_left_equal",
    "down_left_unequal",
    "up_right_equal",
    "up_left_equal",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten recoverable Manhattan-Voronoi lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|horizontal_even_tie|horizontal_odd_no_tie|vertical_even_tie|vertical_odd_no_tie|down_right_equal|down_right_unequal|down_left_equal|down_left_unequal|up_right_equal|up_left_equal",
    }
}

_PUBLIC_ROWS = (
    "00000006/00050003/00000000/05000000/00000000/00000000/00000000/00000000/00005002/00000000",
    "000000000000/000009900000/000009900000/000000000000/000000000066/000000000066/000000000003/000880000000/000880000000/000000002000",
    "00000006/00000006/00200000/00000000/07000066/00000090/00000000/00000300",
    "000000066000/800770066002/000770000000/000000000000/000090000000/000000000000/000000000000/000000000000/000000300000/000000000000/000000000000",
    "0000002000/0000000000/0000000000/0000000000/0000000000/0009000000/0000000000/3000000000/0000007006",
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
    if not 6 <= len(grid) <= 30 or not 6 <= width <= 30:
        return ["input dimensions must be between 6 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2, 3, 5, 6, 7, 8, 9) for row in grid for value in row):
        return ["input cells must be literal 0, 2, 3, or distractor colors 5 through 9"]
    return []


def _extract_facts(grid):
    red = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 2)
    green = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 3)
    if len(red) != 1 or len(green) != 1:
        return {"errors": [f"expected exactly one red and green seed, got {len(red)} and {len(green)}"]}
    red, green = red[0], green[0]
    output = [list(row) for row in grid]
    red_fill, green_fill, ties = [], [], []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            d2 = abs(row - red[0]) + abs(col - red[1])
            d3 = abs(row - green[0]) + abs(col - green[1])
            if d2 < d3:
                output[row][col] = 2
                red_fill.append((row, col))
            elif d3 < d2:
                output[row][col] = 3
                green_fill.append((row, col))
            else:
                ties.append((row, col))
    decoys = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value not in (0, 2, 3))
    return {
        "errors": [], "height": len(grid), "width": len(grid[0]), "red": red, "green": green,
        "delta": (green[0] - red[0], green[1] - red[1]), "red_fill": tuple(red_fill),
        "green_fill": tuple(green_fill), "ties": tuple(ties), "decoys": decoys, "output": output,
    }


def rule_mirror(grid):
    """Exact Python mirror of the canonical Manhattan-distance rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    drow, dcol = facts["delta"]
    if drow == 0 and dcol:
        return "horizontal_even_tie" if abs(dcol) % 2 == 0 else "horizontal_odd_no_tie"
    if dcol == 0 and drow:
        return "vertical_even_tie" if abs(drow) % 2 == 0 else "vertical_odd_no_tie"
    if drow > 0 and dcol > 0:
        return "down_right_equal" if abs(drow) == abs(dcol) else "down_right_unequal"
    if drow > 0 and dcol < 0:
        return "down_left_equal" if abs(drow) == abs(dcol) else "down_left_unequal"
    if drow < 0 and dcol > 0 and abs(drow) == abs(dcol):
        return "up_right_equal"
    if drow < 0 and dcol < 0 and abs(drow) == abs(dcol):
        return "up_left_equal"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    decoy_colors = {grid[row][col] for row, col in facts["decoys"]}
    if len(facts["decoys"]) < 3 or len(decoy_colors) < 2:
        errors.append("at least three distractor cells in at least two colors are required")
    if not facts["red_fill"] or not facts["green_fill"]:
        errors.append("both seeds must claim at least one zero cell")
    if profile in {"horizontal_even_tie", "vertical_even_tie", "down_right_equal", "down_right_unequal", "down_left_equal", "down_left_unequal", "up_right_equal", "up_left_equal"} and not facts["ties"]:
        errors.append("declared tie profile must retain at least one equal-distance zero")
    if profile in {"horizontal_odd_no_tie", "vertical_odd_no_tie"} and facts["ties"]:
        errors.append("odd aligned seed distance must not retain zero ties")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared Manhattan-Voronoi profile")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    if any(facts["output"][row][col] != grid[row][col] for row, col in facts["decoys"] + (facts["red"], facts["green"])):
        errors.append("all original nonzero cells must remain unchanged")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimensions(difficulty, rng):
    bands = {
        None: ((8, 14), (10, 17)),
        "easy": ((8, 10), (10, 13)),
        "medium": ((10, 13), (13, 17)),
        "hard": ((13, 17), (17, 21)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    return rng.randint(h0, h1), rng.randint(w0, w1)


def _marker_pair(profile, height, width, rng):
    if profile.startswith("horizontal_"):
        separation = rng.choice((4, 6, 8)) if profile == "horizontal_even_tie" else rng.choice((5, 7))
        separation = min(separation, width - 3)
        if (separation % 2 == 0) != profile.endswith("even_tie"):
            separation -= 1
        row = rng.randint(1, height - 2)
        left = rng.randint(1, width - separation - 2)
        pair = ((row, left), (row, left + separation))
        return pair if rng.random() < 0.5 else pair[::-1]
    if profile.startswith("vertical_"):
        separation = rng.choice((4, 6, 8)) if profile == "vertical_even_tie" else rng.choice((5, 7))
        separation = min(separation, height - 3)
        if (separation % 2 == 0) != profile.endswith("even_tie"):
            separation -= 1
        col = rng.randint(1, width - 2)
        top = rng.randint(1, height - separation - 2)
        pair = ((top, col), (top + separation, col))
        return pair if rng.random() < 0.5 else pair[::-1]
    equal = profile.endswith("_equal")
    if equal:
        distance = rng.randint(3, min(7, height - 3, width - 3))
        drow = dcol = distance
    else:
        short = rng.randint(3, min(5, height - 3))
        long = min(width - 3, short + 2)
        drow, dcol = short, long
    if profile.startswith("down_right"):
        red, green = (1, 1), (1 + drow, 1 + dcol)
    elif profile.startswith("down_left"):
        red, green = (1, width - 2), (1 + drow, width - 2 - dcol)
    elif profile == "up_right_equal":
        red, green = (height - 2, 1), (height - 2 - drow, 1 + dcol)
    else:
        red, green = (height - 2, width - 2), (height - 2 - drow, width - 2 - dcol)
    return red, green


def _place_decoys(grid, occupied, rng):
    height, width = len(grid), len(grid[0])
    colors = rng.sample((5, 6, 7, 8, 9), rng.randint(2, 4))
    shapes = (
        ((0, 0),),
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    )
    target_objects = rng.randint(2, 5)
    placed = 0
    for index in range(target_objects):
        shape = rng.choice(shapes)
        for _ in range(100):
            row = rng.randint(0, height - 1 - max(drow for drow, _ in shape))
            col = rng.randint(0, width - 1 - max(dcol for _, dcol in shape))
            cells = {(row + drow, col + dcol) for drow, dcol in shape}
            halo = {(r + dr, c + dc) for r, c in cells for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))}
            if cells.isdisjoint(occupied) and not any(0 <= r < height and 0 <= c < width and (r, c) in occupied for r, c in halo):
                color = colors[index % len(colors)]
                for r, c in cells:
                    grid[r][c] = color
                occupied.update(cells)
                placed += len(cells)
                break
    return placed >= 3


def _general_scene(difficulty, profile, rng):
    for _ in range(100):
        height, width = _dimensions(difficulty, rng)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        red, green = _marker_pair(profile, height, width, rng)
        grid[red[0]][red[1]], grid[green[0]][green[1]] = 2, 3
        if not _place_decoys(grid, {red, green}, rng):
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
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 6)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
