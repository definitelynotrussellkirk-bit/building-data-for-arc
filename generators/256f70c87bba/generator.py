"""Generator for H134 — commanded pivot rotations.

Each color-8 pivot reads the cell immediately to its left.  Values 1, 2, and
3 command that pivot's nearest colored components to rotate clockwise by that
many quarter-turns; every other value commands zero turns.  Color 1 is a pure
command marker and is removed before objects are found.  Values 2 and 3 (and
non-command values such as 4 or 5) remain ordinary object cells, so the left
cue itself may rotate as part of an object.

The four-example schedule deliberately covers commands 1, 2, and 3 plus a
non-command identity branch, with two independently commanded pivots in every
scene.  This rebuts object-color, global-command, fixed-position, and
"every pivot rotates" shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "256f70c87bba"
TASK_ID = GENERATOR_ID
RULE_HASH = "3bc100ea5852"
VERSION = "3.0.0"

SUMMARY = (
    "Find the color-8 pivots.  The cell immediately left of each pivot is its "
    "local command: 1, 2, or 3 means rotate every nearest colored component "
    "clockwise by that many quarter-turns; any other value means zero turns. "
    "Color 1 is only a command marker and disappears, while values 2, 3, and "
    "non-command colors remain object cells and move (or stay) with their "
    "components.  Output contains only pivots and the transformed components."
)

INVARIANTS = [
    "background is 0 and there are exactly two color-8 pivots",
    "each pivot has a nonzero non-8 cue immediately to its left",
    "after removing colors 1 and 8, every component has one unique nearest pivot",
    "each pivot owns at least one component and the two local cues are different",
    "at least one cue is 1, 2, or 3 and causes a visible in-bounds transformation",
    "transformed components do not overlap one another or either pivot",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

SCENE_PROFILES = (
    "command_1_and_2",
    "command_3_and_idle_4",
    "command_1_and_3",
    "command_2_and_idle_5",
)
_PROFILE_CUES = {
    "command_1_and_2": (1, 2),
    "command_3_and_idle_4": (3, 4),
    "command_1_and_3": (1, 3),
    "command_2_and_idle_5": (2, 5),
}
_PROFILE_BY_CUES = {cues: name for name, cues in _PROFILE_CUES.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled across the canonical 10..12 range",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled across the canonical 12..14 range",
        "valid": "12..14",
    },
    "scene_profile": {
        "type": "enum",
        "default": "four-example command schedule",
        "valid": [
            "command_1_and_2",
            "command_3_and_idle_4",
            "command_1_and_3",
            "command_2_and_idle_5",
        ],
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Relative object motifs.  Command 1 uses a separately colored object because
# the 1 marker is deleted before component extraction.  Every other cue is
# itself an object color and therefore appears in the motif at (0, -1).
_COMMAND_ONE_MOTIFS = (
    ((-2, 0), (-2, 1), (-1, 1)),
    ((-1, 2), (0, 2), (1, 2)),
    ((1, -2), (2, -2), (2, -1)),
    ((-1, -2), (-2, -2), (-2, -1)),
)
_EMBEDDED_CUE_MOTIFS = (
    ((0, -1), (-1, -1), (-1, 0)),
    ((0, -1), (1, -1), (1, 0)),
    ((0, -1), (-1, 0), (-2, 0)),
    ((0, -1), (1, 0), (2, 0)),
)
_COMMAND_ONE_COLORS = (4, 6, 7, 9)


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components_by_color(
    grid: list[list[int]], *, ignored: set[int]
) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in ignored or (r, c) in seen:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells: list[tuple[int, int]] = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _distance_to_component(
    pivot: tuple[int, int], cells: Iterable[tuple[int, int]]
) -> int:
    pr, pc = pivot
    return min(abs(pr - r) + abs(pc - c) for r, c in cells)


def _rotate_cells_cw(
    cells: Iterable[tuple[int, int]], pivot: tuple[int, int], turns: int
) -> tuple[tuple[int, int], ...]:
    pr, pc = pivot
    rotated: list[tuple[int, int]] = []
    for r, c in cells:
        cr, cc = r, c
        for _ in range(turns % 4):
            dr, dc = cr - pr, cc - pc
            cr, cc = pr + dc, pc - dr
        rotated.append((cr, cc))
    return tuple(sorted(rotated))


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}

    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    pivots = sorted(
        (r, c) for r in range(h) for c in range(w) if g[r][c] == 8
    )
    if len(pivots) != 2:
        errors.append(f"expected exactly two color-8 pivots, found {len(pivots)}")
        return {"errors": errors, "pivots": pivots}

    cues: list[int] = []
    marker_ones: set[tuple[int, int]] = set()
    for pr, pc in pivots:
        if pc == 0:
            errors.append(f"pivot at ({pr},{pc}) has no left cue cell")
            cues.append(0)
            continue
        cue = g[pr][pc - 1]
        cues.append(cue)
        if cue in (0, 8):
            errors.append(
                f"pivot at ({pr},{pc}) has invalid left cue {cue}; expected nonzero non-8"
            )
        if cue == 1:
            marker_ones.add((pr, pc - 1))

    all_ones = {
        (r, c) for r in range(h) for c in range(w) if g[r][c] == 1
    }
    stray_ones = sorted(all_ones - marker_ones)
    if stray_ones:
        errors.append(f"color-1 cells outside left-cue positions: {stray_ones[:4]}")
    if len(set(cues)) != len(cues):
        errors.append("the two pivots must carry different local cues")

    components = _components_by_color(g, ignored={0, 1, 8})
    if not components:
        errors.append("no colored components remain after removing 1 and 8")

    assigned: list[list[dict[str, Any]]] = [[], []]
    for component in components:
        distances = [
            _distance_to_component(pivot, component["cells"]) for pivot in pivots
        ]
        minimum = min(distances)
        owners = [index for index, value in enumerate(distances) if value == minimum]
        if len(owners) != 1:
            errors.append(
                f"component color {component['color']} is tied between pivots: {distances}"
            )
            continue
        owner = owners[0]
        component["owner"] = owner
        component["distance"] = minimum
        assigned[owner].append(component)

    for index, (pivot, cue) in enumerate(zip(pivots, cues)):
        if not assigned[index]:
            errors.append(f"pivot {pivot} owns no nearest component")
        if cue not in (0, 1, 8):
            cue_cell = (pivot[0], pivot[1] - 1)
            if not any(
                component["color"] == cue and cue_cell in component["cells"]
                for component in assigned[index]
            ):
                errors.append(
                    f"left cue {cue} at {cue_cell} is not in a component owned by its pivot"
                )

    transformed_occupancy: dict[tuple[int, int], tuple[int, int]] = {}
    moved_components = 0
    command_branches: set[int] = set()
    idle_branches = 0
    for owner, owner_components in enumerate(assigned):
        pivot = pivots[owner]
        cue = cues[owner]
        turns = cue if cue in (1, 2, 3) else 0
        if turns:
            command_branches.add(turns)
        else:
            idle_branches += 1
        for component in owner_components:
            rotated = _rotate_cells_cw(component["cells"], pivot, turns)
            component["rotated_cells"] = rotated
            component["turns"] = turns
            if rotated != component["cells"]:
                moved_components += 1
            for cell in rotated:
                r, c = cell
                if not (0 <= r < h and 0 <= c < w):
                    errors.append(
                        f"component color {component['color']} rotates out of bounds to {cell}"
                    )
                    continue
                if cell in pivots:
                    errors.append(
                        f"component color {component['color']} rotates onto pivot {cell}"
                    )
                if cell in transformed_occupancy:
                    prior = transformed_occupancy[cell]
                    errors.append(
                        f"transformed components overlap at {cell} (owners {prior[0]} and {owner})"
                    )
                else:
                    transformed_occupancy[cell] = (owner, component["color"])

    if not command_branches:
        errors.append("no pivot has an active 1/2/3 command")
    if moved_components == 0:
        errors.append("active commands produce no visible component movement")

    profile = _PROFILE_BY_CUES.get(tuple(cues))
    return {
        "errors": errors,
        "grid": g,
        "h": h,
        "w": w,
        "pivots": tuple(pivots),
        "cues": tuple(cues),
        "profile": profile,
        "components": components,
        "assigned": assigned,
        "command_branches": command_branches,
        "idle_branches": idle_branches,
        "moved_components": moved_components,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full two-pivot teaching grammar and its transformed scene."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical dimensions in addition to the structural grammar."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if not 10 <= analysis["h"] <= 12:
        reasons.append(f"height {analysis['h']} is outside canonical 10..12")
    if not 12 <= analysis["w"] <= 14:
        reasons.append(f"width {analysis['w']} is outside canonical 12..14")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    if analysis["profile"] is None:
        raise ValueError(f"cue pair {analysis['cues']} is outside SCENE_PROFILES")
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "scene_profile": analysis["profile"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    """Task-linked observables used by focused tests and the review census."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {
        **observe_overrides(grid),
        "cues": list(analysis["cues"]),
        "command_branches": sorted(analysis["command_branches"]),
        "has_idle_branch": bool(analysis["idle_branches"]),
        "moved_components": analysis["moved_components"],
        "component_count": len(analysis["components"]),
        "detached_component": any(
            component["distance"] >= 2 for component in analysis["components"]
        ),
    }


