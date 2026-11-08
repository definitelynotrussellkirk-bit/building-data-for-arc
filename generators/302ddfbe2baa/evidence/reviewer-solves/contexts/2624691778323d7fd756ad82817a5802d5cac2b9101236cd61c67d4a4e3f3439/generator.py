"""Curriculum generator for ARC task 302ddfbe2baa (Rightward Ray Paint).

Every yellow (4) emitter paints cyan (8) into zero-valued cells to its
right.  The scan passes through other non-maroon colors, preserves every
nonzero cell, and stops immediately before the first maroon (9) cell or at
the right edge.

The canonical demonstrations contain exactly three emitters, no distractor
colors, no left-side maroons, and at most one maroon to the right of an
emitter.  Those examples therefore admit several plausible shortcuts.  The
three-slot curriculum below deliberately cycles through a canonical anchor,
a pass-through distractor probe, and a multi-blocker/direction probe.  Every
three consecutive generated demonstrations refute all named canonical
shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "302ddfbe2baa"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "923c6879d312"
SUMMARY = (
    "Yellow emitters paint cyan rightward through zero cells, passing through "
    "other colors and stopping before the first maroon blocker or the edge."
)

BACKGROUND = 0
DISTRACTOR = 2
EMITTER = 4
RAY = 8
BLOCKER = 9
ALLOWED_INPUT_COLORS = frozenset((BACKGROUND, DISTRACTOR, EMITTER, BLOCKER))

SCENE_KINDS = (
    "canonical",
    "pass_through_distractor",
    "multi_blocker",
)
SCHEDULE_PROFILES = SCENE_KINDS
CANONICAL_SHAPES = ((6, 10), (7, 11), (6, 12))
_CANONICAL_SHAPE_BY_BAND = {
    "easy": (6, 10),
    "medium": (7, 11),
    "hard": (6, 12),
}

INVARIANTS = [
    "the grid is rectangular with height 6..10 and width 10..14",
    "the input contains 1..5 yellow (4) emitters in distinct rows and at least one maroon (9) blocker",
    "every nonzero input cell lies in a row containing exactly one emitter",
    "every emitter has at least one visible zero cell to its right before the first maroon or edge",
    "canonical scenes use only 0/4/9 and have no left blocker or second right blocker",
    "pass-through probes place a non-maroon distractor in a live rightward ray",
    "multi-blocker probes make the nearer maroon lie left while two maroons lie right",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical band shape",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical band shape",
        "valid": "10..14",
    },
    "emitter_count": {
        "type": "int",
        "default": "three-slot teaching schedule",
        "valid": "1..5",
    },
    "scene_kind": {
        "type": "str",
        "default": "canonical / pass-through / multi-blocker cycle",
        "valid": "|".join(SCENE_KINDS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if type(difficulty) is not str or difficulty not in _CANONICAL_SHAPE_BY_BAND:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return difficulty


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(normalized) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for key, lo, hi in (
        ("grid_h", 6, 10),
        ("grid_w", 10, 14),
        ("emitter_count", 1, 5),
    ):
        if key not in normalized:
            continue
        value = normalized[key]
        if type(value) is not int:
            raise TypeError(f"{key} must be an exact int, got {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{key}={value} outside [{lo}, {hi}]")

    if "scene_kind" in normalized:
        value = normalized["scene_kind"]
        if type(value) is not str:
            raise TypeError(f"scene_kind must be str, got {type(value).__name__}")
        if value not in SCENE_KINDS:
            raise ValueError(
                f"scene_kind={value!r} not in {', '.join(SCENE_KINDS)}"
            )
    return normalized


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic three-slot lesson profile."""
    del seed
    _band(difficulty)
    if type(sample_index) is not int or isinstance(sample_index, bool):
        raise TypeError("sample_index must be an exact int")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_emitter_count(sample_index: int, scene_kind: str) -> int:
    cycle = sample_index // len(SCHEDULE_PROFILES)
    if scene_kind == "canonical":
        return 3
    if scene_kind == "pass_through_distractor":
        return 4 + (cycle % 2)
    return 1 + (cycle % 3)


def _draw_dimensions(ctx, overrides: dict[str, Any], band: str) -> tuple[int, int]:
    default_h, default_w = _CANONICAL_SHAPE_BY_BAND[band]
    h = int(
        ctx.draw_int("grid_h", 6, 10)
        if "grid_h" in overrides
        else ctx.draw_int("grid_h", default_h, default_h)
    )
    w = int(
        ctx.draw_int("grid_w", 10, 14)
        if "grid_w" in overrides
        else ctx.draw_int("grid_w", default_w, default_w)
    )
    return h, w


