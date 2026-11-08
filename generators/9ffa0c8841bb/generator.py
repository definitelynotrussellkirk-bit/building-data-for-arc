"""Semantic generator for ARC task 9ffa0c8841bb (bank source H91).

Each 4-connected zero chamber is filled with the unique plurality color among
the color-1-through-4 cells on its cardinal boundary.  A tied or empty vote
leaves the chamber zero.  Every other cell is preserved.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9ffa0c8841bb"
TASK_ID = "9ffa0c8841bb"
VERSION = "3.0.0"
RULE_HASH = "e1d60c5dd3e1"
SUMMARY = "Fill each zero chamber with its unique plurality boundary-marker color; ties stay zero."
INVARIANTS = [
    "calibrated inputs contain a complete two-by-two chamber lattice",
    "colors one through four are voting markers and color five is a neutral wall",
    "votes are counted independently on the cardinal boundary of each zero chamber",
    "a unique plurality fills the complete chamber and a tied plurality leaves it zero",
    "wall and marker cells are preserved",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = ("all_colors", "one_tie", "two_ties", "shared_focus")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five complete official vote families plus four controlled plurality contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "5555355515555", "5000005000001", "5000005000001",
        "2000005000004", "4000005000005", "5000004000005",
        "4000005000005", "5553535525155", "5000005000001",
        "3000001000005", "5000005000005", "5000005000001",
        "5000005000005", "5000005000002", "5555255555545",
    ),
    "public_2": (
        "5555225355313555", "5000000050000005", "5000000010000005",
        "5000000050000005", "5000000020000005", "5000000050000005",
        "5000000050000005", "5552554553555135", "4000000050000005",
        "2000000040000002", "5000000010000005", "5000000050000005",
        "5000000050000005", "5355555555155555",
    ),
    "public_3": (
        "55555355555515", "50000004000001", "50000002000005",
        "50000005000005", "50000005000005", "50000005000004",
        "50000005000005", "55253535415355", "50000005000005",
        "50000004000005", "50000005000004", "50000004000005",
        "50000002000005", "20000001000005", "55555555525515",
    ),
    "public_4": (
        "55555515555555", "50000005000005", "50000005000005",
        "40000003000001", "20000002000005", "50000005000005",
        "55514455522525", "50000005000001", "50000002000005",
        "50000004000004", "50000002000005", "30000004000005",
        "55555455555555",
    ),
    "public_5": (
        "55554555555155", "20000005000005", "50000005000005",
        "50000005000005", "50000002000005", "50000002000003",
        "50000002000005", "55555515525325", "50000004000005",
        "40000005000005", "50000001000005", "50000003000005",
        "10000001000005", "55525555155355",
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


def _zero_components(grid):
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


def _boundary_votes(grid, component):
    height, width = len(grid), len(grid[0])
    votes = []
    for row, col in component:
        for other_row, other_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= other_row < height and 0 <= other_col < width:
                value = grid[other_row][other_col]
                if 1 <= value <= 4:
                    votes.append(value)
    return votes


def _unique_plurality(votes):
    ranked = Counter(votes).most_common()
    if not ranked:
        return 0
    if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
        return ranked[0][0]
    return 0


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket program."""
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


