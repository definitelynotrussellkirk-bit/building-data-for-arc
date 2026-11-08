"""Generator for ARC task 32597951: recolor inside a cyan bbox.

The input uses background 0, blue 1, and cyan 8.  Cyan cells define a
bounding rectangle.  Every blue cell inside that rectangle becomes green 3;
all cells outside the rectangle and all cyan cells remain unchanged.

Defaults retain all four complete official cyan-mask/count profiles while
varying absolute placement and the nuisance blue layout.  An alternating
complete/gapped lesson schedule guarantees that every five-pair lesson contains
a gap witness even after any one pair is held out as the query.  Generalized
lessons vary the canvas, bbox geometry, cyan density, outside density, and bbox
position without producing identity examples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "113d9bb402d3"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "3b4315aa79fc"
SUMMARY = (
    "Use the bounding box of all cyan (8) cells as a recolor zone; change "
    "blue (1) cells inside it to green (3), preserving every other cell."
)

INVARIANTS = [
    "inputs use only background 0, blue 1, and cyan 8",
    "cyan cells define a 3..9 by 3..9 bounding rectangle",
    "at least one blue cell lies inside and at least one lies outside the bbox",
    "the cyan bbox can be irregular but touches all four sides by definition",
    "only blue cells inside the cyan bbox change to green in the output",
]

CYAN_LEVELS = ("sparse", "balanced", "dense")
ZONE_COVERAGES = ("complete", "gapped")
OUTSIDE_LEVELS = ("sparse", "balanced", "dense")
BBOX_POSITIONS = ("interior", "edge", "corner")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("gapped", "complete")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted draw including official 17",
        "valid": "11..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted draw including official 17",
        "valid": "11..30",
    },
    "bbox_h": {
        "type": "int",
        "default": "difficulty-weighted cyan-bbox height",
        "valid": "3..9",
    },
    "bbox_w": {
        "type": "int",
        "default": "difficulty-weighted cyan-bbox width",
        "valid": "3..9",
    },
    "cyan_level": {
        "type": "str",
        "default": "uniform over three observable density bands",
        "valid": "sparse|balanced|dense",
    },
    "zone_coverage": {
        "type": "str",
        "default": "alternates gapped and complete by sample_index",
        "valid": "complete|gapped",
    },
    "outside_level": {
        "type": "str",
        "default": "difficulty-weighted outside-blue density",
        "valid": "sparse|balanced|dense",
    },
    "bbox_position": {
        "type": "str",
        "default": "interior, edge, or corner",
        "valid": "interior|edge|corner",
    },
}

_INT_DOMAINS = {
    "grid_h": range(11, 31),
    "grid_w": range(11, 31),
    "bbox_h": range(3, 10),
    "bbox_w": range(3, 10),
}
_CHOICE_DOMAINS = {
    "cyan_level": CYAN_LEVELS,
    "zone_coverage": ZONE_COVERAGES,
    "outside_level": OUTSIDE_LEVELS,
    "bbox_position": BBOX_POSITIONS,
}
# Canonical profiles can only occupy complete schedule slots.  A 0.64
# conditional prior therefore preserves the previous ~0.32 pooled exact-profile
# support while reserving every other slot for a gap witness.
_CANONICAL_PRIOR_P = 0.64

# Complete linked profiles extracted independently from the three train inputs
# and held-out input.  Absolute bbox placement and the arrangement of outside
# blue cells are nuisance; their count remains linked to the profile.
# (height, width, normalized cyan mask, inside-blue count, outside-blue count)
_CANONICAL_PROFILES = (
    (
        17,
        17,
        ("8.888888", "8.8...88", "..8..8.8"),
        10,
        97,
    ),
    (
        17,
        17,
        ("88888", "..8..", "88888", ".8...", "88888"),
        8,
        96,
    ),
    (
        17,
        17,
        ("8..8.", ".88.8", "8..8.", ".88.8", "8..8."),
        13,
        129,
    ),
    (
        17,
        17,
        ("8.88.8", "88.88.", ".88.88", "8.88.8"),
        8,
        89,
    ),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)


def _clone(grid):
    return [row[:] for row in grid]


def _validate_call_scalars(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic teaching profile for one production slot."""
    _validate_call_scalars(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _cyan_level(area, count):
    ratio = count / area
    if ratio < 0.53:
        return "sparse"
    if ratio < 0.63:
        return "balanced"
    return "dense"


def _cyan_count(area, level):
    ratio = {"sparse": 0.48, "balanced": 0.58, "dense": 0.68}[level]
    return max(4, min(area - 2, round(ratio * area)))


def _outside_level(available, count):
    ratio = count / available
    if ratio < 0.36:
        return "sparse"
    if ratio < 0.45:
        return "balanced"
    return "dense"


def _outside_count(available, level):
    ratio = {"sparse": 0.32, "balanced": 0.40, "dense": 0.50}[level]
    return max(1, min(available - 1, round(ratio * available)))


def _bbox_position(height, width, box):
    r0, c0, r1, c1 = box
    vertical = r0 == 0 or r1 == height - 1
    horizontal = c0 == 0 or c1 == width - 1
    if vertical and horizontal:
        return "corner"
    if vertical or horizontal:
        return "edge"
    return "interior"


def _analysis(grid):
    """Recover the full semantic profile solely from a returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a nonempty matrix"]}
    height, width = len(grid), len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return {"errors": ["grid must be rectangular"]}

    errors = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in (0, 1, 8)
            ):
                errors.append(
                    f"input cell ({row},{col}) has invalid value {value!r}"
                )
    if errors:
        return {"height": height, "width": width, "errors": errors}

    cyan = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if not cyan:
        return {
            "height": height,
            "width": width,
            "errors": ["no cyan cells define a bbox"],
        }

    r0 = min(row for row, _ in cyan)
    c0 = min(col for _, col in cyan)
    r1 = max(row for row, _ in cyan)
    c1 = max(col for _, col in cyan)
    box = (r0, c0, r1, c1)
    bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
    area = bbox_h * bbox_w
    cyan_count = len(cyan)
    inside_blue = sum(
        grid[row][col] == 1
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
    )
    inside_zero = area - cyan_count - inside_blue
    total_blue = sum(value == 1 for row in grid for value in row)
    outside_blue = total_blue - inside_blue
    outside_available = height * width - area
    mask = tuple(
        "".join(
            "8" if grid[row][col] == 8 else "."
            for col in range(c0, c1 + 1)
        )
        for row in range(r0, r1 + 1)
    )

    if not 11 <= height <= 30:
        errors.append(f"grid height {height} outside 11..30")
    if not 11 <= width <= 30:
        errors.append(f"grid width {width} outside 11..30")
    if not 3 <= bbox_h <= 9:
        errors.append(f"cyan bbox height {bbox_h} outside 3..9")
    if not 3 <= bbox_w <= 9:
        errors.append(f"cyan bbox width {bbox_w} outside 3..9")
    if cyan_count >= area:
        errors.append("cyan bbox leaves no possible recolor cell")
    if inside_blue < 1:
        errors.append("cyan bbox contains no blue cell to recolor")
    if outside_blue < 1:
        errors.append("grid contains no outside-blue preservation witness")

    return {
        "height": height,
        "width": width,
        "box": box,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "mask": mask,
        "cyan_count": cyan_count,
        "inside_blue": inside_blue,
        "inside_zero": inside_zero,
        "outside_blue": outside_blue,
        "outside_available": outside_available,
        "cyan_level": _cyan_level(area, cyan_count),
        "zone_coverage": "complete" if inside_zero == 0 else "gapped",
        "outside_level": _outside_level(outside_available, outside_blue),
        "bbox_position": _bbox_position(height, width, box),
        "errors": errors,
    }


def profile_signature(grid):
    info = _analysis(grid)
    if info["errors"]:
        return None
    return (
        info["height"],
        info["width"],
        info["mask"],
        info["inside_blue"],
        info["outside_blue"],
    )


def canonical_profile_signature(grid):
    signature = profile_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURES else None


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def observe_overrides(grid):
    """Derive every declared exact axis from observable grid structure."""
    info = _analysis(grid)
    if info["errors"]:
        return {}
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "bbox_h": info["bbox_h"],
        "bbox_w": info["bbox_w"],
        "cyan_level": info["cyan_level"],
        "zone_coverage": info["zone_coverage"],
        "outside_level": info["outside_level"],
        "bbox_position": info["bbox_position"],
    }


def rule_mirror(grid):
    """Independent Python mirror: recolor blue inside the cyan bbox."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("invalid cyan-bbox grid: " + "; ".join(info["errors"]))
    r0, c0, r1, c1 = info["box"]
    output = _clone(grid)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if output[row][col] == 1:
                output[row][col] = 3
    return output


def rival_fill_all_noncyan_bbox(grid):
    """Plausible shortcut: fill every non-cyan bbox cell, including gaps."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("invalid cyan-bbox grid: " + "; ".join(info["errors"]))
    r0, c0, r1, c1 = info["box"]
    output = _clone(grid)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if output[row][col] != 8:
                output[row][col] = 3
    return output


CANONICAL_SHORTCUTS = {
    "fill_all_noncyan_bbox": rival_fill_all_noncyan_bbox,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    return [] if is_canonical_profile(grid) else [
        "lawful generalized lesson is not an exact linked canonical profile"
    ]


SEMANTIC_WITNESSES = {
    "gapped_bbox_refutes_fill_all": (
        lambda grid: rule_mirror(grid) != rival_fill_all_noncyan_bbox(grid)
    ),
}
WITNESS_RIVALS = {
    "gapped_bbox_refutes_fill_all": ["fill_all_noncyan_bbox"],
}


def lesson_identifiable(demos, query):
    """Check finite declared-rival ambiguity, including all query rotations."""
    problems = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        problems.append(f"expected at least {EXAMPLES_NEEDED} demonstrations")
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(pairs) - 1 else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            problems.append(f"{label} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            problems.append(f"{label} input is invalid: {exc}")
            continue
        if pair["output"] != expected:
            problems.append(f"{label} output does not match the canonical rule")
    if problems:
        return problems

    return [
        f"{name} fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete bbox-recolor grammar observationally."""
    info = _analysis(grid)
    errors = list(info["errors"])
    requested = (
        (meta or {}).get("overrides", {})
        if isinstance(meta, dict)
        else {}
    )
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def _validate_requested(overrides):
    for name, value in overrides.items():
        if name in _INT_DOMAINS:
            domain = _INT_DOMAINS[name]
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in domain
            ):
                raise ValueError(
                    f"override {name}={value!r} outside "
                    f"{domain.start}..{domain.stop - 1}"
                )
        elif name in _CHOICE_DOMAINS and value not in _CHOICE_DOMAINS[name]:
            raise ValueError(f"unknown {name} {value!r}")


