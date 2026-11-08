"""Curriculum generator for ``83c4d8ce9656``.

Rule
----
For every maximal horizontal segment of one nonzero color, preserve its first
and last cells and erase its interior.  A singleton is both endpoints and is
therefore preserved.

The canonical demonstrations leave three plausible shortcuts unresolved:

* transform only the longest run in each row;
* treat all occurrences of one color in a row as one span; and
* treat a touching multicolor nonzero block as one run.

Four consecutive generated examples deliberately include one canonical-scale
anchor and one counterexample to each shortcut.  The schedule is explicit so a
four-demo lesson is identifiable by construction rather than by luck.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "83c4d8ce9656"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8cf1fe655564"

SUMMARY = (
    "For each maximal same-color horizontal run, keep only its left and right "
    "endpoints (preserving singletons). Four scheduled scene profiles retain "
    "canonical-scale examples while refuting longest-run-only, per-color-span, "
    "and color-blind nonzero-block shortcuts."
)

INVARIANTS = [
    "the grid is rectangular, uses literal ARC colors 0..9, and contains background 0",
    "every instance contains at least three maximal same-color horizontal runs",
    "at least one run has an erasable interior and at least one run is length 1 or 2",
    "at least two nonzero colors are present",
    "the output is constructed by the pinned canonical Racket rule, not by this mirror",
]

SCENE_PROFILES = (
    "canonical_mix",
    "multiple_long_runs",
    "repeated_color_runs",
    "touching_color_runs",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "(seed + sample_index) modulo four",
        "valid": "|".join(SCENE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# Exact public input signatures: (height, width, palette size including zero).
_CANONICAL_SIGNATURES = {(5, 8, 6), (5, 9, 5)}


def _band(difficulty) -> str:
    if difficulty == "easy":
        return "easy"
    if difficulty == "hard":
        return "hard"
    return "medium"


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive indexes cover all profiles, with a seed phase.

    The seed-dependent rotation prevents an off-diagonal census from aliasing
    one residue while preserving exact four-consecutive lesson coverage.
    """
    del difficulty
    phase = int(seed) % len(SCENE_PROFILES)
    return SCENE_PROFILES[(int(sample_index) + phase) % len(SCENE_PROFILES)]


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _row_runs(row: Iterable[int], row_index: int) -> list[dict[str, int]]:
    values = list(row)
    runs: list[dict[str, int]] = []
    c = 0
    while c < len(values):
        color = values[c]
        if color == 0:
            c += 1
            continue
        end = c
        while end + 1 < len(values) and values[end + 1] == color:
            end += 1
        runs.append(
            {
                "row": row_index,
                "start": c,
                "end": end,
                "color": color,
                "length": end - c + 1,
            }
        )
        c = end + 1
    return runs


