"""Semantic generator for ARC task ``3031e2ee53d1`` (original ``53b68214``).

The authoritative rule finds the smallest row period ``p`` for which the
pattern reappears after a constant horizontal translation ``s``.  It then
continues the first ``p`` rows, translating each successive period block by
``s``, until a square of side equal to the input width has been produced.

The previous generator silently taught the zero-shift special case.  This
version schedules stationary, right-shifting, and left-shifting examples and
covers periods 1, 2, and 3 in every four consecutive demonstrations.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3031e2ee53d1"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e9b80003c95f"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "A 4..8 by 10..16 zero-background input contains one monochrome path. "
    "The rows repeat with the smallest period p in {1,2,3}; after each p-row "
    "block the whole motif is translated left, right, or not at all by a "
    "constant offset. The output is a width-by-width square that continues "
    "the same periodic, translated sequence beyond the input height."
)

INVARIANTS = [
    "input height is smaller than width, so the continuation is visible",
    "every input row contains foreground and the grid contains background",
    "exactly one nonzero color is used",
    "the smallest detected row period is 1, 2, or 3",
    "successive period blocks use one constant horizontal translation",
    "the authoritative continuation has foreground below the input height",
]

COUNTER_HYPOTHESES = [
    "copy the input or pad it with zero rows",
    "repeat rows vertically but ignore horizontal translation",
    "always translate right (or always left)",
    "repeat only the first row, ignoring multi-row periods",
    "always emit the canonical 10x10 output size",
    "memorize a fixed color, fixed period, or fixed motif",
]

AXES = {
    "width": {
        "type": "int",
        "default": "scheduled canonical 10 or generalized 12..16",
        "valid": "10..16",
    },
    "height": {
        "type": "int",
        "default": "scheduled canonical/generalized 4..8",
        "valid": "4..8",
    },
    "period": {
        "type": "int",
        "default": "four-phase schedule covers 1, 2, and 3",
        "valid": "1..3",
    },
    "shift_direction": {
        "type": "str",
        "default": "four-phase schedule covers stationary|right|left",
        "valid": "stationary|right|left",
    },
    "color": {
        "type": "color",
        "default": "rng 1..9",
        "valid": "1..9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)
_SHIFT_DIRECTIONS = ("stationary", "right", "left")
SCHEDULE_PROFILES = (
    "canonical_period3_stationary",
    "canonical_period2_right2",
    "generalized_left",
    "canonical_period1_stationary",
)

# Canonical structural tuples: (height, width, period, exact shift).
_CANONICAL_RULE_PROFILES = {
    (8, 10, 3, 0),
    (5, 10, 1, 0),
    (6, 10, 2, 2),
    (5, 10, 2, 0),
    (8, 10, 2, 0),
}
_CANONICAL_BASE_ROW_COUNTS = {
    (8, 10, 3, 0): (1, 1, 2),
    (5, 10, 1, 0): (1,),
    (6, 10, 2, 2): (3, 1),
    (5, 10, 2, 0): (3, 2),
    (8, 10, 2, 0): (1, 1),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    bounds = {"width": (10, 16), "height": (4, 8), "period": (1, 3)}
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
    direction = overrides.get("shift_direction")
    if direction is not None and direction not in _SHIFT_DIRECTIONS:
        raise ValueError(
            f"override 'shift_direction'={direction!r} not in {_SHIFT_DIRECTIONS}"
        )
    color = overrides.get("color")
    if color is not None:
        if isinstance(color, bool) or not isinstance(color, int):
            raise TypeError("override 'color' must be an integer")
        if not 1 <= color <= 9:
            raise ValueError("override 'color' must be in 1..9")


def _validate_public_call(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive indexes contain all periods and shift signs."""
    _validate_public_call(seed, sample_index)
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(
    seed: int, sample_index: int, band: str
) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, band)
    rng = stable_rng(
        seed, f"{TASK_ID}|{sample_index}|scheduled_defaults", VERSION
    )
    color = rng.randint(1, 9)
    if profile == "canonical_period3_stationary":
        return {
            "width": 10,
            "height": 8,
            "period": 3,
            "shift_direction": "stationary",
            "color": color,
        }
    if profile == "canonical_period2_right2":
        return {
            "width": 10,
            "height": 6,
            "period": 2,
            "shift_direction": "right",
            "color": color,
        }
    if profile == "canonical_period1_stationary":
        return {
            "width": 10,
            "height": 5,
            "period": 1,
            "shift_direction": "stationary",
            "color": color,
        }

    # The generalized phase deliberately leaves the all-canonical width=10
    # shortcut and adds the missing negative-translation branch.
    widths = {"easy": (12,), "medium": (12, 14), "hard": (14, 16)}[band]
    heights = {"easy": (4, 5), "medium": (5, 6, 7), "hard": (7, 8)}[band]
    periods = {"easy": (2,), "medium": (2, 3), "hard": (3,)}[band]
    return {
        "width": rng.choice(widths),
        "height": rng.choice(heights),
        "period": rng.choice(periods),
        "shift_direction": "left",
        "color": color,
    }


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for r, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row]
            except ValueError:
                return None, [f"row {r} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {r} is not a sequence"]
        if width is None:
            width = len(values)
            if width == 0:
                return None, ["grid rows must be nonempty"]
        elif len(values) != width:
            return None, ["grid must be rectangular"]
        for c, value in enumerate(values):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return None, [f"invalid ARC color at ({r},{c}): {value!r}"]
        rows.append(values)
    return rows, []


