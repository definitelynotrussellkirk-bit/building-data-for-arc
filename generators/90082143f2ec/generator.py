"""Canonical-shaped generator for noisy horizontal/vertical color bands.

The task rule compares column and row coherence, then replaces every cell with
its mode on the more coherent axis.  Generated inputs deliberately contain
visible noise, both orientations, and enough examples per lesson to refute the
identity, fixed-axis, and canonical-shape-to-axis shortcuts.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "90082143f2ec"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "a86d1f36d1d2"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.99

SUMMARY = (
    "Remove noise from colored bands: compare column-mode and row-mode "
    "coherence, then fill every column or row with its mode on the more "
    "coherent axis."
)

INVARIANTS = [
    "the input uses all nine non-background ARC colors 1..9",
    "three to five contiguous bands of width at least two define one axis",
    "13%-21% of cells are noise while every dominant slice keeps a strict mode",
    "row and column coherence are decisively different, so the rule is unambiguous",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "13..15",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "14..17",
    },
    "orientation": {
        "type": "str",
        "default": "scheduled vertical/horizontal",
        "valid": "vertical|horizontal",
    },
    "band_count": {
        "type": "int",
        "default": "scheduled 3..5",
        "valid": "3..5",
    },
    "noise_level": {
        "type": "str",
        "default": "scheduled moderate/high",
        "valid": "moderate|high",
    },
}

# The canonical demonstrations accidentally couple shape and orientation:
# height 13 always means vertical bands, while height 15 always means horizontal
# bands.  The eight-slot curriculum keeps every canonical shape but presents it
# once in each orientation.  Match/mismatch slots alternate, so every three-demo
# lesson and every three-of-four query rotation refutes that shape-only shortcut.
# Orientation and noise are independently balanced, and every three consecutive
# slots retain both orientations, both noise levels, and at least two band counts.
_PROFILE_TABLE = (
    (13, 14, "vertical", 3, "moderate"),
    (13, 14, "horizontal", 4, "high"),
    (15, 14, "horizontal", 5, "moderate"),
    (15, 14, "vertical", 3, "high"),
    (13, 17, "vertical", 4, "moderate"),
    (13, 17, "horizontal", 5, "high"),
    (15, 15, "horizontal", 3, "moderate"),
    (15, 15, "vertical", 4, "high"),
)
LESSON_SCHEDULE_PERIOD = len(_PROFILE_TABLE)
SCHEDULE_PROFILES = tuple(f"shape_axis_counterbalanced_{i}" for i in range(LESSON_SCHEDULE_PERIOD))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared profile label for semantic-gate schedule auditing."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _partition(total: int, count: int, rng) -> list[int]:
    """Make varied but balanced bands, avoiding a shortcut-hiding giant band."""
    if total < 2 * count:
        raise ValueError(f"cannot fit {count} bands of width >=2 into length {total}")
    base, remainder = divmod(total, count)
    parts = [base + (1 if index < remainder else 0) for index in range(count)]
    rng.shuffle(parts)
    # One bounded transfer reproduces canonical width variation while keeping
    # every band >=2 and preventing one band from dominating the opposite-axis
    # row/column modes.
    donors = [index for index, width in enumerate(parts) if width > 3]
    recipients = [index for index, width in enumerate(parts) if width >= 2]
    if donors and recipients and rng.random() < 0.75:
        donor = rng.choice(donors)
        recipient = rng.choice([index for index in recipients if index != donor])
        parts[donor] -= 1
        parts[recipient] += 1
    rng.shuffle(parts)
    return parts


def _expand_runs(widths: list[int], colors: list[int]) -> list[int]:
    values: list[int] = []
    for width, color in zip(widths, colors):
        values.extend([color] * width)
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w, scheduled_orientation, scheduled_bands, scheduled_noise = (
        _PROFILE_TABLE[int(sample_index) % len(_PROFILE_TABLE)]
    )
    h = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 13, 15)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 14, 17)
    orientation = _draw_scheduled_choice(
        ctx, "orientation", scheduled_orientation, ("vertical", "horizontal")
    )
    band_count = _draw_scheduled_int(ctx, "band_count", scheduled_bands, 3, 5)
    noise_level = _draw_scheduled_choice(
        ctx, "noise_level", scheduled_noise, ("moderate", "high")
    )

    # Difficulty changes the concrete colors, widths, and noise placement while
    # preserving the same canonical semantic profile and lesson schedule.
    rng = ctx.draw_rng(f"construction:{difficulty or 'unspecified'}")
    axis_length = w if orientation == "vertical" else h
    widths = _partition(axis_length, band_count, rng)
    band_colors = rng.sample(list(range(1, 10)), band_count)
    axis_modes = _expand_runs(widths, band_colors)

    if orientation == "vertical":
        grid = [[axis_modes[c] for c in range(w)] for _ in range(h)]
        dominant_slices = w
        slice_length = h
    else:
        grid = [[axis_modes[r] for _ in range(w)] for r in range(h)]
        dominant_slices = h
        slice_length = w

    target_rate = 0.15 if noise_level == "moderate" else 0.19
    target_noise = round(h * w * target_rate)
    per_slice_cap = max(1, slice_length // 3)
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    used_per_slice = [0] * dominant_slices
    chosen: list[tuple[int, int]] = []
    for r, c in positions:
        slice_index = c if orientation == "vertical" else r
        if used_per_slice[slice_index] >= per_slice_cap:
            continue
        used_per_slice[slice_index] += 1
        chosen.append((r, c))
        if len(chosen) == target_noise:
            break
    if len(chosen) != target_noise:
        raise RuntimeError(
            f"could place only {len(chosen)}/{target_noise} mode-preserving noise cells"
        )

    missing_colors = [color for color in range(1, 10) if color not in band_colors]
    rng.shuffle(missing_colors)
    for index, (r, c) in enumerate(chosen):
        base = grid[r][c]
        if index < len(missing_colors):
            replacement = missing_colors[index]
        else:
            replacement = rng.choice([color for color in range(1, 10) if color != base])
        grid[r][c] = replacement

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator emitted invalid grid: " + "; ".join(errors))
    return grid


def _mode(values: list[int]) -> int:
    counts = Counter(values)
    best = max(counts.values())
    return min(value for value, count in counts.items() if count == best)


def _mode_is_strict(values: list[int], mode: int) -> bool:
    counts = Counter(values)
    ordered = sorted(counts.values(), reverse=True)
    runner_up = ordered[1] if len(ordered) > 1 else 0
    return counts[mode] > runner_up and counts[mode] > len(values) // 2


def _run_lengths(values: list[int]) -> list[tuple[int, int]]:
    if not values:
        return []
    runs: list[tuple[int, int]] = []
    current = values[0]
    width = 1
    for value in values[1:]:
        if value == current:
            width += 1
        else:
            runs.append((current, width))
            current = value
            width = 1
    runs.append((current, width))
    return runs


def _solve_rows(grid: list[list[int]]) -> list[list[int]]:
    return [[_mode(row)] * len(row) for row in grid]


def _solve_cols(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    modes = [_mode([grid[r][c] for r in range(h)]) for c in range(w)]
    return [[modes[c] for c in range(w)] for _ in range(h)]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; the Racket program remains output authority."""
    h, w = len(grid), len(grid[0])
    col_modes = [_mode([grid[r][c] for r in range(h)]) for c in range(w)]
    row_modes = [_mode(list(grid[r])) for r in range(h)]
    col_coherence = sum(grid[r][c] == col_modes[c] for r in range(h) for c in range(w))
    row_coherence = sum(grid[r][c] == row_modes[r] for r in range(h) for c in range(w))
    if col_coherence > row_coherence:
        return [[col_modes[c] for c in range(w)] for _ in range(h)]
    return [[row_modes[r] for _ in range(w)] for r in range(h)]


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Recover exact semantic axes and structural measurements from a grid."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    if w == 0 or any(len(row) != w for row in grid):
        return {"errors": ["grid must be non-empty and rectangular"], "grid_h": h, "grid_w": w}
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9"], "grid_h": h, "grid_w": w}

    col_modes = [_mode([grid[r][c] for r in range(h)]) for c in range(w)]
    row_modes = [_mode(list(grid[r])) for r in range(h)]
    col_coherence = sum(grid[r][c] == col_modes[c] for r in range(h) for c in range(w))
    row_coherence = sum(grid[r][c] == row_modes[r] for r in range(h) for c in range(w))
    orientation = "vertical" if col_coherence > row_coherence else "horizontal"
    ambiguous = col_coherence == row_coherence
    dominant_modes = col_modes if orientation == "vertical" else row_modes
    dominant_lines = (
        [[grid[r][c] for r in range(h)] for c in range(w)]
        if orientation == "vertical"
        else [list(row) for row in grid]
    )
    runs = _run_lengths(dominant_modes)
    clean = _solve_cols(grid) if orientation == "vertical" else _solve_rows(grid)
    alternate = _solve_rows(grid) if orientation == "vertical" else _solve_cols(grid)
    noise_count = sum(
        grid[r][c] != clean[r][c] for r in range(h) for c in range(w)
    )
    noise_rate = noise_count / (h * w)
    return {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "palette": sorted({value for row in grid for value in row}),
        "orientation": orientation,
        "ambiguous": ambiguous,
        "col_coherence": col_coherence,
        "row_coherence": row_coherence,
        "coherence_margin": abs(col_coherence - row_coherence),
        "band_count": len(runs),
        "band_runs": runs,
        "band_colors_distinct": len({color for color, _ in runs}) == len(runs),
        "strict_modes": all(
            _mode_is_strict(line, mode)
            for line, mode in zip(dominant_lines, dominant_modes)
        ),
        "noise_count": noise_count,
        "noise_rate": noise_rate,
        "noise_level": "moderate" if noise_rate < 0.17 else "high",
        "clean": clean,
        "alternate": alternate,
        "identity": clean == grid,
        "axis_answers_differ": clean != alternate,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, ambiguous, or shortcut-hiding scenes."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    h, w = facts["grid_h"], facts["grid_w"]
    if not 13 <= h <= 15:
        errors.append(f"height {h} outside 13..15")
    if not 14 <= w <= 17:
        errors.append(f"width {w} outside 14..17")
    if facts["palette"] != list(range(1, 10)):
        errors.append(f"palette {facts['palette']} must be exactly colors 1..9")
    if facts["ambiguous"]:
        errors.append("row and column coherence tie; orientation is ambiguous")
    total = h * w
    if facts["coherence_margin"] < round(0.30 * total):
        errors.append(
            f"coherence margin {facts['coherence_margin']} is too small for an identifiable axis"
        )
    if not 3 <= facts["band_count"] <= 5:
        errors.append(f"band count {facts['band_count']} outside 3..5")
    if any(width < 2 for _, width in facts["band_runs"]):
        errors.append(f"singleton band in runs {facts['band_runs']}")
    if not facts["band_colors_distinct"]:
        errors.append("non-adjacent band runs reuse a mode color")
    if not facts["strict_modes"]:
        errors.append("at least one dominant row/column lacks a strict majority mode")
    if not 0.13 <= facts["noise_rate"] <= 0.21:
        errors.append(f"noise rate {facts['noise_rate']:.3f} outside 0.13..0.21")
    if facts["identity"]:
        errors.append("input is already clean; transformation would be identity")
    if not facts["axis_answers_differ"]:
        errors.append("row-mode and column-mode rules produce the same answer")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in {(13, 14), (13, 17), (15, 14), (15, 15)}:
        errors.append(f"shape {(h, w)} is in the teaching envelope but not a canonical profile")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "orientation": facts["orientation"],
        "band_count": facts["band_count"],
        "noise_level": facts["noise_level"],
    }


