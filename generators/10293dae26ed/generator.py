"""Generator for ARC task 10293dae26ed (original task 50cb2852).

For every four-connected monochrome non-background rectangle, replace the
strict interior of its bounding box with cyan 8 while preserving the colored
border.  Separate rectangles of the same color remain separate objects and are
both transformed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance

GENERATOR_ID = "10293dae26ed"
TASK_ID = "10293dae26ed"
VERSION = "3.2.0"
RULE_HASH = "8c364b7458e3"
SUMMARY = (
    "A zero-background grid contains two through four solid, cardinally "
    "separated monochrome rectangles, each at least 3x3 and colored from "
    "{1..7,9}. For every rectangle independently, paint every strict "
    "interior cell cyan 8 and preserve its original colored border. Separate "
    "rectangles may share a color; component identity, not color identity, "
    "determines which interiors are filled."
)
INVARIANTS = [
    "background is color 0 and cyan 8 is absent from the input",
    "there are exactly 2..4 four-connected monochrome components",
    "every component is a solid rectangle at least 3x3",
    "distinct rectangles do not touch cardinally",
    "at least two input colors are represented",
    "every rectangle has a nonempty strict interior that the rule changes",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "two_interior_mixed",
    "two_border_mixed",
    "three_interior",
    "three_border",
    "same_size_pair",
    "thin_orientations",
    "four_duplicate_color",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
# Every three consecutive ordinary draws include the decisive four-component
# duplicate-color/border-touching anchor. The ten intervening slots cycle all
# other profiles, so a standard three-demo lesson refutes the plausible
# largest-only, one-per-color, center-only, and skip-border-touching rules.
_SCHEDULE_PATTERN = (
    "four_duplicate_color", "public_1", "public_2",
    "four_duplicate_color", "public_3", "public_4",
    "four_duplicate_color", "two_interior_mixed", "two_border_mixed",
    "four_duplicate_color", "three_interior", "three_border",
    "four_duplicate_color", "same_size_pair", "thin_orientations",
)
SCHEDULE_PROFILES = SCENE_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample-index cycle over four canonical and seven generalized lessons",
        "valid": "public_1|public_2|public_3|public_4|two_interior_mixed|two_border_mixed|three_interior|three_border|same_size_pair|thin_orientations|four_duplicate_color",
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "00000000000",
        "02222000000",
        "02222000000",
        "02222000000",
        "02222000000",
        "00000000000",
        "00000000000",
        "00111111000",
        "00111111000",
        "00111111000",
        "00000000000",
        "00000000000",
    ),
    "public_2": (
        "000000000000000",
        "002222200011100",
        "002222200011100",
        "002222200011100",
        "002222200000000",
        "002222200000000",
        "002222200000000",
        "000000000000000",
        "000000003333333",
        "000000003333333",
        "000000003333333",
        "000000003333333",
        "000000003333333",
    ),
    "public_3": (
        "0000000000000",
        "0000002222000",
        "3333002222000",
        "3333002222000",
        "3333002222000",
        "3333002222000",
        "0000002222000",
        "0000000000000",
        "0011111111000",
        "0011111111000",
        "0011111111000",
        "0011111111000",
    ),
    "public_4": (
        "0111110000000",
        "0111110011100",
        "0111110011100",
        "0111110011100",
        "0000000000000",
        "0022222200000",
        "0022222200000",
        "0022222203333",
        "0022222203333",
        "0022222203333",
        "0022222203333",
        "0000000003333",
        "0000000003333",
        "0000000003333",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}

# Each generalized scene is (height, width, [(row, col, height, width), ...]).
# The normalized component dimensions and number of border-touching components
# form a unique, observable signature even after any D4 transform.
_GENERAL_SCENES = {
    "two_interior_mixed": (
        12,
        14,
        ((1, 1, 3, 4), (6, 7, 5, 6)),
    ),
    "two_border_mixed": (
        12,
        14,
        ((0, 0, 4, 5), (7, 8, 3, 5)),
    ),
    "three_interior": (
        15,
        16,
        ((1, 1, 3, 3), (1, 7, 4, 5), (8, 5, 5, 6)),
    ),
    "three_border": (
        15,
        16,
        ((0, 1, 3, 5), (5, 0, 4, 3), (10, 11, 5, 5)),
    ),
    "same_size_pair": (
        12,
        16,
        ((2, 1, 4, 5), (6, 10, 4, 5)),
    ),
    "thin_orientations": (
        16,
        16,
        ((0, 1, 3, 6), (6, 0, 6, 3), (10, 10, 4, 4)),
    ),
    "four_duplicate_color": (
        18,
        18,
        ((0, 1, 4, 5), (1, 11, 3, 3), (7, 0, 5, 6), (12, 11, 6, 7)),
    ),
}

_GENERAL_SIGNATURES = {
    "two_interior_mixed": (2, 0, ((3, 4), (5, 6)), False),
    "two_border_mixed": (2, 1, ((3, 5), (4, 5)), False),
    "three_interior": (3, 0, ((3, 3), (4, 5), (5, 6)), False),
    "three_border": (3, 3, ((3, 4), (3, 5), (5, 5)), False),
    "same_size_pair": (2, 0, ((4, 5), (4, 5)), False),
    "thin_orientations": (3, 2, ((3, 6), (3, 6), (4, 4)), False),
    "four_duplicate_color": (
        4,
        3,
        ((3, 3), (4, 5), (5, 6), (6, 7)),
        True,
    ),
}
_SIGNATURE_PROFILE = {
    signature: profile for profile, signature in _GENERAL_SIGNATURES.items()
}
if len(_SIGNATURE_PROFILE) != len(_GENERAL_SIGNATURES):
    raise AssertionError("general scene signatures must be unique")


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        return ["grid dimensions must be within 3..30"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC color integers 0..9"]
    return []


def _component_signature(grid, comps):
    height, width = len(grid), len(grid[0])
    dims = []
    border_touch_count = 0
    for comp in comps:
        r1, c1, r2, c2 = comp["bbox"]
        rect_height, rect_width = r2 - r1 + 1, c2 - c1 + 1
        dims.append((min(rect_height, rect_width), max(rect_height, rect_width)))
        if r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1:
            border_touch_count += 1
    has_duplicate_color = len({comp["color"] for comp in comps}) < len(comps)
    return (
        len(comps),
        border_touch_count,
        tuple(sorted(dims)),
        has_duplicate_color,
    )


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "components": []}

    if any(value == 8 for row in grid for value in row):
        errors.append("input must not already contain output color 8")

    comps = components(grid, same_color=True, connectivity=4)
    if not 2 <= len(comps) <= 4:
        errors.append(f"expected 2..4 monochrome rectangles, got {len(comps)}")
    if len({comp["color"] for comp in comps}) < 2:
        errors.append("expected at least two represented rectangle colors")
    if not components_have_clearance(grid, comps, diagonal=False):
        errors.append("distinct rectangles must not touch cardinally")

    for comp in comps:
        r1, c1, r2, c2 = comp["bbox"]
        rect_height, rect_width = r2 - r1 + 1, c2 - c1 + 1
        if rect_height < 3 or rect_width < 3:
            errors.append(
                "rectangle bbox too small for a strict interior: "
                f"{rect_height}x{rect_width}"
            )
        wanted = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
        }
        if set(comp["cells"]) != wanted:
            errors.append("every nonzero component must be a solid rectangle")

    exact = _PUBLIC_EXACT.get(tuple(map(tuple, grid)))
    signature = _component_signature(grid, comps) if comps else None
    profile = exact or _SIGNATURE_PROFILE.get(signature)
    if profile is None:
        errors.append("scene does not match a declared semantic profile")

    return {
        "errors": errors,
        "scene_profile": profile,
        "components": comps,
        "signature": signature,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or lesson-hiding scenes, not merely invalid colors."""
    return _analysis(grid)["errors"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_signature(grid):
    return _PUBLIC_EXACT.get(tuple(map(tuple, grid)))


def rule_mirror(grid):
    """Python test mirror; the Racket program remains output authority."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for comp in components(grid, same_color=True, connectivity=4):
        if comp["color"] == 8:
            continue
        r1, c1, r2, c2 = comp["bbox"]
        if r2 - r1 <= 1 or c2 - c1 <= 1:
            continue
        for row in range(r1 + 1, r2):
            for col in range(c1 + 1, c2):
                output[row][col] = 8
    return output


def _d4(grid, code):
    result = [list(row) for row in grid]
    if code >= 4:
        result = [list(reversed(row)) for row in result]
        code -= 4
    for _ in range(code):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _general_scene(profile, rng):
    height, width, rectangles = _GENERAL_SCENES[profile]
    grid = full_grid(height, width, 0)
    if profile == "four_duplicate_color":
        # The lesson anchor must visibly refute a canonical-palette-only
        # shortcut. Repeat an extended-palette color and include both color
        # families on every draw rather than leaving this to random chance.
        repeated = rng.choice([4, 5, 6, 7, 9])
        canonical = rng.choice([1, 2, 3])
        other_extended = rng.choice(
            [color for color in [4, 5, 6, 7, 9] if color != repeated]
        )
        colors = [repeated, repeated, canonical, other_extended]
        rng.shuffle(colors)
    else:
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], len(rectangles))

    for (row, col, rect_height, rect_width), color in zip(rectangles, colors):
        draw_rect(grid, row, col, rect_height, rect_width, color)

    grid = _d4(grid, rng.randrange(8))

    # Interior-only profiles can safely receive random zero padding without
    # changing their observable border-contact signature.
    if profile in {"two_interior_mixed", "three_interior", "same_size_pair"}:
        top, bottom, left, right = (rng.randrange(3) for _ in range(4))
        padded_width = len(grid[0]) + left + right
        padded = [[0] * padded_width for _ in range(top)]
        padded.extend([[0] * left + row + [0] * right for row in grid])
        padded.extend([[0] * padded_width for _ in range(bottom)])
        grid = padded

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError((profile, analysis))
    return grid



def schedule_profile(seed, sample_index, difficulty=None):
    """Observable ordinary-draw curriculum profile for semantic-gate replay."""
    del difficulty
    return _SCHEDULE_PATTERN[(int(seed) + int(sample_index)) % len(_SCHEDULE_PATTERN)]


def strict_canonical_like(grid):
    """Task-specific lawful-input predicate used by the semantic census."""
    return self_check(grid)


def _largest_only(grid):
    output = [list(row) for row in grid]
    comps = _analysis(grid)["components"]
    selected = [max(comps, key=lambda comp: len(comp["cells"]))] if comps else []
    return _fill_selected_interiors(output, selected)


def _one_per_color(grid):
    output = [list(row) for row in grid]
    selected = []
    seen = set()
    for comp in _analysis(grid)["components"]:
        if comp["color"] not in seen:
            seen.add(comp["color"])
            selected.append(comp)
    return _fill_selected_interiors(output, selected)


def _center_cell_only(grid):
    output = [list(row) for row in grid]
    for comp in _analysis(grid)["components"]:
        r1, c1, r2, c2 = comp["bbox"]
        output[(r1 + r2) // 2][(c1 + c2) // 2] = 8
    return output


def _skip_border_touching(grid):
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    selected = []
    for comp in _analysis(grid)["components"]:
        r1, c1, r2, c2 = comp["bbox"]
        if r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1:
            continue
        selected.append(comp)
    return _fill_selected_interiors(output, selected)


def _canonical_palette_only(grid):
    """Shortcut rival: transform only colors seen in canonical demos."""
    output = [list(row) for row in grid]
    selected = [
        comp
        for comp in _analysis(grid)["components"]
        if comp["color"] in {1, 2, 3}
    ]
    return _fill_selected_interiors(output, selected)


def _fill_selected_interiors(output, selected):
    for comp in selected:
        r1, c1, r2, c2 = comp["bbox"]
        for row in range(r1 + 1, r2):
            for col in range(c1 + 1, c2):
                output[row][col] = 8
    return output


def _witness_multiple_components(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["components"]) >= 2


def _witness_duplicate_color(grid):
    analysis = _analysis(grid)
    colors = [comp["color"] for comp in analysis["components"]]
    return not analysis["errors"] and len(set(colors)) < len(colors)


def _witness_border_touching(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    height, width = len(grid), len(grid[0])
    return any(
        r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1
        for r1, c1, r2, c2 in (comp["bbox"] for comp in analysis["components"])
    )


def _witness_nontrivial_interior(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        (comp["bbox"][2] - comp["bbox"][0] - 1)
        * (comp["bbox"][3] - comp["bbox"][1] - 1) > 1
        for comp in analysis["components"]
    )


def _witness_equal_size_pair(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    dimensions = [
        tuple(sorted((
            comp["bbox"][2] - comp["bbox"][0] + 1,
            comp["bbox"][3] - comp["bbox"][1] + 1,
        )))
        for comp in analysis["components"]
    ]
    return len(set(dimensions)) < len(dimensions)


def _witness_extended_palette(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        comp["color"] not in {1, 2, 3} for comp in analysis["components"]
    )


SEMANTIC_WITNESSES = {
    "multiple_components": _witness_multiple_components,
    "duplicate_color_components": _witness_duplicate_color,
    "border_touching_component": _witness_border_touching,
    "nontrivial_interior": _witness_nontrivial_interior,
    "equal_size_components": _witness_equal_size_pair,
    "extended_palette_component": _witness_extended_palette,
}
SEMANTIC_RIVALS = {
    "largest_only": _largest_only,
    "one_per_color": _one_per_color,
    "center_cell_only": _center_cell_only,
    "skip_border_touching": _skip_border_touching,
    "canonical_palette_only": _canonical_palette_only,
}
WITNESS_RIVALS = {
    "multiple_components": ["largest_only"],
    "duplicate_color_components": ["one_per_color"],
    "border_touching_component": ["skip_border_touching"],
    "nontrivial_interior": ["center_cell_only"],
    "equal_size_components": ["largest_only"],
    "extended_palette_component": ["canonical_palette_only"],
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query):
    """Require demos to refute every named rival before accepting the query."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the declared teaching grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the declared teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match the rectangle-interior rule")
            continue
        valid_demos.append(demo)

    for name, rival in SEMANTIC_RIVALS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"demonstrations fail to refute rival {name}")
    return reasons

def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(unknown)}")

    effective_overrides = dict(overrides)
    if "scene_profile" not in effective_overrides:
        effective_overrides["scene_profile"] = schedule_profile(
            seed, sample_index, difficulty=difficulty
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    if profile in _PUBLIC_INPUTS:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]

    rng = ctx.draw_rng(f"render_{difficulty or 'default'}")
    return _general_scene(profile, rng)
