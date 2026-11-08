"""Input sampler for ``Analogy A:B::C:? with Panel Candidates``.

Panels are square and separated by one full color-9 column.  The first pair
A,B identifies the *first* transform in the authority's order
(identity, 90/180/270 degrees clockwise, horizontal reflection).  That same
transform is applied to C after translation-normalization.  Exactly one
candidate has the transformed normalized support; the rule returns that
candidate at its original in-panel offset, recolored cyan (8).

This module generates inputs only.  The selected Racket rule remains the label
authority.  ``workspace/review_probe.py`` is an independent authoring oracle.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f0f072d3d7e"
TASK_ID = GENERATOR_ID
RULE_HASH = "5c71009c7048"
VERSION = "2.0.0"
SUMMARY = (
    "Square panels A, B, C and 2..3 candidates are separated by color 9. "
    "Infer the first rotation/reflection mapping normalized A to B, apply it "
    "to normalized C, then return the unique matching candidate at its "
    "original offset recolored 8."
)

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "five or six equal square panels are separated by single full color-9 columns",
    "each panel has one distinct object color and connected nonempty support",
    "A to B identifies exactly the requested first-match transform code",
    "all candidates have C's cell count and exactly one normalized candidate equals T(C)",
    "the winning candidate's in-panel translation is preserved in the output",
]

AXES = {
    "panel_s": {
        "type": "int", "default": "scheduled 4", "valid": "3..4",
    },
    "n_candidates": {
        "type": "int", "default": "scheduled 3", "valid": "2..3",
    },
    "shape_size_a": {
        "type": "int", "default": "scheduled 4..6", "valid": "4..6",
    },
    "shape_size_c": {
        "type": "int", "default": "scheduled 3..6", "valid": "3..6",
    },
    "transform_code": {
        "type": "int", "default": "six-profile schedule", "valid": "0..4",
    },
    "winner_rank": {
        "type": "int", "default": "six-profile schedule", "valid": "0..2",
    },
}

# A third candidate is necessary for rank 2.  Every other advertised joint
# assignment is constructively supported, in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_candidates": 2, "winner_rank": 2},
]

SCHEDULE_PROFILES = (
    "cw_pair_a",
    "ccw_pair_a",
    "cw_pair_b",
    "ccw_pair_b",
    "branch_a",
    "branch_b",
)
# The two quarter-turn codes each occur twice per six-pair lesson.  Their
# winner ranks disagree even across a cycle boundary, so no five-demo rotation
# can teach "transform code -> candidate rank".  The final two slots rotate
# through the remaining identity/reflection/half-turn branches over 18 draws.
_PROFILE_RANK_BASE = (2, 2, 1, 1, 0, 0)
_BRANCH_CODES = ((4, 2), (0, 4), (2, 0))
_PROFILE_SIZE_A = (4, 5, 6, 4, 5, 6)
_PROFILE_SIZE_C = (3, 4, 5, 6, 4, 5)
_INVERSE_CODE = {0: 0, 1: 3, 2: 2, 3: 1, 4: 4}
_AXIS_BOUNDS = {
    "panel_s": (3, 4),
    "n_candidates": (2, 3),
    "shape_size_a": (4, 6),
    "shape_size_c": (3, 6),
    "transform_code": (0, 4),
    "winner_rank": (0, 2),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic six-slot teaching profile for this pair.

    Six consecutive accepted samples visit every profile once.  Each canonical
    shortcut has at least two counterexamples per block, so holding any one pair
    out as query still leaves a demonstration that refutes it.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_code(sample_index):
    slot = sample_index % len(SCHEDULE_PROFILES)
    if slot in (0, 2):
        return 1
    if slot in (1, 3):
        return 3
    cycle = (sample_index // len(SCHEDULE_PROFILES)) % len(_BRANCH_CODES)
    return _BRANCH_CODES[cycle][slot - 4]


def _scheduled_rank(sample_index):
    slot = sample_index % len(SCHEDULE_PROFILES)
    cycle = sample_index // len(SCHEDULE_PROFILES)
    return (_PROFILE_RANK_BASE[slot] + cycle) % 3


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot_cw(cells):
    cells = _normalize(cells)
    if not cells:
        return ()
    h = max(r for r, _ in cells) + 1
    return _normalize((c, h - 1 - r) for r, c in cells)


def _flip_lr(cells):
    cells = _normalize(cells)
    if not cells:
        return ()
    w = max(c for _, c in cells) + 1
    return _normalize((r, w - 1 - c) for r, c in cells)


def _apply(cells, code):
    """0=id, 1/2/3=clockwise quarter turns, 4=left-right reflection."""
    cells = _normalize(cells)
    if code == 4:
        return _flip_lr(cells)
    for _ in range(code):
        cells = _rot_cw(cells)
    return cells


def _identify_transform(a, b):
    """Replicate the authority's first-match transform precedence exactly."""
    target = _normalize(b)
    for code in range(4):
        if _apply(a, code) == target:
            return code
    if _flip_lr(a) == target:
        return 4
    return 0


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in remaining and point not in seen:
                seen.add(point)
                stack.append(point)
    return len(seen) == len(remaining)


