"""Semantic generator for ARC task 6d19cd1698b1.

Every maximal horizontal run of one nonzero color grows into an immediately
adjacent zero on its left and right.  Runs at a canvas edge grow only on the
available side.  When two runs share a one-cell zero gap, row-major execution
makes the right-hand run own that shared cell.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d19cd1698b1"
TASK_ID = "6d19cd1698b1"
VERSION = "2.1.0"
RULE_HASH = "c5e0c631ccf8"
SUMMARY = "Grow every horizontal nonzero run by one cell into each available zero flank."

INVARIANTS = [
    "background is literal color 0",
    "each maximal same-color horizontal run is processed independently",
    "only an immediately adjacent zero flank can be painted",
    "left and right canvas edges suppress the missing-side growth",
    "a one-cell gap shared by two runs is overwritten by the later right-hand run",
    "generated lessons contain at least two runs and at least two visible output changes",
]

SCENE_PROFILES = (
    "independent",
    "wide_gap",
    "shared_flank",
    "adjacent_colors",
    "left_edge",
    "right_edge",
    "both_edges",
    "mixed",
    "repeated_color",
    "three_runs",
)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-scale weighted 3..10 with difficulty-biased tail",
        "valid": "3..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-scale weighted 7..14 with difficulty-biased tail",
        "valid": "7..14",
    },
    "scene_profile": {
        "type": "str",
        "default": "rng observable branch profile",
        "valid": "|".join(SCENE_PROFILES),
    },
}


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
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
        return ["cells must be ARC integers 0..9"]
    return []


def _scan_runs(grid):
    runs = []
    rows = defaultdict(list)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        col = 0
        while col < width:
            color = row[col]
            if color == 0:
                col += 1
                continue
            end = col
            while end + 1 < width and row[end + 1] == color:
                end += 1
            run = {
                "row": row_index,
                "start": col,
                "end": end,
                "length": end - col + 1,
                "color": color,
            }
            runs.append(run)
            rows[row_index].append(run)
            col = end + 1
    return runs, rows


def rule_mirror(grid):
    """Test-only Python mirror; production labels still come from Racket."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    width = len(grid[0])
    output = [list(row) for row in grid]
    runs, _ = _scan_runs(grid)
    for run in runs:
        row = run["row"]
        color = run["color"]
        left = run["start"] - 1
        right = run["end"] + 1
        if left >= 0 and grid[row][left] == 0:
            output[row][left] = color
        if right < width and grid[row][right] == 0:
            output[row][right] = color
    return output


def _profile_from_facts(*, row_runs, gaps, left_edge, right_edge):
    # Contrast profiles are inferred from geometry, never from hidden metadata.
    if any(len(runs) >= 3 for runs in row_runs.values()):
        return "three_runs"
    if any(len({run["color"] for run in runs}) < len(runs)
           for runs in row_runs.values()):
        return "repeated_color"
    same_row = any(len(runs) >= 2 for runs in row_runs.values())
    if same_row and (left_edge or right_edge):
        return "mixed"
    if any(gap == 1 for gap in gaps):
        return "shared_flank"
    if any(gap == 0 for gap in gaps):
        return "adjacent_colors"
    if same_row:
        return "wide_gap"
    if left_edge and right_edge:
        return "both_edges"
    if left_edge:
        return "left_edge"
    if right_edge:
        return "right_edge"
    return "independent"


