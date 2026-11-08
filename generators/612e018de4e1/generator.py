"""Generator for bank puzzle E92 — complete a blue rectangle corner.

Rule: exactly three blue cells occupy three corners of one axis-aligned
rectangle.  Add red at the missing fourth corner and preserve every other
cell, including unrelated non-blue distractor objects.

The five canonical inputs couple canvas dimensions, rectangle span, palette
size, and distractor morphology.  Default draws select one complete linked
profile first, then vary only lawful nuisance factors: translation, missing
corner, distractor side, distractor colors, and orientation.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "612e018de4e1"
VERSION = "3.0.0"
TASK_ID = "612e018de4e1"
RULE_HASH = "37cf42b8d83e"
SUMMARY = (
    "A zero-background grid contains exactly three blue cells at three "
    "corners of one axis-aligned rectangle plus one or two unrelated "
    "non-blue distractor objects. Infer the empty fourth rectangle corner "
    "and paint only that cell red; preserve all clues and distractors."
)

INVARIANTS = [
    "background is 0 and red (2) is absent from the input",
    "exactly three blue cells occupy three corners of one rectangle",
    "the implied fourth corner is empty",
    "distractors are non-blue objects outside the rectangle bounding box",
    "the linked canvas/span/distractor profile matches an official example",
]

EXAMPLES_NEEDED = 3

# (height, width, row gap, column gap, distractor morphology)
# Morphology is quotiented by rotation/reflection: ``one_l`` is one connected
# 3-cell L in a 2x2 box; ``two_small`` is one singleton and one domino in
# distinct colors.  These are derived from all four train inputs and the test.
SCENE_PROFILES = {
    "p8x9_two_small": (8, 9, 3, 4, "two_small"),
    "p9x10_two_small": (9, 10, 4, 5, "two_small"),
    "p10x10_one_l": (10, 10, 6, 4, "one_l"),
    "p9x11_one_l": (9, 11, 4, 8, "one_l"),
    "p10x12_two_small": (10, 12, 6, 7, "two_small"),
}
_SCENE_NAMES = tuple(SCENE_PROFILES)
_MISSING_CORNERS = ("tl", "tr", "bl", "br")
_DISTRACTOR_SIDES = ("top", "bottom", "left", "right")
_PALETTE_BANDS = ("low", "high")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete canonical profile",
        "valid": "p8x9_two_small|p9x10_two_small|p10x10_one_l|p9x11_one_l|p10x12_two_small",
    },
    "missing_corner": {
        "type": "str",
        "default": "rng",
        "valid": "tl|tr|bl|br",
    },
    "distractor_side": {
        "type": "str",
        "default": "rng",
        "valid": "top|bottom|left|right",
    },
    "palette_band": {
        "type": "str",
        "default": "rng",
        "valid": "low|high",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components_by_color(grid):
    """Return nonzero 4-connected components grouped by color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    grouped: dict[int, list[list[tuple[int, int]]]] = defaultdict(list)
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            grouped[color].append(sorted(cells))
    return grouped


def _shape_signature(cells):
    """Coarse morphology invariant under D4 orientation."""
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    box_h = max(rows) - min(rows) + 1
    box_w = max(cols) - min(cols) + 1
    return (
        len(cells),
        min(box_h, box_w),
        max(box_h, box_w),
        box_h * box_w - len(cells),
    )


def _blue_geometry(grid):
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    rows = sorted({r for r, _ in blues})
    cols = sorted({c for _, c in blues})
    if len(blues) != 3 or len(rows) != 2 or len(cols) != 2:
        return None
    corners = {(r, c) for r in rows for c in cols}
    missing = corners - set(blues)
    if len(missing) != 1:
        return None
    return blues, rows, cols, next(iter(missing))


def canonical_profile_signature(grid):
    """Linked official signature, or ``None`` for a recombined/impostor grid."""
    if not grid or not grid[0]:
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    geometry = _blue_geometry(grid)
    if geometry is None:
        return None
    _, rows, cols, _ = geometry
    grouped = _components_by_color(grid)
    distractor_signatures = []
    for color, components in grouped.items():
        if color in (1, 2):
            continue
        if len(components) != 1:
            return None
        distractor_signatures.append(_shape_signature(components[0]))
    morphology = tuple(sorted(distractor_signatures))
    return (
        len(grid),
        width,
        rows[1] - rows[0],
        cols[1] - cols[0],
        morphology,
    )


