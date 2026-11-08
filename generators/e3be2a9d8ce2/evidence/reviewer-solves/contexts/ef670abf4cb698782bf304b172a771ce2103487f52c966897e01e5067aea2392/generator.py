"""Generator for ARC task 705a3229 (task_id e3be2a9d8ce2).

Each isolated nonzero input cell emits an L-shaped ray in the output: its
vertical arm reaches the nearer top/bottom edge and its horizontal arm reaches
the nearer left/right edge.  On an exact odd-grid tie the canonical rule uses
the bottom/right direction.  Generated emitters have disjoint complete ray
footprints, so lessons never depend on the canonical program's otherwise
undemonstrated row-major overlap precedence.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e3be2a9d8ce2"
VERSION = "3.1.0"
TASK_ID = "e3be2a9d8ce2"
RULE_HASH = "116a1aaf2218"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An 8..22 by 8..22 zero-background grid contains 1..8 isolated interior "
    "colored pixels.  For each pixel at (r,c), the output keeps the pixel and "
    "draws one vertical arm to its nearer top/bottom edge plus one horizontal "
    "arm to its nearer left/right edge.  Exact center ties on odd dimensions "
    "resolve toward bottom and right, matching the canonical strict-less-than "
    "rule.  Generated complete L-ray footprints are pairwise disjoint, so each "
    "lesson has a unique answer without relying on unshown overlap precedence."
)

INVARIANTS = [
    "background is 0 and dimensions are 8..22 by 8..22",
    "there are 1..8 nonzero pixels, including the canonical one-pixel branch",
    "all emitters are interior and no two are orthogonally adjacent",
    "the complete nearer-edge L-ray footprints of emitters are pairwise disjoint",
    "odd-grid center ties point down/right under the canonical rule",
]

PALETTE_KINDS = ("canonical", "warm", "cool", "broad")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased", "valid": "8..22"},
    "grid_w": {"type": "int", "default": "difficulty-biased", "valid": "8..22"},
    "n_pixels": {"type": "int", "default": "difficulty-biased", "valid": "1..8"},
    "palette_kind": {
        "type": "enum",
        "default": "keyed random",
        "valid": "|".join(PALETTE_KINDS),
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-biased and <= n_pixels",
        "valid": "1..6",
    },
}

_PROFILES = (
    "balanced",
    "top",
    "bottom",
    "left",
    "right",
    "ties",
    "scattered",
)

# Exact (height, width, nonzero-emitter count, nonzero-palette size) profiles
# observed in the linked canonical task.  One unpinned draw in every four uses
# this cycle so every difficulty band retains joint canonical-profile support.
_CANONICAL_PROFILES = (
    (12, 10, 3, 3),
    (14, 15, 2, 2),
    (11, 8, 1, 1),
    (12, 12, 2, 2),
    (11, 16, 4, 4),
)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_INTEGER_AXES = {
    "grid_h": (8, 22),
    "grid_w": (8, 22),
    "n_pixels": (1, 8),
    "palette_size": (1, 6),
}


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer (not bool/float/string)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, (low, high) in _INTEGER_AXES.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not low <= value <= high:
            raise ValueError(
                f"{name} override must be a literal integer in [{low}, {high}]"
            )
    palette_kind = overrides.get("palette_kind")
    if palette_kind is not None and (
        type(palette_kind) is not str or palette_kind not in PALETTE_KINDS
    ):
        raise ValueError(
            f"palette_kind override must be one of {PALETTE_KINDS}"
        )


def _parse_int_override(
    overrides: dict[str, Any], name: str, low: int, high: int
) -> int | None:
    value = overrides.get(name)
    if value is None:
        return None
    if type(value) is not int:
        raise ValueError(f"{name} override must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} override {value} outside [{low}, {high}]")
    return value


def _dimension_values(difficulty: str | None, *, odd_only: bool) -> list[int]:
    if difficulty == "easy":
        values = list(range(8, 13))
    elif difficulty == "hard":
        values = list(range(18, 23))
    else:
        values = list(range(12, 19))
    if odd_only:
        values = [value for value in values if value % 2 == 1]
    return values


def _draw_dimension(ctx, name: str, difficulty: str | None, *, odd_only: bool) -> int:
    # Explicit boundaries remain valid in every difficulty band.  The restricted
    # default option list is only a sampling prior, never an override validity gate.
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, 8, 22)
    return ctx.draw_choice(name, _dimension_values(difficulty, odd_only=odd_only))


def _palette(kind: str, size: int, rng) -> list[int]:
    pools = {
        "canonical": [3, 5, 8, 9, 4, 6, 1, 2, 7],
        "warm": [2, 3, 4, 6, 9, 1, 5, 7, 8],
        "cool": [1, 5, 7, 8, 6, 2, 3, 4, 9],
        "broad": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    }
    values = list(pools[kind])
    rng.shuffle(values)
    return values[:size]


def _go_up(height: int, row: int) -> bool:
    return 2 * row < height - 1


def _go_left(width: int, col: int) -> bool:
    return 2 * col < width - 1


def _direction_tag(height: int, width: int, row: int, col: int) -> str:
    return ("T" if _go_up(height, row) else "B") + (
        "L" if _go_left(width, col) else "R"
    )


def _ray_cells(height: int, width: int, row: int, col: int) -> frozenset[tuple[int, int]]:
    vertical = (
        ((r, col) for r in range(0, row + 1))
        if _go_up(height, row)
        else ((r, col) for r in range(row, height))
    )
    horizontal = (
        ((row, c) for c in range(0, col + 1))
        if _go_left(width, col)
        else ((row, c) for c in range(col, width))
    )
    return frozenset((*vertical, *horizontal))


def _compatible(
    candidate: tuple[int, int],
    footprint: frozenset[tuple[int, int]],
    selected: list[tuple[int, int]],
    occupied_rays: set[tuple[int, int]],
) -> bool:
    row, col = candidate
    if footprint & occupied_rays:
        return False
    return all(abs(row - r) + abs(col - c) >= 2 for r, c in selected)


def _profile_score(
    profile: str, height: int, width: int, row: int, col: int
) -> tuple[int, int]:
    tag = _direction_tag(height, width, row, col)
    tie_count = int(2 * row == height - 1) + int(2 * col == width - 1)
    edge_distance = min(row, height - 1 - row) + min(col, width - 1 - col)
    preferred = {
        "top": tag.startswith("T"),
        "bottom": tag.startswith("B"),
        "left": tag.endswith("L"),
        "right": tag.endswith("R"),
        "ties": tie_count > 0,
    }.get(profile, False)
    if profile == "ties":
        return (-tie_count, edge_distance)
    if profile == "balanced":
        return (0, edge_distance)
    if profile == "scattered":
        return (0, -edge_distance)
    return (0 if preferred else 1, edge_distance)


def _profile_satisfied(
    profile: str,
    height: int,
    width: int,
    selected: Iterable[tuple[int, int]],
) -> bool:
    points = list(selected)
    tags = {_direction_tag(height, width, row, col) for row, col in points}
    if profile == "balanced" and len(points) >= 4:
        return {"TL", "TR", "BL", "BR"} <= tags
    if profile == "top":
        return any(tag.startswith("T") for tag in tags)
    if profile == "bottom":
        return any(tag.startswith("B") for tag in tags)
    if profile == "left":
        return any(tag.endswith("L") for tag in tags)
    if profile == "right":
        return any(tag.endswith("R") for tag in tags)
    if profile == "ties":
        return (
            any(2 * row == height - 1 for row, _ in points)
            and any(2 * col == width - 1 for _, col in points)
        )
    return True


def _select_positions(ctx, height: int, width: int, count: int, profile: str) -> list[tuple[int, int]]:
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    footprints = {
        point: _ray_cells(height, width, point[0], point[1])
        for point in candidates
    }
    best: list[tuple[int, int]] = []
    # Randomized greedy is fast on this geometry; retries are independently keyed
    # so the exact result remains deterministic and adding later draws cannot move it.
    for attempt in range(192):
        ordered = list(candidates)
        ctx.draw_rng(f"placement_attempt_{attempt}").shuffle(ordered)
        ordered.sort(
            key=lambda point: _profile_score(
                profile, height, width, point[0], point[1]
            )
        )
        selected: list[tuple[int, int]] = []
        occupied_rays: set[tuple[int, int]] = set()
        for point in ordered:
            footprint = footprints[point]
            if not _compatible(point, footprint, selected, occupied_rays):
                continue
            selected.append(point)
            occupied_rays.update(footprint)
            if len(selected) == count:
                if _profile_satisfied(profile, height, width, selected):
                    return selected
                break
        if len(selected) > len(best):
            best = selected

    # A profile is a sampling schedule, not a user-facing axis.  If its preferred
    # witness was geometrically too restrictive, retain the lawful exact-count
    # scene rather than silently changing a caller override.
    if len(best) >= count:
        return best[:count]
    raise ValueError(
        f"could not place {count} disjoint ray emitters on {height}x{width}; "
        f"best lawful placement had {len(best)}"
    )


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every exact numeric axis from the returned input grid."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    colors = [value for row in grid for value in row if value != 0]
    return {
        "grid_h": height,
        "grid_w": width,
        "n_pixels": len(colors),
        "palette_size": len(set(colors)),
    }


def self_check(
    grid: list[list[int]], *, difficulty=None, meta=None
) -> list[str]:
    """Reject malformed or ambiguous lessons while accepting every canonical input."""
    del difficulty
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 22 or not 8 <= width <= 22:
        errors.append(f"expected dimensions in 8..22; got {height}x{width}")

    emitters = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not 1 <= len(emitters) <= 8:
        errors.append(f"expected 1..8 nonzero emitters; got {len(emitters)}")
    if not emitters:
        return errors

    for row, col, _ in emitters:
        if row in (0, height - 1) or col in (0, width - 1):
            errors.append("every ray emitter must be strictly interior")
            break

    for index, (row, col, _) in enumerate(emitters):
        for other_row, other_col, _ in emitters[index + 1 :]:
            if abs(row - other_row) + abs(col - other_col) < 2:
                errors.append("ray emitters may not be orthogonally adjacent")
                break
        if errors and errors[-1].startswith("ray emitters may"):
            break

    footprints: list[frozenset[tuple[int, int]]] = []
    for row, col, _ in emitters:
        footprint = _ray_cells(height, width, row, col)
        if any(footprint & previous for previous in footprints):
            errors.append(
                "complete L-ray footprints must be pairwise disjoint to avoid "
                "unshown overlap precedence"
            )
            break
        footprints.append(footprint)

    observed = observe_overrides(grid)
    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(overrides, dict):
        for axis, requested in overrides.items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed "
                    f"{observed[axis]!r}"
                )
    return errors


def _transform_with_arms(
    grid: list[list[int]], *, vertical: bool, horizontal: bool
) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid ray input: " + "; ".join(errors))
    height = len(grid)
    width = len(grid[0])
    emitters = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            for source_row, source_col, color in emitters:
                on_vertical = vertical and col == source_col and (
                    (row <= source_row)
                    if _go_up(height, source_row)
                    else (row >= source_row)
                )
                on_horizontal = horizontal and row == source_row and (
                    (col <= source_col)
                    if _go_left(width, source_col)
                    else (col >= source_col)
                )
                if on_vertical or on_horizontal:
                    output[row][col] = color
                    break
    return output


def diagnostic_transform(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the pinned canonical Racket rule."""
    return _transform_with_arms(grid, vertical=True, horizontal=True)


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    """The production grammar is deliberately a strict canonical-like manifold."""
    return self_check(grid)


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_vertical_only(grid: list[list[int]]) -> list[list[int]]:
    return _transform_with_arms(grid, vertical=True, horizontal=False)


