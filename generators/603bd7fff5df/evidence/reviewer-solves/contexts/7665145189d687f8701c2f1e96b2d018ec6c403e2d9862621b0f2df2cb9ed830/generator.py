"""High-signal generator for ARC task 3f7978a0 / 603bd7fff5df.

Selected rule
-------------
Find the bounding box of all gray (5) cells and return exactly the columns of
that box, extending the row interval by one row above and one row below.

The canonical task uses a deliberately narrow visual language: colors
``{0, 5, 8}``, two gray side columns, and blue content both inside and outside
the selected crop.  This generator stays on that language while varying the
recoverable dimensions that matter: canonical scene scale, horizontal frame
placement, and how densely the gray side columns are marked.

Every ordinary draw places blue evidence in four semantically distinct regions:
the upper halo row, lower halo row, gray-box interior, and outside the answer
crop.  Those placements make the ``+/- one row`` and ``ignore outside decoys``
parts of the rule observable instead of allowing a gray-bbox or nonzero-bbox
shortcut.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "603bd7fff5df"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "539d28e25b24"

SUMMARY = (
    "On a 0-background grid with blue (8) content and two gray (5) side "
    "columns, crop the gray bounding-box columns and include exactly one row "
    "above and below the gray bounding-box rows."
)
INVARIANTS = [
    "the palette is exactly {0, 5, 8}",
    "all gray cells lie on the two side columns of one rectangular bounding box",
    "both side columns mark the top and bottom gray-bbox rows",
    "the gray bbox has at least one source row above and below",
    "blue appears in the top halo, bottom halo, frame interior, and outside the answer crop",
]

# The four source examples have exactly these (grid_h, grid_w, bbox_h, bbox_w)
# signatures.  Keeping them as a composite axis avoids the impossible cross-
# product that the previous independent dimension axes advertised.
SCENE_PROFILES = (
    "p0_9x11_3x7",
    "p1_9x9_3x5",
    "p2_11x13_4x5",
    "p3_14x13_8x4",
)
_PROFILE_SPECS: dict[str, tuple[int, int, int, int]] = {
    "p0_9x11_3x7": (9, 11, 3, 7),
    "p1_9x9_3x5": (9, 9, 3, 5),
    "p2_11x13_4x5": (11, 13, 4, 5),
    "p3_14x13_8x4": (14, 13, 8, 4),
}
_PROFILE_BY_SIGNATURE = {value: key for key, value in _PROFILE_SPECS.items()}

PLACEMENTS = ("left_edge", "interior", "right_edge")
SIDE_STYLES = ("full_sides", "gapped_sides", "corners_only")
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "12-slot deterministic lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "placement": {
        "type": "str",
        "default": "12-slot deterministic lesson schedule",
        "valid": "|".join(PLACEMENTS),
    },
    "side_style": {
        "type": "str",
        "default": "full/gapped/corners lesson schedule",
        "valid": "|".join(SIDE_STYLES),
    },
}

# Every value of every public axis works with every value of the other axes and
# in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = tuple(range(12))


def _band_name(difficulty: Any) -> str:
    return difficulty if difficulty in {"easy", "medium", "hard"} else "medium"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the declared 12-slot curriculum cell for this draw.

    Difficulty rotates the schedule rather than changing the legal domain, so
    exact overrides remain band-independent while default rows are not cloned
    across easy/medium/hard.
    """
    del seed
    offset = {"easy": 0, "medium": 4, "hard": 8}.get(_band_name(difficulty), 4)
    return (int(sample_index) + offset) % len(SCHEDULE_PROFILES)