def _draw_scene_kind(ctx, overrides: dict[str, Any], profile: str) -> str:
    if "scene_kind" in overrides:
        return str(ctx.draw_choice("scene_kind", SCENE_KINDS))
    return str(ctx.draw_choice("scene_kind", (profile,)))


def _draw_emitter_count(
    ctx,
    overrides: dict[str, Any],
    sample_index: int,
    scene_kind: str,
) -> int:
    if "emitter_count" in overrides:
        return int(ctx.draw_int("emitter_count", 1, 5))
    scheduled = _scheduled_emitter_count(sample_index, scene_kind)
    return int(ctx.draw_int("emitter_count", scheduled, scheduled))


def _ordinary_block_flags(count: int, rng) -> list[bool]:
    if count == 1:
        # A lone unblocked emitter is a shape-blind singleton impostor.  The
        # selected teaching grammar keeps at least one maroon anchor in every
        # input while still allowing other emitter rows to run to the edge.
        return [True]
    flags = [index % 2 == 0 for index in range(count)]
    rng.shuffle(flags)
    return flags


def _place_ordinary_row(
    grid: list[list[int]],
    row: int,
    source_col: int,
    blocked: bool,
    rng,
) -> None:
    width = len(grid[0])
    grid[row][source_col] = EMITTER
    if blocked:
        grid[row][rng.randint(source_col + 2, width - 1)] = BLOCKER


def _build_canonical(h: int, w: int, count: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, BACKGROUND)
    rows = sorted(rng.sample(range(h), count))
    source_cols = rng.sample(range(0, w - 2), count)
    flags = _ordinary_block_flags(count, rng)
    for row, source_col, blocked in zip(rows, source_cols, flags):
        _place_ordinary_row(grid, row, source_col, blocked, rng)
    return grid


def _build_pass_through(h: int, w: int, count: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, BACKGROUND)
    rows = sorted(rng.sample(range(h), count))
    witness_row = rows[0]
    source_col = rng.randint(0, w - 6)
    grid[witness_row][source_col] = EMITTER
    grid[witness_row][source_col + 2] = DISTRACTOR
    grid[witness_row][source_col + 5] = BLOCKER

    flags = _ordinary_block_flags(max(0, count - 1), rng)
    for row, blocked in zip(rows[1:], flags):
        ordinary_source = rng.randint(0, w - 3)
        _place_ordinary_row(grid, row, ordinary_source, blocked, rng)
    return grid


