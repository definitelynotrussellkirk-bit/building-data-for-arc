"""Semantic generator for ARC task de8785512d06 (source task f8f52ecc).

Repeated cells of each ordinary color are terminals of one network.  For each
color independently, the canonical rule starts at the first terminal in
reading order and repeatedly attaches one remaining terminal to the existing
network by the shortest valid horizontal/vertical L path.  Color 8 is a wall,
the modal color is background, and any other non-background color also blocks
a path belonging to a different color.  When both L bends are available, the
already-painted row/column through the source terminal determines the preferred
bend; if that bend is blocked, the other one is used.  Singleton colors and
wall cells are left alone.

The old v1.3 generator emitted only two same-row/same-column terminals per
color.  Consequently the lesson could be solved by the shortcut "draw straight
segments between aligned equal colors" and almost never exercised the actual L
routing, multi-terminal tree construction, or bend preference.  This version
keeps one third of the stream on the five linked public morphology profiles,
uses a branch-rich vertical-wall control every third sample, and uses a fully
procedural network for the remaining third.  Every three-demo sliding lesson
therefore contains a control that kills the named shortcut rules.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "de8785512d06"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
# Pinned to the exact current selected Racket source across all active carriers.
RULE_HASH = "36c7f3a6c69b"

SUMMARY = (
    "Connect every repeated non-background/non-8 color into one obstacle-aware "
    "L-path tree; choose the shortest available attachment, use the existing "
    "same-color row/column to choose an open bend, and preserve color-8 walls "
    "and singleton distractor colors."
)

INVARIANTS = [
    "the modal color is background and color 8 is reserved for straight wall components",
    "every repeated active color occupies at least two disconnected input components",
    "paths may paint only original background or cells of their own color, never walls or other colors",
    "each repeated color gains at least one path cell while singleton colors remain unchanged",
    "multi-terminal colors are attached to the existing tree, not handled as independent terminal pairs",
    "the returned stream contains both public-profile morphology and obstacle/orientation counterexamples",
]

# ---------------------------------------------------------------------------
# Canonical linked morphology profiles
# ---------------------------------------------------------------------------

# A profile stores the *linked* facts measured from one unique public input:
# dimensions, palette size, per-color 4-connected component-size partitions,
# and wall-component sizes.  Active color labels themselves are a nuisance
# variable for the rule, so generated anchors may permute them while preserving
# the multiset of component partitions.
_CANONICAL_PROFILE_SPECS: dict[str, dict[str, object]] = {
    "canon_10x10_single": {
        "dims": (10, 10),
        "active_parts": ((2, 1, 1),),
        "wall_parts": (6,),
    },
    "canon_10x10_multi": {
        "dims": (10, 10),
        "active_parts": ((3, 1, 1), (2, 1), (1,)),
        "wall_parts": (3,),
    },
    "canon_12x12_full": {
        "dims": (12, 12),
        "active_parts": ((1, 1, 1), (1,), (1, 1), (1,), (1, 1, 1), (1,), (1, 1, 1)),
        "wall_parts": (8, 8),
    },
    "canon_8x10_sparse": {
        "dims": (8, 10),
        "active_parts": ((1,), (1, 1, 1, 1), (1,), (1,), (1, 1), (1,)),
        "wall_parts": (2, 1),
    },
    "canon_12x12_multi": {
        "dims": (12, 12),
        "active_parts": ((2, 2, 1), (1, 1, 1, 1), (1, 1), (1,), (1,), (1,)),
        "wall_parts": (6, 5),
    },
}

CANONICAL_PROFILES = tuple(_CANONICAL_PROFILE_SPECS)
CONTROL_PROFILE = "control_12x12_vertical"
RANDOM_PROFILE = "general_12x12_network"
PROFILE_NAMES = CANONICAL_PROFILES + (CONTROL_PROFILE, RANDOM_PROFILE)

# The public examples use background 1 and horizontal 8-walls.  Color renaming
# among ordinary colors is semantics-preserving, but strict_canonical_like keeps
# the public background/wall roles and the complete linked morphology exact.
_CANONICAL_ACTIVE_LABELS = (0, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index schedule: public anchor / vertical-wall control / procedural network",
        "valid": "canon_10x10_single|canon_10x10_multi|canon_12x12_full|canon_8x10_sparse|canon_12x12_multi|control_12x12_vertical|general_12x12_network",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Every three consecutive demonstrations include the middle control slot.
EXAMPLES_NEEDED = 3
_SCHEDULE = tuple(
    item
    for canonical in CANONICAL_PROFILES
    for item in (canonical, CONTROL_PROFILE, RANDOM_PROFILE)
)
SCHEDULE_PROFILES = PROFILE_NAMES
MIN_STRICT_FRAC = 0.25

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


# ---------------------------------------------------------------------------
# Grid / morphology helpers
# ---------------------------------------------------------------------------

def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell {(r, c)} is not an ARC color 0..9: {value!r}"]
    return []


def _mode(grid) -> int:
    counts = Counter(value for row in grid for value in row)
    # Counter.most_common preserves first encounter on equal counts, matching
    # the canonical inputs' unique modal background while remaining deterministic.
    return counts.most_common(1)[0][0]


def _cells_of(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _components_for_cells(cells: Iterable[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    unseen = set(cells)
    found: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        found.append(tuple(sorted(component)))
    return sorted(found, key=lambda component: component[0])


def _component_parts(grid, color: int) -> tuple[int, ...]:
    return tuple(sorted((len(component) for component in _components_for_cells(_cells_of(grid, color))), reverse=True))


def _straight_component(component: Iterable[tuple[int, int]]) -> bool:
    cells = list(component)
    return len({r for r, _ in cells}) == 1 or len({c for _, c in cells}) == 1


def _wall_orientations(grid) -> tuple[str, ...]:
    orientations: list[str] = []
    for component in _components_for_cells(_cells_of(grid, 8)):
        rows = {r for r, _ in component}
        cols = {c for _, c in component}
        if len(component) == 1:
            orientations.append("point")
        elif len(rows) == 1:
            orientations.append("h")
        elif len(cols) == 1:
            orientations.append("v")
        else:
            orientations.append("bent")
    return tuple(sorted(orientations))


def _morphology(grid) -> dict[str, object]:
    bg = _mode(grid)
    colors = sorted({value for row in grid for value in row})
    active = [color for color in colors if color not in (bg, 8)]
    return {
        "dims": (len(grid), len(grid[0])),
        "bg": bg,
        "palette_size": len(colors),
        "active_parts": tuple(sorted((_component_parts(grid, color) for color in active), reverse=True)),
        "wall_parts": _component_parts(grid, 8) if 8 in colors else (),
        "wall_orientations": _wall_orientations(grid) if 8 in colors else (),
        "active_colors": tuple(active),
    }


def _canonical_profile_from_morphology(grid) -> str | None:
    facts = _morphology(grid)
    if facts["bg"] != 1:
        return None
    wall_orientations = facts["wall_orientations"]
    if any(orientation not in {"h", "point"} for orientation in wall_orientations):
        return None
    for name, spec in _CANONICAL_PROFILE_SPECS.items():
        if facts["dims"] != spec["dims"]:
            continue
        if facts["active_parts"] != tuple(sorted(spec["active_parts"], reverse=True)):
            continue
        if facts["wall_parts"] != tuple(sorted(spec["wall_parts"], reverse=True)):
            continue
        return name
    return None


def _profile_of(grid) -> str | None:
    canonical = _canonical_profile_from_morphology(grid)
    if canonical is not None:
        return canonical
    facts = _morphology(grid)
    p3 = _CANONICAL_PROFILE_SPECS["canon_12x12_full"]
    if (
        facts["dims"] == p3["dims"]
        and facts["bg"] == 1
        and facts["active_parts"] == tuple(sorted(p3["active_parts"], reverse=True))
        and facts["wall_parts"] == tuple(sorted(p3["wall_parts"], reverse=True))
        and facts["wall_orientations"] == ("v", "v")
    ):
        return CONTROL_PROFILE
    if (
        facts["dims"] == (12, 12)
        and facts["bg"] == 1
        and facts["palette_size"] == 9
        and facts["wall_parts"] == (4, 3, 2)
    ):
        return RANDOM_PROFILE
    return None


# ---------------------------------------------------------------------------
# Independent Python mirror of the selected Racket rule.
# The Racket program remains the sole output authority used by materialization.
# ---------------------------------------------------------------------------

def _between(a: int, b: int) -> list[int]:
    return list(range(min(a, b), max(a, b) + 1))


def _candidate_paths(a: tuple[int, int], b: tuple[int, int]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    r1, c1 = a
    r2, c2 = b
    path_h = [(r1, c) for c in _between(c1, c2)] + [(r, c2) for r in _between(r1, r2)]
    path_v = [(r, c1) for r in _between(r1, r2)] + [(r2, c) for c in _between(c1, c2)]
    return path_h, path_v


def _path_valid(grid, path: Iterable[tuple[int, int]], *, bg: int, color: int, allow_walls: bool = False) -> bool:
    allowed = {bg, color}
    if allow_walls:
        allowed.add(8)
    return all(grid[r][c] in allowed for r, c in path)


def _has_row(out, r: int, c: int, color: int) -> bool:
    return any(cc != c and out[r][cc] == color for cc in range(len(out[0])))


def _has_col(out, r: int, c: int, color: int) -> bool:
    return any(rr != r and out[rr][c] == color for rr in range(len(out)))


def _path_for(
    grid,
    out,
    a: tuple[int, int],
    b: tuple[int, int],
    color: int,
    *,
    bg: int,
    bend_policy: str = "canonical",
    allow_walls: bool = False,
) -> tuple[list[tuple[int, int]], dict[str, object]]:
    path_h, path_v = _candidate_paths(a, b)
    ok_h = _path_valid(grid, path_h, bg=bg, color=color, allow_walls=allow_walls)
    ok_v = _path_valid(grid, path_v, bg=bg, color=color, allow_walls=allow_walls)
    r1, c1 = a
    has_row = _has_row(out, r1, c1, color)
    has_col = _has_col(out, r1, c1, color)
    prefer_h = has_row or not has_col
    if bend_policy == "always_h":
        prefer_h = True
    elif bend_policy == "always_v":
        prefer_h = False

    chosen = "blocked"
    path: list[tuple[int, int]] = []
    if prefer_h and ok_h:
        path, chosen = path_h, "h"
    elif (not prefer_h) and ok_v:
        path, chosen = path_v, "v"
    elif ok_h:
        path, chosen = path_h, "h_fallback"
    elif ok_v:
        path, chosen = path_v, "v_fallback"
    return path, {
        "a": a,
        "b": b,
        "ok_h": ok_h,
        "ok_v": ok_v,
        "prefer_h": prefer_h,
        "has_row": has_row,
        "has_col": has_col,
        "chosen": chosen,
        "unaligned": a[0] != b[0] and a[1] != b[1],
    }


def _solve(
    grid,
    *,
    bend_policy: str = "canonical",
    allow_walls: bool = False,
    first_two_only: bool = False,
    newest_source_only: bool = False,
    trace: bool = False,
):
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    bg = _mode(grid)
    colors = sorted({value for row in grid for value in row if value not in (bg, 8)})
    out = [list(row) for row in grid]
    events: list[dict[str, object]] = []

    for color in colors:
        points = _cells_of(grid, color)
        if first_two_only:
            points = points[:2]
        if len(points) < 2:
            continue
        tree = [points[0]]
        remaining = points[1:]
        while remaining:
            sources = tree[:1] if newest_source_only else tree
            candidates: list[tuple[int, tuple[int, int], tuple[int, int], list[tuple[int, int]], dict[str, object], int]] = []
            for source_index, a in enumerate(sources):
                for b in remaining:
                    path, detail = _path_for(
                        grid,
                        out,
                        a,
                        b,
                        color,
                        bg=bg,
                        bend_policy=bend_policy,
                        allow_walls=allow_walls,
                    )
                    length = len(path) if path else 999
                    key = (
                        length * 1_000_000
                        + a[0] * 10_000
                        + a[1] * 100
                        + b[0] * 10
                        + b[1]
                    )
                    candidates.append((key, a, b, path, detail, source_index))
            _, a, b, path, detail, source_index = min(candidates, key=lambda candidate: candidate[0])
            before = [out[r][c] for r, c in path]
            for r, c in path:
                out[r][c] = color
            if trace:
                event = dict(detail)
                event.update({
                    "color": color,
                    "source_index": source_index,
                    "candidate_count": len(candidates),
                    "new_cells": sum(value == bg for value in before),
                    "path_len": len(path),
                })
                events.append(event)
            tree.insert(0, b)
            remaining = [point for point in remaining if point != b]
    return (out, events) if trace else out


def rule_mirror(grid):
    """Independent parity/test mirror; never called by generate for outputs."""
    return _solve(grid)


# ---------------------------------------------------------------------------
# Structural grammar and task-linked semantic contract
# ---------------------------------------------------------------------------

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 16 and 8 <= width <= 17):
        errors.append(f"grid dimensions {height}x{width} outside supported 8..16 by 8..17 envelope")

    bg = _mode(grid)
    if bg == 8:
        errors.append("color 8 must be a wall, not the modal background")
    colors = sorted({value for row in grid for value in row})
    if 8 not in colors:
        errors.append("at least one color-8 wall component is required")
    else:
        for index, component in enumerate(_components_for_cells(_cells_of(grid, 8))):
            if not _straight_component(component):
                errors.append(f"wall component {index} is bent; teaching walls must be straight runs")

    active = [color for color in colors if color not in (bg, 8)]
    repeated = [color for color in active if len(_cells_of(grid, color)) >= 2]
    if not repeated:
        errors.append("no repeated active color to connect")

    output = None
    try:
        output = _solve(grid)
    except Exception as exc:  # fail loud in the checker rather than hiding malformed grids
        errors.append(f"rule mirror could not evaluate the grid: {exc}")

    if output is not None:
        total_new = 0
        for color in active:
            cells = _cells_of(grid, color)
            out_cells = _cells_of(output, color)
            if len(cells) == 1:
                if out_cells != cells:
                    errors.append(f"singleton color {color} would not remain unchanged")
                continue
            components = _components_for_cells(cells)
            if len(components) < 2:
                errors.append(f"repeated color {color} is already one connected input component")
            added = len(out_cells) - len(cells)
            if added <= 0:
                errors.append(f"repeated color {color} gains no path cells")
            total_new += max(0, added)
        if total_new == 0:
            errors.append("the canonical rule would be an identity on this grid")
        if any(output[r][c] != 8 for r, c in _cells_of(grid, 8)):
            errors.append("a routed path would overwrite a color-8 wall")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = _canonical_profile_from_morphology(grid)
    if profile is None:
        facts = _morphology(grid)
        reasons.append(
            "grid does not match any linked public morphology profile "
            f"(dims={facts['dims']}, active_parts={facts['active_parts']}, wall_parts={facts['wall_parts']}, "
            f"wall_orientations={facts['wall_orientations']})"
        )
    return reasons


def canonical_profile_signature(grid):
    return _canonical_profile_from_morphology(grid)


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("grid does not match any declared scene_profile")
    return {"scene_profile": profile}


def _trace(grid) -> list[dict[str, object]]:
    _out, events = _solve(grid, trace=True)
    return events


def _witness_h_preference(grid) -> bool:
    if self_check(grid):
        return False
    return any(
        event["unaligned"] and event["ok_h"] and event["ok_v"]
        and event["prefer_h"] and event["chosen"] == "h"
        for event in _trace(grid)
    )


def _witness_v_preference(grid) -> bool:
    if self_check(grid):
        return False
    return any(
        event["unaligned"] and event["ok_h"] and event["ok_v"]
        and not event["prefer_h"] and event["chosen"] == "v"
        for event in _trace(grid)
    )


def _witness_forced_detour(grid) -> bool:
    if self_check(grid):
        return False
    structural = any(
        event["unaligned"] and (event["ok_h"] != event["ok_v"])
        and event["chosen"] != "blocked"
        for event in _trace(grid)
    )
    # A blocked bend is only evidence for the *wall-obstacle* lesson when
    # making walls passable changes the observable answer. Other colored
    # terminals can also block one bend, so do not over-claim those cases.
    return structural and _solve(grid, allow_walls=True) != _solve(grid)


def _witness_multi_terminal_tree(grid) -> bool:
    if self_check(grid):
        return False
    bg = _mode(grid)
    return any(
        color not in (bg, 8) and len(_cells_of(grid, color)) >= 3
        for color in {value for row in grid for value in row}
    )


def _witness_existing_tree_source(grid) -> bool:
    if self_check(grid):
        return False
    structural = any(
        event["source_index"] > 0 and event["new_cells"] > 0
        for event in _trace(grid)
    )
    # Merely selecting an older tree node is not a teaching witness if a
    # newest-only chain paints the same final union. Require an observable
    # counterexample to that shortcut.
    return structural and _solve(grid, newest_source_only=True) != _solve(grid)


def _witness_singleton_distractor(grid) -> bool:
    if self_check(grid):
        return False
    bg = _mode(grid)
    return any(
        color not in (bg, 8) and len(_cells_of(grid, color)) == 1
        for color in {value for row in grid for value in row}
    )


def _witness_vertical_walls(grid) -> bool:
    if self_check(grid):
        return False
    orientations = _wall_orientations(grid)
    return bool(orientations) and all(orientation in {"v", "point"} for orientation in orientations) and "v" in orientations


# ---------------------------------------------------------------------------
# Explicit wrong competitors used to prove the lesson is identifiable.
# ---------------------------------------------------------------------------

def _rival_straight_only(grid):
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    bg = _mode(grid)
    out = [list(row) for row in grid]
    for color in sorted({v for row in grid for v in row if v not in (bg, 8)}):
        points = _cells_of(grid, color)
        for i, a in enumerate(points):
            for b in points[i + 1:]:
                if a[0] != b[0] and a[1] != b[1]:
                    continue
                path_h, _path_v = _candidate_paths(a, b)
                if _path_valid(grid, path_h, bg=bg, color=color):
                    for r, c in path_h:
                        out[r][c] = color
    return out


def _rival_always_h_first(grid):
    return _solve(grid, bend_policy="always_h")


def _rival_always_v_first(grid):
    return _solve(grid, bend_policy="always_v")


def _rival_ignore_walls(grid):
    return _solve(grid, allow_walls=True)


def _rival_first_two_only(grid):
    return _solve(grid, first_two_only=True)


def _rival_newest_chain(grid):
    return _solve(grid, newest_source_only=True)


def _rival_route_singletons(grid):
    out = _solve(grid)
    bg = _mode(grid)
    for color in sorted({v for row in grid for v in row if v not in (bg, 8)}):
        points = _cells_of(grid, color)
        if len(points) != 1:
            continue
        r, c = points[0]
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]) and grid[rr][cc] == bg:
                out[rr][cc] = color
                break
    return out


def _rival_horizontal_walls_only(grid):
    if "v" in _wall_orientations(grid):
        return [list(row) for row in grid]
    return _solve(grid)


SEMANTIC_RIVALS = {
    "straight_segments_only": _rival_straight_only,
    "always_horizontal_first": _rival_always_h_first,
    "always_vertical_first": _rival_always_v_first,
    "walls_are_passable": _rival_ignore_walls,
    "only_first_terminal_pair": _rival_first_two_only,
    "attach_only_to_newest_terminal": _rival_newest_chain,
    "route_singleton_colors": _rival_route_singletons,
    "horizontal_walls_only": _rival_horizontal_walls_only,
}

SEMANTIC_WITNESSES = {
    "horizontal_bend_preference": _witness_h_preference,
    "vertical_bend_preference": _witness_v_preference,
    "one_bend_blocked_forces_detour": _witness_forced_detour,
    "multi_terminal_tree": _witness_multi_terminal_tree,
    "older_tree_node_can_be_best_source": _witness_existing_tree_source,
    "singleton_color_is_distractor": _witness_singleton_distractor,
    "vertical_wall_generalization": _witness_vertical_walls,
}

WITNESS_RIVALS = {
    "horizontal_bend_preference": ["always_vertical_first"],
    "vertical_bend_preference": ["always_horizontal_first"],
    "one_bend_blocked_forces_detour": ["walls_are_passable"],
    "multi_terminal_tree": ["only_first_terminal_pair"],
    "older_tree_node_can_be_best_source": ["attach_only_to_newest_terminal"],
    "singleton_color_is_distractor": ["route_singleton_colors"],
    "vertical_wall_generalization": ["horizontal_walls_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "straight_segments_only": _rival_straight_only,
    "always_horizontal_first": _rival_always_h_first,
    "only_first_terminal_pair": _rival_first_two_only,
    "attach_only_to_newest_terminal": _rival_newest_chain,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    valid_demos: list[dict[str, object]] = []
    control_seen = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input violates teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output differs from the selected rule")
        if _profile_of(demo["input"]) == CONTROL_PROFILE:
            control_seen = True
        valid_demos.append(demo)

    if not control_seen:
        reasons.append("demonstrations omit the branch-rich vertical-wall control")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input violates teaching grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in valid_demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} matches every demonstration but answers the query differently"
            )
    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    # Seed and difficulty intentionally do not move the semantic schedule: the
    # sliding-window guarantee is over sample_index and therefore survives every
    # materializer seed/band choice. Layout nuisance randomness still uses seed.
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)]


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------

def _adjacent(cell: tuple[int, int]) -> set[tuple[int, int]]:
    r, c = cell
    return {(r + dr, c + dc) for dr, dc in _CARDINAL}


def _line_cells(r: int, c: int, length: int, orientation: str) -> tuple[tuple[int, int], ...]:
    if orientation == "h":
        return tuple((r, c + offset) for offset in range(length))
    return tuple((r + offset, c) for offset in range(length))


def _place_component(
    grid,
    rng,
    *,
    color: int,
    length: int,
    occupied: set[tuple[int, int]],
    same_color: set[tuple[int, int]],
    orientation: str | None = None,
    max_tries: int = 300,
) -> tuple[tuple[int, int], ...] | None:
    height, width = len(grid), len(grid[0])
    orientations = [orientation] if orientation else ["h", "v"]
    for _ in range(max_tries):
        orient = rng.choice(orientations)
        max_r = height - (length if orient == "v" else 1)
        max_c = width - (length if orient == "h" else 1)
        if max_r < 0 or max_c < 0:
            return None
        r = rng.randint(0, max_r)
        c = rng.randint(0, max_c)
        cells = _line_cells(r, c, length, orient)
        if any(cell in occupied for cell in cells):
            continue
        # Keep separately-declared components separate under 4-connectivity.
        if any(neighbor in same_color for cell in cells for neighbor in _adjacent(cell) if neighbor not in cells):
            continue
        for rr, cc in cells:
            grid[rr][cc] = color
        occupied.update(cells)
        same_color.update(cells)
        return cells
    return None


def _permuted_active_labels(rng, count: int) -> tuple[int, ...]:
    labels = list(_CANONICAL_ACTIVE_LABELS)
    rng.shuffle(labels)
    return tuple(labels[:count])


def _construct_anchor(profile: str, rng):
    spec = _CANONICAL_PROFILE_SPECS[profile]
    height, width = spec["dims"]
    active_parts = list(spec["active_parts"])
    wall_parts = list(spec["wall_parts"])

    for _attempt in range(500):
        grid = full_grid(height, width, 1)
        occupied: set[tuple[int, int]] = set()
        wall_cells: set[tuple[int, int]] = set()
        ok = True
        for length in wall_parts:
            placed = _place_component(
                grid,
                rng,
                color=8,
                length=int(length),
                occupied=occupied,
                same_color=wall_cells,
                orientation="h",
            )
            if placed is None:
                ok = False
                break
        if not ok:
            continue

        labels = _permuted_active_labels(rng, len(active_parts))
        # Shuffle which semantic color receives which canonical morphology while
        # preserving the complete color-quotiented profile.
        parts_order = list(active_parts)
        rng.shuffle(parts_order)
        for color, parts in zip(labels, parts_order):
            same_color: set[tuple[int, int]] = set()
            for length in parts:
                placed = _place_component(
                    grid,
                    rng,
                    color=color,
                    length=int(length),
                    occupied=occupied,
                    same_color=same_color,
                )
                if placed is None:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        if not self_check(grid) and _canonical_profile_from_morphology(grid) == profile:
            return grid
    raise RuntimeError(f"could not construct canonical anchor profile {profile}")


def _control_base() -> list[list[int]]:
    """Hand-built counterexample covering every material routing branch.

    The morphology deliberately matches the public 12x12/full-palette profile
    (two length-8 wall components and the same active-component partition), but
    rotates the walls vertical and arranges terminals so the output cannot be
    explained by straight-line completion, a fixed bend order, newest-only
    attachment, or treating walls as passable.
    """
    grid = full_grid(12, 12, 1)

    # Two disjoint vertical length-8 walls.
    for row in range(2, 10):
        grid[row][4] = 8
    for row in range(1, 9):
        grid[row][8] = 8

    terminals = {
        # A->B must go V-first because the H bend crosses the left wall; the
        # later terminal also exercises tree growth.
        2: ((3, 1), (10, 6), (6, 6)),
        # First pair establishes vertical connectivity; the third terminal has
        # both bends open and therefore exercises vertical bend preference.
        6: ((1, 10), (4, 10), (7, 9)),
        # The third terminal is closer to the older tree node than the newest
        # node, proving attachment searches the whole accumulated tree.
        9: ((0, 7), (1, 1), (3, 6)),
        # Initial unaligned pair with both bends open exercises H preference.
        4: ((9, 9), (11, 11)),
        # Singleton colors are distractors and must remain unchanged.
        3: ((0, 0),),
        5: ((0, 11),),
        7: ((11, 0),),
    }
    for color, cells in terminals.items():
        for row, col in cells:
            if grid[row][col] != 1:
                raise AssertionError(f"control scaffold overlap at {(row, col)}")
            grid[row][col] = color
    return grid


def _flip_rows(grid):
    return [list(row) for row in reversed(grid)]


def _flip_cols(grid):
    return [list(reversed(row)) for row in grid]


def _recolor_active(grid, rng):
    bg = _mode(grid)
    old = sorted({value for row in grid for value in row if value not in (bg, 8)})
    new = list(old)
    rng.shuffle(new)
    mapping = dict(zip(old, new))
    return [
        [mapping.get(value, value) for value in row]
        for row in grid
    ]


def _control_is_strong(grid) -> bool:
    if self_check(grid):
        return False
    if _profile_of(grid) != CONTROL_PROFILE:
        return False
    if not all(witness(grid) for witness in SEMANTIC_WITNESSES.values()):
        return False
    expected = rule_mirror(grid)
    return all(rival(grid) != expected for rival in LESSON_COMPETITORS.values())


def _construct_control(rng):
    base = _control_base()
    # Only use symmetries that preserve the vertical-wall role; select among
    # those that still satisfy every declared branch/rival discriminator.
    variants = [base, _flip_rows(base), _flip_cols(base), _flip_rows(_flip_cols(base))]
    strong = [variant for variant in variants if _control_is_strong(variant)]
    if not strong:
        raise RuntimeError("internal control scaffold no longer satisfies semantic witnesses")
    grid = [row[:] for row in rng.choice(strong)]
    # Color permutation is a true nuisance factor: 8 and modal background 1 are
    # fixed, while all ordinary color identities are interchangeable.
    recolored = _recolor_active(grid, rng)
    if not _control_is_strong(recolored):
        raise AssertionError("active-color permutation changed control semantics")
    return recolored


def _construct_random_network(rng):
    height, width = 12, 12
    # Distinct linked morphology from the public 12x12/full profile makes the
    # categorical override observable without a hidden marker.
    wall_parts = (4, 3, 2)
    active_parts = ((2, 1, 1), (1, 1, 1, 1), (2, 1), (1, 1, 1), (1, 1), (1, 1), (1,))
    for _attempt in range(800):
        grid = full_grid(height, width, 1)
        occupied: set[tuple[int, int]] = set()
        wall_cells: set[tuple[int, int]] = set()
        ok = True
        for index, length in enumerate(wall_parts):
            orientation = "v" if index == 0 and rng.random() < 0.5 else None
            placed = _place_component(
                grid,
                rng,
                color=8,
                length=length,
                occupied=occupied,
                same_color=wall_cells,
                orientation=orientation,
            )
            if placed is None:
                ok = False
                break
        if not ok:
            continue
        labels = _permuted_active_labels(rng, len(active_parts))
        parts_order = list(active_parts)
        rng.shuffle(parts_order)
        for color, parts in zip(labels, parts_order):
            same_color: set[tuple[int, int]] = set()
            for length in parts:
                placed = _place_component(
                    grid,
                    rng,
                    color=color,
                    length=length,
                    occupied=occupied,
                    same_color=same_color,
                )
                if placed is None:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        if not self_check(grid) and _profile_of(grid) == RANDOM_PROFILE:
            return grid
    raise RuntimeError("could not construct generalized random network")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))

    rng = ctx.draw_rng(f"layout:{profile}:band={difficulty or 'default'}")
    if profile in _CANONICAL_PROFILE_SPECS:
        grid = _construct_anchor(profile, rng)
    elif profile == CONTROL_PROFILE:
        grid = _construct_control(rng)
    elif profile == RANDOM_PROFILE:
        grid = _construct_random_network(rng)
    else:  # draw_choice makes this unreachable; keep the failure explicit.
        raise AssertionError(f"unknown selected profile {profile!r}")

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"internal invalid scene for {profile}: {errors}")
    observed = _profile_of(grid)
    if observed != profile:
        raise AssertionError(f"scene profile observation mismatch: requested {profile!r}, observed {observed!r}")
    return grid
