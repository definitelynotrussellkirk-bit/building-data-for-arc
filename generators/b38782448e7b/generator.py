"""Generator for ARC task b38782448e7b: gated vertical XOR sweeps.

The unique modal colour is background.  A non-background cell in row 0 is a
firing marker exactly when it differs from the cell directly below it.  In each
firing column, every body cell equal to the marker becomes background and every
other body cell becomes the marker.  Non-firing top-row decoys and all cells
outside firing columns are preserved.

The curriculum deliberately includes four facts that the former sampler hid:
non-firing top decoys, preserved coloured body content outside firing columns,
third-colour overwrite inside a firing column, and marker-equal XOR-off cells.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b38782448e7b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "06479b7ecc39"

SUMMARY = (
    "Use the unique modal colour as background. A non-background row-0 cell "
    "fires only when it differs from row 1 in its column. Down each firing "
    "column, marker-colour cells turn into background and every other body "
    "cell turns into the marker colour. Non-firing top decoys and all cells "
    "outside firing columns remain unchanged."
)

INVARIANTS = [
    "inputs are 20..30 by 20..30 ARC grids with a unique modal background",
    "the input palette contains 3..7 colours",
    "there are 2..6 firing top-row markers and 0..3 non-firing top decoys",
    "firing columns jointly expose background, marker-equal, and third-colour body cells",
    "coloured body content exists outside firing marker columns",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "20..30",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "20..30",
    },
    "bg_color": {
        "type": "color",
        "default": "canonical-profile schedule plus keyed colour draw",
        "valid": "0..9",
    },
    "palette_size": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "3..7",
    },
    "n_markers": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty draw",
        "valid": "2..6",
    },
    "n_decoys": {
        "type": "int",
        "default": "semantic schedule",
        "valid": "0..3",
    },
}

# The first three branches exactly realize every canonical (height, width,
# palette-size) profile.  The fourth broad branch supplies additional support.
_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "name": "canonical_20x20_palette3",
        "grid_h": 20,
        "grid_w": 20,
        "bg_color": 8,
        "palette_size": 3,
        "n_markers": 2,
        "n_decoys": 1,
    },
    {
        "name": "canonical_30x30_palette6",
        "grid_h": 30,
        "grid_w": 30,
        "bg_color": 4,
        "palette_size": 6,
        "n_markers": 6,
        "n_decoys": 1,
    },
    {
        "name": "canonical_30x30_palette7",
        "grid_h": 30,
        "grid_w": 30,
        "bg_color": 7,
        "palette_size": 7,
        "n_markers": 5,
        "n_decoys": 2,
    },
    {
        "name": "broad",
        "grid_h": None,
        "grid_w": None,
        "bg_color": None,
        "palette_size": None,
        "n_markers": None,
        "n_decoys": None,
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic profile branch used by generation."""
    del seed
    _validate_difficulty(difficulty)
    return _PROFILES[int(sample_index) % len(_PROFILES)]["name"]


def _profile_for(sample_index: int) -> dict[str, Any]:
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ranges = {
        "grid_h": (20, 30),
        "grid_w": (20, 30),
        "palette_size": (3, 7),
        "n_markers": (2, 6),
        "n_decoys": (0, 3),
    }
    for name, (lo, hi) in ranges.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"override {name} must be an integer in {lo}..{hi}")

    if "bg_color" in overrides and overrides["bg_color"] is not None:
        value = overrides["bg_color"]
        if type(value) is not int or not 0 <= value <= 9:
            raise ValueError("override bg_color must be an integer colour in 0..9")


