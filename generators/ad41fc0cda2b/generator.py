"""Generator for ARC task 8a004b2b / canonical task ad41fc0cda2b.

Four yellow corner markers define a rectangular output crop.  Colored square
reference blocks inside that rectangle reveal the scale and placement of a
small multicolour key drawn below the rectangle.  The answer crops to the
four-corner rectangle and replaces every key cell with a square block of the
observed size, aligned so the key's matching reference cells land on the
in-frame blocks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid


GENERATOR_ID = "ad41fc0cda2b"
TASK_ID = "ad41fc0cda2b"
VERSION = "4.0.0"
RULE_HASH = "22b0a6e75254"

SUMMARY = (
    "Exactly four yellow cells mark the corners of a rectangular crop. A "
    "connected three-colour key lies below the crop. Two or three complete "
    "same-colour square blocks already appear inside the crop at positions "
    "consistent with selected key cells. Infer the common block size from "
    "those references, scale every key cell to that square size, align the "
    "key to the references, and return only the completed corner-marked "
    "rectangle."
)

INVARIANTS = [
    "color 4 occurs exactly four times at the Cartesian-product corners of the output rectangle",
    "the input palette is exactly background 0, corner color 4, and three distinct key colors",
    "the key is a connected multicolor pattern wholly below the corner rectangle",
    "inside references are complete 2x2, 3x3, or 4x4 blocks matching selected key cells",
    "at least one key cell is absent from the input rectangle, so completion is visible",
    "the output is the rectangle crop with every key cell expanded by the inferred block size",
]

EXAMPLES_NEEDED = 3
PALETTE_KINDS = ("low", "high")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()


@dataclass(frozen=True)
class Variant:
    grid_h: int
    grid_w: int
    frame_top: int
    frame_left: int
    frame_h: int
    frame_w: int
    block_size: int
    key_top: int
    key_left: int
    key_roles: tuple[tuple[int, int, str], ...]
    reference_cells: tuple[tuple[int, int], ...]
    output_origin: tuple[int, int]


# These are the four authoritative canonical geometry branches.  Palettes vary,
# but dimensions, sparse key grammar, scale, and reference placement match the
# real source rows exactly.  Ordering is deliberate: any three consecutive
# sample indices contain at least two block sizes, making fixed-scale shortcuts
# falsifiable in every materialized lesson.
VARIANTS: dict[str, Variant] = {
    "small_square": Variant(
        grid_h=17,
        grid_w=18,
        frame_top=1,
        frame_left=2,
        frame_h=7,
        frame_w=7,
        block_size=2,
        key_top=13,
        key_left=10,
        key_roles=(
            (0, 0, "a"),
            (0, 1, "b"),
            (1, 0, "b"),
            (1, 1, "c"),
        ),
        reference_cells=((0, 0), (1, 1)),
        output_origin=(1, 1),
    ),
    "medium_hook": Variant(
        grid_h=16,
        grid_w=18,
        frame_top=0,
        frame_left=3,
        frame_h=11,
        frame_w=11,
        block_size=3,
        key_top=13,
        key_left=6,
        key_roles=(
            (0, 0, "a"),
            (0, 1, "b"),
            (0, 2, "b"),
            (1, 1, "c"),
            (1, 2, "b"),
        ),
        reference_cells=((0, 0), (0, 2), (1, 1)),
        output_origin=(3, 1),
    ),
    "wide_arch": Variant(
        grid_h=17,
        grid_w=17,
        frame_top=0,
        frame_left=2,
        frame_h=9,
        frame_w=14,
        block_size=2,
        key_top=12,
        key_left=2,
        key_roles=(
            (0, 0, "a"),
            (0, 4, "b"),
            (1, 0, "c"),
            (1, 1, "c"),
            (1, 3, "c"),
            (1, 4, "c"),
            (2, 1, "c"),
            (2, 2, "c"),
            (2, 3, "c"),
        ),
        reference_cells=((0, 0), (0, 4), (2, 2)),
        output_origin=(2, 1),
    ),
    "large_tee": Variant(
        grid_h=19,
        grid_w=18,
        frame_top=0,
        frame_left=0,
        frame_h=14,
        frame_w=18,
        block_size=4,
        key_top=15,
        key_left=8,
        key_roles=(
            (0, 0, "a"),
            (0, 2, "b"),
            (1, 0, "c"),
            (1, 1, "c"),
            (1, 2, "c"),
            (2, 1, "c"),
        ),
        reference_cells=((0, 0), (0, 2)),
        output_origin=(2, 4),
    ),
}
VARIANT_NAMES = tuple(VARIANTS)

AXES = {
    "scene_variant": {
        "type": "str",
        "default": "sample-index schedule across all canonical geometry branches",
        "valid": "small_square|medium_hook|wide_arch|large_tee",
    },
    "palette_band": {
        "type": "str",
        "default": "deterministic low/high alternation",
        "valid": "low|high",
    },
}


@dataclass(frozen=True)
class Analysis:
    variant_name: str
    variant: Variant
    role_colors: dict[str, int]


def _scheduled_choice(ctx, label: str, scheduled: str, choices: tuple[str, ...]) -> str:
    """Record a deterministic schedule through GenCtx while honoring overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (scheduled,))