def _difficulty_int_range(name, difficulty):
    if name in ("grid_h", "grid_w"):
        if difficulty == "easy":
            return tuple(range(11, 19))
        if difficulty == "hard":
            return tuple(range(17, 31))
        return tuple(range(14, 25))
    if difficulty == "easy":
        return (3, 4, 5)
    if difficulty == "hard":
        return (4, 5, 6, 7, 8, 9)
    return (3, 4, 5, 6, 7)


def _difficulty_choices(name, difficulty):
    if name == "cyan_level":
        return CYAN_LEVELS
    if name == "zone_coverage":
        if difficulty == "easy":
            return ("complete", "complete", "gapped")
        if difficulty == "hard":
            return ("complete", "gapped", "gapped")
        return ZONE_COVERAGES
    if name == "outside_level":
        if difficulty == "easy":
            return ("sparse", "balanced", "balanced", "dense")
        if difficulty == "hard":
            return ("sparse", "balanced", "dense", "dense")
        return OUTSIDE_LEVELS
    if difficulty == "easy":
        return ("interior", "interior", "edge", "corner")
    if difficulty == "hard":
        return ("interior", "edge", "corner", "corner")
    return BBOX_POSITIONS


def _bbox_origin(rng, height, width, bbox_h, bbox_w, position):
    if position == "interior":
        return (
            rng.randint(1, height - bbox_h - 1),
            rng.randint(1, width - bbox_w - 1),
        )
    if position == "corner":
        return (
            rng.choice((0, height - bbox_h)),
            rng.choice((0, width - bbox_w)),
        )
    side = rng.choice(("top", "bottom", "left", "right"))
    if side in ("top", "bottom"):
        return (
            0 if side == "top" else height - bbox_h,
            rng.randint(1, width - bbox_w - 1),
        )
    return (
        rng.randint(1, height - bbox_h - 1),
        0 if side == "left" else width - bbox_w,
    )