def _analysis(grid):
    errors = _grid_errors(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    if not 3 <= height <= 10:
        errors.append("grid height must be in 3..10")
    if not 7 <= width <= 14:
        errors.append("grid width must be in 7..14")

    runs, row_runs = _scan_runs(grid)
    gaps = []
    for current_runs in row_runs.values():
        for left, right in zip(current_runs, current_runs[1:]):
            gaps.append(right["start"] - left["end"] - 1)

    left_edge = any(run["start"] == 0 for run in runs)
    right_edge = any(run["end"] == width - 1 for run in runs)
    output = rule_mirror(grid)
    changed = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != output[row][col]
    }
    blank_rows = sum(all(value == 0 for value in row) for row in grid)
    background_count = sum(value == 0 for row in grid for value in row)
    colors = {run["color"] for run in runs}

    if not 2 <= len(runs) <= 6:
        errors.append(f"teaching scenes require 2..6 horizontal runs, found {len(runs)}")
    if runs and not any(run["length"] >= 2 for run in runs):
        errors.append("at least one run must contain two or more cells")
    if any(run["length"] > 5 for run in runs):
        errors.append("calibrated run lengths are 1..5")
    if any(len(current_runs) > 3 for current_runs in row_runs.values()):
        errors.append("a row may contain at most three runs")
    if blank_rows < 1:
        errors.append("at least one blank distractor row is required")
    if background_count <= height * width // 2:
        errors.append("literal background 0 must occupy a strict majority")
    if not 2 <= len(colors) <= 5:
        errors.append("teaching scenes use two through five nonzero colors")
    if len(changed) < 2:
        errors.append("the rule must make at least two visible cell changes")

    profile = _profile_from_facts(
        row_runs=row_runs,
        gaps=gaps,
        left_edge=left_edge,
        right_edge=right_edge,
    )
    write_counts = Counter()
    writes = []
    for run in runs:
        row = run["row"]
        for side, col in (("left", run["start"] - 1), ("right", run["end"] + 1)):
            if 0 <= col < width and grid[row][col] == 0:
                write_counts[(row, col)] += 1
                writes.append(
                    {
                        "row": row,
                        "col": col,
                        "color": run["color"],
                        "side": side,
                    }
                )

    result.update(
        {
            "errors": errors,
            "scene_profile": profile,
            "runs": runs,
            "row_runs": dict(row_runs),
            "gaps": gaps,
            "left_edge": left_edge,
            "right_edge": right_edge,
            "changed_cells": sorted(changed),
            "output": output,
            "writes": writes,
            "shared_write_cells": sorted(cell for cell, count in write_counts.items() if count > 1),
            "blank_rows": blank_rows,
            "color_count": len(colors),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {})
    if not errors:
        observed = {
            "grid_h": len(grid),
            "grid_w": len(grid[0]),
            "scene_profile": analysis["scene_profile"],
        }
        for key in ("grid_h", "grid_w", "scene_profile"):
            if key in requested and requested[key] != observed[key]:
                errors.append(
                    f"{key} drifted from requested {requested[key]!r} to {observed[key]!r}"
                )
    return errors


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_profile": analysis["scene_profile"],
    }


def _run_count(difficulty, capacity, rng):
    bounds = {
        "easy": (2, 3),
        "medium": (2, 4),
        "hard": (3, 5),
        None: (2, 5),
    }
    lo, hi = bounds[difficulty]
    hi = min(hi, capacity, 6)
    lo = min(lo, hi)
    return rng.randint(lo, hi)


def _interior_layout(width, rng):
    options = [
        (start, start + length - 1)
        for length in range(1, min(5, width - 2) + 1)
        for start in range(1, width - length)
        if start + length - 1 <= width - 2
    ]
    return rng.choice(options)


def _left_layout(width, rng):
    length = rng.randint(1, min(5, width - 1))
    return 0, length - 1


def _right_layout(width, rng):
    length = rng.randint(1, min(5, width - 1))
    return width - length, width - 1


