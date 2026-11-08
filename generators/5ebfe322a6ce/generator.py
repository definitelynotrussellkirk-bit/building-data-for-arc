"""Generator for ARC task 5ebfe322a6ce: choose maximum row-closure gain.

For each nonzero color, close every occupied row horizontally from its leftmost
marker to its rightmost marker.  The score is the number of cells added by that
closure.  Select the unique color with the largest *total* gain across all of
its rows, crop its closed shape, and recolor the crop cyan (8).

Normal generated scenes deliberately make several colors gain cells.  A
single very wide distractor row and a marker-rich distractor both lose to a
multi-row target whose summed gain is larger.  Those controls distinguish the
true rule from widest-span, largest-bounding-box, most-markers, most-rows, and
fixed-color shortcuts that fit all three canonical examples.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5ebfe322a6ce"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c97e8e4575ff"

SUMMARY = (
    "Horizontally close every row of every nonzero color, score each color by "
    "the total number of added cells, select the unique maximum-gain color, "
    "and return its tightly cropped closure recolored cyan (8)."
)

INVARIANTS = [
    "background is 0 and input markers use two to five nonzero colors",
    "at least two colors have positive horizontal-closure gain",
    "the winning color has a unique positive maximum total gain over all rows",
    "the winner occupies at least two rows and every winning row contains a visible gap",
    "normal draws contain a wider single-row distractor and a marker-richer distractor",
    "the returned input belongs to one exact observable scene profile",
]

# Each profile is identified exactly by (height, width, number of nonzero
# colors).  The first two reproduce the public profile envelope and output
# grammars; the generalized profiles add extra competitors and scale.
SCENE_SPECS = {
    "canonical_8x13_three": {
        "height": 8,
        "width": 13,
        "patterns": (
            ((0, 4, 2), (1, 4, 2)),       # target: total 8, output 2x6
            ((0, 7, 2),),                  # widest row: total 7
            ((0, 1, 3), (1, 1, 3), (2, 1, 3)),  # more rows/markers: total 3
        ),
    },
    "canonical_9x14_three": {
        "height": 9,
        "width": 14,
        "patterns": (
            ((0, 5, 2), (2, 5, 2)),       # target: total 10, output 3x7
            ((0, 9, 2),),                  # widest row: total 9
            ((0, 2, 4), (1, 2, 4), (2, 2, 4)),  # more rows/markers: total 6
        ),
    },
    "wide_12x17_four": {
        "height": 12,
        "width": 17,
        "patterns": (
            ((0, 3, 2), (1, 3, 2), (3, 3, 2)),  # target total 9
            ((0, 8, 2),),                        # widest row total 8
            ((0, 2, 4), (1, 2, 4), (2, 2, 4)),  # marker-rich total 6
            ((0, 1, 3), (1, 1, 3), (2, 1, 3), (3, 1, 3)),  # most rows, total 4
        ),
    },
    "hard_16x20_five": {
        "height": 16,
        "width": 20,
        "patterns": (
            ((0, 4, 2), (2, 4, 2), (4, 4, 2)),  # target total 12
            ((0, 11, 2),),                       # widest row total 11
            ((0, 3, 4), (1, 3, 4), (2, 3, 4)),  # marker-rich total 9
            ((0, 2, 3), (1, 2, 3), (2, 2, 3), (3, 2, 3)),
            ((0, 1, 3), (1, 1, 3)),              # total 2
        ),
    },
}
SCENE_PROFILES = tuple(SCENE_SPECS)
CANONICAL_PROFILES = frozenset(
    {"canonical_8x13_three", "canonical_9x14_three"}
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "keyed random choice over all exact scene profiles",
        "valid": "canonical_8x13_three|canonical_9x14_three|wide_12x17_four|hard_16x20_five",
    }
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
MIN_STRICT_FRAC = 0.25
EXAMPLES_NEEDED = 3


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _color_info(grid) -> dict[int, dict]:
    colors = sorted({value for row in grid for value in row if value != 0})
    infos: dict[int, dict] = {}
    for color in colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        by_row: dict[int, list[int]] = {}
        for r, c in cells:
            by_row.setdefault(r, []).append(c)
        row_stats = []
        closed = []
        for r in sorted(by_row):
            cols = sorted(by_row[r])
            lo, hi = cols[0], cols[-1]
            closure = [(r, c) for c in range(lo, hi + 1)]
            gain = len(closure) - len(cols)
            row_stats.append(
                {
                    "row": r,
                    "lo": lo,
                    "hi": hi,
                    "markers": len(cols),
                    "gain": gain,
                }
            )
            closed.extend(closure)
        infos[color] = {
            "color": color,
            "cells": cells,
            "marker_count": len(cells),
            "rows": tuple(sorted(by_row)),
            "row_count": len(by_row),
            "row_stats": tuple(row_stats),
            "closed": tuple(closed),
            "gain": sum(row["gain"] for row in row_stats),
            "max_row_gain": max((row["gain"] for row in row_stats), default=0),
            "bbox_width": (
                max(c for _, c in cells) - min(c for _, c in cells) + 1
                if cells
                else 0
            ),
        }
    return infos


def _winner_info(grid) -> tuple[dict[int, dict], dict]:
    infos = _color_info(grid)
    if not infos:
        raise ValueError("grid has no nonzero colors")
    winner = min(infos.values(), key=lambda info: (-info["gain"], info["color"]))
    return infos, winner


def _crop_closed(cells, color: int = 8) -> list[list[int]]:
    cells = list(cells)
    if not cells:
        raise ValueError("cannot crop an empty cell set")
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    output = full_grid(r2 - r1 + 1, c2 - c1 + 1, 0)
    for r, c in cells:
        output[r - r1][c - c1] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; the canonical Racket rule is authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    _, winner = _winner_info(grid)
    return _crop_closed(winner["closed"], 8)


def _profile_of(grid) -> str | None:
    if _grid_errors(grid):
        return None
    signature = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row if value != 0}),
    )
    for name, spec in SCENE_SPECS.items():
        expected = (spec["height"], spec["width"], len(spec["patterns"]))
        if signature == expected:
            return name
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding input scenes."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    _band(difficulty)
    infos = _color_info(grid)
    if not 2 <= len(infos) <= 5:
        errors.append(f"expected 2..5 nonzero colors, found {len(infos)}")
        return errors

    for color, info in infos.items():
        if info["marker_count"] < 2:
            errors.append(f"color {color} needs at least two markers")
        if any(row["markers"] < 2 for row in info["row_stats"]):
            errors.append(f"color {color} has a singleton row that hides row closure")

    ordered = sorted(infos.values(), key=lambda info: (-info["gain"], info["color"]))
    winner = ordered[0]
    max_gain_count = sum(info["gain"] == winner["gain"] for info in ordered)
    if winner["gain"] <= 0:
        errors.append("winning horizontal-closure gain must be positive")
    if max_gain_count != 1:
        errors.append(
            f"maximum gain must be unique, found {max_gain_count} colors at gain {winner['gain']}"
        )
    if sum(info["gain"] > 0 for info in ordered) < 2:
        errors.append("at least two colors must have positive closure gain")
    if winner["row_count"] < 2:
        errors.append("winner must span at least two rows so total gain is observable")
    if any(row["gain"] <= 0 for row in winner["row_stats"]):
        errors.append("every occupied winning row must contain a visible horizontal gap")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] only for the two public profile/output grammars."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = _profile_of(grid)
    if profile not in CANONICAL_PROFILES:
        reasons.append(f"scene profile {profile!r} is generalized rather than canonical")
        return reasons
    output = rule_mirror(grid)
    expected = {
        "canonical_8x13_three": (2, 6, ((8,) * 6, (8,) * 6)),
        "canonical_9x14_three": (3, 7, ((8,) * 7, (0,) * 7, (8,) * 7)),
    }[profile]
    shape_and_rows = (len(output), len(output[0]), tuple(tuple(row) for row in output))
    if shape_and_rows != expected:
        reasons.append(
            f"profile {profile!r} has noncanonical output grammar {shape_and_rows[:2]}"
        )
    return reasons


def canonical_profile_signature(grid):
    profile = _profile_of(grid)
    return profile if profile in CANONICAL_PROFILES and not strict_canonical_like(grid) else None


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("grid does not match a declared scene profile")
    return {"scene_profile": profile}


def _block_height(pattern) -> int:
    return max(row_offset for row_offset, _, _ in pattern) + 1


def _allocate_block_starts(rng, height: int, patterns) -> list[int]:
    heights = [_block_height(pattern) for pattern in patterns]
    order = list(range(len(patterns)))
    rng.shuffle(order)
    slack = height - sum(heights)
    if slack < 0:
        raise ValueError("profile row patterns do not fit")
    gaps = [0] * (len(patterns) + 1)
    for _ in range(slack):
        gaps[rng.randrange(len(gaps))] += 1
    starts = [0] * len(patterns)
    cursor = gaps[0]
    for position, pattern_index in enumerate(order):
        starts[pattern_index] = cursor
        cursor += heights[pattern_index] + gaps[position + 1]
    return starts


def _marker_columns(start: int, width: int, marker_count: int, rng) -> list[int]:
    if marker_count == 2:
        return [start, start + width - 1]
    interior = list(range(start + 1, start + width - 1))
    chosen = rng.sample(interior, marker_count - 2)
    return [start, *sorted(chosen), start + width - 1]


def _runtime_patterns(profile: str, rng):
    """Vary generalized target geometry without changing the exact profile."""
    patterns = [tuple(row for row in pattern) for pattern in SCENE_SPECS[profile]["patterns"]]
    if profile == "wide_12x17_four":
        gains = list(rng.choice(((2, 3, 4), (3, 3, 3))))
        rng.shuffle(gains)
        offsets = rng.choice(((0, 1, 3), (0, 2, 3), (0, 1, 2)))
        patterns[0] = tuple((offset, gain, 2) for offset, gain in zip(offsets, gains))
    elif profile == "hard_16x20_five":
        gains = list(rng.choice(((2, 5, 5), (3, 4, 5), (4, 4, 4))))
        rng.shuffle(gains)
        offsets = rng.choice(((0, 1, 4), (0, 2, 4), (0, 3, 4), (0, 1, 3)))
        patterns[0] = tuple((offset, gain, 2) for offset, gain in zip(offsets, gains))
    return tuple(patterns)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    spec = SCENE_SPECS[profile]
    height, width = spec["height"], spec["width"]
    rng = ctx.draw_rng(f"layout_{band}")
    patterns = _runtime_patterns(profile, rng)

    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], len(patterns))
    if palette[0] == min(palette):
        palette[0], palette[1] = palette[1], palette[0]
    starts = _allocate_block_starts(rng, height, patterns)
    grid = full_grid(height, width, 0)

    # Pattern 0 is the true maximum-gain target; colors and vertical block order
    # are randomized so neither fixed color nor fixed position predicts it.
    for pattern_index, (color, pattern, row_start) in enumerate(
        zip(palette, patterns, starts)
    ):
        aligned_start = None
        target_jitter = 0
        if pattern_index == 0:
            max_span = max(gain + markers for _, gain, markers in pattern)
            target_jitter = 0 if profile in CANONICAL_PROFILES else (2 if profile == "wide_12x17_four" else 3)
            aligned_start = rng.randint(0, width - max_span - target_jitter)
        for row_offset, gain, marker_count in pattern:
            span_width = gain + marker_count
            if aligned_start is None:
                col_start = rng.randint(0, width - span_width)
            else:
                col_start = aligned_start + (rng.randint(0, target_jitter) if target_jitter else 0)
            for col in _marker_columns(col_start, span_width, marker_count, rng):
                grid[row_start + row_offset][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"internal generator error for {profile}: {errors}")
    return grid


# ---------------------------------------------------------------------------
# Named plausible rival rules.  Every one fits all three canonical pairs; the
# generated wide-row and marker-rich controls force them to disagree.
# ---------------------------------------------------------------------------


def _rival_output(grid, key: Callable[[dict], tuple]) -> list[list[int]]:
    infos = _color_info(grid)
    if not infos:
        return []
    chosen = min(infos.values(), key=key)
    return _crop_closed(chosen["closed"], 8)


def _widest_single_row(grid):
    return _rival_output(grid, lambda info: (-info["max_row_gain"], info["color"]))


def _largest_bbox_width(grid):
    return _rival_output(grid, lambda info: (-info["bbox_width"], info["color"]))


def _most_markers(grid):
    return _rival_output(grid, lambda info: (-info["marker_count"], info["color"]))


def _most_active_rows(grid):
    return _rival_output(grid, lambda info: (-info["row_count"], info["color"]))


def _lowest_color(grid):
    return _rival_output(grid, lambda info: (info["color"],))


SEMANTIC_RIVALS = {
    "widest_single_row": _widest_single_row,
    "largest_bbox_width": _largest_bbox_width,
    "most_markers": _most_markers,
    "most_active_rows": _most_active_rows,
    "lowest_color": _lowest_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_info(grid):
    if self_check(grid):
        return None, None
    return _winner_info(grid)


def _witness_widest_loses(grid) -> bool:
    pair = _valid_info(grid)
    if pair == (None, None):
        return False
    infos, winner = pair
    return any(
        info["color"] != winner["color"]
        and info["max_row_gain"] > winner["max_row_gain"]
        for info in infos.values()
    )


def _witness_marker_rich_loses(grid) -> bool:
    pair = _valid_info(grid)
    if pair == (None, None):
        return False
    infos, winner = pair
    return any(
        info["color"] != winner["color"]
        and info["marker_count"] > winner["marker_count"]
        for info in infos.values()
    )


def _witness_more_rows_loses(grid) -> bool:
    pair = _valid_info(grid)
    if pair == (None, None):
        return False
    infos, winner = pair
    return any(
        info["color"] != winner["color"]
        and info["row_count"] > winner["row_count"]
        for info in infos.values()
    )


def _witness_multiple_positive_gains(grid) -> bool:
    pair = _valid_info(grid)
    if pair == (None, None):
        return False
    infos, _ = pair
    return sum(info["gain"] > 0 for info in infos.values()) >= 2


def _witness_winner_not_lowest_color(grid) -> bool:
    pair = _valid_info(grid)
    if pair == (None, None):
        return False
    infos, winner = pair
    return winner["color"] != min(infos)


def _witness_profile(name: str):
    return lambda grid: not self_check(grid) and _profile_of(grid) == name


SEMANTIC_WITNESSES = {
    "sum_beats_widest_single_row": _witness_widest_loses,
    "sum_beats_marker_count": _witness_marker_rich_loses,
    "sum_beats_active_row_count": _witness_more_rows_loses,
    "multiple_colors_need_closure": _witness_multiple_positive_gains,
    "winner_not_fixed_to_lowest_color": _witness_winner_not_lowest_color,
    "canonical_8x13_output_grammar": _witness_profile("canonical_8x13_three"),
    "canonical_9x14_output_grammar": _witness_profile("canonical_9x14_three"),
    "four_color_generalization": _witness_profile("wide_12x17_four"),
    "five_color_generalization": _witness_profile("hard_16x20_five"),
}

WITNESS_RIVALS = {
    "sum_beats_widest_single_row": ["widest_single_row", "largest_bbox_width"],
    "sum_beats_marker_count": ["most_markers"],
    "sum_beats_active_row_count": ["most_active_rows"],
    "winner_not_fixed_to_lowest_color": ["lowest_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named canonical-fitting shortcut survives."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is not lawful: {errors}")

    if reasons:
        return reasons

    query_answer = query["output"]
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} matches every demo but answers the query differently"
            )
    return reasons
