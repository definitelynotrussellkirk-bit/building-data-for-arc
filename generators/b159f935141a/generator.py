"""Teach the four-cardinal-neighbor conjunction with contrastive inputs.

The unchanged Racket rule is the label authority.  This module only samples
inputs and declares deterministic wrong-rule diagnostics.  Default draws cycle
through one exact canonical profile and three contrastive profiles, so ordinary
three-example lessons contain shortcut-breaking evidence without losing the
small canonical scale.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b159f935141a"
TASK_ID = GENERATOR_ID
RULE_HASH = "d4bb39745d13"
VERSION = "3.1.0"
SUMMARY = (
    "Fill a zero cell exactly when its four cardinal neighbors share one "
    "nonzero color. Preserve exact canonical-size two-plus examples while "
    "mixing horizontal-only, vertical-only, three-arm, mixed-arm, occupied-"
    "center, and diagonal decoys that distinguish plausible shortcut rules."
)

INVARIANTS = [
    "rectangular ARC grid with integer colors 0..9 and background 0",
    "every generated input contains at least one hollow monochrome cardinal plus",
    "contrastive draws include lawful decoys that the selected rule leaves unchanged",
    "accepted dimension and motif-count overrides are exactly observable from pixels",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 5..6; compact contrastive 8..14",
        "valid": "5..22",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 6..8; compact contrastive 8..14",
        "valid": "5..22",
    },
    "n_plusses": {
        "type": "int",
        "default": "2 canonical; 1..3 contrastive",
        "valid": "1..8",
    },
    "n_decoys": {
        "type": "int",
        "default": "0 canonical; 3..5 contrastive",
        "valid": "0..8",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical",
    "contrastive_three",
    "contrastive_mixed",
    "contrastive_joint",
)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_COLORS = tuple(range(1, 10))
_DECOY_KINDS = (
    "horizontal_pair",
    "vertical_pair",
    "three_arms",
    "mixed_arms",
    "occupied",
    "diagonal",
)
_DECOY_PLANS = {
    0: ("diagonal", "occupied", "three_arms", "mixed_arms", "horizontal_pair", "vertical_pair"),
    1: ("diagonal", "occupied", "three_arms", "horizontal_pair", "mixed_arms", "vertical_pair"),
    2: ("diagonal", "occupied", "mixed_arms", "vertical_pair", "three_arms", "horizontal_pair"),
    3: ("diagonal", "occupied", "three_arms", "mixed_arms", "horizontal_pair", "vertical_pair"),
}
_CANONICAL_LAYOUTS = {
    (5, 7): ((2, 2), (2, 5)),
    (6, 6): ((2, 1), (3, 4)),
    (5, 8): ((2, 1), (2, 6)),
    (5, 6): ((2, 1), (3, 4)),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _incompatible(message: str, *axes: str) -> None:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _arms(grid: list[list[int]], r: int, c: int, offsets=_CARD) -> tuple[int, ...]:
    return tuple(grid[r + dr][c + dc] for dr, dc in offsets)


def _fires(grid: list[list[int]]) -> set[tuple[int, int]]:
    targets: set[tuple[int, int]] = set()
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = _arms(grid, r, c)
            if grid[r][c] == 0 and arms[0] != 0 and len(set(arms)) == 1:
                targets.add((r, c))
    return targets


def _decoy_kind(grid: list[list[int]], r: int, c: int) -> str | None:
    center = grid[r][c]
    up, down, left, right = _arms(grid, r, c)
    cardinal = (up, down, left, right)
    nonzero = [value for value in cardinal if value != 0]

    if center == 0 and left == right != 0 and up == down == 0:
        return "horizontal_pair"
    if center == 0 and up == down != 0 and left == right == 0:
        return "vertical_pair"
    if center == 0 and len(nonzero) == 3 and len(set(nonzero)) == 1:
        return "three_arms"
    if center == 0 and len(nonzero) == 4 and len(set(cardinal)) > 1:
        return "mixed_arms"
    if center != 0 and cardinal[0] != 0 and len(set(cardinal)) == 1:
        return "occupied"

    diagonal = _arms(grid, r, c, _DIAG)
    if center == 0 and not nonzero and diagonal[0] != 0 and len(set(diagonal)) == 1:
        return "diagonal"
    return None


def _primary_decoys(grid: list[list[int]]) -> dict[tuple[int, int], str]:
    """Classify motifs while folding pair patterns induced by a diagonal motif."""
    classified = {
        (r, c): kind
        for r in range(1, len(grid) - 1)
        for c in range(1, len(grid[0]) - 1)
        if (kind := _decoy_kind(grid, r, c)) is not None
    }
    diagonal_centers = {
        position for position, kind in classified.items() if kind == "diagonal"
    }
    return {
        (r, c): kind
        for (r, c), kind in classified.items()
        if not (
            kind in {"horizontal_pair", "vertical_pair"}
            and any(abs(r - dr) + abs(c - dc) == 1 for dr, dc in diagonal_centers)
        )
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every exact axis from pixels rather than draw provenance."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_plusses": len(_fires(grid)),
        "n_decoys": len(_primary_decoys(grid)),
    }


def _capacity(h: int, w: int) -> int:
    # Five-cell spacing leaves at least two blank cells between 3x3 motif boxes,
    # preventing facing arms from accidentally forming a new two-arm decoy.
    return (1 + (h - 3) // 5) * (1 + (w - 3) // 5)


def _slots(h: int, w: int, rng) -> list[tuple[int, int]]:
    n_rows = 1 + (h - 3) // 5
    n_cols = 1 + (w - 3) // 5
    max_r0 = h - 2 - 5 * (n_rows - 1)
    max_c0 = w - 2 - 5 * (n_cols - 1)
    r0 = rng.randint(1, max_r0)
    c0 = rng.randint(1, max_c0)
    slots = [(r0 + 5 * rr, c0 + 5 * cc) for rr in range(n_rows) for cc in range(n_cols)]
    rng.shuffle(slots)
    return slots


def _paint_plus(grid: list[list[int]], r: int, c: int, color: int) -> None:
    for dr, dc in _CARD:
        grid[r + dr][c + dc] = color


def _paint_decoy(
    grid: list[list[int]],
    r: int,
    c: int,
    kind: str,
    color: int,
    other: int,
) -> None:
    if kind == "horizontal_pair":
        grid[r][c - 1] = color
        grid[r][c + 1] = color
        return
    if kind == "vertical_pair":
        grid[r - 1][c] = color
        grid[r + 1][c] = color
        return
    if kind == "three_arms":
        for dr, dc in _CARD[:3]:
            grid[r + dr][c + dc] = color
        return
    if kind == "mixed_arms":
        for dr, dc in _CARD:
            grid[r + dr][c + dc] = color
        grid[r][c + 1] = other
        return
    if kind == "occupied":
        _paint_plus(grid, r, c, color)
        grid[r][c] = other
        return
    if kind == "diagonal":
        for dr, dc in _DIAG:
            grid[r + dr][c + dc] = color
        return
    raise ValueError(f"unknown decoy kind: {kind!r}")


def _canonical_grid(ctx) -> list[list[int]]:
    profile = ctx.draw_choice("canonical_profile", tuple(_CANONICAL_LAYOUTS))
    h, w = profile
    ctx.draw_choice("grid_h", (h,))
    ctx.draw_choice("grid_w", (w,))
    ctx.draw_int_strict("n_plusses", 2, 2)
    ctx.draw_int_strict("n_decoys", 0, 0)
    grid = full_grid(h, w, 0)
    colors = ctx.draw_rng("canonical_palette").sample(_COLORS, 2)
    centers = list(_CANONICAL_LAYOUTS[profile])
    transform = ctx.draw_int("canonical_transform", 0, 3)
    if transform & 1:
        centers = [(r, w - 1 - c) for r, c in centers]
    if transform & 2:
        centers = [(h - 1 - r, c) for r, c in centers]
    for center, color in zip(centers, colors):
        _paint_plus(grid, *center, color)
    return grid


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(
            f"unknown or removed override axes: {sorted(unknown)}; supported: {sorted(AXES)}"
        )
    bounds = {
        "grid_h": (5, 22),
        "grid_w": (5, 22),
        "n_plusses": (1, 8),
        "n_decoys": (0, 8),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = bounds[name]
        if type(value) is not int or not lo <= value <= hi:
            raise TypeError(f"{name} must be an integer in {lo}..{hi} (not bool)")


def _draw_dimensions(ctx, required: int, difficulty: str | None) -> tuple[int, int]:
    compact_default = not ctx.overrides
    max_area = {"easy": 104, "medium": 117, "hard": 126}.get(difficulty, 117)
    pinned_h = ctx.overrides.get("grid_h")
    pinned_w = ctx.overrides.get("grid_w")
    pairs: list[tuple[int, int]] = []
    for h in range(5, 23):
        if pinned_h is not None and h != pinned_h:
            continue
        for w in range(5, 23):
            if pinned_w is not None and w != pinned_w:
                continue
            if _capacity(h, w) < required:
                continue
            if compact_default and not (8 <= h <= 14 and 8 <= w <= 14):
                continue
            if compact_default and h * w > max_area:
                continue
            pairs.append((h, w))

    if not pairs:
        involved = tuple(
            name
            for name in ("grid_h", "grid_w", "n_plusses", "n_decoys")
            if name in ctx.overrides and ctx.overrides[name] is not None
        )
        _incompatible("requested motif counts do not fit the selected dimensions", *involved)

    heights = sorted({h for h, _ in pairs})
    h = ctx.draw_choice("grid_h", heights)
    widths = sorted({w for ph, w in pairs if ph == h})
    w = ctx.draw_choice("grid_w", widths)
    return h, w


def _contrastive_grid(ctx, difficulty: str | None) -> list[list[int]]:
    explicit_plusses = ctx.overrides.get("n_plusses")
    explicit_decoys = ctx.overrides.get("n_decoys")

    if ctx.overrides:
        if explicit_plusses is not None:
            n_plusses = ctx.draw_int_strict("n_plusses", 1, 8)
        else:
            n_plusses = ctx.draw_int_strict("n_plusses", 1, 1)
        if explicit_decoys is not None:
            n_decoys = ctx.draw_int_strict("n_decoys", 0, 8)
        else:
            n_decoys = ctx.draw_int_strict("n_decoys", 0, 0)
    else:
        phase = ctx.sample_index % LESSON_SCHEDULE_PERIOD
        if difficulty == "easy":
            plus_lo, plus_hi = 1, 2
        elif difficulty == "hard":
            plus_lo, plus_hi = 2, 2
        else:
            plus_lo, plus_hi = 1, 3
        if phase == 3:
            plus_hi = min(plus_hi, 2)
        n_plusses = ctx.draw_int_strict("n_plusses", plus_lo, plus_hi)
        decoy_lo = 4 if phase == 3 else 3
        n_decoys = ctx.draw_int_strict(
            "n_decoys", decoy_lo, min(5, 6 - n_plusses)
        )

    required = n_plusses + n_decoys
    h, w = _draw_dimensions(ctx, required, difficulty)
    capacity = _capacity(h, w)
    if required > capacity:
        involved = tuple(
            name
            for name in ("grid_h", "grid_w", "n_plusses", "n_decoys")
            if name in ctx.overrides and ctx.overrides[name] is not None
        )
        _incompatible("n_plusses+n_decoys exceed separated motif capacity", *involved)

    rng = ctx.draw_rng(f"layout_{difficulty or 'mixed'}")
    slots = _slots(h, w, rng)
    palette = rng.sample(_COLORS, 2)
    grid = full_grid(h, w, 0)

    intended = set(slots[:n_plusses])
    for index, (r, c) in enumerate(slots[:n_plusses]):
        _paint_plus(grid, r, c, palette[index % 2])

    decoy_plan = _DECOY_PLANS[ctx.sample_index % LESSON_SCHEDULE_PERIOD]
    for index, (r, c) in enumerate(slots[n_plusses : n_plusses + n_decoys]):
        kind = decoy_plan[index % len(decoy_plan)]
        color = palette[index % 2]
        other = palette[(index + 1) % 2]
        _paint_decoy(grid, r, c, kind, color, other)

    observed = observe_overrides(grid)
    if _fires(grid) != intended:
        raise RuntimeError("constructed motifs created or destroyed an intended plus")
    if observed["n_decoys"] != n_decoys:
        raise RuntimeError(
            f"constructed {n_decoys} decoys but pixel observer found {observed['n_decoys']}"
        )
    return grid


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if not overrides and schedule_profile(seed, sample_index, difficulty) == "canonical":
        return _canonical_grid(ctx)
    return _contrastive_grid(ctx, difficulty)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must contain rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be nonempty"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    if not (3 <= h <= 30 and 3 <= w <= 30):
        return ["grid dimensions must be in 3..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9 (not booleans)"]
    if not _fires(grid):
        return ["input must contain at least one fillable hollow cardinal plus"]
    return []


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


# Deliberately wrong rules below are diagnostics only; Racket remains authority.
def _intended_python(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r, c in _fires(grid):
        out[r][c] = grid[r - 1][c]
    return out


def _horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0 and grid[r][c - 1] == grid[r][c + 1] != 0:
                out[r][c] = grid[r][c - 1]
    return out


def _vertical_only(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] == 0 and grid[r - 1][c] == grid[r + 1][c] != 0:
                out[r][c] = grid[r - 1][c]
    return out


def _three_arms(grid: list[list[int]]) -> list[list[int]]:
    out = _intended_python(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] != 0:
                continue
            arms = _arms(grid, r, c)
            for color in _COLORS:
                if arms.count(color) >= 3:
                    out[r][c] = color
    return out


def _mixed_majority(grid: list[list[int]]) -> list[list[int]]:
    out = _intended_python(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = _arms(grid, r, c)
            if grid[r][c] == 0 and all(arms):
                out[r][c] = max(_COLORS, key=lambda color: (arms.count(color), -color))
    return out


def _overwrite_occupied(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = _arms(grid, r, c)
            if arms[0] != 0 and len(set(arms)) == 1:
                out[r][c] = arms[0]
    return out


def _diagonals_also(grid: list[list[int]]) -> list[list[int]]:
    out = _intended_python(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            diagonal = _arms(grid, r, c, _DIAG)
            if grid[r][c] == 0 and diagonal[0] != 0 and len(set(diagonal)) == 1:
                out[r][c] = diagonal[0]
    return out


def _has_decoy(kind: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid: list[list[int]]) -> bool:
        return kind in _primary_decoys(grid).values()

    return predicate


SEMANTIC_RIVALS = {
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "three_arms": _three_arms,
    "mixed_majority": _mixed_majority,
    "overwrite_occupied": _overwrite_occupied,
    "diagonals_also": _diagonals_also,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "diagonal_cluster": _has_decoy("diagonal"),
    "occupied_center": _has_decoy("occupied"),
    "three_arms": _has_decoy("three_arms"),
    "mixed_arms": _has_decoy("mixed_arms"),
}
WITNESS_RIVALS = {
    "diagonal_cluster": ["horizontal_only", "vertical_only", "diagonals_also"],
    "occupied_center": ["overwrite_occupied"],
    "three_arms": ["three_arms"],
    "mixed_arms": ["mixed_majority"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