def _role_map(variant: Variant) -> dict[tuple[int, int], str]:
    return {(r, c): role for r, c, role in variant.key_roles}


def _corners(variant: Variant) -> set[tuple[int, int]]:
    top = variant.frame_top
    left = variant.frame_left
    bottom = top + variant.frame_h - 1
    right = left + variant.frame_w - 1
    return {(top, left), (top, right), (bottom, left), (bottom, right)}


def _variant_from_geometry(grid: list[list[int]]) -> tuple[str, Variant] | None:
    h, w = len(grid), len(grid[0])
    fours = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    for name, variant in VARIANTS.items():
        if (h, w) == (variant.grid_h, variant.grid_w) and fours == _corners(variant):
            return name, variant
    return None


def _analyze(grid: Any) -> tuple[Analysis | None, list[str]]:
    """Parse the exact canonical teaching grammar without mutating ``grid``."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None, ["grid is not a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["ragged or zero-width grid"]
    if len(grid) > 30 or width > 30:
        return None, [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["cell outside integer ARC palette 0..9"]

    identified = _variant_from_geometry(grid)
    if identified is None:
        return None, [
            "dimensions and four yellow-corner geometry do not match any canonical branch"
        ]
    variant_name, variant = identified
    errors: list[str] = []
    role_colors: dict[str, int] = {}
    key_positions = {(r, c) for r, c, _ in variant.key_roles}

    # Key occupancy and role-equality constraints.
    for dr, dc, role in variant.key_roles:
        value = grid[variant.key_top + dr][variant.key_left + dc]
        if value in (0, 4):
            errors.append(f"key cell {(dr, dc)} is background/corner color")
            continue
        previous = role_colors.get(role)
        if previous is None:
            role_colors[role] = value
        elif previous != value:
            errors.append(f"key role {role!r} uses inconsistent colors")

    if set(role_colors) == {"a", "b", "c"} and len(set(role_colors.values())) != 3:
        errors.append("key roles a/b/c must use three distinct colors")
    elif set(role_colors) != {"a", "b", "c"}:
        errors.append("key does not expose all three color roles")

    frame_top = variant.frame_top
    frame_left = variant.frame_left
    frame_bottom = frame_top + variant.frame_h - 1
    frame_right = frame_left + variant.frame_w - 1
    expected_key_abs = {
        (variant.key_top + dr, variant.key_left + dc)
        for dr, dc in key_positions
    }
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 4):
                continue
            inside = frame_top <= r <= frame_bottom and frame_left <= c <= frame_right
            if not inside and (r, c) not in expected_key_abs:
                errors.append(f"unexpected colored cell outside frame at {(r, c)}")

    # Every expected projected block is either a complete reference or absent.
    role_at = _role_map(variant)
    reference_set = set(variant.reference_cells)
    bs = variant.block_size
    origin_r, origin_c = variant.output_origin
    for key_pos, role in role_at.items():
        dr, dc = key_pos
        expected_color = role_colors.get(role)
        if expected_color is None:
            continue
        top = frame_top + origin_r + dr * bs
        left = frame_left + origin_c + dc * bs
        cells = [grid[top + rr][left + cc] for rr in range(bs) for cc in range(bs)]
        if key_pos in reference_set:
            if any(value != expected_color for value in cells):
                errors.append(f"reference block {key_pos} is not a full {bs}x{bs} role-{role} square")
        elif any(value != 0 for value in cells):
            errors.append(f"non-reference projected block {key_pos} must be absent from the input")

    # No interior colored material may exist outside the projected block cells.
    allowed_inside: set[tuple[int, int]] = set()
    for dr, dc in reference_set:
        top = frame_top + origin_r + dr * bs
        left = frame_left + origin_c + dc * bs
        allowed_inside.update(
            (top + rr, left + cc) for rr in range(bs) for cc in range(bs)
        )
    corner_set = _corners(variant)
    for r in range(frame_top, frame_bottom + 1):
        for c in range(frame_left, frame_right + 1):
            value = grid[r][c]
            if (r, c) in corner_set:
                if value != 4:
                    errors.append(f"frame corner {(r, c)} is not yellow")
            elif (r, c) in allowed_inside:
                if value in (0, 4):
                    errors.append(f"reference material missing at {(r, c)}")
            elif value != 0:
                errors.append(f"unexpected interior colored cell at {(r, c)}")

    palette = {value for row in grid for value in row}
    if len(palette) != 5 or not {0, 4}.issubset(palette):
        errors.append(f"expected exact five-color palette including 0 and 4, got {sorted(palette)}")

    # Occupancy is connected independent of color, so the key is one structural object.
    remaining = set(key_positions)
    if remaining:
        stack = [next(iter(remaining))]
        seen: set[tuple[int, int]] = set()
        while stack:
            cell = stack.pop()
            if cell in seen:
                continue
            seen.add(cell)
            r, c = cell
            stack.extend(
                neighbor
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                if neighbor in remaining and neighbor not in seen
            )
        if seen != remaining:
            errors.append("key occupancy is not 4-connected")

    if errors:
        return None, sorted(set(errors))
    return Analysis(variant_name, variant, role_colors), []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural defects for this task's exact canonical grammar."""
    _analysis, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is deliberately the four canonical profiles."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def observe_overrides(grid) -> dict[str, str]:
    """Recover both declared axes from the returned grid itself."""
    analysis, errors = _analyze(grid)
    if errors or analysis is None:
        return {"scene_variant": "unknown", "palette_band": "unknown"}
    palette_band = "high" if max(analysis.role_colors.values()) >= 6 else "low"
    return {"scene_variant": analysis.variant_name, "palette_band": palette_band}


