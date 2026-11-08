"""Generator for 19ba16363b7f — a corner legend selects seeds to grow.

The nonzero color at ``(0, 0)`` is a legend swatch.  Every other cell of that
color is a selected seed.  The output discards the legend and all distractors,
then paints the in-bounds union of a full 3x3 cyan stencil around every
selected seed.

Ordinary draws use a four-position schedule.  Every consecutive four examples
contain: a canonical-scale anchor, a case where a distractor color is more
frequent than the selected color, a clipped border stamp, and overlapping
selected stamps.  This makes the legend, stencil, clipping, and union semantics
observable at lesson level rather than merely producing varied-looking grids.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "19ba16363b7f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "02a300f6b627"

SUMMARY = (
    "Cell (0,0) is a nonzero legend color. Select every other cell with that "
    "color, grow each selected seed by the full 3x3 Chebyshev-radius-one "
    "stencil, clip the stencil at grid edges, take the union, recolor it cyan "
    "(8), and discard the legend plus all non-selected colors."
)

INVARIANTS = [
    "background is 0 and the isolated top-left legend color is neither 0 nor 8",
    "2-6 non-legend cells match the legend and therefore become stamp centers",
    "2-8 distractor cells use at least two colors distinct from the legend and 8",
    "ordinary four-example lessons cover canonical scale, modal-color rebuttal, clipping, and overlap",
    "the Racket rule is the sole output authority; Python mirrors below are validation rivals only",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled/difficulty-aware draw within 7..15",
        "valid": "7..15",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled/difficulty-aware draw within 7..15",
        "valid": "7..15",
        "doc": "Returned grid width.",
    },
    "n_keys": {
        "type": "int",
        "default": "scheduled/difficulty-aware draw within 2..6",
        "valid": "2..6",
        "doc": "Selected legend-color seed count, excluding the legend cell.",
    },
    "n_distract": {
        "type": "int",
        "default": "scheduled/difficulty-aware draw within 2..8",
        "valid": "2..8",
        "doc": "Total non-selected nonzero distractor-cell count.",
    },
}

_PROFILE_CANONICAL = "canonical_anchor"
_PROFILE_MODAL = "modal_rebuttal"
_PROFILE_CLIPPED = "clipped_border"
_PROFILE_OVERLAP = "overlapping_union"
SCHEDULE_PROFILES = (
    _PROFILE_CANONICAL,
    _PROFILE_MODAL,
    _PROFILE_CLIPPED,
    _PROFILE_OVERLAP,
)

_RESERVED = {(0, 0), (0, 1), (1, 0), (1, 1)}
_SQUARE_OFFSETS = tuple(
    (dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
)
_PLUS_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic four-example semantic schedule slot."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default_lo: int,
    default_hi: int,
    valid_lo: int,
    valid_hi: int,
) -> int:
    """Honor exact overrides across the full declared domain."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _stamp(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
    centers: list[tuple[int, int]],
    offsets: tuple[tuple[int, int], ...] = _SQUARE_OFFSETS,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for row, col in centers:
        for drow, dcol in offsets:
            rr, cc = row + drow, col + dcol
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = 8
    return out


