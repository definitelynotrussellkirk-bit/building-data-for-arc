"""Source-bound generator for ARC task 34abaec056ef.

A cardinal 2-3-4 tripod defines local coordinates: color 2 is the origin,
color 3 is local (1, 0), and color 4 is local (0, 1).  The canonical rule
emits a 3x3 grid containing 8 exactly where a color-8 input cell occupies the
corresponding local coordinate in {-1, 0, 1}^2.  Other colors and radius-2
color-8 markers are ignored.

The four-slot production schedule deliberately alternates one canonical-profile
clean case with three color-selection witnesses.  Every four-example lesson
therefore contains the 9x9 / five-color canonical profile while also refuting
the strongest canonical shortcut: treating every occupied non-frame local cell
as an output marker regardless of its color.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "34abaec056ef"
TASK_ID = GENERATOR_ID
RULE_HASH = "8623727f72da"
VERSION = "2.0.0"
SUMMARY = (
    "Normalize the color-2/3/4 cardinal frame and emit a 3x3 map of only "
    "the local color-8 cells; ignore other colors and radius-2 markers."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_clean",
    "local_color_witness_a",
    "local_color_witness_b",
    "local_color_witness_c",
)
MIN_STRICT_FRAC = 1.0
# Six non-frame cells are available; production emits every subset of size 1..5.
EXPECTED_OUTPUT_CODOMAIN = 62

INVARIANTS = [
    "the grid is 9..15 rows by 9..16 columns",
    "exactly one color-2 origin, color-3 x tip and color-4 y tip form an ordered cardinal orthogonal frame",
    "1..5 visible color-8 markers occupy free local cells in the 3x3 output window",
    "0..4 additional color-8 markers occupy only the radius-2 ring and are ignored by the output",
    "0..1 ignored-color distractor occupies a free local output cell and 0..4 lie outside radius 2",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9 or difficulty-weighted 9..15", "valid": "9..15"},
    "grid_w": {"type": "int", "default": "scheduled 9 or difficulty-weighted 9..16", "valid": "9..16"},
    "orientation": {"type": "int", "default": "uniform ordered cardinal basis 0..7", "valid": "0..7"},
    "n_markers": {"type": "int", "default": "scheduled/difficulty-weighted 1..5", "valid": "1..5"},
    "n_outer_markers": {"type": "int", "default": "scheduled/difficulty-weighted 0..4", "valid": "0..4"},
    "n_local_distractors": {"type": "int", "default": "0 in canonical slot, 1 in witness slots", "valid": "0..1"},
    "n_exterior_distractors": {"type": "int", "default": "scheduled/difficulty-weighted 0..4", "valid": "0..4"},
}
# All cross-products are constructive, including the 9x9 maximum-count case.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Every ordered orthogonal pair of unit cardinal vectors.
_BASES = (
    ((0, 1), (1, 0)),
    ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)),
    ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)),
    ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)),
    ((1, 0), (0, 1)),
)
_BLOCKED_LOCAL = frozenset({(0, 0), (1, 0), (0, 1)})
_VISIBLE_FREE = tuple(
    (u, v)
    for u in range(-1, 2)
    for v in range(-1, 2)
    if (u, v) not in _BLOCKED_LOCAL
)
_OUTPUT_SUBSETS = tuple(
    subset
    for size in range(1, 6)
    for subset in combinations(_VISIBLE_FREE, size)
)
assert len(_OUTPUT_SUBSETS) == EXPECTED_OUTPUT_CODOMAIN
_OUTER_RING = tuple(
    (u, v)
    for u in range(-2, 3)
    for v in range(-2, 3)
    if max(abs(u), abs(v)) == 2
)
_DISTRACTOR_COLORS = (1, 5, 6, 7, 9)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BOUNDS = {
    "grid_h": (9, 15),
    "grid_w": (9, 16),
    "orientation": (0, 7),
    "n_markers": (1, 5),
    "n_outer_markers": (0, 4),
    "n_local_distractors": (0, 1),
    "n_exterior_distractors": (0, 4),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic role for one sample index."""
    del seed
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _global(frame, u, v):
    origin, vx, vy = frame
    return (
        origin[0] + u * vx[0] + v * vy[0],
        origin[1] + u * vx[1] + v * vy[1],
    )


