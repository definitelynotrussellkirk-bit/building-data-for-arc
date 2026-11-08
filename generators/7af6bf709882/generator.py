"""Generator for ARC task 7af6bf709882 (cad67732).

The input is a finite window onto a colored motif repeated by one translation
``(period_r, period_c)``.  The canonical rule enumerates positive-row shifts
lexicographically, chooses the *first* shift whose in-bounds nonzero cells all
land on equal colors, and continues that translation through a doubled canvas.
Negative column periods are anchored in the right half of the output.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7af6bf709882"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4e87f3f4ed54"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Find the first positive-row translation that preserves every in-bounds "
    "nonzero cell, then extrapolate the colored strip by that translation in "
    "a 2h x 2w canvas; negative column periods are anchored on the right."
)
INVARIANTS = [
    "the returned grid has a first valid period with 2 <= period_r <= 5",
    "at least three complete motif copies witness the selected translation",
    "the selected translation, not a visual bounding-box shortcut, determines the output",
    "the Racket rule is the sole output authority",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-scale and generalized profiles",
        "valid": "5..15",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-scale and generalized profiles",
        "valid": "5..15",
    },
    "period_r": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "2..5",
    },
    "period_c": {
        "type": "int",
        "default": "scheduled negative, zero, and positive drift",
        "valid": "-4..4",
    },
    "motif_size": {
        "type": "int",
        "default": "scheduled 2..9 source-chain cells",
        "valid": "2..9",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 2..4 nonzero colors",
        "valid": "2..4",
    },
}

# The first four are deliberate: every materialized 3-demo lesson shows
# positive, negative, and zero horizontal period branches before its query.
_SCHEDULED_PROFILES = (
    (6, 6, 2, 2, 4, 4),
    (8, 8, 2, -2, 2, 2),
    (5, 5, 2, 0, 2, 2),
    (10, 10, 3, 3, 6, 3),
    (10, 10, 2, -2, 6, 3),
    (9, 9, 3, 0, 3, 3),
    (11, 12, 3, -3, 7, 4),
    (12, 10, 4, 0, 8, 4),
    (13, 15, 4, 4, 8, 4),
    (14, 15, 5, -4, 9, 4),
    (15, 15, 5, 4, 9, 4),
    (12, 14, 2, 1, 5, 2),
)
_AXIS_NAMES = tuple(AXES)
_AXIS_BOUNDS = {
    "grid_h": (5, 15),
    "grid_w": (5, 15),
    "period_r": (2, 5),
    "period_c": (-4, 4),
    "motif_size": (2, 9),
    "palette_size": (2, 4),
}


def _shape_options(h: int, w: int, pr: int, pc: int, motif_size: int):
    """Return motif rectangles that permit at least three full copies."""
    options = []
    max_mh = min(pr, h - 2 * pr)
    if max_mh < 1:
        return options
    horizontal_span = w - 2 * abs(pc)
    if horizontal_span < 1:
        return options
    for mh in range(1, max_mh + 1):
        for mw in range(1, horizontal_span + 1):
            if mh * mw < motif_size:
                continue
            vertical_copies = 1 + (h - mh) // pr
            horizontal_copies = (
                vertical_copies
                if pc == 0
                else 1 + (w - mw) // abs(pc)
            )
            copies = min(vertical_copies, horizontal_copies)
            if copies >= 3:
                options.append((mh, mw, copies))
    return options


def _profile_feasible(profile: tuple[int, int, int, int, int, int]) -> bool:
    h, w, pr, pc, motif_size, palette_size = profile
    return (
        palette_size <= motif_size
        and bool(_shape_options(h, w, pr, pc, motif_size))
    )


for _profile in _SCHEDULED_PROFILES:
    if not _profile_feasible(_profile):  # import-time contract, never silent
        raise RuntimeError(f"infeasible scheduled profile: {_profile}")


@lru_cache(maxsize=512)
def _matching_profiles(fixed_items: tuple[tuple[str, int], ...]):
    """Enumerate feasible axis tuples satisfying explicit overrides."""
    fixed = dict(fixed_items)
    domains: dict[str, Iterable[int]] = {
        name: (fixed[name],) if name in fixed else range(lo, hi + 1)
        for name, (lo, hi) in _AXIS_BOUNDS.items()
    }
    matches = []
    for h in domains["grid_h"]:
        for w in domains["grid_w"]:
            for pr in domains["period_r"]:
                for pc in domains["period_c"]:
                    for motif_size in domains["motif_size"]:
                        for palette_size in domains["palette_size"]:
                            profile = (h, w, pr, pc, motif_size, palette_size)
                            if _profile_feasible(profile):
                                matches.append(profile)
    return tuple(matches)


def _clean_overrides(overrides: dict[str, Any]) -> dict[str, int]:
    cleaned = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(cleaned) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    normalized: dict[str, int] = {}
    for name, value in cleaned.items():
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} override must be an integer") from exc
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
        normalized[name] = value
    return normalized


def _choose_profile(ctx, sample_index: int, overrides: dict[str, int]):
    if not overrides:
        # Band offsets keep equal-sized censuses from aligning on the same
        # profile while preserving the first four lesson profiles at difficulty=None.
        band_offset = {"easy": 0, "medium": 4, "hard": 8}.get(ctx.difficulty, 0)
        profile = _SCHEDULED_PROFILES[
            (sample_index + band_offset) % len(_SCHEDULED_PROFILES)
        ]
    else:
        fixed = tuple(sorted(overrides.items()))
        matches = _matching_profiles(fixed)
        if not matches:
            raise ValueError(
                "incompatible override combination: "
                + ", ".join(f"{key}={value}" for key, value in fixed)
            )
        profile = matches[ctx.draw_rng("axis_profile").randrange(len(matches))]

    values = dict(zip(_AXIS_NAMES, profile))
    realized = {}
    for name in _AXIS_NAMES:
        lo, hi = _AXIS_BOUNDS[name]
        if name in overrides:
            realized[name] = ctx.draw_int(name, lo, hi)
        else:
            # A singleton keyed choice records exact provenance without
            # pretending an independently sampled value survived constraints.
            realized[name] = ctx.draw_choice(name, (values[name],))
    return realized


def _valid_periods(grid: list[list[int]]):
    """Mirror the canonical rule's lexicographic check-shift enumeration."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    cells = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    out = []
    for dr in range(1, h):
        for dc in range(1 - w, w):
            overlap = [
                (r, c, value)
                for r, c, value in cells
                if 0 <= r + dr < h and 0 <= c + dc < w
            ]
            if overlap and all(
                grid[r + dr][c + dc] == value
                for r, c, value in overlap
            ):
                out.append((dr, dc, len(overlap)))
    return out


