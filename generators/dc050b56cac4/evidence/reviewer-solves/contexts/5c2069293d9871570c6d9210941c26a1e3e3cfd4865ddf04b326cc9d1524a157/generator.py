"""Constructive generator for ARC task e48d4e1a / dc050b56cac4.

Each lawful input contains one full-row/full-column cross and N gray markers,
where 1 <= N <= 3.  The selected Racket rule removes the markers and redraws
the cross with its center shifted by (+N, -N).

Canonical examples place the gray markers as a top-right vertical stack.  That
leaves several plausible but wrong rules indistinguishable: using the number of
gray-bearing rows, the gray vertical span, or the top-right stack length.  The
ordinary three-profile schedule retains a canonical-linked stack and adds two
constructive layouts that refute all three shortcuts.
"""
from __future__ import annotations

from typing import Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc050b56cac4"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4fe6d23687d0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "One colored full-row/full-column cross plus 1-3 gray markers; count every "
    "gray cell and move the cross center by (+N,-N), erasing the markers."
)
INVARIANTS = [
    "an 8..20 rectangular ARC grid with cells 0..9",
    "exactly one full row and one full column of the same color in 1..9 except 5",
    "no off-cross occurrence of the cross color and no third foreground color",
    "exactly 1..3 gray(5) cells, all off the cross",
    "the center shifted by (+N,-N) remains in bounds",
]

CROSS_POSITIONS = (
    "center",
    "upper_left",
    "upper_right",
    "lower_left",
    "lower_right",
)
SCHEDULE_PROFILES = (
    "canonical_stack",
    "same_row_witness",
    "scattered_witness",
)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10 on canonical-stack draws; difficulty-weighted 8..20 otherwise",
        "valid": "8..20",
    },
    "grid_w": {
        "type": "int",
        "default": "10 on canonical-stack draws; difficulty-weighted 8..20 otherwise",
        "valid": "8..20",
    },
    "cross_color": {
        "type": "color",
        "default": "uniform ARC color except 0 and 5",
        "valid": "1..9 (≠5)",
    },
    "n_grays": {
        "type": "int",
        "default": "scheduled 1..3; witness profiles use 2 and 3",
        "valid": "1..3",
    },
    "cross_position": {
        "type": "str",
        "default": "canonical stack uses center; witness profiles vary",
        "valid": "|".join(CROSS_POSITIONS),
    },
}

# Every advertised cross-product combination is constructive in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Point = tuple[int, int]


def _validate_call_arguments(seed, sample_index) -> None:
    """Reject scalar aliases before they reach deterministic draw helpers."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the deterministic semantic profile for a draw."""
    _validate_call_arguments(seed, sample_index)
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "cross_color", "n_grays"}:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer (bool is not accepted)")
        elif name == "cross_position" and type(value) is not str:
            raise TypeError("cross_position must be a string")


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int, overrides: dict) -> int:
    """Use a pinned default while retaining the complete exact override domain."""
    if overrides.get(name) is None:
        return int(ctx.draw_choice(name, (default,)))
    return ctx.draw_int_strict(name, lo, hi)


def _scheduled_choice(ctx, name: str, options: Sequence[str], default: str, overrides: dict) -> str:
    if overrides.get(name) is None:
        return str(ctx.draw_choice(name, (default,)))
    return str(ctx.draw_choice(name, tuple(options)))


def _default_dimension(ctx, label: str, profile: str, band: str) -> int:
    if profile == "canonical_stack":
        return 10
    lo, hi = {
        "easy": (8, 11),
        "medium": (10, 16),
        "hard": (16, 20),
    }[band]
    return ctx.draw_rng(f"default:{label}:{profile}:{band}").randint(lo, hi)


