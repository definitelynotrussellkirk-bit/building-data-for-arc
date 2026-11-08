"""Generator for 69927005ac25 — connect diagonal distance-two pairs.

The selected rule fills the empty midpoint between equal-colored endpoints at
(row, column) and (row + 2, column +/- 2).  Ordinary generation exposes exact
size, pair-count and palette controls and constructively places every requested
pair; the three historical degenerate textures remain explicit diagnostics.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69927005ac25"
VERSION = "3.0.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "Place one to four distinct-colored endpoint pairs at diagonal distance two "
    "on a zero background.  The rule fills each empty diagonal midpoint with "
    "the endpoint color; unrelated cells are unchanged."
)
INVARIANTS = [
    "ordinary scenes contain 1..4 distinct colors, each appearing at exactly two endpoints",
    "each endpoint pair differs by two rows and two columns",
    "every intended midpoint is zero and all intended triples are cell-disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "midpoint_filled", "axis_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS
PALETTES = {
    "default": (1, 2, 3, 4, 6, 7, 8, 9),
    "warm": (1, 2, 4, 7),
    "cool": (3, 6, 8, 9),
    "varied": (1, 3, 6, 9, 2, 4, 7, 8),
}
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 7..12", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..14", "valid": "6..14"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_pairs": {"type": "int", "default": "difficulty-aware 2..4", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "equals n_pairs", "valid": "1..4"},
    "position_bias": {"type": "str", "default": "diagonal_distance_2_pairs",
                      "valid": "diagonal_distance_2_pairs"},
    "n_distinct_colors": {"type": "int", "default": "equals n_pairs", "valid": "1..4"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "optional palette alias",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


class IncompatibleOverrides(ValueError):
    """Individually valid controls cannot be realized together."""


def _exact_int(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    supplied = {name: value for name, value in overrides.items() if value is not None}
    for name in ("grid_h", "grid_w", "n_pairs", "palette_size", "n_distinct_colors"):
        if name in supplied:
            low, high = {"grid_h": (5, 12), "grid_w": (6, 14)}.get(name, (1, 4))
            _exact_int(name, supplied[name], low, high)
    if "palette_kind" in supplied and supplied["palette_kind"] not in PALETTE_KINDS:
        raise ValueError("unknown palette_kind")
    if "texture" in supplied and supplied["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("unknown texture")
    if supplied.get("position_bias", "diagonal_distance_2_pairs") != "diagonal_distance_2_pairs":
        raise ValueError("position_bias must be diagonal_distance_2_pairs")
    if supplied.get("density", "sparse") != "sparse":
        raise ValueError("density must be sparse")
    counts = [supplied[name] for name in ("n_pairs", "palette_size", "n_distinct_colors")
              if name in supplied]
    if counts and any(value != counts[0] for value in counts[1:]):
        raise IncompatibleOverrides("n_pairs, palette_size and n_distinct_colors must agree")
    if supplied.get("texture") in HELPFUL_TEXTURES and "palette_kind" in supplied:
        if supplied["texture"] != supplied["palette_kind"]:
            raise IncompatibleOverrides("helpful texture and palette_kind must agree")
    return supplied


def _candidate_triples(height, width):
    result = []
    for row in range(height - 2):
        for column in range(width):
            for dc in (-2, 2):
                end_column = column + dc
                if 0 <= end_column < width:
                    midpoint = (row + 1, column + dc // 2)
                    cells = ((row, column), midpoint, (row + 2, end_column))
                    result.append(cells)
    return result


def _select_disjoint_triples(height, width, count, rng):
    candidates = _candidate_triples(height, width)
    rng.shuffle(candidates)

    def search(start, chosen, occupied):
        if len(chosen) == count:
            return chosen
        if len(candidates) - start < count - len(chosen):
            return None
        for index in range(start, len(candidates)):
            cells = candidates[index]
            if any(cell in occupied for cell in cells):
                continue
            found = search(index + 1, chosen + [cells], occupied | set(cells))
            if found is not None:
                return found
        return None

    selected = search(0, [], set())
    if selected is None:
        raise RuntimeError(f"cannot place {count} diagonal pairs on {height}x{width}")
    return selected


def _default_ranges(difficulty):
    if difficulty == "easy":
        return (7, 8), (8, 9), (2, 2)
    if difficulty == "medium":
        return (8, 10), (9, 11), (2, 3)
    if difficulty == "hard":
        return (9, 12), (10, 14), (3, 4)
    return (7, 10), (8, 11), (2, 3)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    supplied = _validate_overrides(overrides)
    texture = supplied.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    h_range, w_range, pair_range = _default_ranges(difficulty)
    height = supplied.get("grid_h", rng.randint(*h_range))
    width = supplied.get("grid_w", rng.randint(*w_range))
    requested = next((supplied[name] for name in ("n_pairs", "palette_size", "n_distinct_colors")
                      if name in supplied), None)
    n_pairs = requested if requested is not None else rng.randint(*pair_range)
    palette_kind = supplied.get("palette_kind")
    if texture in HELPFUL_TEXTURES:
        palette_kind = texture
    if palette_kind is None:
        palette_kind = rng.choice(PALETTE_KINDS)
    palette = PALETTES[palette_kind]
    if n_pairs > len(palette):
        raise IncompatibleOverrides(f"palette {palette_kind} cannot realize {n_pairs} distinct colors")

    colors = rng.sample(list(palette), n_pairs)
    triples = _select_disjoint_triples(height, width, n_pairs, rng)
    grid = full_grid(height, width, 0)
    for color, (first, midpoint, second) in zip(colors, triples):
        grid[first[0]][first[1]] = color
        grid[second[0]][second[1]] = color
        if grid[midpoint[0]][midpoint[1]] != 0:
            raise RuntimeError("constructive midpoint reservation failed")
    return grid


def observe_overrides(grid):
    counts = Counter(value for row in grid for value in row if value)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_pairs": sum(count == 2 for count in counts.values()),
        "palette_size": len(counts),
        "n_distinct_colors": len(counts),
        "position_bias": "diagonal_distance_2_pairs",
        "density": "sparse",
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be lists or tuples"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["ragged or empty rows"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer colors 0..9"]

    positions = {}
    for row, line in enumerate(grid):
        for column, value in enumerate(line):
            if value:
                positions.setdefault(value, []).append((row, column))
    if not positions:
        return []

    # Retain the two historical non-ordinary diagnostic textures.
    if len(positions) == 1:
        cells = next(iter(positions.values()))
        if len(cells) == 2:
            (r1, c1), (r2, c2) = sorted(cells)
            if (r1 == r2 and abs(c1 - c2) == 2) or (c1 == c2 and abs(r1 - r2) == 2):
                return []
        if len(cells) == 3:
            ordered = sorted(cells)
            if any(set(ordered) == {(r, c), (r + 1, c + dc), (r + 2, c + 2 * dc)}
                   for r, c in ordered for dc in (-1, 1)):
                return []

    reasons = []
    for color, cells in sorted(positions.items()):
        if len(cells) != 2:
            reasons.append(f"color {color} must appear exactly twice, got {len(cells)}")
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if r2 - r1 != 2 or abs(c2 - c1) != 2:
            reasons.append(f"color {color} endpoints are not at diagonal distance two")
            continue
        midpoint = (r1 + 1, (c1 + c2) // 2)
        if grid[midpoint[0]][midpoint[1]] != 0:
            reasons.append(f"color {color} midpoint must be zero")
    return reasons


def _draw_from_degenerate(name):
    height, width = 8, 9
    grid = full_grid(height, width, 0)
    if name == "no_pairs":
        return grid
    if name == "midpoint_filled":
        grid[1][1] = grid[2][2] = grid[3][3] = 4
        return grid
    if name == "axis_aligned":
        grid[3][1] = grid[3][3] = 4
        return grid
    raise ValueError(f"unknown degenerate texture: {name}")