def _scheduled_axes(slot: int) -> tuple[str, str, str]:
    scene_profile = SCENE_PROFILES[slot % len(SCENE_PROFILES)]
    # Shift the placement permutation every three rows so placement and side
    # style do not collapse into a one-to-one shortcut.
    placement = PLACEMENTS[(slot + slot // 3) % len(PLACEMENTS)]
    side_style = SIDE_STYLES[slot % len(SIDE_STYLES)]
    return scene_profile, placement, side_style


def _draw_choice(ctx, overrides, name: str, options: tuple[str, ...], scheduled: str) -> str:
    # Singleton options preserve an explicit keyed-draw provenance record for
    # scheduled defaults.  Exact overrides are validated against the full set.
    choices = options if name in overrides else (scheduled,)
    return str(ctx.draw_choice(name, choices))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    scheduled_profile, scheduled_placement, scheduled_style = _scheduled_axes(slot)
    scene_profile = _draw_choice(
        ctx, overrides, "scene_profile", SCENE_PROFILES, scheduled_profile
    )
    placement = _draw_choice(ctx, overrides, "placement", PLACEMENTS, scheduled_placement)
    side_style = _draw_choice(ctx, overrides, "side_style", SIDE_STYLES, scheduled_style)

    height, width, box_h, box_w = _PROFILE_SPECS[scene_profile]
    band = _band_name(difficulty)
    rng = ctx.draw_rng(f"layout:{band}")

    top = rng.randint(1, height - box_h - 1)
    if placement == "left_edge":
        left = 0
    elif placement == "right_edge":
        left = width - box_w
    else:
        left = rng.randint(1, width - box_w - 1)

    grid = full_grid(height, width, 0)
    _draw_gray_sides(grid, top, left, box_h, box_w, side_style)
    _draw_blue_evidence(grid, top, left, box_h, box_w, rng, band)

    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid generator scene: {errors}")
    return [row[:] for row in grid]


def _draw_gray_sides(
    grid: list[list[int]], top: int, left: int, box_h: int, box_w: int, style: str
) -> None:
    right = left + box_w - 1
    bottom = top + box_h - 1
    for row, col in ((top, left), (top, right), (bottom, left), (bottom, right)):
        grid[row][col] = 5

    if style == "full_sides":
        for row in range(top, bottom + 1):
            grid[row][left] = 5
            grid[row][right] = 5
    elif style == "gapped_sides":
        # Alternating one-sided marks remain distinguishable from both the four
        # corners and continuous full sides even for the canonical 3-row boxes.
        for offset, row in enumerate(range(top + 1, bottom)):
            col = left if offset % 2 == 0 else right
            grid[row][col] = 5
    elif style != "corners_only":  # defensive; draw_choice already validates
        raise ValueError(f"unsupported side_style {style!r}")


def _draw_blue_evidence(
    grid: list[list[int]],
    top: int,
    left: int,
    box_h: int,
    box_w: int,
    rng,
    band: str,
) -> None:
    height, width = len(grid), len(grid[0])
    right = left + box_w - 1
    bottom = top + box_h - 1

    interior_cols = list(range(left + 1, right))
    interior_rows = list(range(top, bottom + 1))
    if not interior_cols:
        raise ValueError("profile has no frame interior columns")

    # Do not put blue at both gray-side endpoints in either halo row.  The
    # canonical examples do, so this is a deliberate generated counterexample
    # to the tempting endpoint-8 shortcut.
    top_blue = (top - 1, rng.choice(interior_cols))
    bottom_blue = (bottom + 1, rng.choice(interior_cols))
    inside_blue = (rng.choice(interior_rows), rng.choice(interior_cols))

    target_rows = range(top - 1, bottom + 2)
    target_cols = range(left, right + 1)
    outside_candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if not (row in target_rows and col in target_cols)
    ]
    outside_blue = rng.choice(outside_candidates)

    for row, col in (top_blue, bottom_blue, inside_blue, outside_blue):
        grid[row][col] = 8

    forbidden = {
        (top - 1, left),
        (top - 1, right),
        (bottom + 1, left),
        (bottom + 1, right),
    }
    forbidden.update((row, left) for row in range(top, bottom + 1))
    forbidden.update((row, right) for row in range(top, bottom + 1))
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0 and (row, col) not in forbidden
    ]
    rng.shuffle(candidates)
    extra_count = {"easy": 4, "medium": 7, "hard": 10}[band]
    for row, col in candidates[:extra_count]:
        grid[row][col] = 8


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _gray_bbox(grid: list[list[int]]) -> tuple[int, int, int, int]:
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        raise ValueError("grid has no gray cells")
    return (
        min(row for row, _ in gray),
        min(col for _, col in gray),
        max(row for row, _ in gray),
        max(col for _, col in gray),
    )