def _cyan_positions(rng, bbox_h, bbox_w, count):
    positions = [(row, col) for row in range(bbox_h) for col in range(bbox_w)]
    for _attempt in range(512):
        chosen = set(rng.sample(positions, count))
        rows = {row for row, _ in chosen}
        cols = {col for _, col in chosen}
        if 0 in rows and bbox_h - 1 in rows and 0 in cols and bbox_w - 1 in cols:
            return chosen
    raise ValueError("could not construct cyan mask with the requested bbox")


def _record_axes(ctx, values):
    ctx.overrides.update(values)
    observed = {}
    for name in ("grid_h", "grid_w", "bbox_h", "bbox_w"):
        observed[name] = ctx.draw_int(name, values[name], values[name])
    for name in (
        "cyan_level",
        "zone_coverage",
        "outside_level",
        "bbox_position",
    ):
        observed[name] = ctx.draw_choice(name, (values[name],))
    if observed != values:
        raise AssertionError("axis provenance changed the planned lesson")


def _render_general(ctx, values):
    height, width = values["grid_h"], values["grid_w"]
    bbox_h, bbox_w = values["bbox_h"], values["bbox_w"]
    layout_rng = ctx.draw_rng("layout")
    r0, c0 = _bbox_origin(
        layout_rng,
        height,
        width,
        bbox_h,
        bbox_w,
        values["bbox_position"],
    )
    area = bbox_h * bbox_w
    cyan_count = _cyan_count(area, values["cyan_level"])
    cyan = _cyan_positions(layout_rng, bbox_h, bbox_w, cyan_count)
    zone_free = [
        (row, col)
        for row in range(bbox_h)
        for col in range(bbox_w)
        if (row, col) not in cyan
    ]
    if values["zone_coverage"] == "complete":
        zone_blue = zone_free
    else:
        count = layout_rng.randint(1, len(zone_free) - 1)
        zone_blue = layout_rng.sample(zone_free, count)

    grid = full_grid(height, width, 0)
    for row, col in cyan:
        grid[r0 + row][c0 + col] = 8
    for row, col in zone_blue:
        grid[r0 + row][c0 + col] = 1

    outside = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if not (r0 <= row < r0 + bbox_h and c0 <= col < c0 + bbox_w)
    ]
    outside_count = _outside_count(len(outside), values["outside_level"])
    for row, col in layout_rng.sample(outside, outside_count):
        grid[row][col] = 1
    return grid