def _default_gray_count(sample_index: int, profile: str) -> int:
    if profile == "same_row_witness":
        return 2
    if profile == "scattered_witness":
        return 3
    # Canonical-linked draws cycle through every legal count without coupling
    # it to seed.  The full 3-profile lesson schedule still covers all rivals.
    return 1 + (sample_index // len(SCHEDULE_PROFILES)) % 3


def _cross_center(position: str, h: int, w: int, n_grays: int) -> Point:
    r_lo, r_hi = 0, h - 1 - n_grays
    c_lo, c_hi = n_grays, w - 1
    points = {
        "center": ((r_lo + r_hi) // 2, (c_lo + c_hi) // 2),
        "upper_left": (r_lo, c_lo),
        "upper_right": (r_lo, c_hi),
        "lower_left": (r_hi, c_lo),
        "lower_right": (r_hi, c_hi),
    }
    try:
        return points[position]
    except KeyError as exc:
        raise ValueError(f"unknown cross_position {position!r}") from exc


def _vertical_stack(h: int, w: int, cr: int, cc: int, n: int) -> list[Point]:
    """Prefer the canonical top-right stack, falling back constructively."""
    for c in range(w - 1, -1, -1):
        if c == cc:
            continue
        for start in range(0, h - n + 1):
            points = [(start + offset, c) for offset in range(n)]
            if all(r != cr for r, _ in points):
                return points
    raise RuntimeError("could not place a lawful vertical gray stack")


def _same_row(h: int, w: int, cr: int, cc: int, n: int) -> list[Point]:
    # The legal center bound guarantees cr + n <= h - 1.
    row = cr + n
    columns = [c for c in range(w) if c not in {cc, w - 1}]
    if len(columns) < n:
        columns = [c for c in range(w) if c != cc]
    return [(row, c) for c in columns[:n]]


def _scattered(h: int, w: int, cr: int, cc: int, n: int) -> list[Point]:
    # For N=3, two bottom-adjacent rows make row-count and vertical-span equal
    # 2 rather than 3. For N=2 both markers share one row. N=1 remains lawful.
    bottom = h - 1
    columns = [c for c in range(w) if c not in {cc, w - 1}]
    if len(columns) < n:
        columns = [c for c in range(w) if c != cc]
    if n <= 2:
        points = [(bottom, columns[i]) for i in range(n)]
    else:
        points = [(bottom, columns[0]), (bottom, columns[1]), (bottom - 1, columns[2])]
    if any(r == cr or c == cc for r, c in points):
        raise RuntimeError("constructive gray witness collided with the cross")
    return points


def _gray_points(profile: str, h: int, w: int, cr: int, cc: int, n: int) -> list[Point]:
    if profile == "canonical_stack":
        return _vertical_stack(h, w, cr, cc, n)
    if profile == "same_row_witness":
        return _same_row(h, w, cr, cc, n)
    if profile == "scattered_witness":
        return _scattered(h, w, cr, cc, n)
    raise ValueError(f"unknown schedule profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    """Generate one lawful, deterministic input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    _validate_overrides(overrides)
    band = "medium" if difficulty is None else difficulty
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    h = _scheduled_int(
        ctx, "grid_h", 8, 20, _default_dimension(ctx, "grid_h", profile, band), overrides
    )
    w = _scheduled_int(
        ctx, "grid_w", 8, 20, _default_dimension(ctx, "grid_w", profile, band), overrides
    )
    if overrides.get("cross_color") is None:
        cross_color = ctx.draw_color("cross_color", exclude={0, 5})
    else:
        cross_color = ctx.draw_color("cross_color", exclude={0, 5})
    n_grays = _scheduled_int(
        ctx, "n_grays", 1, 3, _default_gray_count(sample_index, profile), overrides
    )
    default_position = (
        "center"
        if profile == "canonical_stack"
        else ctx.draw_rng(f"default:cross_position:{profile}").choice(CROSS_POSITIONS)
    )
    cross_position = _scheduled_choice(
        ctx, "cross_position", CROSS_POSITIONS, default_position, overrides
    )
    cr, cc = _cross_center(cross_position, h, w, n_grays)

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[cr][c] = cross_color
    for r in range(h):
        grid[r][cc] = cross_color
    for r, c in _gray_points(profile, h, w, cr, cc, n_grays):
        if grid[r][c] != 0:
            raise RuntimeError("constructive gray placement collided with foreground")
        grid[r][c] = 5

    # Construction is direct (no rejection or clipping); the public checker
    # and task-local tests validate the returned pixels independently.
    return grid


def _analyze(grid) -> dict[str, object]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    h = len(grid)
    if not (8 <= h <= 20 and 8 <= w <= 20):
        raise ValueError(f"grid shape {h}x{w} outside 8..20")

    rows = []
    for r, row in enumerate(grid):
        if row[0] not in (0, 5) and len(set(row)) == 1:
            rows.append((r, row[0]))
    cols = []
    for c in range(w):
        values = [grid[r][c] for r in range(h)]
        if values[0] not in (0, 5) and len(set(values)) == 1:
            cols.append((c, values[0]))
    if len(rows) != 1 or len(cols) != 1 or rows[0][1] != cols[0][1]:
        raise ValueError("need exactly one full row and one full column of the same non-gray color")

    cr, cross_color = rows[0]
    cc, _ = cols[0]
    if cross_color in (0, 5) or not 1 <= cross_color <= 9:
        raise ValueError("cross color must be 1..9 except 5")
    allowed = {0, 5, cross_color}
    if any(value not in allowed for row in grid for value in row):
        raise ValueError("only background, gray markers, and the cross color are allowed")
    cross_cells = {(cr, c) for c in range(w)} | {(r, cc) for r in range(h)}
    observed_cross = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == cross_color
    }
    if observed_cross != cross_cells:
        raise ValueError("cross color must occur exactly on the one full row and column")
    grays = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not 1 <= len(grays) <= 3:
        raise ValueError(f"gray marker count {len(grays)} outside 1..3")
    if any(r == cr or c == cc for r, c in grays):
        raise ValueError("gray markers must be off the cross")
    if cr + len(grays) >= h or cc - len(grays) < 0:
        raise ValueError("cross center shifted by (+N,-N) would leave the grid")
    return {
        "grid_h": h,
        "grid_w": w,
        "cross_row": cr,
        "cross_col": cc,
        "cross_color": cross_color,
        "n_grays": len(grays),
        "grays": tuple(grays),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """The complete lawful input manifold for the selected rule."""
    return self_check(grid)


def _position_name(h: int, w: int, n: int, cr: int, cc: int) -> str:
    hits = [name for name in CROSS_POSITIONS if _cross_center(name, h, w, n) == (cr, cc)]
    if len(hits) != 1:
        raise ValueError(f"cross center {(cr, cc)} is not an advertised exact position")
    return hits[0]


def observe_overrides(grid) -> dict[str, object]:
    """Recover every public exact axis from pixels."""
    facts = _analyze(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "cross_color": facts["cross_color"],
        "n_grays": facts["n_grays"],
        "cross_position": _position_name(
            int(facts["grid_h"]),
            int(facts["grid_w"]),
            int(facts["n_grays"]),
            int(facts["cross_row"]),
            int(facts["cross_col"]),
        ),
    }


def _output_for_shift(grid, shift: int) -> Grid:
    facts = _analyze(grid)
    nr = int(facts["cross_row"]) + shift
    nc = int(facts["cross_col"]) - shift
    h, w = int(facts["grid_h"]), int(facts["grid_w"])
    if not (0 <= nr < h and 0 <= nc < w):
        raise ValueError(f"rival shift {shift} leaves the grid")
    color = int(facts["cross_color"])
    return [[color if r == nr or c == nc else 0 for c in range(w)] for r in range(h)]


def rule_mirror(grid) -> Grid:
    """Supplementary Python mirror of the selected Racket rule."""
    return _output_for_shift(grid, int(_analyze(grid)["n_grays"]))


def _gray_row_count(grid) -> Grid:
    facts = _analyze(grid)
    return _output_for_shift(grid, len({r for r, _ in facts["grays"]}))


def _gray_vertical_span(grid) -> Grid:
    rows = [r for r, _ in _analyze(grid)["grays"]]
    return _output_for_shift(grid, max(rows) - min(rows) + 1)


def _top_right_stack_length(grid) -> Grid:
    n = 0
    for row in grid:
        if row[-1] != 5:
            break
        n += 1
    return _output_for_shift(grid, n)


def _same_row_witness(grid) -> bool:
    try:
        facts = _analyze(grid)
    except ValueError:
        return False
    grays = facts["grays"]
    n = int(facts["n_grays"])
    return n >= 2 and len({r for r, _ in grays}) == 1 and all(c != int(facts["grid_w"]) - 1 for _, c in grays)


def _scattered_witness(grid) -> bool:
    try:
        facts = _analyze(grid)
    except ValueError:
        return False
    rows = [r for r, _ in facts["grays"]]
    n = int(facts["n_grays"])
    return (
        n == 3
        and len(set(rows)) == 2
        and max(rows) - min(rows) + 1 == 2
        and all(c != int(facts["grid_w"]) - 1 for _, c in facts["grays"])
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "gray_row_count": _gray_row_count,
    "gray_vertical_span": _gray_vertical_span,
    "top_right_stack_length": _top_right_stack_length,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "same_row_markers": _same_row_witness,
    "two_row_scatter": _scattered_witness,
}
WITNESS_RIVALS = {
    "same_row_markers": tuple(SEMANTIC_RIVALS),
    "two_row_scatter": tuple(SEMANTIC_RIVALS),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a declared rival alive."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must be a labeled pair"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} is not a labeled pair")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demonstration {index} is outside the rule domain: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demonstration {index} output does not match the gray-count rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons
    if "output" in query and query["output"] != query_answer:
        reasons.append("query output does not match the gray-count rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair.get("output") for pair in demos)
            changes_query = rival(query["input"]) != query_answer
        except (TypeError, ValueError) as exc:
            reasons.append(f"competing rule {name!r} errored: {exc}")
            continue
        if survives and changes_query:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons
