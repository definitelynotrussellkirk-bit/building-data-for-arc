"""Semantic generator for ARC task c5905adcd2cb (source 6d0160f0).

An 11x11 gray lattice partitions nine 3x3 interiors.  The first yellow-4
cell identifies a source interior by quotient coordinates; its local row and
column identify the destination interior.  Clear every non-gray cell, then
copy every nonzero/non-gray source cell—including the marker—to the same
local offset in the destination.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c5905adcd2cb"
TASK_ID = "c5905adcd2cb"
VERSION = "3.0.0"
RULE_HASH = "93e6c6c4b04f"
SUMMARY = "Clear all nine lattice interiors, then copy the marker's 3x3 source pattern to the macro-cell encoded by the marker's local position."
INVARIANTS = [
    "the calibrated canvas is an 11x11 grid with complete gray-5 separators at rows and columns 3 and 7",
    "the first color-4 cell's quotient-by-four coordinates select its source 3x3 interior",
    "the marker's local row and column, each zero through two, select one of the nine destination interiors",
    "every nonzero/non-gray source cell is copied at the same local offset, including the color-4 marker",
    "all non-gray content outside the copied destination pattern is cleared to zero",
    "every gray-5 cell is preserved",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "empty_destination",
    "light_destination",
    "dense_destination",
    "same_destination",
    "marker_only",
    "full_source",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five complete official scenes plus six labeled clear/copy contrasts",
        "valid": "public_1|public_2|public_3|public_4|public_5|empty_destination|light_destination|dense_destination|same_destination|marker_only|full_source",
    }
}

ACCENT_COLORS = (1, 2, 3, 6, 7, 8, 9)
SEPARATORS = (3, 7)
MACROS = tuple((row, col) for row in range(3) for col in range(3))

_PUBLIC_ROWS = {
    "public_1": (
        "07050605700", "83650005080", "00050305000", "55555555555",
        "08750305007", "00058005086", "00650005300", "55555555555",
        "06050805000", "80053005408", "07050605067",
    ),
    "public_2": (
        "30050205060", "00750005009", "06050105000", "55555555555",
        "03050005000", "10950065073", "00050005000", "55555555555",
        "90050905090", "06050045001", "00057005000",
    ),
    "public_3": (
        "30050105002", "02050305060", "00050005000", "55555555555",
        "01050005030", "70652075070", "00050005060", "55555555555",
        "70050405003", "00050705200", "03050305006",
    ),
    "public_4": (
        "30057065807", "00950305060", "72050025030", "55555555555",
        "70258705023", "00650035007", "30052005060", "55555555555",
        "03450205207", "70057035001", "00250605030",
    ),
    "public_5": (
        "20352005030", "76050705670", "00056035002", "55555555555",
        "70050005604", "06050275020", "60250305070", "55555555555",
        "70050605230", "00650205000", "20050705067",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _first_marker(grid):
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 4:
                return row, col
    raise ValueError("clear-and-copy rule requires at least one color-4 marker")


def _rule_facts(grid):
    marker_row, marker_col = _first_marker(grid)
    source_row, source_col = (marker_row // 4) * 4, (marker_col // 4) * 4
    destination_row = (marker_row - source_row) * 4
    destination_col = (marker_col - source_col) * 4
    if source_row + 2 >= len(grid) or source_col + 2 >= len(grid[0]):
        raise ValueError("marker source 3x3 rectangle is outside the input")
    source_cells = tuple(
        (row, col, grid[row][col])
        for row in range(source_row, source_row + 3)
        for col in range(source_col, source_col + 3)
        if grid[row][col] not in (0, 5)
    )
    if any(
        not (0 <= destination_row + row - source_row < len(grid))
        or not (0 <= destination_col + col - source_col < len(grid[0]))
        for row, col, _ in source_cells
    ):
        raise ValueError("marker-selected destination is outside the input")
    return {
        "marker": (marker_row, marker_col),
        "source_macro": (source_row // 4, source_col // 4),
        "destination_macro": (destination_row // 4, destination_col // 4),
        "source_origin": (source_row, source_col),
        "destination_origin": (destination_row, destination_col),
        "source_cells": source_cells,
    }


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical clear-and-copy rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _rule_facts(grid)
    output = [
        [5 if value == 5 else 0 for value in row]
        for row in grid
    ]
    source_row, source_col = facts["source_origin"]
    destination_row, destination_col = facts["destination_origin"]
    for row, col, value in facts["source_cells"]:
        output[destination_row + row - source_row][destination_col + col - source_col] = value
    return output


def _canonicalize_colors(grid):
    mapping = {0: 0, 4: 4, 5: 5}
    next_label = 10
    normalized = []
    for row in grid:
        normalized_row = []
        for value in row:
            if value not in mapping:
                mapping[value] = next_label
                next_label += 1
            normalized_row.append(mapping[value])
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


def _d4_grids(grid):
    variants = set()
    current = tuple(map(tuple, grid))
    for _ in range(4):
        variants.add(current)
        variants.add(tuple(tuple(reversed(row)) for row in current))
        current = tuple(tuple(current[len(current) - 1 - row][col] for row in range(len(current))) for col in range(len(current[0])))
    return tuple(sorted(variants))


_PUBLIC_FAMILY_KEYS = {
    _canonicalize_colors(transformed): profile
    for profile, grid in _PUBLIC_INPUTS.items()
    for transformed in _d4_grids(grid)
}
if len(_PUBLIC_FAMILY_KEYS) != sum(len(_d4_grids(grid)) for grid in _PUBLIC_INPUTS.values()):
    raise AssertionError("official lattice families must be distinct")


def _public_family(grid):
    try:
        return _PUBLIC_FAMILY_KEYS.get(_canonicalize_colors(grid))
    except TypeError:
        return None


def _macro_values(grid, macro):
    row0, col0 = macro[0] * 4, macro[1] * 4
    return tuple(
        grid[row0 + row][col0 + col]
        for row in range(3) for col in range(3)
    )


def _general_profile(grid, facts):
    source = facts["source_macro"]
    destination = facts["destination_macro"]
    if source == destination:
        return "same_destination"
    source_count = len(facts["source_cells"])
    if source_count == 1:
        return "marker_only"
    if source_count == 9:
        return "full_source"
    destination_count = sum(value not in (0, 5) for value in _macro_values(grid, destination))
    if destination_count == 0:
        return "empty_destination"
    if destination_count >= 5:
        return "dense_destination"
    return "light_destination"


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    if len(grid) != 11 or len(grid[0]) != 11:
        errors.append("calibrated scenes must use the official 11x11 canvas")
    marker_count = sum(value == 4 for row in grid for value in row)
    if marker_count != 1:
        errors.append(f"calibrated scenes require exactly one color-4 marker, found {marker_count}")
    if len(grid) == 11 and len(grid[0]) == 11:
        for separator in SEPARATORS:
            if any(grid[separator][col] != 5 for col in range(11)):
                errors.append(f"separator row {separator} must be entirely gray 5")
            if any(grid[row][separator] != 5 for row in range(11)):
                errors.append(f"separator column {separator} must be entirely gray 5")
        if any(
            grid[row][col] == 5
            for row in range(11) for col in range(11)
            if row not in SEPARATORS and col not in SEPARATORS
        ):
            errors.append("gray 5 may occur only on the calibrated separator lattice")
    try:
        facts = _rule_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    palette = {value for row in grid for value in row}
    non_lattice = sum(value not in (0, 5) for row in grid for value in row)
    source_count = len(facts["source_cells"])
    if not 6 <= len(palette) <= 10:
        errors.append("calibrated scenes require six through ten colors")
    if not 15 <= non_lattice <= 55:
        errors.append("calibrated scenes require fifteen through fifty-five non-lattice colored cells")
    if not 1 <= source_count <= 9:
        errors.append("source interior must contain one through nine copied cells")
    output = rule_mirror(grid)
    changed = sum(
        before != after
        for before_row, after_row in zip(grid, output)
        for before, after in zip(before_row, after_row)
    )
    if changed < 15 or output == [list(row) for row in grid]:
        errors.append("the clear-and-copy transformation must visibly change at least fifteen cells")
    public = _public_family(grid)
    profile = public or _general_profile(grid, facts)
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared semantic profile")
    facts = dict(facts)
    facts.update({
        "palette": tuple(sorted(palette)),
        "non_lattice_count": non_lattice,
        "source_count": source_count,
        "destination_input_count": sum(
            value not in (0, 5)
            for value in _macro_values(grid, facts["destination_macro"])
        ),
        "changed": changed,
    })
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


@lru_cache(maxsize=None)
def _replacement_orders(count):
    return tuple(permutations(ACCENT_COLORS, count))


def _embed_public(profile, rng, uniqueness_index=None):
    transforms = _d4_grids(_PUBLIC_INPUTS[profile])
    grid = rng.choice(transforms) if uniqueness_index is None else transforms[
        uniqueness_index % len(transforms)
    ]
    source_colors = sorted({value for row in grid for value in row if value not in (0, 4, 5)})
    if uniqueness_index is None:
        replacement = rng.sample(ACCENT_COLORS, len(source_colors))
    else:
        orders = _replacement_orders(len(source_colors))
        replacement = orders[(uniqueness_index // len(transforms)) % len(orders)]
    color_map = dict(zip(source_colors, replacement))
    return [
        [value if value in (0, 4, 5) else color_map[value] for value in row]
        for row in grid
    ]


def _empty_lattice():
    grid = [[0] * 11 for _ in range(11)]
    for separator in SEPARATORS:
        for index in range(11):
            grid[separator][index] = 5
            grid[index][separator] = 5
    return grid


def _set_macro(grid, macro, values):
    row0, col0 = macro[0] * 4, macro[1] * 4
    for index, value in enumerate(values):
        grid[row0 + index // 3][col0 + index % 3] = value


def _random_general(profile, difficulty, rng):
    grid = _empty_lattice()
    palette_count = {"easy": 4, "hard": 7}.get(difficulty, rng.randint(5, 7))
    colors = rng.sample(ACCENT_COLORS, palette_count)
    density = {"easy": 0.30, "hard": 0.58}.get(difficulty, 0.44)
    destination = rng.choice(MACROS)
    source = destination if profile == "same_destination" else rng.choice(
        [macro for macro in MACROS if macro != destination]
    )
    local_row, local_col = destination
    marker_index = local_row * 3 + local_col

    for macro in MACROS:
        if macro == source:
            continue
        values = [rng.choice(colors) if rng.random() < density else 0 for _ in range(9)]
        _set_macro(grid, macro, values)

    if profile == "marker_only":
        source_values = [0] * 9
    elif profile == "full_source":
        source_values = [rng.choice(colors) for _ in range(9)]
    else:
        source_values = [0] * 9
        target = rng.randint(3, 6)
        for index in rng.sample([item for item in range(9) if item != marker_index], target - 1):
            source_values[index] = rng.choice(colors)
    source_values[marker_index] = 4
    _set_macro(grid, source, source_values)

    if source != destination:
        destination_values = list(_macro_values(grid, destination))
        if profile == "empty_destination":
            destination_values = [0] * 9
        elif profile == "light_destination":
            destination_values = [0] * 9
            for index in rng.sample(range(9), rng.randint(1, 4)):
                destination_values[index] = rng.choice(colors)
        elif profile == "dense_destination":
            destination_values = [0] * 9
            for index in rng.sample(range(9), rng.randint(5, 9)):
                destination_values[index] = rng.choice(colors)
        _set_macro(grid, destination, destination_values)

    # Ensure every chosen accent color is represented without disturbing the
    # profile-defining source or destination macro-cells.
    protected = {source, destination}
    available = [macro for macro in MACROS if macro not in protected]
    for color in colors:
        if any(value == color for row in grid for value in row):
            continue
        macro = rng.choice(available)
        values = list(_macro_values(grid, macro))
        values[rng.randrange(9)] = color
        _set_macro(grid, macro, values)

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        # Construction has ample state; retrying with a derived substream is
        # deterministic and avoids weakening the validator for rare low-counts.
        for _ in range(200):
            return _random_general(profile, difficulty, rng)
        raise AssertionError(f"could not construct lattice lesson {profile!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES)
        + [item for item in GENERAL_PROFILES if item != "marker_only"] * 2
        + ["marker_only"],
    )
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("scene")
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    # Mix episode seed and within-episode index while giving the health
    # sampler's four bands disjoint 1k windows.  The coefficients are also
    # coprime to the smallest official-family state space under the strided
    # 5k semantic census, preventing birthday-style pair rejection.
    uniqueness_index = 19 * seed - 18 * sample_index - 3960 * band_index
    grid = _embed_public(profile, rng, uniqueness_index) if profile in PUBLIC_PROFILES else _random_general(
        profile, difficulty, rng
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lattice lesson: " + "; ".join(errors))
    return grid