@lru_cache(maxsize=48)
def _pair_layouts(width, profile):
    options = []
    for first_length in range(1, 6):
        for second_length in range(1, 6):
            for first_start in range(width):
                first_end = first_start + first_length - 1
                if first_end >= width:
                    continue
                for gap in range(0, width):
                    second_start = first_end + gap + 1
                    second_end = second_start + second_length - 1
                    if second_end >= width:
                        continue
                    no_edge = first_start > 0 and second_end < width - 1
                    has_edge = first_start == 0 or second_end == width - 1
                    if profile in ("wide_gap", "repeated_color") and no_edge and gap >= 2:
                        options.append((first_start, first_end, second_start, second_end))
                    elif profile == "shared_flank" and no_edge and gap == 1:
                        options.append((first_start, first_end, second_start, second_end))
                    elif profile == "adjacent_colors" and no_edge and gap == 0:
                        options.append((first_start, first_end, second_start, second_end))
                    elif profile == "mixed" and has_edge and gap >= 1:
                        options.append((first_start, first_end, second_start, second_end))
    return tuple(options)


@lru_cache(maxsize=8)
def _triple_layouts(width):
    """Interior three-run layouts; touching runs receive different colors."""
    options = []
    for first_length in range(1, 6):
        for second_length in range(1, 6):
            for third_length in range(1, 6):
                if max(first_length, second_length, third_length) < 2:
                    continue
                for first_gap in range(3):
                    for second_gap in range(3):
                        span = first_length + second_length + third_length + first_gap + second_gap
                        for start in range(1, width - span):
                            a_end = start + first_length - 1
                            b_start = a_end + first_gap + 1
                            b_end = b_start + second_length - 1
                            c_start = b_end + second_gap + 1
                            options.append((start, a_end, b_start, b_end,
                                            c_start, c_start + third_length - 1))
    return tuple(options)


def _paint_runs(height, width, intervals, pair_indices, rng, *, profile):
    grid = full_grid(height, width, 0)
    minimum_palette = 3 if profile == "three_runs" else 2
    maximum_palette = min(5, len(intervals), 9)
    palette_size = rng.randint(minimum_palette, maximum_palette)
    palette = rng.sample(list(range(1, 10)), palette_size)
    colors = [rng.choice(palette) for _ in intervals]

    for left_index, right_index in pair_indices:
        if colors[left_index] == colors[right_index]:
            colors[right_index] = rng.choice(
                [color for color in palette if color != colors[left_index]]
            )
    if len(intervals) >= 3 and rng.random() < 0.55:
        colors[-1] = colors[0]

    if profile == "repeated_color":
        # Two disconnected occurrences in one row plus another color elsewhere.
        # Distinct outer bounds cannot explain the two inward growth cells.
        colors[1] = colors[0]
        colors[2] = rng.choice([color for color in palette if color != colors[0]])
    elif profile == "three_runs":
        # Preserve all three runs even when they touch, and give the third an
        # observable right flank. The layout is strictly interior.
        colors[:3] = rng.sample(palette, 3)

    for (row, start, end), color in zip(intervals, colors):
        for col in range(start, end + 1):
            grid[row][col] = color
    return grid


