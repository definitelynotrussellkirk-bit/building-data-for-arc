"""Generator for training task ecaa0ec1 / d833a288bd7d.

A dense square bitmap uses colors 1 and 8.  One yellow cell at an
expanded bounding-box corner identifies the source diagonal; a separate
three-yellow L cluster identifies the target diagonal.  The output clears
the markers, rotates the colored bitmap by ``target - source`` quarter
turns clockwise in its original box, and marks the target corner yellow.

The five public scenes all use a dense 3x3 bitmap and a three-corner
cluster on a spacing-two scaffold.  Their complete linked profiles retain
canvas dimensions, the colored bitmap, source corner, and cluster offsets.
Whole-scene translation is answer-bearing placement nuisance, not a change
to the profile morphology.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d833a288bd7d"
VERSION = "3.0.1"
TASK_ID = "d833a288bd7d"
RULE_HASH = "67e977ce99e1"

SUMMARY = (
    "A 10..20 square-ish canvas contains one dense 3..6 square bitmap in "
    "colors 1/8, one yellow source marker at an expanded bbox corner, and "
    "a separate three-cell yellow L cluster in the target quadrant. Rotate "
    "the colored bitmap by target-source quarter turns and mark the target "
    "corner yellow."
)

INVARIANTS = [
    "the color-1/8 bitmap densely fills a square 3..6 bounding box",
    "both shape colors 1 and 8 occur",
    "exactly one yellow occupies an expanded bbox corner",
    "the other three yellows form an L triad wholly in one strict quadrant",
    "the source marker, target cluster, shape, and rotated answer fit in-bounds",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 10..20",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 10..20",
        "valid": "10..20",
    },
    "shape_dim": {
        "type": "int",
        "default": "difficulty-aware rng 3..6",
        "valid": "3..6",
    },
    "source_diag": {
        "type": "int",
        "default": "rng 0..3",
        "valid": "0..3",
    },
    "target_diag": {
        "type": "int",
        "default": "rng 0..3",
        "valid": "0..3",
    },
}

_PROFILE_PRIOR = 0.08
_VALID_H = (10, 20)
_VALID_W = (10, 20)
_VALID_DIM = (3, 6)
EXAMPLES_NEEDED = 3
_TEACHING_TURNS = (0, 1, 2, 3)

# h, w, dense colored shape, original top/left, source diagonal, and the
# target cluster expressed relative to shape top-left.
_PROFILE_SPECS = (
    (
        11,
        10,
        ((8, 1, 8), (1, 8, 8), (1, 1, 1)),
        3,
        3,
        0,
        ((2, -2), (4, -2), (4, 0)),
    ),
    (
        10,
        10,
        ((1, 1, 1), (8, 1, 8), (8, 1, 1)),
        3,
        3,
        1,
        ((-2, -2), (-2, 0), (0, -2)),
    ),
    (
        11,
        11,
        ((1, 1, 1), (8, 8, 8), (1, 8, 1)),
        4,
        4,
        1,
        ((2, 4), (4, 2), (4, 4)),
    ),
    (
        12,
        10,
        ((8, 1, 8), (8, 1, 8), (1, 1, 8)),
        5,
        4,
        2,
        ((-2, -2), (-2, 0), (0, -2)),
    ),
    (
        11,
        11,
        ((1, 1, 1), (1, 8, 8), (1, 8, 1)),
        4,
        4,
        3,
        ((-2, 2), (-2, 4), (0, 4)),
    ),
 )


def _profile_turn(spec):
    """Return the clockwise turn encoded by one complete canonical profile."""
    _, _, shape, top, left, source, cluster_rel = spec
    cluster = tuple((top + r, left + c) for r, c in cluster_rel)
    target = _target_diag(
        cluster,
        top + (len(shape) - 1) // 2,
        left + (len(shape) - 1) // 2,
    )
    return (target - source) % 4


def _scheduled_turn(sample_index):
    """Cycle all four turns so every three-example window contains an odd turn."""
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return _TEACHING_TURNS[sample_index % len(_TEACHING_TURNS)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


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


def _expanded_corners(r0, c0, r1, c1):
    return (
        (r0 - 1, c0 - 1),
        (r0 - 1, c1 + 1),
        (r1 + 1, c1 + 1),
        (r1 + 1, c0 - 1),
    )


def _target_diag(cluster, center_r, center_c):
    mean_r = sum(r for r, _ in cluster) // len(cluster)
    mean_c = sum(c for _, c in cluster) // len(cluster)
    if mean_r <= center_r and mean_c <= center_c:
        return 0
    if mean_r <= center_r and mean_c > center_c:
        return 1
    if mean_r > center_r and mean_c > center_c:
        return 2
    return 3


def _strict_quadrant(cell, center_r, center_c):
    r, c = cell
    if r < center_r and c < center_c:
        return 0
    if r < center_r and c > center_c:
        return 1
    if r > center_r and c > center_c:
        return 2
    if r > center_r and c < center_c:
        return 3
    return None


def _is_l_triad(cells):
    if len(cells) != 3:
        return False
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if len(rows) != 2 or len(cols) != 2:
        return False
    if not 1 <= rows[1] - rows[0] <= 3:
        return False
    if not 1 <= cols[1] - cols[0] <= 3:
        return False
    return set(cells) <= {
        (rows[0], cols[0]),
        (rows[0], cols[1]),
        (rows[1], cols[0]),
        (rows[1], cols[1]),
    }


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    h = len(grid)
    w = len(grid[0]) if grid else 0
    shape_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 8)
    ]
    if not shape_cells:
        return {
            "grid": grid,
            "h": h,
            "w": w,
            "shape_cells": (),
            "yellows": (),
        }
    r0 = min(r for r, _, _ in shape_cells)
    c0 = min(c for _, c, _ in shape_cells)
    r1 = max(r for r, _, _ in shape_cells)
    c1 = max(c for _, c, _ in shape_cells)
    shape = tuple(
        tuple(grid[r][c] for c in range(c0, c1 + 1))
        for r in range(r0, r1 + 1)
    )
    yellows = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    )
    corners = _expanded_corners(r0, c0, r1, c1)
    sources = tuple(i for i, corner in enumerate(corners) if corner in yellows)
    source = sources[0] if len(sources) == 1 else None
    cluster = tuple(
        sorted(
            cell
            for cell in yellows
            if cell not in set(corners)
        )
    )
    center_r = (r0 + r1) // 2
    center_c = (c0 + c1) // 2
    target = (
        _target_diag(cluster, center_r, center_c)
        if cluster
        else None
    )
    return {
        "grid": grid,
        "h": h,
        "w": w,
        "shape_cells": tuple(shape_cells),
        "shape": shape,
        "r0": r0,
        "c0": c0,
        "r1": r1,
        "c1": c1,
        "center_r": center_r,
        "center_c": center_c,
        "corners": corners,
        "sources": sources,
        "source_diag": source,
        "yellows": yellows,
        "cluster": cluster,
        "target_diag": target,
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or value not in (0, 1, 4, 8)
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integers from {0,1,4,8}")
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 10..20")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 10..20")
    scene = _analyze_scene(coerced)
    shape_cells = scene["shape_cells"]
    if not shape_cells:
        errors.append("missing color-1/8 shape")
        return errors
    shape_h = scene["r1"] - scene["r0"] + 1
    shape_w = scene["c1"] - scene["c0"] + 1
    if shape_h != shape_w or not (_VALID_DIM[0] <= shape_h <= _VALID_DIM[1]):
        errors.append("shape bbox must be square with dimension 3..6")
    if len(shape_cells) != shape_h * shape_w:
        errors.append("shape must densely fill its square bounding box")
    shape_colors = {value for _, _, value in shape_cells}
    if shape_colors != {1, 8}:
        errors.append("shape must contain both colors 1 and 8")
    if any(
        not (0 <= r < h and 0 <= c < w)
        for r, c in scene["corners"]
    ):
        errors.append("all four expanded shape corners must be in-bounds")
    if len(scene["yellows"]) != 4:
        errors.append("scene must contain exactly four yellow cells")
    if len(scene["sources"]) != 1:
        errors.append("exactly one yellow must occupy an expanded bbox corner")
    cluster = scene["cluster"]
    if len(cluster) != 3:
        errors.append("target cluster must contain exactly three non-corner yellows")
    elif not _is_l_triad(cluster):
        errors.append("target cluster must be three corners of an L scaffold")
    if len(cluster) == 3:
        if any(
            scene["r0"] <= r <= scene["r1"]
            and scene["c0"] <= c <= scene["c1"]
            for r, c in cluster
        ):
            errors.append("target cluster must remain outside the shape bbox")
        quadrants = {
            _strict_quadrant(cell, scene["center_r"], scene["center_c"])
            for cell in cluster
        }
        if None in quadrants or len(quadrants) != 1:
            errors.append(
                "every target-cluster cell must lie in one strict quadrant"
            )
        elif scene["target_diag"] not in quadrants:
            errors.append("cluster centroid disagrees with its target quadrant")
    return errors


def observe_overrides(grid):
    scene = _analyze_scene(grid)
    if self_check(grid):
        raise ValueError("cannot observe overrides from an invalid scene")
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "shape_dim": scene["r1"] - scene["r0"] + 1,
        "source_diag": scene["source_diag"],
        "target_diag": scene["target_diag"],
    }


def _rotate_shape(shape, turns):
    result = tuple(tuple(row) for row in shape)
    for _ in range(turns % 4):
        n = len(result)
        result = tuple(
            tuple(result[n - 1 - r][c] for r in range(n))
            for c in range(n)
        )
    return result


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    turns = (scene["target_diag"] - scene["source_diag"]) % 4
    rotated = _rotate_shape(scene["shape"], turns)
    out = full_grid(scene["h"], scene["w"], 0)
    for dr, row in enumerate(rotated):
        for dc, value in enumerate(row):
            out[scene["r0"] + dr][scene["c0"] + dc] = value
    marker = scene["corners"][scene["target_diag"]]
    out[marker[0]][marker[1]] = 4
    return out


def _reverse_rotation_rival(grid):
    """Plausible shortcut: rotate from target back toward the source."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    turns = (scene["source_diag"] - scene["target_diag"]) % 4
    rotated = _rotate_shape(scene["shape"], turns)
    out = full_grid(scene["h"], scene["w"], 0)
    for dr, row in enumerate(rotated):
        for dc, value in enumerate(row):
            out[scene["r0"] + dr][scene["c0"] + dc] = value
    marker = scene["corners"][scene["target_diag"]]
    out[marker[0]][marker[1]] = 4
    return out


