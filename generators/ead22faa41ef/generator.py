"""Generator for ARC training task d90796e8 / ead22faa41ef.

Every isolated orthogonally adjacent 3/2 pair is local: the 3 becomes 8 and
the 2 becomes 0.  Unpaired 3s, unpaired 2s, and gray 5 distractors survive.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ead22faa41ef"
VERSION = "3.1.0"
TASK_ID = "ead22faa41ef"
RULE_HASH = "6615d26334ba"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("preserved_lones", "free")

SUMMARY = (
    "Construct isolated orthogonally adjacent green-3/red-2 pairs in all "
    "four relative directions. The rule changes paired 3s to cyan 8 and "
    "paired 2s to background 0 while preserving deliberately unpaired 3s, "
    "unpaired 2s, and gray 5 distractors. A controlled default prior covers "
    "all four complete public local-adjacency profiles. Alternating default "
    "lesson slots contain preserved 3 and 2 witnesses that reject a global "
    "color-replacement shortcut."
)

INVARIANTS = [
    "the input is a rectangular 3..14 by 3..14 grid",
    "the input palette is a subset of 0, 2, 3, and 5",
    "at least one orthogonally adjacent 3/2 pair appears",
    "every paired 3 and paired 2 has exactly one opposite-color neighbor",
    "unpaired 3s, unpaired 2s, and gray 5 distractors remain unchanged",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_DIRECTION_DELTAS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}
_DIRECTION_MODES = ("up", "down", "left", "right", "mixed")
_VALID_H = (3, 14)
_VALID_W = (3, 14)
_PROFILE_PRIOR = 0.10
_BAND_BOUNDS = {
    "easy": ((3, 7), (3, 7)),
    "medium": ((6, 10), (6, 10)),
    "hard": ((9, 14), (9, 14)),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 3..14",
        "valid": "3..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 3..14",
        "valid": "3..14",
    },
    "pair_direction": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(_DIRECTION_MODES),
    },
}


def _profile(
    height,
    width,
    directions,
    lone3,
    lone2,
    fives,
    pair_edge,
    pair_corner,
    lone_edge,
    lone_corner,
    five_edge,
    five_corner,
):
    direction_counts = Counter(directions)
    n_pairs = len(directions)
    return {
        "height": height,
        "width": width,
        "directions": tuple(directions),
        "lone3": lone3,
        "lone2": lone2,
        "fives": fives,
        "pair_edge": pair_edge,
        "pair_corner": pair_corner,
        "lone_edge": lone_edge,
        "lone_corner": lone_corner,
        "five_edge": five_edge,
        "five_corner": five_corner,
        "signature": (
            height,
            width,
            n_pairs + lone3,
            n_pairs + lone2,
            fives,
            n_pairs,
            n_pairs,
            lone3,
            lone2,
            direction_counts["up"],
            direction_counts["down"],
            direction_counts["left"],
            direction_counts["right"],
            pair_edge,
            pair_corner,
            lone_edge,
            lone_corner,
            five_edge,
            five_corner,
        ),
    }


_PROFILE_SPECS = (
    _profile(
        7, 6, ("right", "down"), 1, 1, 2,
        0, 0, 1, 0, 2, 1,
    ),
    _profile(
        3, 3, ("right",), 0, 0, 1,
        2, 1, 0, 0, 1, 0,
    ),
    _profile(
        7, 7, ("left", "right", "up"), 2, 1, 2,
        1, 0, 3, 0, 2, 0,
    ),
    _profile(
        7, 9, ("right", "up", "down"), 1, 3, 5,
        1, 0, 3, 0, 4, 2,
    ),
)
_CANONICAL_PROFILE_SIGNATURES = frozenset(
    spec["signature"] for spec in _PROFILE_SPECS
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    direction = overrides.get("pair_direction")
    if direction is not None:
        if not isinstance(direction, str):
            raise ValueError("pair_direction must be a string")
        if direction not in _DIRECTION_MODES:
            raise ValueError(
                "pair_direction must be up, down, left, right, or mixed"
            )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _neighbors(row, col, height, width):
    for name, (dr, dc) in _DIRECTION_DELTAS.items():
        rr = row + dr
        cc = col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield name, rr, cc


def _edge(cell, height, width):
    row, col = cell
    return row in (0, height - 1) or col in (0, width - 1)


def _corner(cell, height, width):
    row, col = cell
    return row in (0, height - 1) and col in (0, width - 1)


def _scene_features(grid):
    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    threes = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    }
    twos = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    fives = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    }
    paired3 = set()
    paired2 = set()
    direction_counts = Counter()
    degrees3 = Counter()
    degrees2 = Counter()
    for row, col in threes:
        for name, rr, cc in _neighbors(row, col, height, width):
            if (rr, cc) not in twos:
                continue
            paired3.add((row, col))
            paired2.add((rr, cc))
            direction_counts[name] += 1
            degrees3[(row, col)] += 1
            degrees2[(rr, cc)] += 1

    pair_cells = paired3 | paired2
    lone_cells = (threes - paired3) | (twos - paired2)
    signature = (
        height,
        width,
        counts[3],
        counts[2],
        counts[5],
        len(paired3),
        len(paired2),
        counts[3] - len(paired3),
        counts[2] - len(paired2),
        direction_counts["up"],
        direction_counts["down"],
        direction_counts["left"],
        direction_counts["right"],
        sum(_edge(cell, height, width) for cell in pair_cells),
        sum(_corner(cell, height, width) for cell in pair_cells),
        sum(_edge(cell, height, width) for cell in lone_cells),
        sum(_corner(cell, height, width) for cell in lone_cells),
        sum(_edge(cell, height, width) for cell in fives),
        sum(_corner(cell, height, width) for cell in fives),
    )
    return {
        "signature": signature,
        "counts": counts,
        "paired3": paired3,
        "paired2": paired2,
        "directions": direction_counts,
        "degrees3": degrees3,
        "degrees2": degrees2,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    height = len(coerced)
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append("grid height must be in 3..14")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append("grid width must be in 3..14")
    if any(
        type(value) is not int or value not in (0, 2, 3, 5)
        for row in coerced
        for value in row
    ):
        errors.append("input colors must be integer 0, 2, 3, or 5")
        return errors

    features = _scene_features(coerced)
    if not features["paired3"]:
        errors.append("at least one orthogonally adjacent 3/2 pair is required")
    if (
        any(degree != 1 for degree in features["degrees3"].values())
        or any(degree != 1 for degree in features["degrees2"].values())
    ):
        errors.append(
            "paired cells must form isolated 3/2 matches, not adjacency clusters"
        )
    counts = features["counts"]
    if len(features["paired3"]) > 5:
        errors.append("at most five isolated pairs are supported")
    if counts[3] - len(features["paired3"]) > 4:
        errors.append("at most four unpaired 3 cells are supported")
    if counts[2] - len(features["paired2"]) > 4:
        errors.append("at most four unpaired 2 cells are supported")
    if counts[5] > 5:
        errors.append("at most five gray distractors are supported")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    coerced = _coerce_grid(grid)
    features = _scene_features(coerced)
    present = [
        name
        for name in _DIRECTION_DELTAS
        if features["directions"][name]
    ]
    direction = present[0] if len(present) == 1 else "mixed"
    return {
        "grid_h": len(coerced),
        "grid_w": len(coerced[0]),
        "pair_direction": direction,
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    source = _coerce_grid(grid)
    height = len(source)
    width = len(source[0])
    output = [row[:] for row in source]
    for row in range(height):
        for col in range(width):
            value = source[row][col]
            neighbors = [
                source[rr][cc]
                for _name, rr, cc in _neighbors(
                    row, col, height, width
                )
            ]
            if value == 3 and 2 in neighbors:
                output[row][col] = 8
            elif value == 2 and 3 in neighbors:
                output[row][col] = 0
    return output


def _global_replacement_rival(grid):
    """Wrong shortcut: transform every 3 and 2 without testing adjacency."""
    source = _coerce_grid(grid)
    return [
        [8 if value == 3 else 0 if value == 2 else value for value in row]
        for row in source
    ]


LESSON_COMPETITORS = {
    "global_replacement": _global_replacement_rival,
}


def lesson_identifiable(demos, query):
    """Reject lessons whose demonstrations admit the global replacement rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is not an input/output pair"]
        errors = self_check(pair["input"])
        if errors:
            return [f"demo {index} is outside the task manifold: {errors[0]}"]
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the local-pair rule")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input grid")
        return reasons
    errors = self_check(query["input"])
    if errors:
        reasons.append(f"query is outside the task manifold: {errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query output disagrees with the local-pair rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        ) and competitor(query["input"]) != query_truth:
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a different query"
            )
    return reasons


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    signature = _scene_features(_coerce_grid(grid))["signature"]
    return signature if signature in _CANONICAL_PROFILE_SIGNATURES else None


