"""Generator for ARC task 22425bda (task 00af0f134576) — hidden-line depth.

The selected Racket rule is ``(line-z-order g 7)``.  For every non-background
color it infers the strongest full horizontal, vertical, main-diagonal, or
anti-diagonal line, counts how many cells of that full line are hidden by
other colors, and sorts by ``(hidden_count, color)`` descending.  In the
canonical puzzles that hidden-cell count is the visible z-depth signal; when
two lines have the same hidden count the larger color is deliberately first.

Ordinary generation stays on that exact grammar.  It paints 2..6 distinct
full lines on background 7, including diagonal and parallel-line schedules,
and rejects layouts where a color no longer identifies its intended line.
A four-slot schedule guarantees every four-demo lesson contains: a pure
crossing that defeats color-only sorting, a diagonal case that defeats a
visible-cell-count shortcut, a tied-depth case that exposes the canonical
color-descending tie break, and a 5/6-line case that defeats fixed-length
answers.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00af0f134576"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "04cf01eb1b78"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "bg=7; infer each colored full H/V/main-diagonal/anti-diagonal line, count "
    "the cells hidden by other colored lines, then emit the colors as one row "
    "sorted by (hidden-cell count, color value) descending. Ordinary lessons "
    "schedule crossings, diagonals, equal-depth tie breaks, and 5/6-line piles."
)

INVARIANTS = [
    "background is color 7 and the input is a square canonical-scale grid",
    "2..6 distinct non-7 colors each lie on one inferable full H/V/diagonal line",
    "every missing cell of an inferred line is occupied by another line color, never background",
    "at least one line is genuinely obscured, so the transform is not an identity/no-overlap case",
    "output order is hidden-cell count descending, then color value descending for exact ties",
]

PALETTE = (0, 1, 2, 3, 4, 5, 6, 8, 9)
LINE_KINDS = ("h", "v", "d", "a")
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 1.0

# Every declared axis is exact, boundary-valid in every difficulty band, and
# recoverable from the returned grid via observe_overrides().  Difficulty only
# changes the scheduled ordinary defaults; explicit overrides always use the
# full declared domain.
AXES = {
    "grid_size": {
        "type": "int",
        "default": "four-slot canonical-profile schedule",
        "valid": "7..16",
        "doc": "Square side length.",
    },
    "n_lines": {
        "type": "int",
        "default": "2, 3, 4, then 5/6 by schedule and band",
        "valid": "2..6",
        "doc": "Number of distinct colored full lines / output colors.",
    },
    "diagonal_count": {
        "type": "int",
        "default": "scheduled 0..2",
        "valid": "0..2",
        "doc": "Number of inferred main/anti-diagonal line colors.",
    },
}

# All boundary combinations of the three axes are intentionally supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


@dataclass(frozen=True)
class _LineInfo:
    color: int
    kind: str
    key: int
    shown: int
    expected: int
    obscured: int
    positions: frozenset[tuple[int, int]]
    expected_positions: frozenset[tuple[int, int]]


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Expose the four-slot lesson schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % 4


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (int(scheduled),)))


def _scheduled_defaults(profile: int, difficulty: str | None) -> tuple[int, int, int]:
    # First three slots reproduce the canonical size/palette envelopes exactly:
    # 7x7/2 lines, 10x10/3 lines, 12x12/4 lines.  Slot 3 covers the canonical
    # 16x16 deep piles, with hard explicitly reaching six output colors.
    if profile == 0:
        return (7, 2, 0)
    if profile == 1:
        return (10, 3, 1)
    if profile == 2:
        return (12, 4, 1)
    if difficulty == "hard":
        return (16, 6, 2)
    if difficulty == "medium":
        return (16, 5, 2)
    return (16, 5, 0)


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}")


def _cells_for(kind: str, key: int, size: int) -> frozenset[tuple[int, int]]:
    if kind == "h":
        return frozenset((key, c) for c in range(size))
    if kind == "v":
        return frozenset((r, key) for r in range(size))
    if kind == "d":
        return frozenset((r, c) for r in range(size) for c in range(size) if r - c == key)
    if kind == "a":
        return frozenset((r, c) for r in range(size) for c in range(size) if r + c == key)
    raise ValueError(f"unknown line kind {kind!r}")


def _infer_one_line(grid: list[list[int]], color: int) -> _LineInfo:
    h, w = len(grid), len(grid[0])
    positions = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
    if not positions:
        raise ValueError(f"color {color} is absent")

    row_c = Counter(r for r, _ in positions)
    col_c = Counter(c for _, c in positions)
    diag_c = Counter(r - c for r, c in positions)
    anti_c = Counter(r + c for r, c in positions)
    max_r = max(row_c.values())
    max_c = max(col_c.values())
    max_d = max(diag_c.values())
    max_a = max(anti_c.values())
    peak = max(max_r, max_c, max_d, max_a)

    # Match the Racket primitive's orientation precedence exactly: row, column,
    # main diagonal, anti-diagonal.  For lawful scenes the winning key is unique.
    if peak == max_r:
        kind = "h"
        key = min(k for k, v in row_c.items() if v == max_r)
        expected_positions = frozenset((key, c) for c in range(w))
    elif peak == max_c:
        kind = "v"
        key = min(k for k, v in col_c.items() if v == max_c)
        expected_positions = frozenset((r, key) for r in range(h))
    elif peak == max_d:
        kind = "d"
        key = min(k for k, v in diag_c.items() if v == max_d)
        expected_positions = frozenset(
            (r, c) for r in range(h) for c in range(w) if r - c == key
        )
    else:
        kind = "a"
        key = min(k for k, v in anti_c.items() if v == max_a)
        expected_positions = frozenset(
            (r, c) for r in range(h) for c in range(w) if r + c == key
        )

    shown_positions = frozenset(positions)
    expected = len(expected_positions)
    shown = len(shown_positions)
    return _LineInfo(
        color=color,
        kind=kind,
        key=key,
        shown=shown,
        expected=expected,
        obscured=expected - shown,
        positions=shown_positions,
        expected_positions=expected_positions,
    )


def _line_analysis(grid: list[list[int]]) -> list[_LineInfo]:
    colors = sorted({value for row in grid for value in row if value != 7})
    return [_infer_one_line(grid, color) for color in colors]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror of ``line-z-order`` for tests/adversarial probes.

    The Racket program remains the sole training-output authority; this mirror
    exists only to make semantic witnesses and focused tests inspectable.
    """
    infos = _line_analysis(grid)
    return [[info.color for info in sorted(infos, key=lambda x: (x.obscured, x.color), reverse=True)]]


