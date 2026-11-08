"""Semantic generator for ARC task e971e0773705.

Every red object is an isolated T-tetromino in one of two vertical
orientations.  A top-bar T contributes to the blue tally and a bottom-bar T
contributes to the green tally.  Each tally is capped at four and written into
fixed positions in a 3x6 output emblem by the canonical Racket rule.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "e971e0773705"
TASK_ID = "e971e0773705"
VERSION = "3.0.1"
RULE_HASH = "2855526e979d"
# The output is a fixed 3x6 pair of independently saturated four-position
# tallies.  Each side has five observable states (0, 1, 2, 3, >=4), excluding
# only the empty/empty state because every calibrated input contains at least
# one T: 5 * 5 - 1 = 24.  Declaring the exact finite codomain lets the standard
# diversity lint distinguish complete class coverage from sampler collapse.
EXPECTED_OUTPUT_CODOMAIN = 24
SUMMARY = (
    "Count isolated red top-bar and bottom-bar T-tetrominoes into capped "
    "blue and green positions of a fixed 3x6 emblem."
)
INVARIANTS = [
    "the input palette is exactly background 0 and object color 2",
    "every red 4-connected component is one exact four-cell T-tetromino",
    "top-bar and bottom-bar T-tetrominoes are separate components",
    "top-bar T counts are encoded in blue 1 and bottom-bar T counts in green 3",
    "each output tally saturates after its fourth object",
]

TOP_T = ((0, 0), (0, 1), (0, 2), (1, 1))
BOTTOM_T = ((0, 1), (1, 0), (1, 1), (1, 2))
T_SHAPES = (TOP_T, BOTTOM_T)

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 10))
GENERAL_COUNTS = {
    "top_single": (1, 0),
    "top_pair": (2, 0),
    "top_only": (3, 0),
    "top_four": (4, 0),
    "bottom_single": (0, 1),
    "bottom_pair": (0, 2),
    "bottom_only": (0, 3),
    "bottom_four": (0, 4),
    "count_1_2": (1, 2),
    "count_2_3": (2, 3),
    "count_2_4": (2, 4),
    "count_3_3": (3, 3),
    "count_3_4": (3, 4),
    "count_4_1": (4, 1),
    "count_4_2": (4, 2),
    "balanced_four": (4, 4),
    "top_cap": (5, 2),
    "bottom_cap": (2, 5),
    "both_cap": (5, 5),
}
GENERAL_PROFILES = tuple(GENERAL_COUNTS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
PROFILE_TO_CODE = {profile: index for index, profile in enumerate(SCENE_PROFILES)}
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": "balanced schedule over 0..27",
        "valid": "0..27",
        "doc": "Index into SCENE_PROFILES: nine official families, the full capped count lattice, and cap contrasts.",
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "0200222", "2220020", "0000000", "0000222", "0020020", "0222000",
    ),
    "public_2": (
        "0222000", "0020000", "0000020", "2220222", "0200000", "0000000",
        "0022200", "0002000",
    ),
    "public_3": (
        "0200000", "2220020", "0000222", "0020000", "0222000", "0000222",
        "0200020", "2220000",
    ),
    "public_4": ("2220", "0200", "0000", "0200", "2220"),
    "public_5": ("22200", "02000", "00000", "00222", "02020", "22200"),
    "public_6": (
        "0000000", "2220000", "0200020", "0000222", "0000000", "0020000",
        "0222020", "0000222",
    ),
    "public_7": (
        "000000000000000", "000200000000000", "002220000000000",
        "000000000000000", "000000022200000", "222000002000000",
        "020000000000000", "000000000000000", "000002220000000",
        "002000200000020", "022200000000222", "000000000000000",
        "000000222000000", "000000020000000", "000000000000000",
    ),
    "public_8": (
        "00000000000", "00200000000", "02220002220", "00000000200",
        "00222000000", "00020000000", "00000022200", "00200002000",
        "02220000000", "00000000000",
    ),
    "public_9": (
        "000000222", "020000020", "222002000", "000022200", "000200000",
        "002220222", "000000020", "222000000", "020022200", "000002000",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}

_GREEN_POSITIONS = ((0, 0), (2, 0), (0, 2), (2, 2))
_BLUE_POSITIONS = ((0, 3), (2, 3), (0, 5), (2, 5))


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


def _components4(grid, color=2):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for neighbor in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return tuple(components)


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _emblem(top_count, bottom_count):
    output = [[0] * 6 for _ in range(3)]
    for row, col in _GREEN_POSITIONS[:min(bottom_count, 4)]:
        output[row][col] = 3
    for row, col in _BLUE_POSITIONS[:min(top_count, 4)]:
        output[row][col] = 1
    return output


def _facts(grid):
    components = _components4(grid)
    normalized = tuple(_normalize(component) for component in components)
    counts = Counter(normalized)
    top_count = counts[TOP_T]
    bottom_count = counts[BOTTOM_T]
    exact_t = len(components) == top_count + bottom_count
    return {
        "components": components,
        "normalized": normalized,
        "exact_t": exact_t,
        "top_count": top_count,
        "bottom_count": bottom_count,
        "component_count": len(components),
        "output": _emblem(top_count, bottom_count),
    }


def rule_mirror(grid):
    """Broad input-pure mirror of the executable component-counting rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    top_count = 0
    bottom_count = 0
    for component in _components4(grid):
        top_row = min(row for row, _ in component)
        cells_on_top = sum(row == top_row for row, _ in component)
        if cells_on_top >= 3:
            top_count += 1
        else:
            bottom_count += 1
    return _emblem(top_count, bottom_count)


