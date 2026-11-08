"""Generator for bank task e352836528da:H2 / e250cb77a62e.

A blue frame contains a yellow prototype.  Each isolated orange seed denotes
the prototype's interior top-left anchor; stamp the yellow-cell offsets there
in cyan.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "e250cb77a62e"
VERSION = "4.0.0"
TASK_ID = "e250cb77a62e"
RULE_HASH = "61dff2d29f6e"

SUMMARY = (
    "Place one hollow blue frame containing a connected yellow prototype. "
    "Place one to four isolated orange anchors elsewhere with room for the "
    "complete prototype footprint. Stamp every prototype offset at every "
    "anchor in cyan."
)

INVARIANTS = [
    "input colors are 0, 1, 4, and 7",
    "exactly one 4..7 by 4..7 hollow blue frame contains the prototype",
    "the yellow prototype is connected and spans its frame interior",
    "the prototype includes its interior top-left anchor",
    "there are exactly 1..4 orange seeds outside the frame",
    "every complete stamp is in bounds and disjoint from the source and peers",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 11..22",
        "valid": "11..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 11..22",
        "valid": "11..22",
    },
    "n_seeds": {
        "type": "int",
        "default": "difficulty-aware rng 1..4",
        "valid": "1..4",
    },
}

_VALID_H = (11, 22)
_VALID_W = (11, 22)
_VALID_SEEDS = (1, 4)
_PROFILE_PRIOR = 0.08
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PUBLIC_PATTERN = ((0, 0), (0, 1), (1, 1), (2, 1))

# Height, width, outer-frame height/width, prototype, number of seeds.
# Frame and seed positions are nuisance variables and are randomized.
_PROFILE_SPECS = (
    (11, 11, 5, 4, _PUBLIC_PATTERN, 2),
    (12, 12, 5, 4, _PUBLIC_PATTERN, 2),
    (13, 13, 5, 4, _PUBLIC_PATTERN, 2),
)


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


def _is_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    remaining = set(cells)
    start = min(remaining)
    remaining.remove(start)
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINALS:
            neighbor = (r + dr, c + dc)
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    h = len(grid)
    w = len(grid[0]) if grid else 0
    rectangular = bool(grid) and all(len(row) == w for row in grid)
    if not rectangular:
        return {
            "grid": grid,
            "h": h,
            "w": w,
            "frame_bbox": None,
            "frame_h": 0,
            "frame_w": 0,
            "pattern": (),
            "seeds": (),
        }
    blue = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )
    frame_bbox = None
    if blue:
        frame_bbox = (
            min(r for r, _ in blue),
            min(c for _, c in blue),
            max(r for r, _ in blue),
            max(c for _, c in blue),
        )
    pattern = ()
    frame_h = frame_w = 0
    if frame_bbox is not None:
        r0, c0, r1, c1 = frame_bbox
        frame_h = r1 - r0 + 1
        frame_w = c1 - c0 + 1
        pattern = tuple(
            sorted(
                (r - r0 - 1, c - c0 - 1)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value == 4
                and r0 < r < r1
                and c0 < c < c1
            )
        )
    seeds = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    )
    return {
        "grid": grid,
        "h": h,
        "w": w,
        "frame_bbox": frame_bbox,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "pattern": pattern,
        "seeds": seeds,
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
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 11..22")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 11..22")
    if any(
        type(value) is not int or value not in (0, 1, 4, 7)
        for row in coerced
        for value in row
    ):
        errors.append("input values must be integer colors 0, 1, 4, or 7")

    scene = _analyze_scene(coerced)
    frame_bbox = scene["frame_bbox"]
    if frame_bbox is None:
        errors.append("scene must contain one blue frame")
        return errors
    r0, c0, r1, c1 = frame_bbox
    if not (4 <= scene["frame_h"] <= 7):
        errors.append("frame height must be in 4..7")
    if not (4 <= scene["frame_w"] <= 7):
        errors.append("frame width must be in 4..7")
    expected_blue = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    actual_blue = {
        (r, c)
        for r, row in enumerate(coerced)
        for c, value in enumerate(row)
        if value == 1
    }
    if actual_blue != expected_blue:
        errors.append("blue cells must form exactly one complete hollow frame")

    actual_yellow = {
        (r, c)
        for r, row in enumerate(coerced)
        for c, value in enumerate(row)
        if value == 4
    }
    expected_yellow = {
        (r0 + 1 + dr, c0 + 1 + dc)
        for dr, dc in scene["pattern"]
    }
    if actual_yellow != expected_yellow:
        errors.append("all yellow cells must lie strictly inside the frame")
    interior_h = scene["frame_h"] - 2
    interior_w = scene["frame_w"] - 2
    if not scene["pattern"]:
        errors.append("frame must contain a yellow prototype")
    else:
        if (0, 0) not in scene["pattern"]:
            errors.append("prototype must include the top-left anchor")
        if (interior_h - 1, interior_w - 1) not in scene["pattern"]:
            errors.append("prototype must span to the interior bottom-right")
        if not _is_connected(scene["pattern"]):
            errors.append("prototype must be 4-connected")

    if not (_VALID_SEEDS[0] <= len(scene["seeds"]) <= _VALID_SEEDS[1]):
        errors.append("scene must contain exactly 1..4 orange seeds")

    frame_cells = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
    }
    target_sets = []
    for seed_r, seed_c in scene["seeds"]:
        targets = {
            (seed_r + dr, seed_c + dc)
            for dr, dc in scene["pattern"]
        }
        if any(
            not (0 <= r < h and 0 <= c < w)
            for r, c in targets
        ):
            errors.append("every complete stamp must fit inside the grid")
        if targets & frame_cells:
            errors.append("stamp targets must not overlap the source frame")
        if any(targets & prior for prior in target_sets):
            errors.append("stamp target sets must be pairwise disjoint")
        target_sets.append(targets)
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "n_seeds": len(scene["seeds"]),
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    for seed_r, seed_c in scene["seeds"]:
        for dr, dc in scene["pattern"]:
            output[seed_r + dr][seed_c + dc] = 8
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return (
        scene["h"],
        scene["w"],
        scene["frame_h"],
        scene["frame_w"],
        scene["pattern"],
        len(scene["seeds"]),
    )


def _profile_signature(profile):
    h, w, frame_h, frame_w, pattern, n_seeds = profile
    return h, w, frame_h, frame_w, tuple(pattern), n_seeds


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _boxes_separated(first, second):
    return (
        first[2] + 1 < second[0]
        or second[2] + 1 < first[0]
        or first[3] + 1 < second[1]
        or second[3] + 1 < first[1]
    )


def _random_boxes(h, w, frame_h, frame_w, stamp_h, stamp_w, n_seeds, rng):
    frame_options = [
        (r, c, r + frame_h - 1, c + frame_w - 1)
        for r in range(h - frame_h + 1)
        for c in range(w - frame_w + 1)
    ]
    stamp_options = [
        (r, c, r + stamp_h - 1, c + stamp_w - 1)
        for r in range(h - stamp_h + 1)
        for c in range(w - stamp_w + 1)
    ]
    rng.shuffle(frame_options)
    rng.shuffle(stamp_options)
    for frame_box in frame_options:
        stamps = []
        for stamp_box in stamp_options:
            if not _boxes_separated(frame_box, stamp_box):
                continue
            if not all(
                _boxes_separated(stamp_box, prior)
                for prior in stamps
            ):
                continue
            stamps.append(stamp_box)
            if len(stamps) == n_seeds:
                return frame_box, tuple(stamps)
    return None


def _make_pattern(interior_h, interior_w, band, rng):
    r = c = 0
    cells = {(0, 0)}
    while r < interior_h - 1 or c < interior_w - 1:
        moves = []
        if r < interior_h - 1:
            moves.append((r + 1, c))
        if c < interior_w - 1:
            moves.append((r, c + 1))
        r, c = rng.choice(moves)
        cells.add((r, c))
    extra_rate = {
        "easy": 0.12,
        "medium": 0.28,
        "hard": 0.45,
    }[band]
    candidates = [
        (row, col)
        for row in range(interior_h)
        for col in range(interior_w)
        if (row, col) not in cells
        and any(
            (row + dr, col + dc) in cells
            for dr, dc in _CARDINALS
        )
    ]
    rng.shuffle(candidates)
    for cell in candidates:
        if rng.random() < extra_rate:
            cells.add(cell)
    return tuple(sorted(cells))


def _paint_scene(h, w, frame_box, pattern, stamp_boxes):
    grid = full_grid(h, w, 0)
    r0, c0, r1, c1 = frame_box
    draw_frame(grid, r0, c0, r1, c1, 1)
    for dr, dc in pattern:
        grid[r0 + 1 + dr][c0 + 1 + dc] = 4
    for stamp_box in stamp_boxes:
        grid[stamp_box[0]][stamp_box[1]] = 7
    return grid


def _draw_scene(h, w, frame_h, frame_w, pattern, n_seeds, rng):
    placement = _random_boxes(
        h,
        w,
        frame_h,
        frame_w,
        frame_h - 2,
        frame_w - 2,
        n_seeds,
        rng,
    )
    if placement is None:
        return None
    frame_box, stamp_boxes = placement
    return _paint_scene(h, w, frame_box, pattern, stamp_boxes)


def _fallback_scene(h, w, n_seeds):
    frame_box = (0, 0, 4, 3)
    stamp_boxes = (
        (0, 6, 2, 7),
        (4, 6, 6, 7),
        (8, 6, 10, 7),
        (7, 0, 9, 1),
    )[:n_seeds]
    return _paint_scene(
        h,
        w,
        frame_box,
        _PUBLIC_PATTERN,
        stamp_boxes,
    )


def _draw_general(h, w, n_seeds, band, rng):
    frame_ranges = {
        "easy": ((4, 5), (4, 5)),
        "medium": ((4, 6), (4, 6)),
        "hard": ((5, 7), (4, 7)),
    }[band]
    for _ in range(40):
        frame_h = rng.randint(*frame_ranges[0])
        frame_w = rng.randint(*frame_ranges[1])
        pattern = _make_pattern(frame_h - 2, frame_w - 2, band, rng)
        grid = _draw_scene(
            h,
            w,
            frame_h,
            frame_w,
            pattern,
            n_seeds,
            rng,
        )
        if grid is not None:
            return grid
    return _fallback_scene(h, w, n_seeds)


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
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        h, w, frame_h, frame_w, pattern, n_seeds = profile
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("n_seeds", n_seeds, n_seeds)
        grid = _draw_scene(
            h,
            w,
            frame_h,
            frame_w,
            pattern,
            n_seeds,
            ctx.draw_rng("layout"),
        )
        if grid is None:
            grid = _fallback_scene(h, w, n_seeds)
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (11, 14),
                    "medium": (12, 18),
                    "hard": (15, 22),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (11, 14),
                    "medium": (12, 18),
                    "hard": (15, 22),
                }[band],
            )
        if overrides.get("n_seeds") is not None:
            n_seeds = ctx.draw_int("n_seeds", *_VALID_SEEDS)
        else:
            n_seeds = ctx.draw_int(
                "n_seeds",
                *{
                    "easy": (1, 2),
                    "medium": (2, 3),
                    "hard": (3, 4),
                }[band],
            )
        grid = _draw_general(
            h,
            w,
            n_seeds,
            band,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
