"""Generator for ARC task 5e0575c16ab4 (Fill the horizontal bridge).

The selected rule scans colors globally.  A color is extended only when it
appears exactly twice in the whole grid, both cells share a row, and every cell
strictly between the endpoints is zero.  The ordinary curriculum alternates
four profiles so every four-example lesson demonstrates the positive branch
and the three guards that the public examples leave ambiguous:

* canonical: only globally unique fillable endpoint pairs;
* global_repeat: the same color forms two row-local pairs (four cells total);
* blocked_bridge: an otherwise valid pair contains a foreign blocker;
* count_alignment: one vertical pair and one three-cell row are left alone.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5e0575c16ab4"
TASK_ID = "5e0575c16ab4"
VERSION = "2.0.0"
RULE_HASH = "8cad321146ee"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Globally unique same-color row endpoints with an empty bridge are filled. "
    "Scheduled distractor profiles teach the global count, blank-span, row-"
    "alignment, and exactly-two preconditions."
)

INVARIANTS = [
    "background is 0",
    "every ordinary grid has one or two globally unique fillable row pairs",
    "all fillable endpoint pairs have at least one zero strictly between them",
    "scheduled negative branches remain unchanged by the selected rule",
]

SCHEDULE_PROFILES = (
    "canonical",
    "global_repeat",
    "blocked_bridge",
    "count_alignment",
)
HELPFUL_TEXTURES = SCHEDULE_PROFILES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile/difficulty-aware rng with canonical anchors",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "profile/difficulty-aware rng with canonical anchors",
        "valid": "7..18",
    },
    "positive_pairs": {
        "type": "int",
        "default": "2 for canonical; difficulty-aware 1..2 otherwise",
        "valid": "1..2",
    },
    "profile": {
        "type": "str",
        "default": "four-example deterministic schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cycle profiles so every consecutive four examples cover all branches."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    values = dict(overrides)
    texture = values.pop("texture", None)
    legacy_pairs = values.pop("pairs", None)

    if legacy_pairs is not None:
        if "positive_pairs" in values and int(values["positive_pairs"]) != int(legacy_pairs):
            raise ValueError("pairs and positive_pairs overrides disagree")
        values["positive_pairs"] = legacy_pairs

    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        if "profile" in values and values["profile"] != texture:
            raise ValueError("texture and profile overrides disagree")
        values["profile"] = texture

    unknown = sorted(set(values) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    return values


def _difficulty_bounds(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (5, 7), (7, 10)
    if difficulty == "hard":
        return (9, 14), (12, 18)
    if difficulty in (None, "medium"):
        return (7, 11), (9, 14)
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _draw_profile(ctx, values: dict[str, Any], seed: int, sample_index: int, difficulty) -> str:
    if "profile" in values:
        return ctx.draw_choice("profile", SCHEDULE_PROFILES)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    return ctx.draw_choice("profile", (scheduled,))


def _draw_dimensions(ctx, values: dict[str, Any], profile: str, difficulty) -> tuple[int, int]:
    if "grid_h" in values:
        h = ctx.draw_int("grid_h", 5, 14)
    elif profile == "canonical":
        h_choices = (5, 8)
        chosen_h = h_choices[ctx.draw_rng("canonical_height").randrange(len(h_choices))]
        h = ctx.draw_int("grid_h", chosen_h, chosen_h)
    else:
        (h_lo, h_hi), _ = _difficulty_bounds(difficulty)
        h = ctx.draw_int("grid_h", h_lo, h_hi)

    if "grid_w" in values:
        w = ctx.draw_int("grid_w", 7, 18)
    elif profile == "canonical":
        w_choices = (7, 8, 9)
        chosen_w = w_choices[ctx.draw_rng("canonical_width").randrange(len(w_choices))]
        w = ctx.draw_int("grid_w", chosen_w, chosen_w)
    else:
        _, (w_lo, w_hi) = _difficulty_bounds(difficulty)
        w = ctx.draw_int("grid_w", w_lo, w_hi)
    return h, w


def _draw_positive_pairs(ctx, values: dict[str, Any], profile: str, difficulty) -> int:
    if "positive_pairs" in values:
        return ctx.draw_int("positive_pairs", 1, 2)
    if profile == "canonical" or difficulty == "hard":
        return ctx.draw_int("positive_pairs", 2, 2)
    return ctx.draw_int("positive_pairs", 1, 2)


def _span(
    w: int,
    rng,
    *,
    min_distance: int = 2,
    excluded_columns: frozenset[int] = frozenset(),
) -> tuple[int, int]:
    candidates = [
        (left, right)
        for left in range(w)
        for right in range(left + min_distance, w)
        if left not in excluded_columns and right not in excluded_columns
    ]
    if not candidates:
        raise ValueError(
            f"cannot place span of width {min_distance} in {w} columns "
            f"while excluding {sorted(excluded_columns)}"
        )
    return rng.choice(candidates)


def _paint_pair(
    grid: list[list[int]],
    row: int,
    color: int,
    w: int,
    rng,
    *,
    excluded_columns: frozenset[int] = frozenset(),
) -> None:
    left, right = _span(w, rng, excluded_columns=excluded_columns)
    grid[row][left] = color
    grid[row][right] = color


def _build_scene(
    h: int,
    w: int,
    positive_pairs: int,
    profile: str,
    rng,
) -> list[list[int]]:
    extra_rows = {
        "canonical": 0,
        "global_repeat": 2,
        "blocked_bridge": 1,
        "count_alignment": 3,
    }[profile]
    needed_rows = positive_pairs + extra_rows
    if needed_rows > h:
        raise ValueError(
            f"profile {profile!r} with {positive_pairs} positive pairs needs "
            f"{needed_rows} rows, got {h}"
        )

    rows = list(range(h))
    rng.shuffle(rows)
    positive_rows = rows[:positive_pairs]
    decoy_rows = rows[positive_pairs:needed_rows]

    needed_colors = positive_pairs + {
        "canonical": 0,
        "global_repeat": 1,
        "blocked_bridge": 2,
        "count_alignment": 2,
    }[profile]
    colors = rng.sample(range(1, 10), needed_colors)
    grid = full_grid(h, w, 0)

    reserved_vertical_column = None
    if profile == "count_alignment":
        reserved_vertical_column = rng.randrange(w)

    excluded_positive_columns = (
        frozenset((reserved_vertical_column,))
        if reserved_vertical_column is not None
        else frozenset()
    )
    for row, color in zip(positive_rows, colors[:positive_pairs]):
        _paint_pair(
            grid,
            row,
            color,
            w,
            rng,
            excluded_columns=excluded_positive_columns,
        )

    next_color = positive_pairs
    if profile == "global_repeat":
        repeated = colors[next_color]
        for row in decoy_rows:
            _paint_pair(grid, row, repeated, w, rng)

    elif profile == "blocked_bridge":
        pair_color = colors[next_color]
        blocker_color = colors[next_color + 1]
        row = decoy_rows[0]
        left, right = _span(w, rng)
        blocker = rng.randint(left + 1, right - 1)
        grid[row][left] = pair_color
        grid[row][blocker] = blocker_color
        grid[row][right] = pair_color

    elif profile == "count_alignment":
        vertical_color = colors[next_color]
        triple_color = colors[next_color + 1]
        # Any two rows chosen from three distinct rows can be made non-adjacent
        # by using the extremes of the three-row set.
        all_decoy_rows = sorted(decoy_rows)
        vertical_rows = (all_decoy_rows[0], all_decoy_rows[-1])
        triple_row = all_decoy_rows[1]
        assert reserved_vertical_column is not None
        column = reserved_vertical_column
        grid[vertical_rows[0]][column] = vertical_color
        grid[vertical_rows[1]][column] = vertical_color

        left, right = _span(
            w,
            rng,
            min_distance=4,
            excluded_columns=frozenset((column,)),
        )
        middle_candidates = [
            candidate
            for candidate in range(left + 1, right)
            if candidate != column
        ]
        if not middle_candidates:
            raise ValueError("triple span has no non-reserved middle column")
        middle = rng.choice(middle_candidates)
        grid[triple_row][left] = triple_color
        grid[triple_row][middle] = triple_color
        grid[triple_row][right] = triple_color

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=values,
    )
    profile = _draw_profile(ctx, values, seed, sample_index, difficulty)
    h, w = _draw_dimensions(ctx, values, profile, difficulty)
    positive_pairs = _draw_positive_pairs(ctx, values, profile, difficulty)
    return _build_scene(h, w, positive_pairs, profile, ctx.draw_rng("scene"))


def _by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result.setdefault(value, []).append((r, c))
    return result


def _blank_horizontal_bridge(grid, row: int, left: int, right: int) -> bool:
    return right - left >= 2 and all(grid[row][c] == 0 for c in range(left + 1, right))


def rule_mirror(grid):
    """Python test mirror; the selected canonical Racket rule is authoritative."""
    out = [row[:] for row in grid]
    for color, cells in _by_color(grid).items():
        if len(cells) != 2 or cells[0][0] != cells[1][0]:
            continue
        row = cells[0][0]
        left, right = sorted((cells[0][1], cells[1][1]))
        # The canonical rule also accepts adjacent endpoints (empty interior),
        # but they are identity examples.  Painting them remains behaviorally
        # correct; ordinary teaching examples require a real gap in self_check.
        if all(grid[row][c] == 0 for c in range(left + 1, right)):
            for c in range(left, right + 1):
                out[row][c] = color
    return out


def semantic_observables(grid) -> dict[str, Any]:
    h = len(grid) if isinstance(grid, list) else 0
    w = len(grid[0]) if h and isinstance(grid[0], list) else 0
    qualifying: list[int] = []
    repeated: list[int] = []
    blocked: list[int] = []
    vertical: list[int] = []
    triples: list[int] = []
    singletons: list[int] = []
    adjacent: list[int] = []
    other: list[int] = []

    if h and all(isinstance(row, list) and len(row) == w for row in grid):
        for color, cells in _by_color(grid).items():
            if len(cells) == 1:
                singletons.append(color)
                continue
            if len(cells) == 2:
                (r1, c1), (r2, c2) = cells
                if r1 == r2:
                    left, right = sorted((c1, c2))
                    if right - left == 1:
                        adjacent.append(color)
                    elif _blank_horizontal_bridge(grid, r1, left, right):
                        qualifying.append(color)
                    else:
                        blocked.append(color)
                elif c1 == c2 and abs(r1 - r2) >= 2:
                    vertical.append(color)
                else:
                    other.append(color)
                continue
            if len(cells) == 3 and len({r for r, _ in cells}) == 1:
                triples.append(color)
                continue
            if len(cells) == 4:
                rows: dict[int, list[int]] = {}
                for row, col in cells:
                    rows.setdefault(row, []).append(col)
                if len(rows) == 2 and all(len(cols) == 2 for cols in rows.values()):
                    lawful_pairs = True
                    for row, cols in rows.items():
                        left, right = sorted(cols)
                        lawful_pairs &= _blank_horizontal_bridge(grid, row, left, right)
                    if lawful_pairs:
                        repeated.append(color)
                        continue
            other.append(color)

    profile = None
    if qualifying and not any((repeated, blocked, vertical, triples, singletons, adjacent, other)):
        profile = "canonical"
    elif (
        qualifying
        and len(repeated) == 1
        and not any((blocked, vertical, triples, singletons, adjacent, other))
    ):
        profile = "global_repeat"
    elif (
        qualifying
        and len(blocked) == 1
        and len(singletons) == 1
        and not any((repeated, vertical, triples, adjacent, other))
    ):
        profile = "blocked_bridge"
    elif (
        qualifying
        and len(vertical) == 1
        and len(triples) == 1
        and not any((repeated, blocked, singletons, adjacent, other))
    ):
        profile = "count_alignment"

    negative_branches = []
    if repeated:
        negative_branches.append("global_count")
    if blocked:
        negative_branches.append("blank_bridge")
    if vertical:
        negative_branches.append("same_row")
    if triples:
        negative_branches.append("exactly_two")

    return {
        "grid_h": h,
        "grid_w": w,
        "positive_pairs": len(qualifying),
        "profile": profile,
        "qualifying_colors": tuple(sorted(qualifying)),
        "repeated_pair_colors": tuple(sorted(repeated)),
        "blocked_pair_colors": tuple(sorted(blocked)),
        "vertical_pair_colors": tuple(sorted(vertical)),
        "triple_colors": tuple(sorted(triples)),
        "singleton_colors": tuple(sorted(singletons)),
        "adjacent_pair_colors": tuple(sorted(adjacent)),
        "other_colors": tuple(sorted(other)),
        "negative_branches": tuple(negative_branches),
    }


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = semantic_observables(grid)
    profile = facts["profile"]
    if profile is None:
        raise ValueError("cannot observe profile")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "positive_pairs": facts["positive_pairs"],
        "profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate a recognizable, non-identity lesson from the selected rule."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty 2D list"]
    if any(not isinstance(row, list) for row in grid):
        return ["grid rows must be lists"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    h = len(grid)
    if not 5 <= h <= 14:
        errors.append(f"grid height must be in 5..14, got {h}")
    if not 7 <= width <= 18:
        errors.append(f"grid width must be in 7..18, got {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer colors 0..9")
    if errors:
        return errors

    facts = semantic_observables(grid)
    if not 1 <= facts["positive_pairs"] <= 2:
        errors.append(
            "grid must contain one or two globally unique fillable horizontal pairs"
        )
    if facts["profile"] not in SCHEDULE_PROFILES:
        errors.append("grid does not match a declared teaching profile")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] for a lawful input on the selected rule's teaching manifold."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _identity(grid):
    return [row[:] for row in grid]


def row_local_pairs(grid):
    """Shortcut: apply the pair rule independently in each row."""
    out = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append(col)
        for color, cols in positions.items():
            if len(cols) != 2:
                continue
            left, right = sorted(cols)
            if all(grid[row_index][c] == 0 for c in range(left + 1, right)):
                for c in range(left, right + 1):
                    out[row_index][c] = color
    return out


def ignore_blank_guard(grid):
    """Shortcut: ignore blockers between globally unique row endpoints."""
    out = [row[:] for row in grid]
    for color, cells in _by_color(grid).items():
        if len(cells) == 2 and cells[0][0] == cells[1][0]:
            row = cells[0][0]
            left, right = sorted((cells[0][1], cells[1][1]))
            for c in range(left, right + 1):
                out[row][c] = color
    return out


def connect_vertical_pairs(grid):
    """Shortcut: apply the horizontal rule and also bridge vertical pairs."""
    out = rule_mirror(grid)
    for color, cells in _by_color(grid).items():
        if len(cells) != 2 or cells[0][1] != cells[1][1]:
            continue
        top, bottom = sorted((cells[0][0], cells[1][0]))
        col = cells[0][1]
        if all(grid[r][col] == 0 for r in range(top + 1, bottom)):
            for r in range(top, bottom + 1):
                out[r][col] = color
    return out


def row_extremes_for_repeated_color(grid):
    """Shortcut: fill between row-wise color extremes whenever count >= 2."""
    out = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append(col)
        for color, cols in positions.items():
            if len(cols) < 2:
                continue
            left, right = min(cols), max(cols)
            for c in range(left, right + 1):
                out[row_index][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "row_local_pairs": row_local_pairs,
    "ignore_blank_guard": ignore_blank_guard,
    "connect_vertical_pairs": connect_vertical_pairs,
    "row_extremes_for_repeated_color": row_extremes_for_repeated_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "row_local_pairs",
        "ignore_blank_guard",
        "connect_vertical_pairs",
        "row_extremes_for_repeated_color",
    )
}


def _lawful_facts(grid) -> dict[str, Any] | None:
    return None if self_check(grid) else semantic_observables(grid)


def _has_positive(grid) -> bool:
    facts = _lawful_facts(grid)
    return bool(facts and facts["positive_pairs"] >= 1)


def _has_branch(branch: str):
    return lambda grid: bool(
        (facts := _lawful_facts(grid)) is not None
        and branch in facts["negative_branches"]
    )


SEMANTIC_WITNESSES = {
    "positive_fill_branch": _has_positive,
    "global_count_guard": _has_branch("global_count"),
    "blank_bridge_guard": _has_branch("blank_bridge"),
    "same_row_guard": _has_branch("same_row"),
    "exactly_two_guard": _has_branch("exactly_two"),
}
WITNESS_RIVALS = {
    "positive_fill_branch": ["identity"],
    "global_count_guard": ["row_local_pairs", "row_extremes_for_repeated_color"],
    "blank_bridge_guard": ["ignore_blank_guard"],
    "same_row_guard": ["connect_vertical_pairs"],
    "exactly_two_guard": ["row_extremes_for_repeated_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when any named rival survives demos but changes query."""
    reasons: list[str] = []
    prepared: list[tuple[list[list[int]], dict[str, list[list[int]]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        prepared.append(
            (
                pair["output"],
                {
                    name: competitor(pair["input"])
                    for name, competitor in LESSON_COMPETITORS.items()
                },
            )
        )
    if reasons:
        return sorted(set(reasons))

    if not isinstance(query, dict) or "input" not in query:
        return ["query is malformed"]
    query_errors = self_check(query["input"])
    if query_errors:
        return ["query input is invalid: " + "; ".join(query_errors)]

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(outputs[name] == expected for expected, outputs in prepared)
        if survives and competitor(query["input"]) != query_truth:
            reasons.append(
                f"competing rule {name!r} matches every demo but changes the query"
            )
    return sorted(reasons)