def _build_multi_blocker(h: int, w: int, count: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, BACKGROUND)
    rows = sorted(rng.sample(range(h), count))
    witness_row = rows[0]
    source_col = rng.randint(3, w - 7)
    grid[witness_row][source_col - 2] = BLOCKER
    grid[witness_row][source_col] = EMITTER
    grid[witness_row][source_col + 3] = BLOCKER
    grid[witness_row][source_col + 6] = BLOCKER

    flags = _ordinary_block_flags(max(0, count - 1), rng)
    for row, blocked in zip(rows[1:], flags):
        ordinary_source = rng.randint(0, w - 3)
        _place_ordinary_row(grid, row, ordinary_source, blocked, rng)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid with exact, observable overrides."""
    band = _band(difficulty)
    normalized = _normalize_overrides(overrides)
    if type(sample_index) is not int or isinstance(sample_index, bool):
        raise TypeError("sample_index must be an exact int")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    h, w = _draw_dimensions(ctx, normalized, band)
    scene_kind = _draw_scene_kind(ctx, normalized, profile)
    emitter_count = _draw_emitter_count(
        ctx, normalized, sample_index, scene_kind
    )
    if emitter_count > h:
        raise ValueError(
            f"emitter_count={emitter_count} cannot fit in {h} distinct rows"
        )

    rng = ctx.draw_rng("layout")
    if scene_kind == "canonical":
        grid = _build_canonical(h, w, emitter_count, rng)
    elif scene_kind == "pass_through_distractor":
        grid = _build_pass_through(h, w, emitter_count, rng)
    else:
        grid = _build_multi_blocker(h, w, emitter_count, rng)

    errors = self_check(grid, meta={"overrides": normalized})
    if errors:
        raise AssertionError("generated invalid input: " + "; ".join(errors))
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Structural validation and exact pixel observability
# ---------------------------------------------------------------------------


def _rectangular_grid_errors(grid: Any) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"], len(grid), 0
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)):
            errors.append(f"row {row_index} is not a sequence")
            continue
        if len(row) != width:
            errors.append(f"row {row_index} has width {len(row)}, expected {width}")
    if errors:
        return errors, len(grid), width
    return [], len(grid), width


def _positions(grid: Sequence[Sequence[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _row_facts(row: Sequence[int]) -> dict[str, Any]:
    emitters = [col for col, value in enumerate(row) if value == EMITTER]
    source = emitters[0] if len(emitters) == 1 else None
    maroons = [col for col, value in enumerate(row) if value == BLOCKER]
    distractors = [col for col, value in enumerate(row) if value == DISTRACTOR]
    return {
        "emitters": emitters,
        "source": source,
        "maroons": maroons,
        "distractors": distractors,
        "left_maroons": [] if source is None else [col for col in maroons if col < source],
        "right_maroons": [] if source is None else [col for col in maroons if col > source],
    }


def _classify_scene_from_rows(row_facts: Sequence[dict[str, Any]]) -> str:
    if any(facts["distractors"] for facts in row_facts):
        return "pass_through_distractor"
    if any(facts["left_maroons"] and len(facts["right_maroons"]) >= 2 for facts in row_facts):
        return "multi_blocker"
    return "canonical"


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors, h, w = _rectangular_grid_errors(grid)
    facts: dict[str, Any] = {
        "grid_h": h,
        "grid_w": w,
        "emitters": [],
        "row_facts": [],
        "scene_kind": None,
    }
    if errors:
        return {"errors": errors, "facts": facts}

    if not 6 <= h <= 10:
        errors.append(f"grid height {h} outside 6..10")
    if not 10 <= w <= 14:
        errors.append(f"grid width {w} outside 10..14")

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an exact int"
                )
            elif value not in ALLOWED_INPUT_COLORS:
                errors.append(
                    f"cell ({row_index},{col_index}) uses unsupported input color {value}"
                )

    emitters = _positions(grid, EMITTER)
    facts["emitters"] = emitters
    if not 1 <= len(emitters) <= 5:
        errors.append(f"expected 1..5 emitters, found {len(emitters)}")
    if not _positions(grid, BLOCKER):
        errors.append("input must contain at least one maroon blocker")

    row_facts = [_row_facts(row) for row in grid]
    facts["row_facts"] = row_facts
    for row_index, (row, row_info) in enumerate(zip(grid, row_facts)):
        nonzero = [col for col, value in enumerate(row) if value != BACKGROUND]
        if not nonzero:
            continue
        if len(row_info["emitters"]) != 1:
            errors.append(
                f"active row {row_index} must contain exactly one emitter"
            )
            continue
        source = int(row_info["source"])
        stop = min(row_info["right_maroons"], default=w)
        live_zeros = [
            col for col in range(source + 1, stop) if row[col] == BACKGROUND
        ]
        if not live_zeros:
            errors.append(
                f"emitter in row {row_index} has no visible rightward zero cell"
            )

    scene_kind = _classify_scene_from_rows(row_facts)
    facts["scene_kind"] = scene_kind

    if scene_kind == "canonical":
        for row_index, row_info in enumerate(row_facts):
            if not row_info["emitters"]:
                continue
            if row_info["distractors"]:
                errors.append(f"canonical row {row_index} contains a distractor")
            if row_info["left_maroons"]:
                errors.append(f"canonical row {row_index} contains a left maroon")
            if len(row_info["right_maroons"]) > 1:
                errors.append(
                    f"canonical row {row_index} contains multiple right maroons"
                )

    elif scene_kind == "pass_through_distractor":
        witness_count = 0
        for row_index, (row, row_info) in enumerate(zip(grid, row_facts)):
            if not row_info["emitters"]:
                continue
            if row_info["left_maroons"]:
                errors.append(
                    f"pass-through row {row_index} contains a left maroon"
                )
            if len(row_info["right_maroons"]) > 1:
                errors.append(
                    f"pass-through row {row_index} contains multiple right maroons"
                )
            source = int(row_info["source"])
            stop = min(row_info["right_maroons"], default=w)
            for distractor_col in row_info["distractors"]:
                if not source < distractor_col < stop:
                    errors.append(
                        f"distractor at ({row_index},{distractor_col}) is not on a live rightward ray"
                    )
                    continue
                if any(
                    row[col] == BACKGROUND
                    for col in range(distractor_col + 1, stop)
                ):
                    witness_count += 1
        if witness_count == 0:
            errors.append(
                "pass-through scene lacks a distractor with observable ray cells beyond it"
            )

    else:  # multi_blocker
        witness_count = 0
        for row_index, (row, row_info) in enumerate(zip(grid, row_facts)):
            if not row_info["emitters"]:
                continue
            source = int(row_info["source"])
            left = row_info["left_maroons"]
            right = row_info["right_maroons"]
            if left or len(right) > 1:
                if not left or len(right) < 2:
                    errors.append(
                        f"multi-blocker row {row_index} must have a left maroon and two right maroons"
                    )
                    continue
                nearest_left = max(left)
                first_right, second_right = right[0], right[1]
                if source - nearest_left >= first_right - source:
                    errors.append(
                        f"multi-blocker row {row_index} does not make the left maroon strictly nearer"
                    )
                if not any(
                    row[col] == BACKGROUND
                    for col in range(source + 1, first_right)
                ):
                    errors.append(
                        f"multi-blocker row {row_index} has no intended right-ray cell"
                    )
                if not any(
                    row[col] == BACKGROUND
                    for col in range(first_right + 1, second_right)
                ):
                    errors.append(
                        f"multi-blocker row {row_index} does not expose first-vs-rightmost stopping"
                    )
                if not any(
                    row[col] == BACKGROUND
                    for col in range(nearest_left + 1, source)
                ):
                    errors.append(
                        f"multi-blocker row {row_index} does not expose direction choice"
                    )
                witness_count += 1
        if witness_count != 1:
            errors.append(
                f"multi-blocker scene must contain exactly one structured witness row, found {witness_count}"
            )

    return {"errors": errors, "facts": facts}


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe invalid ray scene: " + "; ".join(analysis["errors"])
        )
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "emitter_count": len(facts["emitters"]),
        "scene_kind": facts["scene_kind"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        for axis in AXES:
            if axis in meta:
                requested[axis] = meta[axis]
    if requested:
        observed_values = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis not in AXES or expected is None:
                continue
            if observed_values[axis] != expected:
                errors.append(
                    f"override {axis}={expected!r} was not realized; "
                    f"observed {observed_values[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    observed_values = observe_overrides(grid)
    strict_errors: list[str] = []
    if (observed_values["grid_h"], observed_values["grid_w"]) not in CANONICAL_SHAPES:
        strict_errors.append("shape is not one of the canonical 6x10, 7x11, or 6x12 canvases")
    if observed_values["emitter_count"] != 3:
        strict_errors.append("canonical inputs contain exactly three emitters")
    if observed_values["scene_kind"] != "canonical":
        strict_errors.append("canonical inputs contain no distractor or multi-blocker probe")
    source_cols = [col for _, col in _positions(grid, EMITTER)]
    if len(set(source_cols)) != len(source_cols):
        strict_errors.append("canonical emitters occupy distinct columns")
    return strict_errors


# ---------------------------------------------------------------------------
# Executable rule mirror, canonical shortcuts, and witness predicates
# ---------------------------------------------------------------------------


def _ray_with_policy(
    grid: Sequence[Sequence[int]],
    emitters: Sequence[tuple[int, int]],
    *,
    direction_for: Callable[[int, int], int],
    stop_for: Callable[[int, Sequence[int], int, int], int | None],
    stop_at_any_nonzero: bool = False,
) -> list[list[int]]:
    shape_errors, _h, width = _rectangular_grid_errors(grid)
    if shape_errors:
        raise ValueError("invalid grid: " + "; ".join(shape_errors))
    out = [list(row) for row in grid]
    for row, source_col in emitters:
        direction = direction_for(row, source_col)
        stop_col = stop_for(row, grid[row], source_col, direction)
        col = source_col + direction
        while 0 <= col < width:
            value = grid[row][col]
            if stop_col is not None and col == stop_col:
                break
            if stop_at_any_nonzero and value != BACKGROUND:
                break
            if value == BLOCKER and stop_col is None:
                break
            if value == BACKGROUND:
                out[row][col] = RAY
            col += direction
    return out


def _first_right_maroon(
    row_index: int, row: Sequence[int], source_col: int, direction: int
) -> int | None:
    del row_index, direction
    right = [col for col, value in enumerate(row) if value == BLOCKER and col > source_col]
    return min(right) if right else None


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket authority."""
    return _ray_with_policy(
        grid,
        sorted(_positions(grid, EMITTER)),
        direction_for=lambda row, col: 1,
        stop_for=_first_right_maroon,
    )