def analyze_grid(grid) -> dict[str, object]:
    """Return the same-color horizontal-run structure used by all contracts."""
    height, width, errors = _validate_grid(grid)
    if errors:
        return {
            "height": height,
            "width": width,
            "errors": errors,
            "runs": [],
            "runs_by_row": {},
            "palette": set(),
            "zero_count": 0,
            "touching_color_boundaries": [],
        }

    runs: list[dict[str, int]] = []
    runs_by_row: dict[int, list[dict[str, int]]] = {}
    touching: list[tuple[int, int, int, int]] = []
    palette: set[int] = set()
    zero_count = 0
    for r, row in enumerate(grid):
        row_runs = _row_runs(row, r)
        runs.extend(row_runs)
        runs_by_row[r] = row_runs
        palette.update(row)
        zero_count += sum(value == 0 for value in row)
        for c in range(width - 1):
            left, right = row[c], row[c + 1]
            if left != 0 and right != 0 and left != right:
                touching.append((r, c, left, right))
    return {
        "height": height,
        "width": width,
        "errors": [],
        "runs": runs,
        "runs_by_row": runs_by_row,
        "palette": palette,
        "zero_count": zero_count,
        "touching_color_boundaries": touching,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed grids and scenes that do not visibly teach the rule."""
    del difficulty, meta
    analysis = analyze_grid(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    height = int(analysis["height"])
    width = int(analysis["width"])
    runs = list(analysis["runs"])
    palette = set(analysis["palette"])
    if not (5 <= height <= 12):
        errors.append(f"height {height} outside supported range 5..12")
    if not (8 <= width <= 18):
        errors.append(f"width {width} outside supported range 8..18")
    if 0 not in palette or int(analysis["zero_count"]) == 0:
        errors.append("background color 0 must be visibly present")

    active_colors = palette - {0}
    if len(active_colors) < 2:
        errors.append(f"expected at least two nonzero colors, found {len(active_colors)}")
    if len(runs) < 3:
        errors.append(f"expected at least three horizontal runs, found {len(runs)}")
    if not any(int(run["length"]) >= 3 for run in runs):
        errors.append("no run has an erasable interior (length at least 3)")
    if not any(int(run["length"]) <= 2 for run in runs):
        errors.append("no length-1/2 run demonstrates endpoint preservation")
    return errors


def rule_mirror(grid):
    """Python mirror for tests only; the Racket program remains authoritative."""
    height, width, errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = full_grid(height, width, 0)
    for run in analyze_grid(grid)["runs"]:
        r = int(run["row"])
        start = int(run["start"])
        end = int(run["end"])
        color = int(run["color"])
        output[r][start] = color
        output[r][end] = color
    return output


def _rival_color_span_per_row(grid):
    """Wrong: merge separated occurrences of the same row/color into one span."""
    height, width, errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = full_grid(height, width, 0)
    for r, row in enumerate(grid):
        by_color: dict[int, list[int]] = defaultdict(list)
        for c, color in enumerate(row):
            if color != 0:
                by_color[color].append(c)
        for color, columns in by_color.items():
            output[r][columns[0]] = color
            output[r][columns[-1]] = color
    return output


def _rival_nonzero_block_endpoints(grid):
    """Wrong: ignore color boundaries inside a contiguous nonzero block."""
    height, width, errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = full_grid(height, width, 0)
    for r, row in enumerate(grid):
        c = 0
        while c < width:
            if row[c] == 0:
                c += 1
                continue
            end = c
            while end + 1 < width and row[end + 1] != 0:
                end += 1
            output[r][c] = row[c]
            output[r][end] = row[end]
            c = end + 1
    return output


def _rival_longest_run_per_row(grid):
    """Wrong: transform only one longest run in each row."""
    _, _, errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = [list(row) for row in grid]
    for r, row in enumerate(grid):
        runs = _row_runs(row, r)
        if not runs:
            continue
        chosen = max(runs, key=lambda run: (int(run["length"]), -int(run["start"])))
        for c in range(int(chosen["start"]) + 1, int(chosen["end"])):
            output[r][c] = 0
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


SEMANTIC_RIVALS = {
    "color_span_per_row": _rival_color_span_per_row,
    "nonzero_block_endpoints": _rival_nonzero_block_endpoints,
    "longest_run_per_row": _rival_longest_run_per_row,
}

# Each wrong rule above reproduces every public train/test pair.  The generated
# curriculum must therefore provide the missing counterexample.
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid) -> list[str]:
    """Narrow support matching public dimensions/palette and shortcut ambiguity."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    signature = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if signature not in _CANONICAL_SIGNATURES:
        reasons.append(
            f"canonical input signature is one of {sorted(_CANONICAL_SIGNATURES)}, "
            f"found {signature}"
        )
    authoritative = rule_mirror(grid)
    for name, shortcut in CANONICAL_SHORTCUTS.items():
        if shortcut(grid) != authoritative:
            reasons.append(f"canonical inputs do not refute shortcut {name}")
    return reasons


def _witness_multiple_long_runs(grid) -> bool:
    if self_check(grid):
        return False
    analysis = analyze_grid(grid)
    return any(
        sum(int(run["length"]) >= 3 for run in row_runs) >= 2
        for row_runs in analysis["runs_by_row"].values()
    ) and _rival_longest_run_per_row(grid) != rule_mirror(grid)


def _witness_same_color_separated_runs(grid) -> bool:
    if self_check(grid):
        return False
    return _rival_color_span_per_row(grid) != rule_mirror(grid)


def _witness_touching_color_boundary(grid) -> bool:
    if self_check(grid):
        return False
    return bool(analyze_grid(grid)["touching_color_boundaries"]) and (
        _rival_nonzero_block_endpoints(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "multiple_long_runs_one_row": _witness_multiple_long_runs,
    "same_color_separated_runs": _witness_same_color_separated_runs,
    "touching_color_boundary": _witness_touching_color_boundary,
}
WITNESS_RIVALS = {
    "multiple_long_runs_one_row": ["longest_run_per_row"],
    "same_color_separated_runs": ["color_span_per_row"],
    "touching_color_boundary": ["nonzero_block_endpoints"],
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "identity": _rival_identity,
}


def observe_overrides(grid) -> dict[str, object]:
    """Recover the one public axis from observable grid semantics."""
    analysis = analyze_grid(grid)
    if analysis["errors"]:
        return {"scene_profile": "invalid"}
    if analysis["touching_color_boundaries"]:
        return {"scene_profile": "touching_color_runs"}
    if _rival_color_span_per_row(grid) != rule_mirror(grid):
        return {"scene_profile": "repeated_color_runs"}
    if _witness_multiple_long_runs(grid):
        return {"scene_profile": "multiple_long_runs"}
    if not strict_canonical_like(grid):
        return {"scene_profile": "canonical_mix"}
    return {"scene_profile": "unclassified"}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a valid four-profile lesson that eliminates every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful teaching grammar")
    if "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output does not match the exact endpoint rule")

    profiles: set[str] = set()
    valid_pairs: list[dict] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the exact endpoint rule")
            continue
        profile = str(observe_overrides(demo["input"])["scene_profile"])
        if profile not in SCENE_PROFILES:
            reasons.append(f"demo {index} has unclassified scene profile {profile!r}")
        else:
            profiles.add(profile)
        valid_pairs.append(demo)

    missing = sorted(set(SCENE_PROFILES) - profiles)
    if missing:
        reasons.append(f"demonstrations omit scheduled scene profiles {missing}")
    for name, rival in LESSON_COMPETITORS.items():
        if valid_pairs and all(rival(pair["input"]) == pair["output"] for pair in valid_pairs):
            reasons.append(f"competitor {name} survives every demonstration")
    return reasons


def _put_run(grid, row: int, start: int, length: int, color: int) -> None:
    if length < 1:
        raise ValueError("run length must be positive")
    if not (0 <= row < len(grid)) or not (0 <= start <= len(grid[0]) - length):
        raise ValueError("run placement is out of bounds")
    if any(grid[row][c] != 0 for c in range(start, start + length)):
        raise ValueError("run placement overlaps an existing segment")
    for c in range(start, start + length):
        grid[row][c] = color


def _profile_dimensions(profile: str, band: str) -> tuple[int, int]:
    if profile == "canonical_mix":
        # Both signatures are exact public morphology; band only changes which
        # one is sampled, not the rule or profile.
        return (5, 8) if band == "easy" else (5, 9)
    return {
        "easy": (5, 10),
        "medium": (6, 11),
        "hard": (7, 13),
    }[band]


def _draw_colors(ctx, label: str, count: int) -> list[int]:
    return list(ctx.draw_distinct_colors(label, n=count, exclude={0}))


def _render_canonical_mix(ctx, band: str):
    height, width = _profile_dimensions("canonical_mix", band)
    rng = ctx.draw_rng(f"layout:canonical_mix:{band}")
    lengths = [1, 2, 3, 4, 5]
    rng.shuffle(lengths)

    nonzero_palette = 5 if width == 8 else 4
    colors = _draw_colors(ctx, f"colors:canonical_mix:{band}", nonzero_palette)
    rng.shuffle(colors)
    if width == 8:
        row_colors = colors[:]
    else:
        repeated = colors[rng.randrange(len(colors))]
        row_colors = colors[:] + [repeated]
        rng.shuffle(row_colors)

    grid = full_grid(height, width, 0)
    row_order = list(range(height))
    rng.shuffle(row_order)
    for index, row in enumerate(row_order):
        length = lengths[index]
        start = rng.randint(0, width - length)
        _put_run(grid, row, start, length, row_colors[index])
    return grid


def _general_profile_setup(ctx, profile: str, band: str, extra_colors: int):
    height, width = _profile_dimensions(profile, band)
    rng = ctx.draw_rng(f"layout:{profile}:{band}")
    colors = _draw_colors(ctx, f"colors:{profile}:{band}", height + extra_colors)
    rng.shuffle(colors)
    witness_row = rng.randrange(height)
    grid = full_grid(height, width, 0)
    return grid, rng, colors, witness_row


def _fill_other_rows(grid, rng, colors, witness_row: int, color_offset: int) -> None:
    rows = [row for row in range(len(grid)) if row != witness_row]
    rng.shuffle(rows)
    lengths = [1, 2, 3, 4, 5, 2, 3, 1]
    for index, row in enumerate(rows):
        length = min(lengths[index], len(grid[0]) - 1)
        start = rng.randint(0, len(grid[0]) - length)
        _put_run(grid, row, start, length, colors[color_offset + index])


def _render_multiple_long_runs(ctx, band: str):
    grid, rng, colors, row = _general_profile_setup(
        ctx, "multiple_long_runs", band, extra_colors=1
    )
    width = len(grid[0])
    max_length = 3 if band == "easy" else (4 if band == "medium" else 5)
    left_length = rng.randint(3, max_length)
    right_length = rng.randint(3, max_length)
    gap = rng.randint(1, 2)
    while left_length + gap + right_length > width:
        if right_length > 3:
            right_length -= 1
        elif left_length > 3:
            left_length -= 1
        else:
            gap = 1
            break
    span = left_length + gap + right_length
    start = rng.randint(0, width - span)
    _put_run(grid, row, start, left_length, colors[0])
    _put_run(grid, row, start + left_length + gap, right_length, colors[1])
    _fill_other_rows(grid, rng, colors, row, color_offset=2)
    return grid


def _render_repeated_color_runs(ctx, band: str):
    grid, rng, colors, row = _general_profile_setup(
        ctx, "repeated_color_runs", band, extra_colors=0
    )
    width = len(grid[0])
    max_length = 3 if band == "easy" else 4
    left_length = rng.randint(2, max_length)
    right_length = rng.randint(2, max_length)
    gap = rng.randint(1, 2)
    while left_length + gap + right_length > width:
        if right_length > 2:
            right_length -= 1
        elif left_length > 2:
            left_length -= 1
        else:
            gap = 1
            break
    span = left_length + gap + right_length
    start = rng.randint(0, width - span)
    _put_run(grid, row, start, left_length, colors[0])
    _put_run(grid, row, start + left_length + gap, right_length, colors[0])
    _fill_other_rows(grid, rng, colors, row, color_offset=1)
    return grid


def _render_touching_color_runs(ctx, band: str):
    grid, rng, colors, row = _general_profile_setup(
        ctx, "touching_color_runs", band, extra_colors=1
    )
    width = len(grid[0])
    max_length = 3 if band == "easy" else (4 if band == "medium" else 5)
    left_length = rng.randint(2, max_length)
    right_length = rng.randint(2, max_length)
    span = left_length + right_length
    start = rng.randint(0, width - span)
    _put_run(grid, row, start, left_length, colors[0])
    _put_run(grid, row, start + left_length, right_length, colors[1])
    _fill_other_rows(grid, rng, colors, row, color_offset=2)
    return grid


_RENDERERS = {
    "canonical_mix": _render_canonical_mix,
    "multiple_long_runs": _render_multiple_long_runs,
    "repeated_color_runs": _render_repeated_color_runs,
    "touching_color_runs": _render_touching_color_runs,
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    band = _band(difficulty)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", options)
    grid = _RENDERERS[profile](ctx, band)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid {profile!r} instance: {errors}")
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise ValueError(
            f"constructed profile {profile!r} but observer recovered {observed!r}"
        )
    return [row[:] for row in grid]
