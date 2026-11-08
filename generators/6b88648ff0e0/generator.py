"""Semantic generator for ARC task 6b88648ff0e0 (source aab50785).

Exact 2x2 cyan (8) marker pairs are embedded in a dense field containing all
other ARC colors.  For each marker top row, extract the two rows strictly
between its leftmost and rightmost marker blocks.  Stack those strips in
top-to-bottom order.  Noise outside the marked intervals is discarded.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "6b88648ff0e0"
TASK_ID = "6b88648ff0e0"
VERSION = "3.0.0"
RULE_HASH = "7bc08a76718f"
SUMMARY = "Extract each two-row strip between paired 2x2 cyan markers and stack the strips in marker-row order, discarding the surrounding nine-color noise field."
INVARIANTS = [
    "inputs contain all ten ARC colors, with cyan 8 reserved exclusively for exact 2x2 marker blocks",
    "each marker top row contains exactly two 2x2 cyan blocks",
    "one through four marker groups are vertically disjoint and ordered by top row",
    "every group has the same three-through-seven-cell interior width",
    "interior strips and exterior distractor cells may contain any non-cyan color, including zero",
    "the output is the two interior rows from each group stacked top-to-bottom",
    "all cells outside the marked interiors and every cyan marker are discarded",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5", "public_6")
GENERAL_PROFILES = (
    "groups1_narrow", "groups1_wide",
    "groups2_narrow", "groups2_wide",
    "groups3_narrow", "groups3_wide",
    "groups4_narrow", "groups4_wide",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "six exact-public and eight group-count/strip-width extraction lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|public_6|groups1_narrow|groups1_wide|groups2_narrow|groups2_wide|groups3_narrow|groups3_wide|groups4_narrow|groups4_wide",
    }
}

_PUBLIC_ROWS = (
    "92153430000500000/08830707884072000/18802006880000070/10000413910759470/00322026049240305/06883019288030400/00880792988093009/00040757501302000/00993640472090090/91900715710505969/00372088900008810/67040488040208850",
    "040100010000000/003007907700130/200006000000000/000088359188020/000088100688300/200050000092002/009049990296140/000000940000005/100000090005060/210060627040007/090020501000053/400300000000400",
    "9005000044/9400000050/2206005053/2902640100/0029049113/8810977088/8840056488/0590000000/0001050030/0900000709/0051700099/0090010007",
    "0727020004001000/0100000600200731/0088652881024500/0088002880071007/0000400090700000/8813088000090301/8800988000003092/0070000009340000/4009090073060405/6000400300205000/0000300012040000/4500604000005202/0906000720930006",
    "02000045001065000/90430090479460270/07300090090099950/05530306047232030/08800070889006004/08864319880000007/90095200000020001/02990090710009000/07088040608890000/02488030068865790/00920200079000571/10030104140000109/10621460019030140",
    "00690009007090090/00000006700000000/00440900000201051/21088415088010400/07388090088060472/25040000790950401/88590488403700005/88770088647060004/06904003090300034/05200002900604500/07038845438895030/00008800708800000/00100000002010350/09200098800608806/00090008807048800",
)
_NON_CYAN = tuple(color for color in range(10) if color != 8)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 8 <= len(grid) <= 30:
        return ["input must contain eight through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 8 <= len(grid[0]) <= 30:
        return ["input must contain eight through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _detected_groups(grid):
    height, width = len(grid), len(grid[0])
    by_row = defaultdict(list)
    for row in range(height - 1):
        for col in range(width - 1):
            if all(grid[r][c] == 8 for r in (row, row + 1) for c in (col, col + 1)):
                by_row[row].append(col)
    return tuple((row, tuple(cols)) for row, cols in sorted(by_row.items()))


def _geometry_signature(grid):
    return len(grid), len(grid[0]), _detected_groups(grid)


_PUBLIC_GEOMETRIES = {_geometry_signature(grid): name for name, grid in _PUBLIC_INPUTS.items()}


def rule_mirror(grid):
    """Exact Python mirror of the canonical 2x2-marker extraction rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    groups = _detected_groups(grid)
    if not groups:
        raise ValueError("no 2x2 cyan marker groups found")
    strips = []
    for top, cols in groups:
        left, right = min(cols), max(cols)
        strips.extend([list(grid[row][left + 2:right]) for row in (top, top + 1)])
    width = len(strips[0])
    if width < 1 or any(len(row) != width for row in strips):
        raise ValueError("extracted strips must have one uniform positive width")
    return strips