def _stop_at_any_nonzero(grid):
    return _ray_with_policy(
        grid,
        sorted(_positions(grid, EMITTER)),
        direction_for=lambda row, col: 1,
        stop_for=lambda row_index, row, source, direction: None,
        stop_at_any_nonzero=True,
    )


def _rightmost_maroon(grid):
    def stop(row_index, row, source_col, direction):
        del row_index, direction
        right = [
            col
            for col, value in enumerate(row)
            if value == BLOCKER and col > source_col
        ]
        return max(right) if right else None

    return _ray_with_policy(
        grid,
        sorted(_positions(grid, EMITTER)),
        direction_for=lambda row, col: 1,
        stop_for=stop,
    )


def _nearest_maroon_direction(grid):
    chosen: dict[tuple[int, int], tuple[int, int | None]] = {}
    for row, source_col in sorted(_positions(grid, EMITTER)):
        maroons = [
            col for col, value in enumerate(grid[row]) if value == BLOCKER
        ]
        if not maroons:
            chosen[(row, source_col)] = (1, None)
            continue
        target = min(maroons, key=lambda col: (abs(col - source_col), col))
        chosen[(row, source_col)] = (1 if target > source_col else -1, target)

    return _ray_with_policy(
        grid,
        sorted(_positions(grid, EMITTER)),
        direction_for=lambda row, col: chosen[(row, col)][0],
        stop_for=lambda row, row_values, source_col, direction: chosen[
            (row, source_col)
        ][1],
    )


