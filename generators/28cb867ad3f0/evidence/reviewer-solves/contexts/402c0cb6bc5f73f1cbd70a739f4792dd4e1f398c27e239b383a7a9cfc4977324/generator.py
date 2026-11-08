"""Semantic generator for ARC task 28cb867ad3f0 (bank 385e738e9e70:H97).

Every 4-connected color-0 chamber is filled with the unique plurality among
colors 1..4 on its cardinal boundary.  A tied or empty vote leaves the chamber
0.  Color 5 is a neutral wall and every non-chamber cell is preserved.

The curriculum alternates a compact full-contrast scene with nine canonical or
controlled profiles.  Therefore every four-pair lesson retains a full-contrast
demonstration under every possible query rotation, while the odd positions keep
canonical geometry and simpler contrasts in the training distribution.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "28cb867ad3f0"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "56654a66f781"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Fill each 4-connected zero chamber with its unique plurality boundary "
    "marker color from 1..4. Tied or empty votes leave that chamber zero; "
    "color-5 walls and all marker cells are preserved."
)

INVARIANTS = [
    "zero chambers do not touch the outer border; border markers may vote from outside",
    "colors 1..4 are voting markers and every marker touches a zero chamber",
    "votes are counted per cardinal incidence; one marker may vote multiple times for one chamber",
    "votes are counted independently for each chamber, including shared markers",
    "a unique plurality fills the whole chamber; a tie leaves it zero",
    "all nonzero cells are preserved by the rule",
    "ordinary draws alternate full-contrast witnesses with canonical or controlled profiles",
    "every four consecutive samples contain two full-contrast witnesses",
    "the declared scene_profile is exactly recoverable from the returned grid",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = ("all_colors", "one_tie", "two_ties", "shared_focus")
FULL_CONTRAST_PROFILE = "full_contrast"
ROTATING_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
SCENE_PROFILES = ROTATING_PROFILES + (FULL_CONTRAST_PROFILE,)
SCHEDULE_PROFILES = (FULL_CONTRAST_PROFILE,) + ROTATING_PROFILES
LESSON_SCHEDULE_PERIOD = 18
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "alternating full-contrast witnesses and a deterministic nine-profile cycle",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {'public_1': ('55555555555555',
              '55112555332555',
              '51000055000035',
              '55000055000055',
              '55000055000025',
              '55554422000055',
              '55550000055555',
              '55550000055555',
              '55550000055555',
              '55555555555555'),
 'public_2': ('5555555555555',
              '5522555444555',
              '5500055000055',
              '5100055000035',
              '5500055000055',
              '5500055555555',
              '5500051125555',
              '5555550000155',
              '5555550000555',
              '5555550000555',
              '5555555555555'),
 'public_3': ('555555555555555',
              '555333555222555',
              '555000055000005',
              '551000055000005',
              '555000055000002',
              '554140055555555',
              '510000555555555',
              '550000555555555',
              '550000555555555',
              '555555555555555'),
 'public_4': ('55555555555555',
              '55555555335555',
              '55111555000035',
              '55000055000055',
              '52000055000045',
              '55000055000055',
              '55555555000055',
              '55555554445555',
              '55555550000555',
              '55555550000255',
              '55555550000555',
              '55555555555555'),
 'public_5': ('555555555555555',
              '552225555114555',
              '550000055000055',
              '530000055000015',
              '550000055000055',
              '555555555000055',
              '555553345555555',
              '555550000055555',
              '555550000045555',
              '555550000055555',
              '555555555555555')}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _zero_components(grid: list[list[int]] | tuple[tuple[int, ...], ...]):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    }
    components = []
    while cells:
        queue = [cells.pop()]
        component = []
        for row, col in queue:
            component.append((row, col))
            for other in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if other in cells:
                    cells.remove(other)
                    queue.append(other)
        components.append(component)
    return sorted(components, key=lambda component: min(component))


def _boundary_positions(grid, component):
    height, width = len(grid), len(grid[0])
    positions = []
    for row, col in component:
        for other_row, other_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= other_row < height and 0 <= other_col < width:
                value = grid[other_row][other_col]
                if 1 <= value <= 4:
                    positions.append((other_row, other_col))
    return positions


def _boundary_votes(grid, component):
    return [grid[row][col] for row, col in _boundary_positions(grid, component)]


def _unique_plurality(votes) -> int:
    ranked = Counter(votes).most_common()
    if not ranked:
        return 0
    if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
        return ranked[0][0]
    return 0


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    result = [list(row) for row in grid]
    for component in _zero_components(grid):
        winner = _unique_plurality(_boundary_votes(grid, component))
        if winner:
            for row, col in component:
                result[row][col] = winner
    return result


def _component_facts(grid, component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    rectangle = len(component) == (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
    positions = _boundary_positions(grid, component)
    votes = [grid[row][col] for row, col in positions]
    counts = Counter(votes)
    return {
        "cells": tuple(sorted(component)),
        "bbox": bbox,
        "rectangle": rectangle,
        "boundary_positions": tuple(positions),
        "votes": tuple(counts[color] for color in range(1, 5)),
        "winner": _unique_plurality(votes),
        "distinct_vote_colors": len(counts),
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 30 or not 7 <= width <= 30:
        errors.append(f"grid dimensions must be 7..30, got {height}x{width}")
    if any(value not in range(6) for row in grid for value in row):
        errors.append("task palette is restricted to colors 0..5")
    palette = {value for row in grid for value in row}
    if palette != set(range(6)):
        errors.append(f"task input must witness every color 0..5, got {sorted(palette)}")
    border = list(grid[0]) + list(grid[-1]) + [row[0] for row in grid[1:-1]] + [row[-1] for row in grid[1:-1]]
    if any(value == 0 for value in border):
        errors.append("zero chambers must not touch the outer border")

    components = _zero_components(grid)
    if not 1 <= len(components) <= 8:
        errors.append(f"expected 1..8 zero chambers, got {len(components)}")
    chamber_facts = []
    marker_to_components: dict[tuple[int, int], set[int]] = {}
    for index, component in enumerate(components):
        if len(component) < 4:
            errors.append(f"zero chamber {index} is too small ({len(component)} cells)")
        if any(row in (0, height - 1) or col in (0, width - 1) for row, col in component):
            errors.append(f"zero chamber {index} touches the outer border")
        facts = _component_facts(grid, component)
        if not any(facts["votes"]):
            errors.append(f"zero chamber {index} has no boundary marker")
        chamber_facts.append(facts)
        for position in set(facts["boundary_positions"]):
            marker_to_components.setdefault(position, set()).add(index)

    marker_positions = {
        (row, col)
        for row in range(height) for col in range(width)
        if 1 <= grid[row][col] <= 4
    }
    stray = marker_positions - set(marker_to_components)
    if stray:
        errors.append(f"marker cells must touch a zero chamber; stray={sorted(stray)[:4]}")

    shared_markers = {position: owners for position, owners in marker_to_components.items() if len(owners) > 1}
    exact_profile = None
    try:
        exact_profile = _SCENE_VARIANTS.get(tuple(tuple(row) for row in grid))
    except (TypeError, NameError):
        exact_profile = None

    profile = exact_profile
    if not errors and profile is None and len(chamber_facts) == 4 and all(f["rectangle"] for f in chamber_facts):
        winners = [facts["winner"] for facts in chamber_facts]
        ties = winners.count(0)
        distinct = len(set(winners) - {0})
        if ties == 0 and distinct == 4 and not shared_markers:
            profile = "all_colors"
        elif ties == 1 and distinct == 3 and not shared_markers:
            profile = "one_tie"
        elif ties == 2 and distinct == 2 and not shared_markers:
            profile = "two_ties"
        elif ties == 0 and distinct == 1 and len(shared_markers) >= 4:
            profile = "shared_focus"

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": chamber_facts,
        "shared_markers": shared_markers,
        "scene_profile": profile,
    }


def observe_overrides(grid: Any) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["scene_profile"] not in SCENE_PROFILES:
        raise ValueError("grid is lawful but is not one of the declared scene profiles")
    return {"scene_profile": analysis["scene_profile"]}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if not errors and requested.get("scene_profile") is not None:
        observed = analysis["scene_profile"]
        if observed != requested["scene_profile"]:
            errors.append(
                f"scene_profile drifted from requested {requested['scene_profile']!r} to {observed!r}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The task manifold is the enclosed chamber-and-boundary-vote grammar."""
    return self_check(grid)


