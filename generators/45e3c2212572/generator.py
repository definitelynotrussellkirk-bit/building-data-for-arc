"""Generator for ARC task 45e3c2212572 — pack four coloured L-trominoes.

Each input contains exactly one monochromatic 3-cell L-tromino in every
orientation.  Normalize each object's cells to its 2x2 bounding box, then copy
that normalized L into the output quadrant selected by the orientation:

* missing south-east corner -> output top-left,
* missing south-west corner -> output top-right,
* missing north-east corner -> output bottom-left,
* missing north-west corner -> output bottom-right.

The source positions are irrelevant.  The ordinary four-example schedule moves
orientations between source quadrants and permutes colour ranks, explicitly
refuting the plausible shortcut "topmost objects belong in the top output row"
that fits both public training demonstrations.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "45e3c2212572"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Hash of the currently selected canonical Racket program_solution.  The
# returned authority-sync patch updates this pin atomically with the selected
# commented source.
RULE_HASH = "d2dde893aca3"

SUMMARY = (
    "Find the four differently coloured 3-cell L-trominoes. Normalize each "
    "to a 2x2 box and copy it into a 4x4 output: missing SE -> top-left, "
    "missing SW -> top-right, missing NE -> bottom-left, and missing NW -> "
    "bottom-right. Source position and colour magnitude do not affect the map."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is 0",
    "the grid is rectangular and between 1x1 and 30x30",
    "exactly four nonzero 4-connected components are present",
    "each component is a monochromatic 3-cell L in a 2x2 bounding box",
    "all four missing-corner orientations occur exactly once",
    "the four objects use four distinct nonzero colours",
]

COUNTER_HYPOTHESES = [
    "sort objects by source row and put the top two in the top output row",
    "place objects according to their source quadrant",
    "sort colours by magnitude before filling output quadrants",
    "rotate or reflect each L instead of preserving its normalized orientation",
]

ORIENTATIONS = ("SE", "SW", "NE", "NW")
QUADRANTS = ("TL", "TR", "BL", "BR")

# Normalized cells keyed by the missing corner of the 2x2 box.
SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "NE": ((0, 0), (1, 0), (1, 1)),
    "NW": ((0, 1), (1, 0), (1, 1)),
    "SE": ((0, 0), (0, 1), (1, 0)),
    "SW": ((0, 0), (0, 1), (1, 1)),
}
SHAPE_TO_ORIENTATION = {frozenset(cells): name for name, cells in SHAPES.items()}
OUTPUT_QUADRANT = dict(zip(ORIENTATIONS, QUADRANTS))
QUADRANT_BASE = {"TL": (0, 0), "TR": (0, 2), "BL": (2, 0), "BR": (2, 2)}

LAYOUT_PROFILES = (
    "aligned",
    "vertical_flip",
    "horizontal_flip",
    "quarter_turn",
)
# orientation -> source quadrant.  Every profile is a permutation, so the
# generated objects stay widely separated while source position changes role.
_LAYOUT_MAPS: dict[str, dict[str, str]] = {
    "aligned": dict(zip(ORIENTATIONS, ("TL", "TR", "BL", "BR"))),
    "vertical_flip": dict(zip(ORIENTATIONS, ("BL", "BR", "TL", "TR"))),
    "horizontal_flip": dict(zip(ORIENTATIONS, ("TR", "TL", "BR", "BL"))),
    "quarter_turn": dict(zip(ORIENTATIONS, ("TR", "BR", "TL", "BL"))),
}

PALETTE_PROFILES = (
    "ascending",
    "descending",
    "rotate_left",
    "swap_pairs",
)
# Rank of the sorted four-colour nuisance palette assigned to ORIENTATIONS.
_PALETTE_RANKS: dict[str, tuple[int, int, int, int]] = {
    "ascending": (0, 1, 2, 3),
    "descending": (3, 2, 1, 0),
    "rotate_left": (1, 2, 3, 0),
    "swap_pairs": (1, 0, 3, 2),
}

_SCHEDULE = tuple(zip(LAYOUT_PROFILES, PALETTE_PROFILES))
SCHEDULE_PROFILES = tuple(f"{layout}/{palette}" for layout, palette in _SCHEDULE)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor 13; exact override 11..15",
        "valid": "11..15",
        "doc": "Exact input height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor 13; exact override 11..15",
        "valid": "11..15",
        "doc": "Exact input width.",
    },
    "layout_profile": {
        "type": "str",
        "default": "four-example schedule",
        "valid": "|".join(LAYOUT_PROFILES),
        "doc": "Exact permutation from L orientations to source quadrants.",
    },
    "palette_profile": {
        "type": "str",
        "default": "four-example schedule",
        "valid": "|".join(PALETTE_PROFILES),
        "doc": "Exact colour-rank permutation across the four orientations.",
    },
}

# Every exact-axis combination is supported; a rejection is therefore a bug.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared four-role lesson schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or isinstance(value, bool) or not 11 <= value <= 15
        ):
            raise ValueError(f"{name} must be an integer in [11, 15]")
    if overrides.get("layout_profile") is not None and overrides["layout_profile"] not in LAYOUT_PROFILES:
        raise ValueError(f"layout_profile must be one of {LAYOUT_PROFILES}")
    if overrides.get("palette_profile") is not None and overrides["palette_profile"] not in PALETTE_PROFILES:
        raise ValueError(f"palette_profile must be one of {PALETTE_PROFILES}")


def _quadrant_ranges(size: int) -> dict[str, tuple[int, int]]:
    """Legal 2x2 top-left ranges with a full zero moat at both midlines."""
    top = (1, size // 2 - 2)
    bottom = ((size + 1) // 2 + 1, size - 3)
    if top[0] > top[1] or bottom[0] > bottom[1]:
        raise AssertionError(f"internal quadrant layout does not fit size {size}")
    return {"T": top, "B": bottom}


def _draw_position(ctx, orientation: str, quadrant: str, h: int, w: int, difficulty: Any) -> tuple[int, int]:
    row_bands = _quadrant_ranges(h)
    col_bands = _quadrant_ranges(w)
    row_key, col_key = quadrant
    rlo, rhi = row_bands[row_key]
    clo, chi = col_bands["T" if col_key == "L" else "B"]
    # Difficulty changes only nuisance placement, never the grammar or exact
    # override domain.  Label-keyed RNG keeps the result deterministic.
    rng = ctx.draw_rng(f"position:{difficulty or 'default'}:{orientation}:{quadrant}")
    return rng.randint(rlo, rhi), rng.randint(clo, chi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)

    slot = int(sample_index) % len(_SCHEDULE)
    scheduled_layout, scheduled_palette = _SCHEDULE[slot]
    effective = dict(overrides)
    effective.setdefault("grid_h", 13)
    effective.setdefault("grid_w", 13)
    effective.setdefault("layout_profile", scheduled_layout)
    effective.setdefault("palette_profile", scheduled_palette)

    ctx = gen_ctx(
        seed=int(seed),
        sample_index=int(sample_index),
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 11, 15)
    w = ctx.draw_int("grid_w", 11, 15)
    layout_profile = ctx.draw_choice("layout_profile", LAYOUT_PROFILES)
    palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)

    nuisance_colors = sorted(ctx.draw_distinct_colors("object_colors", n=4, exclude={0}))
    ranks = _PALETTE_RANKS[palette_profile]
    colors = {
        orientation: nuisance_colors[ranks[index]]
        for index, orientation in enumerate(ORIENTATIONS)
    }

    grid = full_grid(h, w, 0)
    for orientation in ORIENTATIONS:
        source_quadrant = _LAYOUT_MAPS[layout_profile][orientation]
        top, left = _draw_position(
            ctx, orientation, source_quadrant, h, w, difficulty
        )
        for dr, dc in SHAPES[orientation]:
            if grid[top + dr][left + dc] != 0:
                raise AssertionError("internal layout bug: L-trominoes overlap")
            grid[top + dr][left + dc] = colors[orientation]

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "layout_profile": layout_profile,
        "palette_profile": palette_profile,
    }
    if observed != expected:
        raise AssertionError(f"observable axis mismatch: expected {expected}, got {observed}")
    return grid


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty rectangular sequence"], "components": []}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"], "components": []}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "components": []}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} must lie within 1..30")
    for row in grid:
        for value in row:
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colours 0..9")
                return {
                    "errors": errors,
                    "height": height,
                    "width": width,
                    "components": [],
                }

    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            colors = {grid[r][c] for r, c in cells}
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            normalized = frozenset((r - top, c - left) for r, c in cells)
            orientation = SHAPE_TO_ORIENTATION.get(normalized)
            obj_errors: list[str] = []
            if len(cells) != 3:
                obj_errors.append(f"component at ({top},{left}) has {len(cells)} cells, expected 3")
            if len(colors) != 1:
                obj_errors.append(f"component at ({top},{left}) is not monochromatic")
            if (bottom - top + 1, right - left + 1) != (2, 2):
                obj_errors.append(f"component at ({top},{left}) does not have a 2x2 bounding box")
            if orientation is None:
                obj_errors.append(f"component at ({top},{left}) is not a 3-cell L-tromino")
            errors.extend(obj_errors)
            components.append({
                "cells": tuple(sorted(cells)),
                "color": next(iter(colors)) if len(colors) == 1 else None,
                "top": top,
                "left": left,
                "bottom": bottom,
                "right": right,
                "normalized": tuple(sorted(normalized)),
                "orientation": orientation,
            })

    if len(components) != 4:
        errors.append(f"expected exactly 4 nonzero components, found {len(components)}")
    valid_orientations = [obj["orientation"] for obj in components if obj["orientation"] is not None]
    if len(components) == 4 and sorted(valid_orientations) != sorted(ORIENTATIONS):
        errors.append(
            "expected each missing-corner orientation exactly once; found "
            + repr(sorted(valid_orientations))
        )
    valid_colors = [obj["color"] for obj in components if obj["color"] is not None]
    if len(components) == 4 and len(valid_colors) == 4 and len(set(valid_colors)) != 4:
        errors.append(f"expected 4 distinct object colours, found {len(set(valid_colors))}")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": sorted(components, key=lambda obj: (obj["top"], obj["left"])),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task grammar; all canonical inputs are accepted."""
    del difficulty, meta
    return list(_analyze_scene(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """This task's semantic manifold is exactly the grammar checked above."""
    return self_check(grid)


def _source_quadrant(obj: dict[str, Any], height: int, width: int) -> str:
    center_r = (obj["top"] + obj["bottom"]) / 2
    center_c = (obj["left"] + obj["right"]) / 2
    return ("T" if center_r < height / 2 else "B") + (
        "L" if center_c < width / 2 else "R"
    )


def _classify_layout(analysis: dict[str, Any]) -> str:
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    realized = {
        obj["orientation"]: _source_quadrant(obj, analysis["height"], analysis["width"])
        for obj in analysis["components"]
    }
    matches = [name for name, mapping in _LAYOUT_MAPS.items() if realized == mapping]
    return matches[0] if len(matches) == 1 else "custom"


def _classify_palette(analysis: dict[str, Any]) -> str:
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    by_orientation = {obj["orientation"]: obj["color"] for obj in analysis["components"]}
    ordered_colors = [by_orientation[name] for name in ORIENTATIONS]
    sorted_colors = sorted(ordered_colors)
    ranks = tuple(sorted_colors.index(color) for color in ordered_colors)
    matches = [name for name, signature in _PALETTE_RANKS.items() if ranks == signature]
    return matches[0] if len(matches) == 1 else "custom"


def semantic_observables(grid) -> dict[str, Any]:
    """Recover exact controls and task-linked facts from a lawful input."""
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    orientation_colors = {
        obj["orientation"]: obj["color"] for obj in analysis["components"]
    }
    source_quadrants = {
        obj["orientation"]: _source_quadrant(obj, analysis["height"], analysis["width"])
        for obj in analysis["components"]
    }
    layout = _classify_layout(analysis)
    palette = _classify_palette(analysis)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "layout_profile": layout,
        "palette_profile": palette,
        "orientation_colors": orientation_colors,
        "source_quadrants": source_quadrants,
        "all_orientations": set(orientation_colors) == set(ORIENTATIONS),
        "vertical_rank_disagrees": rule_mirror(grid) != rival_vertical_rank(grid),
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    observed = {name: facts[name] for name in AXES}
    if observed["layout_profile"] == "custom" or observed["palette_profile"] == "custom":
        raise ValueError("generated scene does not encode a declared exact profile")
    return observed


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket rule for tests and analysis."""
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(analysis["errors"]))
    output = full_grid(4, 4, 0)
    for obj in analysis["components"]:
        base_r, base_c = QUADRANT_BASE[OUTPUT_QUADRANT[obj["orientation"]]]
        for dr, dc in obj["normalized"]:
            output[base_r + dr][base_c + dc] = obj["color"]
    return output


def rival_vertical_rank(grid) -> list[list[int]]:
    """Wrong but plausible: top two source objects go in the top output row.

    This reproduces both public training pairs.  The held-out canonical pair and
    the generated vertical/quarter-turn profiles refute it.
    """
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(analysis["errors"]))
    output = full_grid(4, 4, 0)
    for rank, obj in enumerate(analysis["components"]):
        base_r = 0 if rank < 2 else 2
        base_c = QUADRANT_BASE[OUTPUT_QUADRANT[obj["orientation"]]][1]
        for dr, dc in obj["normalized"]:
            output[base_r + dr][base_c + dc] = obj["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "vertical_rank": rival_vertical_rank,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _vertical_rank_counterexample(grid: Any) -> bool:
    try:
        return rule_mirror(grid) != rival_vertical_rank(grid)
    except ValueError:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "vertical_rank_counterexample": _vertical_rank_counterexample,
}
WITNESS_RIVALS = {
    "vertical_rank_counterexample": ["vertical_rank"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require four lawful demonstrations that eliminate every named rival."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson requires at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    profiles: set[str] = set()
    palette_profiles: set[str] = set()
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} lacks input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is outside the task grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the pinned rule")
        if index < len(demos):
            facts = semantic_observables(pair["input"])
            profiles.add(facts["layout_profile"])
            palette_profiles.add(facts["palette_profile"])
    if reasons:
        return reasons
    missing_layouts = sorted(set(LAYOUT_PROFILES) - profiles)
    if missing_layouts:
        reasons.append("demos omit layout profile(s): " + ", ".join(missing_layouts))
    missing_palettes = sorted(set(PALETTE_PROFILES) - palette_profiles)
    if missing_palettes:
        reasons.append("demos omit palette profile(s): " + ", ".join(missing_palettes))
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-specific malformed scenes that the teaching grammar must reject."""
    valid = generate(
        451_032,
        0,
        difficulty="medium",
        grid_h=13,
        grid_w=13,
        layout_profile="aligned",
        palette_profile="ascending",
    )
    facts = _analyze_scene(valid)
    components = facts["components"]
    by_orientation = {obj["orientation"]: obj for obj in components}
    fixtures: list[tuple[str, list[list[int]]]] = []

    duplicate_orientation = deepcopy(valid)
    victim = by_orientation["NE"]
    for r, c in victim["cells"]:
        duplicate_orientation[r][c] = 0
    for dr, dc in SHAPES["SE"]:
        duplicate_orientation[victim["top"] + dr][victim["left"] + dc] = victim["color"]
    fixtures.append(("duplicate_orientation_missing_ne", duplicate_orientation))

    straight_triomino = deepcopy(valid)
    victim = by_orientation["NW"]
    for r, c in victim["cells"]:
        straight_triomino[r][c] = 0
    for dc in range(3):
        straight_triomino[victim["top"]][victim["left"] + dc] = victim["color"]
    fixtures.append(("straight_triomino", straight_triomino))

    repeated_color = deepcopy(valid)
    victim = by_orientation["SW"]
    replacement = by_orientation["SE"]["color"]
    for r, c in victim["cells"]:
        repeated_color[r][c] = replacement
    fixtures.append(("repeated_object_color", repeated_color))

    attached_stray = deepcopy(valid)
    victim = by_orientation["SE"]
    candidate_cells = (
        (victim["bottom"] + 1, victim["left"]),
        (victim["top"], victim["right"] + 1),
    )
    stray = next(
        (r, c)
        for r, c in candidate_cells
        if 0 <= r < len(attached_stray)
        and 0 <= c < len(attached_stray[0])
        and attached_stray[r][c] == 0
    )
    attached_stray[stray[0]][stray[1]] = victim["color"]
    fixtures.append(("attached_fourth_cell", attached_stray))

    missing_cell = deepcopy(valid)
    victim = by_orientation["SW"]
    r, c = victim["cells"][0]
    missing_cell[r][c] = 0
    fixtures.append(("two_cell_component", missing_cell))

    return fixtures


def fresh_copy(grid) -> list[list[int]]:
    """Explicit fresh-return helper used by focused regression tests."""
    return deepcopy(grid)