def _odd_quarter_turn(grid):
    if self_check(grid):
        return False
    scene = _analyze_scene(grid)
    turn = (scene["target_diag"] - scene["source_diag"]) % 4
    return turn in (1, 3) and _reverse_rotation_rival(grid) != rule_mirror(grid)


def strict_canonical_like(grid):
    """This generator's validated manifold is its strict canonical-like domain."""
    return self_check(grid)


SEMANTIC_RIVALS = {"reverse_rotation": _reverse_rotation_rival}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"odd_quarter_turn": _odd_quarter_turn}
WITNESS_RIVALS = {"odd_quarter_turn": ["reverse_rotation"]}


def lesson_identifiable(demos, query):
    """Require demonstrations to reject the opposite-direction rotation rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"{label} must contain input and reference output"]
        errors = self_check(pair["input"])
        if errors:
            return [f"{label} is outside the strict manifold: {errors[0]}"]
        if rule_mirror(pair["input"]) != pair["output"]:
            return [f"{label} output disagrees with the intended rule"]
    findings = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                findings.append(
                    f"competitor '{name}' fits every demonstration and changes the query"
                )
            else:
                findings.append(f"competitor '{name}' survives every demonstration")
    return findings


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return (
        scene["h"],
        scene["w"],
        scene["shape"],
        scene["source_diag"],
        tuple(
            sorted(
                (r - scene["r0"], c - scene["c0"])
                for r, c in scene["cluster"]
            )
        ),
    )


def _profile_signature(spec):
    h, w, shape, _, _, source, cluster_rel = spec
    return (
        h,
        w,
        shape,
        source,
        tuple(sorted(cluster_rel)),
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(spec) for spec in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _paint_scene(h, w, shape, top, left, source, cluster):
    grid = full_grid(h, w, 0)
    for dr, row in enumerate(shape):
        for dc, value in enumerate(row):
            grid[top + dr][left + dc] = value
    dim = len(shape)
    corners = _expanded_corners(
        top,
        left,
        top + dim - 1,
        left + dim - 1,
    )
    grid[corners[source][0]][corners[source][1]] = 4
    for r, c in cluster:
        grid[r][c] = 4
    return grid


def _draw_profile(spec, rng):
    h, w, shape, top, left, source, cluster_rel = spec
    occupied = (
        [(top + r, left + c) for r in range(len(shape)) for c in range(len(shape))]
        + list(_expanded_corners(
            top,
            left,
            top + len(shape) - 1,
            left + len(shape) - 1,
        ))
        + [(top + r, left + c) for r, c in cluster_rel]
    )
    shifts = []
    for dr in range(-min(r for r, _ in occupied), h - max(r for r, _ in occupied)):
        for dc in range(-min(c for _, c in occupied), w - max(c for _, c in occupied)):
            shifts.append((dr, dc))
    dr, dc = rng.choice(shifts)
    cluster = tuple(
        (top + dr + r, left + dc + c)
        for r, c in cluster_rel
    )
    return _paint_scene(
        h,
        w,
        shape,
        top + dr,
        left + dc,
        source,
        cluster,
    )


def _draw_dense_shape(dim, rng):
    # Odd clockwise turns must differ from the opposite-direction rival.  A
    # 180-degree-symmetric bitmap would hide that distinction, so generated
    # bitmaps exclude only that narrow teaching-degenerate case.
    for _ in range(64):
        values = [rng.choice((1, 8)) for _ in range(dim * dim)]
        if len(set(values)) == 1:
            values[-1] = 8 if values[0] == 1 else 1
        shape = tuple(
            tuple(values[r * dim:(r + 1) * dim])
            for r in range(dim)
        )
        if _rotate_shape(shape, 1) != _rotate_shape(shape, 3):
            return shape
    raise RuntimeError("could not draw a reverse-rotation-distinguishing bitmap")


def _pairs(values):
    return tuple(
        (a, b)
        for i, a in enumerate(values)
        for b in values[i + 1:]
        if 1 <= b - a <= 3
    )


def _cluster_candidates(h, w, top, left, dim, source, target):
    r1 = top + dim - 1
    c1 = left + dim - 1
    center_r = (top + r1) // 2
    center_c = (left + c1) // 2
    row_values = (
        range(0, center_r)
        if target in (0, 1)
        else range(center_r + 1, h)
    )
    col_values = (
        range(0, center_c)
        if target in (0, 3)
        else range(center_c + 1, w)
    )
    expanded = _expanded_corners(top, left, r1, c1)
    corners = set(expanded)
    source_cell = expanded[source]
    candidates = []
    for ra, rb in _pairs(tuple(row_values)):
        for ca, cb in _pairs(tuple(col_values)):
            scaffold = (
                (ra, ca),
                (ra, cb),
                (rb, ca),
                (rb, cb),
            )
            for missing in range(4):
                cluster = tuple(
                    cell
                    for index, cell in enumerate(scaffold)
                    if index != missing
                )
                if source_cell in cluster or any(cell in corners for cell in cluster):
                    continue
                if any(
                    top <= r <= r1 and left <= c <= c1
                    for r, c in cluster
                ):
                    continue
                candidates.append(cluster)
    return candidates


def _draw_general(h, w, dim, source, target, rng):
    shape = _draw_dense_shape(dim, rng)
    positions = [
        (top, left)
        for top in range(1, h - dim)
        for left in range(1, w - dim)
    ]
    rng.shuffle(positions)
    for top, left in positions:
        candidates = _cluster_candidates(
            h,
            w,
            top,
            left,
            dim,
            source,
            target,
        )
        if not candidates:
            continue
        cluster = rng.choice(candidates)
        return _paint_scene(
            h,
            w,
            shape,
            top,
            left,
            source,
            cluster,
        )
    raise ValueError(
        f"cannot place dim-{dim} source/target scene on {h}x{w}"
    )


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
    exact_overrides = {
        label for label in AXES if overrides.get(label) is not None
    }
    teaching_turn = _scheduled_turn(sample_index)
    profile = None
    if not exact_overrides:
        matching_profiles = tuple(
            index
            for index, spec in enumerate(_PROFILE_SPECS)
            if _profile_turn(spec) == teaching_turn
        )
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        eligible_turns = {_profile_turn(spec) for spec in _PROFILE_SPECS}
        # Turn 0 has no canonical complete profile.  Raise the conditional
        # draw probability only on eligible turns so the overall prior remains
        # the original 8%, rather than silently falling to 6%.
        conditional_prior = _PROFILE_PRIOR * len(_TEACHING_TURNS) / len(eligible_turns)
        if matching_profiles and prior_rng.random() < conditional_prior:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                matching_profiles,
            )
            profile = _PROFILE_SPECS[profile_index]

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", *_VALID_H)
    elif profile is not None:
        h = ctx.draw_int("grid_h", profile[0], profile[0])
    else:
        h = ctx.draw_int(
            "grid_h",
            *{
                "easy": (10, 13),
                "medium": (11, 17),
                "hard": (15, 20),
            }[band],
        )

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif profile is not None:
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        w = ctx.draw_int(
            "grid_w",
            *{
                "easy": (10, 13),
                "medium": (11, 17),
                "hard": (15, 20),
            }[band],
        )

    if overrides.get("shape_dim") is not None:
        dim = ctx.draw_int("shape_dim", *_VALID_DIM)
    elif profile is not None:
        dim = ctx.draw_int("shape_dim", len(profile[2]), len(profile[2]))
    else:
        dim = ctx.draw_int(
            "shape_dim",
            *{
                "easy": (3, 3),
                "medium": (3, 5),
                "hard": (4, 6),
            }[band],
        )

    if profile is not None:
        source = ctx.draw_int(
            "source_diag",
            profile[5],
            profile[5],
        )
        profile_cluster = tuple(
            (profile[3] + r, profile[4] + c)
            for r, c in profile[6]
        )
        target_value = _target_diag(
            profile_cluster,
            profile[3] + (dim - 1) // 2,
            profile[4] + (dim - 1) // 2,
        )
        target = ctx.draw_int(
            "target_diag",
            target_value,
            target_value,
        )
    else:
        source_exact = overrides.get("source_diag") is not None
        target_exact = overrides.get("target_diag") is not None
        if source_exact and target_exact:
            source = ctx.draw_int("source_diag", 0, 3)
            target = ctx.draw_int("target_diag", 0, 3)
        elif source_exact:
            source = ctx.draw_int("source_diag", 0, 3)
            target_value = (source + teaching_turn) % 4
            target = ctx.draw_int("target_diag", target_value, target_value)
        elif target_exact:
            target = ctx.draw_int("target_diag", 0, 3)
            source_value = (target - teaching_turn) % 4
            source = ctx.draw_int("source_diag", source_value, source_value)
        else:
            source = ctx.draw_int("source_diag", 0, 3)
            target_value = (source + teaching_turn) % 4
            target = ctx.draw_int("target_diag", target_value, target_value)

    rng = ctx.draw_rng("layout")
    if profile is not None:
        grid = _draw_profile(profile, rng)
    else:
        grid = _draw_general(h, w, dim, source, target, rng)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
