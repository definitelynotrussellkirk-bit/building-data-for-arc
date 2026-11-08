"""Constructive sampler for ARC task ``cf4fdf474ad5``.

The unchanged authority extracts the color-8/color-3 patch with the greatest
number of green cells among patches whose bounding-box height is at most eight.
Equal green counts are resolved by smaller bounding-box area and then top-left
position.  This module creates inputs only; :func:`rule_mirror` and the declared
rivals are independent regression/teaching probes, not label authority.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf4fdf474ad5"
TASK_ID = GENERATOR_ID
RULE_HASH = "9316ff1c04fa"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Three or four separated solid rectangular patches use cyan 8 with green 3 "
    "overlays. Ignore patches taller than eight rows; among the remaining "
    "patches crop the one with the most green cells, breaking ties by smaller "
    "bounding-box area and then top-left position. Default scenes include a "
    "taller higher-green decoy, larger-area and denser valid decoys, and "
    "alternating equal-count area-tie witnesses."
)

INVARIANTS = [
    "integer rectangular 20..28 canvas using only colors 0, 3, and 8",
    "three or four separated fully occupied rectangular multicolor patches",
    "each patch is 5..10 rows by 7..11 columns and contains both 3 and 8",
    "at least one patch has bounding-box height at most eight",
    "the selected crop maximizes green count among valid-height patches",
    "ties use smaller bounding-box area, then top-left position",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-shape cycle", "valid": "22..28"},
    "grid_w": {"type": "int", "default": "canonical-shape cycle", "valid": "22..28"},
    "n_patches": {"type": "int", "default": "4", "valid": "3..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("unique", "tie_area")
_CANONICAL_CANVASES = ((24, 24), (23, 23), (22, 22), (22, 24))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Alternate unique-count and area-tie scenes independently of the seed."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _exact_dimension(ctx, name: str, preferred: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 22, 28)
    return ctx.draw_choice(name, (preferred,))


def _exact_patch_count(ctx) -> int:
    if ctx.overrides.get("n_patches") is not None:
        return ctx.draw_int_strict("n_patches", 3, 4)
    return ctx.draw_choice("n_patches", (4,))


def _paint_patch(
    grid: list[list[int]],
    *,
    top: int,
    left: int,
    height: int,
    width: int,
    green_count: int,
    rng,
) -> None:
    area = height * width
    if not 1 <= green_count < area:
        raise ValueError(f"green_count {green_count} outside 1..{area - 1}")
    cells = [(r, c) for r in range(top, top + height) for c in range(left, left + width)]
    for r, c in cells:
        grid[r][c] = 8
    for r, c in rng.sample(cells, green_count):
        grid[r][c] = 3


def _patch_specs(profile: str, difficulty, n_patches: int):
    winner_green = {"easy": 18, "medium": 23, "hard": 25, None: 23}[difficulty]
    # Scan order is deliberate: large valid, tall invalid, intended winner,
    # then the small dense decoy.  The winner is neither first nor last.
    specs = [
        {
            "role": "large_valid",
            "height": 8,
            "width": 11,
            "green": winner_green if profile == "tie_area" else winner_green - 1,
        },
        {
            "role": "tall_invalid",
            "height": 9,
            "width": 10,
            "green": winner_green + 2,
        },
        {
            "role": "winner",
            "height": 8,
            "width": 9 if profile == "tie_area" else 10,
            "green": winner_green,
        },
        {
            "role": "dense_valid",
            "height": 5,
            "width": 7,
            "green": 13 if winner_green >= 25 else 12,
        },
    ]
    return specs[:n_patches]


def _positions(h: int, w: int, specs: Sequence[dict[str, int]], rng):
    by_role = {str(spec["role"]): spec for spec in specs}
    large = by_role["large_valid"]
    tall = by_role["tall_invalid"]
    winner = by_role["winner"]
    dense = by_role.get("dense_valid")

    top_height = max(int(large["height"]), int(tall["height"]))
    bottom_height = max(int(winner["height"]), int(dense["height"]) if dense else 0)
    required_h = top_height + 1 + bottom_height
    required_w = int(large["width"]) + 1 + int(tall["width"])
    if h < required_h or w < required_w:
        raise ValueError(
            f"canvas {h}x{w} cannot fit constructive layout {required_h}x{required_w}"
        )
    row0 = rng.randint(0, h - required_h)
    col0 = rng.randint(0, w - required_w)
    bottom = row0 + top_height + 1
    result = {
        "large_valid": (row0, col0),
        "tall_invalid": (row0, col0 + int(large["width"]) + 1),
        "winner": (bottom, col0 + 1),
    }
    if dense:
        result["dense_valid"] = (
            bottom,
            col0 + required_w - int(dense["width"]),
        )
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful deterministic input without consulting the authority."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    preferred_h, preferred_w = _CANONICAL_CANVASES[sample_index % len(_CANONICAL_CANVASES)]
    h = _exact_dimension(ctx, "grid_h", preferred_h)
    w = _exact_dimension(ctx, "grid_w", preferred_w)
    n_patches = _exact_patch_count(ctx)
    profile = ctx.draw_choice(
        "curriculum_profile", (schedule_profile(seed, sample_index, difficulty),)
    )
    specs = _patch_specs(profile, difficulty, n_patches)
    layout = _positions(h, w, specs, ctx.draw_rng("layout"))
    grid = full_grid(h, w, 0)
    for spec in specs:
        role = str(spec["role"])
        top, left = layout[role]
        _paint_patch(
            grid,
            top=top,
            left=left,
            height=int(spec["height"]),
            width=int(spec["width"]),
            green_count=int(spec["green"]),
            rng=ctx.draw_rng(f"texture_{role}"),
        )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator produced invalid input: " + "; ".join(errors))
    return grid


def _components(grid: Sequence[Sequence[int]]):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    components = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            height = r2 - r1 + 1
            width = c2 - c1 + 1
            area = height * width
            n3 = sum(grid[r][c] == 3 for r, c in cells)
            n8 = sum(grid[r][c] == 8 for r, c in cells)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "height": height,
                    "width": width,
                    "area": area,
                    "size": len(cells),
                    "n3": n3,
                    "n8": n8,
                    "density": n3 / area,
                }
            )
    return components


def _winner(components):
    eligible = [component for component in components if component["height"] <= 8]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda component: (
            -component["n3"],
            component["area"],
            component["r1"],
            component["c1"],
        ),
    )


def _monochrome_object_count(grid: Sequence[Sequence[int]]) -> int:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    count = 0
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            count += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and grid[rr][cc] == color
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
    return count


def _analyze(grid: Sequence[Sequence[int]]):
    components = _components(grid)
    winner = _winner(components)
    return {"components": components, "winner": winner}


def _crop(grid: Sequence[Sequence[int]], component) -> list[list[int]]:
    return [
        list(row[component["c1"] : component["c2"] + 1])
        for row in grid[component["r1"] : component["r2"] + 1]
    ]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python reconstruction of the pinned Racket selection order."""
    winner = _winner(_components(grid))
    if winner is None:
        raise ValueError("input has no patch with bounding-box height at most eight")
    return _crop(grid, winner)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the reviewed task input grammar, including all canonical inputs."""
    del meta
    errors: list[str] = []
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append(f"invalid difficulty {difficulty!r}")
    if not isinstance(grid, (list, tuple)) or not grid:
        return errors + ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return errors + ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return errors + ["grid must be rectangular"]
    height = len(grid)
    if not (20 <= height <= 28 and 20 <= width <= 28):
        errors.append(f"canvas must be 20..28 by 20..28, got {height}x{width}")
    if any(type(value) is not int or value not in (0, 3, 8) for row in grid for value in row):
        errors.append("cells must be integer colors 0, 3, or 8 (not bool/float)")
        return errors

    components = _components(grid)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected three or four nonzero patches, got {len(components)}")
    for index, component in enumerate(components):
        if component["size"] != component["area"]:
            errors.append(f"patch {index} does not fully occupy its bounding box")
        if not 5 <= component["height"] <= 10:
            errors.append(f"patch {index} height {component['height']} outside 5..10")
        if not 7 <= component["width"] <= 11:
            errors.append(f"patch {index} width {component['width']} outside 7..11")
        if component["n3"] == 0 or component["n8"] == 0:
            errors.append(f"patch {index} must contain both colors 3 and 8")
    if _winner(components) is None:
        errors.append("at least one patch must have bounding-box height at most eight")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical canvas/patch manifold without replaying examples."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if not (22 <= h <= 24 and 20 <= w <= 24):
        reasons.append(f"canonical canvas range is 22..24 by 20..24, got {h}x{w}")
    analysis = _analyze(grid)
    winner = analysis["winner"]
    assert winner is not None
    if winner["height"] not in (7, 8):
        reasons.append(f"canonical winning height is seven or eight, got {winner['height']}")
    if not 10 <= winner["n3"] <= 30:
        reasons.append(f"canonical winning green count is 10..30, got {winner['n3']}")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    components = _components(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_patches": len(components)}


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    components = analysis["components"]
    winner = analysis["winner"]
    if winner is None:
        raise ValueError("no valid-height winner")
    eligible = [component for component in components if component["height"] <= 8]
    invalid = [component for component in components if component["height"] > 8]
    max_valid_green = max(component["n3"] for component in eligible)
    tied = [component for component in eligible if component["n3"] == max_valid_green]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_patches": len(components),
        "eligible_count": len(eligible),
        "invalid_tall_count": len(invalid),
        "invalid_max_green": max((component["n3"] for component in invalid), default=-1),
        "winner_green": winner["n3"],
        "winner_area": winner["area"],
        "winner_density": winner["density"],
        "winner_component_index": components.index(winner),
        "largest_valid_area": max(component["area"] for component in eligible),
        "highest_valid_density": max(component["density"] for component in eligible),
        "max_valid_green": max_valid_green,
        "max_valid_green_tied": len(tied) > 1,
        "profile": "tie_area" if len(tied) > 1 else "unique",
        "monochrome_object_count": _monochrome_object_count(grid),
    }


def _copy_grid(grid):
    return [list(row) for row in grid]


def _select(grid, components, key) -> list[list[int]]:
    if not components:
        return _copy_grid(grid)
    return _crop(grid, min(components, key=key))


def _rival_identity(grid):
    return _copy_grid(grid)


def _rival_max_green_any_height(grid):
    components = _components(grid)
    return _select(
        grid,
        components,
        lambda component: (
            -component["n3"],
            component["area"],
            component["r1"],
            component["c1"],
        ),
    )


def _rival_highest_density_valid(grid):
    components = [component for component in _components(grid) if component["height"] <= 8]
    return _select(
        grid,
        components,
        lambda component: (
            -component["density"],
            -component["n3"],
            component["area"],
            component["r1"],
            component["c1"],
        ),
    )


def _rival_largest_valid_area(grid):
    components = [component for component in _components(grid) if component["height"] <= 8]
    return _select(
        grid,
        components,
        lambda component: (
            -component["area"],
            -component["n3"],
            component["r1"],
            component["c1"],
        ),
    )


def _rival_first_valid(grid):
    components = [component for component in _components(grid) if component["height"] <= 8]
    return _select(grid, components, lambda component: (component["r1"], component["c1"]))


def _rival_top_left_on_tie(grid):
    """Canonical-fitting shortcut: ignores smaller-area tie-breaking."""
    components = [component for component in _components(grid) if component["height"] <= 8]
    return _select(
        grid,
        components,
        lambda component: (-component["n3"], component["r1"], component["c1"]),
    )


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _rival_identity,
    "max_green_any_height": _rival_max_green_any_height,
    "highest_density_valid": _rival_highest_density_valid,
    "largest_valid_area": _rival_largest_valid_area,
    "first_valid": _rival_first_valid,
    "top_left_on_tie": _rival_top_left_on_tie,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"top_left_on_tie": _rival_top_left_on_tie}


def _differs(grid, rival: Callable) -> bool:
    return rival(grid) != rule_mirror(grid)


def _height_gate(grid) -> bool:
    facts = semantic_observables(grid)
    return facts["invalid_max_green"] > facts["winner_green"] and _differs(
        grid, _rival_max_green_any_height
    )


def _absolute_count(grid) -> bool:
    facts = semantic_observables(grid)
    return facts["highest_valid_density"] > facts["winner_density"] and _differs(
        grid, _rival_highest_density_valid
    )


def _area_not_size(grid) -> bool:
    facts = semantic_observables(grid)
    return facts["largest_valid_area"] > facts["winner_area"] and _differs(
        grid, _rival_largest_valid_area
    )


def _not_first_patch(grid) -> bool:
    facts = semantic_observables(grid)
    return facts["winner_component_index"] != 0 and _differs(grid, _rival_first_valid)


def _smaller_area_tie_break(grid) -> bool:
    facts = semantic_observables(grid)
    return facts["max_valid_green_tied"] and _differs(grid, _rival_top_left_on_tie)


def _crop_extraction(grid) -> bool:
    return _differs(grid, _rival_identity)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "height_gate": _height_gate,
    "absolute_count": _absolute_count,
    "area_not_size": _area_not_size,
    "not_first_patch": _not_first_patch,
    "smaller_area_tie_break": _smaller_area_tie_break,
    "crop_extraction": _crop_extraction,
}
WITNESS_RIVALS = {
    "height_gate": ["max_green_any_height"],
    "absolute_count": ["highest_density_valid"],
    "area_not_size": ["largest_valid_area"],
    "not_first_patch": ["first_valid"],
    "smaller_area_tie_break": ["top_left_on_tie"],
    "crop_extraction": ["identity"],
}


def lesson_identifiable(demos: Iterable[dict], query: dict | None) -> list[str]:
    """Reject lessons where a named wrong rule fits demos but changes query."""
    demo_list = list(demos)
    reasons: list[str] = []
    for index, pair in enumerate(demo_list):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:  # pragma: no cover - defensive contract boundary
            reasons.append(f"demo {index} is outside the reviewed domain: {exc}")
            continue
        if expected != pair.get("output"):
            reasons.append(f"demo {index} label disagrees with the pinned rule mirror")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return reasons + ["query must be a labeled input/output pair"]
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demo_list)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons
