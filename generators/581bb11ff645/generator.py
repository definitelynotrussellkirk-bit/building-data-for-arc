"""Semantic generator for ARC task 581bb11ff645.

Red column groups span the canvas height and are separated by zero columns.
Count the zero holes inside each group, sort complete groups by increasing
hole count, and copy them into the original left-to-right group slots.  The
background, separators, and holes are zero; all other input cells are red (2).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "581bb11ff645"
TASK_ID = "581bb11ff645"
VERSION = "3.0.0"
RULE_HASH = "79264cb5e9cc"
MIN_SYNTHETIC_CHANGE_RATE = 0.03
SUMMARY = "Sort complete separator-delimited red column groups into their original slots by increasing zero-hole count."
INVARIANTS = [
    "red column groups are separated by complete zero columns",
    "all groups have one common width and span the full grid height except for holes",
    "group hole counts are distinct ranks from one through the group count",
    "groups move as complete two-dimensional patterns into fixed left-to-right slots",
    "the output orders groups from fewest holes to most holes",
    "the palette is intrinsically limited to zero and red (2)",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "groups3_width2",
    "groups3_width3",
    "groups3_width4",
    "groups4_width2",
    "groups4_width3",
    "groups4_width4",
    "groups5_width2",
    "groups5_width3",
    "groups5_width4",
    "reverse_ranks",
    "adjacent_rank_swap",
    "cyclic_ranks",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve recoverable hole-rank sorting lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = (
    "222022202220222/222020202020222/222022202220222/222020202020202/222022202220222/202020202020222/222022202220222/202022202020222/222022202220222",
    "22202220222/20202220202/22202220222/20202220202/22202220222/22202020202/22202220222",
    "222022202220222/222020202220202/222022202220222/222020202020202/222022202220222/202022202020202/222022202220222/222020202220202/222022202220222",
    "2220222022202220222/2220222020202020202/2220222022202220222/2220222022202020222/2220222022202220222/2020222020202020202/2220222022202220222/2220202020202020202/2220222022202220222/2020222022202020202/2220222022202220222",
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
    if not 5 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["input dimensions must be between 5 and 30 rows and 7 and 30 columns"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2) for row in grid for value in row):
        return ["input cells must be literal zero or red (2)"]
    return []


def _group_bounds(grid):
    height, width = len(grid), len(grid[0])
    groups = []
    start = None
    for col in range(width):
        has_red = any(grid[row][col] == 2 for row in range(height))
        if has_red and start is None:
            start = col
        elif not has_red and start is not None:
            groups.append((start, col - 1))
            start = None
    if start is not None:
        groups.append((start, width - 1))
    return tuple(groups)


def _hole_counts(grid, groups):
    height = len(grid)
    return tuple(sum(grid[row][col] == 0 for row in range(height) for col in range(first, last + 1)) for first, last in groups)


def _apply_rule(grid, groups, hole_counts):
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    ranked = sorted(zip(hole_counts, groups), key=lambda item: item[0])
    for destination, (_, source) in zip(groups, ranked):
        source_first, source_last = source
        destination_first, _ = destination
        for row in range(height):
            for offset in range(source_last - source_first + 1):
                output[row][destination_first + offset] = grid[row][source_first + offset]
    return output


def rule_mirror(grid):
    """Exact Python mirror of canonical group discovery, sorting, and copy."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    groups = _group_bounds(grid)
    if not groups:
        raise ValueError("no red column groups")
    return _apply_rule(grid, groups, _hole_counts(grid, groups))


def _rank_profile(hole_counts):
    count = len(hole_counts)
    if hole_counts == tuple(range(count, 0, -1)):
        return "reverse_ranks"
    if hole_counts == (2, 1, *range(3, count + 1)):
        return "adjacent_rank_swap"
    if hole_counts == (*range(2, count + 1), 1):
        return "cyclic_ranks"
    return None


def _profile_for(grid, groups, hole_counts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    special = _rank_profile(hole_counts)
    if special:
        return special
    width = groups[0][1] - groups[0][0] + 1
    candidate = f"groups{len(groups)}_width{width}"
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    groups = _group_bounds(grid)
    if not 3 <= len(groups) <= 5:
        errors.append("exactly three through five red column groups are required")
    if groups and (groups[0][0] != 0 or groups[-1][1] != width - 1):
        errors.append("group slots must cover both outer grid edges")
    if any(groups[index + 1][0] - groups[index][1] != 2 for index in range(len(groups) - 1)):
        errors.append("adjacent group slots must have exactly one zero separator column")
    widths = tuple(last - first + 1 for first, last in groups)
    if not widths or len(set(widths)) != 1 or widths[0] not in (2, 3, 4):
        errors.append("all groups must share a width of two, three, or four columns")
    holes = _hole_counts(grid, groups)
    if set(holes) != set(range(1, len(groups) + 1)):
        errors.append("hole counts must be distinct ranks from one through the group count")
    if holes == tuple(sorted(holes)):
        errors.append("groups already sorted by holes would make an identity lesson")
    profile = _profile_for(grid, groups, holes) if groups else None
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared group/rank profile")
    output = _apply_rule(grid, groups, holes) if not errors else None
    if output is not None and output == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    facts = {
        "height": height,
        "width": width,
        "groups": groups,
        "group_widths": widths,
        "hole_counts": holes,
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


def _height(difficulty, rng):
    if difficulty == "easy":
        return rng.randint(7, 9)
    if difficulty == "medium":
        return rng.randint(8, 11)
    if difficulty == "hard":
        return rng.randint(10, 13)
    return rng.randint(7, 12)


def _special_shape(profile):
    if profile == "reverse_ranks":
        return 5, 3
    if profile == "adjacent_rank_swap":
        return 3, 3
    return 4, 3


def _generic_rank_order(count, rng):
    forbidden = {
        tuple(range(1, count + 1)),
        tuple(range(count, 0, -1)),
        (2, 1, *range(3, count + 1)),
        (*range(2, count + 1), 1),
    }
    candidates = []
    values = list(range(1, count + 1))
    for _ in range(100):
        rng.shuffle(values)
        candidate = tuple(values)
        if candidate not in forbidden:
            return candidate
        candidates.append(candidate)
    raise AssertionError(f"could not draw generic rank order from {candidates[-3:]}")


def _general_scene(profile, difficulty, rng):
    for _ in range(100):
        if profile.startswith("groups"):
            count = int(profile[6])
            group_width = int(profile[-1])
            rank_order = _generic_rank_order(count, rng)
        else:
            count, group_width = _special_shape(profile)
            if profile == "reverse_ranks":
                rank_order = tuple(range(count, 0, -1))
            elif profile == "adjacent_rank_swap":
                rank_order = (2, 1, *range(3, count + 1))
            else:
                rank_order = (*range(2, count + 1), 1)
        height = _height(difficulty, rng)
        width = count * group_width + count - 1
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for index, holes in enumerate(rank_order):
            start = index * (group_width + 1)
            cells = [(row, col) for row in range(height) for col in range(start, start + group_width)]
            hole_cells = set(rng.sample(cells, holes))
            for row, col in cells:
                grid[row][col] = 0 if (row, col) in hole_cells else 2
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