def _scheduled_offset(seed: int, label: str, modulus: int) -> int:
    return stable_rng(seed, f"{TASK_ID}|{label}", VERSION).randrange(modulus)


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _paint_relative(
    grid: list[list[int]], pivot: tuple[int, int],
    cells: Iterable[tuple[int, int]], color: int,
) -> None:
    pr, pc = pivot
    for dr, dc in cells:
        r, c = pr + dr, pc + dc
        if grid[r][c] not in (0, color):
            raise AssertionError(f"construction collision at {(r, c)}")
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    band_offset = {"easy": 0, "medium": 1, "hard": 2}[band]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    profile = _draw_scheduled_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        SCENE_PROFILES[
            (_scheduled_offset(seed, "scene_profile", len(SCENE_PROFILES)) + int(sample_index) + band_offset)
            % len(SCENE_PROFILES)
        ],
    )
    h = _draw_scheduled_int(
        ctx,
        "grid_h",
        10,
        12,
        10 + ((_scheduled_offset(seed, "grid_h", 3) + int(sample_index) + band_offset) % 3),
    )
    w = _draw_scheduled_int(
        ctx,
        "grid_w",
        12,
        14,
        12 + ((_scheduled_offset(seed, "grid_w", 3) + 2 * int(sample_index) + band_offset) % 3),
    )

    layout_rng = ctx.draw_rng(f"layout:{band}")
    # The two safe zones preserve a wide nearest-pivot margin while allowing
    # visible position variation.  Row-major ordering stays stable, which makes
    # the command profile exactly observable.
    pivot_a = (2 + layout_rng.randrange(2), 3 + layout_rng.randrange(2))
    pivot_b = (
        h - 4 + layout_rng.randrange(2),
        w - 5 + layout_rng.randrange(2),
    )
    pivots = (pivot_a, pivot_b)
    cues = _PROFILE_CUES[profile]

    grid = full_grid(h, w, 0)
    used_command_one_colors: set[int] = set()
    for index, (pivot, cue) in enumerate(zip(pivots, cues)):
        pr, pc = pivot
        grid[pr][pc] = 8
        motif_index = (
            _scheduled_offset(seed, f"motif:{index}", len(_EMBEDDED_CUE_MOTIFS))
            + int(sample_index)
            + band_offset
        ) % len(_EMBEDDED_CUE_MOTIFS)
        if cue == 1:
            grid[pr][pc - 1] = 1
            choices = [color for color in _COMMAND_ONE_COLORS if color not in cues]
            choices = [color for color in choices if color not in used_command_one_colors]
            if not choices:
                choices = list(_COMMAND_ONE_COLORS)
            object_color = layout_rng.choice(choices)
            used_command_one_colors.add(object_color)
            motif = _COMMAND_ONE_MOTIFS[motif_index]
            _paint_relative(grid, pivot, motif, object_color)
        else:
            motif = _EMBEDDED_CUE_MOTIFS[motif_index]
            _paint_relative(grid, pivot, motif, cue)

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "scene_profile": profile}
    if observed != expected:
        raise AssertionError(f"constructed axes drifted: expected {expected}, observed {observed}")
    return grid