def _rival_horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    return _transform_with_arms(grid, vertical=False, horizontal=True)


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "vertical_only": _rival_vertical_only,
    "horizontal_only": _rival_horizontal_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "nontrivial_ray_growth": lambda grid: diagnostic_transform(grid)
    != [list(row) for row in grid],
    "horizontal_arm_visible": lambda grid: diagnostic_transform(grid)
    != _rival_vertical_only(grid),
    "vertical_arm_visible": lambda grid: diagnostic_transform(grid)
    != _rival_horizontal_only(grid),
}
WITNESS_RIVALS = {
    "nontrivial_ray_growth": ["identity"],
    "horizontal_arm_visible": ["vertical_only"],
    "vertical_arm_visible": ["horizontal_only"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Reject lessons where a declared wrong rule survives every demonstration."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = diagnostic_transform(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} has invalid input: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the nearer-edge L-ray rule")
            continue
        valid_demos.append(pair)
    try:
        query_expected = diagnostic_transform(query["input"])
    except (TypeError, ValueError) as exc:
        reasons.append(f"query has invalid input: {exc}")
        query_expected = None
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            if query_expected is not None and rival(query["input"]) != query_expected:
                reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)

    requested_n = _parse_int_override(overrides, "n_pixels", 1, 8)
    requested_palette = _parse_int_override(overrides, "palette_size", 1, 6)
    if (
        requested_n is not None
        and requested_palette is not None
        and requested_palette > requested_n
    ):
        raise ValueError(
            "palette_size cannot exceed n_pixels because every palette color "
            "must be observable in the returned grid"
        )

    profile = _PROFILES[int(sample_index) % len(_PROFILES)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    effective_overrides = any(value is not None for value in overrides.values())
    use_canonical_profile = sample_index % 4 == 0 and not effective_overrides
    if use_canonical_profile:
        height, width, n_pixels, palette_size = _CANONICAL_PROFILES[
            (sample_index // 4) % len(_CANONICAL_PROFILES)
        ]
        height = ctx.draw_choice("grid_h", (height,))
        width = ctx.draw_choice("grid_w", (width,))
        n_pixels = ctx.draw_choice("n_pixels", (n_pixels,))
        palette_size = ctx.draw_choice("palette_size", (palette_size,))
    else:
        odd_only = profile == "ties"
        height = _draw_dimension(ctx, "grid_h", difficulty, odd_only=odd_only)
        width = _draw_dimension(ctx, "grid_w", difficulty, odd_only=odd_only)
        # Two residues in every four-pair episode force a visible multi-color
        # branch.  Therefore every three-demo query rotation still contains a
        # counterexample to "transform only the first/last color" shortcuts.
        force_multicolor = (
            requested_n is None
            and requested_palette is None
            and sample_index % 4 in (1, 3)
        )
        n_low = max(requested_palette or 1, 2 if force_multicolor else 1)
        n_pixels = ctx.draw_int_diff("n_pixels", n_low, 8)
        palette_low = 2 if force_multicolor else 1
        palette_size = ctx.draw_int_diff(
            "palette_size", palette_low, min(6, n_pixels)
        )
    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))

    positions = _select_positions(ctx, height, width, n_pixels, profile)
    palette = _palette(palette_kind, palette_size, ctx.draw_rng("palette"))
    colors = [palette[index % palette_size] for index in range(n_pixels)]
    ctx.draw_rng("color_assignment").shuffle(colors)

    grid = full_grid(height, width, 0)
    for (row, col), color in zip(positions, colors, strict=True):
        grid[row][col] = color
    return grid