def _paint_components(grid, chooser: Callable[[list[int], dict[str, Any]], int]) -> list[list[int]]:
    result = [list(row) for row in grid]
    analysis = _analysis(grid)
    for facts in analysis.get("components", []):
        votes = []
        for color, count in enumerate(facts["votes"], start=1):
            votes.extend([color] * count)
        color = chooser(votes, facts)
        if color:
            for row, col in facts["cells"]:
                result[row][col] = color
    return result


def _unique_presence_only(grid):
    return _paint_components(
        grid,
        lambda votes, _facts: next(iter(set(votes))) if len(set(votes)) == 1 else 0,
    )


def _global_plurality(grid):
    analysis = _analysis(grid)
    all_votes = []
    for facts in analysis.get("components", []):
        for color, count in enumerate(facts["votes"], start=1):
            all_votes.extend([color] * count)
    winner = _unique_plurality(all_votes)
    return _paint_components(grid, lambda _votes, _facts: winner)


def _tie_break_smallest(grid):
    return _paint_components(
        grid,
        lambda votes, _facts: _unique_plurality(votes) or (min(votes) if votes else 0),
    )


def _ignore_shared_markers(grid):
    analysis = _analysis(grid)
    shared = set(analysis.get("shared_markers", {}))
    result = [list(row) for row in grid]
    for facts in analysis.get("components", []):
        votes = [
            grid[row][col]
            for row, col in facts["boundary_positions"]
            if (row, col) not in shared
        ]
        winner = _unique_plurality(votes)
        if winner:
            for row, col in facts["cells"]:
                result[row][col] = winner
    return result


