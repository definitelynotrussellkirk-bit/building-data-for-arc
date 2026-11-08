"""Canonical-density lesson generator for checkerboard-parity filling.

A single marker color defines an ordered pair of row/column parities.  The
selected Racket authority replaces only background-0 cells having that exact
parity pair.  Gray-5 cells are immutable blockers.  Generated inputs retain the
three published size/palette profiles and dense, fragmented gray surrounds,
while varying the open field, marker, and blocker geometry.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "c9034f0626e0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d29d80b108a0"

SUMMARY = (
    "A dense gray-5 surround encloses a large irregular zero field containing "
    "one marker color. Replace exactly the zero cells whose row parity and "
    "column parity both match the marker; preserve gray blockers, the marker, "
    "and every other zero cell."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "dimensions and gray count realize one published canonical profile",
    "exactly one cell has a color other than 0 or 5",
    "the marker lies in a large connected zero field",
    "fragmented gray blockers include the marker's exact parity class",
    "all four parity classes retain background cells, refuting one-coordinate and fill-all rivals",
]

# (height, width, gray count, open-field height, open-field width,
#  target gray-component count, target largest gray component)
PROFILE_SPECS: dict[str, tuple[int, int, int, int, int, int, int]] = {
    "canonical_13x13": (13, 13, 69, 8, 8, 11, 23),
    "canonical_13x16": (13, 16, 94, 7, 8, 9, 28),
    "canonical_15x17": (15, 17, 81, 11, 12, 11, 43),
}
SCENE_PROFILES = tuple(PROFILE_SPECS)
_PROFILE_BY_DIMS = {(spec[0], spec[1]): name for name, spec in PROFILE_SPECS.items()}
MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
# Alternate around immutable gray-5 so every three-demo support refutes
# lowest-color-only and highest-color-only label shortcuts.
_MARKER_COLOR_SCHEDULE = (1, 6, 2, 7, 3, 8, 4, 9)
MARKER_PARITIES = ("p00", "p01", "p10", "p11")
_PARITY_VALUE = {name: (int(name[1]), int(name[2])) for name in MARKER_PARITIES}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic three-profile curriculum",
        "valid": "canonical_13x13|canonical_13x16|canonical_15x17",
    },
    "marker_color": {
        "type": "color",
        "default": "deterministic cycle over non-0/non-5 ARC colors",
        "valid": "1|2|3|4|6|7|8|9",
    },
    "marker_parity": {
        "type": "str",
        "default": "deterministic cycle over the four ordered parity pairs",
        "valid": "p00|p01|p10|p11",
    },
}


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise ValueError(f"seed must be a literal integer, got {seed!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError(
            f"sample_index must be a non-negative literal integer, got {sample_index!r}"
        )
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if type(value) is not str or value not in PROFILE_SPECS:
            raise ValueError(f"invalid scene_profile override: {value!r}")
    if "marker_color" in overrides:
        value = overrides["marker_color"]
        if type(value) is not int or value not in MARKER_COLORS:
            raise ValueError(f"invalid marker_color override: {value!r}")
    if "marker_parity" in overrides:
        value = overrides["marker_parity"]
        if type(value) is not str or value not in MARKER_PARITIES:
            raise ValueError(f"invalid marker_parity override: {value!r}")


def _band(difficulty: Any) -> str:
    return "medium" if difficulty is None else str(difficulty)


def schedule_profile(seed: Any, sample_index: int, difficulty: Any = None) -> str:
    """Exact cyclic profile schedule; seed/band affect pixels, not coverage."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def schedule_marker_color(seed: Any, sample_index: int, difficulty: Any = None) -> int:
    del seed, difficulty
    return _MARKER_COLOR_SCHEDULE[int(sample_index) % len(_MARKER_COLOR_SCHEDULE)]


def schedule_marker_parity(seed: Any, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return MARKER_PARITIES[int(sample_index) % len(MARKER_PARITIES)]


def _neighbors(point: Cell) -> tuple[Cell, Cell, Cell, Cell]:
    row, col = point
    return ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))


