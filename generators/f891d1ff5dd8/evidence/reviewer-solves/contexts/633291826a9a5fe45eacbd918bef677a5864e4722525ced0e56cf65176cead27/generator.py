"""Reviewed generator for ARC task f891d1ff5dd8.

The first row is an ordered cycle of colors.  Row one is a preserved decoy.
Every later output row is replaced by a solid band whose color is selected by
its *position* in the first-row cycle.  The input body may be blank or contain
one compact decoy rectangle; the latter is intentionally overwritten.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


Grid = list[list[int]]

GENERATOR_ID = "f891d1ff5dd8"
VERSION = "2.1.0"
TASK_ID = "f891d1ff5dd8"
RULE_HASH = "9a77eb6a5412"
SUMMARY = (
    "Read row 0 as an ordered color cycle; preserve rows 0 and 1, then "
    "overwrite each later row with the corresponding cycle color."
)

INVARIANTS = [
    "the grid is rectangular with height 3..18 and width 2..8",
    "row 0 contains at least two nonzero colors and defines an ordered cycle",
    "row 1 is a solid nonzero decoy color absent from row 0",
    "the body is blank or one solid rectangle in the row-1 decoy color",
]

BODY_PATTERNS = ("blank", "rectangle")
AXES = {
    "grid_h": {"type": "int", "default": "curriculum 3..18", "valid": "3..18"},
    "grid_w": {"type": "int", "default": "curriculum 2..8", "valid": "2..8"},
    "body_pattern": {
        "type": "str",
        "default": "four-slot blank|rectangle curriculum",
        "valid": "blank|rectangle",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Three demonstrations are sufficient because every three consecutive slots of
# the four-profile schedule contain all three counterexample types below.
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 0.20


def _grid_errors(grid: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    if not 3 <= h <= 18:
        errors.append(f"height {h} outside 3..18")
    if not 2 <= w <= 8:
        errors.append(f"width {w} outside 2..8")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color 0..9")
                return errors
    if errors:
        return errors

    row0 = grid[0]
    if any(value == 0 for value in row0):
        errors.append("row 0 may not contain background color 0")
    if len(set(row0)) < 2:
        errors.append("row 0 must contain at least two distinct cycle colors")

    row1 = grid[1]
    if len(set(row1)) != 1 or row1[0] == 0:
        errors.append("row 1 must be one solid nonzero decoy color")
        return errors
    decoy = row1[0]
    if decoy in row0:
        errors.append("row-1 decoy color must be absent from row 0")

    body_cells: list[tuple[int, int]] = []
    for r in range(2, h):
        for c in range(w):
            value = grid[r][c]
            if value not in (0, decoy):
                errors.append("body cells may contain only background or the row-1 decoy color")
                return errors
            if value == decoy:
                body_cells.append((r, c))
    if body_cells:
        top = min(r for r, _ in body_cells)
        bottom = max(r for r, _ in body_cells)
        left = min(c for _, c in body_cells)
        right = max(c for _, c in body_cells)
        expected = {
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
        }
        if set(body_cells) != expected:
            errors.append("nonzero body cells must form one filled rectangle")
    return errors


def self_check(grid: object, *, difficulty=None, meta=None) -> list[str]:
    """Return concise reasons when an input is outside the reviewed grammar."""
    del difficulty, meta
    return _grid_errors(grid)


def strict_canonical_like(grid: object) -> list[str]:
    """The reviewed production grammar is the declared canonical neighborhood."""
    return _grid_errors(grid)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Four-slot curriculum; seed/difficulty vary instances, not lesson roles."""
    del seed, difficulty
    return sample_index % 4


def _canonical_widths(difficulty) -> tuple[int, ...]:
    if difficulty == "easy":
        return (2, 3)
    if difficulty == "hard":
        return (4, 5)
    if difficulty == "medium":
        return (3, 4)
    return (2, 3, 4, 5)


def _broad_ranges(difficulty, *, repeated: bool) -> tuple[int, int, int, int]:
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 10, 2, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 18, 4, 8
    elif difficulty == "medium":
        h_lo, h_hi, w_lo, w_hi = 7, 15, 3, 7
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 18, 2, 8
    if repeated:
        h_lo = max(h_lo, 5)
        w_lo = max(w_lo, 3)
    return h_lo, h_hi, w_lo, w_hi


def _long_body_widths(difficulty, *, repeated: bool) -> tuple[int, ...]:
    """Widths that leave room for strictly more than two complete cycles."""
    h_lo, h_hi, w_lo, w_hi = _broad_ranges(difficulty, repeated=repeated)
    del h_lo
    widths = tuple(w for w in range(w_lo, w_hi + 1) if 2 * w + 3 <= h_hi)
    if not widths:
        raise AssertionError("difficulty band cannot host a long-body witness")
    return widths


def _validate_call_controls(seed: Any, sample_index: Any, difficulty: Any) -> None:
    """Reject malformed request controls before deterministic sampling."""
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer, "
            f"not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, not {sample_index}")
    if difficulty is not None:
        if type(difficulty) is not str:
            raise TypeError(
                "difficulty must be a string or None, "
                f"not {type(difficulty).__name__}"
            )
        if difficulty not in ("easy", "medium", "hard"):
            raise ValueError(
                "difficulty must be one of ('easy', 'medium', 'hard') or None, "
                f"not {difficulty!r}"
            )