@lru_cache(maxsize=8)
def _shape_pool(side, size):
    """All translation-normalized connected supports in the finite domain."""
    points = tuple(product(range(side), repeat=2))
    return tuple(sorted({
        _normalize(cells)
        for cells in combinations(points, size)
        if _connected(cells)
    }))


@lru_cache(maxsize=40)
def _exact_a_pool(side, size, code):
    """Shapes whose requested A->B code survives first-match precedence."""
    return tuple(
        shape for shape in _shape_pool(side, size)
        if _identify_transform(shape, _apply(shape, code)) == code
    )


def _placements(shape, side):
    shape = _normalize(shape)
    h = max(r for r, _ in shape) + 1
    w = max(c for _, c in shape) + 1
    return tuple(
        tuple((r + dr, c + dc) for r, c in shape)
        for dr in range(side - h + 1)
        for dc in range(side - w + 1)
    )


def _draw_axis(ctx, name, desired, domain, overrides):
    """Honor exact overrides while making the default teaching schedule exact."""
    options = tuple(domain) if name in overrides else (desired,)
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    clean = {name: value for name, value in overrides.items() if value is not None}
    for name, value in clean.items():
        lo, hi = _AXIS_BOUNDS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    if clean.get("n_candidates") == 2 and clean.get("winner_rank") == 2:
        raise ValueError(
            "incompatible overrides: n_candidates=2 cannot realize winner_rank=2"
        )
    return clean


def _paint(grid, column_offset, cells, color):
    for r, c in cells:
        grid[r][column_offset + c] = color


def _pick_shape_c(rng, side, size, code):
    pool = list(_shape_pool(side, size))
    if code in (1, 3):
        inverse = _INVERSE_CODE[code]
        directional = [s for s in pool if _apply(s, code) != _apply(s, inverse)]
        if directional:
            pool = directional
    # Prefer targets with a genuine translation degree of freedom.  This is a
    # preference, not a rejected domain: the exact (3,6,quarter-turn) boundary
    # remains supported even though every directional target spans the panel.
    shiftable = [s for s in pool if len(_placements(_apply(s, code), side)) > 1]
    if shiftable:
        pool = shiftable
    return rng.choice(pool)


