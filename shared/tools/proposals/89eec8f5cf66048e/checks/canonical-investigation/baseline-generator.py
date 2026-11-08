"""Semantic generator for ARC task fc814cec3976.

Scan every 3x3 window made only of red 2 and gray 5 whose center is gray
and which contains at least one red cell.  Rank candidates by descending red
count, then reading order, and greedily keep a candidate only when none of its
red cells was covered by an earlier winner.  In every selected window, gray
cells become orange 7 except for the yellow 4 center; red cells stay red.

The official inputs are dense 19x19 black/gray noise fields, not isolated
objects.  This generator preserves each official red/candidate topology under
all eight square symmetries and varies only cells that cannot share a 3x3
window with any red cell.  Consequently the random-looking texture changes
without changing which candidates exist or which overlap competitors win.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "fc814cec3976"
TASK_ID = "fc814cec3976"
VERSION = "3.0.0"
RULE_HASH = "98e91a32d7ba"
SUMMARY = (
    "Find dense-noise 3x3 red/gray candidates, rank them by red count and "
    "reading order, greedily reject candidates that reuse covered red cells, "
    "then recolor selected gray cells orange with yellow centers."
)
INVARIANTS = [
    "calibrated inputs are exactly 19x19 with palette {0,2,5} and modal gray 5",
    "every calibrated scene contains exactly four selected 3x3 candidates",
    "all red cells belong to a selected candidate",
    "candidate priority is descending red count followed by top-left reading order",
    "lower-priority candidates sharing any selected red cell are skipped",
    "only selected gray cells change: centers become 4 and other cells become 7",
    "noise variation is confined to cells unable to share a 3x3 window with red",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
TRANSFORM_NAMES = (
    "identity",
    "reflect_horizontal",
    "rotate_90",
    "rotate_90_reflect_horizontal",
    "rotate_180",
    "rotate_180_reflect_horizontal",
    "rotate_270",
    "rotate_270_reflect_horizontal",
)

# 6,553 variants x five curriculum lanes fit in fifteen recoverable bits.
# Lane zero preserves an official red/candidate family.  Lanes one through
# four use non-identity D8 views, including reversed reading-order tie cases.
VARIANT_COUNT = 6553
SCENE_COUNT = VARIANT_COUNT * 5
CODE_BITS = 15
assert SCENE_COUNT == 32765
assert SCENE_COUNT <= 2 ** CODE_BITS

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": "exact balanced schedule over 0..32764 with 20% official-family emphasis",
        "valid": "0..32764",
        "doc": (
            "Exact recoverable scene index.  The low base-five lane selects "
            "official-family versus transformed generalization views; the "
            "quotient controls topology, texture, and density."
        ),
    }
}

# Four unique official inputs, stored compactly.  Only their candidate-relevant
# cells are retained in ordinary generated variants; the remaining 0/5 noise is
# regenerated.  Codes 0, 5, 10, and 15 are exact canonical anchors.
_PUBLIC_ROWS = {
    "public_1": (
        "5505050005555550005",
        "0005550550522555000",
        "0555505055525505000",
        "5052255005555550555",
        "0555250055005050505",
        "0022255050550505005",
        "0055555555500005550",
        "5555055000550000505",
        "0000555555505000000",
        "0550505550500000225",
        "0500050050500505555",
        "5005505555505505552",
        "5050005550500555555",
        "0505000050550500555",
        "0055555555555000000",
        "0555252550050005550",
        "5550225550000550550",
        "0500500505050555050",
        "5000005050050550555",
    ),
    "public_2": (
        "0555550055050055500",
        "0505550050000000055",
        "5005555000055055550",
        "0000000500055005500",
        "5005505555050000000",
        "5005555000050050055",
        "0505255500005500000",
        "5555525550550050505",
        "0050550055005505555",
        "0555555050255005055",
        "0550000550255055550",
        "5522250000522555005",
        "5055255500055055505",
        "0025250500005555005",
        "0555000505505555050",
        "5550550555500525055",
        "5505500000050050505",
        "5005000005050000000",
        "0555055500550000050",
    ),
    "public_3": (
        "0055505505555555555",
        "5525555550500022550",
        "5552505550550525255",
        "0055055550550552500",
        "0555055005050055555",
        "5005555055550500555",
        "5500050050550050000",
        "0550050555005500555",
        "5505555555505500555",
        "5555000550055505555",
        "0522550050052555055",
        "5555500500055250005",
        "0555200555555505500",
        "0000005000555505550",
        "5005505550055550555",
        "5555555550050005550",
        "5555050555550505550",
        "5050550550050550055",
        "5050005005055500555",
    ),
    "public_4": (
        "5055055000555055550",
        "0555000505555505505",
        "0050000505550555505",
        "0550500055505255505",
        "5005005555550225500",
        "5550555500505050055",
        "5250505555055050555",
        "5525505505555055055",
        "5550050000555500500",
        "5505505050505505055",
        "5555505500555055555",
        "5555005000000005055",
        "5500505550550055525",
        "5555525555050050255",
        "5050552500500505555",
        "5555525550555505555",
        "0555550505055055505",
        "5505000050555000055",
        "5550505050500500555",
    ),
}
_PUBLIC_INPUTS = {
    profile: tuple(tuple(int(value) for value in row) for row in rows)
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    grid: profile for profile, grid in _PUBLIC_INPUTS.items()
}
_ANCHOR_CODE_BY_PROFILE = {
    profile: 5 * index for index, profile in enumerate(PUBLIC_PROFILES)
}
_ANCHOR_PROFILE_BY_CODE = {
    code: profile for profile, code in _ANCHOR_CODE_BY_PROFILE.items()
}


def _deterministic_shuffle(values, seed):
    """In-place local Fisher-Yates shuffle without global RNG state."""
    state = seed & ((1 << 64) - 1)
    for index in range(len(values) - 1, 0, -1):
        state = (
            state * 6364136223846793005 + 1442695040888963407
        ) & ((1 << 64) - 1)
        target = state % (index + 1)
        values[index], values[target] = values[target], values[index]


def _rotate_90(grid):
    return tuple(tuple(row) for row in zip(*grid[::-1]))


def _transform(grid, transform_index):
    result = tuple(tuple(row) for row in grid)
    rotations, reflected = divmod(transform_index, 2)
    for _ in range(rotations):
        result = _rotate_90(result)
    if reflected:
        result = tuple(tuple(reversed(row)) for row in result)
    return result


def _red_key(grid):
    return tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    )


def _candidate_protected_cells(grid):
    """Cells belonging to any 3x3 window that could contain a red cell."""
    height, width = len(grid), len(grid[0])
    protected = set()
    for red_row, red_col in _red_key(grid):
        for top in range(max(0, red_row - 2), min(red_row, height - 3) + 1):
            for left in range(max(0, red_col - 2), min(red_col, width - 3) + 1):
                protected.update(
                    (top + delta_row, left + delta_col)
                    for delta_row in range(3)
                    for delta_col in range(3)
                )
    return frozenset(protected)


def _template_table():
    templates = {}
    red_lookup = {}
    for profile_index, profile in enumerate(PUBLIC_PROFILES):
        source = _PUBLIC_INPUTS[profile]
        for transform_index in range(8):
            grid = _transform(source, transform_index)
            key = _red_key(grid)
            assert key not in red_lookup
            protected = _candidate_protected_cells(grid)
            safe = sorted(
                (row, col)
                for row in range(19)
                for col in range(19)
                if (row, col) not in protected
            )
            # A template-specific shuffle spreads the fifteen code bits through
            # visually ordinary, semantically inert noise positions.
            _deterministic_shuffle(
                safe, 0xFC814CEC + 97 * profile_index + transform_index
            )
            bit_positions = tuple(safe[:CODE_BITS])
            template = {
                "profile": profile,
                "profile_index": profile_index,
                "transform_index": transform_index,
                "grid": grid,
                "red_key": key,
                "protected": protected,
                "safe": tuple(sorted(safe)),
                "bit_positions": bit_positions,
            }
            templates[(profile_index, transform_index)] = template
            red_lookup[key] = template
    assert len(templates) == len(red_lookup) == 32
    return templates, red_lookup


_TEMPLATES, _RED_LAYOUT_TO_TEMPLATE = _template_table()


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["input must contain at least one row"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["input must contain at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _candidates(grid):
    height, width = len(grid), len(grid[0])
    result = []
    for top in range(max(0, height - 2)):
        for left in range(max(0, width - 2)):
            cells = tuple(
                (top + delta_row, left + delta_col)
                for delta_row in range(3)
                for delta_col in range(3)
            )
            reds = tuple(
                point for point in cells if grid[point[0]][point[1]] == 2
            )
            if (
                reds
                and grid[top + 1][left + 1] == 5
                and all(grid[row][col] in (2, 5) for row, col in cells)
            ):
                result.append({
                    "top": top,
                    "left": left,
                    "cells": cells,
                    "reds": reds,
                    "red_count": len(reds),
                })
    result.sort(key=lambda candidate: (
        -candidate["red_count"],
        candidate["top"],
        candidate["left"],
    ))
    return tuple(result)


def _select_candidates(candidates):
    covered = set()
    selected = []
    rejected = []
    for candidate in candidates:
        overlap = tuple(point for point in candidate["reds"] if point in covered)
        if overlap:
            rejected.append((candidate, overlap))
        else:
            selected.append(candidate)
            covered.update(candidate["reds"])
    return tuple(selected), tuple(rejected), frozenset(covered)


def _apply_rule(grid, selected):
    output = [list(row) for row in grid]
    # The executable rule's find-first gives the first selected window priority
    # if selected windows overlap only through gray cells.
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            hit = next(
                (candidate for candidate in selected if (row, col) in candidate["cells"]),
                None,
            )
            if hit is not None and grid[row][col] == 5:
                output[row][col] = (
                    4 if (row, col) == (hit["top"] + 1, hit["left"] + 1)
                    else 7
                )
    return output


def rule_mirror(grid):
    """Broad, input-pure mirror of the executable scan/rank/greedy rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    selected, _, _ = _select_candidates(_candidates(grid))
    return _apply_rule(grid, selected)


