"""Generator for ARC task 9679db24667b, "Marker Takes the Row Color".

For each row, the unchanged Racket authority replaces every 9 when that row
contains exactly one distinct color outside {0, 9}.  Rows with no companion
color or multiple companion colors are unchanged.

The default lesson schedule alternates a sparse canonical profile with a
teaching profile.  Every teaching input simultaneously distinguishes the rule
from five plausible row-local shortcuts, so any consecutive three examples—and
all 3-of-4 query rotations—contain decisive evidence.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9679db24667b"
TASK_ID = GENERATOR_ID
RULE_HASH = "7ebc4d35864a"
VERSION = "3.0.0"
SUMMARY = (
    "Sparse 0-background row scenes. A qualifying row contains one distinct "
    "non-{0,9} color plus one or more 9s; every 9 in that row adopts the "
    "companion color. Canonical-profile inputs mirror the published examples. "
    "Alternating teaching-profile inputs add a 9-only row, a two-color row, "
    "multiple 9s, and repeated companion cells; those distractors stay "
    "unchanged and make the exact predicate and all-occurrences replacement "
    "identifiable from each consecutive lesson."
)

INVARIANTS = [
    "1..3 qualifying rows use pairwise-distinct companion colors",
    "canonical profile: qualifying rows have exactly one 9 and no distractor rows",
    "teaching profile: exactly one 9-only row and one two-color-plus-9 row stay unchanged",
    "teaching qualifying rows contain multiple 9s and repeated companion-color cells",
    "at least one blank row remains in every generated input",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchor or broad 6..10", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "canonical anchor or broad 8..12", "valid": "8..12"},
    "n_positive_rows": {"type": "int", "default": "canonical anchor or broad 1..3", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = ("canonical", "teaching")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

_ALLOWED_COLORS = tuple(range(1, 9))
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
# (height, width, qualifying-row count) reproduces every canonical
# (height, width, palette-size) profile because qualifying colors are distinct.
_CANONICAL_AXIS_PROFILES = (
    (6, 8, 2),
    (7, 9, 2),
    (8, 10, 3),
    (9, 10, 3),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic two-profile curriculum slot."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _band(difficulty) -> str:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return "medium" if difficulty is None else difficulty


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _scheduled_axis(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Draw an exact scheduled default while keeping the full override domain.

    ``GenCtx.draw_choice`` uses a fresh label-keyed RNG.  We independently
    reproduce its first index, then permute the complete option list so that
    the scheduled default occupies that index.  Every legal value remains in
    the option set, so caller overrides are still exact and provenance-backed.
    """
    if not lo <= default <= hi:
        raise ValueError(f"scheduled {name}={default} outside [{lo},{hi}]")
    options = list(range(lo, hi + 1))
    chosen_index = ctx.draw_rng(name).randrange(len(options))
    default_index = options.index(default)
    options[chosen_index], options[default_index] = (
        options[default_index],
        options[chosen_index],
    )
    return ctx.draw_choice(name, options)


def _put_values(row: list[int], values: list[int], rng) -> None:
    if len(values) > len(row):
        raise ValueError("row is too narrow for requested semantic witness")
    columns = rng.sample(range(len(row)), len(values))
    rng.shuffle(values)
    for column, value in zip(columns, values):
        row[column] = value


