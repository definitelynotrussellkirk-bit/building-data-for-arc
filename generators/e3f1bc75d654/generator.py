"""Generator for ARC task e3f1bc75d654.

A scene contains several one-cell-thick rectangular frames in distinct colors.
Exactly one frame contains a non-empty pattern of cells in its own interior.
The Racket oracle keeps that template and every empty frame with the same
interior dimensions, stamps the template's relative pattern into each retained
frame using that frame's color, and erases every differently sized frame.

The public axes below are deliberately limited to quantities recoverable from a
returned grid.  Joint values are selected from a feasible domain before any
axis is recorded, so exact overrides are honored without clamping, retries, or
an override-blind fallback.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "e3f1bc75d654"
TASK_ID = "e3f1bc75d654"
VERSION = "5.1.0"  # strict controls + source-bound semantic teaching contract
RULE_HASH = "0ac13a729d1a"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "A 0-background grid contains 2-4 same-size rectangular frames and 1-3 "
    "differently sized distractor frames, all in distinct colors and separated "
    "by background. Exactly one same-size frame is the template: its interior "
    "contains a non-empty, non-solid pattern in its own color. The oracle keeps "
    "all frames matching the template's interior height and width, copies the "
    "relative pattern into each in that frame's color, and erases every "
    "mismatched frame."
)

INVARIANTS = [
    "the background is 0 and every frame has a distinct non-zero color",
    "exactly one frame has a non-empty, non-solid interior pattern",
    "2-4 frames share the template's exact interior dimensions",
    "1-3 empty distractor frames have other interior dimensions",
    "frames do not overlap or touch, and every normal draw changes under the rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-linked feasible joint draw",
        "valid": "10..28",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-linked feasible joint draw",
        "valid": "10..28",
        "doc": "Exact returned grid width.",
    },
    "frame_h": {
        "type": "int",
        "default": "difficulty-linked feasible joint draw",
        "valid": "4..8",
        "doc": "Exact outer height of the template and all matching frames.",
    },
    "frame_w": {
        "type": "int",
        "default": "difficulty-linked feasible joint draw",
        "valid": "4..8",
        "doc": "Exact outer width of the template and all matching frames.",
    },
    "n_match": {
        "type": "int",
        "default": "2-3 easy / 3-4 medium-hard",
        "valid": "2..4",
        "doc": "Exact count of template-size frames, including the template.",
    },
    "n_distract": {
        "type": "int",
        "default": "1 easy / 1-2 medium / 2-3 hard",
        "valid": "1..3",
        "doc": "Exact count of differently sized empty frames.",
    },
    "template_color": {
        "type": "color",
        "default": "rng non-zero color",
        "valid": "1..9",
        "doc": "Exact color of the sole patterned template frame.",
    },
}

_INT_RANGES = {
    "grid_h": (10, 28),
    "grid_w": (10, 28),
    "frame_h": (4, 8),
    "frame_w": (4, 8),
    "n_match": (2, 4),
    "n_distract": (1, 3),
    "template_color": (1, 9),
}
_LAYOUT_AXES = ("grid_h", "grid_w", "frame_h", "frame_w", "n_match", "n_distract")

# Default-only complete linked-profile prior (KRF-0003/KRF-0004).  Each
# archetype was extracted executable-first from every unique canonical input.
# Palette and D2 canvas symmetry are nuisance variations; canvas dimensions,
# frame-size linkage, distractor-size multiset, and template morphology remain
# one intact official profile.  Any explicit axis override bypasses this branch.
#
# Even sample-index slots are reserved for a generated counterexample to the
# canonical-fitting "leftmost frame sets the kept size" shortcut.  The prior is
# therefore sampled at 60% on the remaining half of the schedule, retaining an
# effective 30% default prior while making every four-pair lesson teach the rule.
_CANONICAL_PRIOR_RATE = 0.60
LESSON_SCHEDULE_PERIOD = 2
EXAMPLES_NEEDED = 3
_CANONICAL_ARCHETYPES = (
    {
        "grid": (21, 21),
        "frames": (
            {"bbox": (1, 7, 6, 11), "kind": "receiver"},
            {"bbox": (2, 16, 7, 20), "kind": "receiver"},
            {"bbox": (7, 1, 12, 5), "kind": "receiver"},
            {"bbox": (11, 11, 16, 15), "kind": "template"},
            {"bbox": (16, 3, 19, 7), "kind": "distractor"},
        ),
        "pattern": ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2), (3, 0)),
    },
    {
        "grid": (19, 19),
        "frames": (
            {"bbox": (1, 1, 7, 8), "kind": "template"},
            {"bbox": (2, 11, 8, 18), "kind": "receiver"},
            {"bbox": (11, 3, 17, 10), "kind": "receiver"},
            {"bbox": (11, 13, 15, 17), "kind": "distractor"},
        ),
        "pattern": (
            (0, 5), (1, 1), (1, 2), (2, 0), (2, 1), (2, 3),
            (2, 4), (3, 2), (3, 3), (3, 5), (4, 4),
        ),
    },
    {
        "grid": (22, 22),
        "frames": (
            {"bbox": (1, 5, 6, 11), "kind": "receiver"},
            {"bbox": (3, 16, 6, 19), "kind": "distractor"},
            {"bbox": (8, 0, 13, 6), "kind": "template"},
            {"bbox": (12, 11, 17, 17), "kind": "receiver"},
            {"bbox": (15, 2, 21, 7), "kind": "distractor"},
        ),
        "pattern": (
            (0, 1), (1, 0), (1, 1), (1, 3), (1, 4),
            (2, 1), (2, 2), (2, 3), (2, 4), (3, 3),
        ),
    },
    {
        "grid": (23, 22),
        "frames": (
            {"bbox": (1, 12, 6, 21), "kind": "distractor"},
            {"bbox": (2, 2, 6, 9), "kind": "receiver"},
            {"bbox": (8, 11, 12, 18), "kind": "receiver"},
            {"bbox": (12, 1, 16, 8), "kind": "template"},
            {"bbox": (14, 15, 19, 20), "kind": "distractor"},
            {"bbox": (18, 4, 21, 12), "kind": "distractor"},
        ),
        "pattern": (
            (0, 1), (0, 2), (0, 5), (1, 0), (1, 1), (1, 3),
            (1, 4), (1, 5), (2, 1), (2, 2), (2, 3),
        ),
    },
)

_BAND_PREFS = {
    "easy": {
        "grid_h": range(10, 19),
        "grid_w": range(10, 19),
        "frame_h": range(4, 7),
        "frame_w": range(4, 7),
        "n_match": range(2, 4),
        "n_distract": (1,),
    },
    "medium": {
        "grid_h": range(16, 24),
        "grid_w": range(16, 24),
        "frame_h": range(5, 9),
        "frame_w": range(5, 9),
        "n_match": range(3, 5),
        "n_distract": range(1, 3),
    },
    "hard": {
        "grid_h": range(20, 29),
        "grid_w": range(20, 29),
        "frame_h": range(5, 9),
        "frame_w": range(5, 9),
        "n_match": range(3, 5),
        "n_distract": range(2, 4),
    },
}


def _validate_call_arguments(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an exact integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _normalize_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if type(difficulty) is not str or difficulty not in _BAND_PREFS:
        raise ValueError("difficulty must be 'easy', 'medium', 'hard', or None")
    return difficulty


def _read_int_override(overrides: dict[str, Any], name: str, lo: int, hi: int) -> int | None:
    if name not in overrides or overrides[name] is None:
        return None
    raw = overrides[name]
    if isinstance(raw, bool):
        raise ValueError(f"{name} override must be an integer, not bool")
    if type(raw) is not int:
        raise TypeError(f"{name} override must be an exact integer")
    if not lo <= raw <= hi:
        raise ValueError(f"{name} override {raw} outside [{lo}, {hi}]")
    return raw


def _slot_capacity(h: int, w: int, frame_h: int, frame_w: int) -> int:
    """Guaranteed capacity with one blank row/column between max-size slots."""
    return ((h + 1) // (frame_h + 1)) * ((w + 1) // (frame_w + 1))


@lru_cache(maxsize=None)
def _feasible_specs(
    band: str,
    requested_values: tuple[int | None, ...],
) -> tuple[tuple[int, int, int, int, int, int], ...]:
    """Return joint values that have a constructive separated-frame layout."""
    requested = dict(zip(_LAYOUT_AXES, requested_values))
    domains = {
        name: (
            (requested[name],)
            if requested[name] is not None
            else range(_INT_RANGES[name][0], _INT_RANGES[name][1] + 1)
        )
        for name in _LAYOUT_AXES
    }
    all_candidates: list[tuple[int, int, int, int, int, int]] = []
    preferred: list[tuple[int, int, int, int, int, int]] = []
    prefs = _BAND_PREFS[band]

    for h, w, fh, fw, n_match, n_distract in product(
        domains["grid_h"],
        domains["grid_w"],
        domains["frame_h"],
        domains["frame_w"],
        domains["n_match"],
        domains["n_distract"],
    ):
        if _slot_capacity(h, w, fh, fw) < n_match + n_distract:
            continue
        candidate = (h, w, fh, fw, n_match, n_distract)
        all_candidates.append(candidate)
        if all(
            requested[name] is not None or value in prefs[name]
            for name, value in zip(_LAYOUT_AXES, candidate)
        ):
            # Canonical templates are rectangular, and a non-square template
            # admits an equal-area transposed distractor. That witness directly
            # rebuts area-only largest/smallest shortcuts on ordinary one-decoy
            # lessons. Explicit square overrides remain fully supported.
            explicit_square = (
                requested.get("frame_h") is not None
                and requested.get("frame_w") is not None
                and requested["frame_h"] == requested["frame_w"]
            )
            if fh == fw and not explicit_square:
                continue
            if (
                n_distract == 1
                and fh != fw
                and _slot_capacity(h, w, max(fh, fw), max(fh, fw))
                < n_match + n_distract
            ):
                continue
            preferred.append(candidate)

    return tuple(preferred or all_candidates)


def _choose_scene_spec(ctx, band: str, requested: dict[str, int | None]):
    key = tuple(requested[name] for name in _LAYOUT_AXES)
    candidates = _feasible_specs(band, key)
    if not candidates:
        explicit = ", ".join(
            f"{name}={requested[name]}"
            for name in _LAYOUT_AXES
            if requested[name] is not None
        )
        raise ValueError(
            "incompatible overrides: no separated layout can realize "
            f"the requested frame counts and dimensions in a 10..28 grid ({explicit})"
        )
    chosen = ctx.draw_rng("scene_spec").choice(candidates)
    realized = {}
    for name, value in zip(_LAYOUT_AXES, chosen):
        realized[name] = ctx.draw_int(name, value, value)
    return realized


def _apply_canvas_symmetry(grid, symmetry: str):
    if symmetry == "identity":
        return [row[:] for row in grid]
    if symmetry == "hflip":
        return [list(reversed(row)) for row in grid]
    if symmetry == "vflip":
        return [row[:] for row in reversed(grid)]
    if symmetry == "rot180":
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError(f"unknown canvas symmetry {symmetry!r}")


def _draw_canonical_archetype(ctx):
    """Return one complete official linked profile with nuisance variation.

    The early-return branch records every public axis under its normal keyed
    provenance label before construction.  It is entered only when no exact
    override is active, so it cannot make caller controls inert.
    """
    archetype = ctx.draw_rng("canonical_archetype").choice(_CANONICAL_ARCHETYPES)
    template = next(frame for frame in archetype["frames"] if frame["kind"] == "template")
    tr0, tc0, tr1, tc1 = template["bbox"]
    realized = {
        "grid_h": archetype["grid"][0],
        "grid_w": archetype["grid"][1],
        "frame_h": tr1 - tr0 + 1,
        "frame_w": tc1 - tc0 + 1,
        "n_match": sum(frame["kind"] != "distractor" for frame in archetype["frames"]),
        "n_distract": sum(frame["kind"] == "distractor" for frame in archetype["frames"]),
    }
    for name in _LAYOUT_AXES:
        ctx.draw_int(name, realized[name], realized[name])
    template_color = ctx.draw_int("template_color", 1, 9)

    other_colors = ctx.draw_rng("canonical_colors").sample(
        [color for color in range(1, 10) if color != template_color],
        len(archetype["frames"]) - 1,
    )
    color_iter = iter(other_colors)
    grid = full_grid(*archetype["grid"], 0)
    for frame in archetype["frames"]:
        color = template_color if frame["kind"] == "template" else next(color_iter)
        r0, c0, r1, c1 = frame["bbox"]
        draw_frame(grid, r0, c0, r1, c1, color)
        if frame["kind"] == "template":
            for dr, dc in archetype["pattern"]:
                grid[r0 + 1 + dr][c0 + 1 + dc] = color

    symmetry = ctx.draw_rng("canonical_symmetry").choice(
        ("identity", "hflip", "vflip", "rot180")
    )
    return _apply_canvas_symmetry(grid, symmetry)


def _shape_category(shape: tuple[int, int], base: tuple[int, int]) -> str:
    h, w = shape
    bh, bw = base
    if h <= bh and w <= bw:
        return "smaller"
    if h >= bh and w >= bw:
        return "larger"
    return "crossed"


def _choose_distractor_shapes(
    rng,
    *,
    h: int,
    w: int,
    frame_h: int,
    frame_w: int,
    total: int,
    count: int,
) -> list[tuple[int, int]]:
    """Choose distinct mismatched sizes while preserving a guaranteed layout.

    Preference rotates through smaller/larger/crossed shapes.  This prevents a
    corpus shortcut such as "always erase the smallest frame" while keeping
    every selected set constructively packable.
    """
    base = (frame_h, frame_w)
    if count == 1 and frame_h != frame_w:
        transposed = (frame_w, frame_h)
        slot_h = max(frame_h, transposed[0])
        slot_w = max(frame_w, transposed[1])
        if _slot_capacity(h, w, slot_h, slot_w) >= total:
            return [transposed]

    all_shapes = [
        (shape_h, shape_w)
        for shape_h in range(3, min(10, h) + 1)
        for shape_w in range(3, min(10, w) + 1)
        if (shape_h, shape_w) != base
    ]
    rng.shuffle(all_shapes)
    categories = {
        name: [shape for shape in all_shapes if _shape_category(shape, base) == name]
        for name in ("smaller", "larger", "crossed")
    }
    category_orders = [
        ("smaller", "larger", "crossed"),
        ("larger", "smaller", "crossed"),
    ]
    order = list(category_orders[rng.randrange(len(category_orders))])
    targets = [order[index % len(order)] for index in range(count)]

    selected: list[tuple[int, int]] = []
    max_h, max_w = frame_h, frame_w
    for target in targets:
        pools = [categories[target], all_shapes]
        choice = None
        for pool in pools:
            for shape in pool:
                if shape in selected:
                    continue
                next_h = max(max_h, shape[0])
                next_w = max(max_w, shape[1])
                if _slot_capacity(h, w, next_h, next_w) >= total:
                    choice = shape
                    break
            if choice is not None:
                break
        if choice is None:
            raise ValueError("internal layout error: no feasible distractor shape")
        selected.append(choice)
        max_h = max(max_h, choice[0])
        max_w = max(max_w, choice[1])
    return selected


def _distributed_origins(rng, length: int, slot_size: int, count: int) -> list[int]:
    """Randomized slot origins with at least one blank cell between slots."""
    used = count * slot_size + max(0, count - 1)
    slack = length - used
    if slack < 0:
        raise ValueError("internal layout error: slot partition does not fit")
    extras = [0] * (count + 1)
    for _ in range(slack):
        extras[rng.randrange(count + 1)] += 1
    origins: list[int] = []
    cursor = extras[0]
    for index in range(count):
        origins.append(cursor)
        if index + 1 < count:
            cursor += slot_size + 1 + extras[index + 1]
    return origins


def _build_roles(
    rng,
    *,
    n_match: int,
    distractor_shapes: list[tuple[int, int]],
    frame_h: int,
    frame_w: int,
) -> list[dict[str, Any]]:
    roles = [
        {"kind": "template", "shape": (frame_h, frame_w)},
        *[
            {"kind": "receiver", "shape": (frame_h, frame_w)}
            for _ in range(n_match - 1)
        ],
        *[
            {"kind": "distractor", "shape": shape}
            for shape in distractor_shapes
        ],
    ]
    rng.shuffle(roles)
    return roles


def _place_roles(
    rng,
    *,
    h: int,
    w: int,
    roles: list[dict[str, Any]],
    force_leftmost_distractor: bool = False,
) -> list[dict[str, Any]]:
    slot_h = max(role["shape"][0] for role in roles)
    slot_w = max(role["shape"][1] for role in roles)
    row_count = (h + 1) // (slot_h + 1)
    col_count = (w + 1) // (slot_w + 1)
    slots = list(product(range(row_count), range(col_count)))
    if len(slots) < len(roles):
        raise ValueError("internal layout error: chosen shapes exceed scene capacity")

    row_origins = _distributed_origins(rng, h, slot_h, row_count)
    col_origins = _distributed_origins(rng, w, slot_w, col_count)
    if force_leftmost_distractor:
        target = (0, 0)
        remaining_slots = [slot for slot in slots if slot != target]
        selected_slots = [target, *rng.sample(remaining_slots, len(roles) - 1)]
        distractor_index = next(
            index for index, role in enumerate(roles) if role["kind"] == "distractor"
        )
        ordered_roles = [roles[distractor_index], *roles[:distractor_index], *roles[distractor_index + 1 :]]
    else:
        selected_slots = rng.sample(slots, len(roles))
        ordered_roles = roles

    placed: list[dict[str, Any]] = []
    for index, (role, (slot_row, slot_col)) in enumerate(zip(ordered_roles, selected_slots)):
        role_h, role_w = role["shape"]
        if force_leftmost_distractor and index == 0:
            # Pin the distractor to the upper-left corner of the first slot.
            # Every other selected slot is lexicographically later, so this is
            # unambiguously the leftmost frame under (column, row) ordering.
            r0 = row_origins[slot_row]
            c0 = col_origins[slot_col]
        else:
            r0 = row_origins[slot_row] + rng.randint(0, slot_h - role_h)
            c0 = col_origins[slot_col] + rng.randint(0, slot_w - role_w)
        placed.append({**role, "r0": r0, "c0": c0})
    return placed


def _pattern_cells(rng, frame_h: int, frame_w: int, band: str) -> list[tuple[int, int]]:
    interior = list(product(range(frame_h - 2), range(frame_w - 2)))
    area = len(interior)
    if band == "easy":
        lo, hi = 1, max(1, min(area - 1, (area + 2) // 3))
    elif band == "hard":
        lo, hi = max(2, area // 3), area - 1
    else:
        lo, hi = max(2, area // 4), max(2, min(area - 1, (2 * area) // 3))
    count = rng.randint(lo, hi)
    selected = rng.sample(interior, count)
    boundary = [
        cell
        for cell in interior
        if cell[0] in (0, frame_h - 3) or cell[1] in (0, frame_w - 3)
    ]
    # The canonical Racket rule discovers frames by 4-connected color
    # components. At least one interior mark must touch the outline component
    # or the otherwise valid-looking pattern would be invisible as a template.
    if not any(cell in boundary for cell in selected):
        selected[rng.randrange(len(selected))] = rng.choice(boundary)
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one lawful input grid; the Racket program remains output authority."""
    _validate_call_arguments(seed, sample_index)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _normalize_difficulty(difficulty)
    requested = {
        name: _read_int_override(overrides, name, lo, hi)
        for name, (lo, hi) in _INT_RANGES.items()
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    has_explicit_override = any(
        name in overrides and overrides[name] is not None for name in AXES
    )
    force_leftmost_distractor = sample_index % LESSON_SCHEDULE_PERIOD == 0
    if (
        not force_leftmost_distractor
        and not has_explicit_override
        and ctx.draw_rng("canonical_prior").random() < _CANONICAL_PRIOR_RATE
    ):
        return _draw_canonical_archetype(ctx)

    spec = _choose_scene_spec(ctx, band, requested)
    template_color = ctx.draw_int("template_color", 1, 9)

    h, w = spec["grid_h"], spec["grid_w"]
    frame_h, frame_w = spec["frame_h"], spec["frame_w"]
    n_match, n_distract = spec["n_match"], spec["n_distract"]
    total = n_match + n_distract

    shape_rng = ctx.draw_rng("distractor_shapes")
    distractor_shapes = _choose_distractor_shapes(
        shape_rng,
        h=h,
        w=w,
        frame_h=frame_h,
        frame_w=frame_w,
        total=total,
        count=n_distract,
    )
    roles = _build_roles(
        ctx.draw_rng("role_order"),
        n_match=n_match,
        distractor_shapes=distractor_shapes,
        frame_h=frame_h,
        frame_w=frame_w,
    )
    placed = _place_roles(
        ctx.draw_rng("layout"),
        h=h,
        w=w,
        roles=roles,
        force_leftmost_distractor=force_leftmost_distractor,
    )

    other_colors = ctx.draw_rng("colors").sample(
        [color for color in range(1, 10) if color != template_color],
        total - 1,
    )
    color_iter = iter(other_colors)
    for role in placed:
        role["color"] = template_color if role["kind"] == "template" else next(color_iter)

    grid = full_grid(h, w, 0)
    for role in placed:
        r0, c0 = role["r0"], role["c0"]
        role_h, role_w = role["shape"]
        draw_frame(grid, r0, c0, r0 + role_h - 1, c0 + role_w - 1, role["color"])

    template = next(role for role in placed if role["kind"] == "template")
    pattern = _pattern_cells(ctx.draw_rng("pattern"), frame_h, frame_w, band)
    for dr, dc in pattern:
        grid[template["r0"] + 1 + dr][template["c0"] + 1 + dc] = template_color
    return grid


def _rectangles_touch_or_overlap(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    rows_separated = lr1 + 1 < rr0 or rr1 + 1 < lr0
    cols_separated = lc1 + 1 < rc0 or rc1 + 1 < lc0
    return not (rows_separated or cols_separated)


def _analyze_scene(grid) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"errors": errors, "frames": []}
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a non-empty list")
        return result
    if not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid rows must be non-empty lists")
        return result
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer colors 0..9")
        return result

    h, w = len(grid), width
    result.update({"grid_h": h, "grid_w": w})
    if not 10 <= h <= 28 or not 10 <= w <= 28:
        errors.append(f"grid dimensions {h}x{w} outside 10..28")

    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                by_color.setdefault(color, []).append((r, c))
    if not 3 <= len(by_color) <= 7:
        errors.append(f"expected 3..7 distinct non-zero frame colors, found {len(by_color)}")

    frames: list[dict[str, Any]] = []
    for color, cells in sorted(by_color.items()):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        if frame_h < 3 or frame_w < 3:
            errors.append(f"color {color} does not form a frame: bbox {frame_h}x{frame_w}")
            continue
        border = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        ]
        missing = [(r, c) for r, c in border if grid[r][c] != color]
        if missing:
            errors.append(f"color {color} has an incomplete rectangular border")
            continue
        foreign = [
            (r, c, grid[r][c])
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, color)
        ]
        if foreign:
            errors.append(f"color {color} frame contains a foreign interior color")
            continue
        pattern = [
            (r - r0 - 1, c - c0 - 1)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] == color
        ]
        frames.append(
            {
                "color": color,
                "bbox": (r0, c0, r1, c1),
                "frame_h": frame_h,
                "frame_w": frame_w,
                "interior": (frame_h - 2, frame_w - 2),
                "pattern": pattern,
                "pattern_count": len(pattern),
            }
        )
    result["frames"] = frames
    if len(frames) != len(by_color):
        return result

    for index, left in enumerate(frames):
        for right in frames[index + 1 :]:
            if _rectangles_touch_or_overlap(left["bbox"], right["bbox"]):
                errors.append(
                    f"frames {left['color']} and {right['color']} touch or overlap"
                )

    templates = [frame for frame in frames if frame["pattern_count"] > 0]
    result["templates"] = templates
    if len(templates) != 1:
        errors.append(f"expected exactly one patterned template, found {len(templates)}")
        return result
    template = templates[0]
    result["template"] = template
    interior_area = template["interior"][0] * template["interior"][1]
    if template["pattern_count"] >= interior_area:
        errors.append("template interior pattern must leave at least one background cell")
    interior_h, interior_w = template["interior"]
    if not any(
        dr in (0, interior_h - 1) or dc in (0, interior_w - 1)
        for dr, dc in template["pattern"]
    ):
        errors.append(
            "template pattern must touch its frame component through an interior edge cell"
        )

    matching = [frame for frame in frames if frame["interior"] == template["interior"]]
    distractors = [frame for frame in frames if frame["interior"] != template["interior"]]
    result["matching"] = matching
    result["distractors"] = distractors
    if not 2 <= len(matching) <= 4:
        errors.append(f"expected 2..4 template-size frames, found {len(matching)}")
    if not 1 <= len(distractors) <= 3:
        errors.append(f"expected 1..3 mismatched distractors, found {len(distractors)}")
    patterned_receivers = [
        frame for frame in matching if frame is not template and frame["pattern_count"]
    ]
    if patterned_receivers:
        errors.append("same-size receiver frames must start with empty interiors")
    patterned_distractors = [frame for frame in distractors if frame["pattern_count"]]
    if patterned_distractors:
        errors.append("distractor frames must start with empty interiors")
    if not 4 <= template["frame_h"] <= 8 or not 4 <= template["frame_w"] <= 8:
        errors.append(
            f"template outer dimensions {template['frame_h']}x{template['frame_w']} outside 4..8"
        )

    result["observed"] = {
        "grid_h": h,
        "grid_w": w,
        "frame_h": template["frame_h"],
        "frame_w": template["frame_w"],
        "n_match": len(matching),
        "n_distract": len(distractors),
        "template_color": template["color"],
    }
    return result


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a valid returned grid."""
    analysis = _analyze_scene(grid)
    return dict(analysis.get("observed") or {})


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, touching, or rule-hiding lesson scenes."""
    analysis = _analyze_scene(grid)
    errors = list(analysis["errors"])
    observed = analysis.get("observed") or {}
    if isinstance(meta, dict):
        explicit = meta.get("overrides")
        if not isinstance(explicit, dict):
            explicit = meta
        for axis in AXES:
            if axis not in explicit or explicit[axis] is None:
                continue
            requested = explicit[axis]
            if axis in _INT_RANGES:
                try:
                    requested = int(requested)
                except (TypeError, ValueError):
                    pass
            if observed.get(axis) != requested:
                errors.append(
                    f"{axis} requested {requested!r}, observed {observed.get(axis)!r}"
                )
    return errors


