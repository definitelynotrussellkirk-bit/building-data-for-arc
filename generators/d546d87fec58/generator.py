"""Generator for ARC task d546d87fec58 (source task b8825c91).

A fully horizontal-and-vertical-symmetric colored image is partially erased by
one or more rectangular yellow (color 4) masks.  The executable rule preserves
visible cells and reconstructs each erased cell from the first available
counterpart in this order: 180-degree rotation, horizontal reflection, then
vertical reflection.

The public examples only need the 180-degree branch.  The two fallback profiles
below keep the same fully symmetric latent image, so every available counterpart
has the same answer; they exercise the executable branches without teaching
priority conflicts that the source task does not support.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "d546d87fec58"
TASK_ID = "d546d87fec58"
VERSION = "3.1.0"
# Re-pinned 2026-07-24: the canonical rule now precomputes (rotate-180 g)/
# (flip-lr g)/(flip-ud g) instead of recomputing mirrored indices inline.
# Same semantics (verified 4/4 train + 1/1 test), new normalized hash.
RULE_HASH = "5c0ceb196b2a"

SUMMARY = (
    "Start with a square image that is symmetric across the horizontal and "
    "vertical axes (and therefore under 180-degree rotation). Rectangular "
    "yellow regions are missing data. Keep every non-yellow cell unchanged; "
    "for each yellow cell, copy the first non-yellow value found at its "
    "180-degree, horizontal, then vertical mirror counterpart."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the completed image is symmetric horizontally, vertically, and by 180-degree rotation",
    "color 4 marks one to three filled rectangular missing-data regions",
    "every color-4 cell has at least one visible mirror counterpart and is reconstructed",
    "all visible mirror counterparts of an erased cell agree on the same latent color",
    "the latent palette contains 2..8 colors from 1..9 excluding color 4",
]

MASK_PROFILES = (
    "rot180",
    "horizontal_fallback",
    "mixed_fallback",
)

AXES = {
    "grid_size": {
        "type": "int",
        "default": "one-third canonical anchor 16; otherwise difficulty-weighted 10..20",
        "valid": "10..20",
    },
    "palette_size": {
        "type": "int",
        "default": "one-third canonical anchor 7..8; otherwise difficulty-weighted 2..8",
        "valid": "2..8",
    },
    "block_h": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
    },
    "block_w": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
    },
    "mask_profile": {
        "type": "str",
        "default": "cyclic by sample_index; every 3 consecutive instances cover all profiles",
        "valid": "rot180|horizontal_fallback|mixed_fallback",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ALLOWED_BASE_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_ROT180_INDEX = {0: 3, 1: 2, 2: 1, 3: 0}


def _validate_controls(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name in ("grid_size", "palette_size", "block_h", "block_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} override must be an integer")
    if "mask_profile" in overrides and overrides["mask_profile"] is not None:
        if not isinstance(overrides["mask_profile"], str):
            raise TypeError("mask_profile override must be a string")


def _draw_curriculum_int(
    ctx,
    label: str,
    lo: int,
    hi: int,
    canonical_values: tuple[int, ...],
    *,
    canonical_profile: bool,
) -> int:
    """Draw a canonical anchor unless an exact caller override takes precedence."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_diff(label, lo, hi)
    if canonical_profile:
        return ctx.draw_choice(label, canonical_values)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_mask_profile(ctx, sample_index: int) -> str:
    """Guarantee every visible four-example window contains a fallback case."""
    if "mask_profile" in ctx.overrides and ctx.overrides["mask_profile"] is not None:
        return ctx.draw_choice("mask_profile", MASK_PROFILES)
    scheduled = MASK_PROFILES[sample_index % len(MASK_PROFILES)]
    # Keep the deterministic lesson schedule while recording this exact axis
    # through the public keyed-draw API used by override/provenance audits.
    return ctx.draw_choice("mask_profile", (scheduled,))


def _symmetry_orbit(size: int, row: int, col: int) -> set[tuple[int, int]]:
    return {
        (row, col),
        (row, size - 1 - col),
        (size - 1 - row, col),
        (size - 1 - row, size - 1 - col),
    }


def _orbit_representative(size: int, row: int, col: int) -> tuple[int, int]:
    return min(row, size - 1 - row), min(col, size - 1 - col)