_CANONICAL_SIGNATURES = frozenset(
    {
        (8, 9, 3, 4, ((1, 1, 1, 0), (2, 1, 2, 0))),
        (9, 10, 4, 5, ((1, 1, 1, 0), (2, 1, 2, 0))),
        (10, 10, 6, 4, ((3, 2, 2, 1),)),
        (9, 11, 4, 8, ((3, 2, 2, 1),)),
        (10, 12, 6, 7, ((1, 1, 1, 0), (2, 1, 2, 0))),
    }
)
_PROFILE_BY_SIGNATURE = {
    signature: name
    for name, profile in SCENE_PROFILES.items()
    for signature in [
        (
            profile[0],
            profile[1],
            profile[2],
            profile[3],
            ((3, 2, 2, 1),)
            if profile[4] == "one_l"
            else ((1, 1, 1, 0), (2, 1, 2, 0)),
        )
    ]
}


def _choice(ctx, overrides, label, default_options, all_options):
    """Band-shaped default; explicit overrides remain band-independent."""
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, all_options)
    return ctx.draw_choice(label, default_options)


def _rectangle_origin(h, w, row_gap, col_gap, side, rng):
    r_lo, r_hi = 0, h - row_gap - 1
    c_lo, c_hi = 0, w - col_gap - 1
    if side == "top":
        r_lo = 2
    elif side == "bottom":
        r_hi = h - row_gap - 3
    elif side == "left":
        c_lo = 2
    elif side == "right":
        c_hi = w - col_gap - 3
    if r_lo > r_hi or c_lo > c_hi:
        raise ValueError(
            f"profile cannot reserve a two-cell {side} distractor band"
        )
    return rng.randint(r_lo, r_hi), rng.randint(c_lo, c_hi)


def _block_origin(h, w, rows, cols, side, block_h, block_w, rng):
    r0, r1 = rows
    c0, c1 = cols
    if side == "top":
        return (
            rng.randint(0, r0 - block_h),
            rng.randint(c0, c1 - block_w + 1),
        )
    if side == "bottom":
        return (
            rng.randint(r1 + 1, h - block_h),
            rng.randint(c0, c1 - block_w + 1),
        )
    if side == "left":
        return (
            rng.randint(r0, r1 - block_h + 1),
            rng.randint(0, c0 - block_w),
        )
    return (
        rng.randint(r0, r1 - block_h + 1),
        rng.randint(c1 + 1, w - block_w),
    )