def _teaching_density(band: str, rng) -> tuple[int, int, int, int]:
    """Return positive color cells, positive 9s, 9-only count, multicolor 9s."""
    if band == "easy":
        return 2, 2, 2, 2
    if band == "hard":
        return 3, 3, 4, 3
    return rng.choice((2, 3)), rng.choice((2, 3)), 3, rng.choice((2, 3))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic input grid; labels remain Racket-authoritative."""
    _validate_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "canonical":
        h_default, w_default, n_positive_default = _CANONICAL_AXIS_PROFILES[
            (int(sample_index) // 2) % len(_CANONICAL_AXIS_PROFILES)
        ]
    else:
        # The teaching half explores the full public domains.  Dedicated RNG
        # labels keep these defaults independent while _scheduled_axis records
        # each advertised control through GenCtx.
        h_default = ctx.draw_rng("broad:grid_h").randint(6, 10)
        w_default = ctx.draw_rng("broad:grid_w").randint(8, 12)
        n_positive_default = ctx.draw_rng("broad:n_positive_rows").randint(1, 3)

    h = _scheduled_axis(ctx, "grid_h", 6, 10, h_default)
    w = _scheduled_axis(ctx, "grid_w", 8, 12, w_default)
    n_positive = _scheduled_axis(
        ctx, "n_positive_rows", 1, 3, n_positive_default
    )

    n_extra_rows = 2 if profile == "teaching" else 0
    if n_positive + n_extra_rows >= h:
        raise ValueError("grid_h must leave at least one blank row")

    layout_rng = ctx.draw_rng(f"layout:{band}:{profile}")
    occupied_rows = layout_rng.sample(range(h), n_positive + n_extra_rows)
    positive_rows = occupied_rows[:n_positive]
    positive_colors = ctx.draw_rng(f"colors:{band}:{profile}").sample(
        _ALLOWED_COLORS, n_positive + (2 if profile == "teaching" else 0)
    )

    grid = full_grid(h, w, 0)
    for index, (row_index, color) in enumerate(zip(positive_rows, positive_colors)):
        row_rng = ctx.draw_rng(f"positive:{band}:{profile}:{index}")
        if profile == "canonical":
            n_color = row_rng.randint(1, 3)
            n_nines = 1
        else:
            n_color, n_nines, _, _ = _teaching_density(band, row_rng)
        _put_values(grid[row_index], [color] * n_color + [9] * n_nines, row_rng)

    if profile == "teaching":
        nine_only_row, multi_color_row = occupied_rows[-2:]
        density_rng = ctx.draw_rng(f"distractor-density:{band}")
        _, _, n_nine_only, n_multi_nines = _teaching_density(band, density_rng)

        nine_rng = ctx.draw_rng(f"nine-only:{band}")
        _put_values(grid[nine_only_row], [9] * n_nine_only, nine_rng)

        multi_rng = ctx.draw_rng(f"multi-color:{band}")
        color_a, color_b = positive_colors[-2:]
        # 2:1 companion-color counts make both "first color" and "majority"
        # shortcuts visibly wrong; the correct exact-one-color predicate does nothing.
        _put_values(
            grid[multi_color_row],
            [color_a, color_a, color_b] + [9] * n_multi_nines,
            multi_rng,
        )

    return grid


def _grid_copy(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    rows: list[list[int]] = []
    width = None
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("grid rows must be nonempty lists")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("grid must be rectangular")
        copied = list(row)
        if any(type(value) is not int or not 0 <= value <= 9 for value in copied):
            raise ValueError("grid cells must be integer colors 0..9")
        rows.append(copied)
    return rows


def _row_colors(row: list[int]) -> set[int]:
    return {value for value in row if value not in (0, 9)}


def rule_mirror(grid):
    """Independent Python mirror of the unchanged Racket row predicate."""
    source = _grid_copy(grid)
    output = deepcopy(source)
    for row_index, row in enumerate(source):
        colors = _row_colors(row)
        if len(colors) == 1 and 9 in row:
            replacement = next(iter(colors))
            output[row_index] = [replacement if value == 9 else value for value in row]
    return output


def _analyze_grid(grid) -> dict[str, Any]:
    try:
        rows = _grid_copy(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "rows": [], "profile": None}

    h, w = len(rows), len(rows[0])
    errors: list[str] = []
    if not 6 <= h <= 10:
        errors.append(f"grid_h={h} outside [6,10]")
    if not 8 <= w <= 12:
        errors.append(f"grid_w={w} outside [8,12]")

    facts = []
    for index, row in enumerate(rows):
        colors = _row_colors(row)
        counts = Counter(value for value in row if value not in (0, 9))
        nines = row.count(9)
        colored_cells = sum(counts.values())
        if not colors and not nines:
            kind = "blank"
        elif len(colors) == 1 and nines:
            kind = "positive"
        elif not colors and nines:
            kind = "nine_only"
        elif len(colors) >= 2 and nines:
            kind = "multi_color"
        else:
            kind = "color_only"
        facts.append(
            {
                "index": index,
                "kind": kind,
                "colors": tuple(sorted(colors)),
                "counts": dict(counts),
                "nines": nines,
                "colored_cells": colored_cells,
            }
        )

    by_kind = {
        kind: [fact for fact in facts if fact["kind"] == kind]
        for kind in ("blank", "positive", "nine_only", "multi_color", "color_only")
    }
    positives = by_kind["positive"]
    if not 1 <= len(positives) <= 3:
        errors.append(f"expected 1..3 qualifying rows; found {len(positives)}")
    if not by_kind["blank"]:
        errors.append("expected at least one blank row")
    if by_kind["color_only"]:
        errors.append("rows with companion colors but no 9 are outside the generator grammar")

    positive_colors = [fact["colors"][0] for fact in positives]
    if len(set(positive_colors)) != len(positive_colors):
        errors.append("qualifying rows must use pairwise-distinct companion colors")

    if not by_kind["nine_only"] and not by_kind["multi_color"]:
        profile = "canonical"
        for fact in positives:
            if fact["nines"] != 1:
                errors.append("canonical qualifying rows must contain exactly one 9")
            if not 1 <= fact["colored_cells"] <= 3:
                errors.append("canonical qualifying rows need 1..3 companion-color cells")
    elif len(by_kind["nine_only"]) == 1 and len(by_kind["multi_color"]) == 1:
        profile = "teaching"
        for fact in positives:
            if not 2 <= fact["nines"] <= 3:
                errors.append("teaching qualifying rows need 2..3 nines")
            if not 2 <= fact["colored_cells"] <= 3:
                errors.append("teaching qualifying rows need 2..3 companion-color cells")
        nine_only = by_kind["nine_only"][0]
        if not 2 <= nine_only["nines"] <= 4:
            errors.append("the 9-only witness row needs 2..4 nines")
        multi = by_kind["multi_color"][0]
        if len(multi["colors"]) != 2:
            errors.append("the multicolor witness row must have exactly two companion colors")
        if sorted(multi["counts"].values()) != [1, 2]:
            errors.append("the multicolor witness row needs a 2:1 companion-color count")
        if not 2 <= multi["nines"] <= 3:
            errors.append("the multicolor witness row needs 2..3 nines")
    else:
        profile = None
        errors.append(
            "expected either no distractors or exactly one 9-only and one multicolor marker row"
        )

    return {
        "errors": errors,
        "rows": facts,
        "by_kind": by_kind,
        "profile": profile,
        "grid_h": h,
        "grid_w": w,
        "n_positive_rows": len(positives),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept only the two documented structural grammars (plus canonical data)."""
    del difficulty, meta
    return list(_analyze_grid(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised axis from pixels rather than RNG bookkeeping."""
    analysis = _analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError("invalid generated grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_positive_rows": analysis["n_positive_rows"],
    }


def strict_canonical_like(grid):
    """Accept lawful sparse examples without the teaching-only distractor rows."""
    analysis = _analyze_grid(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    if analysis["profile"] != "canonical":
        return ["contains teaching-only 9-only or multicolor distractor rows"]
    return []


# ---------------------------------------------------------------------------
# Explicit alternative rules used as semantic competitors, never as authority.
# ---------------------------------------------------------------------------

def _rival_first_nine_only(grid):
    source = _grid_copy(grid)
    output = deepcopy(source)
    for row_index, row in enumerate(source):
        colors = _row_colors(row)
        if len(colors) == 1 and 9 in row:
            output[row_index][row.index(9)] = next(iter(colors))
    return output


def _rival_unique_companion_cell_only(grid):
    source = _grid_copy(grid)
    output = deepcopy(source)
    for row_index, row in enumerate(source):
        companions = [value for value in row if value not in (0, 9)]
        if len(companions) == 1 and 9 in row:
            output[row_index] = [companions[0] if value == 9 else value for value in row]
    return output


def _rival_first_color_even_when_multiple(grid):
    source = _grid_copy(grid)
    output = deepcopy(source)
    for row_index, row in enumerate(source):
        companions = [value for value in row if value not in (0, 9)]
        if companions and 9 in row:
            output[row_index] = [companions[0] if value == 9 else value for value in row]
    return output


def _rival_majority_color_even_when_multiple(grid):
    source = _grid_copy(grid)
    output = deepcopy(source)
    for row_index, row in enumerate(source):
        companions = [value for value in row if value not in (0, 9)]
        if companions and 9 in row:
            counts = Counter(companions)
            replacement = max(
                counts,
                key=lambda color: (counts[color], -row.index(color)),
            )
            output[row_index] = [replacement if value == 9 else value for value in row]
    return output


def _rival_borrow_nearest_row_color(grid):
    source = _grid_copy(grid)
    output = rule_mirror(source)
    donor_rows = []
    for row_index, row in enumerate(source):
        colors = _row_colors(row)
        if len(colors) == 1:
            donor_rows.append((row_index, next(iter(colors))))
    for row_index, row in enumerate(source):
        if 9 in row and not _row_colors(row) and donor_rows:
            _, replacement = min(
                donor_rows,
                key=lambda item: (abs(item[0] - row_index), item[0]),
            )
            output[row_index] = [replacement if value == 9 else value for value in row]
    return output


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analyze_grid(grid)
    return None if analysis["errors"] else analysis


def _witness_multiple_nines(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and any(fact["nines"] >= 2 for fact in analysis["by_kind"]["positive"])
    )


def _witness_repeated_companion(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and any(fact["colored_cells"] >= 2 for fact in analysis["by_kind"]["positive"])
    )


def _witness_nine_only(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["by_kind"]["nine_only"])


def _witness_multicolor_marker_row(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["by_kind"]["multi_color"])


SEMANTIC_WITNESSES = {
    "replace_all_nines": _witness_multiple_nines,
    "distinct_color_not_single_cell": _witness_repeated_companion,
    "no_companion_means_no_change": _witness_nine_only,
    "multiple_companion_colors_mean_no_change": _witness_multicolor_marker_row,
}
SEMANTIC_RIVALS = {
    "first_nine_only": _rival_first_nine_only,
    "unique_companion_cell_only": _rival_unique_companion_cell_only,
    "first_color_even_when_multiple": _rival_first_color_even_when_multiple,
    "majority_color_even_when_multiple": _rival_majority_color_even_when_multiple,
    "borrow_nearest_row_color": _rival_borrow_nearest_row_color,
}
WITNESS_RIVALS = {
    "replace_all_nines": ["first_nine_only"],
    "distinct_color_not_single_cell": ["unique_companion_cell_only"],
    "no_companion_means_no_change": ["borrow_nearest_row_color"],
    "multiple_companion_colors_mean_no_change": [
        "first_color_even_when_multiple",
        "majority_color_even_when_multiple",
    ],
}
# These four wrong rules happen to fit every published pair; generated teaching
# examples are therefore necessary counterexamples.  The single-cell rival is
# already refuted by published rows containing repeated companion-color cells.
CANONICAL_SHORTCUTS = {
    "first_nine_only": _rival_first_nine_only,
    "first_color_even_when_multiple": _rival_first_color_even_when_multiple,
    "majority_color_even_when_multiple": _rival_majority_color_even_when_multiple,
    "borrow_nearest_row_color": _rival_borrow_nearest_row_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report named alternatives that fit all demos but change the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