def _lattice_facts(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    wall_rows = [row for row in range(height) if all(grid[row][col] != 0 for col in range(width))]
    wall_cols = [col for col in range(width) if all(grid[row][col] != 0 for row in range(height))]
    if len(wall_rows) != 3 or wall_rows[0] != 0 or wall_rows[-1] != height - 1:
        errors.append("calibrated input must have exactly three complete horizontal wall lines")
    if len(wall_cols) != 3 or wall_cols[0] != 0 or wall_cols[-1] != width - 1:
        errors.append("calibrated input must have exactly three complete vertical wall lines")
    if errors:
        return {"errors": errors}
    if any(value not in range(6) for row in grid for value in row):
        errors.append("calibrated palette must be colors zero through five")
    if set(value for row in grid for value in row) != set(range(6)):
        errors.append("calibrated input must witness every color zero through five")
    if any(
        grid[row][col] != 0 and row not in wall_rows and col not in wall_cols
        for row in range(height) for col in range(width)
    ):
        errors.append("markers and neutral walls must remain on complete lattice lines")
    if any(grid[row][col] != 5 for row in wall_rows for col in wall_cols):
        errors.append("all nine wall-line intersections must remain neutral color five")
    row_heights = (wall_rows[1] - 1, wall_rows[2] - wall_rows[1] - 1)
    col_widths = (wall_cols[1] - 1, wall_cols[2] - wall_cols[1] - 1)
    if any(not 4 <= size <= 9 for size in row_heights + col_widths):
        errors.append("each calibrated chamber side must be four through nine cells")
    components = _zero_components(grid)
    if len(components) != 4:
        errors.append(f"expected four separate zero chambers, got {len(components)}")
    chamber_facts = []
    for component in components:
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
        rectangle = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
        }
        if set(component) != rectangle:
            errors.append("every calibrated zero chamber must be a complete rectangle")
        votes = _boundary_votes(grid, component)
        if not 4 <= len(votes) <= 12:
            errors.append("each calibrated chamber must receive four through twelve votes")
        chamber_facts.append({
            "bbox": (row0, col0, row1, col1),
            "height": row1 - row0 + 1,
            "width": col1 - col0 + 1,
            "votes": tuple(Counter(votes)[color] for color in range(1, 5)),
            "winner": _unique_plurality(votes),
        })
    marker_count = sum(1 for row in grid for value in row if 1 <= value <= 4)
    if not 12 <= marker_count <= 32:
        errors.append("calibrated lattice must contain twelve through thirty-two markers")
    internal_markers = sum(
        1
        for row in range(height) for col in range(width)
        if 1 <= grid[row][col] <= 4
        and (row == wall_rows[1] or col == wall_cols[1])
    )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "wall_rows": tuple(wall_rows),
        "wall_cols": tuple(wall_cols),
        "row_heights": row_heights,
        "col_widths": col_widths,
        "chambers": sorted(chamber_facts, key=lambda fact: fact["bbox"]),
        "marker_count": marker_count,
        "internal_markers": internal_markers,
    }


def _raw_signature(facts):
    return (
        facts["height"],
        facts["width"],
        tuple(
            (fact["height"], fact["width"], fact["votes"])
            for fact in facts["chambers"]
        ),
    )


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
    return [
        [mapping.get(value, value) for value in row]
        for row in grid
    ]


_PUBLIC_SIGNATURES = {}
for _profile, _grid in _PUBLIC_INPUTS.items():
    for _variant in _transforms(_grid):
        for _palette in permutations((1, 2, 3, 4)):
            _facts = _lattice_facts(_recolor_markers(_variant, _palette))
            _signature = _raw_signature(_facts)
            _prior = _PUBLIC_SIGNATURES.setdefault(_signature, _profile)
            if _prior != _profile:
                raise AssertionError("official vote-family signatures collide")


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def _classify(grid):
    facts = _lattice_facts(grid)
    if facts["errors"]:
        return None, facts
    profile = _PUBLIC_SIGNATURES.get(_raw_signature(facts))
    if profile is not None:
        return profile, facts
    winners = [fact["winner"] for fact in facts["chambers"]]
    ties = winners.count(0)
    distinct = len(set(winners) - {0})
    if ties == 0 and distinct == 4:
        profile = "all_colors"
    elif ties == 1 and distinct == 3:
        profile = "one_tie"
    elif ties == 2 and distinct == 2:
        profile = "two_ties"
    elif ties == 0 and distinct == 1 and facts["internal_markers"] >= 4:
        profile = "shared_focus"
    return profile, facts