def _render_profile(ctx, profile):
    height, width, mask, _inside_blue, outside_blue = profile
    bbox_h, bbox_w = len(mask), len(mask[0])
    layout_rng = ctx.draw_rng("layout")
    r0, c0 = _bbox_origin(
        layout_rng, height, width, bbox_h, bbox_w, "interior"
    )
    grid = full_grid(height, width, 0)
    for row, pattern in enumerate(mask):
        for col, value in enumerate(pattern):
            grid[r0 + row][c0 + col] = 8 if value == "8" else 1
    outside = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if not (r0 <= row < r0 + bbox_h and c0 <= col < c0 + bbox_w)
    ]
    for row, col in layout_rng.sample(outside, outside_blue):
        grid[row][col] = 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_scalars(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    _validate_requested(overrides)
    requested = dict(overrides)
    scheduled_coverage = schedule_profile(seed, sample_index, difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    use_profile = (
        not requested
        and scheduled_coverage == "complete"
        and ctx.draw_rng("canonical_prior").random() < _CANONICAL_PRIOR_P
    )

    if use_profile:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        grid = _render_profile(ctx, profile)
        values = observe_overrides(grid)
    else:
        planner = ctx.draw_rng("planner")
        values = {}
        for name in ("grid_h", "grid_w", "bbox_h", "bbox_w"):
            values[name] = requested.get(
                name,
                planner.choice(_difficulty_int_range(name, difficulty)),
            )
        for name in (
            "cyan_level",
            "outside_level",
            "bbox_position",
        ):
            values[name] = requested.get(
                name,
                planner.choice(_difficulty_choices(name, difficulty)),
            )
        values["zone_coverage"] = requested.get(
            "zone_coverage", scheduled_coverage
        )
        grid = _render_general(ctx, values)

    if not values:
        raise ValueError("could not recover axes from canonical-profile lesson")
    _record_axes(ctx, values)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": requested},
    )
    if errors:
        raise ValueError("constructed invalid cyan-bbox grid: " + "; ".join(errors))
    return _clone(grid)