def _component_sizes(points: set[Cell]) -> list[int]:
    unseen = set(points)
    sizes: list[int] = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        size = 0
        while queue:
            point = queue.popleft()
            size += 1
            for neighbor in _neighbors(point):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _field_cells(height: int, width: int, field_h: int, field_w: int, rng) -> tuple[set[Cell], int, int]:
    # Keep a one-cell exterior margin on all sides.  Position remains seed-varying.
    row0 = rng.randint(1, height - field_h - 1)
    col0 = rng.randint(1, width - field_w - 1)
    cells = {
        (row, col)
        for row in range(row0, row0 + field_h)
        for col in range(col0, col0 + field_w)
    }
    return cells, row0, col0


def _choose_marker(field: set[Cell], row0: int, col0: int, field_h: int, field_w: int, parity: tuple[int, int], rng) -> Cell:
    # Prefer the field interior so the marker is not a boundary cue.
    interior = [
        (row, col)
        for row, col in sorted(field)
        if row0 < row < row0 + field_h - 1
        and col0 < col < col0 + field_w - 1
        and (row % 2, col % 2) == parity
    ]
    candidates = interior or [
        point for point in sorted(field) if (point[0] % 2, point[1] % 2) == parity
    ]
    if not candidates:
        raise RuntimeError(f"open field cannot realize marker parity {parity}")
    return rng.choice(candidates)


def _gray_candidate(
    exterior: list[Cell],
    gray_count: int,
    marker: Cell,
    marker_parity: tuple[int, int],
    target_components: int,
    target_largest: int,
    height: int,
    width: int,
    rng,
) -> tuple[set[Cell], tuple[int, int, int]]:
    gray = set(rng.sample(exterior, gray_count))
    sizes = _component_sizes(gray)
    all_cells = {(row, col) for row in range(height) for col in range(width)}
    zeros = all_cells - gray - {marker}
    zero_counts = {
        parity: sum((row % 2, col % 2) == parity for row, col in zeros)
        for parity in ((0, 0), (0, 1), (1, 0), (1, 1))
    }
    hard_penalty = 0
    if not any((row % 2, col % 2) == marker_parity for row, col in gray):
        hard_penalty += 100_000
    if min(zero_counts.values()) < 2:
        hard_penalty += 100_000
    # Component count dominates, but largest-component proximity breaks ties.
    score = hard_penalty + 10 * abs(len(sizes) - target_components) + abs(sizes[0] - target_largest)
    return gray, (score, len(sizes), sizes[0])


