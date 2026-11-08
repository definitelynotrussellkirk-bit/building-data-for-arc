"""Curriculum generator for ARC task 3618c87e / content hash 44d20451ce17.

The selected Racket authority is unchanged: every color-1 cell above the
bottom row is erased, and the bottom cell of every column that contained a 1
in the input becomes 1.  Other cells are preserved.  The two generated scene
profiles deliberately separate that column-wise rule from four shortcuts that
all fit the compact canonical demonstrations.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "44d20451ce17"
TASK_ID = GENERATOR_ID
RULE_HASH = "fc96c07b50d8"
VERSION = "3.0.0"

SUMMARY = (
    "Move the presence of color 1 to the bottom of each affected column: "
    "erase every 1 above the bottom row, set the bottom cell to 1 whenever "
    "that input column contained a 1, and preserve every non-1 cell. Lessons "
    "alternate a canonical 5-supported scaffold with a counterexample that "
    "uses repeated 1s, a non-5 destination, a different source row, and no "
    "direct 5 support."
)
INVARIANTS = [
    "rectangular 5..10 by 5..10 grid using exactly colors 0, 1, and 5",
    "1..4 color-1 cells occur above the bottom row and none occur on it",
    "canonical_scaffold and counterexample profiles are visually recoverable",
    "three consecutive samples include a counterexample to every declared shortcut",
]

SCENE_PROFILES = ("canonical_scaffold", "counterexample")
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Static finite domains keep every advertised override probeable.  Every joint
# boundary combination is constructive at the 5x5 minimum.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "5 for canonical scaffold; otherwise difficulty-banded",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "5 for canonical scaffold; otherwise difficulty-banded",
        "valid": "5..10",
    },
    "n_ones": {
        "type": "int",
        "default": "difficulty-banded; counterexamples use at least 2",
        "valid": "1..4",
    },
    "scene_profile": {
        "type": "str",
        "default": "alternates by sample_index",
        "valid": "canonical_scaffold|counterexample",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _strict_index(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    _strict_index("seed", seed)
    _strict_index("sample_index", sample_index)
    _band(difficulty)
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _draw_profile(ctx, sample_index: int, overrides: dict[str, Any]) -> str:
    if "scene_profile" in overrides:
        return ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
    return ctx.draw_choice(
        "scene_profile", [SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]]
    )


def _draw_dim(
    ctx,
    name: str,
    *,
    profile: str,
    band: str,
    overrides: dict[str, Any],
) -> int:
    if name in overrides:
        return ctx.draw_int_strict(name, 5, 10)
    if profile == "canonical_scaffold":
        # This exact canonical shape/palette profile is present in every band.
        return ctx.draw_choice(name, [5])
    choices = {
        "easy": [5, 6],
        "medium": [5, 6, 7, 8],
        "hard": [5, 8, 9, 10],
    }[band]
    return ctx.draw_choice(name, choices)


def _draw_n_ones(
    ctx,
    *,
    profile: str,
    band: str,
    overrides: dict[str, Any],
) -> int:
    if "n_ones" in overrides:
        return ctx.draw_int_strict("n_ones", 1, 4)
    choices = {
        "canonical_scaffold": {
            "easy": [1, 2],
            "medium": [1, 2, 3],
            "hard": [2, 3, 4],
        },
        "counterexample": {
            "easy": [2],
            "medium": [2, 3],
            "hard": [3, 4],
        },
    }[profile][band]
    return ctx.draw_choice("n_ones", choices)


def _put_extra_fives(grid: list[list[int]], rng, *, forbidden: set[tuple[int, int]]) -> None:
    """Add sparse keyed decoys without changing any semantic profile cue."""
    candidates = [
        (r, c)
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]))
        if grid[r][c] == 0 and (r, c) not in forbidden
    ]
    if not candidates:
        return
    count = rng.randint(0, min(3, len(candidates)))
    for r, c in rng.sample(candidates, count):
        grid[r][c] = 5


def _draw_canonical_scaffold(ctx, h: int, w: int, n_ones: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("placement")
    columns = sorted(rng.sample(range(w), n_ones))
    source_row = h - 3
    support_row = h - 2
    for c in range(w):
        grid[h - 1][c] = 5
    for c in columns:
        grid[source_row][c] = 1
        grid[support_row][c] = 5
    _put_extra_fives(
        grid,
        ctx.draw_rng("decoys"),
        forbidden={(source_row, c) for c in columns},
    )
    return grid


def _draw_counterexample(ctx, h: int, w: int, n_ones: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("placement")
    target_col = rng.randrange(w)

    # Consecutive upper cells make repeated-column evidence conspicuous while
    # guaranteeing no 5 lies immediately below any 1.  With one overridden 1,
    # row 0 still refutes the fixed h-3 source-row shortcut.
    rows = list(range(n_ones))
    for r in rows:
        grid[r][target_col] = 1

    # The affected destination is 0, not the canonical 5.  Other bottom cells
    # remain 5 so the palette and visual analogy to the canonical task survive.
    for c in range(w):
        if c != target_col:
            grid[h - 1][c] = 5

    forbidden = {(r, target_col) for r in range(h - 1)}
    _put_extra_fives(grid, ctx.draw_rng("decoys"), forbidden=forbidden)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _strict_index("seed", seed)
    sample_index = _strict_index("sample_index", sample_index)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _draw_profile(ctx, sample_index, overrides)
    h = _draw_dim(ctx, "grid_h", profile=profile, band=band, overrides=overrides)
    w = _draw_dim(ctx, "grid_w", profile=profile, band=band, overrides=overrides)
    n_ones = _draw_n_ones(ctx, profile=profile, band=band, overrides=overrides)

    if profile == "canonical_scaffold":
        return _draw_canonical_scaffold(ctx, h, w, n_ones)
    if profile == "counterexample":
        return _draw_counterexample(ctx, h, w, n_ones)
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _shape(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
    if not (5 <= h <= 10 and 5 <= w <= 10):
        errors.append(f"grid dimensions must each be 5..10, got {h}x{w}")
    return h, w, errors


def _profile_of(grid: Any, h: int, w: int, ones: list[tuple[int, int]]) -> str | None:
    if (
        all(grid[h - 1][c] == 5 for c in range(w))
        and all(r == h - 3 for r, _ in ones)
        and all(grid[h - 2][c] == 5 for _, c in ones)
        and len({c for _, c in ones}) == len(ones)
    ):
        return "canonical_scaffold"

    columns = {c for _, c in ones}
    if len(columns) == 1:
        target_col = next(iter(columns))
        expected_rows = set(range(len(ones)))
        if (
            {r for r, _ in ones} == expected_rows
            and grid[h - 1][target_col] == 0
            and all(grid[h - 1][c] == 5 for c in range(w) if c != target_col)
            and all(grid[r + 1][target_col] != 5 for r, _ in ones)
        ):
            return "counterexample"
    return None


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, errors = _shape(grid)
    info: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return info, errors

    flat = [value for row in grid for value in row]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not (0 <= value <= 9)
        for value in flat
    ):
        return info, ["cells must be integer ARC colors 0..9"]

    colors = set(flat)
    if colors != {0, 1, 5}:
        errors.append(f"expected exactly colors [0, 1, 5], got {sorted(colors)}")
        return info, errors

    ones = [
        (r, c)
        for r in range(h - 1)
        for c in range(w)
        if grid[r][c] == 1
    ]
    bottom_ones = [(h - 1, c) for c in range(w) if grid[h - 1][c] == 1]
    if bottom_ones:
        errors.append("input profile must not contain color 1 on the bottom row")
    if not (1 <= len(ones) <= 4):
        errors.append(f"expected 1..4 color-1 cells above the bottom row, got {len(ones)}")
    if errors:
        return info, errors

    profile = _profile_of(grid, h, w, ones)
    if profile is None:
        errors.append("grid does not match a declared scene profile")
        return info, errors
    info.update({"n_ones": len(ones), "scene_profile": profile, "ones": ones})
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and the two explicit, rule-revealing profiles."""
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (info["grid_h"], info["grid_w"]) != (5, 5):
        reasons.append("canonical task uses a 5x5 grid")
    return reasons