def _rectangles_only(grid):
    return _paint_components(
        grid,
        lambda votes, facts: _unique_plurality(votes) if facts["rectangle"] else 0,
    )


def _distinct_cardinal_marker_cells(grid):
    """Wrong rule: count each adjacent marker cell once per chamber."""
    result = [list(row) for row in grid]
    analysis = _analysis(grid)
    for facts in analysis.get("components", []):
        votes = [
            grid[row][col]
            for row, col in set(facts["boundary_positions"])
        ]
        winner = _unique_plurality(votes)
        if winner:
            for row, col in facts["cells"]:
                result[row][col] = winner
    return result


SEMANTIC_RIVALS = {
    "unique_presence_only": _unique_presence_only,
    "global_plurality": _global_plurality,
    "tie_break_smallest": _tie_break_smallest,
    "ignore_shared_markers": _ignore_shared_markers,
    "rectangles_only": _rectangles_only,
    "distinct_cardinal_marker_cells": _distinct_cardinal_marker_cells,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "distinct_cardinal_marker_cells": _distinct_cardinal_marker_cells,
}


def _witness_multi_color_plurality(grid) -> bool:
    analysis = _analysis(grid)
    return any(
        facts["winner"] and facts["distinct_vote_colors"] >= 2
        for facts in analysis.get("components", [])
    )


def _witness_local_not_global(grid) -> bool:
    return rule_mirror(grid) != _global_plurality(grid)


def _witness_tie_stays_zero(grid) -> bool:
    return rule_mirror(grid) != _tie_break_smallest(grid)


def _witness_shared_marker(grid) -> bool:
    analysis = _analysis(grid)
    return bool(analysis.get("shared_markers")) and rule_mirror(grid) != _ignore_shared_markers(grid)


def _witness_nonrectangular(grid) -> bool:
    analysis = _analysis(grid)
    return any(not facts["rectangle"] for facts in analysis.get("components", [])) and rule_mirror(grid) != _rectangles_only(grid)


def _witness_boundary_incidence_multiplicity(grid) -> bool:
    analysis = _analysis(grid)
    has_repeated_marker_incidence = any(
        len(facts["boundary_positions"]) > len(set(facts["boundary_positions"]))
        for facts in analysis.get("components", [])
    )
    return has_repeated_marker_incidence and rule_mirror(grid) != _distinct_cardinal_marker_cells(grid)


