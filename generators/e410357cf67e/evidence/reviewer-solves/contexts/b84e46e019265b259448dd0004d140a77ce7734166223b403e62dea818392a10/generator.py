"""Constructive generator for e410357cf67e — reflected laser trail.

The unchanged Racket authority finds the first color-2 border emitter and sends
one beam inward.  Top/bottom edges take precedence at corners.  Empty cells on
the traversed ray become color 7; color 4 reflects ``(dr, dc)`` to
``(-dc, -dr)``, color 5 reflects it to ``(dc, dr)``, and color 8 stops it.

The five-profile schedule deliberately teaches corner priority, both mirror
handednesses, wall stopping, boundary stopping, and the irrelevance of off-path
mirrors.  Any four consecutive examples refute every declared shortcut, so a
four-demonstration lesson remains identifiable under query rotation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e410357cf67e"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "ca02c94ead8c"

SUMMARY = (
    "A single color-2 border emitter sends a laser inward. The laser paints "
    "empty cells 7, reflects differently at color-4 and color-5 mirrors, and "
    "stops at color-8 walls or the boundary. A five-profile cyclic curriculum "
    "covers corner precedence, one- and two-reflection paths, active walls, "
    "boundary exits, and off-route mirror decoys."
)

INVARIANTS = [
    "input is 7..16 rows by 9..16 columns with colors drawn from 0,2,4,5,8",
    "there is exactly one color-2 emitter on the border; corners are lawful",
    "at least one color-4 or color-5 mirror is present, though it may be off-route",
    "the canonical beam paints at least two empty cells and terminates at a wall or boundary",
]

SCHEDULE_PROFILES = (
    "corner_complex_wall",
    "complex_boundary",
    "corner_single_wall",
    "single_boundary",
    "straight_wall_decoys",
)
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor every other five-sample block; otherwise difficulty-aware rng",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor every other five-sample block; otherwise difficulty-aware rng",
        "valid": "9..16",
    },
    "profile": {
        "type": "str",
        "default": "sample_index mod 5",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_DIMS = {
    "corner_complex_wall": (8, 9),
    "complex_boundary": (7, 11),
    "corner_single_wall": (7, 10),
    "single_boundary": (8, 10),
    "straight_wall_decoys": (8, 9),
}
_DIFFICULTY_BOUNDS = {
    None: ((8, 12), (9, 13)),
    "easy": ((7, 9), (9, 11)),
    "medium": ((9, 12), (10, 13)),
    "hard": ((12, 16), (13, 16)),
}
_ALLOWED_INPUT_COLORS = {0, 2, 4, 5, 8}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the finite teaching profile selected by the cyclic schedule."""
    del seed
    if difficulty not in _DIFFICULTY_BOUNDS:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTY_BOUNDS:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        lo, hi = (7, 16) if name == "grid_h" else (9, 16)
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")

    profile = overrides.get("profile")
    if profile is not None and profile not in SCHEDULE_PROFILES:
        raise ValueError(f"unknown profile {profile!r}")