def _decoy_shapes(shape_c, target, side, count, code, rng):
    """Construct equal-count, normalized nonmatches without capped retries."""
    mandatory = []
    inverse = _apply(shape_c, _INVERSE_CODE[code])
    if inverse != target:
        mandatory.append(inverse)

    transform_decoys = []
    for alt_code in range(5):
        candidate = _apply(shape_c, alt_code)
        if candidate != target and candidate not in mandatory and candidate not in transform_decoys:
            transform_decoys.append(candidate)
    rng.shuffle(transform_decoys)

    pool = [
        shape for shape in _shape_pool(side, len(shape_c))
        if shape != target and shape not in mandatory and shape not in transform_decoys
    ]
    rng.shuffle(pool)
    if len(_placements(target, side)) > 1:
        # When the winner can move, prefer decoys that can move too.  Candidate
        # translation is then a nuisance shared by all options, not a winner cue.
        pool.sort(key=lambda shape: len(_placements(shape, side)) <= 1)

    selected = mandatory + transform_decoys + pool
    if len(selected) < count:
        raise RuntimeError("finite shape domain cannot supply enough nonmatching candidates")
    selected = selected[:count]
    rng.shuffle(selected)
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % len(SCHEDULE_PROFILES)

    side = _draw_axis(ctx, "panel_s", 4, range(3, 5), overrides)
    # winner_rank=2 alone forces a realizable three-candidate scene.
    desired_n = 3
    n_domain = (3,) if overrides.get("winner_rank") == 2 else range(2, 4)
    n_candidates = _draw_axis(ctx, "n_candidates", desired_n, n_domain, overrides)

    code = _draw_axis(
        ctx, "transform_code", _scheduled_code(sample_index), range(5), overrides
    )
    band_shift = {"easy": -1, "hard": 1}.get(difficulty, 0)
    desired_size_a = min(6, max(4, _PROFILE_SIZE_A[slot] + band_shift))
    desired_size_c = min(6, max(3, _PROFILE_SIZE_C[slot] + band_shift))
    size_a = _draw_axis(
        ctx, "shape_size_a", desired_size_a, range(4, 7), overrides
    )
    size_c = _draw_axis(
        ctx, "shape_size_c", desired_size_c, range(3, 7), overrides
    )
    scheduled_rank = min(_scheduled_rank(sample_index), n_candidates - 1)
    winner_rank = _draw_axis(
        ctx, "winner_rank", scheduled_rank, range(n_candidates), overrides
    )

    band_label = difficulty if difficulty in ("easy", "medium", "hard") else "default"
    shape_rng = ctx.draw_rng(f"shape_selection:{band_label}")
    pool_a = _exact_a_pool(side, size_a, code)
    if not pool_a:
        raise RuntimeError(
            f"no exact A shape for side={side}, size={size_a}, code={code}"
        )
    shape_a = shape_rng.choice(pool_a)
    shape_b = _apply(shape_a, code)
    shape_c = _pick_shape_c(shape_rng, side, size_c, code)
    target = _apply(shape_c, code)

    decoys = _decoy_shapes(
        shape_c, target, side, n_candidates - 1, code,
        ctx.draw_rng(f"decoy_shapes:{band_label}")
    )
    candidate_shapes = list(decoys)
    candidate_shapes.insert(winner_rank, target)

    position_rng = ctx.draw_rng(f"panel_positions:{band_label}")
    supports = [
        position_rng.choice(_placements(shape_a, side)),
        position_rng.choice(_placements(shape_b, side)),
        position_rng.choice(_placements(shape_c, side)),
    ]
    candidate_placements = [list(_placements(shape, side)) for shape in candidate_shapes]
    prefer_shift = slot in (0, 1, 2, 3)
    shifted_options = [
        [p for p in placements if _normalize(p) != tuple(sorted(p))]
        for placements in candidate_placements
    ]
    if prefer_shift and all(shifted_options):
        # Every candidate—not only the winner—uses a nonzero translation.
        for placements in shifted_options:
            supports.append(position_rng.choice(placements))
    else:
        # A common top-left mode avoids leaking the answer when any candidate
        # lacks translation room (notably some side=3,size=6 supports).
        for shape in candidate_shapes:
            supports.append(tuple(sorted(_normalize(shape))))

    panel_count = len(supports)
    width = panel_count * side + panel_count - 1
    grid = full_grid(side, width, 0)
    for index in range(1, panel_count):
        separator = index * side + index - 1
        for r in range(side):
            grid[r][separator] = 9

    colors = ctx.draw_rng(f"panel_colors:{band_label}").sample(range(1, 9), panel_count)
    for index, (cells, color) in enumerate(zip(supports, colors)):
        _paint(grid, index * (side + 1), cells, color)
    return grid