def _analysis(grid):
    profile, facts = _classify(grid)
    errors = list(facts["errors"])
    if not errors and profile is None:
        errors.append("unsupported calibrated plurality and tie signature")
    output = rule_mirror(grid) if not facts["errors"] else None
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": facts,
        "output": output,
    }


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _segments(facts):
    wall_rows = facts["wall_rows"]
    wall_cols = facts["wall_cols"]
    result = []
    for row in wall_rows:
        for index in range(2):
            result.append([(row, col) for col in range(wall_cols[index] + 1, wall_cols[index + 1])])
    for col in wall_cols:
        for index in range(2):
            result.append([(row, col) for row in range(wall_rows[index] + 1, wall_rows[index + 1])])
    return result


def _public_scene(profile, rng):
    grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    facts = _lattice_facts(grid)
    for segment in _segments(facts):
        values = [grid[row][col] for row, col in segment]
        rng.shuffle(values)
        for (row, col), value in zip(segment, values):
            grid[row][col] = value
    palette = list(range(1, 5))
    rng.shuffle(palette)
    grid = _recolor_markers(grid, palette)
    return rng.choice(_transforms(grid))


def _room_outer_segment(room_index, wall_rows, wall_cols):
    row_index, col_index = divmod(room_index, 2)
    row = wall_rows[0] if row_index == 0 else wall_rows[2]
    return [(row, col) for col in range(wall_cols[col_index] + 1, wall_cols[col_index + 1])]


def _put_votes(grid, cells, votes, rng):
    chosen = rng.sample(cells, len(votes))
    values = list(votes)
    rng.shuffle(values)
    for (row, col), value in zip(chosen, values):
        grid[row][col] = value


def _general_scene(profile, difficulty, rng):
    if difficulty == "easy":
        side_range = (5, 6)
    elif difficulty == "medium":
        side_range = (5, 7)
    elif difficulty == "hard":
        side_range = (6, 9)
    else:
        side_range = (5, 7)
    row_heights = (rng.randint(*side_range), rng.randint(*side_range))
    col_widths = (rng.randint(*side_range), rng.randint(*side_range))
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
    room_order = list(range(4))
    rng.shuffle(room_order)
    vote_sets = {}
    if profile == "all_colors":
        for room, winner in zip(room_order, colors):
            vote_sets[room] = (winner, winner, winner, colors[(colors.index(winner) + 1) % 4])
    elif profile == "one_tie":
        tie_room = room_order[0]
        winners = colors[:3]
        vote_sets[tie_room] = (colors[3], colors[3], colors[0], colors[0])
        for room, winner in zip(room_order[1:], winners):
            vote_sets[room] = (winner, winner, winner, colors[3])
    elif profile == "two_ties":
        vote_sets[room_order[0]] = (colors[2], colors[2], colors[0], colors[0])
        vote_sets[room_order[1]] = (colors[3], colors[3], colors[1], colors[1])
        vote_sets[room_order[2]] = (colors[0], colors[0], colors[0], colors[2])
        vote_sets[room_order[3]] = (colors[1], colors[1], colors[1], colors[3])
    elif profile == "shared_focus":
        winner = colors[0]
        for index, room in enumerate(room_order):
            vote_sets[room] = (winner, winner, colors[1 + index % 3])
    else:
        raise ValueError(f"unknown generalized profile: {profile!r}")
    for room in range(4):
        _put_votes(
            grid,
            _room_outer_segment(room, wall_rows, wall_cols),
            vote_sets[room],
            rng,
        )
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
    grid = rng.choice(_transforms(grid))
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(
            f"constructed invalid plurality lesson {profile!r}: {analysis['errors']!r}; "
            f"observed={analysis['scene_profile']!r}"
        )
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
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) * 3 + list(GENERAL_PROFILES) * 2)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("scene")
    grid = _public_scene(profile, rng) if profile in PUBLIC_PROFILES else _general_scene(profile, difficulty, rng)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid plurality lesson: " + "; ".join(errors))
    return grid