def is_canonical_profile(grid):
    return (
        canonical_profile_signature(grid)
        in _CANONICAL_PROFILE_SIGNATURES
    )


def _candidate_pairs(height, width, direction):
    dr, dc = _DIRECTION_DELTAS[direction]
    candidates = []
    for row in range(height):
        for col in range(width):
            rr = row + dr
            cc = col + dc
            if 0 <= rr < height and 0 <= cc < width:
                candidates.append(((row, col), (rr, cc), direction))
    return candidates


def _matching_adjacency(threes, twos):
    for row, col in threes:
        degree = sum(
            (row + dr, col + dc) in twos
            for dr, dc in _DIRECTION_DELTAS.values()
        )
        if degree != 1:
            return False
    for row, col in twos:
        degree = sum(
            (row + dr, col + dc) in threes
            for dr, dc in _DIRECTION_DELTAS.values()
        )
        if degree != 1:
            return False
    return True


def _place_pairs(
    height,
    width,
    directions,
    rng,
    *,
    target_edge=None,
    target_corner=None,
    require_edge=False,
    require_corner=False,
):
    directions = list(directions)
    rng.shuffle(directions)
    by_direction = {}
    for direction in set(directions):
        candidates = _candidate_pairs(height, width, direction)
        rng.shuffle(candidates)
        by_direction[direction] = candidates

    nodes = 0

    def visit(index, threes, twos, edge_count, corner_count):
        nonlocal nodes
        nodes += 1
        if nodes > 100_000:
            return None
        if index == len(directions):
            if target_edge is not None and edge_count != target_edge:
                return None
            if target_corner is not None and corner_count != target_corner:
                return None
            if require_edge and edge_count == 0:
                return None
            if require_corner and corner_count == 0:
                return None
            return threes, twos

        remaining = len(directions) - index - 1
        candidates = list(by_direction[directions[index]])
        if require_corner and corner_count == 0:
            candidates.sort(
                key=lambda item: not any(
                    _corner(cell, height, width) for cell in item[:2]
                )
            )
        elif require_edge and edge_count == 0:
            candidates.sort(
                key=lambda item: not any(
                    _edge(cell, height, width) for cell in item[:2]
                )
            )

        for three, two, _direction in candidates:
            if three in threes or three in twos:
                continue
            if two in threes or two in twos:
                continue
            next_threes = threes | {three}
            next_twos = twos | {two}
            if not _matching_adjacency(next_threes, next_twos):
                continue
            add_edge = int(_edge(three, height, width))
            add_edge += int(_edge(two, height, width))
            add_corner = int(_corner(three, height, width))
            add_corner += int(_corner(two, height, width))
            next_edge = edge_count + add_edge
            next_corner = corner_count + add_corner
            if target_edge is not None:
                if next_edge > target_edge:
                    continue
                if next_edge + 2 * remaining < target_edge:
                    continue
            if target_corner is not None:
                if next_corner > target_corner:
                    continue
                if next_corner + 2 * remaining < target_corner:
                    continue
            result = visit(
                index + 1,
                next_threes,
                next_twos,
                next_edge,
                next_corner,
            )
            if result is not None:
                return result
        return None

    return visit(0, set(), set(), 0, 0)