def _scheduled_int(ctx, overrides, name: str, default: int | None, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if default is not None:
        return ctx.draw_choice(name, (default,))
    return ctx.draw_int_diff(name, lo, hi)


def _scheduled_color(ctx, overrides, default: int | None) -> int:
    if "bg_color" in overrides and overrides["bg_color"] is not None:
        return ctx.draw_color("bg_color")
    if default is not None:
        return ctx.draw_choice("bg_color", (default,))
    return ctx.draw_color("bg_color")


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _unique_mode(grid: Any) -> tuple[int | None, list[str]]:
    counts = Counter(value for row in grid for value in row)
    ordered = counts.most_common()
    if not ordered:
        return None, ["grid contains no cells"]
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        return None, ["background must be the unique modal colour"]
    return ordered[0][0], []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 20 <= height <= 30:
        errors.append(f"height must be in 20..30, found {height}")
    if not 20 <= width <= 30:
        errors.append(f"width must be in 20..30, found {width}")

    bg, mode_errors = _unique_mode(grid)
    errors.extend(mode_errors)
    if bg is None:
        return {"errors": errors}

    palette = {value for row in grid for value in row}
    if not 3 <= len(palette) <= 7:
        errors.append(f"palette size must be in 3..7, found {len(palette)}")

    markers = [
        col
        for col, value in enumerate(grid[0])
        if value != bg and height > 1 and value != grid[1][col]
    ]
    decoys = [
        col
        for col, value in enumerate(grid[0])
        if value != bg and height > 1 and value == grid[1][col]
    ]
    if not 2 <= len(markers) <= 6:
        errors.append(f"expected 2..6 firing marker columns, found {len(markers)}")
    if not 0 <= len(decoys) <= 3:
        errors.append(f"expected 0..3 non-firing top decoys, found {len(decoys)}")

    body_has_bg = any(
        grid[row][col] == bg
        for col in markers
        for row in range(1, height)
    )
    body_has_marker_match = any(
        grid[row][col] == grid[0][col]
        for col in markers
        for row in range(1, height)
    )
    body_has_third = any(
        grid[row][col] not in (bg, grid[0][col])
        for col in markers
        for row in range(1, height)
    )
    if markers and not body_has_bg:
        errors.append("firing columns need at least one background body cell")
    if markers and not body_has_marker_match:
        errors.append("firing columns need at least one marker-equal XOR-off cell")
    if markers and not body_has_third:
        errors.append("firing columns need at least one third-colour overwrite cell")

    marker_set = set(markers)
    preserved_body = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if col not in marker_set and grid[row][col] != bg
    ]
    if not preserved_body:
        errors.append("need coloured body content outside firing marker columns")

    bad_decoys = [
        col
        for col in decoys
        if not any(grid[row][col] != grid[0][col] for row in range(2, height))
    ]
    if bad_decoys:
        errors.append(f"non-firing top decoys need contrasting body evidence: {bad_decoys}")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "bg": bg,
        "palette": palette,
        "markers": markers,
        "decoys": decoys,
        "preserved_body": preserved_body,
        "body_has_bg": body_has_bg,
        "body_has_marker_match": body_has_marker_match,
        "body_has_third": body_has_third,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact advertised axis from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "bg_color": analysis["bg"],
        "palette_size": len(analysis["palette"]),
        "n_markers": len(analysis["markers"]),
        "n_decoys": len(analysis["decoys"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or off-contract input scenes."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical examples and generated examples share this strict grammar."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror for diagnostics; canonical Racket is authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input grid: " + "; ".join(analysis["errors"]))
    bg = analysis["bg"]
    output = [list(row) for row in grid]
    for col in analysis["markers"]:
        marker = grid[0][col]
        for row in range(1, len(grid)):
            output[row][col] = bg if grid[row][col] == marker else marker
    return output


def _all_top_non_background(grid):
    bg, errors = _unique_mode(grid)
    if errors or bg is None:
        raise ValueError("grid must have a unique modal background")
    output = [list(row) for row in grid]
    for col, marker in enumerate(grid[0]):
        if marker == bg:
            continue
        for row in range(1, len(grid)):
            output[row][col] = bg if grid[row][col] == marker else marker
    return output


def _erase_unmarked_body(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input grid")
    bg = analysis["bg"]
    output = [[bg for _ in row] for row in grid]
    output[0] = list(grid[0])
    for col in analysis["markers"]:
        marker = grid[0][col]
        for row in range(1, len(grid)):
            output[row][col] = bg if grid[row][col] == marker else marker
    return output


def _binary_toggle_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input grid")
    bg = analysis["bg"]
    output = [list(row) for row in grid]
    for col in analysis["markers"]:
        marker = grid[0][col]
        for row in range(1, len(grid)):
            value = grid[row][col]
            if value == marker:
                output[row][col] = bg
            elif value == bg:
                output[row][col] = marker
    return output


def _solid_paint_columns(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input grid")
    output = [list(row) for row in grid]
    for col in analysis["markers"]:
        marker = grid[0][col]
        for row in range(1, len(grid)):
            output[row][col] = marker
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "all_top_non_background": _all_top_non_background,
    "erase_unmarked_body": _erase_unmarked_body,
    "binary_toggle_only": _binary_toggle_only,
    "solid_paint_columns": _solid_paint_columns,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "all_top_non_background": _all_top_non_background,
}


def _lawful(grid) -> bool:
    return not _analysis(grid)["errors"]


def _has_non_firing_top_decoy(grid) -> bool:
    if not _lawful(grid):
        return False
    analysis = _analysis(grid)
    return bool(analysis["decoys"]) and _all_top_non_background(grid) != rule_mirror(grid)


def _has_unmarked_body_preservation(grid) -> bool:
    return _lawful(grid) and bool(_analysis(grid)["preserved_body"]) and _erase_unmarked_body(grid) != rule_mirror(grid)


def _has_third_color_overwrite(grid) -> bool:
    return _lawful(grid) and bool(_analysis(grid)["body_has_third"]) and _binary_toggle_only(grid) != rule_mirror(grid)


def _has_xor_off_marker_match(grid) -> bool:
    return _lawful(grid) and bool(_analysis(grid)["body_has_marker_match"]) and _solid_paint_columns(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "non_firing_top_decoy": _has_non_firing_top_decoy,
    "unmarked_body_preservation": _has_unmarked_body_preservation,
    "third_color_overwrite": _has_third_color_overwrite,
    "xor_off_marker_match": _has_xor_off_marker_match,
}
WITNESS_RIVALS = {
    "non_firing_top_decoy": ["all_top_non_background"],
    "unmarked_body_preservation": ["erase_unmarked_body"],
    "third_color_overwrite": ["binary_toggle_only"],
    "xor_off_marker_match": ["solid_paint_columns"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the gated XOR rule")
            continue
        valid_demos.append(demo)

    if len(valid_demos) != len(demos):
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _paint_canonical_scale_component(
    grid, colors: tuple[int, ...], ctx
) -> tuple[int, int, int, int]:
    """Paint a canonical-scale component at a deterministic variable position.

    The block starts below the top control evidence and ends above the palette
    swatches.  Its horizontal position varies across the full grid.  Generation
    later anchors one active marker inside the block, so lessons demonstrate that
    the sweep cuts through substantial objects rather than only empty columns.
    """
    height, width = len(grid), len(grid[0])
    block_height = 6 if height <= 22 else 12 if height >= 28 else 9
    block_width = 9
    rng = ctx.draw_rng("canonical_scale_component")
    row0 = rng.randint(5, height - block_height - 5)
    col0 = rng.randint(0, width - block_width)
    color = colors[0]
    for row in range(row0, row0 + block_height):
        for col in range(col0, col0 + block_width):
            grid[row][col] = color
    return row0, col0, block_height, block_width


def _paint_attached_palette_regions(
    grid,
    colors: tuple[int, ...],
    component: tuple[int, int, int, int],
) -> None:
    """Expose every extra colour in one compact body component.

    Earlier versions scattered random rectangles and bottom swatches, creating
    16 non-background components at the median versus five canonically.  A
    two-row band immediately below the large body block keeps all colour roles
    visible while matching the canonical connected-mosaic morphology.
    """
    if len(colors) <= 1:
        return
    _, block_col, block_height, block_width = component
    block_row = component[0]
    height, width = len(grid), len(grid[0])
    band_row = block_row + block_height
    extras = colors[1:]
    band_width = 2 * len(extras)
    band_col = max(0, min(width - band_width, block_col + (block_width - band_width) // 2))
    if band_row + 1 >= height:  # Construction reserves five rows below the block.
        raise RuntimeError("palette band does not fit below canonical-scale component")
    for index, color in enumerate(extras):
        col0 = band_col + 2 * index
        for row in (band_row, band_row + 1):
            grid[row][col0] = color
            grid[row][col0 + 1] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; canonical Racket owns labels."""
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    profile = _profile_for(int(sample_index))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, overrides, "grid_h", profile["grid_h"], 20, 30)
    width = _scheduled_int(ctx, overrides, "grid_w", profile["grid_w"], 20, 30)
    bg = _scheduled_color(ctx, overrides, profile["bg_color"])
    palette_size = _scheduled_int(
        ctx, overrides, "palette_size", profile["palette_size"], 3, 7
    )
    n_markers = _scheduled_int(
        ctx, overrides, "n_markers", profile["n_markers"], 2, 6
    )
    default_decoys = profile["n_decoys"]
    if default_decoys is None:
        default_decoys = 1 + (int(sample_index) % 3)
    n_decoys = _scheduled_int(
        ctx, overrides, "n_decoys", int(default_decoys), 0, 3
    )

    colors = ctx.draw_distinct_colors(
        "palette_colors", n=palette_size - 1, exclude=(bg,)
    )
    grid = full_grid(height, width, bg)
    component = _paint_canonical_scale_component(grid, colors, ctx)
    _paint_attached_palette_regions(grid, colors, component)
    _, component_col, _, component_width = component
    component_cols = tuple(range(component_col, component_col + component_width))

    placement_rng = ctx.draw_rng("control_columns")
    anchor_marker = placement_rng.choice(component_cols)
    available = [col for col in range(width) if col != anchor_marker]
    remaining_controls = placement_rng.sample(
        available, n_markers + n_decoys - 1
    )
    marker_cols = sorted([anchor_marker, *remaining_controls[: n_markers - 1]])
    decoy_cols = sorted(remaining_controls[n_markers - 1 :])

    color_rng = ctx.draw_rng("control_colors")
    color_order = list(colors)
    color_rng.shuffle(color_order)

    for index, col in enumerate(marker_cols):
        marker = color_order[index % len(color_order)]
        third = next(color for color in colors if color != marker)
        grid[0][col] = marker
        # Keep each top control compact: row 1 differs from the marker so the
        # column fires, while rows 0..2 remain one non-background component.
        grid[1][col] = third
        grid[2][col] = marker
        grid[3][col] = bg
        grid[4][col] = bg

    for index, col in enumerate(decoy_cols):
        decoy = color_order[(n_markers + index) % len(color_order)]
        other = next(color for color in colors if color != decoy)
        grid[0][col] = decoy
        grid[1][col] = decoy
        grid[2][col] = other
        grid[3][col] = bg

    issues = self_check(grid)
    if issues:  # Construction failures are programming errors, never silent data.
        raise RuntimeError("constructed invalid b38782448e7b input: " + "; ".join(issues))
    return grid
