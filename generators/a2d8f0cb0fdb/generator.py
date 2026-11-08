"""Generate legend-row recolor-mask lessons for task a2d8f0cb0fdb.

The selected Racket authority reads the FIRST nonzero cell of row 0 as the
output color.  It clears the entire grid, then recolors exactly the body cells
whose input value is blue (1).  Other nonzero body colors are distractors and
must disappear.

The four-position curriculum preserves canonical one-marker examples while
forcing two distinctions hidden by every public demonstration:

* first header nonzero, not last/only header nonzero;
* body value 1 only, not every nonzero body cell.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2d8f0cb0fdb"
TASK_ID = GENERATOR_ID
RULE_HASH = "b1048663f6a3"
VERSION = "2.0.0"
SUMMARY = (
    "Read the first nonzero color in row 0, clear the header and all distractors, "
    "and recolor exactly the blue (1) cells below the header with that color."
)

INVARIANTS = [
    "the input is a rectangular ARC grid with at least two rows",
    "row 0 contains at least one nonzero legend cell",
    "the body contains at least one blue (1) cell",
    "the first nonzero header color is the recolor target",
    "all output cells except recolored body 1s are black",
]

SCENE_PROFILES = (
    "canonical_anchor",
    "header_choice",
    "body_filter",
    "combined",
)
SCHEDULE_PROFILES = SCENE_PROFILES
_SCHEDULE = (
    "canonical_anchor",
    "header_choice",
    "body_filter",
    "canonical_anchor",
    "combined",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-position semantic curriculum",
        "valid": "|".join(SCENE_PROFILES),
    }
}

# The single exact axis has no incompatible combinations.  Declaring the empty
# matrix activates the strict override policy rather than legacy rejection
# acceptance.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

Grid = list[list[int]]

# (nonzero header cells, non-{0,1} body distractor cells)
_PROFILE_COUNTS = {
    "canonical_anchor": (1, 0),
    "header_choice": (3, 0),
    "body_filter": (1, 2),
    "combined": (3, 2),
}
_PROFILE_BY_COUNTS = {value: key for key, value in _PROFILE_COUNTS.items()}

# Every difficulty band retains an exact canonical (h,w,palette-size) anchor.
# The other profiles broaden scale while keeping the semantic schedule fixed.
_DIMENSIONS = {
    "easy": {
        "canonical_anchor": ((4, 5), (4, 6)),
        "header_choice": ((4, 6), (5, 6)),
        "body_filter": ((4, 6), (5, 6)),
        "combined": ((5, 6), (5, 7)),
    },
    "medium": {
        "canonical_anchor": ((4, 5), (4, 6)),
        "header_choice": ((5, 7), (6, 8)),
        "body_filter": ((5, 7), (6, 8)),
        "combined": ((6, 8), (7, 9)),
    },
    "hard": {
        "canonical_anchor": ((4, 5), (4, 6)),
        "header_choice": ((7, 9), (8, 10)),
        "body_filter": ((7, 9), (8, 10)),
        "combined": ((8, 10), (9, 12)),
    },
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the semantic role at this curriculum position."""
    del seed
    _band(difficulty)  # validate even though the role cycle is band-independent
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    return band


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule owns the label."""
    band = _validate_call(difficulty, overrides)
    scheduled = overrides.get("scene_profile") or schedule_profile(
        seed, sample_index, band
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    # The singleton is deliberate: scheduling chooses the default, while an
    # explicit override replaces it before this exact observable draw.
    profile = ctx.draw_choice("scene_profile", (scheduled,))
    header_count, distractor_count = _PROFILE_COUNTS[profile]

    h, w = ctx.draw_rng("dimensions").choice(_DIMENSIONS[band][profile])
    grid = full_grid(h, w, 0)

    header_rng = ctx.draw_rng("header_layout")
    color_rng = ctx.draw_rng("colors")
    header_columns = sorted(header_rng.sample(range(w), header_count))
    target = color_rng.choice(tuple(range(2, 10)))
    remaining_header_colors = color_rng.sample(
        [color for color in range(2, 10) if color != target],
        header_count - 1,
    )
    header_colors = [target, *remaining_header_colors]
    for column, color in zip(header_columns, header_colors):
        grid[0][column] = color

    body_cells = [(row, col) for row in range(1, h) for col in range(w)]
    capacity = len(body_cells) - distractor_count
    if band == "easy":
        lo, hi = 3, min(5, capacity)
    elif band == "hard":
        lo, hi = 6, min(12, capacity)
    else:
        lo, hi = 4, min(8, capacity)
    n_ones = ctx.draw_rng("one_count").randint(lo, hi)

    chosen = ctx.draw_rng("body_layout").sample(
        body_cells, n_ones + distractor_count
    )
    for row, col in chosen[:n_ones]:
        grid[row][col] = 1

    excluded = set(header_colors)
    available_distractors = [
        color for color in range(2, 10) if color not in excluded
    ]
    distractor_colors = color_rng.sample(
        available_distractors, distractor_count
    )
    for (row, col), color in zip(chosen[n_ones:], distractor_colors):
        grid[row][col] = color

    observed = observe_overrides(grid)
    if observed.get("scene_profile") != profile:
        raise AssertionError(
            f"constructed profile {profile!r} observed as "
            f"{observed.get('scene_profile')!r}"
        )
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    if not 2 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [
            f"grid dimensions must be 2..30 by 1..30, found "
            f"{len(grid)}x{width}"
        ]
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    header = [
        (column, value)
        for column, value in enumerate(grid[0])
        if value != 0
    ]
    body_ones = [
        (row, col)
        for row in range(1, h)
        for col in range(w)
        if grid[row][col] == 1
    ]
    body_distractors = [
        (row, col, grid[row][col])
        for row in range(1, h)
        for col in range(w)
        if grid[row][col] not in (0, 1)
    ]

    if not header:
        errors.append("row 0 must contain at least one nonzero legend cell")
    elif header[0][1] == 1:
        errors.append("the first nonzero legend color must differ from blue (1)")
    if not body_ones:
        errors.append("body must contain at least one blue (1) cell")

    profile = _PROFILE_BY_COUNTS.get((len(header), len(body_distractors)))
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "header": header,
        "target": header[0][1] if header else None,
        "body_ones": body_ones,
        "body_distractors": body_distractors,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level grammar without narrowing valid inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as "
                f"{observed.get(name)!r}"
            )
    return errors


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the narrower generated curriculum and exact profile axis."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    h, w = analysis["height"], analysis["width"]
    if not (4 <= h <= 9 and 5 <= w <= 12):
        errors.append(f"teaching dimensions must be 4..9 by 5..12, found {h}x{w}")
    if analysis["target"] not in range(2, 10):
        errors.append("teaching target must be a non-blue color in 2..9")
    header_values = [value for _column, value in analysis["header"]]
    if len(header_values) != len(set(header_values)):
        errors.append("teaching header colors must be distinct")
    if analysis["scene_profile"] is None:
        errors.append(
            "teaching scene must realize one of the declared "
            "(header-count, distractor-count) profiles"
        )
    if not 3 <= len(analysis["body_ones"]) <= 12:
        errors.append(
            f"teaching scene must contain 3..12 body 1s, found "
            f"{len(analysis['body_ones'])}"
        )
    distractor_values = [
        value for _row, _col, value in analysis["body_distractors"]
    ]
    if len(distractor_values) != len(set(distractor_values)):
        errors.append("teaching body distractor colors must be distinct")
    if set(distractor_values) & set(header_values):
        errors.append("teaching body distractor colors must differ from header colors")

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as "
                f"{observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact declared axis from returned pixels."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def strict_canonical_like(grid) -> list[str]:
    """Generated lessons and all public canonical inputs satisfy this profile."""
    return teaching_check(grid)


def _header_nonzeros(grid: Grid) -> list[int]:
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    values = [value for value in grid[0] if value != 0]
    if not values:
        raise ValueError("row 0 has no nonzero legend cell")
    return values


def _paint_body(grid: Grid, target: int, mode: str) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if mode == "ones_only" and value == 1:
                output[row][col] = target
            elif mode == "all_nonzero" and value != 0:
                output[row][col] = target
            elif mode == "preserve_distractors":
                if value == 1:
                    output[row][col] = target
                elif value != 0:
                    output[row][col] = value
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror; selected Racket remains label authority."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _paint_body(grid, analysis["target"], "ones_only")


def _rival_last_header_nonzero(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: use the last, not first, header marker."""
    return _paint_body(grid, _header_nonzeros(grid)[-1], "ones_only")


def _rival_recolor_all_nonzero_body(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: treat every nonzero body cell as signal."""
    return _paint_body(grid, _header_nonzeros(grid)[0], "all_nonzero")


def _rival_preserve_body_distractors(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: recolor 1s but retain other body colors."""
    return _paint_body(grid, _header_nonzeros(grid)[0], "preserve_distractors")


def _multiple_header_markers(grid: Grid) -> bool:
    analysis = _analysis(grid)
    return not analysis.get("errors") and len(analysis["header"]) > 1


def _body_distractors(grid: Grid) -> bool:
    analysis = _analysis(grid)
    return not analysis.get("errors") and bool(analysis["body_distractors"])


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "multiple_header_markers": _multiple_header_markers,
    "body_distractors": _body_distractors,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "last_header_nonzero": _rival_last_header_nonzero,
    "recolor_all_nonzero_body": _rival_recolor_all_nonzero_body,
    "preserve_body_distractors": _rival_preserve_body_distractors,
}
WITNESS_RIVALS = {
    "multiple_header_markers": ["last_header_nonzero"],
    "body_distractors": [
        "recolor_all_nonzero_body",
        "preserve_body_distractors",
    ],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every materialized lesson to refute all named shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if teaching_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = teaching_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the selected rule")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