def _valid_facts(grid) -> dict[str, Any] | None:
    if self_check(grid):
        return None
    return semantic_observables(grid)


def _witness_orientation(name: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: bool((facts := _valid_facts(grid)) and facts["orientation"] == name)


def _witness_bands(count: int) -> Callable[[list[list[int]]], bool]:
    return lambda grid: bool((facts := _valid_facts(grid)) and facts["band_count"] == count)


def _witness_noise(level: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: bool((facts := _valid_facts(grid)) and facts["noise_level"] == level)


def _witness_shape_axis_counterexample(orientation: str) -> Callable[[list[list[int]]], bool]:
    expected_height = 15 if orientation == "vertical" else 13
    return lambda grid: bool(
        (facts := _valid_facts(grid))
        and facts["orientation"] == orientation
        and facts["grid_h"] == expected_height
    )


SEMANTIC_WITNESSES = {
    "vertical_axis": _witness_orientation("vertical"),
    "horizontal_axis": _witness_orientation("horizontal"),
    "three_bands": _witness_bands(3),
    "four_bands": _witness_bands(4),
    "five_bands": _witness_bands(5),
    "moderate_noise": _witness_noise("moderate"),
    "high_noise": _witness_noise("high"),
    "vertical_on_tall_shape": _witness_shape_axis_counterexample("vertical"),
    "horizontal_on_short_shape": _witness_shape_axis_counterexample("horizontal"),
    "all_nine_colors": lambda grid: not self_check(grid)
    and semantic_observables(grid)["palette"] == list(range(1, 10)),
}


def _identity(grid):
    return copy.deepcopy(grid)


def _always_rows(grid):
    return _solve_rows(grid)


def _always_cols(grid):
    return _solve_cols(grid)


def _global_mode(grid):
    h, w = len(grid), len(grid[0])
    color = _mode([value for row in grid for value in row])
    return [[color for _ in range(w)] for _ in range(h)]


def _shape_axis_shortcut(grid):
    """Canonical-fitting shortcut: infer the denoising axis from height only."""
    return _solve_cols(grid) if len(grid) == 13 else _solve_rows(grid)


SEMANTIC_RIVALS = {
    "identity": _identity,
    "always_row_modes": _always_rows,
    "always_column_modes": _always_cols,
    "global_mode_fill": _global_mode,
    "shape_axis_shortcut": _shape_axis_shortcut,
}
WITNESS_RIVALS = {
    "vertical_axis": ["always_row_modes"],
    "horizontal_axis": ["always_column_modes"],
    "three_bands": ["identity"],
    "four_bands": ["identity"],
    "five_bands": ["identity"],
    "moderate_noise": ["identity"],
    "high_noise": ["identity"],
    "vertical_on_tall_shape": ["shape_axis_shortcut"],
    "horizontal_on_short_shape": ["shape_axis_shortcut"],
    "all_nine_colors": ["global_mode_fill"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that reject plausible fixed-axis shortcuts."""
    reasons: list[str] = []
    orientations: set[str] = set()
    noise_levels: set[str] = set()
    band_counts: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output does not match the coherence rule")
        facts = semantic_observables(demo["input"])
        orientations.add(facts["orientation"])
        noise_levels.add(facts["noise_level"])
        band_counts.add(facts["band_count"])
    if orientations != {"vertical", "horizontal"}:
        reasons.append("demos do not contain both vertical and horizontal cases")
    if noise_levels != {"moderate", "high"}:
        reasons.append("demos do not contain both canonical noise levels")
    if len(band_counts) < 2:
        reasons.append("demos do not vary the number of bands")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
        return reasons
    official_query = rule_mirror(query["input"])
    if official_query != query["output"]:
        reasons.append("query output does not match the coherence rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            isinstance(demo, dict)
            and "input" in demo
            and competitor(demo["input"]) == demo.get("output")
            for demo in demos
        )
        if survives and competitor(query["input"]) != official_query:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named task-local near-misses that structural self_check must reject."""
    valid = generate(99173, 0, difficulty="medium")
    fixtures: list[tuple[str, list[list[int]]]] = []

    no_noise = rule_mirror(valid)
    fixtures.append(("already_clean_identity", no_noise))

    reduced_palette = copy.deepcopy(valid)
    for r, row in enumerate(reduced_palette):
        for c, value in enumerate(row):
            if value not in (1, 2):
                reduced_palette[r][c] = 1 if (r + c) % 2 == 0 else 2
    fixtures.append(("two_color_impostor", reduced_palette))

    checkerboard = [
        [1 + ((r + c) % 9) for c in range(14)]
        for r in range(13)
    ]
    fixtures.append(("axis_ambiguous_checkerboard", checkerboard))

    singleton_band = generate(
        99174,
        0,
        difficulty="medium",
        orientation="vertical",
        grid_h=13,
        grid_w=14,
        band_count=3,
        noise_level="moderate",
    )
    facts = semantic_observables(singleton_band)
    clean = facts["clean"]
    replacement = next(
        color for color in range(1, 10) if color not in {clean[0][0], clean[0][1]}
    )
    for r in range(len(singleton_band)):
        singleton_band[r][1] = replacement
    fixtures.append(("singleton_mode_band", singleton_band))

    excessive_noise = copy.deepcopy(valid)
    clean = rule_mirror(valid)
    changed = 0
    for r in range(len(excessive_noise)):
        for c in range(len(excessive_noise[0])):
            if changed >= round(len(excessive_noise) * len(excessive_noise[0]) * 0.30):
                break
            base = clean[r][c]
            excessive_noise[r][c] = 1 + (base % 9)
            changed += 1
        if changed >= round(len(excessive_noise) * len(excessive_noise[0]) * 0.30):
            break
    fixtures.append(("excessive_noise", excessive_noise))
    return fixtures