def _place_lones(
    height,
    width,
    threes,
    twos,
    n_lone3,
    n_lone2,
    rng,
    *,
    target_edge=None,
    target_corner=None,
):
    values = [3] * n_lone3 + [2] * n_lone2
    rng.shuffle(values)
    all_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
    ]
    rng.shuffle(all_cells)
    occupied = threes | twos
    nodes = 0

    def visit(index, lone3, lone2, edge_count, corner_count):
        nonlocal nodes
        nodes += 1
        if nodes > 100_000:
            return None
        if index == len(values):
            if target_edge is not None and edge_count != target_edge:
                return None
            if target_corner is not None and corner_count != target_corner:
                return None
            return lone3, lone2

        remaining = len(values) - index - 1
        value = values[index]
        candidates = list(all_cells)
        if target_corner is not None and corner_count < target_corner:
            candidates.sort(
                key=lambda cell: not _corner(cell, height, width)
            )
        elif target_edge is not None and edge_count < target_edge:
            candidates.sort(key=lambda cell: not _edge(cell, height, width))

        for cell in candidates:
            if cell in occupied or cell in lone3 or cell in lone2:
                continue
            row, col = cell
            opposite = twos | lone2 if value == 3 else threes | lone3
            if any(
                (row + dr, col + dc) in opposite
                for dr, dc in _DIRECTION_DELTAS.values()
            ):
                continue
            next_edge = edge_count + int(_edge(cell, height, width))
            next_corner = corner_count + int(
                _corner(cell, height, width)
            )
            if target_edge is not None:
                if next_edge > target_edge:
                    continue
                if next_edge + remaining < target_edge:
                    continue
            if target_corner is not None:
                if next_corner > target_corner:
                    continue
                if next_corner + remaining < target_corner:
                    continue
            next_lone3 = lone3 | ({cell} if value == 3 else set())
            next_lone2 = lone2 | ({cell} if value == 2 else set())
            result = visit(
                index + 1,
                next_lone3,
                next_lone2,
                next_edge,
                next_corner,
            )
            if result is not None:
                return result
        return None

    return visit(0, set(), set(), 0, 0)


def _place_fives(
    height,
    width,
    occupied,
    count,
    rng,
    *,
    target_edge=None,
    target_corner=None,
):
    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in occupied
    ]
    rng.shuffle(available)
    if target_edge is None or target_corner is None:
        return set(available[:count]) if len(available) >= count else None

    corners = [
        cell for cell in available if _corner(cell, height, width)
    ]
    edges = [
        cell
        for cell in available
        if _edge(cell, height, width)
        and not _corner(cell, height, width)
    ]
    interiors = [
        cell for cell in available if not _edge(cell, height, width)
    ]
    need_edge_only = target_edge - target_corner
    need_interior = count - target_edge
    if (
        target_corner < 0
        or need_edge_only < 0
        or need_interior < 0
        or len(corners) < target_corner
        or len(edges) < need_edge_only
        or len(interiors) < need_interior
    ):
        return None
    return set(
        corners[:target_corner]
        + edges[:need_edge_only]
        + interiors[:need_interior]
    )


def _paint_scene(height, width, threes, twos, lone3, lone2, fives):
    grid = full_grid(height, width, 0)
    for row, col in threes | lone3:
        grid[row][col] = 3
    for row, col in twos | lone2:
        grid[row][col] = 2
    for row, col in fives:
        grid[row][col] = 5
    return grid


def _construct_scene(
    height,
    width,
    directions,
    n_lone3,
    n_lone2,
    n_fives,
    rng,
    *,
    pair_edge=None,
    pair_corner=None,
    lone_edge=None,
    lone_corner=None,
    five_edge=None,
    five_corner=None,
    require_pair_edge=False,
    require_pair_corner=False,
):
    for _ in range(80):
        pairs = _place_pairs(
            height,
            width,
            directions,
            rng,
            target_edge=pair_edge,
            target_corner=pair_corner,
            require_edge=require_pair_edge,
            require_corner=require_pair_corner,
        )
        if pairs is None:
            continue
        threes, twos = pairs
        lones = _place_lones(
            height,
            width,
            threes,
            twos,
            n_lone3,
            n_lone2,
            rng,
            target_edge=lone_edge,
            target_corner=lone_corner,
        )
        if lones is None:
            continue
        lone3, lone2 = lones
        fives = _place_fives(
            height,
            width,
            threes | twos | lone3 | lone2,
            n_fives,
            rng,
            target_edge=five_edge,
            target_corner=five_corner,
        )
        if fives is None:
            continue
        grid = _paint_scene(
            height, width, threes, twos, lone3, lone2, fives
        )
        if not self_check(grid):
            return grid
    return None


def _draw_profile(spec, rng):
    grid = _construct_scene(
        spec["height"],
        spec["width"],
        spec["directions"],
        spec["lone3"],
        spec["lone2"],
        spec["fives"],
        rng,
        pair_edge=spec["pair_edge"],
        pair_corner=spec["pair_corner"],
        lone_edge=spec["lone_edge"],
        lone_corner=spec["lone_corner"],
        five_edge=spec["five_edge"],
        five_corner=spec["five_corner"],
    )
    if grid is None:
        raise AssertionError("could not construct exact public profile")
    if canonical_profile_signature(grid) != spec["signature"]:
        raise AssertionError("constructed profile signature drifted")
    return grid


