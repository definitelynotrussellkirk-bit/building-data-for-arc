"""Generator for ``8cfb4420a8f1``.

A single nonzero cell in the top row is a colour selector.  The selected
colour is erased everywhere below the top row; the marker itself and every
other colour remain unchanged.

Every ordinary generated scene contains three deliberate controls that the
canonical examples only imply indirectly:

* the most frequent body colour is a non-marker distractor, so "erase the
  modal colour" is wrong; and
* that distractor occupies the marker's column while all true targets avoid
  it, so "erase the colour below the marker" is also wrong; and
* the first nonzero body cell is a distractor, refuting the canonical-fitting
  shortcut "erase the first body colour".

Distractor colours form connected objects, matching the canonical texture
instead of creating a field of isolated singleton pixels.  The four-phase
schedule inserts an exact canonical-profile anchor in every band and varies
marker position, marker colour, target count, and palette size.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8cfb4420a8f1"
TASK_ID = "8cfb4420a8f1"
VERSION = "3.1.0"  # strict scalars, connected objects, valid canonical shortcut
RULE_HASH = "506219441313"

SUMMARY = (
    "Read the unique nonzero marker in row 0. Preserve that marker, erase every "
    "cell of the same colour below row 0, and leave every other cell unchanged."
)

INVARIANTS = [
    "background is 0",
    "row 0 contains exactly one nonzero marker",
    "the marker colour occurs at least once below row 0",
    "at least one non-marker colour occurs below row 0",
    "only below-row cells matching the marker colour are erased",
]

_H_LO, _H_HI = 5, 8
_W_LO, _W_HI = 8, 12
_MARKED_LO, _MARKED_HI = 1, 4
_PRIMARY_LO, _PRIMARY_HI = 2, 6
_COLOR_LO, _COLOR_HI = 3, 4
_MARKER_POSITIONS = ("left", "center", "right")
_BANDS = ("easy", "medium", "hard")
_BAND_OFFSETS = {"easy": 0, "medium": 3, "hard": 6}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-phase band schedule with canonical anchors",
        "valid": "5..8",
    },
    "grid_w": {
        "type": "int",
        "default": "four-phase band schedule with canonical anchors",
        "valid": "8..12",
    },
    "marker_position": {
        "type": "enum",
        "default": "sample-index cycle",
        "valid": "left|center|right",
    },
    "marker_color": {
        "type": "int",
        "default": "sample-index colour cycle",
        "valid": "1..9",
    },
    "marked_cells": {
        "type": "int",
        "default": "phase schedule 1,2,3,4",
        "valid": "1..4",
    },
    "primary_distractor_count": {
        "type": "int",
        "default": "phase schedule 4,4,5,6",
        "valid": "2..6",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "3 or 4 nonzero colours, including the marker",
        "valid": "3..4",
    },
}

# Every cross-product of the declared axis domains fits in the minimum grid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "left_shortcut_guard",
    "center_shortcut_guard",
    "right_shortcut_guard",
)


def _validate_request_scalars(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BANDS:
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the exact four-phase curriculum schedule to the semantic gate."""
    _validate_request_scalars(seed, sample_index)
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(sample_index: int, band: str) -> dict[str, Any]:
    phase = sample_index % len(SCHEDULE_PROFILES)
    if phase == 0:
        # Exact canonical profiles are (5,9,5 colours including zero) and
        # (6,9,4 colours including zero).  Anchor every band explicitly.
        h, w, n_colors = (5, 9, 4) if band == "easy" else (6, 9, 3)
        marked, primary, marker_position = 1, 4, "center"
    elif phase == 1:
        h, w = {"easy": (5, 8), "medium": (6, 10), "hard": (7, 11)}[band]
        n_colors, marked, primary, marker_position = 3, 2, 4, "left"
    elif phase == 2:
        h, w = {"easy": (6, 9), "medium": (7, 11), "hard": (8, 12)}[band]
        n_colors, marked, primary, marker_position = 4, 3, 5, "center"
    else:
        h, w = {"easy": (6, 10), "medium": (8, 12), "hard": (7, 12)}[band]
        n_colors, marked, primary, marker_position = 3, 4, 6, "right"

    marker_color = ((sample_index + _BAND_OFFSETS[band]) % 9) + 1
    return {
        "grid_h": h,
        "grid_w": w,
        "marker_position": marker_position,
        "marker_color": marker_color,
        "marked_cells": marked,
        "primary_distractor_count": primary,
        "n_distinct_colors": n_colors,
    }