def _draw_dimensions(ctx, profile: str, overrides: dict[str, Any]) -> tuple[int, int]:
    anchor_block = (ctx.sample_index // LESSON_SCHEDULE_PERIOD) % 2 == 0
    anchor_h, anchor_w = _CANONICAL_DIMS[profile]
    (h_lo, h_hi), (w_lo, w_hi) = _DIFFICULTY_BOUNDS[ctx.difficulty]

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int_strict("grid_h", 7, 16)
    elif anchor_block:
        h = ctx.draw_int_strict("grid_h", anchor_h, anchor_h)
    else:
        h = ctx.draw_int_strict("grid_h", h_lo, h_hi)

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int_strict("grid_w", 9, 16)
    elif anchor_block:
        w = ctx.draw_int_strict("grid_w", anchor_w, anchor_w)
    else:
        w = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    return h, w


def _put(grid: list[list[int]], row: int, col: int, value: int) -> None:
    if grid[row][col] != 0:
        raise ValueError(f"constructive placement collision at {(row, col)}")
    grid[row][col] = value


def _corner_complex_wall(h: int, w: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mirror_row = rng.randint(3, h - 3)
    wall_row = rng.randint(1, mirror_row - 2)
    if rng.randrange(2) == 0:
        second_col = rng.randint(max(3, w // 2), w - 2)
        _put(grid, 0, 0, 2)
        _put(grid, mirror_row, 0, 5)
        _put(grid, mirror_row, second_col, 4)
        _put(grid, wall_row, second_col, 8)
    else:
        second_col = rng.randint(1, min(w - 4, (w - 1) // 2))
        _put(grid, 0, w - 1, 2)
        _put(grid, mirror_row, w - 1, 4)
        _put(grid, mirror_row, second_col, 5)
        _put(grid, wall_row, second_col, 8)
    return grid


def _complex_boundary(h: int, w: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mirror_row = rng.randint(2, h - 2)
    if rng.randrange(2) == 0:
        first_col = rng.randint(1, max(1, w // 3))
        second_col = rng.randint(max(first_col + 2, 2 * w // 3), w - 2)
        _put(grid, 0, first_col, 2)
        _put(grid, mirror_row, first_col, 5)
        _put(grid, mirror_row, second_col, 4)
    else:
        first_col = rng.randint(min(w - 2, 2 * w // 3), w - 2)
        second_col = rng.randint(1, min(first_col - 2, max(1, w // 3)))
        _put(grid, 0, first_col, 2)
        _put(grid, mirror_row, first_col, 4)
        _put(grid, mirror_row, second_col, 5)
    return grid


def _corner_single_wall(h: int, w: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mirror_row = rng.randint(2, h - 2)
    if rng.randrange(2) == 0:
        wall_col = rng.randint(max(3, w // 2), w - 2)
        _put(grid, 0, 0, 2)
        _put(grid, mirror_row, 0, 5)
        _put(grid, mirror_row, wall_col, 8)
    else:
        wall_col = rng.randint(1, min(w - 4, (w - 1) // 2))
        _put(grid, 0, w - 1, 2)
        _put(grid, mirror_row, w - 1, 4)
        _put(grid, mirror_row, wall_col, 8)
    return grid


def _single_boundary(h: int, w: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    mirror_row = rng.randint(2, h - 2)
    if rng.randrange(2) == 0:
        source_col = rng.randint(1, max(1, w // 3))
        _put(grid, 0, source_col, 2)
        _put(grid, mirror_row, source_col, 5)
    else:
        source_col = rng.randint(min(w - 2, 2 * w // 3), w - 2)
        _put(grid, 0, source_col, 2)
        _put(grid, mirror_row, source_col, 4)
    return grid


def _straight_wall_decoys(h: int, w: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    beam_row = rng.randint(1, h - 2)
    if rng.randrange(2) == 0:
        wall_col = rng.randint(max(3, w // 2), w - 2)
        _put(grid, beam_row, 0, 2)
        _put(grid, beam_row, wall_col, 8)
    else:
        wall_col = rng.randint(1, min(w - 4, (w - 1) // 2))
        _put(grid, beam_row, w - 1, 2)
        _put(grid, beam_row, wall_col, 8)

    candidates = [
        (row, col)
        for row in range(1, h - 1)
        for col in range(1, w - 1)
        if row != beam_row
    ]
    first, second = rng.sample(candidates, 2)
    _put(grid, first[0], first[1], 4)
    _put(grid, second[0], second[1], 5)
    return grid


_PROFILE_BUILDERS: dict[str, Callable[[int, int, Any], list[list[int]]]] = {
    "corner_complex_wall": _corner_complex_wall,
    "complex_boundary": _complex_boundary,
    "corner_single_wall": _corner_single_wall,
    "single_boundary": _single_boundary,
    "straight_wall_decoys": _straight_wall_decoys,
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, structurally valid teaching instance."""
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCHEDULE_PROFILES if overrides.get("profile") is not None else (scheduled,)
    profile = ctx.draw_choice("profile", profile_options)
    h, w = _draw_dimensions(ctx, profile, overrides)
    rng = ctx.draw_rng("layout")
    grid = _PROFILE_BUILDERS[profile](h, w, rng)
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid profile {profile!r}: {'; '.join(errors)}")
    return grid


def _rectangular_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty 2D list"]
    if any(not isinstance(row, list) for row in grid):
        return None, ["grid rows must be lists"]
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None, ["grid must be a nonempty rectangle"]
    return grid, []


def _source_and_direction(
    grid: list[list[int]], *, corner_mode: str = "canonical"
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    sources = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if not sources:
        return None, None
    row, col = sources[0]
    h, w = len(grid), len(grid[0])
    if corner_mode == "horizontal" and row in (0, h - 1) and col in (0, w - 1):
        return (row, col), ((0, 1) if col == 0 else (0, -1))
    if row == 0:
        direction = (1, 0)
    elif row == h - 1:
        direction = (-1, 0)
    elif col == 0:
        direction = (0, 1)
    else:
        direction = (0, -1)
    return (row, col), direction


def _bounce(value: int, dr: int, dc: int, mode: str) -> tuple[int, int]:
    kind = value
    if mode == "swap":
        kind = 5 if value == 4 else 4
    elif mode == "slash":
        kind = 4
    elif mode == "backslash":
        kind = 5
    elif mode == "ignore":
        return dr, dc
    elif mode != "canonical":
        raise ValueError(f"unknown mirror mode {mode!r}")
    if kind == 4:
        return -dc, -dr
    return dc, dr


def _apply_beam(
    grid: list[list[int]],
    *,
    mirror_mode: str = "canonical",
    ignore_walls: bool = False,
    stop_at_first_mirror: bool = False,
    corner_mode: str = "canonical",
) -> list[list[int]]:
    """Apply one beam variant without mutating the input."""
    source, direction = _source_and_direction(grid, corner_mode=corner_mode)
    output = deepcopy(grid)
    if source is None or direction is None:
        return output
    h, w = len(grid), len(grid[0])
    row, col = source
    dr, dc = direction
    fuel = 4 * h * w
    while fuel > 0:
        fuel -= 1
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < h and 0 <= next_col < w):
            break
        value = grid[next_row][next_col]
        if value == 8 and not ignore_walls:
            break
        if value in (4, 5):
            if stop_at_first_mirror:
                break
            dr, dc = _bounce(value, dr, dc, mirror_mode)
        elif value == 0:
            output[next_row][next_col] = 7
        row, col = next_row, next_col
    return output


def _analysis(grid: Any) -> dict[str, Any]:
    """Trace the canonical beam and expose structural facts for audits/tests."""
    checked, shape_errors = _rectangular_grid(grid)
    facts: dict[str, Any] = {
        "errors": list(shape_errors),
        "height": 0,
        "width": 0,
        "source": None,
        "corner_source": False,
        "path": [],
        "hit_mirrors": [],
        "mirrors": [],
        "walls": [],
        "termination": None,
        "active_wall": None,
    }
    if checked is None:
        return facts
    h, w = len(checked), len(checked[0])
    facts["height"], facts["width"] = h, w
    sources = [
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value == 2
    ]
    facts["mirrors"] = [
        (row, col, value)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value in (4, 5)
    ]
    facts["walls"] = [
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value == 8
    ]
    if len(sources) != 1:
        facts["errors"].append(f"expected exactly one color-2 emitter, got {len(sources)}")
        return facts
    source, direction = _source_and_direction(checked)
    assert source is not None and direction is not None
    facts["source"] = source
    facts["corner_source"] = source[0] in (0, h - 1) and source[1] in (0, w - 1)
    row, col = source
    dr, dc = direction
    seen: set[tuple[int, int, int, int]] = set()
    for _step in range(4 * h * w):
        state = (row, col, dr, dc)
        if state in seen:
            facts["termination"] = "loop"
            facts["errors"].append("beam enters a repeated directional state")
            return facts
        seen.add(state)
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < h and 0 <= next_col < w):
            facts["termination"] = "boundary"
            return facts
        value = checked[next_row][next_col]
        if value == 8:
            facts["termination"] = "wall"
            facts["active_wall"] = (next_row, next_col)
            return facts
        if value in (4, 5):
            facts["hit_mirrors"].append((next_row, next_col, value))
            dr, dc = _bounce(value, dr, dc, "canonical")
        elif value == 0:
            facts["path"].append((next_row, next_col))
        row, col = next_row, next_col
    facts["termination"] = "fuel"
    facts["errors"].append("beam exhausted its canonical fuel bound")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful canonical beam grammar, including straight cases."""
    del difficulty, meta
    checked, errors = _rectangular_grid(grid)
    if checked is None:
        return errors
    h, w = len(checked), len(checked[0])
    if not 7 <= h <= 16:
        errors.append(f"input height must be in 7..16, got {h}")
    if not 9 <= w <= 16:
        errors.append(f"input width must be in 9..16, got {w}")
    invalid = [
        value
        for row in checked
        for value in row
        if type(value) is not int or value not in _ALLOWED_INPUT_COLORS
    ]
    if invalid:
        errors.append("input cells must be integer colors from {0,2,4,5,8}; color 7 is output-only")
        return errors

    sources = [
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(sources) != 1:
        errors.append(f"expected exactly one color-2 emitter, got {len(sources)}")
        return errors
    source_row, source_col = sources[0]
    if source_row not in (0, h - 1) and source_col not in (0, w - 1):
        errors.append("color-2 emitter must be on the border")
    mirror_count = sum(value in (4, 5) for row in checked for value in row)
    if mirror_count < 1:
        errors.append("expected at least one color-4 or color-5 mirror")

    trace = _analysis(checked)
    errors.extend(trace["errors"])
    if len(trace["path"]) < 2:
        errors.append("canonical beam must paint at least two empty cells")
    if trace["termination"] not in ("wall", "boundary"):
        errors.append(f"canonical beam must terminate at a wall or boundary, got {trace['termination']!r}")
    return list(dict.fromkeys(errors))


def strict_canonical_like(grid) -> list[str]:
    """Return [] for the canonical-scale, canonical-palette beam manifold."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Executable Python mirror; the unchanged Racket program is authoritative."""
    checked, errors = _rectangular_grid(grid)
    if checked is None:
        raise ValueError(errors[0])
    return _apply_beam(checked)


def _ignore_walls_rival(grid):
    return _apply_beam(grid, ignore_walls=True)


def _ignore_mirrors_rival(grid):
    return _apply_beam(grid, mirror_mode="ignore")


def _swap_mirrors_rival(grid):
    return _apply_beam(grid, mirror_mode="swap")


def _both_slash_rival(grid):
    return _apply_beam(grid, mirror_mode="slash")


def _both_backslash_rival(grid):
    return _apply_beam(grid, mirror_mode="backslash")


def _stop_at_first_mirror_rival(grid):
    return _apply_beam(grid, stop_at_first_mirror=True)


def _horizontal_corner_priority_rival(grid):
    return _apply_beam(grid, corner_mode="horizontal")


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_walls": _ignore_walls_rival,
    "ignore_mirrors": _ignore_mirrors_rival,
    "swap_mirrors": _swap_mirrors_rival,
    "treat_both_mirrors_as_slash": _both_slash_rival,
    "treat_both_mirrors_as_backslash": _both_backslash_rival,
    "stop_at_first_mirror": _stop_at_first_mirror_rival,
    "horizontal_corner_priority": _horizontal_corner_priority_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# Every canonical label leaves its only wall off-route, so wall-ignorance is a
# genuine shortcut that the active-wall generated profiles must break.
CANONICAL_SHORTCUTS = {"ignore_walls": _ignore_walls_rival}


def _differs(grid: Any, rival_names: tuple[str, ...]) -> bool:
    truth = rule_mirror(grid)
    return all(SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


def _active_wall_witness(grid: Any) -> bool:
    return _analysis(grid)["termination"] == "wall" and _differs(grid, ("ignore_walls",))


def _reflection_witness(grid: Any) -> bool:
    return bool(_analysis(grid)["hit_mirrors"]) and _differs(
        grid, ("ignore_mirrors", "stop_at_first_mirror")
    )


def _handedness_witness(grid: Any) -> bool:
    kinds = {kind for _row, _col, kind in _analysis(grid)["hit_mirrors"]}
    return kinds == {4, 5} and _differs(
        grid,
        (
            "swap_mirrors",
            "treat_both_mirrors_as_slash",
            "treat_both_mirrors_as_backslash",
        ),
    )


def _corner_priority_witness(grid: Any) -> bool:
    return _analysis(grid)["corner_source"] and _differs(
        grid, ("horizontal_corner_priority",)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "active_wall": _active_wall_witness,
    "reflection": _reflection_witness,
    "mirror_handedness": _handedness_witness,
    "corner_priority": _corner_priority_witness,
}
WITNESS_RIVALS = {
    "active_wall": ["ignore_walls"],
    "reflection": ["ignore_mirrors", "stop_at_first_mirror"],
    "mirror_handedness": [
        "swap_mirrors",
        "treat_both_mirrors_as_slash",
        "treat_both_mirrors_as_backslash",
    ],
    "corner_priority": ["horizontal_corner_priority"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Check one lesson against the finite declared-rival contract."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"demo {index} malformed: {findings[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match the reflected-laser rule")
            continue
        valid_demos.append(pair)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input pair")
    else:
        findings = self_check(query["input"])
        if findings:
            reasons.append(f"query malformed: {findings[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the reflected-laser rule")
    return reasons


def _profile_from_analysis(facts: dict[str, Any]) -> str:
    corner = facts["corner_source"]
    hits = len(facts["hit_mirrors"])
    termination = facts["termination"]
    mirror_count = len(facts["mirrors"])
    signatures = {
        (True, 2, "wall", 2): "corner_complex_wall",
        (False, 2, "boundary", 2): "complex_boundary",
        (True, 1, "wall", 1): "corner_single_wall",
        (False, 1, "boundary", 1): "single_boundary",
        (False, 0, "wall", 2): "straight_wall_decoys",
    }
    signature = (corner, hits, termination, mirror_count)
    if signature not in signatures:
        raise ValueError(f"grid does not identify one declared profile: {signature!r}")
    return signatures[signature]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover all exact declared axes from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = _analysis(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "profile": _profile_from_analysis(facts),
    }


MIN_STRICT_FRAC = 0.95
