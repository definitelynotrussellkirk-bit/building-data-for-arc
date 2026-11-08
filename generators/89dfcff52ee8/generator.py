"""Generator for ARC task 89dfcff52ee8 (horizontal span closure).

Every nonzero input cell is a marker.  On each active row, the reference rule
paints the inclusive interval from the leftmost marker to the rightmost marker
with cyan (8) on an otherwise blank, same-size output.  A singleton row is a
lawful one-cell interval; the canonical training data contains one.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "89dfcff52ee8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
SUMMARY = "Sparse row markers expand to inclusive horizontal spans, including singleton rows."

INVARIANTS = [
    "every nonzero cell is a marker, regardless of marker color",
    "each active row contributes its inclusive leftmost-to-rightmost interval",
    "singleton active rows contribute one cyan output cell",
    "the output is a blank same-size grid with the union of row intervals painted 8",
]

TEXTURES = ("balanced", "singleton_mix", "boundary_contacts")
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty keyed", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "difficulty keyed", "valid": "7..30"},
    "active_rows": {"type": "int", "default": "difficulty keyed", "valid": "2..6"},
    "texture": {"type": "str", "default": "keyed choice", "valid": "|".join(TEXTURES)},
}


def _strict_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _strict_int(seed, "seed", -(2**63), 2**63 - 1)
    _strict_int(sample_index, "sample_index", 0, 2**63 - 1)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, low, high in (("grid_h", 6, 30), ("grid_w", 7, 30), ("active_rows", 2, 6)):
        if name in overrides and overrides[name] is not None:
            _strict_int(overrides[name], name, low, high)
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str or value not in TEXTURES:
            raise ValueError(f"texture must be one of {TEXTURES}")


def _default_ranges(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 8), (7, 10), (2, 3)
    if difficulty == "hard":
        return (14, 30), (16, 30), (4, 6)
    return (8, 14), (10, 18), (3, 4)


def _draw_dimension(ctx, overrides: dict[str, Any], name: str, default: tuple[int, int], global_: tuple[int, int]) -> int:
    lo, hi = global_ if overrides.get(name) is not None else default
    return ctx.draw_int_strict(name, lo, hi)


def _span(rng, width: int, *, boundary_left: bool, boundary_right: bool) -> tuple[int, int]:
    if boundary_left:
        left = 0
    else:
        left = rng.randint(1, max(1, width // 3))
    if boundary_right:
        right = width - 1
    else:
        right_low = max(left + 2, width // 2)
        right = rng.randint(right_low, width - 2)
    if right - left < 2:
        raise RuntimeError("constructed span is too short")
    return left, right


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a lawful teaching input with strict, observable controls."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_range, w_range, n_range = _default_ranges(difficulty)
    h = _draw_dimension(ctx, overrides, "grid_h", h_range, (6, 30))
    w = _draw_dimension(ctx, overrides, "grid_w", w_range, (7, 30))
    n = _draw_dimension(ctx, overrides, "active_rows", n_range, (2, 6))
    if n > h:
        raise ValueError("active_rows cannot exceed grid_h")
    texture = ctx.draw_choice("texture", TEXTURES)

    layout = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    rows = sorted(layout.sample(range(h), n))
    grid = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    color_rng.shuffle(colors)
    color_cursor = 0

    singleton_index = layout.randrange(n) if texture == "singleton_mix" else None
    for index, row in enumerate(rows):
        if index == singleton_index:
            col = layout.randint(1, w - 2)
            grid[row][col] = colors[color_cursor % len(colors)]
            color_cursor += 1
            continue

        left, right = _span(
            layout,
            w,
            boundary_left=texture == "boundary_contacts" and index == 0,
            boundary_right=texture == "boundary_contacts" and index == n - 1,
        )
        marker_cols = [left, right]
        if right - left >= 4 and layout.random() < 0.75:
            marker_cols.append(layout.randint(left + 1, right - 1))
        if right - left >= 7 and layout.random() < 0.35:
            available = [c for c in range(left + 1, right) if c not in marker_cols]
            if available:
                marker_cols.append(layout.choice(available))
        for col in sorted(marker_cols):
            grid[row][col] = colors[color_cursor % len(colors)]
            color_cursor += 1

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _analysis(grid: object) -> dict[str, Any]:
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    active: list[dict[str, Any]] = []
    for r, row in enumerate(grid):
        bad = [value for value in row if type(value) is not int or not 0 <= value <= 9]
        if bad:
            errors.append(f"row {r} contains a non-ARC or non-integer cell")
        cols = [c for c, value in enumerate(row) if type(value) is int and value != 0]
        if cols:
            active.append({"row": r, "cols": cols, "left": min(cols), "right": max(cols)})
    return {
        "errors": errors,
        "height": len(grid),
        "width": width,
        "active": active,
        "singleton_rows": sum(len(item["cols"]) == 1 for item in active),
        "has_left_boundary": any(item["left"] == 0 for item in active),
        "has_right_boundary": any(item["right"] == width - 1 for item in active),
    }


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides on an invalid grid")
    if analysis["singleton_rows"]:
        texture = "singleton_mix"
    elif analysis["has_left_boundary"] and analysis["has_right_boundary"]:
        texture = "boundary_contacts"
    else:
        texture = "balanced"
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "active_rows": len(analysis["active"]),
        "texture": texture,
    }


def rule_mirror(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for item in analysis["active"]:
        for col in range(item["left"], item["right"] + 1):
            output[item["row"]][col] = 8
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if "height" not in analysis:
        return errors
    if not 1 <= analysis["height"] <= 30 or not 1 <= analysis["width"] <= 30:
        errors.append("grid dimensions must be within the ARC 1..30 limit")
    active = analysis["active"]
    if not 1 <= len(active) <= 6:
        errors.append(f"expected 1..6 active rows, got {len(active)}")
    if active and not any(item["right"] - item["left"] >= 2 for item in active):
        errors.append("at least one active row must teach a nontrivial horizontal span")
    if any(value == 8 for row in grid for value in row if type(value) is int):
        errors.append("input should not contain output fill color 8")
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be None, easy, medium, or hard")

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(overrides, dict):
        try:
            observed = observe_overrides(grid)
        except ValueError:
            observed = {}
        for name, expected in overrides.items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                errors.append(f"override {name}={expected!r} was not realized (got {observed.get(name)!r})")
    return errors