def _analyze(grid: list[list[int]]):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty list of rows")
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    h = len(grid)
    cells = {
        (r, c): grid[r][c]
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    periods = _valid_periods(grid)
    if not periods:
        raise ValueError("no valid positive-row translation")
    pr, pc, overlap = periods[0]
    bases = []
    chain_lengths = []
    for (r, c), value in cells.items():
        predecessor = (r - pr, c - pc)
        if cells.get(predecessor) == value:
            continue
        bases.append((r, c, value))
        length = 0
        rr, cc = r, c
        while cells.get((rr, cc)) == value:
            length += 1
            rr += pr
            cc += pc
        chain_lengths.append(length)
    return {
        "grid_h": h,
        "grid_w": w,
        "period_r": pr,
        "period_c": pc,
        "motif_size": len(bases),
        "palette_size": len(set(cells.values())),
        "nonzero": len(cells),
        "overlap": overlap,
        "support_fraction": overlap / len(cells) if cells else 0.0,
        "base_fraction": len(bases) / len(cells) if cells else 1.0,
        "periods": periods,
        "bases": bases,
        "chain_lengths": chain_lengths,
    }


def _solve_with_period(grid: list[list[int]], period: tuple[int, int]):
    """Python test mirror for one chosen period; Racket remains authority."""
    h, w = len(grid), len(grid[0])
    oh, ow = 2 * h, 2 * w
    pr, pc = period
    c_offset = 0 if pc >= 0 else w
    output = full_grid(oh, ow, 0)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for k in range(oh + ow):
                nr = r + k * pr
                nc = c + c_offset + k * pc
                if 0 <= nr < oh and 0 <= nc < ow:
                    output[nr][nc] = value
    return output


def rule_mirror(grid: list[list[int]]):
    analysis = _analyze(grid)
    return _solve_with_period(
        grid, (analysis["period_r"], analysis["period_c"])
    )


def _build_grid(ctx, axes: dict[str, int]):
    h = axes["grid_h"]
    w = axes["grid_w"]
    pr = axes["period_r"]
    pc = axes["period_c"]
    motif_size = axes["motif_size"]
    palette_size = axes["palette_size"]
    options = _shape_options(h, w, pr, pc, motif_size)
    if not options:
        raise ValueError(f"incompatible realized axes: {axes}")

    rng = ctx.draw_rng("motif_layout_colors_and_anchor")
    for _attempt in range(512):
        mh, mw, max_copies = options[rng.randrange(len(options))]
        copies = rng.randint(3, max_copies)
        r0 = h - mh - (copies - 1) * pr  # final copy is flush to bottom
        if pc >= 0:
            c_lo, c_hi = 0, w - mw - (copies - 1) * pc
        else:
            c_lo, c_hi = (copies - 1) * (-pc), w - mw
        if c_lo > c_hi:
            continue
        c0 = rng.randint(c_lo, c_hi)

        positions = [(r, c) for r in range(mh) for c in range(mw)]
        rng.shuffle(positions)
        positions = sorted(positions[:motif_size])
        colors = list(range(1, 10))
        rng.shuffle(colors)
        palette = colors[:palette_size]
        assignments = palette[:]
        assignments.extend(
            palette[rng.randrange(palette_size)]
            for _ in range(motif_size - palette_size)
        )
        rng.shuffle(assignments)
        motif = [
            (r, c, assignments[index])
            for index, (r, c) in enumerate(positions)
        ]

        grid = full_grid(h, w, 0)
        for copy_index in range(copies):
            br = r0 + copy_index * pr
            bc = c0 + copy_index * pc
            for dr, dc, value in motif:
                grid[br + dr][bc + dc] = value

        try:
            analysis = _analyze(grid)
        except ValueError:
            continue
        periods_follow_same_lattice = all(
            dr % pr == 0 and dc == (dr // pr) * pc
            for dr, dc, _ in analysis["periods"]
        )
        if (
            (analysis["period_r"], analysis["period_c"]) == (pr, pc)
            and analysis["motif_size"] == motif_size
            and analysis["palette_size"] == palette_size
            and analysis["support_fraction"] >= 0.5
            and periods_follow_same_lattice
        ):
            return grid
    raise ValueError(
        "could not realize an unambiguous first-period scene for axes "
        f"{axes}; choose a compatible override combination"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    cleaned = _clean_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=cleaned,
    )
    axes = _choose_profile(ctx, sample_index, cleaned)
    return _build_grid(ctx, axes)


def observe_overrides(grid):
    analysis = _analyze(grid)
    return {name: analysis[name] for name in _AXIS_NAMES}


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    h, w = analysis["grid_h"], analysis["grid_w"]
    if not 5 <= h <= 15 or not 5 <= w <= 15:
        errors.append(f"input dimensions must be within 5..15, got {h}x{w}")
    illegal = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if illegal:
        errors.append("grid contains a non-integer or color outside 0..9")
    if not 2 <= analysis["palette_size"] <= 4:
        errors.append(
            f"expected 2..4 nonzero colors, found {analysis['palette_size']}"
        )
    if not 2 <= analysis["period_r"] <= 5:
        errors.append(
            f"first valid period_r must be 2..5, got {analysis['period_r']}"
        )
    if not -4 <= analysis["period_c"] <= 4:
        errors.append(
            f"first valid period_c must be -4..4, got {analysis['period_c']}"
        )
    if not 2 <= analysis["motif_size"] <= 9:
        errors.append(
            f"source-chain motif size must be 2..9, got {analysis['motif_size']}"
        )
    if analysis["nonzero"] < 6:
        errors.append("expected at least six nonzero cells")
    if analysis["support_fraction"] < 0.40:
        errors.append(
            "too few nonzero cells are supported by the selected translation "
            f"({analysis['overlap']}/{analysis['nonzero']})"
        )
    if analysis["base_fraction"] > 0.60:
        errors.append(
            "too many nonzero cells are unsupported source-chain starts "
            f"({analysis['motif_size']}/{analysis['nonzero']})"
        )

    if not errors:
        output = rule_mirror(grid)
        input_nonzero = sum(value != 0 for row in grid for value in row)
        output_nonzero = sum(value != 0 for row in output for value in row)
        if output_nonzero <= input_nonzero:
            errors.append("selected period does not extrapolate beyond the input evidence")

    requested = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict) and not errors:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in AXES and expected is not None and observed.get(axis) != int(expected):
                errors.append(
                    f"override {axis} requested {expected!r}, "
                    f"observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    reasons = []
    if analysis["grid_h"] > 10 or analysis["grid_w"] > 10:
        reasons.append("outside canonical 5..10 input-size envelope")
    if analysis["period_r"] not in (2, 3):
        reasons.append("canonical rows use period_r 2 or 3")
    if abs(analysis["period_c"]) > 3:
        reasons.append("canonical rows use |period_c| <= 3")
    return reasons


MIN_STRICT_FRAC = 0.30


def _witness_period_c(sign: int):
    def predicate(grid):
        try:
            pc = _analyze(grid)["period_c"]
        except ValueError:
            return False
        return (pc > 0) if sign > 0 else (pc < 0) if sign < 0 else (pc == 0)

    return predicate


def _witness_large_period(grid):
    try:
        return _analyze(grid)["period_r"] >= 3
    except ValueError:
        return False


def _witness_repeated_colors(grid):
    try:
        a = _analyze(grid)
        return a["motif_size"] > a["palette_size"]
    except ValueError:
        return False


def _witness_unique_motif_colors(grid):
    try:
        a = _analyze(grid)
        return a["motif_size"] == a["palette_size"]
    except ValueError:
        return False


def _witness_answer_equivalent_multiples(grid):
    try:
        a = _analyze(grid)
        if len(a["periods"]) < 2:
            return False
        first = _solve_with_period(grid, (a["period_r"], a["period_c"]))
        return all(
            _solve_with_period(grid, (dr, dc)) == first
            for dr, dc, _ in a["periods"][1:]
        )
    except ValueError:
        return False


SEMANTIC_WITNESSES = {
    "positive_column_period": _witness_period_c(1),
    "negative_column_period": _witness_period_c(-1),
    "zero_column_period": _witness_period_c(0),
    "period_r_at_least_three": _witness_large_period,
    "repeated_colors_inside_motif": _witness_repeated_colors,
    "unique_color_per_motif_cell": _witness_unique_motif_colors,
    "later_period_multiples_are_answer_equivalent": _witness_answer_equivalent_multiples,
}


def lesson_identifiable(demos, query):
    """Require demonstrations that identify first-period and sign anchoring."""
    reasons = []
    if len(demos) < 3:
        reasons.append("need three demonstrations")
        return reasons

    signs = set()
    demos_distinguish_first = False
    for index, pair in enumerate(demos):
        try:
            analysis = _analyze(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is not analyzable: {exc}")
            continue
        official = pair.get("output")
        predicted = _solve_with_period(
            pair["input"], (analysis["period_r"], analysis["period_c"])
        )
        if official != predicted:
            reasons.append(f"demo {index} output is not the first-period extrapolation")
        signs.add((analysis["period_c"] > 0) - (analysis["period_c"] < 0))
        for dr, dc, _ in analysis["periods"][1:]:
            if _solve_with_period(pair["input"], (dr, dc)) != official:
                demos_distinguish_first = True
                break

    if signs != {-1, 0, 1}:
        reasons.append("demos do not cover negative, zero, and positive column anchoring")
    try:
        query_analysis = _analyze(query["input"])
        query_expected = _solve_with_period(
            query["input"],
            (query_analysis["period_r"], query_analysis["period_c"]),
        )
        if query.get("output") != query_expected:
            reasons.append("query answer is not the first-period extrapolation")
        query_has_different_alternative = any(
            _solve_with_period(query["input"], (dr, dc)) != query_expected
            for dr, dc, _ in query_analysis["periods"][1:]
        )
        if query_has_different_alternative and not demos_distinguish_first:
            reasons.append(
                "query has a different-answer period alternative but demos "
                "do not identify the first-shift convention"
            )
    except Exception as exc:
        reasons.append(f"query input is not analyzable: {exc}")
    return reasons


def mutation_fixtures():
    """Task-semantic impostors that self_check must reject."""
    base = generate(seed=99173, sample_index=3, difficulty="medium")
    analysis = _analyze(base)
    pr, pc = analysis["period_r"], analysis["period_c"]

    broken_color = [row[:] for row in base]
    target = next(
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if base[r][c] != 0
        and 0 <= r - pr < len(base)
        and 0 <= c - pc < len(base[0])
        and base[r - pr][c - pc] == base[r][c]
    )
    old = broken_color[target[0]][target[1]]
    palette = sorted({value for row in base for value in row if value})
    broken_color[target[0]][target[1]] = next(value for value in palette if value != old)

    missing_repeat = [row[:] for row in base]
    missing_repeat[target[0]][target[1]] = 0

    off_period = [row[:] for row in base]
    occupied = {(r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value}
    extra = next(
        (r, c)
        for r in range(1, len(base) - 1)
        for c in range(1, len(base[0]) - 1)
        if (r, c) not in occupied
        and (r + pr, c + pc) not in occupied
        and 0 <= r + pr < len(base)
        and 0 <= c + pc < len(base[0])
    )
    off_period[extra[0]][extra[1]] = palette[0]

    all_zero = full_grid(8, 8, 0)
    full_one_color = full_grid(8, 8, 4)
    short_accidental = full_grid(7, 7, 0)
    short_accidental[1][1] = 2
    short_accidental[3][3] = 2

    return [
        ("broken_repeated_color", broken_color),
        ("missing_interior_repeat", missing_repeat),
        ("off_period_distractor", off_period),
        ("all_zero", all_zero),
        ("full_one_color", full_one_color),
        ("two_pixel_accidental_period", short_accidental),
    ]