def _rule_shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty list of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not (0 <= value <= 9)
        for row in grid
        for value in row
    ):
        raise ValueError("cells must be integer ARC colors 0..9")
    return h, w


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python statement of the selected canonical Racket rule."""
    h, w = _rule_shape(grid)
    out = [list(row) for row in grid]
    for c in range(w):
        had_one = any(grid[r][c] == 1 for r in range(h))
        for r in range(h - 1):
            if grid[r][c] == 1:
                out[r][c] = 0
        if had_one:
            out[h - 1][c] = 1
    return out


def _copy(grid: Any) -> list[list[int]]:
    _rule_shape(grid)
    return [list(row) for row in grid]


def _rival_bottom_five_only(grid: Any) -> list[list[int]]:
    """Shortcut: only columns whose destination was canonical color 5 move."""
    h, w = _rule_shape(grid)
    out = _copy(grid)
    for c in range(w):
        rows = [r for r in range(h - 1) if grid[r][c] == 1]
        if rows and grid[h - 1][c] == 5:
            for r in rows:
                out[r][c] = 0
            out[h - 1][c] = 1
    return out


def _rival_direct_five_support_only(grid: Any) -> list[list[int]]:
    """Shortcut: a column moves only when a 1 sits directly above a 5."""
    h, w = _rule_shape(grid)
    out = _copy(grid)
    for c in range(w):
        rows = [r for r in range(h - 1) if grid[r][c] == 1]
        supported = any(grid[r + 1][c] == 5 for r in rows)
        if rows and supported:
            for r in rows:
                out[r][c] = 0
            out[h - 1][c] = 1
    return out


def _rival_fixed_source_row_only(grid: Any) -> list[list[int]]:
    """Shortcut: only canonical row h-3 is inspected and erased."""
    h, w = _rule_shape(grid)
    out = _copy(grid)
    source_row = h - 3
    for c in range(w):
        if grid[source_row][c] == 1:
            out[source_row][c] = 0
            out[h - 1][c] = 1
    return out


def _rival_lowest_one_only(grid: Any) -> list[list[int]]:
    """Shortcut: move only the lowest 1 in each affected column."""
    h, w = _rule_shape(grid)
    out = _copy(grid)
    for c in range(w):
        rows = [r for r in range(h - 1) if grid[r][c] == 1]
        if rows:
            out[max(rows)][c] = 0
            out[h - 1][c] = 1
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "bottom_five_only": _rival_bottom_five_only,
    "direct_five_support_only": _rival_direct_five_support_only,
    "fixed_source_row_only": _rival_fixed_source_row_only,
    "lowest_one_only": _rival_lowest_one_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _is_counterexample(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info.get("scene_profile") == "counterexample"


def _bottom_target_not_five(grid: Any) -> bool:
    info, errors = _analyse(grid)
    if errors or info.get("scene_profile") != "counterexample":
        return False
    target_col = info["ones"][0][1]
    return grid[-1][target_col] != 5


def _no_direct_five_support(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and all(grid[r + 1][c] != 5 for r, c in info["ones"])


def _source_rows_vary(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(r != info["grid_h"] - 3 for r, _ in info["ones"])


def _multiple_ones_share_column(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return (
        not errors
        and len(info["ones"]) >= 2
        and len({c for _, c in info["ones"]}) == 1
    )


SEMANTIC_WITNESSES = {
    "bottom_target_is_not_five": _bottom_target_not_five,
    "no_direct_five_support": _no_direct_five_support,
    "source_rows_vary": _source_rows_vary,
    "multiple_ones_share_column": _multiple_ones_share_column,
}
WITNESS_RIVALS = {
    "bottom_target_is_not_five": ["bottom_five_only"],
    "no_direct_five_support": ["direct_five_support_only"],
    "source_rows_vary": ["fixed_source_row_only"],
    "multiple_ones_share_column": ["lowest_one_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check materialized demos against the declared shortcut family."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a sequence"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the canonical rule")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        if "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the canonical rule")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(deepcopy(pair["input"])) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"declared competitor remains unrefuted: {name}")
    return reasons