def _infer_side_style(
    gray: set[tuple[int, int]], r0: int, c0: int, r1: int, c1: int
) -> str | None:
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    if not corners.issubset(gray):
        return None
    full = {(row, col) for row in range(r0, r1 + 1) for col in (c0, c1)}
    if gray == full:
        return "full_sides"
    if gray == corners:
        return "corners_only"
    if corners.issubset(gray) and gray < full:
        return "gapped_sides"
    return None


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if palette != {0, 5, 8}:
        errors.append(f"palette must be exactly {{0, 5, 8}}, got {sorted(palette)}")

    gray = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    if len(gray) < 4:
        errors.append(f"expected at least four gray side markers, got {len(gray)}")
        return {"errors": errors, "height": height, "width": width, "palette": palette}

    r0 = min(row for row, _ in gray)
    c0 = min(col for _, col in gray)
    r1 = max(row for row, _ in gray)
    c1 = max(col for _, col in gray)
    box_h, box_w = r1 - r0 + 1, c1 - c0 + 1
    signature = (height, width, box_h, box_w)
    scene_profile = _PROFILE_BY_SIGNATURE.get(signature)
    if scene_profile is None:
        errors.append(f"unsupported scene signature {signature}")

    if r0 == 0:
        errors.append("gray bbox has no row above it")
    if r1 == height - 1:
        errors.append("gray bbox has no row below it")
    if c0 == c1:
        errors.append("gray bbox must have two distinct side columns")
    if any(col not in (c0, c1) for _, col in gray):
        errors.append("gray cells may appear only on the two bbox side columns")

    side_style = _infer_side_style(gray, r0, c0, r1, c1)
    if side_style is None:
        errors.append("gray side markers are not full, gapped, or four-corner sides")

    placement = (
        "left_edge" if c0 == 0 else "right_edge" if c1 == width - 1 else "interior"
    )
    if placement not in PLACEMENTS:
        errors.append("could not infer a supported horizontal placement")

    top_blue = bottom_blue = inside_blue = outside_blue = 0
    top_endpoint_pair = bottom_endpoint_pair = False
    if 0 < r0 and r1 < height - 1:
        top_row = grid[r0 - 1]
        bottom_row = grid[r1 + 1]
        top_blue = sum(top_row[col] == 8 for col in range(c0, c1 + 1))
        bottom_blue = sum(bottom_row[col] == 8 for col in range(c0, c1 + 1))
        top_endpoint_pair = top_row[c0] == 8 and top_row[c1] == 8
        bottom_endpoint_pair = bottom_row[c0] == 8 and bottom_row[c1] == 8
        inside_blue = sum(
            grid[row][col] == 8
            for row in range(r0, r1 + 1)
            for col in range(c0 + 1, c1)
        )
        outside_blue = sum(
            grid[row][col] == 8
            for row in range(height)
            for col in range(width)
            if not (r0 - 1 <= row <= r1 + 1 and c0 <= col <= c1)
        )
        if top_blue == 0:
            errors.append("top halo row must contain blue content inside crop columns")
        if bottom_blue == 0:
            errors.append("bottom halo row must contain blue content inside crop columns")
        if inside_blue == 0:
            errors.append("gray bbox interior must contain blue content")
        if outside_blue == 0:
            errors.append("at least one blue decoy must lie outside the answer crop")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "gray": gray,
        "bbox": (r0, c0, r1, c1),
        "box_h": box_h,
        "box_w": box_w,
        "scene_profile": scene_profile,
        "placement": placement,
        "side_style": side_style,
        "top_blue": top_blue,
        "bottom_blue": bottom_blue,
        "inside_blue": inside_blue,
        "outside_blue": outside_blue,
        "top_endpoint_pair": top_endpoint_pair,
        "bottom_endpoint_pair": bottom_endpoint_pair,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed grids and scenes that hide any essential rule region."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The ordinary teaching grammar is deliberately the canonical manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "scene_profile": analysis["scene_profile"],
        "placement": analysis["placement"],
        "side_style": analysis["side_style"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_shape": [analysis["height"], analysis["width"]],
        "bbox": list(analysis["bbox"]),
        "bbox_shape": [analysis["box_h"], analysis["box_w"]],
        "scene_profile": analysis["scene_profile"],
        "placement": analysis["placement"],
        "side_style": analysis["side_style"],
        "blue_region_counts": {
            "top_halo": analysis["top_blue"],
            "bottom_halo": analysis["bottom_blue"],
            "inside": analysis["inside_blue"],
            "outside_crop": analysis["outside_blue"],
        },
        "halo_side_endpoint_pairs": {
            "top": analysis["top_endpoint_pair"],
            "bottom": analysis["bottom_endpoint_pair"],
        },
    }