SEMANTIC_WITNESSES = {
    "multi_color_plurality": _witness_multi_color_plurality,
    "local_votes_not_global": _witness_local_not_global,
    "tie_stays_zero": _witness_tie_stays_zero,
    "shared_marker_counted_per_chamber": _witness_shared_marker,
    "nonrectangular_chamber": _witness_nonrectangular,
    "boundary_incidence_multiplicity": _witness_boundary_incidence_multiplicity,
}
WITNESS_RIVALS = {
    "multi_color_plurality": ["unique_presence_only"],
    "local_votes_not_global": ["global_plurality"],
    "tie_stays_zero": ["tie_break_smallest"],
    "shared_marker_counted_per_chamber": ["ignore_shared_markers"],
    "nonrectangular_chamber": ["rectangles_only"],
    "boundary_incidence_multiplicity": ["distinct_cardinal_marker_cells"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject a lesson when a named wrong rule fits demos but changes the query."""
    reasons: list[str] = []
    all_pairs = [("demo", index, pair) for index, pair in enumerate(demos)] + [("query", 0, query)]
    for kind, index, pair in all_pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{kind} {index}: pair must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.extend(f"{kind} {index}: {error}" for error in errors)
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{kind} {index}: output disagrees with the chamber plurality rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demos: {name}")
    return reasons


def _transforms(grid):
    source = [list(row) for row in grid]
    variants = []
    current = source
    for _ in range(4):
        variants.append(current)
        variants.append([row[::-1] for row in current])
        current = [list(row) for row in zip(*current[::-1])]
    unique = {}
    for variant in variants:
        unique[tuple(map(tuple, variant))] = variant
    return list(unique.values())


def _recolor_markers(grid, palette):
    mapping = {color: palette[color - 1] for color in range(1, 5)}
    return [[mapping.get(value, value) for value in row] for row in grid]


_PUBLIC_VARIANTS: dict[tuple[tuple[int, ...], ...], str] = {}
_PUBLIC_VARIANT_GRIDS: dict[str, list[list[list[int]]]] = {profile: [] for profile in PUBLIC_PROFILES}
for _profile, _grid in _PUBLIC_INPUTS.items():
    for _variant in _transforms(_grid):
        for _palette in permutations((1, 2, 3, 4)):
            _recolored = _recolor_markers(_variant, _palette)
            _key = tuple(map(tuple, _recolored))
            _prior = _PUBLIC_VARIANTS.setdefault(_key, _profile)
            if _prior != _profile:
                raise AssertionError("canonical profile variants collide")
            if len(_recolored) == len(_grid) and len(_recolored[0]) == len(_grid[0]):
                _PUBLIC_VARIANT_GRIDS[_profile].append(_recolored)


def _build_full_contrast_base() -> list[list[int]]:
    """One compact scene that separates every declared partial rival."""
    # public_4 already separates unique-presence, global-plurality, tie-break,
    # and ignore-shared-marker rules.  The appended panel handles the two
    # remaining shape/incidence shortcuts without inflating every lesson.
    result = [row[:] for row in _PUBLIC_INPUTS["public_4"]]

    # The central color-1 cell contributes four cardinal incidences to one
    # chamber.  The two color-2 cells contribute one incidence each.  The
    # intended rule therefore selects 1 (4 vs 2), while the canonical-fitting
    # shortcut that deduplicates marker cells selects 2 (1 distinct vs 2).
    incidence_panel = [
        [int(value) for value in row]
        for row in (
            "52555",
            "50005",
            "50105",
            "50005",
            "55525",
        )
    ]
    result.append([5] * 14)
    result.extend([[5] * 4 + row + [5] * 5 for row in incidence_panel])
    return result


_FULL_CONTRAST_BASE = _build_full_contrast_base()
_FULL_CONTRAST_VARIANT_GRIDS: list[list[list[int]]] = []
_SCENE_VARIANTS = dict(_PUBLIC_VARIANTS)
for _variant in _transforms(_FULL_CONTRAST_BASE):
    for _palette in permutations((1, 2, 3, 4)):
        _recolored = _recolor_markers(_variant, _palette)
        _key = tuple(map(tuple, _recolored))
        _prior = _SCENE_VARIANTS.setdefault(_key, FULL_CONTRAST_PROFILE)
        if _prior != FULL_CONTRAST_PROFILE:
            raise AssertionError("full-contrast variants collide with another profile")
        _FULL_CONTRAST_VARIANT_GRIDS.append(_recolored)


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if not analysis["errors"] else None


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    _validate_call(seed, sample_index, difficulty, {})
    if sample_index % 2 == 0:
        return FULL_CONTRAST_PROFILE
    offset = {None: 0, "easy": 0, "medium": 3, "hard": 6}[difficulty]
    rotating_index = sample_index // 2
    return ROTATING_PROFILES[(rotating_index + offset) % len(ROTATING_PROFILES)]


def _public_scene(profile: str, rng) -> list[list[int]]:
    variants = _PUBLIC_VARIANT_GRIDS[profile]
    return [row[:] for row in rng.choice(variants)]


def _full_contrast_scene(rng) -> list[list[int]]:
    return [row[:] for row in rng.choice(_FULL_CONTRAST_VARIANT_GRIDS)]


def _band_sizes(difficulty: Any, rng):
    if difficulty == "easy":
        row_heights, col_widths = [3, 4], [5, 5]
    elif difficulty == "hard":
        row_heights, col_widths = [4, 5], [6, 6]
    else:
        row_heights, col_widths = [4, 4], [5, 6]
    rng.shuffle(row_heights)
    rng.shuffle(col_widths)
    return tuple(row_heights), tuple(col_widths)


def _room_outer_segment(room_index, wall_rows, wall_cols):
    row_index, col_index = divmod(room_index, 2)
    row = wall_rows[0] if row_index == 0 else wall_rows[2]
    return [(row, col) for col in range(wall_cols[col_index] + 1, wall_cols[col_index + 1])]


def _put_votes(grid, cells, votes, rng):
    if len(votes) > len(cells):
        raise ValueError("vote set does not fit boundary segment")
    chosen = rng.sample(cells, len(votes))
    values = list(votes)
    rng.shuffle(values)
    for (row, col), value in zip(chosen, values):
        grid[row][col] = value


def _general_scene(profile: str, difficulty: Any, rng) -> list[list[int]]:
    row_heights, col_widths = _band_sizes(difficulty, rng)
    height = sum(row_heights) + 3
    width = sum(col_widths) + 3
    wall_rows = (0, row_heights[0] + 1, height - 1)
    wall_cols = (0, col_widths[0] + 1, width - 1)
    grid = [[0] * width for _ in range(height)]
    for row in wall_rows:
        for col in range(width):
            grid[row][col] = 5
    for col in wall_cols:
        for row in range(height):
            grid[row][col] = 5

    colors = list(range(1, 5))
    rng.shuffle(colors)
    rooms = list(range(4))
    rng.shuffle(rooms)
    vote_sets: dict[int, tuple[int, ...]] = {}
    if profile == "all_colors":
        for room, winner in zip(rooms, colors):
            loser = colors[(colors.index(winner) + 1) % 4]
            vote_sets[room] = (winner, winner, winner, loser)
    elif profile == "one_tie":
        vote_sets[rooms[0]] = (colors[3], colors[3], colors[0], colors[0])
        for room, winner in zip(rooms[1:], colors[:3]):
            vote_sets[room] = (winner, winner, winner, colors[3])
    elif profile == "two_ties":
        vote_sets[rooms[0]] = (colors[2], colors[2], colors[0], colors[0])
        vote_sets[rooms[1]] = (colors[3], colors[3], colors[1], colors[1])
        vote_sets[rooms[2]] = (colors[0], colors[0], colors[0], colors[2])
        vote_sets[rooms[3]] = (colors[1], colors[1], colors[1], colors[3])
    elif profile == "shared_focus":
        winner = colors[0]
        for index, room in enumerate(rooms):
            vote_sets[room] = (winner, winner, colors[1 + index % 3])
    else:
        raise ValueError(f"unknown generalized profile: {profile!r}")

    for room in range(4):
        _put_votes(grid, _room_outer_segment(room, wall_rows, wall_cols), vote_sets[room], rng)

    if profile == "shared_focus":
        internal_segments = (
            [(wall_rows[1], col) for col in range(wall_cols[0] + 1, wall_cols[1])],
            [(wall_rows[1], col) for col in range(wall_cols[1] + 1, wall_cols[2])],
            [(row, wall_cols[1]) for row in range(wall_rows[0] + 1, wall_rows[1])],
            [(row, wall_cols[1]) for row in range(wall_rows[1] + 1, wall_rows[2])],
        )
        for segment in internal_segments:
            row, col = rng.choice(segment)
            grid[row][col] = colors[0]

    same_shape = [
        variant for variant in _transforms(grid)
        if len(variant) == height and len(variant[0]) == width
    ]
    grid = rng.choice(same_shape)
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(
            f"constructed invalid plurality lesson {profile!r}: {analysis['errors']!r}; "
            f"observed={analysis['scene_profile']!r}"
        )
    return grid


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    rng = ctx.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        grid = _public_scene(profile, rng)
    elif profile == FULL_CONTRAST_PROFILE:
        grid = _full_contrast_scene(rng)
    else:
        grid = _general_scene(profile, difficulty, rng)
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid plurality lesson: " + "; ".join(errors))
    return grid