def _construct_scene(height, width, profile, difficulty, rng):
    for _ in range(256):
        intervals = []
        pair_indices = []
        rows = list(range(height))
        rng.shuffle(rows)

        if profile == "three_runs":
            triple = rng.choice(_triple_layouts(width))
            intervals.extend((rows[0], triple[i], triple[i + 1]) for i in (0, 2, 4))
            capacity = 3 + max(0, height - 2)
            target_count = max(3, _run_count(difficulty, capacity, rng))
            for row in rows[1 : 1 + target_count - 3]:
                intervals.append((row, *_interior_layout(width, rng)))
        elif profile in ("wide_gap", "shared_flank", "adjacent_colors", "mixed", "repeated_color"):
            pair_options = _pair_layouts(width, profile)
            if not pair_options:
                raise ValueError(
                    f"scene_profile={profile!r} is incompatible with grid_w={width}"
                )
            pair_row = rows[0]
            first_start, first_end, second_start, second_end = rng.choice(pair_options)
            intervals.extend(
                [
                    (pair_row, first_start, first_end),
                    (pair_row, second_start, second_end),
                ]
            )
            pair_indices.append((0, 1))
            capacity = 2 + max(0, height - 2)
            target_count = _run_count(difficulty, capacity, rng)
            if profile == "repeated_color":
                target_count = max(3, target_count)
            extra_rows = rows[1 : 1 + max(0, target_count - 2)]
            for row in extra_rows:
                start, end = _interior_layout(width, rng)
                intervals.append((row, start, end))
        else:
            capacity = max(2, height - 1)
            target_count = _run_count(difficulty, capacity, rng)
            selected_rows = rows[:target_count]
            if profile == "left_edge":
                intervals.append((selected_rows[0], *_left_layout(width, rng)))
                for row in selected_rows[1:]:
                    intervals.append((row, *_interior_layout(width, rng)))
            elif profile == "right_edge":
                intervals.append((selected_rows[0], *_right_layout(width, rng)))
                for row in selected_rows[1:]:
                    intervals.append((row, *_interior_layout(width, rng)))
            elif profile == "both_edges":
                intervals.append((selected_rows[0], *_left_layout(width, rng)))
                intervals.append((selected_rows[1], *_right_layout(width, rng)))
                for row in selected_rows[2:]:
                    intervals.append((row, *_interior_layout(width, rng)))
            else:
                for row in selected_rows:
                    intervals.append((row, *_interior_layout(width, rng)))

        grid = _paint_runs(height, width, intervals, pair_indices, rng, profile=profile)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct calibrated profile {profile!r}")



def _size_options(difficulty):
    # Keep canonical scale in EVERY band, not only the easy interval. The
    # shared prior retains all supported dimensions; difficulty changes only
    # the added tail weights and the run-count distribution, never support.
    heights = tuple(range(3, 11)) + (3,) * 16 + (4,) * 3 + (6,) * 2
    widths = tuple(range(7, 15)) + (7,) * 8 + (8,) * 4 + (9,) * 8
    h_tail, w_tail = {
        "easy": ((3, 4, 5), (7, 8, 9)),
        "medium": ((5, 6, 7), (9, 10, 11)),
        "hard": ((8, 9, 10), (12, 13, 14)),
        None: ((), ()),
    }[difficulty]
    return heights + h_tail * 2, widths + w_tail * 2


def _rival_color_envelope(grid):
    """Evaluation-only competitor; never used to produce training labels."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for color in sorted(set(row) - {0}, key=row.index):
            positions = [c for c, value in enumerate(row) if value == color]
            for c in (positions[0] - 1, positions[-1] + 1):
                if 0 <= c < len(row) and row[c] == 0:
                    out[r][c] = color
    return out


def _rival_first_two_runs(grid):
    """Evaluation-only competitor that drops a third run in a row."""
    out = [list(row) for row in grid]
    _, row_runs = _scan_runs(grid)
    for r, runs in row_runs.items():
        for run in runs[:2]:
            for c in (run["start"] - 1, run["end"] + 1):
                if 0 <= c < len(grid[r]) and grid[r][c] == 0:
                    out[r][c] = run["color"]
    return out


SEMANTIC_RIVALS = {
    "color_envelope": _rival_color_envelope,
    "first_two_runs": _rival_first_two_runs,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "repeated_color": lambda grid: _analysis(grid)["scene_profile"] == "repeated_color",
    "three_runs": lambda grid: _analysis(grid)["scene_profile"] == "three_runs",
}
WITNESS_RIVALS = {
    "repeated_color": ["color_envelope"],
    "three_runs": ["first_two_runs"],
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    for key in ("grid_h", "grid_w"):
        if key in overrides and type(overrides[key]) is not int:
            raise ValueError(f"{key} must be an integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height_options, width_options = _size_options(difficulty)
    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    grid = _construct_scene(height, width, profile, difficulty, ctx.draw_rng("geometry"))
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile!r} -> {analysis}")
    return grid