def _draw_gray_surround(
    height: int,
    width: int,
    gray_count: int,
    field: set[Cell],
    marker: Cell,
    marker_parity: tuple[int, int],
    target_components: int,
    target_largest: int,
    rng,
) -> set[Cell]:
    exterior = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in field
    ]
    if len(exterior) < gray_count:
        raise RuntimeError("profile has too few exterior cells for its gray count")

    best_gray: set[Cell] | None = None
    best_score: tuple[int, int, int] | None = None
    # A bounded best-of draw preserves determinism and avoids rejection-loop tails.
    for _ in range(32):
        gray, score = _gray_candidate(
            exterior,
            gray_count,
            marker,
            marker_parity,
            target_components,
            target_largest,
            height,
            width,
            rng,
        )
        if best_score is None or score < best_score:
            best_gray, best_score = gray, score
    assert best_gray is not None and best_score is not None
    if best_score[0] >= 100_000:
        raise RuntimeError("could not realize mandatory parity witnesses")
    return best_gray


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one input grid; the pinned Racket authority owns labels."""
    _validate_call(seed, sample_index, difficulty, overrides)

    selected_profile = overrides.get(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    selected_color = overrides.get(
        "marker_color", schedule_marker_color(seed, sample_index, difficulty)
    )
    selected_parity = overrides.get(
        "marker_parity", schedule_marker_parity(seed, sample_index, difficulty)
    )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", (selected_profile,))
    marker_color = ctx.draw_choice("marker_color", (selected_color,))
    parity_name = ctx.draw_choice("marker_parity", (selected_parity,))
    marker_parity = _PARITY_VALUE[parity_name]

    height, width, gray_count, field_h, field_w, target_components, target_largest = PROFILE_SPECS[profile]
    band = _band(difficulty)
    # Difficulty changes morphology without narrowing any exact override domain:
    # easy favors one fewer/larger gray region, hard one more/smaller region.
    target_components += {"easy": -1, "medium": 0, "hard": 1}[band]
    target_largest += {"easy": 5, "medium": 0, "hard": -5}[band]
    rng = ctx.draw_rng("layout")
    # gen_ctx intentionally keeps keyed draws stable across bands. Advance a
    # fixed amount so the difficulty knob produces genuinely different pixels.
    for _ in range({"easy": 0, "medium": 1, "hard": 2}[band]):
        rng.random()
    field, row0, col0 = _field_cells(height, width, field_h, field_w, rng)
    marker = _choose_marker(field, row0, col0, field_h, field_w, marker_parity, rng)
    gray = _draw_gray_surround(
        height,
        width,
        gray_count,
        field,
        marker,
        marker_parity,
        target_components,
        target_largest,
        rng,
    )

    grid = full_grid(height, width, 0)
    for row, col in gray:
        grid[row][col] = 5
    grid[marker[0]][marker[1]] = marker_color

    expected = {
        "scene_profile": profile,
        "marker_color": marker_color,
        "marker_parity": parity_name,
    }
    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError(f"constructed grid violated strict grammar: {errors}")
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"draw/observation mismatch: expected {expected}, observed {observed}")
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC dimensions must lie in 1..30, found {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integer colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    profile = _PROFILE_BY_DIMS.get((height, width))
    if profile is None:
        errors.append(f"dimensions {(height, width)} do not identify a declared scene profile")

    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly one non-0/non-5 marker, found {len(markers)}")
        marker = None
    else:
        marker = markers[0]

    gray = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    zeros = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    }
    gray_sizes = _component_sizes(gray) if gray else []
    zero_sizes = _component_sizes(zeros) if zeros else []

    area = height * width
    if len(gray) < max(20, area // 4):
        errors.append(f"gray surround is too sparse: {len(gray)} of {area} cells")
    if not gray_sizes or not 3 <= len(gray_sizes) <= 30:
        errors.append(f"expected fragmented gray surround, found {len(gray_sizes)} components")
    if not zero_sizes or zero_sizes[0] < max(24, area // 5):
        errors.append("expected one substantial connected background field")

    if marker is not None:
        mr, mc, marker_color = marker
        if marker_color not in MARKER_COLORS:
            errors.append(f"marker color must be one of {MARKER_COLORS}, found {marker_color}")
        marker_parity = (mr % 2, mc % 2)
        zero_counts = {
            parity: sum((row % 2, col % 2) == parity for row, col in zeros)
            for parity in ((0, 0), (0, 1), (1, 0), (1, 1))
        }
        if min(zero_counts.values(), default=0) < 1:
            errors.append("all four row/column parity classes need background witnesses")
        if not any((row % 2, col % 2) == marker_parity for row, col in gray):
            errors.append("need a same-parity gray blocker to teach blocker preservation")
    else:
        marker_parity = None

    return {
        "errors": sorted(set(errors)),
        "height": height,
        "width": width,
        "profile": profile,
        "marker": marker,
        "marker_parity": marker_parity,
        "gray_count": len(gray),
        "gray_sizes": gray_sizes,
        "zero_sizes": zero_sizes,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's dense input grammar without consulting labels."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Linked canonical size/count profiles plus broad morphology envelopes."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    profile = analysis.get("profile")
    if profile is None:
        return sorted(set(errors))

    expected_gray = PROFILE_SPECS[profile][2]
    if analysis["gray_count"] != expected_gray:
        errors.append(
            f"profile {profile} requires {expected_gray} gray cells, found {analysis['gray_count']}"
        )
    gray_components = len(analysis["gray_sizes"])
    if not 5 <= gray_components <= 18:
        errors.append(f"gray component count {gray_components} outside canonical envelope 5..18")
    largest_gray = analysis["gray_sizes"][0] if analysis["gray_sizes"] else 0
    if not 10 <= largest_gray <= 80:
        errors.append(f"largest gray component {largest_gray} outside canonical envelope 10..80")
    min_zero = {
        "canonical_13x13": 55,
        "canonical_13x16": 45,
        "canonical_15x17": 110,
    }[profile]
    largest_zero = analysis["zero_sizes"][0] if analysis["zero_sizes"] else 0
    if largest_zero < min_zero:
        errors.append(
            f"largest zero field {largest_zero} below profile minimum {min_zero}"
        )
    return sorted(set(errors))


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = strict_canonical_like(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return sorted(set(errors))


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors']}")
    marker = analysis["marker"]
    assert marker is not None and analysis["profile"] is not None
    row, col, color = marker
    return {
        "scene_profile": analysis["profile"],
        "marker_color": color,
        "marker_parity": f"p{row % 2}{col % 2}",
    }


def canonical_profile_index(grid) -> int | None:
    analysis = _analyze(grid)
    profile = analysis.get("profile")
    if profile is None:
        return None
    return SCENE_PROFILES.index(profile)


def _find_marker(grid: Grid) -> tuple[int, int, int]:
    hits = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]
    if len(hits) != 1:
        raise ValueError(f"expected one marker, found {len(hits)}")
    return hits[0]


def _apply_rule(grid: Grid) -> Grid:
    mr, mc, color = _find_marker(grid)
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 and (row % 2, col % 2) == (mr % 2, mc % 2):
                out[row][col] = color
    return out


def _rival_row_only(grid: Grid) -> Grid:
    mr, _mc, color = _find_marker(grid)
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 and row % 2 == mr % 2:
                out[row][col] = color
    return out


def _rival_column_only(grid: Grid) -> Grid:
    _mr, mc, color = _find_marker(grid)
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 and col % 2 == mc % 2:
                out[row][col] = color
    return out


def _rival_sum_parity(grid: Grid) -> Grid:
    mr, mc, color = _find_marker(grid)
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 and (row + col) % 2 == (mr + mc) % 2:
                out[row][col] = color
    return out


def _rival_fill_all(grid: Grid) -> Grid:
    _mr, _mc, color = _find_marker(grid)
    return [[color if value == 0 else value for value in row] for row in grid]


def _rival_overwrite_gray(grid: Grid) -> Grid:
    mr, mc, color = _find_marker(grid)
    out = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, _value in enumerate(values):
            if (row % 2, col % 2) == (mr % 2, mc % 2):
                out[row][col] = color
    return out


def _rival_identity(grid: Grid) -> Grid:
    return deepcopy(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "row_only": _rival_row_only,
    "column_only": _rival_column_only,
    "sum_parity": _rival_sum_parity,
    "fill_all": _rival_fill_all,
    "overwrite_gray": _rival_overwrite_gray,
    "identity": _rival_identity,
}


def _witness_for(rival_name: str) -> Callable[[Grid], bool]:
    return lambda grid: _apply_rule(grid) != SEMANTIC_RIVALS[rival_name](grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "row_coordinate_is_not_enough": _witness_for("row_only"),
    "column_coordinate_is_not_enough": _witness_for("column_only"),
    "ordered_pair_not_sum_parity": _witness_for("sum_parity"),
    "opposite_parities_stay_background": _witness_for("fill_all"),
    "same_parity_gray_is_preserved": _witness_for("overwrite_gray"),
    "same_parity_background_changes": _witness_for("identity"),
}
WITNESS_RIVALS = {
    "row_coordinate_is_not_enough": ["row_only"],
    "column_coordinate_is_not_enough": ["column_only"],
    "ordered_pair_not_sum_parity": ["sum_parity"],
    "opposite_parities_stay_background": ["fill_all"],
    "same_parity_gray_is_preserved": ["overwrite_gray"],
    "same_parity_background_changes": ["identity"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of the named rivals fits all three published pairs; keep this honest.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Check labels and reject any lesson left ambiguous by a named rival."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside strict grammar: {grammar[0]}")
            continue
        if _apply_rule(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output does not match exact parity-pair fill")
    if reasons:
        return sorted(set(reasons))

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            suffix = (
                "and also matches the query"
                if rival(query["input"]) == query["output"]
                else "but disagrees on the query"
            )
            reasons.append(f"competitor {name} fits every demonstration {suffix}")
    return sorted(set(reasons))