def _validate_override_keys(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    """Generate a deterministic lawful input with exact-or-loud public axes."""
    _validate_call_controls(seed, sample_index, difficulty)
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
    has_override = any(value is not None for value in overrides.values())

    if has_override:
        h = ctx.draw_int_strict("grid_h", 3, 18)
        w = ctx.draw_int_strict("grid_w", 2, 8)
        body_pattern = ctx.draw_choice("body_pattern", BODY_PATTERNS)
    elif profile == 0:
        widths = _canonical_widths(difficulty)
        w = ctx.draw_choice("grid_w", widths)
        h = ctx.draw_choice("grid_h", (2 * w + 2,))
        body_pattern = ctx.draw_choice("body_pattern", ("blank",))
    else:
        repeated = profile in (2, 3)
        h_lo, h_hi, w_lo, w_hi = _broad_ranges(difficulty, repeated=repeated)
        if profile in (1, 3):
            # These two roles jointly guarantee that every 3-of-4 lesson
            # contains a counterexample to the canonical-fitting shortcut
            # "paint exactly two header cycles, then stop".
            widths = _long_body_widths(difficulty, repeated=repeated)
            w = ctx.draw_choice("grid_w", widths)
            h = ctx.draw_int_strict("grid_h", max(h_lo, 2 * w + 3), h_hi)
        else:
            h = ctx.draw_int_strict("grid_h", h_lo, h_hi)
            w = ctx.draw_int_strict("grid_w", w_lo, w_hi)
        scheduled_body = "rectangle" if profile in (1, 3) else "blank"
        body_pattern = ctx.draw_choice("body_pattern", (scheduled_body,))

    repeated_cycle = profile in (2, 3) and w >= 3 and h >= 5
    palette_size = (3 if repeated_cycle else w + 1)
    palette = list(
        ctx.draw_distinct_colors("semantic_palette", n=palette_size, exclude=(0,))
    )
    decoy = palette[-1]

    if repeated_cycle:
        a, b = palette[0], palette[1]
        row0 = [a, b, b]
        for c in range(3, w):
            row0.append(a if c % 2 else b)
    else:
        row0 = palette[:w]

    grid = full_grid(h, w, 0)
    grid[0] = row0[:]
    grid[1] = [decoy] * w

    if body_pattern == "rectangle":
        # Anchor the decoy rectangle to row 1.  This preserves the canonical
        # one-object foreground morphology while still testing that the body is
        # overwritten rather than merely filled where blank.
        body_h = h - 2
        rng = ctx.draw_rng("body_rectangle")
        rect_h = rng.randint(1, max(1, body_h // 2))
        rect_w = rng.randint(1, max(1, w // 2))
        left = rng.randint(0, w - rect_w)
        for r in range(2, 2 + rect_h):
            for c in range(left, left + rect_w):
                grid[r][c] = decoy

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator produced an invalid grid: " + "; ".join(errors))
    return grid


def observe_overrides(grid: Grid) -> dict[str, object]:
    """Recover every advertised axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "body_pattern": (
            "rectangle"
            if any(value != 0 for row in grid[2:] for value in row)
            else "blank"
        ),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror used only for focused tests and semantic rivals."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    output = deepcopy(grid)
    width = len(grid[0])
    for r in range(2, len(grid)):
        color = grid[0][(r - 2) % width]
        output[r] = [color] * width
    return output


def _rival_preserve_body_decoys(grid: Grid) -> Grid:
    """Shortcut fitting public blank bodies: fill zeros but preserve decoys."""
    output = deepcopy(grid)
    width = len(grid[0])
    for r in range(2, len(grid)):
        color = grid[0][(r - 2) % width]
        output[r] = [color if value == 0 else value for value in grid[r]]
    return output


def _rival_deduplicate_cycle(grid: Grid) -> Grid:
    """Shortcut fitting public distinct headers: cycle first-seen colors only."""
    unique: list[int] = []
    for value in grid[0]:
        if value not in unique:
            unique.append(value)
    output = deepcopy(grid)
    width = len(grid[0])
    for r in range(2, len(grid)):
        color = unique[(r - 2) % len(unique)]
        output[r] = [color] * width
    return output


def _rival_two_cycles_only(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: paint two cycles, then leave later rows."""
    output = deepcopy(grid)
    width = len(grid[0])
    stop = min(len(grid), 2 + 2 * width)
    for r in range(2, stop):
        color = grid[0][(r - 2) % width]
        output[r] = [color] * width
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "preserve_body_decoys": _rival_preserve_body_decoys,
    "deduplicate_cycle": _rival_deduplicate_cycle,
    "two_cycles_only": _rival_two_cycles_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_body_overwrite(grid: Grid) -> bool:
    return (
        not self_check(grid)
        and any(value != 0 for row in grid[2:] for value in row)
        and _rival_preserve_body_decoys(grid) != rule_mirror(grid)
    )


def _witness_positional_repetition(grid: Grid) -> bool:
    return (
        not self_check(grid)
        and len(set(grid[0])) < len(grid[0])
        and _rival_deduplicate_cycle(grid) != rule_mirror(grid)
    )


def _witness_beyond_two_cycles(grid: Grid) -> bool:
    return (
        not self_check(grid)
        and len(grid) - 2 > 2 * len(grid[0])
        and _rival_two_cycles_only(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "body_overwrite": _witness_body_overwrite,
    "positional_repetition": _witness_positional_repetition,
    "beyond_two_cycles": _witness_beyond_two_cycles,
}
WITNESS_RIVALS = {
    "body_overwrite": ["preserve_body_decoys"],
    "positional_repetition": ["deduplicate_cycle"],
    "beyond_two_cycles": ["two_cycles_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when a declared shortcut survives all demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(pair["input"]) != truth:
                refuted[name] = True

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute competitor {name!r}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query output disagrees with the selected rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and {"input", "output"} <= set(pair)
            and competitor(pair["input"]) == pair["output"]
            for pair in demos
        ) and competitor(query["input"]) != truth:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons
