"""Semantic generator for ARC task a0ff437161da.

On an 8 background, find the first non-8 cell in row-major order and fill the
axis-aligned rectangle from it to the nearest corner with its color. Manhattan
distance ties follow corner order UL, UR, LL, LR.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "a0ff437161da"
TASK_ID = GENERATOR_ID
VERSION = "4.2.0"
RULE_HASH = "c70fab479c5e"
SUMMARY = (
    "Fill the rectangle from the lone colored cell to its nearest corner, "
    "resolving ties in UL/UR/LL/LR order."
)
INVARIANTS = [
    "background is literal color 8",
    "calibrated scenes contain exactly one non-8 marker",
    "the marker is not itself at a corner",
    "the output rectangle includes both the marker and the selected nearest corner",
]
PUBLIC_PROFILES = (
    "public_1",
    "public_2",
    "public_3",
    "public_4",
    "public_5",
)
GENERAL_PROFILES = (
    "nearest_ul",
    "nearest_ur",
    "nearest_ll",
    "nearest_lr",
    "top_tie",
    "bottom_tie",
    "left_tie",
    "right_tie",
    "four_way_tie",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rotation-safe exact-public, unique-corner, and tie lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_SPECS = {
    "public_1": (6, 8, 3, 2, 4),
    "public_2": (6, 6, 2, 4, 9),
    "public_3": (10, 8, 4, 2, 6),
    "public_4": (4, 4, 0, 2, 6),
    "public_5": (10, 10, 7, 8, 4),
}


def _single(spec):
    h, w, r, c, color = spec
    grid = [[8] * w for _ in range(h)]
    grid[r][c] = color
    return grid


_PUBLIC_INPUTS = {name: _single(spec) for name, spec in _PUBLIC_SPECS.items()}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}

_CORNERS = ("ul", "ur", "ll", "lr")
_REVERSE_TIE_CORNERS = ("lr", "ll", "ur", "ul")
TIE_PROFILES = (
    "top_tie",
    "bottom_tie",
    "left_tie",
    "right_tie",
    "four_way_tie",
)

# A four-example lesson is formed from four consecutive default sample indices.
# Alternating a tie profile with a broad non-tie cycle means every cyclic
# four-example window contains exactly two direct witnesses to the canonical tie
# priority. Holding out any one example still leaves a witness in the demos.
_NON_TIE_SCHEDULE = (
    # Odd schedule slots with index 1 mod 4 are forced color 9. Public_2 is
    # the only exact public profile with that marker color. Odd slots with
    # index 3 mod 4 are non-9, allowing the other four public profiles.
    "public_2",
    "public_1",
    "nearest_ul",
    "public_3",
    "nearest_ur",
    "public_4",
    "nearest_ll",
    "public_5",
    "nearest_lr",
    "nearest_ul",
    "nearest_ul",
    "nearest_ur",
    "nearest_ur",
    "nearest_ll",
    "nearest_ll",
    "nearest_lr",
    "nearest_lr",
    "nearest_ul",
)

_TIE_SCHEDULE = tuple(
    TIE_PROFILES[index % len(TIE_PROFILES)]
    for index in range(len(_NON_TIE_SCHEDULE))
)
DEFAULT_PROFILE_SCHEDULE = tuple(
    profile
    for tie_profile, non_tie_profile in zip(
        _TIE_SCHEDULE, _NON_TIE_SCHEDULE, strict=True
    )
    for profile in (tie_profile, non_tie_profile)
)
DEFAULT_FORCE_NINE_SCHEDULE = tuple(
    index % 4 in (0, 1) for index in range(len(DEFAULT_PROFILE_SCHEDULE))
)


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _corner_coordinates(height, width):
    return {
        "ul": (0, 0),
        "ur": (0, width - 1),
        "ll": (height - 1, 0),
        "lr": (height - 1, width - 1),
    }


def _solve_with_corner_order(grid, corner_order):
    height = len(grid)
    width = len(grid[0])
    markers = [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c in range(width)
        if grid[r][c] != 8
    ]
    if not markers:
        raise ValueError("grid has no non-8 marker")

    r, c, color = markers[0]
    coordinates = _corner_coordinates(height, width)
    distances = tuple(
        abs(r - coordinates[name][0]) + abs(c - coordinates[name][1])
        for name in _CORNERS
    )
    chosen_name = min(
        corner_order,
        key=lambda name: (
            abs(r - coordinates[name][0]) + abs(c - coordinates[name][1]),
            corner_order.index(name),
        ),
    )
    rr, cc = coordinates[chosen_name]
    output = [list(row) for row in grid]
    for y in range(min(r, rr), max(r, rr) + 1):
        for x in range(min(c, cc), max(c, cc) + 1):
            output[y][x] = color
    return output, markers, (r, c), chosen_name, distances


def _solve(grid):
    return _solve_with_corner_order(grid, _CORNERS)


def _relation(r, c, height, width):
    distances = (
        r + c,
        r + width - 1 - c,
        height - 1 - r + c,
        height - 1 - r + width - 1 - c,
    )
    minimum = min(distances)
    nearest = tuple(index for index, value in enumerate(distances) if value == minimum)
    return {
        (0,): "nearest_ul",
        (1,): "nearest_ur",
        (2,): "nearest_ll",
        (3,): "nearest_lr",
        (0, 1): "top_tie",
        (2, 3): "bottom_tie",
        (0, 2): "left_tie",
        (1, 3): "right_tie",
        (0, 1, 2, 3): "four_way_tie",
    }.get(nearest)


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    height = len(grid)
    width = len(grid[0])
    markers = [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c in range(width)
        if grid[r][c] != 8
    ]
    if len(markers) != 1:
        errors.append("calibrated scene must contain exactly one non-8 marker")
    if not markers:
        return result

    r, c, color = markers[0]
    if color == 8:
        errors.append("marker color must differ from background 8")
    if (r, c) in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
        errors.append("marker must not lie at a corner")

    output, _, marker, corner, distances = _solve(grid)
    signature = tuple(map(tuple, grid))
    profile = _PUBLIC_SIGNATURES.get(signature) or _relation(r, c, height, width)
    if profile not in SCENE_PROFILES:
        errors.append("marker/corner relation does not match a declared profile")
    rr, cc = _corner_coordinates(height, width)[corner]
    result.update(
        {
            "marker": marker,
            "marker_color": color,
            "nearest_corner": corner,
            "corner_distances": distances,
            "rectangle_area": (abs(r - rr) + 1) * (abs(c - cc) + 1),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _solve(grid)[0]


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _odd(rng, lower, upper):
    choices = [value for value in range(lower, upper + 1) if value % 2]
    return rng.choice(choices)


def _position(rng, profile, height, width):
    middle_row = (height - 1) // 2
    middle_col = (width - 1) // 2
    if profile == "nearest_ul":
        return rng.randint(0, middle_row), rng.randint(0, middle_col)
    if profile == "nearest_ur":
        return rng.randint(0, middle_row), rng.randint(middle_col + 1, width - 1)
    if profile == "nearest_ll":
        return rng.randint(middle_row + 1, height - 1), rng.randint(0, middle_col)
    if profile == "nearest_lr":
        return (
            rng.randint(middle_row + 1, height - 1),
            rng.randint(middle_col + 1, width - 1),
        )
    if profile == "top_tie":
        return rng.randint(0, middle_row - 1), middle_col
    if profile == "bottom_tie":
        return rng.randint(middle_row + 1, height - 1), middle_col
    if profile == "left_tie":
        return middle_row, rng.randint(0, middle_col - 1)
    if profile == "right_tie":
        return middle_row, rng.randint(middle_col + 1, width - 1)
    return middle_row, middle_col


def _general(rng, profile, band, *, marker_color=None, allow_nine=True):
    lower, upper = {
        "easy": (4, 12),
        "medium": (8, 18),
        "hard": (16, 29),
    }[band]
    if profile in ("top_tie", "bottom_tie", "four_way_tie"):
        width = _odd(rng, max(5, lower), upper)
    else:
        width = rng.randint(lower, upper)
    if profile in ("left_tie", "right_tie", "four_way_tie"):
        height = _odd(rng, max(5, lower), upper)
    else:
        height = rng.randint(lower, upper)

    for _ in range(100):
        r, c = _position(rng, profile, height, width)
        corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
        if (r, c) not in corners and _relation(r, c, height, width) == profile:
            break
    else:
        raise RuntimeError(f"could not choose position for {profile!r}")

    colors = (0, 1, 2, 3, 4, 5, 6, 7, 9) if allow_nine else (0, 1, 2, 3, 4, 5, 6, 7)
    color = marker_color if marker_color is not None else rng.choice(colors)
    return _single((height, width, r, c, color))


def _validate_generation_scalar(name, value):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if not 0 <= value < 2**63:
        raise ValueError(f"{name} must satisfy 0 <= {name} < 2**63")
    return value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generation_scalar("seed", seed)
    _validate_generation_scalar("sample_index", sample_index)

    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    schedule_index = sample_index % len(DEFAULT_PROFILE_SCHEDULE)
    if requested is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
        force_nine = False
    else:
        scheduled = DEFAULT_PROFILE_SCHEDULE[schedule_index]
        profile = ctx.draw_choice("scene_profile", (scheduled,))
        force_nine = DEFAULT_FORCE_NINE_SCHEDULE[schedule_index]
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]

    # The shared bounded first-color-only diagnostic treats literal nonzero
    # background 8 as a candidate color. A cyclic 9,9,<9,<9 marker schedule
    # leaves two color-9 refutations in every four-pair lesson while still
    # preserving non-9 tie and non-tie counterfactuals. Explicit overrides keep
    # the full nuisance-color distribution.
    marker_color = 9 if force_nine else None
    return _general(
        ctx.draw_rng("layout"),
        profile,
        band,
        marker_color=marker_color,
        allow_nine=requested is not None,
    )


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    """Return semantic-shape diagnostics for strict gate sampling."""
    return self_check(grid)


def _reverse_tie_order(grid):
    """RIVAL: choose the same nearest corner but reverse all distance ties."""
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _solve_with_corner_order(grid, _REVERSE_TIE_CORNERS)[0]


def _tie_break_witness(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["scene_profile"] in TIE_PROFILES


EXAMPLES_NEEDED = 3
SEMANTIC_WITNESSES = {"tie_break": _tie_break_witness}
CANONICAL_SHORTCUTS = {"reverse_tie_order": _reverse_tie_order}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
WITNESS_RIVALS = {"tie_break": ["reverse_tie_order"]}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def lesson_identifiable(demos, query):
    """Require the demonstrations to refute any query-changing declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is missing input/output"]
        findings = self_check(pair["input"])
        if findings:
            return [f"demo {index}: {finding}" for finding in findings]

    query_grid = query.get("input") if isinstance(query, dict) else query
    findings = self_check(query_grid)
    if findings:
        return [f"query: {finding}" for finding in findings]

    expected_query = rule_mirror(query_grid)
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query_grid) != expected_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