def _paint_distractors(grid, morphology, side, palette_band, rng):
    geometry = _blue_geometry(grid)
    assert geometry is not None
    _, rows, cols, _ = geometry
    h, w = len(grid), len(grid[0])
    palette = [3, 4, 5] if palette_band == "low" else [6, 7, 8, 9]
    rng.shuffle(palette)

    if morphology == "one_l":
        br, bc = _block_origin(h, w, rows, cols, side, 2, 2, rng)
        omitted = rng.choice(((0, 0), (0, 1), (1, 0), (1, 1)))
        for dr in range(2):
            for dc in range(2):
                if (dr, dc) != omitted:
                    grid[br + dr][bc + dc] = palette[0]
        return

    if side in ("top", "bottom"):
        block_h, block_w = 2, 3
        templates = (
            (((0, 0), (0, 1)), (1, 2)),
            (((0, 0), (1, 0)), (0, 2)),
        )
    else:
        block_h, block_w = 3, 2
        templates = (
            (((0, 0), (0, 1)), (2, 0)),
            (((0, 0), (1, 0)), (2, 1)),
        )
    br, bc = _block_origin(
        h, w, rows, cols, side, block_h, block_w, rng
    )
    domino, singleton = rng.choice(templates)
    for dr, dc in domino:
        grid[br + dr][bc + dc] = palette[0]
    sr, sc = singleton
    grid[br + sr][bc + sc] = palette[1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    # SCHEDULE (2026-07-24, semantic-gate repair): the default missing corner
    # cycles tl/tr/bl/br by sample_index, so any three consecutive samples
    # witness three DISTINCT missing corners.  Before this, 9/200 pinned
    # lesson windows drew the same missing corner in all three demos, leaving
    # the fixed-corner overfit rule alive.  Explicit overrides still win.
    effective = dict(overrides)
    effective.setdefault(
        "missing_corner",
        _MISSING_CORNERS[int(sample_index) % len(_MISSING_CORNERS)],
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    band = difficulty or "medium"
    if band == "easy":
        default_profiles = (
            _SCENE_NAMES[0], _SCENE_NAMES[0],
            _SCENE_NAMES[1], _SCENE_NAMES[1],
            _SCENE_NAMES[2], _SCENE_NAMES[3], _SCENE_NAMES[4],
        )
    elif band == "hard":
        default_profiles = (
            _SCENE_NAMES[0], _SCENE_NAMES[1],
            _SCENE_NAMES[2], _SCENE_NAMES[2],
            _SCENE_NAMES[3], _SCENE_NAMES[3],
            _SCENE_NAMES[4], _SCENE_NAMES[4],
        )
    else:
        default_profiles = _SCENE_NAMES

    profile_name = _choice(
        ctx,
        overrides,
        "scene_profile",
        default_profiles,
        _SCENE_NAMES,
    )
    missing_name = ctx.draw_choice("missing_corner", _MISSING_CORNERS)
    side = ctx.draw_choice("distractor_side", _DISTRACTOR_SIDES)
    palette_band = ctx.draw_choice("palette_band", _PALETTE_BANDS)
    h, w, row_gap, col_gap, morphology = SCENE_PROFILES[profile_name]

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    top, left = _rectangle_origin(
        h, w, row_gap, col_gap, side, rng
    )
    bottom, right = top + row_gap, left + col_gap
    corners = {
        "tl": (top, left),
        "tr": (top, right),
        "bl": (bottom, left),
        "br": (bottom, right),
    }
    for name, (r, c) in corners.items():
        if name != missing_name:
            grid[r][c] = 1
    _paint_distractors(grid, morphology, side, palette_band, rng)
    return grid


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact semantic axis from the returned grid."""
    signature = canonical_profile_signature(grid)
    profile_name = _PROFILE_BY_SIGNATURE.get(signature, "unknown")
    geometry = _blue_geometry(grid)
    if geometry is None:
        return {"scene_profile": profile_name}
    _, rows, cols, missing = geometry
    corner_names = {
        (rows[0], cols[0]): "tl",
        (rows[0], cols[1]): "tr",
        (rows[1], cols[0]): "bl",
        (rows[1], cols[1]): "br",
    }
    distractors = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 2)
    ]
    if distractors and all(r < rows[0] for r, _, _ in distractors):
        side = "top"
    elif distractors and all(r > rows[1] for r, _, _ in distractors):
        side = "bottom"
    elif distractors and all(c < cols[0] for _, c, _ in distractors):
        side = "left"
    elif distractors and all(c > cols[1] for _, c, _ in distractors):
        side = "right"
    else:
        side = "mixed"
    colors = {value for _, _, value in distractors}
    palette_band = "low" if colors and max(colors) <= 5 else "high"
    return {
        "scene_profile": profile_name,
        "missing_corner": corner_names[missing],
        "distractor_side": side,
        "palette_band": palette_band,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural gate for the official linked teaching distribution."""
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    values = [value for row in grid for value in row]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for value in values
    ):
        return ["cell value outside integer ARC palette 0..9"]
    if 0 not in values:
        errors.append("zero background is absent")
    if 2 in values:
        errors.append("red output color must be absent from the input")

    geometry = _blue_geometry(grid)
    if geometry is None:
        errors.append("expected exactly three blue corners spanning two rows and columns")
        return errors
    blues, rows, cols, missing = geometry
    if rows[1] - rows[0] < 2 or cols[1] - cols[0] < 2:
        errors.append("rectangle row and column gaps must both be at least two")
    if grid[missing[0]][missing[1]] != 0:
        errors.append("implied fourth rectangle corner must be empty")

    distractor_colors = sorted(set(values) - {0, 1, 2})
    grouped = _components_by_color(grid)
    if len(distractor_colors) not in (1, 2):
        errors.append("expected one L distractor color or two small distractor colors")
    for color in distractor_colors:
        components = grouped.get(color, [])
        if len(components) != 1:
            errors.append(f"distractor color {color} must form one component")
            continue
        for r, c in components[0]:
            if rows[0] <= r <= rows[1] and cols[0] <= c <= cols[1]:
                errors.append("all distractor cells must lie outside the rectangle bbox")
                break

    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(
            "canvas, rectangle span, and distractor morphology do not match an official linked profile"
        )
    # Fresh-set check catches a hidden extra blue component even if a future
    # geometry helper is weakened.
    if len(set(blues)) != 3:
        errors.append("blue clue cells must be three distinct positions")
    return errors


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md)
# ---------------------------------------------------------------------------

def strict_canonical_like(grid) -> list[str]:
    """[] when `grid` is a lawful canonical-like scene for THIS task.

    Enforces the LINKED profile family, not the coarse morphology marginals
    that let an 8x9 four-color impostor through: three blue cells on three
    rectangle corners with gaps >= 2, an empty implied fourth corner, no red
    in the input, distractors as one component per color strictly outside the
    rectangle bbox, and a (canvas, span, distractor-morphology) signature
    matching one of the five official profiles.  Pure.
    """
    return list(self_check(grid))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for hook logic; Racket stays authoritative."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    geometry = _blue_geometry(grid)
    _, _rows, _cols, missing = geometry
    out = [list(row) for row in grid]
    out[missing[0]][missing[1]] = 2
    return out


def _lawful_observables(grid) -> dict[str, str] | None:
    if self_check(grid):
        return None
    return observe_overrides(grid)


def _witness_field(grid, extract) -> bool:
    obs = _lawful_observables(grid)
    return False if obs is None else bool(extract(obs))


