"""Semantic curriculum for row-leader recoloring.

The selected authority preserves the grid shape and all background cells.  In
each non-empty row, the leftmost non-zero cell is the leader; every other
non-zero cell in that row is recolored to the leader's color.

Every generated instance contains sparse and frequency-controlled rows that
distinguish the selected rule from rightmost, modal, rarest-color, global-leader,
span-fill, row-fill, and per-component shortcuts.  The two observable curriculum
profiles alternate; one also contains an already-uniform row so identity behavior
remains visible.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0bb8813a21dc"
TASK_ID = GENERATOR_ID
RULE_HASH = "42a14ef4873c"
VERSION = "3.1.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "For each active row, read the leftmost non-zero color and recolor every "
    "non-zero cell in that row to it. Background gaps remain background."
)

INVARIANTS = [
    "background is 0 and grid shape is preserved",
    "each task-like input has three active rows with at least three non-zero cells",
    "at least two rows have different leader colors",
    "a sparse witness row has distinct wrong modal and rightmost choices across a gap",
    "another row repeats its leader while leaving a singleton nonleader, refuting rarest-color",
    "identity_scope includes one already-uniform row; mixed_scope includes none",
]

SCENE_PROFILES = ("identity_scope", "mixed_scope")
SCHEDULE_PROFILES = SCENE_PROFILES
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "alternating identity_scope|mixed_scope curriculum",
        "valid": "identity_scope|mixed_scope",
        "doc": (
            "Exact observable profile. identity_scope contains one uniform active "
            "row; mixed_scope has three mixed rows. Both retain the decisive "
            "sparse leader witness."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Exact canonical (height, width, palette-size including background) profiles.
# Cycling all four in every band makes the profile-floor contract constructive.
_CANONICAL_PROFILES = (
    (5, 6, 9),
    (4, 7, 10),
    (4, 6, 8),
    (4, 7, 8),
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None:
        if type(profile) is not str:
            raise ValueError("scene_profile must be a string")
        if profile not in SCENE_PROFILES:
            raise ValueError(
                "scene_profile must be one of " + ", ".join(SCENE_PROFILES)
            )


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return None, ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be non-empty and rectangular"]
    cooked: list[list[int]] = []
    for row in grid:
        cooked_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, ["grid cells must be literal ARC integers 0..9"]
            cooked_row.append(value)
        cooked.append(cooked_row)
    return cooked, []


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    cooked, errors = _coerce_grid(grid)
    if errors:
        return None, errors
    assert cooked is not None
    height, width = len(cooked), len(cooked[0])
    if not 4 <= height <= 5 or not 6 <= width <= 7:
        errors.append(f"task-like dimensions must be 4..5 by 6..7; found {height}x{width}")

    active_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(cooked):
        occupied = [index for index, value in enumerate(row) if value != 0]
        if not occupied:
            continue
        if len(occupied) < 3:
            errors.append(
                f"row {row_index} must contain at least three non-zero cells; found {len(occupied)}"
            )
        values = [row[index] for index in occupied]
        active_rows.append(
            {
                "row": row_index,
                "occupied": tuple(occupied),
                "values": tuple(values),
                "leader": values[0],
                "uniform": len(set(values)) == 1,
                "gapped": occupied != list(range(occupied[0], occupied[-1] + 1)),
            }
        )

    if len(active_rows) != 3:
        errors.append(f"expected exactly three active rows; found {len(active_rows)}")
    if active_rows and len({row["leader"] for row in active_rows}) < 2:
        errors.append("expected at least two distinct row-leader colors")
    if active_rows and not any(
        any(value != row["leader"] for value in row["values"][1:])
        for row in active_rows
    ):
        errors.append("no row has a visible non-leader color to recolor")
    if active_rows and not any(row["gapped"] for row in active_rows):
        errors.append("no active row contains an internal background gap")

    palette_size = len({value for row in cooked for value in row})
    if not 8 <= palette_size <= 10:
        errors.append(f"task-like palette size must be 8..10; found {palette_size}")

    if errors:
        return None, errors
    return {
        "grid": cooked,
        "height": height,
        "width": width,
        "active_rows": active_rows,
        "palette_size": palette_size,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the task-linked training grammar."""
    del difficulty, meta
    _analysis, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the lawful grammar and one of the exact canonical profiles."""
    analysis, errors = _analyze(grid)
    if errors:
        return errors
    assert analysis is not None
    profile = (analysis["height"], analysis["width"], analysis["palette_size"])
    if profile not in _CANONICAL_PROFILES:
        return [f"shape/palette profile {profile} is outside canonical support"]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    cooked, errors = _coerce_grid(grid)
    if errors:
        raise ValueError(errors[0])
    assert cooked is not None
    out: list[list[int]] = []
    for row in cooked:
        leader = next((value for value in row if value != 0), None)
        if leader is None:
            out.append([0 for _ in row])
        else:
            out.append([leader if value != 0 else 0 for value in row])
    return out


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact declared profile from returned pixels."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe profile on invalid grid: " + "; ".join(errors))
    assert analysis is not None
    profile = (
        "identity_scope"
        if any(row["uniform"] for row in analysis["active_rows"])
        else "mixed_scope"
    )
    return {"scene_profile": profile}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Alternate profiles so every three-example lesson sees both."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _profile_tuple(sample_index: int, difficulty) -> tuple[int, int, int]:
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    return _CANONICAL_PROFILES[(int(sample_index) + offsets[difficulty]) % len(_CANONICAL_PROFILES)]


def _choose_columns(rng, width: int, count: int, *, sparse: bool = False) -> list[int]:
    choices = list(combinations(range(width), count))
    if sparse:
        choices = [
            columns
            for columns in choices
            if columns[-1] - columns[0] + 1 > count
            and (columns[0] > 0 or columns[-1] < width - 1)
        ]
    if not choices:
        raise ValueError(f"cannot place {count} cells in width {width} with sparse={sparse}")
    return list(rng.choice(choices))


def _build_profile(ctx, profile: str, sample_index: int, difficulty) -> list[list[int]]:
    height, width, palette_size = _profile_tuple(sample_index, difficulty)
    color_count = palette_size - 1

    palette = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(palette)
    colors = palette[:color_count]

    # The decisive sparse row gives the true leader, modal color, and rightmost
    # color three different values. This also preserves internal background gaps.
    witness = ("witness", [colors[0], colors[1], colors[1], colors[2]], True)

    if profile == "identity_scope":
        uniform = ("uniform", [colors[3], colors[3], colors[3]], False)
        # Repeating the true leader while leaving later singleton colors ensures
        # the canonical "choose the rarest row color" shortcut is wrong.
        carrier_values = [colors[4], colors[4], *colors[5:]]
        carrier = ("anti_rarest", carrier_values, False)
        roles = [witness, uniform, carrier]
    else:
        anti_rarest = ("anti_rarest", [colors[3], colors[3], colors[4]], False)
        remaining = list(colors[5:])
        while len(remaining) < 3:
            remaining.append(remaining[0])
        roles = [
            witness,
            anti_rarest,
            ("carrier", remaining, False),
        ]

    layout_rng = ctx.draw_rng("layout")
    role_rng = ctx.draw_rng("role_order")
    active_rows = sorted(layout_rng.sample(range(height), 3))
    role_rng.shuffle(roles)

    grid = full_grid(height, width, 0)
    for row_index, (_name, values, sparse) in zip(active_rows, roles):
        columns = _choose_columns(layout_rng, width, len(values), sparse=sparse)
        for column, value in zip(columns, values):
            grid[row_index][column] = value

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise ValueError(f"constructed profile {profile!r} but observed {observed!r}")
    return [row[:] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the selected Racket rule owns output."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    return _build_profile(ctx, profile, int(sample_index), difficulty)


def _rival_rightmost(grid: list[list[int]]) -> list[list[int]]:
    out = []
    for row in grid:
        values = [value for value in row if value != 0]
        leader = values[-1] if values else None
        out.append([leader if value != 0 else 0 for value in row] if leader else [0 for _ in row])
    return out


def _rival_modal(grid: list[list[int]]) -> list[list[int]]:
    out = []
    for row in grid:
        values = [value for value in row if value != 0]
        if not values:
            out.append([0 for _ in row])
            continue
        counts = Counter(values)
        best = max(counts.values())
        leader = next(value for value in values if counts[value] == best)
        out.append([leader if value != 0 else 0 for value in row])
    return out


def _rival_rarest(grid: list[list[int]]) -> list[list[int]]:
    out = []
    for row in grid:
        values = [value for value in row if value != 0]
        if not values:
            out.append([0 for _ in row])
            continue
        counts = Counter(values)
        fewest = min(counts.values())
        leader = next(value for value in values if counts[value] == fewest)
        out.append([leader if value != 0 else 0 for value in row])
    return out


def _rival_global_leader(grid: list[list[int]]) -> list[list[int]]:
    leader = next((value for row in grid for value in row if value != 0), None)
    if leader is None:
        return [[0 for _ in row] for row in grid]
    return [[leader if value != 0 else 0 for value in row] for row in grid]


def _rival_fill_span(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        occupied = [index for index, value in enumerate(row) if value != 0]
        if occupied:
            leader = row[occupied[0]]
            for column in range(occupied[0], occupied[-1] + 1):
                out[row_index][column] = leader
    return out


def _rival_fill_row(grid: list[list[int]]) -> list[list[int]]:
    out = []
    for row in grid:
        leader = next((value for value in row if value != 0), None)
        out.append([leader for _ in row] if leader is not None else [0 for _ in row])
    return out


def _rival_per_component(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            leader = row[column]
            while column < len(row) and row[column] != 0:
                out[row_index][column] = leader
                column += 1
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "rightmost_nonzero": _rival_rightmost,
    "modal_row_color": _rival_modal,
    "rarest_row_color": _rival_rarest,
    "global_first_nonzero": _rival_global_leader,
    "fill_between_extremes": _rival_fill_span,
    "fill_entire_active_row": _rival_fill_row,
    "recolor_each_component": _rival_per_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "rarest_row_color": _rival_rarest,
}


def _differs_from(name: str):
    def predicate(grid) -> bool:
        try:
            return not self_check(grid) and SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
        except Exception:
            return False
    return predicate


SEMANTIC_WITNESSES = {
    "leader_not_rightmost": _differs_from("rightmost_nonzero"),
    "leader_not_mode": _differs_from("modal_row_color"),
    "leader_not_rarest": _differs_from("rarest_row_color"),
    "leaders_are_row_scoped": _differs_from("global_first_nonzero"),
    "background_gaps_are_preserved": _differs_from("fill_between_extremes"),
    "outside_background_is_preserved": _differs_from("fill_entire_active_row"),
    "leader_crosses_components": _differs_from("recolor_each_component"),
}
WITNESS_RIVALS = {
    "leader_not_rightmost": ["rightmost_nonzero"],
    "leader_not_mode": ["modal_row_color"],
    "leader_not_rarest": ["rarest_row_color"],
    "leaders_are_row_scoped": ["global_first_nonzero"],
    "background_gaps_are_preserved": ["fill_between_extremes"],
    "outside_background_is_preserved": ["fill_entire_active_row"],
    "leader_crosses_components": ["recolor_each_component"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate labels and require every declared rival to lose on a demo."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos[:EXAMPLES_NEEDED]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match row-leader recoloring")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append("query input is malformed: " + query_errors[0])
        elif query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match row-leader recoloring")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