def _local(frame, row, col):
    origin, vx, vy = frame
    dr, dc = row - origin[0], col - origin[1]
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def _find_frame(grid):
    points = {}
    for color in (2, 3, 4):
        hits = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(hits) != 1:
            raise ValueError(f"expected exactly one color-{color} frame cell, found {len(hits)}")
        points[color] = hits[0]
    origin = points[2]
    vx = tuple(points[3][i] - origin[i] for i in (0, 1))
    vy = tuple(points[4][i] - origin[i] for i in (0, 1))
    if (vx, vy) not in _BASES:
        raise ValueError("colors 2, 3 and 4 must form an ordered cardinal orthogonal frame")
    return origin, vx, vy


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name, defaults, overrides):
    """Use full strict bounds for explicit controls and scheduled choices otherwise."""
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    values = tuple(defaults)
    if not values or any(type(v) is not int or not lo <= v <= hi for v in values):
        raise RuntimeError(f"invalid default domain for {name}: {values!r}")
    return ctx.draw_choice(name, values)


def _defaults(difficulty, phase):
    if phase == 0:
        return {
            "grid_h": (9,),
            "grid_w": (9,),
            "n_markers": (3,),
            "n_outer_markers": (0,),
            "n_local_distractors": (0,),
            "n_exterior_distractors": (0,),
        }
    if difficulty == "easy":
        h, w, markers, outer, exterior = range(9, 12), range(9, 12), range(1, 4), range(0, 2), range(0, 2)
    elif difficulty == "hard":
        h, w, markers, outer, exterior = range(11, 16), range(12, 17), range(3, 6), range(1, 5), range(1, 5)
    else:
        h, w, markers, outer, exterior = range(9, 14), range(9, 15), range(2, 5), range(0, 4), range(0, 4)
    return {
        "grid_h": tuple(h),
        "grid_w": tuple(w),
        "n_markers": tuple(markers),
        "n_outer_markers": tuple(outer),
        "n_local_distractors": (1,),
        "n_exterior_distractors": tuple(exterior),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    defaults = _defaults(difficulty, phase)
    h = _draw_axis(ctx, "grid_h", defaults["grid_h"], overrides)
    w = _draw_axis(ctx, "grid_w", defaults["grid_w"], overrides)
    orientation = _draw_axis(ctx, "orientation", range(8), overrides)
    scheduled_marker_uvs = None
    marker_defaults = defaults["n_markers"]
    if overrides.get("n_markers") is None:
        scheduled_marker_uvs = _OUTPUT_SUBSETS[(seed + sample_index) % len(_OUTPUT_SUBSETS)]
        marker_defaults = (len(scheduled_marker_uvs),)
    n_markers = _draw_axis(ctx, "n_markers", marker_defaults, overrides)
    n_outer = _draw_axis(ctx, "n_outer_markers", defaults["n_outer_markers"], overrides)
    n_local_noise = _draw_axis(
        ctx, "n_local_distractors", defaults["n_local_distractors"], overrides
    )
    n_exterior_noise = _draw_axis(
        ctx, "n_exterior_distractors", defaults["n_exterior_distractors"], overrides
    )

    origins = tuple((r, c) for r in range(2, h - 2) for c in range(2, w - 2))
    origin = ctx.draw_rng("origin").choice(origins)
    frame = (origin, *_BASES[orientation])
    grid = full_grid(h, w, 0)
    for uv, color in zip(((0, 0), (1, 0), (0, 1)), (2, 3, 4)):
        r, c = _global(frame, *uv)
        grid[r][c] = color

    visible_rng = ctx.draw_rng("visible_markers")
    marker_uvs = (
        list(scheduled_marker_uvs)
        if scheduled_marker_uvs is not None
        else visible_rng.sample(_VISIBLE_FREE, n_markers)
    )
    remaining_visible = tuple(uv for uv in _VISIBLE_FREE if uv not in marker_uvs)
    local_noise_uvs = ctx.draw_rng("local_distractors").sample(
        remaining_visible, n_local_noise
    )
    outer_uvs = ctx.draw_rng("outer_markers").sample(_OUTER_RING, n_outer)

    for uv in (*marker_uvs, *outer_uvs):
        r, c = _global(frame, *uv)
        if grid[r][c] != 0:
            raise RuntimeError("constructive marker placement collided")
        grid[r][c] = 8

    color_rng = ctx.draw_rng("distractor_colors")
    for uv in local_noise_uvs:
        r, c = _global(frame, *uv)
        if grid[r][c] != 0:
            raise RuntimeError("constructive local distractor placement collided")
        grid[r][c] = color_rng.choice(_DISTRACTOR_COLORS)

    exterior_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and max(map(abs, _local(frame, r, c))) > 2
    ]
    exterior = ctx.draw_rng("exterior_distractors").sample(
        exterior_candidates, n_exterior_noise
    )
    for r, c in exterior:
        grid[r][c] = color_rng.choice(_DISTRACTOR_COLORS)
    return grid