def _orientation_plan(n_lines: int, diagonal_count: int, rng) -> list[str]:
    kinds: list[str] = []
    if diagonal_count == 1:
        kinds.append(rng.choice(("d", "a")))
    elif diagonal_count == 2:
        kinds.extend(("d", "a"))

    remaining = n_lines - diagonal_count
    if remaining == 1:
        kinds.append(rng.choice(("h", "v")))
    elif remaining >= 2:
        # Guarantee both orthogonal families whenever possible; extras become
        # lawful parallel lines, which are essential for canonical depth ties.
        kinds.extend(("h", "v"))
        for i in range(remaining - 2):
            kinds.append("h" if i % 2 == 0 else "v")
    rng.shuffle(kinds)
    return kinds


def _line_specs(size: int, kinds: list[str], rng) -> list[tuple[str, int]]:
    counts = Counter(kinds)
    specs: list[tuple[str, int]] = []
    if counts["h"]:
        rows = rng.sample(range(1, size - 1), counts["h"])
        specs.extend(("h", row) for row in rows)
    if counts["v"]:
        cols = rng.sample(range(1, size - 1), counts["v"])
        specs.extend(("v", col) for col in cols)
    if counts["d"]:
        # |offset| <= size-4 guarantees at least four visible candidate cells
        # before crossings, avoiding one-pixel orientation ambiguity.
        offsets = list(range(-(size - 4), size - 3))
        specs.extend(("d", d) for d in rng.sample(offsets, counts["d"]))
    if counts["a"]:
        sums = list(range(3, 2 * size - 4))
        specs.extend(("a", a) for a in rng.sample(sums, counts["a"]))
    rng.shuffle(specs)
    return specs