def _draw_symmetric_base(
    size: int,
    palette: tuple[int, ...],
    rng,
    forced_orbits: dict[tuple[int, int], int],
) -> list[list[int]]:
    representatives = [
        (row, col)
        for row in range((size + 1) // 2)
        for col in range((size + 1) // 2)
    ]
    rng.shuffle(representatives)

    orbit_colors = dict(forced_orbits)
    missing_colors = [color for color in palette if color not in orbit_colors.values()]
    available = [rep for rep in representatives if rep not in orbit_colors]
    if len(available) < len(missing_colors):
        raise ValueError("grid is too small to realize the requested palette")
    for representative, color in zip(available, missing_colors):
        orbit_colors[representative] = color
    for representative in representatives:
        orbit_colors.setdefault(representative, rng.choice(palette))

    grid = [[palette[0] for _col in range(size)] for _row in range(size)]
    for (row, col), color in orbit_colors.items():
        for rr, cc in _symmetry_orbit(size, row, col):
            grid[rr][cc] = color
    return grid


def _corner_rectangles(
    size: int,
    block_h: int,
    block_w: int,
    rng,
) -> tuple[tuple[int, int, int, int], ...]:
    # Keep at least one unmasked row and column between mirrored copies, so
    # connected-component dimensions remain exactly observable at all bounds.
    max_row = (size - 2 * block_h - 1) // 2
    max_col = (size - 2 * block_w - 1) // 2
    if max_row < 0 or max_col < 0:
        raise ValueError(
            f"block {block_h}x{block_w} is incompatible with grid_size={size}"
        )
    row = rng.randint(0, max_row)
    col = rng.randint(0, max_col)
    return (
        (row, col, block_h, block_w),
        (row, size - col - block_w, block_h, block_w),
        (size - row - block_h, col, block_h, block_w),
        (size - row - block_h, size - col - block_w, block_h, block_w),
    )


def _profile_rectangles(
    rectangles: tuple[tuple[int, int, int, int], ...],
    profile: str,
    variant: int,
) -> tuple[tuple[int, int, int, int], ...]:
    if profile == "rot180":
        indexes = (variant,)
    elif profile == "horizontal_fallback":
        indexes = (variant, _ROT180_INDEX[variant])
    elif profile == "mixed_fallback":
        indexes = tuple(index for index in range(4) if index != variant)
    else:  # draw_choice validates this, but keep the helper fail-closed.
        raise ValueError(f"unknown mask_profile: {profile!r}")
    return tuple(rectangles[index] for index in indexes)


def _paint_rectangles(
    grid: list[list[int]],
    rectangles: Iterable[tuple[int, int, int, int]],
) -> None:
    for row, col, height, width in rectangles:
        for rr in range(row, row + height):
            for cc in range(col, col + width):
                grid[rr][cc] = 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally valid teaching input."""
    _validate_controls(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # One third of lessons anchor the official 16x16, 8/9-input-color scale
    # in every difficulty band.  The broad branch preserves the full difficulty-shaped
    # range, and exact caller overrides still take precedence in either branch.
    canonical_profile = ctx.draw_choice(
        "curriculum_profile",
        ("canonical", "broad", "broad"),
    ) == "canonical"
    size = _draw_curriculum_int(
        ctx,
        "grid_size",
        10,
        20,
        (16,),
        canonical_profile=canonical_profile,
    )
    palette_size = _draw_curriculum_int(
        ctx,
        "palette_size",
        2,
        8,
        (7, 8),
        canonical_profile=canonical_profile,
    )
    block_h = ctx.draw_int_diff("block_h", 2, 4)
    block_w = ctx.draw_int_diff("block_w", 2, 4)
    profile = _draw_mask_profile(ctx, sample_index)

    palette_rng = ctx.draw_rng("palette")
    palette_pool = list(_ALLOWED_BASE_COLORS)
    palette_rng.shuffle(palette_pool)
    palette = tuple(palette_pool[:palette_size])

    all_rectangles = _corner_rectangles(
        size,
        block_h,
        block_w,
        ctx.draw_rng("mask_anchor"),
    )
    variant = ctx.draw_rng("mask_variant").randrange(4)
    selected = _profile_rectangles(all_rectangles, profile, variant)

    # Canonical masks cover multiple latent colors.  Force two distinct answer
    # orbits under every generated mask, while seeding every remaining palette
    # color on another orbit so palette_size stays exact at all boundaries.
    answer_cells = (selected[0][:2], (selected[0][0], selected[0][1] + 1))
    forced_orbits = {
        _orbit_representative(size, row, col): color
        for (row, col), color in zip(answer_cells, palette[:2])
    }
    base = _draw_symmetric_base(
        size,
        palette,
        ctx.draw_rng("base_pattern"),
        forced_orbits,
    )

    grid = [row[:] for row in base]
    _paint_rectangles(grid, selected)

    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise RuntimeError(
            "internal generator invariant failure: "
            + "; ".join(analysis["errors"])
        )
    observed = _observable_axes(analysis)
    expected = {
        "grid_size": size,
        "palette_size": palette_size,
        "block_h": block_h,
        "block_w": block_w,
        "mask_profile": profile,
    }
    if observed != expected:
        raise RuntimeError(
            f"internal override drift: expected {expected!r}, observed {observed!r}"
        )
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket rule for tests/audits."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4:
                continue
            counterparts = (
                ("rot180", height - 1 - row, width - 1 - col),
                ("horizontal", row, width - 1 - col),
                ("vertical", height - 1 - row, col),
            )
            for _branch, rr, cc in counterparts:
                if grid[rr][cc] != 4:
                    output[row][col] = grid[rr][cc]
                    break
    return output


# Keep the historical private name for local probes that imported it.
_apply_rule = rule_mirror


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return None, ["grid rows must be nonempty sequences"]
    width = len(first)
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _mask_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                candidate = (row + dr, col + dc)
                if candidate in remaining:
                    remaining.remove(candidate)
                    component.add(candidate)
                    queue.append(candidate)
        components.append(component)
    return components


def _component_box(component: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _col in component]
    cols = [col for _row, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def _is_filled_rectangle(component: set[tuple[int, int]]) -> bool:
    row1, col1, row2, col2 = _component_box(component)
    return component == {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
    }


def _is_full_symmetric(grid: list[list[int]]) -> bool:
    height = len(grid)
    width = len(grid[0])
    return all(
        value == grid[row][width - 1 - col]
        and value == grid[height - 1 - row][col]
        and value == grid[height - 1 - row][width - 1 - col]
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )


def _branch_facts(grid: list[list[int]]) -> dict[str, Any]:
    height = len(grid)
    width = len(grid[0])
    counts: Counter[str] = Counter()
    conflicts = 0
    unresolved = 0
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 4:
                continue
            counterparts = (
                ("rot180", height - 1 - row, width - 1 - col),
                ("horizontal", row, width - 1 - col),
                ("vertical", height - 1 - row, col),
            )
            available = [
                (branch, grid[rr][cc])
                for branch, rr, cc in counterparts
                if grid[rr][cc] != 4
            ]
            if not available:
                unresolved += 1
                continue
            counts[available[0][0]] += 1
            if len({candidate for _branch, candidate in available}) > 1:
                conflicts += 1
    branches = set(counts)
    if unresolved:
        profile = None
    elif branches == {"rot180"}:
        profile = "rot180"
    elif branches == {"horizontal"}:
        profile = "horizontal_fallback"
    elif branches == {"rot180", "horizontal", "vertical"}:
        profile = "mixed_fallback"
    else:
        profile = None
    return {
        "counts": dict(counts),
        "conflicts": conflicts,
        "unresolved": unresolved,
        "mask_profile": profile,
    }


def _analyze_scene(grid: Any) -> dict[str, Any]:
    coerced, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    assert coerced is not None
    height = len(coerced)
    width = len(coerced[0])
    if height != width:
        errors.append(f"grid must be square, got {height}x{width}")
    if not 10 <= height <= 20:
        errors.append(f"grid_size must be in 10..20, got {height}")

    components = _mask_components(coerced)
    if not components:
        errors.append("at least one color-4 missing-data rectangle is required")
    elif not 1 <= len(components) <= 3:
        errors.append("color 4 must form one to three connected rectangles")

    component_dims: list[tuple[int, int]] = []
    for index, component in enumerate(components):
        if not _is_filled_rectangle(component):
            errors.append(f"color-4 component {index} is not a filled rectangle")
            continue
        row1, col1, row2, col2 = _component_box(component)
        dims = (row2 - row1 + 1, col2 - col1 + 1)
        component_dims.append(dims)
        if not (2 <= dims[0] <= 4 and 2 <= dims[1] <= 4):
            errors.append(
                f"color-4 component {index} has unsupported size {dims[0]}x{dims[1]}"
            )

    branch_facts = _branch_facts(coerced)
    if branch_facts["unresolved"]:
        errors.append(
            f"{branch_facts['unresolved']} color-4 cells have no visible mirror counterpart"
        )
    if branch_facts["conflicts"]:
        errors.append(
            f"{branch_facts['conflicts']} color-4 cells have disagreeing visible mirror values"
        )
    if branch_facts["mask_profile"] is None and components:
        errors.append("mask topology does not match a supported executable branch profile")

    output = rule_mirror(coerced)
    if any(value == 4 for row in output for value in row):
        errors.append("mirror reconstruction leaves unresolved color-4 cells")
    if output == coerced:
        errors.append("mirror reconstruction must change the input")
    if not _is_full_symmetric(output):
        errors.append("the reconstructed image is not fully mirror symmetric")

    palette = {value for row in output for value in row}
    if 0 in palette or 4 in palette:
        errors.append("the latent image palette must exclude colors 0 and 4")
    if not 2 <= len(palette) <= 8:
        errors.append(
            f"the latent image must use 2..8 colors, got {len(palette)}"
        )

    return {
        "errors": errors,
        "grid": coerced,
        "output": output,
        "grid_size": height,
        "palette_size": len(palette),
        "palette": tuple(sorted(palette)),
        "components": components,
        "component_dims": component_dims,
        "branch_counts": branch_facts["counts"],
        "mask_profile": branch_facts["mask_profile"],
        "branch_conflicts": branch_facts["conflicts"],
        "unresolved": branch_facts["unresolved"],
    }


def _observable_axes(analysis: dict[str, Any]) -> dict[str, Any]:
    if analysis.get("errors"):
        return {}
    dimensions = set(analysis["component_dims"])
    if len(dimensions) != 1:
        # Canonical inputs legitimately use differently sized rectangles.  They
        # remain valid lessons, but do not claim exact block_h/block_w controls.
        return {
            "grid_size": analysis["grid_size"],
            "palette_size": analysis["palette_size"],
            "mask_profile": analysis["mask_profile"],
        }
    block_h, block_w = next(iter(dimensions))
    return {
        "grid_size": analysis["grid_size"],
        "palette_size": analysis["palette_size"],
        "block_h": block_h,
        "block_w": block_w,
        "mask_profile": analysis["mask_profile"],
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis when the scene encodes one value."""
    return _observable_axes(_analyze_scene(grid))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or noncanonical teaching scenes."""
    del difficulty, meta
    return list(_analyze_scene(grid)["errors"])

# Semantic contract ---------------------------------------------------------
# The official examples are all solvable by the cheaper rotate-180-only rule.
# Fallback-profile lessons are therefore the task-local counterexamples that
# prove the generated curriculum teaches the selected three-branch authority.
MIN_STRICT_FRAC = 1.0


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid falls outside this generator's lawful manifold."""
    return self_check(grid)


def _rot180_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: repair yellow cells only from 180-degree mirrors."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 4:
                continue
            rr, cc = height - 1 - row, width - 1 - col
            if grid[rr][cc] != 4:
                output[row][col] = grid[rr][cc]
    return output


def _fallback_required(grid: list[list[int]]) -> bool:
    return _branch_facts(grid)["mask_profile"] in {
        "horizontal_fallback",
        "mixed_fallback",
    }


SEMANTIC_WITNESSES = {"fallback_required": _fallback_required}
SEMANTIC_RIVALS = {"rot180_only": _rot180_only}
WITNESS_RIVALS = {"fallback_required": ["rot180_only"]}
CANONICAL_SHORTCUTS = {"rot180_only": _rot180_only}
LESSON_COMPETITORS = {"rot180_only": _rot180_only}