def _crop(grid, r0: int, c0: int, r1: int, c1: int) -> list[list[int]]:
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror for tests; selected Racket remains label authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    r0, c0, r1, c1 = _gray_bbox(grid)
    return _crop(grid, r0 - 1, c0, r1 + 1, c1)


def _bbox_only(grid) -> list[list[int]]:
    r0, c0, r1, c1 = _gray_bbox(grid)
    return _crop(grid, r0, c0, r1, c1)


def _full_width_rows(grid) -> list[list[int]]:
    r0, _, r1, _ = _gray_bbox(grid)
    return _crop(grid, r0 - 1, 0, r1 + 1, len(grid[0]) - 1)


def _nonzero_bbox(grid) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return _crop(grid, min(rows), min(cols), max(rows), max(cols))


def _side_endpoint_eights(grid) -> list[list[int]]:
    """Wrong canonical-fitting rule: use paired blue side endpoints as rows."""
    r0, c0, r1, c1 = _gray_bbox(grid)
    above = [
        row
        for row in range(r0)
        if grid[row][c0] == 8 and grid[row][c1] == 8
    ]
    below = [
        row
        for row in range(r1 + 1, len(grid))
        if grid[row][c0] == 8 and grid[row][c1] == 8
    ]
    if not above or not below:
        return _bbox_only(grid)
    return _crop(grid, max(above), c0, min(below), c1)


def _full_side_only(grid) -> list[list[int]]:
    """Wrong canonical-fitting rule: crop correctly only for continuous sides."""
    r0, c0, r1, c1 = _gray_bbox(grid)
    if all(grid[row][c0] == 5 and grid[row][c1] == 5 for row in range(r0, r1 + 1)):
        return _crop(grid, r0 - 1, c0, r1 + 1, c1)
    return _bbox_only(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "gray_bbox_only": _bbox_only,
    "full_width_halo_rows": _full_width_rows,
    "nonzero_bbox": _nonzero_bbox,
    "side_endpoint_eights": _side_endpoint_eights,
    "full_side_only": _full_side_only,
}

