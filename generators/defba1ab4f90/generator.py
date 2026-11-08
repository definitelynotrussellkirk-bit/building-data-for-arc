"""Constructive input sampler for the color-steered red stream task.

A single red marker on the top edge fires downward.  A marker on the left edge
is the transposed case and fires rightward.  Whenever the stream reaches a
horizontal bar in normalized (top-entry) coordinates, blue steers toward its
left hand and green toward its right hand; it slides above that bar, steps past
its end, and continues to the opposite edge.  Transposition mirrors chirality,
so blue's normalized step is +1 for top entry and -1 for left entry.

This module emits inputs only.  ``rule_mirror`` is evidence and testing support;
the selected Racket program remains the label authority.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "defba1ab4f90"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "c58d2da3a0e5"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A non-corner red 2 marker on the top edge fires a stream downward; a "
    "left-edge marker is the transposed rightward case. On each blue 1 or "
    "green 3 bar, the stream slides above the bar and exits just beyond one "
    "end: blue turns to the stream's left hand and green to its right. "
    "Transposition flips chirality. Unhit length-3 bars are inert distractors."
)

INVARIANTS = [
    "exactly one red marker lies non-corner on the top or left edge",
    "after normalizing left entry by transposition, all blue/green obstacles are horizontal bars",
    "the stream reaches the opposite edge without overwriting any source bar",
    "every active scene contains both blue and green steering events",
    "declared distractor bars are disjoint from the intended red path",
]

AXES = {
    "orientation": {
        "type": "str",
        "default": "four-slot top/left lesson schedule",
        "valid": "top|left",
    },
    "flow_length": {
        "type": "int",
        "default": "scheduled canonical lengths 19,22,29",
        "valid": "19..29",
    },
    "lane_width": {
        "type": "int",
        "default": "scheduled canonical widths 12,13",
        "valid": "10..15",
    },
    "n_turns": {
        "type": "int",
        "default": "uniform 4..8",
        "valid": "4..8",
    },
    "n_distractors": {
        "type": "int",
        "default": "uniform 0..6",
        "valid": "0..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "top_canonical_a",
    "left_short",
    "top_canonical_b",
    "left_tall",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_VALID_DIFFICULTIES = tuple(DIFFICULTY_OFFSETS)
_PROFILE_GEOMETRY = {
    "top_canonical_a": ("top", 22, 12),
    "left_short": ("left", 19, 13),
    "top_canonical_b": ("top", 22, 12),
    "left_tall": ("left", 29, 13),
}
_CANONICAL_LATENT_DIMS = {(22, 12), (19, 13), (29, 13)}

DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot teaching role for one sample."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    index = (int(sample_index) + DIFFICULTY_OFFSETS[difficulty]) % LESSON_SCHEDULE_PERIOD
    return SCHEDULE_PROFILES[index]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")


def _scheduled_choice(ctx, label: str, options: Sequence[Any], scheduled: Any):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _spaced_rows(rng, count: int, lo: int, hi: int, gap: int = 2) -> list[int]:
    """Sample sorted rows with a constructive minimum gap."""
    compressed_hi = hi - (gap - 1) * (count - 1)
    population = list(range(lo, compressed_hi + 1))
    if len(population) < count:
        raise ValueError(
            f"cannot place {count} bars in rows {lo}..{hi} with gap {gap}"
        )
    base = sorted(rng.sample(population, count))
    return [value + index * (gap - 1) for index, value in enumerate(base)]


def _color_sequence(rng, count: int) -> list[int]:
    """Always expose green-vs-blue semantics, then vary the remaining turns."""
    colors = [3, 1]
    while len(colors) < count:
        # Avoid long monochrome suffixes without forcing an alternating shortcut.
        if len(colors) >= 2 and colors[-1] == colors[-2]:
            colors.append(1 if colors[-1] == 3 else 3)
        else:
            colors.append(rng.choice((1, 3)))
    return colors[:count]


def _walk_columns(rng, width: int, colors: Sequence[int], blue_step: int) -> list[int]:
    """Find path columns whose signed jumps are 1..3 and whose bars fit."""
    directions = [blue_step if color == 1 else -blue_step for color in colors]

    def search(index: int, current: int, memo: set[tuple[int, int]]):
        if index == len(directions):
            return [current]
        state = (index, current)
        if state in memo:
            return None
        magnitudes = [1, 2, 3]
        rng.shuffle(magnitudes)
        direction = directions[index]
        for magnitude in magnitudes:
            nxt = current + direction * magnitude
            # A right exit needs a 3-cell bar immediately to its left; a left
            # exit needs the bar immediately to its right.
            if direction > 0:
                fits = 3 <= nxt <= width - 1
            else:
                fits = 0 <= nxt <= width - 4
            if not fits:
                continue
            suffix = search(index + 1, nxt, memo)
            if suffix is not None:
                return [current] + suffix
        memo.add(state)
        return None

    starts = list(range(1, width - 1))
    rng.shuffle(starts)
    for start in starts:
        result = search(0, start, set())
        if result is not None:
            return result
    raise ValueError("no lawful stream walk exists for the selected color sequence")


def _active_bar_start(previous_col: int, next_col: int) -> int:
    if next_col > previous_col:
        return next_col - 3
    return next_col + 1


def _trace_latent(
    latent: list[list[int]],
    blue_step: int,
    *,
    ignore_color: bool = False,
) -> tuple[set[tuple[int, int]], list[dict[str, int]]]:
    markers = [
        (r, c)
        for r, row in enumerate(latent)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(markers) != 1:
        raise ValueError(f"expected one red marker, found {len(markers)}")
    h, w = len(latent), len(latent[0])
    r, c = markers[0]
    if r != 0:
        raise ValueError("normalized marker is not on the top edge")
    cells = {(r, c)}
    turns: list[dict[str, int]] = []
    budget = h * w * 4
    while r < h - 1:
        budget -= 1
        if budget <= 0:
            raise ValueError("stream trace exceeded finite budget")
        below = latent[r + 1][c]
        if below == 0:
            r += 1
            cells.add((r, c))
            continue
        if below not in (1, 3):
            raise ValueError(f"stream hit unsupported color {below}")
        obstacle_color = below
        step = blue_step if (ignore_color or obstacle_color == 1) else -blue_step
        start_col = c
        cc = c + step
        while True:
            if not 0 <= cc < w:
                raise ValueError("stream was steered off the lane")
            cells.add((r, cc))
            if latent[r + 1][cc] == 0:
                cells.add((r + 1, cc))
                turns.append(
                    {
                        "bar_row": r + 1,
                        "color": obstacle_color,
                        "from_col": start_col,
                        "to_col": cc,
                        "step": step,
                    }
                )
                r += 1
                c = cc
                break
            cc += step
    return cells, turns


def _place_distractors(
    grid: list[list[int]],
    path: set[tuple[int, int]],
    active_rows: set[int],
    count: int,
    row_rng,
    bar_rng,
) -> None:
    h, w = len(grid), len(grid[0])
    candidates: list[tuple[int, list[int]]] = []
    for row in range(1, h - 1):
        if row in active_rows:
            continue
        starts = [
            start
            for start in range(0, w - 2)
            if all((row, col) not in path for col in range(start, start + 3))
        ]
        if starts:
            candidates.append((row, starts))
    if len(candidates) < count:
        raise ValueError(
            f"only {len(candidates)} path-disjoint distractor rows for requested {count}"
        )
    chosen_rows = row_rng.sample(candidates, count)
    for row, starts in chosen_rows:
        start = bar_rng.choice(starts)
        color = bar_rng.choice((1, 3))
        for col in range(start, start + 3):
            grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, exact-override stream input."""
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_orientation, scheduled_length, scheduled_width = _PROFILE_GEOMETRY[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    orientation = str(
        _scheduled_choice(ctx, "orientation", ("top", "left"), scheduled_orientation)
    )
    flow_length = _scheduled_int(ctx, "flow_length", 19, 29, scheduled_length)
    lane_width = _scheduled_int(ctx, "lane_width", 10, 15, scheduled_width)
    n_turns = ctx.draw_int_strict("n_turns", 4, 8)
    n_distractors = ctx.draw_int_strict("n_distractors", 0, 6)

    blue_step = 1 if orientation == "top" else -1
    rows = _spaced_rows(
        ctx.draw_rng("active_rows"), n_turns, 2, flow_length - 2, gap=2
    )
    colors = _color_sequence(ctx.draw_rng("active_colors"), n_turns)
    try:
        columns = _walk_columns(
            ctx.draw_rng("stream_walk"), lane_width, colors, blue_step
        )
    except ValueError:
        # A random suffix can ask for too many same-direction turns in a narrow
        # lane.  Alternation is a constructive fallback, not a shortened draw.
        colors = [3 if index % 2 == 0 else 1 for index in range(n_turns)]
        columns = _walk_columns(
            ctx.draw_rng("stream_walk_fallback"), lane_width, colors, blue_step
        )

    latent = full_grid(flow_length, lane_width, 0)
    latent[0][columns[0]] = 2
    for index, row in enumerate(rows):
        start = _active_bar_start(columns[index], columns[index + 1])
        for col in range(start, start + 3):
            latent[row][col] = colors[index]

    path, turns = _trace_latent(latent, blue_step)
    if len(turns) != n_turns:
        raise RuntimeError(
            f"constructive active bars yielded {len(turns)} turns, expected {n_turns}"
        )
    _place_distractors(
        latent,
        path,
        set(rows),
        n_distractors,
        ctx.draw_rng("distractor_rows"),
        ctx.draw_rng("distractor_bars"),
    )
    final_path, final_turns = _trace_latent(latent, blue_step)
    if final_path != path or len(final_turns) != n_turns:
        raise RuntimeError("a distractor altered the intended stream")
    return _transpose(latent) if orientation == "left" else latent


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return len(grid), 0, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or value not in {0, 1, 2, 3}:
                errors.append(
                    f"cell ({r},{c}) must be a literal color in {{0,1,2,3}}, got {value!r}"
                )
                return len(grid), width, errors
    return len(grid), width, errors


def _normalize(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    height, width, errors = _validate_grid(grid)
    if errors:
        return None, errors
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(markers) != 1:
        return None, [f"expected exactly one red marker, found {len(markers)}"]
    r, c = markers[0]
    if r == 0 and 0 < c < width - 1:
        return {
            "orientation": "top",
            "latent": deepcopy(grid),
            "blue_step": 1,
        }, []
    if c == 0 and 0 < r < height - 1:
        return {
            "orientation": "left",
            "latent": _transpose(grid),
            "blue_step": -1,
        }, []
    return None, ["red marker must be non-corner on the top or left edge"]


def _bar_runs(latent: list[list[int]]) -> tuple[list[dict[str, int]], list[str]]:
    runs: list[dict[str, int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(latent):
        col = 0
        while col < len(row):
            if row[col] not in (1, 3):
                col += 1
                continue
            start = col
            values = []
            while col < len(row) and row[col] in (1, 3):
                values.append(row[col])
                col += 1
            end = col - 1
            if len(set(values)) != 1:
                errors.append(
                    f"bar run at row {row_index}, cols {start}..{end} mixes colors"
                )
            length = end - start + 1
            if length not in (2, 3):
                errors.append(
                    f"bar run at row {row_index}, cols {start}..{end} has length {length}, expected 3 or edge-clipped 2"
                )
            if length == 2 and start != 0 and end != len(row) - 1:
                errors.append(
                    f"length-2 bar at row {row_index} is not clipped by an edge"
                )
            runs.append(
                {
                    "row": row_index,
                    "start": start,
                    "end": end,
                    "color": values[0],
                }
            )
    return runs, errors


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    normalized, errors = _normalize(grid)
    if errors or normalized is None:
        return None, errors
    latent = normalized["latent"]
    h, w = len(latent), len(latent[0])
    if h < 8 or w < 7:
        errors.append(f"normalized grid {h}x{w} is too small for a multi-turn stream")
    palette = {value for row in latent for value in row}
    if palette != {0, 1, 2, 3}:
        errors.append(f"expected exact palette {{0,1,2,3}}, found {sorted(palette)}")
    if any(value in (1, 3) for value in latent[0]):
        errors.append("top marker row may not contain source bars")
    runs, run_errors = _bar_runs(latent)
    errors.extend(run_errors)
    try:
        path, turns = _trace_latent(latent, normalized["blue_step"])
    except Exception as exc:
        errors.append(f"stream trace failed: {exc}")
        return None, errors
    overwritten = [
        (r, c, latent[r][c])
        for r, c in path
        if latent[r][c] != 0 and latent[r][c] != 2
    ]
    if overwritten:
        errors.append(
            f"stream path crosses source bars at {overwritten[:4]}"
        )
    if not 4 <= len(turns) <= 8:
        errors.append(f"active turn count must be 4..8, found {len(turns)}")
    active_colors = {turn["color"] for turn in turns}
    if active_colors != {1, 3}:
        errors.append(
            f"active steering must expose both blue and green, found {sorted(active_colors)}"
        )
    if len(runs) < len(turns):
        errors.append("fewer bar runs than active turns")
    info = {
        **normalized,
        "flow_length": h,
        "lane_width": w,
        "path": path,
        "turns": turns,
        "runs": runs,
        "n_turns": len(turns),
        "n_distractors": len(runs) - len(turns),
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical and generated lawful stream scenes; fail closed."""
    del difficulty, meta
    _info, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical-size/palette grammar used by the strict semantic census."""
    info, errors = _analyze(grid)
    if errors or info is None:
        return errors
    dims = (info["flow_length"], info["lane_width"])
    if dims not in _CANONICAL_LATENT_DIMS:
        errors.append(
            f"normalized dimensions {dims} are outside canonical profiles {sorted(_CANONICAL_LATENT_DIMS)}"
        )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control solely from returned pixels."""
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError(f"cannot observe invalid grid: {errors[:2]}")
    return {
        "orientation": info["orientation"],
        "flow_length": info["flow_length"],
        "lane_width": info["lane_width"],
        "n_turns": info["n_turns"],
        "n_distractors": info["n_distractors"],
    }


def _paint_with_policy(
    grid,
    *,
    ignore_color: bool = False,
    flip_left: bool = True,
):
    normalized, errors = _normalize(grid)
    if errors or normalized is None:
        raise ValueError(errors[0] if errors else "invalid grid")
    latent = normalized["latent"]
    blue_step = normalized["blue_step"]
    if normalized["orientation"] == "left" and not flip_left:
        blue_step = 1
    path, _turns = _trace_latent(latent, blue_step, ignore_color=ignore_color)
    out = deepcopy(latent)
    for r, c in path:
        out[r][c] = 2
    return _transpose(out) if normalized["orientation"] == "left" else out


def rule_mirror(grid):
    """Input-pure Python mirror for tests; Racket remains the authority."""
    return _paint_with_policy(grid)


def _safe_rival(grid, **policy):
    try:
        return _paint_with_policy(grid, **policy)
    except Exception:
        return deepcopy(grid)


def _ignore_bar_color(grid):
    return _safe_rival(grid, ignore_color=True)


def _no_left_chirality_flip(grid):
    return _safe_rival(grid, flip_left=False)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "ignore_bar_color": _ignore_bar_color,
    "no_left_chirality_flip": _no_left_chirality_flip,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def _green_steers_opposite(grid) -> bool:
    info, errors = _analyze(grid)
    return not errors and info is not None and _ignore_bar_color(grid) != rule_mirror(grid)


def _left_entry_flips_chirality(grid) -> bool:
    info, errors = _analyze(grid)
    return (
        not errors
        and info is not None
        and info["orientation"] == "left"
        and _no_left_chirality_flip(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "green_steers_opposite": _green_steers_opposite,
    "left_entry_flips_chirality": _left_entry_flips_chirality,
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "green_steers_opposite": ["ignore_bar_color"],
    "left_entry_flips_chirality": ["no_left_chirality_flip"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively refute every declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    reasons = [f"query input is invalid: {query_errors[0]}"] if query_errors else []
    refuted = {name: False for name in LESSON_COMPETITORS}
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
            reasons.append(f"demo {index} output does not match the stream rule")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True
    for name, hit in refuted.items():
        if not hit:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