def _analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty grid rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    frame = _find_frame(grid)
    markers = []
    local_noise = 0
    exterior_noise = 0
    ring_noise = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            uv = _local(frame, r, c)
            radius = max(abs(uv[0]), abs(uv[1]))
            if value == 8:
                markers.append(uv)
            elif value in _DISTRACTOR_COLORS:
                if radius <= 1:
                    local_noise += 1
                elif radius == 2:
                    ring_noise += 1
                else:
                    exterior_noise += 1
    visible = sum(max(abs(u), abs(v)) <= 1 for u, v in markers)
    outer = sum(max(abs(u), abs(v)) == 2 for u, v in markers)
    distant_markers = sum(max(abs(u), abs(v)) > 2 for u, v in markers)
    return {
        "frame": frame,
        "grid_h": len(grid),
        "grid_w": width,
        "orientation": _BASES.index(frame[1:]),
        "n_markers": visible,
        "n_outer_markers": outer,
        "n_distant_markers": distant_markers,
        "n_local_distractors": local_noise,
        "n_ring_distractors": ring_noise,
        "n_exterior_distractors": exterior_noise,
    }


def observe_overrides(grid):
    facts = _analyze(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        facts = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors = []
    if not 9 <= facts["grid_h"] <= 15:
        errors.append("grid_h outside [9,15]")
    if not 9 <= facts["grid_w"] <= 16:
        errors.append("grid_w outside [9,16]")
    origin = facts["frame"][0]
    if not (2 <= origin[0] < facts["grid_h"] - 2 and 2 <= origin[1] < facts["grid_w"] - 2):
        errors.append("the complete radius-2 local square must fit in the grid")
    if not 1 <= facts["n_markers"] <= 5:
        errors.append("visible color-8 marker count must be in [1,5]")
    if not 0 <= facts["n_outer_markers"] <= 4:
        errors.append("radius-2 color-8 marker count must be in [0,4]")
    if facts["n_distant_markers"]:
        errors.append("color-8 markers may not occur outside radius 2")
    if not 0 <= facts["n_local_distractors"] <= 1:
        errors.append("local ignored-color distractor count must be in [0,1]")
    if facts["n_ring_distractors"]:
        errors.append("ignored-color distractors may not occupy the radius-2 ring")
    if not 0 <= facts["n_exterior_distractors"] <= 4:
        errors.append("exterior ignored-color distractor count must be in [0,4]")
    return errors


def strict_canonical_like(grid):
    """All produced inputs stay on the declared lawful task manifold."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python authoring mirror; Racket remains label authority."""
    frame = _find_frame(grid)
    marker_uvs = {
        _local(frame, r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    return [
        [8 if (c - 1, r - 1) in marker_uvs else 0 for c in range(3)]
        for r in range(3)
    ]


def _any_nonframe_local_color(grid):
    """Rival: collapse every occupied non-frame local color to output color 8."""
    frame = _find_frame(grid)
    occupied = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            uv = _local(frame, r, c)
            if max(abs(uv[0]), abs(uv[1])) <= 1 and value not in (0, 2, 3, 4):
                occupied.add(uv)
    return [
        [8 if (c - 1, r - 1) in occupied else 0 for c in range(3)]
        for r in range(3)
    ]


def _has_ignored_local_color(grid):
    try:
        return _analyze(grid)["n_local_distractors"] > 0
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS = {"any_nonframe_local_color": _any_nonframe_local_color}
SEMANTIC_WITNESSES = {"ignored_local_color": _has_ignored_local_color}
WITNESS_RIVALS = {"ignored_local_color": ["any_nonframe_local_color"]}
BRANCH_WITNESSES = {"ignored_local_color"}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Return exact declared-rival ambiguities for one labeled lesson."""
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"at least {EXAMPLES_NEEDED} demonstrations are required")
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if self_check(pair["input"]):
            reasons.append(f"demo {index} input is outside the generator domain")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not follow the reference geometry")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
        return reasons
    if self_check(query["input"]):
        reasons.append("query input is outside the generator domain")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not follow the reference geometry")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
            else:
                reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