SEMANTIC_WITNESSES = {
    # every missing-corner position must be demonstrated
    "missing_tl": lambda grid: _witness_field(grid, lambda o: o["missing_corner"] == "tl"),
    "missing_tr": lambda grid: _witness_field(grid, lambda o: o["missing_corner"] == "tr"),
    "missing_bl": lambda grid: _witness_field(grid, lambda o: o["missing_corner"] == "bl"),
    "missing_br": lambda grid: _witness_field(grid, lambda o: o["missing_corner"] == "br"),
    # distractors must appear on every exterior side
    "distractor_top": lambda grid: _witness_field(grid, lambda o: o["distractor_side"] == "top"),
    "distractor_bottom": lambda grid: _witness_field(grid, lambda o: o["distractor_side"] == "bottom"),
    "distractor_left": lambda grid: _witness_field(grid, lambda o: o["distractor_side"] == "left"),
    "distractor_right": lambda grid: _witness_field(grid, lambda o: o["distractor_side"] == "right"),
    # both distractor morphologies and both palette bands stay represented
    "morphology_one_l": lambda grid: _witness_field(
        grid, lambda o: SCENE_PROFILES.get(o["scene_profile"], ("", "", "", "", ""))[4] == "one_l"
    ),
    "morphology_two_small": lambda grid: _witness_field(
        grid, lambda o: SCENE_PROFILES.get(o["scene_profile"], ("", "", "", "", ""))[4] == "two_small"
    ),
    "palette_low": lambda grid: _witness_field(grid, lambda o: o["palette_band"] == "low"),
    "palette_high": lambda grid: _witness_field(grid, lambda o: o["palette_band"] == "high"),
}


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    """Outputs of the plausible competing rules on a lawful scene, else None.

    Competitors implemented:
      mark_present_corner — paint red on the present corner diagonally
        opposite the missing one instead of the missing corner
      blue_completion — complete the rectangle in blue, not red
      erase_distractors — mark the corner but zero every distractor cell
      corner_only_output — return just the 1x1 red corner, not the full grid
      fixed_missing_corner_{tl,tr,bl,br} — only ever complete corner X;
        otherwise return the input unchanged (the overfit a same-corner demo
        window cannot falsify)
    Pure.
    """
    if self_check(grid):
        return None
    geometry = _blue_geometry(grid)
    _, rows, cols, missing = geometry
    corner_positions = {
        "tl": (rows[0], cols[0]),
        "tr": (rows[0], cols[1]),
        "bl": (rows[1], cols[0]),
        "br": (rows[1], cols[1]),
    }
    missing_name = next(
        name for name, pos in corner_positions.items() if pos == missing
    )
    opposite = {"tl": "br", "br": "tl", "tr": "bl", "bl": "tr"}[missing_name]
    truth = rule_mirror(grid)

    marked_present = [list(row) for row in grid]
    opp_r, opp_c = corner_positions[opposite]
    marked_present[opp_r][opp_c] = 2

    blue_completion = [list(row) for row in grid]
    blue_completion[missing[0]][missing[1]] = 1

    erased = [
        [value if value in (0, 1, 2) else 0 for value in row] for row in truth
    ]

    outputs: dict[str, list[list[int]]] = {
        "mark_present_corner": marked_present,
        "blue_completion": blue_completion,
        "erase_distractors": erased,
        "corner_only_output": [[2]],
    }
    for name in _MISSING_CORNERS:
        outputs[f"fixed_missing_corner_{name}"] = (
            truth if name == missing_name else [list(row) for row in grid]
        )
    return outputs


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos force mark-the-missing-corner-red on the query.

    A competitor that reproduces EVERY demo output yet answers the query
    differently means the lesson underdetermines the rule.  The live danger
    is the fixed-corner overfit: demo windows whose missing corner never
    varies cannot falsify it, which is why the default missing corner now
    cycles by sample_index.  Pure.
    """
    reasons: list[str] = []
    query_competitors = _competitor_outputs(query.get("input"))
    if query_competitors is None:
        return ["query input is not a lawful scene for this task"]
    query_truth = rule_mirror(query.get("input"))

    demo_rows: list[tuple[dict, dict[str, list[list[int]]]]] = []
    for index, demo in enumerate(demos):
        competitors = _competitor_outputs(demo.get("input"))
        if competitors is None:
            reasons.append(f"demo {index} input is not a lawful scene for this task")
            continue
        if demo.get("output") != rule_mirror(demo.get("input")):
            reasons.append(
                f"demo {index} output disagrees with the missing-corner rule mirror"
            )
            continue
        demo_rows.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        survives = all(
            competitors[name] == demo["output"] for demo, competitors in demo_rows
        )
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo yet answers the "
                "query differently"
            )
    return sorted(set(reasons))