def _public_specs():
    specs = {}
    for profile, grid in _PUBLIC_INPUTS.items():
        facts = _facts(grid)
        specs[profile] = {
            "height": len(grid),
            "width": len(grid[0]),
            "top_count": facts["top_count"],
            "bottom_count": facts["bottom_count"],
        }
    return specs


_PUBLIC_SPECS = _public_specs()
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _reflect_horizontal(grid):
    return tuple(tuple(reversed(row)) for row in grid)


_PUBLIC_CORE_LOOKUP = {}
for _profile, _grid in _PUBLIC_INPUTS.items():
    _core = tuple(map(tuple, _grid))
    for _variant in {_core, _reflect_horizontal(_core)}:
        _shape = (len(_variant), len(_variant[0]))
        _PUBLIC_CORE_LOOKUP.setdefault(_shape, {})[_variant] = _profile

_PUBLIC_CODES = tuple(
    (top, bottom, left, right, reflected)
    for total in range(8)
    for top in range(total + 1)
    for bottom in range(total - top + 1)
    for left in range(total - top - bottom + 1)
    for right in (total - top - bottom - left,)
    for reflected in (False, True)
)
_GENERAL_CODES = _PUBLIC_CODES


def _public_family(grid, facts):
    height, width = len(grid), len(grid[0])
    matches = set()
    for (core_height, core_width), lookup in _PUBLIC_CORE_LOOKUP.items():
        if core_height > height or core_width > width:
            continue
        for top in range(height - core_height + 1):
            for left in range(width - core_width + 1):
                core = tuple(
                    tuple(grid[row][left:left + core_width])
                    for row in range(top, top + core_height)
                )
                profile = lookup.get(core)
                if profile is None:
                    continue
                spec = _PUBLIC_SPECS[profile]
                if (
                    facts["top_count"] == spec["top_count"]
                    and facts["bottom_count"] == spec["bottom_count"]
                ):
                    matches.add(profile)
    return next(iter(matches)) if len(matches) == 1 else None