def _first_three_emitters(grid):
    return _ray_with_policy(
        grid,
        sorted(_positions(grid, EMITTER))[:3],
        direction_for=lambda row, col: 1,
        stop_for=_first_right_maroon,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "stop_at_any_nonzero": _stop_at_any_nonzero,
    "rightmost_maroon": _rightmost_maroon,
    "toward_nearest_maroon": _nearest_maroon_direction,
    "first_three_emitters": _first_three_emitters,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid: Any, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError, StopIteration):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "passes_through_non_maroon": lambda grid: _rival_differs(
        grid, "stop_at_any_nonzero"
    ),
    "every_emitter_matters": lambda grid: _rival_differs(
        grid, "first_three_emitters"
    ),
    "first_right_maroon_stops": lambda grid: _rival_differs(
        grid, "rightmost_maroon"
    ),
    "rightward_not_nearest_maroon": lambda grid: _rival_differs(
        grid, "toward_nearest_maroon"
    ),
}
WITNESS_RIVALS = {
    "passes_through_non_maroon": ["stop_at_any_nonzero"],
    "every_emitter_matters": ["first_three_emitters"],
    "first_right_maroon_stops": ["rightmost_maroon"],
    "rightward_not_nearest_maroon": ["toward_nearest_maroon"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any named wrong rule that demos leave live on the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside the task domain: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the pinned rule")
            continue
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the task domain: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the pinned rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} survives every demonstration and changes the query answer"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small invalid fixtures used by the shared self-check power probe."""
    no_emitter = full_grid(6, 10, BACKGROUND)
    no_emitter[2][7] = BLOCKER

    adjacent_blocker = full_grid(6, 10, BACKGROUND)
    adjacent_blocker[2][3] = EMITTER
    adjacent_blocker[2][4] = BLOCKER

    stray_nonzero = full_grid(6, 10, BACKGROUND)
    stray_nonzero[2][2] = EMITTER
    stray_nonzero[2][7] = BLOCKER
    stray_nonzero[4][4] = DISTRACTOR

    ambiguous_left = full_grid(6, 10, BACKGROUND)
    ambiguous_left[2][1] = BLOCKER
    ambiguous_left[2][3] = EMITTER

    return [
        ("no_emitter", no_emitter),
        ("zero_length_ray", adjacent_blocker),
        ("stray_nonzero_row", stray_nonzero),
        ("unstructured_left_maroon", ambiguous_left),
    ]