def _scene_cells(grid: Any) -> list[tuple[int, int, int]]:
    return [
        (row, col, int(value))
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if (row, col) != (0, 0) and value not in (0, 8)
    ]


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    key = int(grid[0][0])
    selected = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == key and (row, col) != (0, 0)
    ]
    distractors = [
        (row, col, int(value))
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 8, key)
    ]
    distractor_colors = sorted({value for _, _, value in distractors})
    clipped = any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in selected
    )
    overlap = any(
        max(abs(row - other_row), abs(col - other_col)) < 3
        for index, (row, col) in enumerate(selected)
        for other_row, other_col in selected[index + 1 :]
    )
    output = _stamp(grid, selected)

    if not 7 <= height <= 15 or not 7 <= width <= 15:
        errors.append(f"dimensions {height}x{width} outside declared 7..15 envelope")
    if key in (0, 8):
        errors.append(f"top-left legend color must be nonzero and not cyan; got {key}")
    if key not in (0, 8):
        for row, col in sorted(_RESERVED - {(0, 0)}):
            if row < height and col < width and grid[row][col] != 0:
                errors.append("top-left legend swatch must be isolated by a 2x2 zero corner")
                break
    if not 2 <= len(selected) <= 6:
        errors.append(f"need 2..6 selected legend-color seeds; found {len(selected)}")
    if not 2 <= len(distractors) <= 8:
        errors.append(f"need 2..8 distractor cells; found {len(distractors)}")
    if len(distractor_colors) < 2:
        errors.append("distractors must use at least two distinct non-selected colors")
    if any(value == 8 for row in grid for value in row):
        errors.append("cyan 8 is reserved for the output and may not appear in the input")
    if selected and not any(value == 8 for row in output for value in row):
        errors.append("selected seeds must produce a nonempty cyan output")

    scene_counts = Counter(value for _, _, value in _scene_cells(grid))
    modal_scene_color = None
    if scene_counts:
        best_count = max(scene_counts.values())
        modal_scene_color = next(
            value
            for _, _, value in _scene_cells(grid)
            if scene_counts[value] == best_count
        )

    result.update(
        {
            "grid_h": height,
            "grid_w": width,
            "key": key,
            "selected": selected,
            "n_keys": len(selected),
            "distractors": distractors,
            "n_distract": len(distractors),
            "distractor_colors": distractor_colors,
            "clipped": clipped,
            "overlap": overlap,
            "output": output,
            "scene_counts": dict(scene_counts),
            "modal_scene_color": modal_scene_color,
            "canonical_dims": (height, width) in {(9, 9), (9, 10)},
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding lesson inputs."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical-scale, full-separated-stamp manifold."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if not analysis["canonical_dims"]:
        reasons.append("dimensions are not canonical 9x9 or 9x10")
    if analysis["clipped"]:
        reasons.append("a selected seed clips at the border")
    if analysis["overlap"]:
        reasons.append("selected 3x3 stamps overlap")
    if len({0, analysis["key"], *analysis["distractor_colors"]}) != 4:
        reasons.append("palette is not canonical four-color support")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_keys": analysis["n_keys"],
        "n_distract": analysis["n_distract"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Validation mirror only; generated labels still come from Racket."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


def _candidate_cells(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in _RESERVED
    ]


def _spaced_selection(
    candidates: list[tuple[int, int]], count: int, rng, minimum_gap: int = 3
) -> list[tuple[int, int]]:
    """Backtracking selection with a Chebyshev separation floor."""
    options = list(candidates)
    rng.shuffle(options)

    def search(chosen: list[tuple[int, int]], start: int) -> list[tuple[int, int]] | None:
        if len(chosen) == count:
            return chosen
        if len(options) - start < count - len(chosen):
            return None
        for index in range(start, len(options)):
            row, col = options[index]
            if any(
                max(abs(row - prior_row), abs(col - prior_col)) < minimum_gap
                for prior_row, prior_col in chosen
            ):
                continue
            found = search(chosen + [(row, col)], index + 1)
            if found is not None:
                return found
        return None

    return search([], 0) or []


def _ordinary_ranges(band: str) -> tuple[tuple[int, int], ...]:
    if band == "easy":
        return (7, 9), (7, 9), (2, 3), (2, 4)
    if band == "hard":
        return (11, 15), (11, 15), (4, 6), (5, 8)
    return (8, 11), (8, 11), (2, 4), (3, 6)


def _pick_dimensions_and_counts(ctx, overrides, band: str, profile: str):
    if overrides:
        (h_lo, h_hi), (w_lo, w_hi), (k_lo, k_hi), (d_lo, d_hi) = _ordinary_ranges(band)
        height = _draw_axis(ctx, overrides, "grid_h", h_lo, h_hi, 7, 15)
        width = _draw_axis(ctx, overrides, "grid_w", w_lo, w_hi, 7, 15)
        n_keys = _draw_axis(ctx, overrides, "n_keys", k_lo, k_hi, 2, 6)
        n_distract = _draw_axis(ctx, overrides, "n_distract", d_lo, d_hi, 2, 8)
        return height, width, n_keys, n_distract

    if profile == _PROFILE_CANONICAL:
        height = ctx.draw_int("grid_h", 9, 9)
        width = ctx.draw_int("grid_w", 9, 10)
        n_keys = ctx.draw_int("n_keys", 2, 2)
        n_distract = ctx.draw_int("n_distract", 2, 2)
    elif profile == _PROFILE_MODAL:
        height = ctx.draw_int("grid_h", 9, 9)
        width = ctx.draw_int("grid_w", 9, 10)
        n_keys = ctx.draw_int("n_keys", 2, 4)
        n_distract = ctx.draw_int("n_distract", n_keys + 2, min(8, n_keys + 2))
    else:
        (h_lo, h_hi), (w_lo, w_hi), (k_lo, k_hi), (d_lo, d_hi) = _ordinary_ranges(band)
        height = ctx.draw_int("grid_h", h_lo, h_hi)
        width = ctx.draw_int("grid_w", w_lo, w_hi)
        n_keys = ctx.draw_int("n_keys", k_lo, k_hi)
        n_distract = ctx.draw_int("n_distract", d_lo, d_hi)
    return height, width, n_keys, n_distract


def _place_selected(
    height: int,
    width: int,
    count: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    candidates = _candidate_cells(height, width)
    interior = [
        (row, col)
        for row, col in candidates
        if 1 <= row < height - 1 and 1 <= col < width - 1
    ]

    if profile in (_PROFILE_CANONICAL, _PROFILE_MODAL):
        selected = _spaced_selection(interior, count, rng)
        if len(selected) != count:
            raise ValueError("could not place full separated selected stamps")
        return selected

    if profile == _PROFILE_CLIPPED:
        border = [
            cell
            for cell in candidates
            if cell[0] in (0, height - 1) or cell[1] in (0, width - 1)
        ]
        rng.shuffle(border)
        for first in border:
            remaining = [
                cell
                for cell in candidates
                if max(abs(cell[0] - first[0]), abs(cell[1] - first[1])) >= 3
            ]
            tail = _spaced_selection(remaining, count - 1, rng)
            if len(tail) == count - 1:
                return [first, *tail]
        raise ValueError("could not place an isolated clipped-border stamp")

    if profile == _PROFILE_OVERLAP:
        pairs = [
            ((row, col), (row, col + 1))
            for row in range(1, height - 1)
            for col in range(1, width - 2)
            if (row, col) not in _RESERVED and (row, col + 1) not in _RESERVED
        ]
        rng.shuffle(pairs)
        for first, second in pairs:
            remaining = [
                cell
                for cell in interior
                if min(
                    max(abs(cell[0] - first[0]), abs(cell[1] - first[1])),
                    max(abs(cell[0] - second[0]), abs(cell[1] - second[1])),
                ) >= 3
            ]
            tail = _spaced_selection(remaining, count - 2, rng)
            if len(tail) == count - 2:
                return [first, second, *tail]
        raise ValueError("could not place an isolated overlapping-stamp pair")

    rng.shuffle(candidates)
    return candidates[:count]


def _place_distractors(
    height: int,
    width: int,
    count: int,
    occupied: set[tuple[int, int]],
    rng,
) -> list[tuple[int, int]]:
    candidates = [cell for cell in _candidate_cells(height, width) if cell not in occupied]
    rng.shuffle(candidates)
    if len(candidates) < count:
        raise ValueError("not enough cells for requested distractors")
    return candidates[:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    band = _band(difficulty)
    profile = "general_override" if overrides else schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height, width, n_keys, n_distract = _pick_dimensions_and_counts(
        ctx, overrides, band, profile
    )
    colors = ctx.draw_distinct_colors("scene_colors", n=3, exclude={0, 8})
    key_color, distractor_a, distractor_b = colors
    layout_rng = ctx.draw_rng("layout")

    selected = _place_selected(height, width, n_keys, profile, layout_rng)
    distractors = _place_distractors(
        height, width, n_distract, set(selected), layout_rng
    )

    grid = full_grid(height, width, 0)
    grid[0][0] = key_color
    for row, col in selected:
        grid[row][col] = key_color

    if profile == _PROFILE_MODAL:
        assignments = [distractor_a] * (n_distract - 1) + [distractor_b]
        layout_rng.shuffle(assignments)
    else:
        assignments = [
            distractor_a if index % 2 == 0 else distractor_b
            for index in range(n_distract)
        ]
        layout_rng.shuffle(assignments)
    for (row, col), color in zip(distractors, assignments):
        grid[row][col] = color

    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError("generated invalid legend-stamp input: " + "; ".join(analysis["errors"]))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_keys": n_keys,
        "n_distract": n_distract,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"realized axis drift: expected {expected}, observed {observed}")
    if profile == _PROFILE_CLIPPED and not analysis["clipped"]:
        raise AssertionError("clipped-border schedule slot did not realize clipping")
    if profile == _PROFILE_OVERLAP and not analysis["overlap"]:
        raise AssertionError("overlap schedule slot did not realize overlapping stamps")
    if profile == _PROFILE_MODAL:
        counts = analysis["scene_counts"]
        if counts.get(analysis["modal_scene_color"], 0) <= counts.get(key_color, 0):
            raise AssertionError("modal-rebuttal slot did not make a distractor color more frequent")
    return grid


# ---------------------------------------------------------------------------
# Explicit wrong-rule competitors used by the semantic gate.
# ---------------------------------------------------------------------------

def _centers_for_color(grid, color: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color and (row, col) != (0, 0)
    ]


def rival_modal_scene_color(grid) -> list[list[int]]:
    cells = _scene_cells(grid)
    counts = Counter(value for _, _, value in cells)
    if not counts:
        return full_grid(len(grid), len(grid[0]), 0)
    best_count = max(counts.values())
    chosen = next(value for _, _, value in cells if counts[value] == best_count)
    return _stamp(grid, _centers_for_color(grid, chosen))


def rival_all_nonzero_stamps(grid) -> list[list[int]]:
    centers = [(row, col) for row, col, _ in _scene_cells(grid)]
    return _stamp(grid, centers)


def rival_plus_stencil(grid) -> list[list[int]]:
    return _stamp(grid, _centers_for_color(grid, grid[0][0]), _PLUS_OFFSETS)


def rival_centers_only(grid) -> list[list[int]]:
    return _stamp(grid, _centers_for_color(grid, grid[0][0]), ((0, 0),))


def rival_drop_border_selected(grid) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    centers = [
        (row, col)
        for row, col in _centers_for_color(grid, grid[0][0])
        if row not in (0, height - 1) and col not in (0, width - 1)
    ]
    return _stamp(grid, centers)


def rival_isolated_selected_only(grid) -> list[list[int]]:
    kept: list[tuple[int, int]] = []
    for row, col in _centers_for_color(grid, grid[0][0]):
        if all(max(abs(row - rr), abs(col - cc)) >= 3 for rr, cc in kept):
            kept.append((row, col))
    return _stamp(grid, kept)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "modal_scene_color": rival_modal_scene_color,
    "stamp_all_nonzero": rival_all_nonzero_stamps,
    "plus_stencil": rival_plus_stencil,
    "centers_only": rival_centers_only,
    "drop_border_selected": rival_drop_border_selected,
    "isolated_selected_only": rival_isolated_selected_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "modal_scene_color": rival_modal_scene_color,
    "drop_border_selected": rival_drop_border_selected,
    "isolated_selected_only": rival_isolated_selected_only,
}


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_modal_rebuttal(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    key_count = analysis["scene_counts"].get(analysis["key"], 0)
    modal_count = analysis["scene_counts"].get(analysis["modal_scene_color"], 0)
    return analysis["modal_scene_color"] != analysis["key"] and modal_count > key_count


def _witness_ignored_distractors(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["n_distract"] >= 2


def _witness_square_diagonals(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    height, width = analysis["grid_h"], analysis["grid_w"]
    return any(
        0 <= row + drow < height and 0 <= col + dcol < width
        for row, col in analysis["selected"]
        for drow, dcol in ((-1, -1), (-1, 1), (1, -1), (1, 1))
    )


def _witness_growth_beyond_centers(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and sum(value == 8 for row in analysis["output"] for value in row) > analysis["n_keys"]


def _witness_clipped(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and bool(analysis["clipped"])
        and rival_drop_border_selected(grid) != analysis["output"]
    )


def _witness_overlap(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and bool(analysis["overlap"])
        and rival_isolated_selected_only(grid) != analysis["output"]
    )


SEMANTIC_WITNESSES = {
    "modal_distractor_beats_selected": _witness_modal_rebuttal,
    "ignored_distractors": _witness_ignored_distractors,
    "full_square_diagonals": _witness_square_diagonals,
    "growth_beyond_centers": _witness_growth_beyond_centers,
    "clipped_border_stamp": _witness_clipped,
    "overlapping_stamp_union": _witness_overlap,
}
WITNESS_RIVALS = {
    "modal_distractor_beats_selected": ["modal_scene_color"],
    "ignored_distractors": ["stamp_all_nonzero"],
    "full_square_diagonals": ["plus_stencil"],
    "growth_beyond_centers": ["centers_only"],
    "clipped_border_stamp": ["drop_border_selected"],
    "overlapping_stamp_union": ["isolated_selected_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each four-demo lesson to eliminate every named shortcut."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        inp, out = pair.get("input"), pair.get("output")
        analysis = _analysis(inp)
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside teaching grammar")
            continue
        if out != analysis["output"]:
            reasons.append(f"demo {index} output does not match legend-selected 3x3 growth")

    for name, competitor in LESSON_COMPETITORS.items():
        if not any(competitor(pair["input"]) != pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} survives every demonstration")

    profiles = {
        _PROFILE_MODAL: any(_witness_modal_rebuttal(pair["input"]) for pair in demos),
        _PROFILE_CLIPPED: any(_witness_clipped(pair["input"]) for pair in demos),
        _PROFILE_OVERLAP: any(_witness_overlap(pair["input"]) for pair in demos),
    }
    if not profiles[_PROFILE_MODAL]:
        reasons.append("no demonstration makes a distractor color beat the selected color")
    if not profiles[_PROFILE_CLIPPED]:
        reasons.append("no demonstration exercises clipped border growth")
    if not profiles[_PROFILE_OVERLAP]:
        reasons.append("no demonstration exercises union of overlapping stamps")
    # The canonical anchor condition is expressed directly to avoid treating
    # [] as false in the list-return semantic-hook convention.
    if not any(strict_canonical_like(pair["input"]) == [] for pair in demos):
        reasons.append("no demonstration anchors canonical full separated geometry")

    query_analysis = _analysis(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside teaching grammar")
    return reasons