def _profile_from_facts(facts):
    top_count = facts["top_count"]
    bottom_count = facts["bottom_count"]
    for profile, counts in GENERAL_COUNTS.items():
        if (top_count, bottom_count) == counts:
            return profile
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 22 or not 4 <= width <= 22:
        errors.append("calibrated T scenes require height 5..22 and width 4..22")
    palette = {value for row in grid for value in row}
    if palette != {0, 2}:
        errors.append("calibrated T scenes require exactly background 0 and red 2")
    facts = _facts(grid)
    if not facts["exact_t"]:
        errors.append("every red component must be one exact top-bar or bottom-bar T")
    if not 1 <= facts["component_count"] <= 10:
        errors.append("calibrated T scenes require one through ten components")
    public_profile = _public_family(grid, facts) if facts["exact_t"] else None
    profile = public_profile or (_profile_from_facts(facts) if facts["exact_t"] else None)
    if profile not in SCENE_PROFILES:
        errors.append("T counts and dimensions do not match a declared scene profile")
    details = dict(facts)
    details.update({
        "height": height,
        "width": width,
        "scene_profile": profile,
        "public_profile": public_profile,
    })
    return {
        "errors": errors,
        "scene_profile": profile,
        "facts": details,
        "output": facts["output"],
    }


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
    if analysis["errors"]:
        return {}
    return {"scene_code": PROFILE_TO_CODE[analysis["scene_profile"]]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _can_place(grid, shape, top, left):
    height, width = len(grid), len(grid[0])
    cells = {(top + row, left + col) for row, col in shape}
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if any(grid[row][col] != 0 for row, col in cells):
        return False
    for row, col in cells:
        for neighbor in (
            (row - 1, col), (row + 1, col),
            (row, col - 1), (row, col + 1),
        ):
            if neighbor not in cells and 0 <= neighbor[0] < height and 0 <= neighbor[1] < width:
                if grid[neighbor[0]][neighbor[1]] == 2:
                    return False
    return True


def _place_scene(height, width, top_count, bottom_count, rng):
    shapes = [TOP_T] * top_count + [BOTTOM_T] * bottom_count
    for _ in range(600):
        grid = [[0] * width for _ in range(height)]
        order = list(shapes)
        rng.shuffle(order)
        success = True
        for shape in order:
            positions = [
                (row, col)
                for row in range(height - 1)
                for col in range(width - 2)
            ]
            rng.shuffle(positions)
            placed = False
            for top, left in positions:
                if not _can_place(grid, shape, top, left):
                    continue
                for row, col in shape:
                    grid[top + row][left + col] = 2
                placed = True
                break
            if not placed:
                success = False
                break
        if success:
            return grid
    raise AssertionError(
        f"could not place {top_count} top and {bottom_count} bottom T shapes "
        f"in {height}x{width}"
    )


def _general_core(profile):
    top_count, bottom_count = GENERAL_COUNTS[profile]
    shapes = []
    remaining_top, remaining_bottom = top_count, bottom_count
    while remaining_top or remaining_bottom:
        if remaining_top:
            shapes.append(TOP_T)
            remaining_top -= 1
        if remaining_bottom:
            shapes.append(BOTTOM_T)
            remaining_bottom -= 1
    if len(shapes) == 3:
        positions = ((0, 0), (0, 4), (3, 1))
        height, width = 5, 7
    else:
        per_row = min(4, len(shapes))
        rows_needed = (len(shapes) + per_row - 1) // per_row
        height = max(5, rows_needed * 3 - 1)
        width = max(4, per_row * 4 - 1)
        positions = tuple(
            ((index // per_row) * 3, (index % per_row) * 4)
            for index in range(len(shapes))
        )
    grid = [[0] * width for _ in range(height)]
    for shape, (top, left) in zip(shapes, positions):
        for row, col in shape:
            grid[top + row][left + col] = 2
    return tuple(tuple(row) for row in grid)


_GENERAL_CORES = {profile: _general_core(profile) for profile in GENERAL_PROFILES}


def _embed_core(core, code):
    top, bottom, left, right, reflected = code
    if reflected:
        core = _reflect_horizontal(core)
    height = top + len(core) + bottom
    width = left + len(core[0]) + right
    grid = [[0] * width for _ in range(height)]
    for row, values in enumerate(core):
        grid[top + row][left:left + len(values)] = values
    return grid


def _unique_codes(core):
    unique = []
    seen = set()
    for code in _PUBLIC_CODES:
        grid = _embed_core(core, code)
        key = tuple(map(tuple, grid))
        if key not in seen:
            seen.add(key)
            unique.append(code)
    return tuple(unique)


_PUBLIC_PROFILE_CODES = {
    profile: _unique_codes(tuple(map(tuple, grid)))
    for profile, grid in _PUBLIC_INPUTS.items()
}
_GENERAL_PROFILE_CODES = {
    profile: _unique_codes(core)
    for profile, core in _GENERAL_CORES.items()
}


def _embed_public(profile, variant_index):
    core = tuple(map(tuple, _PUBLIC_INPUTS[profile]))
    codes = _PUBLIC_PROFILE_CODES[profile]
    return _embed_core(core, codes[variant_index % len(codes)])


def _embed_general(profile, variant_index):
    core = _GENERAL_CORES[profile]
    codes = _GENERAL_PROFILE_CODES[profile]
    return _embed_core(core, codes[variant_index % len(codes)])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
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
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    schedule_index = seed + 36 * sample_index + band_index
    variant_index = sample_index // len(SCENE_PROFILES) + seed + 226 * band_index
    explicit = overrides.get("scene_code") is not None
    if explicit:
        scene_code = ctx.draw_int("scene_code", 0, len(SCENE_PROFILES) - 1)
    else:
        scheduled_code = schedule_index % len(SCENE_PROFILES)
        scene_code = ctx.draw_int("scene_code", scheduled_code, scheduled_code)
    profile = SCENE_PROFILES[scene_code]
    if explicit and profile in PUBLIC_PROFILES:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    elif profile in PUBLIC_PROFILES:
        grid = _embed_public(profile, variant_index)
    else:
        grid = _embed_general(profile, variant_index)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid T-tetromino lesson: " + "; ".join(errors))
    return grid
