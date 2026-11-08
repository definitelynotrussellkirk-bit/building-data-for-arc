"""Semantic generator for ARC task cf6d343a2d09 (bank M101).

Split the non-background cells into four-connected monochrome components.
Every orange-7 component that touches both the top border and the left border
is recolored cyan-8.  Other orange components and every non-orange distractor
remain unchanged.  Touching both borders is the criterion; containing the
upper-left cell is only one way to satisfy it.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "cf6d343a2d09"
TASK_ID = "cf6d343a2d09"
VERSION = "2.0.0"
RULE_HASH = "ae8814a935b3"
SUMMARY = "Recolor every four-connected orange-7 component touching both the top and left borders to cyan 8; preserve all other cells."
INVARIANTS = [
    "the calibrated grid has background zero and literal orange-7 components",
    "exactly one orange component touches both the top and left borders",
    "at least two other orange components touch at most one of those borders",
    "one non-orange singleton distractor is preserved unchanged",
    "only the qualifying orange component is recolored cyan 8",
    "four-connectivity, not size or proximity to a border, defines each object",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "off_corner_bridge",
    "large_target",
    "size_tie",
    "top_left_only",
    "interior_only",
    "singleton_decoys",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five official component signatures plus six border/size/decoy contrasts",
        "valid": "public_1|public_2|public_3|public_4|public_5|off_corner_bridge|large_target|size_tie|top_left_only|interior_only|singleton_decoys",
    }
}

DISTRACTOR_COLORS = (1, 2, 3, 4, 5, 6, 9)
_HEIGHTS = {None: (13,), "easy": (7, 8), "medium": (9, 10), "hard": (11, 12)}
_WIDTHS = tuple(range(8, 15))

# Signature = (target_contains_corner, target_size, top-only sizes,
# left-only sizes, interior sizes).  These are independently recoverable from
# the returned grid.  public_1..public_5 exactly match the five canonical
# examples' orange component signatures.
PROFILE_SIGNATURES = {
    "public_1": (True, 3, (2,), (2,), (3,)),
    "public_2": (True, 4, (2,), (3,), (2,)),
    "public_3": (True, 4, (2,), (), (2, 2)),
    "public_4": (True, 3, (2,), (3,), (2,)),
    "public_5": (True, 3, (3,), (2,), (2,)),
    "off_corner_bridge": (False, 5, (2,), (2,), (2,)),
    "large_target": (True, 6, (2,), (2,), (2,)),
    "size_tie": (True, 4, (4,), (2,), (2,)),
    "top_left_only": (True, 3, (2,), (2,), ()),
    "interior_only": (True, 3, (), (), (2, 3)),
    "singleton_decoys": (True, 3, (1,), (1,), (1,)),
}
SIGNATURE_PROFILE = {signature: profile for profile, signature in PROFILE_SIGNATURES.items()}
if len(SIGNATURE_PROFILE) != len(PROFILE_SIGNATURES):
    raise AssertionError("scene profiles must have distinct component signatures")

_PUBLIC_ROWS = {
    "public_1": (
        "77000700", "70000700", "00000000", "00020000",
        "70000000", "70000000", "00000077", "00000007",
    ),
    "public_2": (
        "700000770", "770000000", "070000000", "000000000", "000000040",
        "700000000", "770000000", "000007000", "000007000",
    ),
    "public_3": (
        "77000007", "70000007", "70000000", "00000070",
        "00000070", "00000600", "00770000",
    ),
    "public_4": (
        "7000000070", "7700000070", "0000000000", "0000003000",
        "7000000000", "7700000000", "0000000000", "0000000000",
        "0000770000",
    ),
    "public_5": (
        "77000070", "70000077", "00000000", "00090000",
        "00000000", "70000000", "70007700",
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


def _neighbors(cell):
    row, col = cell
    return ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))


def _orange_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height) for col in range(width)
        if grid[row][col] == 7
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, component = [start], {start}
        while stack:
            cell = stack.pop()
            for neighbor in _neighbors(cell):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(frozenset(component))
    return tuple(sorted(components, key=lambda cells: min(cells)))


def _component_facts(grid):
    components = _orange_components(grid)
    target, top_only, left_only, interior = [], [], [], []
    for component in components:
        touches_top = any(row == 0 for row, _ in component)
        touches_left = any(col == 0 for _, col in component)
        if touches_top and touches_left:
            target.append(component)
        elif touches_top:
            top_only.append(component)
        elif touches_left:
            left_only.append(component)
        else:
            interior.append(component)
    return {
        "components": components,
        "targets": tuple(target),
        "top_only": tuple(top_only),
        "left_only": tuple(left_only),
        "interior": tuple(interior),
    }


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical component recoloring rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for component in _component_facts(grid)["targets"]:
        for row, col in component:
            output[row][col] = 8
    return output


def _profile_signature(facts):
    if len(facts["targets"]) != 1:
        return None
    target = facts["targets"][0]
    return (
        (0, 0) in target,
        len(target),
        tuple(sorted(map(len, facts["top_only"]))),
        tuple(sorted(map(len, facts["left_only"]))),
        tuple(sorted(map(len, facts["interior"]))),
    )


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 13:
        errors.append("calibrated scenes must contain seven through thirteen rows")
    if not 8 <= width <= 14:
        errors.append("calibrated scenes must contain eight through fourteen columns")
    allowed = {0, 7, *DISTRACTOR_COLORS}
    if any(value not in allowed for row in grid for value in row):
        errors.append("calibrated inputs may contain only zero, orange 7, and one allowed distractor color")
    distractors = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 7)
    ]
    if len(distractors) != 1 or distractors[0][2] not in DISTRACTOR_COLORS:
        errors.append("calibrated scenes require exactly one non-orange singleton distractor")
    facts = _component_facts(grid)
    signature = _profile_signature(facts)
    profile = SIGNATURE_PROFILE.get(signature)
    if len(facts["targets"]) != 1:
        errors.append(f"calibrated scenes require exactly one top-and-left orange component, found {len(facts['targets'])}")
    if len(facts["components"]) < 3:
        errors.append("calibrated scenes require a target and at least two non-target orange components")
    if profile is None:
        errors.append("orange component structure does not match a declared semantic profile")
    output = rule_mirror(grid)
    changed = sum(
        before != after
        for before_row, after_row in zip(grid, output)
        for before, after in zip(before_row, after_row)
    )
    target_size = len(facts["targets"][0]) if len(facts["targets"]) == 1 else 0
    if changed != target_size or changed == 0:
        errors.append(f"only the qualifying component should change ({target_size} cells), found {changed}")
    details = dict(facts)
    details.update({
        "height": height,
        "width": width,
        "signature": signature,
        "target_size": target_size,
        "changed": changed,
        "distractor": distractors[0] if len(distractors) == 1 else None,
        "component_sizes": tuple(sorted(map(len, facts["components"]))),
    })
    return {"errors": errors, "scene_profile": profile, "facts": details, "output": output}


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


def _safe_from_used(cell, used):
    return cell not in used and not any(neighbor in used for neighbor in _neighbors(cell))


def _grow_corner_target(rng, height, width, size):
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = sorted({
            neighbor
            for cell in cells for neighbor in _neighbors(cell)
            if 0 <= neighbor[0] < height - 1 and 0 <= neighbor[1] < width and neighbor not in cells
        })
        if not frontier:
            return None
        cells.add(rng.choice(frontier))
    return cells


def _off_corner_target(rng, height, width):
    # A five-cell bent path joins the top and left borders without using (0,0).
    row, col = rng.choice(((1, 3), (2, 2), (3, 1)))
    if row >= height or col >= width:
        return None
    vertical = {(offset, col) for offset in range(row + 1)}
    horizontal = {(row, offset) for offset in range(col + 1)}
    cells = vertical | horizontal
    return cells if len(cells) == 5 and (0, 0) not in cells else None


def _place_component(rng, height, width, used, size, category):
    if category == "top":
        allowed = {(row, col) for row in range(height - 1) for col in range(1, width)}
        anchors = [(0, col) for col in range(1, width)]
    elif category == "left":
        allowed = {(row, col) for row in range(1, height - 1) for col in range(width)}
        anchors = [(row, 0) for row in range(1, height - 1)]
    else:
        allowed = {(row, col) for row in range(1, height - 1) for col in range(1, width)}
        anchors = list(allowed)
    rng.shuffle(anchors)
    for anchor in anchors:
        if not _safe_from_used(anchor, used):
            continue
        cells = {anchor}
        while len(cells) < size:
            frontier = sorted({
                neighbor
                for cell in cells for neighbor in _neighbors(cell)
                if neighbor in allowed and neighbor not in cells and _safe_from_used(neighbor, used)
            })
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) == size:
            return cells
    return None


def _construct_scene(profile, height, width, rng, uniqueness_index, distractor=None):
    signature = PROFILE_SIGNATURES[profile]
    contains_corner, target_size, top_sizes, left_sizes, interior_sizes = signature
    for _ in range(500):
        target = (
            _grow_corner_target(rng, height, width, target_size)
            if contains_corner else _off_corner_target(rng, height, width)
        )
        if target is None:
            continue
        used = set(target)
        components = [target]
        failed = False
        for category, sizes in (("top", top_sizes), ("left", left_sizes), ("interior", interior_sizes)):
            for size in sizes:
                component = _place_component(rng, height, width, used, size, category)
                if component is None:
                    failed = True
                    break
                components.append(component)
                used.update(component)
            if failed:
                break
        if failed:
            continue
        grid = [[0] * width for _ in range(height)]
        for component in components:
            for row, col in component:
                grid[row][col] = 7
        if distractor is None:
            row, col = height - 1, uniqueness_index % width
            color = DISTRACTOR_COLORS[(uniqueness_index // width) % len(DISTRACTOR_COLORS)]
        else:
            row, col, color = distractor
        if grid[row][col] != 0 or color not in DISTRACTOR_COLORS:
            continue
        grid[row][col] = color
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct component lesson {profile!r}")


def _geometry_state(difficulty, variant_index):
    # The bottom row is reserved for the distractor, giving every profile more
    # than 1,000 injective easy/medium/hard geometry+color states.  This makes
    # the 5k linked census collision-free without adding rule-irrelevant noise.
    states = tuple(
        (height, width, height - 1, col, color)
        for height in _HEIGHTS[difficulty]
        for width in _WIDTHS
        for color in DISTRACTOR_COLORS
        for col in range(width)
    )
    return states[variant_index % len(states)]


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
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    uniqueness_index = 19 * seed - 18 * sample_index + 10_000 * band_index
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
        variant_index = uniqueness_index
    else:
        scheduled = SCENE_PROFILES[uniqueness_index % len(SCENE_PROFILES)]
        profile = ctx.draw_choice("scene_profile", [scheduled])
        variant_index = uniqueness_index // len(SCENE_PROFILES)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if overrides.get("scene_profile") is not None and profile in PUBLIC_PROFILES:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    else:
        rng = ctx.draw_rng("scene-v2")
        height, width, row, col, color = _geometry_state(difficulty, variant_index)
        grid = _construct_scene(
            profile, height, width, rng, variant_index, distractor=(row, col, color)
        )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid border-component lesson: " + "; ".join(errors))
    return grid