def rule_mirror(grid):
    """Python test mirror only; production outputs remain Racket-authoritative."""
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid lesson scene: " + "; ".join(analysis["errors"]))
    template = analysis["template"]
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for frame in analysis["matching"]:
        r0, c0, r1, c1 = frame["bbox"]
        draw_frame(output, r0, c0, r1, c1, frame["color"])
        for dr, dc in template["pattern"]:
            output[r0 + 1 + dr][c0 + 1 + dc] = frame["color"]
    return output



def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid falls outside the selected lesson grammar."""
    return self_check(grid)


def _leftmost_frame_shortcut(grid):
    """Plausible wrong rule: use the leftmost frame as the size template.

    The canonical examples happen to put a template-sized frame furthest left.
    This rival still copies the sole visible pattern, but retains the frames
    matching the leftmost frame rather than those matching the patterned frame.
    Pattern cells outside a smaller receiver are clipped deterministically.
    """
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid lesson scene: " + "; ".join(analysis["errors"]))
    template = analysis["template"]
    selected = min(
        analysis["frames"],
        key=lambda frame: (frame["bbox"][1], frame["bbox"][0], frame["color"]),
    )
    interior_h, interior_w = selected["interior"]
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for frame in analysis["frames"]:
        if frame["interior"] != selected["interior"]:
            continue
        r0, c0, r1, c1 = frame["bbox"]
        draw_frame(output, r0, c0, r1, c1, frame["color"])
        for dr, dc in template["pattern"]:
            if 0 <= dr < interior_h and 0 <= dc < interior_w:
                output[r0 + 1 + dr][c0 + 1 + dc] = frame["color"]
    return output


def _leftmost_frame_is_distractor(grid) -> bool:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        return False
    leftmost = min(
        analysis["frames"],
        key=lambda frame: (frame["bbox"][1], frame["bbox"][0], frame["color"]),
    )
    return leftmost["interior"] != analysis["template"]["interior"]


SEMANTIC_WITNESSES = {
    "leftmost_frame_is_distractor": _leftmost_frame_is_distractor,
}
SEMANTIC_RIVALS = {
    "leftmost_frame_sets_size": _leftmost_frame_shortcut,
}
WITNESS_RIVALS = {
    "leftmost_frame_is_distractor": ["leftmost_frame_sets_size"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute the canonical-fitting leftmost rival."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    errors: list[str] = []
    for label, pair in [
        *((f"demo {index}", pair) for index, pair in enumerate(demos)),
        ("query", query),
    ]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"{label} must contain input and output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            errors.append(f"{label} is outside the grammar: {grammar[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"{label} output disagrees with the selected rule")

    if not errors and all(
        _leftmost_frame_shortcut(pair["input"]) == pair["output"] for pair in demos
    ):
        errors.append("surviving lesson shortcut: leftmost_frame_sets_size")
    return errors