def _parse_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be integers in 0..9")
    if not 3 <= height <= 4:
        raise ValueError("panel side/height must be 3..4")

    separators = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]
    if any(b == a + 1 for a, b in zip(separators, separators[1:])):
        raise ValueError("separator columns must have width exactly one")
    bounds = [-1] + separators + [width]
    if not 4 <= len(separators) <= 5:
        raise ValueError("need A, B, C and 2..3 candidates")
    if any(b - a - 1 != height for a, b in zip(bounds, bounds[1:])):
        raise ValueError("all panels must be square and equal-sized")

    panels = []
    supports = []
    colors = []
    for a, b in zip(bounds, bounds[1:]):
        panel = [list(row[a + 1:b]) for row in grid]
        if any(value == 9 for row in panel for value in row):
            raise ValueError("color 9 is reserved for full separator columns")
        occupied = tuple(
            (r, c)
            for r, row in enumerate(panel)
            for c, value in enumerate(row)
            if value != 0
        )
        if not occupied:
            raise ValueError("every panel must contain a nonempty object")
        panel_colors = {panel[r][c] for r, c in occupied}
        if len(panel_colors) != 1:
            raise ValueError("each panel must use exactly one object color")
        if not _connected(occupied):
            raise ValueError("each panel object must be 4-connected")
        panels.append(panel)
        supports.append(occupied)
        colors.append(next(iter(panel_colors)))
    if len(set(colors)) != len(colors):
        raise ValueError("panel object colors must be distinct")

    a, b, c = supports[:3]
    candidates = supports[3:]
    if not 4 <= len(a) <= 6 or len(b) != len(a):
        raise ValueError("A and B must have the same 4..6 cell count")
    if not 3 <= len(c) <= 6:
        raise ValueError("C must have 3..6 cells")
    code = _identify_transform(a, b)
    if _apply(a, code) != _normalize(b):
        raise ValueError("B is not an allowed transform of A")
    target = _apply(c, code)
    matches = [
        index for index, candidate in enumerate(candidates)
        if _normalize(candidate) == target
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one matching candidate, found {len(matches)}")
    return {
        "side": height,
        "panels": panels,
        "supports": supports,
        "code": code,
        "target": target,
        "matches": matches,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        _parse_grid(grid)
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    """Lawful task-domain inputs, including every canonical input."""
    return self_check(grid)


def observe_overrides(grid):
    parsed = _parse_grid(grid)
    supports = parsed["supports"]
    return {
        "panel_s": parsed["side"],
        "n_candidates": len(supports) - 3,
        "shape_size_a": len(supports[0]),
        "shape_size_c": len(supports[2]),
        "transform_code": parsed["code"],
        "winner_rank": parsed["matches"][0],
    }


def _render(cells, side, color=8):
    occupied = set(cells)
    return [
        [color if (r, c) in occupied else 0 for c in range(side)]
        for r in range(side)
    ]


def _blank(side):
    return [[0 for _ in range(side)] for _ in range(side)]


def _solve(grid):
    """Python mirror for tests/rivals; the Racket program remains authority."""
    parsed = _parse_grid(grid)
    winner = parsed["supports"][3 + parsed["matches"][0]]
    return _render(winner, parsed["side"])


def _first_candidate(grid):
    parsed = _parse_grid(grid)
    return _render(parsed["supports"][3], parsed["side"])


def _inverse_transform(grid):
    parsed = _parse_grid(grid)
    inverse_target = _apply(
        parsed["supports"][2], _INVERSE_CODE[parsed["code"]]
    )
    for candidate in parsed["supports"][3:]:
        if _normalize(candidate) == inverse_target:
            return _render(candidate, parsed["side"])
    return _blank(parsed["side"])


def _normalize_output_position(grid):
    parsed = _parse_grid(grid)
    winner = parsed["supports"][3 + parsed["matches"][0]]
    return _render(_normalize(winner), parsed["side"])


def _copy_c_position(grid):
    parsed = _parse_grid(grid)
    return _render(parsed["supports"][2], parsed["side"])


def _fixed_transform_code_winner_rank(grid):
    """The exact rank lookup induced by the reviewed v1 teaching schedule."""
    parsed = _parse_grid(grid)
    rank = {0: 0, 1: 1, 2: 2, 3: 2, 4: 1}[parsed["code"]]
    candidates = parsed["supports"][3:]
    if rank >= len(candidates):
        return _blank(parsed["side"])
    return _render(candidates[rank], parsed["side"])


def _later_winner(grid):
    return observe_overrides(grid)["winner_rank"] > 0


def _forward_not_inverse(grid):
    return _solve(grid) != _inverse_transform(grid)


def _preserves_nonzero_offset(grid):
    return _solve(grid) != _normalize_output_position(grid)


def _transformed_not_copy_c(grid):
    return _solve(grid) != _copy_c_position(grid)


# Both canonical shortcuts below fit all three public pairs.  Generated examples
# must therefore supply their counterexamples; task tests verify this assertion.
CANONICAL_SHORTCUTS = {
    "always_first_candidate": _first_candidate,
    "apply_inverse_b_to_a_transform": _inverse_transform,
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "normalize_winner_to_top_left": _normalize_output_position,
    "copy_c_at_original_position": _copy_c_position,
    "fixed_transform_code_winner_rank": _fixed_transform_code_winner_rank,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
def _joint_shortcut_counterexample(grid):
    """One compact witness on which every declared rival is actually wrong."""
    answer = _solve(grid)
    return all(rival(grid) != answer for rival in SEMANTIC_RIVALS.values())


SEMANTIC_WITNESSES = {
    "joint_shortcut_counterexample": _joint_shortcut_counterexample,
}
WITNESS_RIVALS = {
    "joint_shortcut_counterexample": list(SEMANTIC_RIVALS),
}


def lesson_identifiable(demos, query):
    """Return surviving declared query-changing rules after the demonstrations."""
    del query
    survivors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    reasons = []
    if survivors:
        reasons.append("declared rivals fit every demonstration: " + ", ".join(survivors))

    ranks_by_code = {}
    for pair in demos:
        observed = observe_overrides(pair["input"])
        ranks_by_code.setdefault(observed["transform_code"], set()).add(
            observed["winner_rank"]
        )
    if not any(len(ranks) > 1 for ranks in ranks_by_code.values()):
        reasons.append("transform code still predicts winner rank in every demonstration")
    return reasons