def _semantic_shape_ok(grid: list[list[int]], profile: int) -> bool:
    """Apply schedule-only teaching constraints; overrides bypass this layer."""
    actual = rule_mirror(grid)
    if profile == 0:
        # With two crossing H/V lines, require the hidden-depth answer to differ
        # from a bare descending-color list.
        return actual != _color_desc_rival(grid)
    if profile == 1:
        # A shortened diagonal must make 'fewest visible cells first' wrong.
        return _has_diagonal(grid) and actual != _visible_count_rival(grid)
    if profile == 2:
        return _has_tie_break_witness(grid)
    # Deep-pile slot: output length itself must refute a fixed-two shortcut.
    return len(actual[0]) >= 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_size, default_lines, default_diags = _scheduled_defaults(profile, difficulty)
    size = _draw_exact_int(ctx, "grid_size", 7, 16, default_size)
    n_lines = _draw_exact_int(ctx, "n_lines", 2, 6, default_lines)
    diagonal_count = _draw_exact_int(ctx, "diagonal_count", 0, 2, default_diags)
    rng = ctx.draw_rng("layout")

    # Overrides may request any declared boundary combination.  Ordinary draws
    # additionally satisfy the four-slot teaching schedule.  Rejection is over
    # deterministic keyed RNG state, so replay remains exact.
    ordinary = not any(k in overrides and overrides[k] is not None for k in AXES)
    for _attempt in range(512):
        kinds = _orientation_plan(n_lines, diagonal_count, rng)
        specs = _line_specs(size, kinds, rng)
        colors = rng.sample(PALETTE, n_lines)
        painted = list(zip(specs, colors))
        rng.shuffle(painted)

        grid = full_grid(size, size, 7)
        intended: dict[int, tuple[str, int]] = {}
        for (kind, key), color in painted:
            intended[color] = (kind, key)
            for r, c in _cells_for(kind, key, size):
                grid[r][c] = color

        errors = self_check(grid)
        if errors:
            continue
        infos = _line_analysis(grid)
        if len(infos) != n_lines:
            continue
        if any((info.kind, info.key) != intended[info.color] for info in infos):
            continue
        observed = observe_overrides(grid)
        if observed != {
            "grid_size": size,
            "n_lines": n_lines,
            "diagonal_count": diagonal_count,
        }:
            continue
        if ordinary and not _semantic_shape_ok(grid, profile):
            continue
        return grid

    raise ValueError(
        "unable to realize a structurally identifiable line layout for "
        f"grid_size={size}, n_lines={n_lines}, diagonal_count={diagonal_count}"
    )


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from one returned grid."""
    infos = _line_analysis(grid)
    return {
        "grid_size": len(grid),
        "n_lines": len(infos),
        "diagonal_count": sum(info.kind in {"d", "a"} for info in infos),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible hidden-full-line input grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]

    errors: list[str] = []
    if h != w:
        errors.append(f"canonical line-z-order family is square, got {h}x{w}")
    if not (7 <= h <= 16):
        errors.append(f"expected canonical-scale side length 7..16, got {h}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    colors = sorted({value for row in grid for value in row if value != 7})
    if not (2 <= len(colors) <= 6):
        errors.append(f"expected 2..6 non-background line colors, got {len(colors)}")
    if 7 not in {value for row in grid for value in row}:
        errors.append("background color 7 must remain visible")
    if errors:
        return errors

    try:
        infos = _line_analysis(grid)
    except Exception as exc:
        return [f"line analysis failed: {type(exc).__name__}: {exc}"]

    obscured_total = 0
    kinds: set[str] = set()
    for info in infos:
        kinds.add(info.kind)
        if info.shown < 2:
            errors.append(f"color {info.color} has only {info.shown} visible cell(s); line orientation is ambiguous")
        if info.expected < 4:
            errors.append(f"color {info.color} infers a too-short {info.kind} line of length {info.expected}")
        off_line = sorted(info.positions - info.expected_positions)
        if off_line:
            errors.append(f"color {info.color} has cells off its inferred {info.kind} line: {off_line[:3]}")
        if info.obscured < 0:
            errors.append(f"color {info.color} has more shown cells than its inferred full line")
            continue
        missing = info.expected_positions - info.positions
        obscured_total += len(missing)
        bg_holes = [(r, c) for r, c in missing if grid[r][c] == 7]
        if bg_holes:
            errors.append(
                f"color {info.color} has {len(bg_holes)} unfilled hole(s) in its inferred line, e.g. {bg_holes[:3]}"
            )
        # A hidden cell must be explained by another inferred line crossing it,
        # not by an arbitrary stray colored pixel.
        other_expected = {
            pos
            for other in infos
            if other.color != info.color
            for pos in other.expected_positions
        }
        unexplained = sorted(pos for pos in missing if pos not in other_expected)
        if unexplained:
            errors.append(
                f"color {info.color} has hidden cells not explained by another line: {unexplained[:3]}"
            )

    if len(kinds) < 2:
        errors.append("all colors infer the same line family; no crossing relation is visible")
    if obscured_total == 0:
        errors.append("no line is obscured; hidden-depth ordering is not demonstrated")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _scores(grid: list[list[int]]) -> list[_LineInfo]:
    return _line_analysis(grid)


def _has_diagonal(grid: list[list[int]]) -> bool:
    return any(info.kind in {"d", "a"} for info in _scores(grid))


def _has_tie_break_witness(grid: list[list[int]]) -> bool:
    infos = _scores(grid)
    by_score: dict[int, list[int]] = {}
    for info in infos:
        by_score.setdefault(info.obscured, []).append(info.color)
    return any(len(colors) >= 2 for colors in by_score.values()) and rule_mirror(grid) != _tie_color_asc_rival(grid)


def _has_visible_count_counterexample(grid: list[list[int]]) -> bool:
    return _has_diagonal(grid) and rule_mirror(grid) != _visible_count_rival(grid)


def _has_depth_not_color_counterexample(grid: list[list[int]]) -> bool:
    return rule_mirror(grid) != _color_desc_rival(grid)


def _has_deep_pile(grid: list[list[int]]) -> bool:
    return len(_scores(grid)) >= 5


def _color_desc_rival(grid: list[list[int]]) -> list[list[int]]:
    colors = sorted((info.color for info in _scores(grid)), reverse=True)
    return [colors]


def _tie_color_asc_rival(grid: list[list[int]]) -> list[list[int]]:
    infos = sorted(_scores(grid), key=lambda x: (-x.obscured, x.color))
    return [[info.color for info in infos]]


def _visible_count_rival(grid: list[list[int]]) -> list[list[int]]:
    # Wrong shortcut: assumes every line has the same full length, so the one
    # with fewer currently visible cells must be deeper.
    infos = sorted(_scores(grid), key=lambda x: (x.shown, -x.color))
    return [[info.color for info in infos]]


def _ignore_diagonal_rival(grid: list[list[int]]) -> list[list[int]]:
    return [[
        info.color
        for info in sorted(_scores(grid), key=lambda x: (x.obscured, x.color), reverse=True)
        if info.kind in {"h", "v"}
    ]]


def _fixed_two_rival(grid: list[list[int]]) -> list[list[int]]:
    return [rule_mirror(grid)[0][:2]]


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "depth_not_color_desc": _has_depth_not_color_counterexample,
    "diagonal_line_included": _has_diagonal,
    "diagonal_refutes_visible_count": _has_visible_count_counterexample,
    "equal_depth_color_tiebreak": _has_tie_break_witness,
    "five_or_six_line_pile": _has_deep_pile,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "color_desc_only": _color_desc_rival,
    "tie_uses_color_ascending": _tie_color_asc_rival,
    "visible_count_only": _visible_count_rival,
    "ignore_diagonals": _ignore_diagonal_rival,
    "fixed_two_outputs": _fixed_two_rival,
}

WITNESS_RIVALS = {
    "depth_not_color_desc": ["color_desc_only"],
    "diagonal_line_included": ["ignore_diagonals"],
    "diagonal_refutes_visible_count": ["visible_count_only"],
    "equal_depth_color_tiebreak": ["tie_uses_color_ascending"],
    "five_or_six_line_pile": ["fixed_two_outputs"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} mirror failed: {type(exc).__name__}: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with hidden-line depth ordering")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(demo["input"]) == demo["output"] for demo in demos)
            differs_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and differs_query:
            reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