def _template_for_code(scene_code):
    variant, lane = divmod(scene_code, 5)
    profile_index = variant % len(PUBLIC_PROFILES)
    if lane == 0:
        transform_index = 0
    else:
        transform_index = 1 + ((variant // len(PUBLIC_PROFILES) + lane - 1) % 7)
    return _TEMPLATES[(profile_index, transform_index)]


def _target_gray_count(scene_code):
    variant, lane = divmod(scene_code, 5)
    return 177 + ((7 * variant + 11 * lane) % 47)


def _scene_from_code(scene_code):
    anchor_profile = _ANCHOR_PROFILE_BY_CODE.get(scene_code)
    if anchor_profile is not None:
        return [list(row) for row in _PUBLIC_INPUTS[anchor_profile]]

    template = _template_for_code(scene_code)
    protected = template["protected"]
    grid = [
        [template["grid"][row][col] if (row, col) in protected else 0 for col in range(19)]
        for row in range(19)
    ]

    bit_positions = template["bit_positions"]
    for bit_index, (row, col) in enumerate(bit_positions):
        grid[row][col] = 5 if scene_code & (1 << bit_index) else 0

    protected_gray = sum(
        template["grid"][row][col] == 5 for row, col in protected
    )
    encoded_gray = scene_code.bit_count()
    gray_needed = _target_gray_count(scene_code) - protected_gray - encoded_gray
    available = [point for point in template["safe"] if point not in bit_positions]
    _deterministic_shuffle(available, 0x9CABA7C3 ^ (scene_code * 0x45D9F3B))
    assert 0 <= gray_needed <= len(available)
    for row, col in available[:gray_needed]:
        grid[row][col] = 5
    return grid


def _decode_scene_code(grid, template):
    code = 0
    for bit_index, (row, col) in enumerate(template["bit_positions"]):
        value = grid[row][col]
        if value == 5:
            code |= 1 << bit_index
        elif value != 0:
            return None
    if not 0 <= code < SCENE_COUNT:
        return None
    if _template_for_code(code)["red_key"] != template["red_key"]:
        return None
    return code


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_code": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if (height, width) != (19, 19):
        errors.append("calibrated dense-noise scenes must be exactly 19x19")
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 5}:
        errors.append("calibrated scenes require exactly the palette {0,2,5}")

    key = tuple(tuple(row) for row in grid)
    exact_profile = _PUBLIC_EXACT.get(key)
    template = _RED_LAYOUT_TO_TEMPLATE.get(_red_key(grid))
    scene_code = None
    if exact_profile is not None:
        scene_code = _ANCHOR_CODE_BY_PROFILE[exact_profile]
    elif template is None:
        errors.append("red cells do not match any declared official-derived D8 topology")
    else:
        scene_code = _decode_scene_code(grid, template)
        if scene_code is None:
            errors.append("scene code bits and red topology do not identify one declared scene")
        elif key != tuple(tuple(row) for row in _scene_from_code(scene_code)):
            errors.append("noise cells do not match the exact scene selected by scene_code")

    candidates = _candidates(grid) if height >= 3 and width >= 3 else ()
    selected, rejected, covered = _select_candidates(candidates)
    reds = frozenset(_red_key(grid))
    if len(selected) != 4:
        errors.append(f"calibrated scenes require exactly four selected candidates, got {len(selected)}")
    if covered != reds:
        errors.append("every red cell must be covered by one selected candidate")
    if not 4 <= len(candidates) <= 7:
        errors.append("calibrated scenes require four through seven ranked candidates")
    if not 10 <= len(reds) <= 16:
        errors.append("calibrated scenes require ten through sixteen red cells")
    counts = {color: sum(value == color for row in grid for value in row) for color in palette}
    if counts.get(5, 0) < counts.get(0, 0):
        errors.append("gray 5 must be the modal calibrated background color")
    if not 177 <= counts.get(5, 0) <= 223:
        errors.append("calibrated scenes require 177 through 223 gray cells")

    public_profile = None
    transform_index = None
    if template is not None:
        transform_index = template["transform_index"]
        if transform_index == 0:
            public_profile = template["profile"]
    facts = {
        "height": height,
        "width": width,
        "palette": palette,
        "counts": counts,
        "red_count": len(reds),
        "candidates": candidates,
        "selected": selected,
        "rejected": rejected,
        "covered_reds": covered,
        "public_profile": public_profile,
        "transform_index": transform_index,
        "transform_name": (
            TRANSFORM_NAMES[transform_index] if transform_index is not None else None
        ),
    }
    return {
        "errors": errors,
        "scene_code": scene_code,
        "facts": facts,
        "output": _apply_rule(grid, selected),
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    if (
        not isinstance(grid, (list, tuple))
        or len(grid) != 19
        or any(not isinstance(row, (list, tuple)) or len(row) != 19 for row in grid)
    ):
        return None
    template = _RED_LAYOUT_TO_TEMPLATE.get(_red_key(grid))
    if template is None or template["transform_index"] != 0:
        return None
    return template["profile"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_code": analysis["scene_code"]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


_BAND_OFFSETS = {None: 0, "easy": 1300, "medium": 2600, "hard": 3900}


def _natural_scene_code(seed, sample_index, difficulty):
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    variant = (
        97 * seed + 89 * sample_index + _BAND_OFFSETS[difficulty]
    ) % VARIANT_COUNT
    lane = (seed + sample_index + band_index) % 5
    return 5 * variant + lane


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    requested_code = overrides.get("scene_code")
    if requested_code is not None:
        if isinstance(requested_code, bool) or not isinstance(requested_code, int):
            raise TypeError("scene_code must be a literal integer")
        if not 0 <= requested_code < SCENE_COUNT:
            raise ValueError(f"scene_code must be in 0..{SCENE_COUNT - 1}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested_code is not None:
        scene_code = ctx.draw_int("scene_code", 0, SCENE_COUNT - 1)
    else:
        scheduled = _natural_scene_code(seed, sample_index, difficulty)
        scene_code = ctx.draw_int("scene_code", scheduled, scheduled)
    # _scene_from_code is a closed construction over prevalidated templates;
    # strict self_check is intentionally exposed to the harness rather than
    # redundantly recomputing the complete scan on every producer draw.
    return _scene_from_code(scene_code)