# Both of these wrong rules fit every canonical public pair.  Generated sparse
# sides and non-endpoint halo evidence are their required counterexamples.
CANONICAL_SHORTCUTS = {
    "side_endpoint_eights": _side_endpoint_eights,
    "full_side_only": _full_side_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


SEMANTIC_WITNESSES = {
    "halo_rows_are_rule_relevant": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and analysis["top_blue"] > 0
        and analysis["bottom_blue"] > 0
    ),
    "outside_blue_is_ignored": lambda grid: (
        (analysis := _lawful(grid)) is not None and analysis["outside_blue"] > 0
    ),
    "halo_endpoint_shortcut_is_false": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and not analysis["top_endpoint_pair"]
        and not analysis["bottom_endpoint_pair"]
    ),
    "sparse_gray_sides_still_define_bbox": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and analysis["side_style"] != "full_sides"
    ),
}

WITNESS_RIVALS = {
    "halo_rows_are_rule_relevant": ["gray_bbox_only"],
    "outside_blue_is_ignored": ["full_width_halo_rows", "nonzero_bbox"],
    "halo_endpoint_shortcut_is_false": ["side_endpoint_eights"],
    "sparse_gray_sides_still_define_bbox": ["full_side_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a three-demo window to falsify every declared wrong rule."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    demo_profiles: list[str] = []
    demo_styles: list[str] = []
    usable_demos: list[dict] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _lawful(demo["input"])
        if analysis is None:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the crop rule")
        demo_profiles.append(analysis["scene_profile"])
        demo_styles.append(analysis["side_style"])
        usable_demos.append(demo)

    query_analysis = _lawful(query["input"])
    if query_analysis is None:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query output disagrees with the crop rule")

    if len(set(demo_profiles)) < EXAMPLES_NEEDED:
        reasons.append("demonstrations do not expose three distinct canonical scene profiles")
    if query_analysis["scene_profile"] in set(demo_profiles):
        reasons.append("query repeats a demonstrated scene profile")
    if set(demo_styles) != set(SIDE_STYLES):
        reasons.append("demonstrations do not include full, gapped, and corner-only gray sides")

    for name, competitor in LESSON_COMPETITORS.items():
        if usable_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in usable_demos
        ):
            reasons.append(f"competing rule {name!r} fits every demonstration")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named malformed variants kept out of the public generation axes."""
    base = generate(77123, 5, difficulty="medium")
    analysis = _analysis(base)
    r0, c0, r1, c1 = analysis["bbox"]

    unsupported_color = deepcopy(base)
    zero = next(
        (row, col)
        for row in range(len(base))
        for col in range(len(base[0]))
        if base[row][col] == 0
    )
    unsupported_color[zero[0]][zero[1]] = 2

    missing_top_halo = deepcopy(base)
    for col in range(c0, c1 + 1):
        if missing_top_halo[r0 - 1][col] == 8:
            missing_top_halo[r0 - 1][col] = 0

    missing_bottom_halo = deepcopy(base)
    for col in range(c0, c1 + 1):
        if missing_bottom_halo[r1 + 1][col] == 8:
            missing_bottom_halo[r1 + 1][col] = 0

    missing_inside = deepcopy(base)
    for row in range(r0, r1 + 1):
        for col in range(c0 + 1, c1):
            if missing_inside[row][col] == 8:
                missing_inside[row][col] = 0

    missing_outside = deepcopy(base)
    for row in range(len(base)):
        for col in range(len(base[0])):
            if not (r0 - 1 <= row <= r1 + 1 and c0 <= col <= c1):
                if missing_outside[row][col] == 8:
                    missing_outside[row][col] = 0

    interior_gray = deepcopy(base)
    interior_gray[r0][c0 + 1] = 5

    missing_corner = deepcopy(base)
    missing_corner[r0][c0] = 0

    top_edge = deepcopy(base)
    shift = r0
    top_edge = top_edge[shift:]

    return [
        ("unsupported_color", unsupported_color),
        ("missing_top_halo", missing_top_halo),
        ("missing_bottom_halo", missing_bottom_halo),
        ("missing_inside_blue", missing_inside),
        ("missing_outside_blue", missing_outside),
        ("interior_gray", interior_gray),
        ("missing_gray_corner", missing_corner),
        ("gray_bbox_at_top_edge", top_edge),
    ]