def _expected_output(grid: Any) -> list[list[int]]:
    """Python mirror for semantic checks only; the Racket rule remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["h"], analysis["w"], 0)
    for r, c in analysis["pivots"]:
        out[r][c] = 8
    for component in analysis["components"]:
        for r, c in component["rotated_cells"]:
            out[r][c] = component["color"]
    return out


def _witness_command(turns: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and turns in analysis["command_branches"]

    return predicate


SEMANTIC_WITNESSES = {
    "command_1": _witness_command(1),
    "command_2": _witness_command(2),
    "command_3": _witness_command(3),
    "noncommand_identity_branch": lambda grid: (
        not _analyze(grid)["errors"] and bool(_analyze(grid)["idle_branches"])
    ),
    "independent_mixed_commands": lambda grid: (
        not _analyze(grid)["errors"] and len(set(_analyze(grid)["cues"])) == 2
    ),
    "detached_component": lambda grid: (
        not _analyze(grid)["errors"]
        and any(component["distance"] >= 2 for component in _analyze(grid)["components"])
    ),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to identify local cue semantics and all branches."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    analyses: list[dict[str, Any]] = []
    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        analysis = _analyze(pair.get("input"))
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if pair.get("output") != _expected_output(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the canonical rule")
        analyses.append(analysis)
        if analysis["profile"] is not None:
            profiles.add(analysis["profile"])

    cue_values = {cue for analysis in analyses for cue in analysis["cues"]}
    missing_commands = sorted({1, 2, 3} - cue_values)
    if missing_commands:
        reasons.append(f"demonstrations omit command values {missing_commands}")
    if not any(cue > 3 for cue in cue_values):
        reasons.append("demonstrations omit the non-command identity branch")
    if len(profiles) < len(SCENE_PROFILES):
        reasons.append("demonstrations do not cover all four command profiles")

    # Rebut the tempting object-color shortcut: a non-1 colored object must
    # rotate under a separate cue 1, while a >3 colored cue/object must stay.
    has_separate_command_one = any(
        cue == 1
        and any(component["owner"] == owner and component["color"] != 1
                and component["rotated_cells"] != component["cells"]
                for component in analysis["components"])
        for analysis in analyses
        for owner, cue in enumerate(analysis["cues"])
    )
    if not has_separate_command_one:
        reasons.append("no demo rebuts the object-color shortcut for command 1")
    has_idle_object = any(
        cue > 3
        and any(component["owner"] == owner
                and component["rotated_cells"] == component["cells"]
                for component in analysis["components"])
        for analysis in analyses
        for owner, cue in enumerate(analysis["cues"])
    )
    if not has_idle_object:
        reasons.append("no demo proves that non-command cues leave objects unchanged")

    query_analysis = _analyze(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside the teaching grammar")
    else:
        if query_analysis["profile"] not in profiles:
            reasons.append("query command profile was not demonstrated")
        if query.get("output") != _expected_output(query["input"]):
            reasons.append("query output disagrees with the canonical rule")

    return sorted(set(reasons))