def _first_nonzero(row: list[int]) -> int | None:
    return next((c for c, value in enumerate(row) if value != 0), None)


def _detect_period_shift(grid: list[list[int]]) -> tuple[int, int] | None:
    """Mirror the canonical Racket detector exactly."""
    h, w = len(grid), len(grid[0])
    f0 = _first_nonzero(grid[0])
    if f0 is None:
        return None
    for period in range(1, h):
        fp = _first_nonzero(grid[period])
        if fp is None:
            continue
        shift = fp - f0
        valid = True
        for r in range(h - period):
            for c in range(w):
                shifted_c = c + shift
                if 0 <= shifted_c < w:
                    if grid[r][c] != grid[r + period][shifted_c]:
                        valid = False
                        break
                elif grid[r][c] != 0:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            return period, shift
    return None


def _render_with_period_shift(
    grid: list[list[int]], period: int, shift: int, side: int | None = None
) -> list[list[int]]:
    width = len(grid[0])
    side = width if side is None else int(side)
    output = full_grid(side, side, 0)
    for r in range(side):
        source_row = r % period
        block = r // period
        for c in range(side):
            source_col = c - shift * block
            if 0 <= source_col < width:
                output[r][c] = grid[source_row][source_col]
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror for focused tests and rival analysis; Racket is authority."""
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    detected = _detect_period_shift(values)
    if detected is None:
        return _render_with_period_shift(values, len(values), 0)
    return _render_with_period_shift(values, detected[0], detected[1])


def _component_count(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    count = 0
    while remaining:
        count += 1
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def semantic_observables(grid: Any) -> dict[str, Any]:
    values, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if errors or values is None:
        return result
    h, w = len(values), len(values[0])
    foreground = sorted({value for row in values for value in row if value != 0})
    row_counts = tuple(sum(value != 0 for value in row) for row in values)
    first_cols = tuple(_first_nonzero(row) for row in values)
    detected = _detect_period_shift(values)
    result.update(
        {
            "grid": values,
            "height": h,
            "width": w,
            "foreground": foreground,
            "foreground_count": sum(row_counts),
            "background_count": h * w - sum(row_counts),
            "row_counts": row_counts,
            "first_columns": first_cols,
            "component_count": _component_count(values),
            "detected": detected,
        }
    )
    if detected is None:
        return result
    period, shift = detected
    direction = "stationary" if shift == 0 else ("right" if shift > 0 else "left")
    output = _render_with_period_shift(values, period, shift)
    result.update(
        {
            "period": period,
            "shift": shift,
            "shift_direction": direction,
            "color": foreground[0] if len(foreground) == 1 else None,
            "extension_nonzero": any(
                value != 0 for row in output[h:] for value in row
            ),
            "strict_profile": (
                len(foreground) == 1
                and (h, w, period, shift) in _CANONICAL_RULE_PROFILES
            ),
        }
    )
    return result


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors") or facts.get("detected") is None:
        return ("invalid", tuple(facts.get("errors", [])))
    return (
        facts["height"],
        facts["width"],
        facts["period"],
        facts["shift"],
        facts["color"],
        facts["row_counts"][: facts["period"]],
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the complete lawful envelope and reject rule-hiding impostors."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    h, w = facts["height"], facts["width"]
    if not 4 <= h <= 8 or not 10 <= w <= 16:
        errors.append(f"supported dimensions are h=4..8 and w=10..16, found {h}x{w}")
    if h >= w:
        errors.append("input height must be smaller than width")
    if len(facts["foreground"]) != 1:
        errors.append(
            f"expected exactly one nonzero color, found {len(facts['foreground'])}"
        )
    if facts["background_count"] == 0:
        errors.append("grid must retain zero background")
    if facts["foreground_count"] >= h * w // 2:
        errors.append("foreground is too dense to expose the translated motif")
    if any(count == 0 for count in facts["row_counts"]):
        errors.append("every row must contain foreground")
    detected = facts.get("detected")
    if detected is None:
        errors.append("no repeated row period with constant translation was detected")
        return errors
    period, shift = detected
    if period not in (1, 2, 3):
        errors.append(f"smallest detected period must be 1..3, found {period}")
    if abs(shift) > 2:
        errors.append(f"translation magnitude must be at most 2, found {shift}")
    if not facts.get("extension_nonzero"):
        errors.append("the square continuation has no foreground below the input")

    # Generated paths are one 4-connected object.  The second canonical test is
    # the lawful sparse exception: one cell per row in an alternating diagonal.
    if facts["component_count"] > 1:
        sparse_diagonal = all(count == 1 for count in facts["row_counts"])
        if sparse_diagonal:
            cols = [int(c) for c in facts["first_columns"]]
            sparse_diagonal = all(abs(a - b) <= 1 for a, b in zip(cols, cols[1:]))
        canonical_key = (h, w, period, shift)
        canonical_fragment = (
            canonical_key in _CANONICAL_BASE_ROW_COUNTS
            and tuple(facts["row_counts"][:period])
            == _CANONICAL_BASE_ROW_COUNTS[canonical_key]
        )
        if not sparse_diagonal and not canonical_fragment:
            errors.append(
                f"foreground fragments into {facts['component_count']} components"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Empirical canonical rule profile, not merely a size/palette marginal."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if not facts.get("strict_profile"):
        reasons.append(
            "(height,width,period,shift) is not one of the five canonical profiles"
        )
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors") or facts.get("detected") is None:
        raise ValueError("cannot observe axes from an invalid grid")
    if facts.get("color") is None:
        raise ValueError("cannot observe a unique foreground color")
    return {
        "width": facts["width"],
        "height": facts["height"],
        "period": facts["period"],
        "shift_direction": facts["shift_direction"],
        "color": facts["color"],
    }


def _bridge_rows(period: int, shift: int, row0_width: int) -> list[set[int]]:
    """Connected base-row masks with distinct row counts for exact period."""
    row0 = set(range(row0_width))
    if period == 1:
        # Width > |shift| makes successive translated copies overlap.
        return [row0]
    next_row0 = {c + shift for c in row0}
    overlap = sorted(row0 & next_row0)
    if not overlap:
        raise ValueError("motif cannot bridge the requested translation")
    pivot = overlap[len(overlap) // 2]
    if period == 2:
        neighbor_candidates = sorted((row0 | next_row0) - {pivot})
        neighbor = min(neighbor_candidates, key=lambda c: (abs(c - pivot), c))
        return [row0, {pivot, neighbor}]

    neighbor_candidates = sorted(row0 - {pivot})
    neighbor = min(neighbor_candidates, key=lambda c: (abs(c - pivot), c))
    return [row0, {pivot, neighbor}, {pivot}]


def _choose_exact_shift(
    profile: str | None,
    direction: str,
    period: int,
    height: int,
    width: int,
    variant: int,
    rng,
) -> tuple[int, list[set[int]], tuple[int, int]]:
    if direction == "stationary":
        magnitudes = (0,)
    elif profile == "canonical_period2_right2":
        magnitudes = (2,)
    elif period == 1:
        magnitudes = (1,)
    else:
        first = rng.choice((1, 2))
        magnitudes = (first, 3 - first)

    sign = -1 if direction == "left" else 1
    for magnitude in magnitudes:
        shift = 0 if magnitude == 0 else sign * magnitude
        base_width = (abs(shift) + 1 if period == 1 else 3) + variant
        rows = _bridge_rows(period, shift, base_width)
        q_extend = height // period
        lo_rel = min(c + min(0, q_extend * shift) for row in rows for c in row)
        hi_rel = max(c + max(0, q_extend * shift) for row in rows for c in row)
        anchor_lo = -lo_rel
        anchor_hi = width - 1 - hi_rel
        if anchor_lo <= anchor_hi:
            return shift, rows, (anchor_lo, anchor_hi)
    raise ValueError(
        "no connected translated motif fits requested width/height/period/direction"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_public_call(seed, sample_index)
    band = _band(difficulty)
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, band) if not overrides else None
    defaults = _scheduled_defaults(seed, sample_index, band)
    effective_overrides = {**defaults, **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective_overrides,
    )
    width = ctx.draw_int("width", 10, 16)
    height = ctx.draw_int("height", 4, 8)
    period = ctx.draw_int("period", 1, 3)
    direction = ctx.draw_choice("shift_direction", _SHIFT_DIRECTIONS)
    color = ctx.draw_color("color", exclude={0})

    motif_rng = ctx.draw_rng("motif")
    max_variant = {"easy": 0, "medium": 1, "hard": 2}[band]
    variant = motif_rng.randint(0, max_variant)
    try:
        shift, base_rows, anchor_bounds = _choose_exact_shift(
            profile, direction, period, height, width, variant, motif_rng
        )
    except ValueError:
        # A large decorative variant may not fit an extreme explicit boundary;
        # retry the same semantics without decoration rather than clamping an axis.
        shift, base_rows, anchor_bounds = _choose_exact_shift(
            profile, direction, period, height, width, 0, motif_rng
        )
    anchor = motif_rng.randint(anchor_bounds[0], anchor_bounds[1])

    grid = full_grid(height, width, 0)
    for r in range(height):
        block = r // period
        base_row = base_rows[r % period]
        for relative_col in base_row:
            c = anchor + relative_col + block * shift
            if not 0 <= c < width:
                raise AssertionError("internal motif escaped the input canvas")
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, "
                f"observed {observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Named rivals and lesson-level identifiability
# ---------------------------------------------------------------------------


def _copy_grid(grid: Any) -> list[list[int]]:
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    return [list(row) for row in values]


def _rival_identity(grid):
    return _copy_grid(grid)


def _rival_zero_pad(grid):
    values = _copy_grid(grid)
    side = len(values[0])
    return values + full_grid(side - len(values), side, 0)


def _rival_no_shift(grid):
    values = _copy_grid(grid)
    detected = _detect_period_shift(values)
    if detected is None:
        return _rival_zero_pad(values)
    return _render_with_period_shift(values, detected[0], 0)


def _rival_always_right(grid):
    values = _copy_grid(grid)
    detected = _detect_period_shift(values)
    if detected is None:
        return _rival_zero_pad(values)
    return _render_with_period_shift(values, detected[0], 1)


def _rival_always_left(grid):
    values = _copy_grid(grid)
    detected = _detect_period_shift(values)
    if detected is None:
        return _rival_zero_pad(values)
    return _render_with_period_shift(values, detected[0], -1)


def _rival_repeat_first_row(grid):
    values = _copy_grid(grid)
    side = len(values[0])
    return [list(values[0]) for _ in range(side)]


def _rival_fixed_width_10(grid):
    true_output = rule_mirror(grid)
    out = full_grid(10, 10, 0)
    for r in range(min(10, len(true_output))):
        for c in range(min(10, len(true_output[r]))):
            out[r][c] = true_output[r][c]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity": _rival_identity,
    "zero_pad_without_continuation": _rival_zero_pad,
    "ignore_horizontal_shift": _rival_no_shift,
    "always_shift_right": _rival_always_right,
    "always_shift_left": _rival_always_left,
    "repeat_first_row_only": _rival_repeat_first_row,
    "fixed_output_width_10": _rival_fixed_width_10,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    # All official examples have width 10, so only generated wider examples can
    # refute this otherwise-perfect canonical shortcut.
    "fixed_output_width_10": _rival_fixed_width_10,
}


def _witness_stationary(grid) -> bool:
    return semantic_observables(grid).get("shift") == 0


def _witness_right(grid) -> bool:
    return semantic_observables(grid).get("shift", 0) > 0


def _witness_left(grid) -> bool:
    return semantic_observables(grid).get("shift", 0) < 0


def _witness_period_1(grid) -> bool:
    return semantic_observables(grid).get("period") == 1


def _witness_period_2(grid) -> bool:
    return semantic_observables(grid).get("period") == 2


def _witness_period_3(grid) -> bool:
    return semantic_observables(grid).get("period") == 3


def _witness_extension(grid) -> bool:
    return bool(semantic_observables(grid).get("extension_nonzero"))


def _witness_generalized_width(grid) -> bool:
    return semantic_observables(grid).get("width") != 10


SEMANTIC_WITNESSES = {
    "stationary_translation": _witness_stationary,
    "right_translation": _witness_right,
    "left_translation": _witness_left,
    "period_1": _witness_period_1,
    "period_2": _witness_period_2,
    "period_3": _witness_period_3,
    "nonzero_continuation": _witness_extension,
    "noncanonical_width": _witness_generalized_width,
}
WITNESS_RIVALS = {
    "stationary_translation": ["always_shift_right", "always_shift_left"],
    "right_translation": ["ignore_horizontal_shift", "always_shift_left"],
    "left_translation": ["ignore_horizontal_shift", "always_shift_right"],
    # A period-1 example is answer-equivalent to some larger-period
    # descriptions, so it is intentionally not overclaimed as a rival refuter.
    "period_2": ["repeat_first_row_only"],
    "period_3": ["repeat_first_row_only"],
    "nonzero_continuation": ["identity", "zero_pad_without_continuation"],
    "noncanonical_width": ["fixed_output_width_10"],
}


def _grids_equal(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which any named wrong rule survives the demos."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            if not fits_demos:
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives demos and query")
            else:
                reasons.append(
                    f"competitor {name!r} fits every demo but disagrees on query"
                )
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