def _profile_for(grid, groups, width):
    exact = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if exact:
        return exact
    family = _PUBLIC_GEOMETRIES.get(_geometry_signature(grid))
    if family:
        return family
    category = "narrow" if width in (3, 4) else "wide" if width in (5, 6, 7) else None
    candidate = f"groups{len(groups)}_{category}" if category else None
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "groups": (), "scene_profile": None, "output": None}
    palette = {value for row in grid for value in row}
    if palette != set(range(10)):
        errors.append(f"input must contain all ten ARC colors, got {sorted(palette)}")
    groups = _detected_groups(grid)
    if not 1 <= len(groups) <= 4:
        errors.append(f"expected one through four marker rows, got {len(groups)}")
    if any(len(cols) != 2 for _, cols in groups):
        errors.append("each marker row must contain exactly two detected 2x2 cyan blocks")
    if any(next_row - row < 3 for (row, _), (next_row, _) in zip(groups, groups[1:])):
        errors.append("marker groups must be separated by at least one complete row")
    marker_cells = set()
    for top, cols in groups:
        for left in cols:
            marker_cells.update((row, col) for row in (top, top + 1) for col in (left, left + 1))
    cyan_cells = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 8}
    if cyan_cells != marker_cells:
        errors.append("cyan 8 must occur exclusively in the detected exact 2x2 marker blocks")
    widths = {max(cols) - min(cols) - 2 for _, cols in groups if len(cols) == 2}
    if len(widths) != 1:
        errors.append("all marker pairs must define one uniform interior width")
        width = None
    else:
        width = next(iter(widths))
        if not 3 <= width <= 7:
            errors.append(f"interior width must be three through seven, got {width}")
    profile = _profile_for(grid, groups, width) if width is not None else None
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared marker-count/width profile")
    output = None
    if not errors:
        output = rule_mirror(grid)
        if len(output) != 2 * len(groups) or len(output[0]) != width:
            errors.append("output dimensions do not equal two rows per group by the shared interior width")
        if any(value == 8 for row in output for value in row):
            errors.append("cyan markers must never enter the extracted output")
    facts = {
        "group_count": len(groups),
        "groups": groups,
        "content_width": width,
        "output_shape": (2 * len(groups), width) if width is not None else None,
        "scene_profile": profile,
        "palette": tuple(sorted(palette)),
    }
    return {"errors": errors, "groups": groups, "facts": facts, "scene_profile": profile, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def canonical_family_signature(grid):
    return _PUBLIC_GEOMETRIES.get(_geometry_signature(grid)) if not _valid_grid(grid) else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return (10, 14), (10, 16)
    if difficulty == "medium":
        return (12, 18), (12, 21)
    if difficulty == "hard":
        return (15, 24), (15, 26)
    return (11, 21), (10, 24)


def _weighted_non_cyan(rng):
    return rng.choice((0, 0, 0, 0) + _NON_CYAN)


def _fill_scene(height, width, layouts, rng):
    grid = [[_weighted_non_cyan(rng) for _ in range(width)] for _ in range(height)]
    marker_cells = {
        (row, col)
        for top, left, right in layouts
        for row in (top, top + 1)
        for start in (left, right)
        for col in (start, start + 1)
    }
    safe = [(row, col) for row in range(height) for col in range(width) if (row, col) not in marker_cells]
    rng.shuffle(safe)
    for color, (row, col) in zip(_NON_CYAN, safe):
        grid[row][col] = color
    for row, col in marker_cells:
        grid[row][col] = 8
    return grid


def _general_scene(profile, difficulty, rng):
    group_text, width_kind = profile.split("_")
    count = int(group_text.removeprefix("groups"))
    content_width = rng.randint(3, 4) if width_kind == "narrow" else rng.randint(5, 7)
    height_limits, width_limits = _limits(difficulty)
    minimum_height = max(height_limits[0], 3 * count - 1)
    minimum_width = max(width_limits[0], content_width + 4)
    height = rng.randint(minimum_height, height_limits[1])
    width = rng.randint(minimum_width, width_limits[1])
    candidates = [tops for tops in combinations(range(height - 1), count) if all(b - a >= 3 for a, b in zip(tops, tops[1:]))]
    tops = rng.choice(candidates)
    layouts = []
    for top in tops:
        left = rng.randint(0, width - content_width - 4)
        right = left + content_width + 2
        layouts.append((top, left, right))
    return _fill_scene(height, width, layouts, rng)


def _public_nuisance(profile, rng):
    source = _PUBLIC_INPUTS[profile]
    layouts = [(top, min(cols), max(cols)) for top, cols in _detected_groups(source)]
    return _fill_scene(len(source), len(source[0]), layouts, rng)


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
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 3 + GENERAL_PROFILES * 6)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_noise"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid strip-extraction lesson: " + "; ".join(errors))
    return grid