def _choose_colors(ctx, palette_band: str) -> dict[str, int]:
    rng = ctx.draw_rng("role_colors")
    if palette_band == "low":
        colors = rng.sample([1, 2, 3, 5], 3)
    else:
        high = rng.choice([6, 7, 8, 9])
        pool = [color for color in (1, 2, 3, 5, 6, 7, 8, 9) if color != high]
        colors = [high, *rng.sample(pool, 2)]
    return dict(zip(("a", "b", "c"), colors))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band_shift = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    scheduled_variant = VARIANT_NAMES[(int(sample_index) + band_shift) % len(VARIANT_NAMES)]
    variant_name = _scheduled_choice(
        ctx, "scene_variant", scheduled_variant, VARIANT_NAMES
    )
    scheduled_palette = "low" if (int(sample_index) + band_shift) % 2 == 0 else "high"
    palette_band = _scheduled_choice(
        ctx, "palette_band", scheduled_palette, PALETTE_KINDS
    )
    variant = VARIANTS[variant_name]
    role_colors = _choose_colors(ctx, palette_band)

    grid = full_grid(variant.grid_h, variant.grid_w, 0)
    for r, c in _corners(variant):
        grid[r][c] = 4

    role_at = _role_map(variant)
    bs = variant.block_size
    origin_r, origin_c = variant.output_origin
    for dr, dc in variant.reference_cells:
        role = role_at[(dr, dc)]
        draw_rect(
            grid,
            variant.frame_top + origin_r + dr * bs,
            variant.frame_left + origin_c + dc * bs,
            bs,
            bs,
            role_colors[role],
        )

    for dr, dc, role in variant.key_roles:
        grid[variant.key_top + dr][variant.key_left + dc] = role_colors[role]
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for semantic tests; Racket remains authority."""
    analysis, errors = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("; ".join(errors))
    variant = analysis.variant
    out = full_grid(variant.frame_h, variant.frame_w, 0)
    out[0][0] = 4
    out[0][-1] = 4
    out[-1][0] = 4
    out[-1][-1] = 4
    bs = variant.block_size
    origin_r, origin_c = variant.output_origin
    for dr, dc, role in variant.key_roles:
        draw_rect(
            out,
            origin_r + dr * bs,
            origin_c + dc * bs,
            bs,
            bs,
            analysis.role_colors[role],
        )
    return out


def _analysis_or_none(grid):
    analysis, errors = _analyze(grid)
    return None if errors else analysis


def _is_variant(name: str):
    return lambda grid: (
        (analysis := _analysis_or_none(grid)) is not None
        and analysis.variant_name == name
    )


def _has_block_size(size: int):
    return lambda grid: (
        (analysis := _analysis_or_none(grid)) is not None
        and analysis.variant.block_size == size
    )


def _reference_count(grid) -> int:
    analysis = _analysis_or_none(grid)
    if analysis is None:
        return 0
    return len(analysis.variant.reference_cells)


SEMANTIC_WITNESSES = {
    "small_square_key": _is_variant("small_square"),
    "medium_hook_key": _is_variant("medium_hook"),
    "wide_arch_key": _is_variant("wide_arch"),
    "large_tee_key": _is_variant("large_tee"),
    "block_size_2": _has_block_size(2),
    "block_size_3": _has_block_size(3),
    "block_size_4": _has_block_size(4),
    "two_reference_blocks": lambda grid: _reference_count(grid) == 2,
    "three_reference_blocks": lambda grid: _reference_count(grid) == 3,
    "non_square_frame": lambda grid: (
        (analysis := _analysis_or_none(grid)) is not None
        and analysis.variant.frame_h != analysis.variant.frame_w
    ),
}


def _crop_only(grid, analysis: Analysis) -> list[list[int]]:
    v = analysis.variant
    return [
        row[v.frame_left : v.frame_left + v.frame_w]
        for row in grid[v.frame_top : v.frame_top + v.frame_h]
    ]


def _paint_scaled(
    analysis: Analysis,
    *,
    scale: int,
    origin: tuple[int, int],
    fill_holes: bool = False,
) -> list[list[int]]:
    v = analysis.variant
    out = full_grid(v.frame_h, v.frame_w, 0)
    out[0][0] = out[0][-1] = out[-1][0] = out[-1][-1] = 4
    role_at = _role_map(v)
    positions = set(role_at)
    if fill_holes:
        max_r = max(r for r, _ in positions)
        max_c = max(c for _, c in positions)
        positions = {(r, c) for r in range(max_r + 1) for c in range(max_c + 1)}
    for dr, dc in positions:
        role = role_at.get((dr, dc), "a")
        color = analysis.role_colors[role]
        top = origin[0] + dr * scale
        left = origin[1] + dc * scale
        for rr in range(scale):
            for cc in range(scale):
                r, c = top + rr, left + cc
                if 0 <= r < v.frame_h and 0 <= c < v.frame_w:
                    out[r][c] = color
    return out


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    analysis, errors = _analyze(grid)
    if errors or analysis is None:
        return None
    v = analysis.variant
    truth = rule_mirror(grid)
    outputs = {
        "crop_existing_references": _crop_only(grid, analysis),
        "unscaled_key": _paint_scaled(analysis, scale=1, origin=v.output_origin),
        "fixed_scale_2": _paint_scaled(analysis, scale=2, origin=v.output_origin),
        "fixed_scale_3": _paint_scaled(analysis, scale=3, origin=v.output_origin),
        "fixed_scale_4": _paint_scaled(analysis, scale=4, origin=v.output_origin),
        "fixed_top_left_alignment": _paint_scaled(
            analysis, scale=v.block_size, origin=(1, 1)
        ),
        "solid_key_bbox": _paint_scaled(
            analysis,
            scale=v.block_size,
            origin=v.output_origin,
            fill_holes=True,
        ),
        "key_itself_is_answer": [
            [
                analysis.role_colors.get(_role_map(v).get((r, c), ""), 0)
                for c in range(max(dc for _, dc, _ in v.key_roles) + 1)
            ]
            for r in range(max(dr for dr, _, _ in v.key_roles) + 1)
        ],
    }
    # A competitor identical on this input is harmless; answer-equivalence is
    # handled by lesson_identifiable when comparing the query output.
    outputs["truth"] = truth
    return outputs


def lesson_identifiable(demos, query) -> list[str]:
    """Reject demo windows that leave a shortcut with a different query answer."""
    reasons: list[str] = []
    query_competitors = _competitor_outputs(query.get("input"))
    if query_competitors is None:
        return ["query input is not lawful for this task"]
    query_truth = rule_mirror(query["input"])

    prepared: list[tuple[dict, dict[str, list[list[int]]]]] = []
    for index, demo in enumerate(demos):
        competitors = _competitor_outputs(demo.get("input"))
        if competitors is None:
            reasons.append(f"demo {index} input is not lawful for this task")
            continue
        expected = rule_mirror(demo["input"])
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the rule mirror")
            continue
        prepared.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        if name == "truth":
            continue
        survives = all(outputs[name] == demo["output"] for demo, outputs in prepared)
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule {name!r} matches every demo but answers the query differently"
            )
    return sorted(set(reasons))