def _direction_list(mode, n_pairs, rng):
    if mode != "mixed":
        return [mode] * n_pairs
    first, second = rng.sample(tuple(_DIRECTION_DELTAS), 2)
    directions = [first, second]
    directions.extend(
        rng.choice(tuple(_DIRECTION_DELTAS))
        for _ in range(n_pairs - 2)
    )
    rng.shuffle(directions)
    return directions


def _draw_general(
    height,
    width,
    mode,
    band,
    rng,
    *,
    require_lone_colors=False,
):
    ranges = {
        "easy": ((1, 2), (0, 2), (0, 2), (0, 2)),
        "medium": ((2, 4), (0, 3), (0, 3), (1, 4)),
        "hard": ((3, 5), (1, 4), (1, 4), (2, 5)),
    }[band]
    area = height * width
    for _ in range(300):
        pair_lo, pair_hi = ranges[0]
        if mode == "mixed":
            pair_lo = max(2, pair_lo)
        pair_hi = min(pair_hi, max(pair_lo, area // 4))
        n_pairs = rng.randint(pair_lo, pair_hi)
        directions = _direction_list(mode, n_pairs, rng)
        remaining = max(0, area - 2 * n_pairs)
        n_lone3 = min(rng.randint(*ranges[1]), remaining)
        if require_lone_colors:
            n_lone3 = max(1, n_lone3)
            if n_lone3 > remaining:
                continue
        remaining -= n_lone3
        n_lone2 = min(rng.randint(*ranges[2]), remaining)
        if require_lone_colors:
            n_lone2 = max(1, n_lone2)
            if n_lone2 > remaining:
                continue
        remaining -= n_lone2
        n_fives = min(rng.randint(*ranges[3]), remaining)
        require_corner = rng.random() < 0.18
        require_edge = require_corner or rng.random() < 0.55
        grid = _construct_scene(
            height,
            width,
            directions,
            n_lone3,
            n_lone2,
            n_fives,
            rng,
            require_pair_edge=require_edge,
            require_pair_corner=require_corner,
        )
        if grid is not None:
            return grid
    fallback_directions = (
        ["right", "down"] if mode == "mixed" else [mode]
    )
    grid = _construct_scene(
        height,
        width,
        fallback_directions,
        1 if require_lone_colors else 0,
        1 if require_lone_colors else 0,
        0,
        rng,
    )
    if grid is None:
        raise AssertionError(
            f"could not construct lawful {mode} scene in {height}x{width}"
        )
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternate witness-bearing and unrestricted slots for lesson windows."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )
    require_lone_colors = (
        not has_override
        and schedule_profile(seed, sample_index, difficulty) == "preserved_lones"
    )
    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            eligible_profiles = tuple(
                index
                for index, spec in enumerate(_PROFILE_SPECS)
                if not require_lone_colors
                or (spec["lone3"] >= 1 and spec["lone2"] >= 1)
            )
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                eligible_profiles,
            )

    if profile_index is not None:
        spec = _PROFILE_SPECS[profile_index]
        height = ctx.draw_int(
            "grid_h", spec["height"], spec["height"]
        )
        width = ctx.draw_int(
            "grid_w", spec["width"], spec["width"]
        )
        mode = (
            spec["directions"][0]
            if len(set(spec["directions"])) == 1
            else "mixed"
        )
        ctx.draw_choice("pair_direction", (mode,))
        grid = _draw_profile(spec, ctx.draw_rng("layout"))
    else:
        height_bounds, width_bounds = _BAND_BOUNDS[band]
        if overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", *_VALID_H)
        else:
            height = ctx.draw_int("grid_h", *height_bounds)
        if overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", *_VALID_W)
        else:
            width = ctx.draw_int("grid_w", *width_bounds)
        mode = ctx.draw_choice("pair_direction", _DIRECTION_MODES)
        grid = _draw_general(
            height,
            width,
            mode,
            band,
            ctx.draw_rng("layout"),
            require_lone_colors=require_lone_colors,
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    if observe_overrides(grid) != {
        "grid_h": height,
        "grid_w": width,
        "pair_direction": mode,
    }:
        raise AssertionError("generated scene disagrees with drawn controls")
    return grid
