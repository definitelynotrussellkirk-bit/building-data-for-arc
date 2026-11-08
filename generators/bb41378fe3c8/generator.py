"""Generator for ARC task bb41378fe3c8 (Down-Right Shadow).

Every colour-2 input cell keeps its value and casts one colour-5 shadow into
its down-right neighbour when that neighbour exists and is background 0.
Non-background destinations block the shadow; non-2 cells never cast one.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "bb41378fe3c8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d655d37ca499"

SUMMARY = (
    "On a colour-0 background, each colour-2 marker casts a one-cell colour-5 "
    "shadow diagonally down-right only when that destination is in bounds and "
    "still 0. The marker and every other input cell are preserved. The teaching "
    "schedule includes blocked destinations, inert non-2 decoys, and clipped "
    "boundary markers so canonical-fitting shortcut rules are falsified."
)

INVARIANTS = [
    "inputs are rectangular 6..11 by 6..11 ARC grids",
    "inputs contain exactly 3..7 pairwise separated colour-2 markers",
    "colour 5 is output-only",
    "at most one marker is clipped at the bottom or right boundary",
    "at most one in-bounds marker has a nonzero blocking destination",
    "there are 0..3 inert non-2 decoys whose own down-right cell is 0",
    "at least one marker has an in-bounds background destination",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_MARKER_PROFILES = ("plain", "blocked", "boundary", "mixed")
_DECOY_COLORS = (1, 3, 4, 6, 7, 8, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-step semantic schedule",
        "valid": "6..11",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-step semantic schedule",
        "valid": "6..11",
    },
    "n_markers": {
        "type": "int",
        "default": "eight-step semantic schedule",
        "valid": "3..7",
    },
    "marker_profile": {
        "type": "str",
        "default": "eight-step semantic schedule",
        "valid": _MARKER_PROFILES,
    },
    "n_decoys": {
        "type": "int",
        "default": "eight-step semantic schedule",
        "valid": "0..3",
    },
}

# Every four consecutive pairs contain two odd-indexed rich examples. Removing
# any one pair as the query therefore leaves a demonstration with BOTH shortcut
# refutations (a blocked colour-2 destination and an inert non-2 decoy).
# Even-indexed anchors use canonical dimensions and palette size two, giving
# exact canonical-profile support in every difficulty band.
_SCHEDULE = (
    {
        "name": "canonical_6_plain",
        "grid_h": 6,
        "grid_w": 6,
        "n_markers": 3,
        "marker_profile": "plain",
        "n_decoys": 0,
    },
    {
        "name": "blocked_decoy_small",
        "grid_h": 7,
        "grid_w": 8,
        "n_markers": 4,
        "marker_profile": "blocked",
        "n_decoys": 1,
    },
    {
        "name": "canonical_7_boundary",
        "grid_h": 7,
        "grid_w": 7,
        "n_markers": 4,
        "marker_profile": "boundary",
        "n_decoys": 0,
    },
    {
        "name": "mixed_decoys_medium",
        "grid_h": 8,
        "grid_w": 7,
        "n_markers": 5,
        "marker_profile": "mixed",
        "n_decoys": 2,
    },
    {
        "name": "canonical_8_plain",
        "grid_h": 8,
        "grid_w": 8,
        "n_markers": 5,
        "marker_profile": "plain",
        "n_decoys": 0,
    },
    {
        "name": "blocked_decoy_large",
        "grid_h": 10,
        "grid_w": 9,
        "n_markers": 6,
        "marker_profile": "blocked",
        "n_decoys": 1,
    },
    {
        "name": "canonical_6_dense_boundary",
        "grid_h": 6,
        "grid_w": 6,
        "n_markers": 7,
        "marker_profile": "boundary",
        "n_decoys": 0,
    },
    {
        "name": "mixed_decoys_maximal",
        "grid_h": 11,
        "grid_w": 11,
        "n_markers": 7,
        "marker_profile": "mixed",
        "n_decoys": 3,
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _SCHEDULE)


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the deterministic semantic curriculum slot for this pair."""
    del seed
    _validate_difficulty(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_profile(sample_index: int) -> dict[str, Any]:
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    integer_ranges = {
        "grid_h": (6, 11),
        "grid_w": (6, 11),
        "n_markers": (3, 7),
        "n_decoys": (0, 3),
    }
    for name, (low, high) in integer_ranges.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"override {name} must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"override {name} must be in {low}..{high}")

    if "marker_profile" in overrides and overrides["marker_profile"] is not None:
        value = overrides["marker_profile"]
        if not isinstance(value, str) or value not in _MARKER_PROFILES:
            raise ValueError(
                f"override marker_profile must be one of {_MARKER_PROFILES}"
            )


def _draw_scheduled_int(
    ctx, overrides: dict[str, Any], label: str, default: int, low: int, high: int
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, low, high)
    return ctx.draw_choice(label, (default,))


def _draw_scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: tuple[str, ...],
) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 11:
        errors.append(f"height must be in 6..11, found {height}")
    if not 6 <= width <= 11:
        errors.append(f"width must be in 6..11, found {width}")

    present = {value for row in grid for value in row}
    if 0 not in present:
        errors.append("background colour 0 must be present")
    if 5 in present:
        errors.append("colour 5 is output-only and must not occur in an input")

    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if not 3 <= len(markers) <= 7:
        errors.append(f"expected 3..7 colour-2 markers, found {len(markers)}")

    for left_index, (row, col) in enumerate(markers):
        for other_row, other_col in markers[left_index + 1 :]:
            if abs(row - other_row) <= 1 and abs(col - other_col) <= 1:
                errors.append(
                    "colour-2 markers must have Chebyshev separation at least 2"
                )
                break
        if errors and errors[-1].startswith("colour-2 markers must"):
            break

    boundary_markers = [
        (row, col)
        for row, col in markers
        if row == height - 1 or col == width - 1
    ]
    if len(boundary_markers) > 1:
        errors.append(
            f"expected at most one clipped boundary marker, found {len(boundary_markers)}"
        )

    blocked_markers = [
        (row, col)
        for row, col in markers
        if row + 1 < height
        and col + 1 < width
        and grid[row + 1][col + 1] != 0
    ]
    if len(blocked_markers) > 1:
        errors.append(
            f"expected at most one blocked marker, found {len(blocked_markers)}"
        )
    for row, col in blocked_markers:
        if grid[row + 1][col + 1] == 2:
            errors.append("a marker may not be blocked by another colour-2 marker")

    blocked_targets = {(row + 1, col + 1) for row, col in blocked_markers}
    free_decoys = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 2) and (row, col) not in blocked_targets
    ]
    if not 0 <= len(free_decoys) <= 3:
        errors.append(f"expected 0..3 inert non-2 decoys, found {len(free_decoys)}")
    for row, col in free_decoys:
        if row + 1 >= height or col + 1 >= width:
            errors.append("every inert non-2 decoy must have an in-bounds down-right cell")
            continue
        if grid[row + 1][col + 1] != 0:
            errors.append("every inert non-2 decoy must have a background down-right cell")

    unblocked_interior = [
        (row, col)
        for row, col in markers
        if row + 1 < height
        and col + 1 < width
        and grid[row + 1][col + 1] == 0
    ]
    if not unblocked_interior:
        errors.append("at least one marker must cast a visible in-bounds shadow")

    if boundary_markers and blocked_markers:
        marker_profile = "mixed"
    elif boundary_markers:
        marker_profile = "boundary"
    elif blocked_markers:
        marker_profile = "blocked"
    else:
        marker_profile = "plain"

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "markers": markers,
        "boundary_markers": boundary_markers,
        "blocked_markers": blocked_markers,
        "blocked_targets": blocked_targets,
        "free_decoys": free_decoys,
        "marker_profile": marker_profile,
        "unblocked_interior": unblocked_interior,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every advertised exact axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_markers": len(analysis["markers"]),
        "marker_profile": analysis["marker_profile"],
        "n_decoys": len(analysis["free_decoys"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or off-contract generated inputs."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The canonical examples and generated scenes share this exact grammar."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror; the selected canonical Racket is authority."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            target_row, target_col = row + 1, col + 1
            if (
                target_row < height
                and target_col < width
                and grid[target_row][target_col] == 0
            ):
                output[target_row][target_col] = 5
    return output


def _overwrite_blockers(grid):
    """Wrong rule: every in-bounds colour-2 target is overwritten with 5."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2 and row + 1 < height and col + 1 < width:
                output[row + 1][col + 1] = 5
    return output


def _all_nonzero_casts(grid):
    """Wrong rule: every nonzero cell casts into a background target."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if (
                grid[row][col] != 0
                and row + 1 < height
                and col + 1 < width
                and grid[row + 1][col + 1] == 0
            ):
                output[row + 1][col + 1] = 5
    return output


SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "overwrite_blockers": _overwrite_blockers,
    "all_nonzero_casts": _all_nonzero_casts,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _lawful_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _has_blocked_destination(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["blocked_markers"])


def _has_non2_decoy_with_empty_shadow(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["free_decoys"])


def _has_boundary_marker(grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["boundary_markers"])


SEMANTIC_WITNESSES = {
    "blocked_destination": _has_blocked_destination,
    "non2_decoy_with_empty_shadow": _has_non2_decoy_with_empty_shadow,
    "boundary_marker": _has_boundary_marker,
}
WITNESS_RIVALS = {
    "blocked_destination": ["overwrite_blockers"],
    "non2_decoy_with_empty_shadow": ["all_nonzero_casts"],
}
BRANCH_WITNESSES = ("boundary_marker",)


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the teaching grammar: {errors[0]}"]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output does not follow the down-right shadow rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require three demonstrations to falsify every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"surviving lesson shortcut: {name}")
    return reasons


def _construct_grid(
    height: int,
    width: int,
    n_markers: int,
    marker_profile: str,
    n_decoys: int,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    wants_boundary = marker_profile in ("boundary", "mixed")
    wants_blocker = marker_profile in ("blocked", "mixed")

    boundary_marker = (height - 1, width - 1)
    interior_candidates = [
        (row, col)
        for row in range(0, height - 1, 2)
        for col in range(0, width - 1, 2)
        if not wants_boundary
        or (
            abs(row - boundary_marker[0]) > 1
            or abs(col - boundary_marker[1]) > 1
        )
    ]
    rng.shuffle(interior_candidates)
    interior_needed = n_markers - int(wants_boundary)
    if len(interior_candidates) < interior_needed:
        raise ValueError(
            f"need {interior_needed} interior markers but only "
            f"{len(interior_candidates)} fit"
        )
    markers = interior_candidates[:interior_needed]
    if wants_boundary:
        markers.append(boundary_marker)
    for row, col in markers:
        grid[row][col] = 2

    interior_markers = [
        (row, col)
        for row, col in markers
        if row + 1 < height and col + 1 < width
    ]
    if wants_blocker:
        blocked_row, blocked_col = rng.choice(interior_markers)
        grid[blocked_row + 1][blocked_col + 1] = 4

    # (even, odd) decoys target (odd, even) cells. Marker cells are (even,
    # even), marker destinations are (odd, odd), and the optional boundary
    # marker is bottom-right, so this parity class guarantees up to six free
    # decoys even in the hardest 6x6 / seven-marker override.
    decoy_candidates = [
        (row, col)
        for row in range(0, height - 1, 2)
        for col in range(1, width - 1, 2)
        if grid[row][col] == 0 and grid[row + 1][col + 1] == 0
    ]
    rng.shuffle(decoy_candidates)
    if len(decoy_candidates) < n_decoys:
        raise ValueError(
            f"need {n_decoys} inert decoys but only {len(decoy_candidates)} fit"
        )
    colors = list(_DECOY_COLORS)
    rng.shuffle(colors)
    for index, (row, col) in enumerate(decoy_candidates[:n_decoys]):
        grid[row][col] = colors[index % len(colors)]

    return [list(row) for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; canonical Racket owns the output."""
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    profile = _scheduled_profile(int(sample_index))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_scheduled_int(
        ctx, overrides, "grid_h", int(profile["grid_h"]), 6, 11
    )
    width = _draw_scheduled_int(
        ctx, overrides, "grid_w", int(profile["grid_w"]), 6, 11
    )
    n_markers = _draw_scheduled_int(
        ctx, overrides, "n_markers", int(profile["n_markers"]), 3, 7
    )
    marker_profile = _draw_scheduled_choice(
        ctx,
        overrides,
        "marker_profile",
        str(profile["marker_profile"]),
        _MARKER_PROFILES,
    )
    n_decoys = _draw_scheduled_int(
        ctx, overrides, "n_decoys", int(profile["n_decoys"]), 0, 3
    )

    grid = _construct_grid(
        height,
        width,
        n_markers,
        marker_profile,
        n_decoys,
        ctx.draw_rng(f"layout:{difficulty or 'medium'}"),
    )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Deterministic task-local near misses that self_check must reject."""
    base = generate(991, 3, marker_profile="mixed", n_decoys=2)

    output_colour = deepcopy(base)
    for row in range(len(output_colour)):
        for col in range(len(output_colour[0])):
            if output_colour[row][col] == 0:
                output_colour[row][col] = 5
                break
        else:
            continue
        break

    adjacent_marker = deepcopy(base)
    marker_row, marker_col = _analysis(adjacent_marker)["markers"][0]
    for row_delta, col_delta in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        row, col = marker_row + row_delta, marker_col + col_delta
        if (
            0 <= row < len(adjacent_marker)
            and 0 <= col < len(adjacent_marker[0])
            and adjacent_marker[row][col] == 0
        ):
            adjacent_marker[row][col] = 2
            break

    no_background = [[2 for _ in row] for row in base]
    return [
        ("output_colour_in_input", output_colour),
        ("adjacent_markers", adjacent_marker),
        ("no_background", no_background),
    ]