def _draw_scheduled_int(ctx: Any, label: str, scheduled: int, lo: int, hi: int) -> int:
    bounds = (lo, hi) if ctx.overrides.get(label) is not None else (scheduled, scheduled)
    return ctx.draw_int_strict(label, *bounds)


def _draw_scheduled_choice(
    ctx: Any, label: str, scheduled: str, options: tuple[str, ...]
) -> str:
    choices = options if ctx.overrides.get(label) is not None else (scheduled,)
    return str(ctx.draw_choice(label, choices))


def _marker_column(width: int, position: str) -> int:
    return {"left": 0, "center": width // 2, "right": width - 1}[position]


def _orthogonal_neighbours(
    position: tuple[int, int], height: int, width: int
) -> tuple[tuple[int, int], ...]:
    r, c = position
    return tuple(
        (nr, nc)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 1 <= nr < height and 0 <= nc < width
    )


def _draw_connected_region(
    available: set[tuple[int, int]],
    size: int,
    rng: Any,
    *,
    starts: list[tuple[int, int]] | None = None,
    height: int,
    width: int,
) -> set[tuple[int, int]]:
    """Draw an exact-size 4-connected region from ``available``.

    Trying candidate starts rather than rerolling the whole scene keeps exact
    overrides deterministic and makes capacity failures explicit.
    """
    if type(size) is not int or size < 1:
        raise ValueError("connected region size must be a positive integer")
    candidates = list(starts if starts is not None else sorted(available))
    rng.shuffle(candidates)
    for start in candidates:
        if start not in available:
            continue
        chosen = {start}
        while len(chosen) < size:
            frontier = sorted(
                {
                    neighbour
                    for cell in chosen
                    for neighbour in _orthogonal_neighbours(cell, height, width)
                    if neighbour in available and neighbour not in chosen
                }
            )
            if not frontier:
                break
            rng.shuffle(frontier)
            chosen.add(frontier[0])
        if len(chosen) == size:
            return chosen
    raise AssertionError(
        f"cannot draw connected region of size {size} from {len(available)} cells"
    )


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts.update({"grid_h": h, "grid_w": w})
    top = [(c, grid[0][c]) for c in range(w) if grid[0][c] != 0]
    if len(top) != 1:
        errors.append(f"row 0 must contain exactly one nonzero marker; found {len(top)}")
        return facts

    marker_col, marker_color = top[0]
    body_counts = Counter(
        grid[r][c] for r in range(1, h) for c in range(w) if grid[r][c] != 0
    )
    marked_cells = body_counts.get(marker_color, 0)
    distractor_counts = Counter(body_counts)
    distractor_counts.pop(marker_color, None)

    if marked_cells < 1:
        errors.append("the marker colour must occur at least once below row 0")
    if not distractor_counts:
        errors.append("the body must contain at least one non-marker distractor colour")

    position_by_col = {0: "left", w // 2: "center", w - 1: "right"}
    marker_position = position_by_col.get(marker_col, "other")
    primary_count = max(distractor_counts.values(), default=0)
    primary_colors = [
        color for color, count in distractor_counts.items() if count == primary_count
    ]

    output = deepcopy(grid)
    for r in range(1, h):
        for c in range(w):
            if output[r][c] == marker_color:
                output[r][c] = 0

    facts.update(
        {
            "marker_col": marker_col,
            "marker_position": marker_position,
            "marker_color": marker_color,
            "marked_cells": marked_cells,
            "distractor_counts": distractor_counts,
            "primary_distractor_count": primary_count,
            "primary_distractor_colors": primary_colors,
            "n_distinct_colors": len(body_counts),
            "output": output,
        }
    )
    return facts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the authority-wide input grammar, including all canonical rows."""
    del difficulty, meta
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    h, w = info["grid_h"], info["grid_w"]
    if not (3 <= h <= 12 and 5 <= w <= 18):
        errors.append(f"dimensions {h}x{w} outside the task grammar")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Empirical canonical profile, quotienting colour and position renaming."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    info = _analyze(grid)
    profile = (
        info["grid_h"],
        info["grid_w"],
        info["n_distinct_colors"] + 1,  # include background zero
    )
    if profile not in {(5, 9, 5), (6, 9, 4)}:
        reasons.append(f"profile {profile} is outside the canonical exact profiles")
    if info["marked_cells"] != 1:
        reasons.append("canonical inputs contain exactly one body target")
    return reasons


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared axis exactly from a generated grid."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if info["marker_position"] == "other":
        raise ValueError("marker is not at a declared position")
    if len(info["primary_distractor_colors"]) != 1:
        raise ValueError("primary distractor count is not uniquely observable")
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "marker_position": info["marker_position"],
        "marker_color": info["marker_color"],
        "marked_cells": info["marked_cells"],
        "primary_distractor_count": info["primary_distractor_count"],
        "n_distinct_colors": info["n_distinct_colors"],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authoritative."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return deepcopy(info["output"])


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_request_scalars(seed, sample_index)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    band = _band(difficulty)
    scheduled = _scheduled_defaults(sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, "grid_h", scheduled["grid_h"], _H_LO, _H_HI)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled["grid_w"], _W_LO, _W_HI)
    marker_position = _draw_scheduled_choice(
        ctx,
        "marker_position",
        scheduled["marker_position"],
        _MARKER_POSITIONS,
    )
    marker_color = _draw_scheduled_int(
        ctx, "marker_color", scheduled["marker_color"], 1, 9
    )
    marked_cells = _draw_scheduled_int(
        ctx, "marked_cells", scheduled["marked_cells"], _MARKED_LO, _MARKED_HI
    )
    primary_count = _draw_scheduled_int(
        ctx,
        "primary_distractor_count",
        scheduled["primary_distractor_count"],
        _PRIMARY_LO,
        _PRIMARY_HI,
    )
    n_colors = _draw_scheduled_int(
        ctx,
        "n_distinct_colors",
        scheduled["n_distinct_colors"],
        _COLOR_LO,
        _COLOR_HI,
    )

    marker_col = _marker_column(w, marker_position)
    palette_rng = ctx.draw_rng("palette")
    available_colors = [color for color in range(1, 10) if color != marker_color]
    palette_rng.shuffle(available_colors)
    distractor_colors = available_colors[: n_colors - 1]
    primary_color = distractor_colors[0]

    grid = full_grid(h, w, 0)
    grid[0][marker_col] = marker_color
    layout_rng = ctx.draw_rng("layout")
    used: set[tuple[int, int]] = set()
    # Reserve a top-left body domino.  It becomes the first extra distractor
    # when the marker is elsewhere, or remains available to the primary object
    # when the marker itself is in the left column.
    first_body_guard = {(1, 0), (2, 0)}

    # True targets are spread over distinct rows and never occupy the marker
    # column or first-body guard.  This makes both shortcut controls decisive.
    marker_rows = list(range(1, h))
    layout_rng.shuffle(marker_rows)
    marker_candidates = [
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if c != marker_col and (r, c) not in first_body_guard
    ]
    layout_rng.shuffle(marker_candidates)
    for index in range(marked_cells):
        row = marker_rows[index % len(marker_rows)]
        candidates = [p for p in marker_candidates if p[0] == row and p not in used]
        if not candidates:
            candidates = [p for p in marker_candidates if p not in used]
        position = candidates[0]
        used.add(position)
        grid[position[0]][position[1]] = marker_color

    # The primary distractor is one connected object, always intersects the
    # marker column, and remains the unique modal distractor.
    primary_available = {
        (r, c) for r in range(1, h) for c in range(w) if (r, c) not in used
    }
    if marker_col != 0:
        primary_available -= first_body_guard
    primary_starts = (
        [(1, 0)]
        if marker_col == 0
        else [
            (r, marker_col)
            for r in range(1, h)
            if (r, marker_col) in primary_available
        ]
    )
    primary_positions = _draw_connected_region(
        primary_available,
        primary_count,
        layout_rng,
        starts=primary_starts,
        height=h,
        width=w,
    )
    for position in primary_positions:
        used.add(position)
        grid[position[0]][position[1]] = primary_color

    # Extra colours are small connected objects, never in the marker column.
    # With a minimum primary override of two they remain singletons so the
    # primary count stays uniquely observable; otherwise they are dominoes,
    # matching the connected-object texture of the canonical examples.
    extra_size = 1 if primary_count == _PRIMARY_LO else 2
    for extra_index, color in enumerate(distractor_colors[1:]):
        extra_available = {
            (r, c)
            for r in range(1, h)
            for c in range(w)
            if (r, c) not in used and c != marker_col
        }
        if extra_index == 0 and marker_col != 0:
            required = {(1, 0)} if extra_size == 1 else first_body_guard
            if not required <= extra_available:
                raise AssertionError("reserved first-body shortcut guard unavailable")
            positions = required
        else:
            positions = _draw_connected_region(
                extra_available,
                extra_size,
                layout_rng,
                height=h,
                width=w,
            )
        for position in positions:
            used.add(position)
            grid[position[0]][position[1]] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generator emitted invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "marker_position": marker_position,
        "marker_color": marker_color,
        "marked_cells": marked_cells,
        "primary_distractor_count": primary_count,
        "n_distinct_colors": n_colors,
    }
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected {expected}, got {observed}")
    return grid


# ---------------------------------------------------------------------------
# Task-linked semantic witnesses and plausible wrong-rule rivals.
# ---------------------------------------------------------------------------


def _facts_or_none(grid: Any) -> dict[str, Any] | None:
    info = _analyze(grid)
    return None if info["errors"] else info


def _marker_has_body_targets(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return info is not None and info["marked_cells"] >= 1


def _modal_colour_is_a_distractor(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return (
        info is not None
        and info["primary_distractor_count"] > info["marked_cells"]
        and len(info["primary_distractor_colors"]) == 1
    )


def _marker_column_contains_decoy(grid: Any) -> bool:
    info = _facts_or_none(grid)
    if info is None:
        return False
    return any(
        grid[r][info["marker_col"]] not in (0, info["marker_color"])
        for r in range(1, info["grid_h"])
    )


def _targets_avoid_marker_column(grid: Any) -> bool:
    info = _facts_or_none(grid)
    if info is None:
        return False
    return all(
        grid[r][info["marker_col"]] != info["marker_color"]
        for r in range(1, info["grid_h"])
    )


def _multiple_distractor_colours(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return info is not None and len(info["distractor_counts"]) >= 2


def _first_body_colour_is_a_distractor(grid: Any) -> bool:
    info = _facts_or_none(grid)
    if info is None:
        return False
    for row in grid[1:]:
        for value in row:
            if value != 0:
                return value != info["marker_color"]
    return False


SEMANTIC_WITNESSES = {
    "marker_colour_has_body_targets": _marker_has_body_targets,
    "modal_body_colour_is_a_distractor": _modal_colour_is_a_distractor,
    "marker_column_contains_nonmarker_decoy": _marker_column_contains_decoy,
    "true_targets_avoid_marker_column": _targets_avoid_marker_column,
    "at_least_two_distractor_colours": _multiple_distractor_colours,
    "first_nonzero_body_colour_is_a_distractor": _first_body_colour_is_a_distractor,
}


def _identity_rule(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def _erase_marker_everywhere(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    out = deepcopy(grid)
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == info["marker_color"]:
                out[r][c] = 0
    return out


def _erase_modal_body_colour(grid: list[list[int]]) -> list[list[int]]:
    body = Counter(value for row in grid[1:] for value in row if value != 0)
    color = max(sorted(body), key=lambda value: body[value])
    out = deepcopy(grid)
    for r in range(1, len(out)):
        for c in range(len(out[0])):
            if out[r][c] == color:
                out[r][c] = 0
    return out


def _erase_colour_below_marker_column(grid: list[list[int]]) -> list[list[int]]:
    info = _analyze(grid)
    column_values = [
        grid[r][info["marker_col"]]
        for r in range(1, info["grid_h"])
        if grid[r][info["marker_col"]] != 0
    ]
    color = column_values[0] if column_values else info["marker_color"]
    out = deepcopy(grid)
    for r in range(1, len(out)):
        for c in range(len(out[0])):
            if out[r][c] == color:
                out[r][c] = 0
    return out


def _erase_repeated_body_colours(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid[1:] for value in row if value != 0)
    repeated = {color for color, count in counts.items() if count > 1}
    out = deepcopy(grid)
    for r in range(1, len(out)):
        for c in range(len(out[0])):
            if out[r][c] in repeated:
                out[r][c] = 0
    return out


def _erase_all_body_objects(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r in range(1, len(out)):
        for c in range(len(out[0])):
            if out[r][c] != 0:
                out[r][c] = 0
    return out


def _erase_first_nonzero_body_colour(grid: list[list[int]]) -> list[list[int]]:
    color = next(value for row in grid[1:] for value in row if value != 0)
    out = deepcopy(grid)
    for r in range(1, len(out)):
        for c in range(len(out[0])):
            if out[r][c] == color:
                out[r][c] = 0
    return out


def _erase_fixed_colour(grid: list[list[int]], color: int) -> list[list[int]]:
    out = deepcopy(grid)
    for r in range(1, len(out)):
        for c in range(len(out[0])):
            if out[r][c] == color:
                out[r][c] = 0
    return out


_RIVAL_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity_rule,
    "erase_marker_including_top_marker": _erase_marker_everywhere,
    "erase_modal_body_colour": _erase_modal_body_colour,
    "erase_colour_found_below_marker_column": _erase_colour_below_marker_column,
    "erase_every_repeated_body_colour": _erase_repeated_body_colours,
    "erase_all_nonzero_body_cells": _erase_all_body_objects,
    "erase_first_nonzero_body_colour": _erase_first_nonzero_body_colour,
}

SEMANTIC_RIVALS = _RIVAL_RULES
LESSON_COMPETITORS = _RIVAL_RULES
CANONICAL_SHORTCUTS = {
    "erase_first_nonzero_body_colour": _erase_first_nonzero_body_colour,
}
WITNESS_RIVALS = {
    "marker_colour_has_body_targets": ["identity"],
    "modal_body_colour_is_a_distractor": ["erase_modal_body_colour"],
    "marker_column_contains_nonmarker_decoy": [
        "erase_colour_found_below_marker_column"
    ],
    "true_targets_avoid_marker_column": [
        "erase_colour_found_below_marker_column"
    ],
    "at_least_two_distractor_colours": [
        "erase_every_repeated_body_colour",
        "erase_all_nonzero_body_cells",
    ],
    "first_nonzero_body_colour_is_a_distractor": [
        "erase_first_nonzero_body_colour"
    ],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject a lesson when a named plausible rival survives its demos."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is outside the task grammar: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output does not match the canonical rule")
    if reasons:
        return reasons

    for name, rival in _RIVAL_RULES.items():
        rival_fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if rival_fits_demos and rival(query["input"]) != query["output"]:
            reasons.append(f"demos do not refute rival rule: {name}")

    if demos:
        first_marker = _analyze(demos[0]["input"])["marker_color"]
        fixed_fits = all(
            _erase_fixed_colour(pair["input"], first_marker) == pair["output"]
            for pair in demos
        )
        if fixed_fits and _erase_fixed_colour(query["input"], first_marker) != query["output"]:
            reasons.append("demos do not refute rival rule: erase one fixed colour")
    return reasons
