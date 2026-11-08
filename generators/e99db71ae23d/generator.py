"""Semantic generator for ARC task e99db71ae23d.

Every 4-connected color-5 or color-2 component is a 2x2 L-tromino.  The
missing bbox corner defines the opening.  Gray (5) projects a yellow (4) copy
one diagonal step toward that opening; red (2) projects a green (3) copy one
diagonal step away.  Projection is clipped at the grid edge and the canonical
pass order makes green overwrite yellow when projected copies collide.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "e99db71ae23d"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "32f38f665cc3"
SUMMARY = (
    "Project each gray L-tromino one diagonal step toward its missing corner "
    "in yellow, and each red L-tromino one step away in green; clip at edges "
    "and let green overwrite yellow on projection collisions."
)
INVARIANTS = [
    "the background is 7 and every active component is a 2x2 L-tromino in color 5 or 2",
    "gray (5) projects the same three-cell L one diagonal step toward its missing bbox corner in yellow (4)",
    "red (2) projects the same three-cell L one diagonal step away from its missing bbox corner in green (3)",
    "off-grid projected cells are clipped and the red/green pass overwrites gray/yellow at cross-color collisions",
    "projected copies never overwrite a source tromino in the teaching distribution",
]

PUBLIC_PROFILES = (
    "public_sparse_3",
    "public_balanced_4",
    "public_dense_16",
)
GENERAL_PROFILES = (
    "general_sparse_4",
    "general_orientation_8",
    "general_edge_6",
    "general_edge_overlap_6",
    "general_overlap_8",
    "general_dense_14",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
# Four-pair lesson blocks use these three demonstrations before a free query.
# Together they expose all four orientations, edge clipping, cross-color
# collision, and green-over-yellow precedence.
_LESSON_DEMO_PROFILES = (
    "general_orientation_8",
    "general_edge_overlap_6",
    "general_overlap_8",
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted exact-public and generalized branch profiles",
        "valid": "|".join(SCENE_PROFILES),
    }
}

# Index is the missing corner: top-left, top-right, bottom-left, bottom-right.
_L_SHAPES = (
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
)
_SHAPE_INDEX = {tuple(sorted(shape)): index for index, shape in enumerate(_L_SHAPES)}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

_PUBLIC_ROWS = {
    "public_sparse_3": (
        "77777777",
        "77772777",
        "75772277",
        "75577777",
        "77777777",
        "77777777",
        "77777277",
        "77772277",
    ),
    "public_balanced_4": (
        "77777777",
        "75777557",
        "75577757",
        "77777777",
        "77777777",
        "72277277",
        "77277227",
        "77777777",
    ),
    "public_dense_16": (
        "7777777777777777",
        "7577777777777777",
        "7557777727755777",
        "7777755722775777",
        "7777775777777777",
        "7777777777772277",
        "7775775577777277",
        "7775577577777777",
        "7777777777722777",
        "7777722772772777",
        "7757772772277777",
        "7755777777777227",
        "7777777775777727",
        "7727722775577777",
        "7722772777772777",
        "7777777777772277",
    ),
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in rows]
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}

_GENERAL_SPECS = {
    "general_sparse_4": {
        "shape": (9, 11), "pieces": 4, "clip": False, "overlap": False,
        "all_color_orientations": False,
    },
    "general_orientation_8": {
        "shape": (12, 12), "pieces": 8, "clip": False, "overlap": False,
        "all_color_orientations": True,
    },
    "general_edge_6": {
        "shape": (10, 13), "pieces": 6, "clip": True, "overlap": False,
        "all_color_orientations": False,
    },
    "general_edge_overlap_6": {
        "shape": (11, 14), "pieces": 6, "clip": True, "overlap": True,
        "all_color_orientations": False,
    },
    "general_overlap_8": {
        "shape": (13, 15), "pieces": 8, "clip": False, "overlap": True,
        "all_color_orientations": False,
    },
    "general_dense_14": {
        "shape": (15, 18), "pieces": 14, "clip": True, "overlap": True,
        "all_color_orientations": False,
    },
}
_GENERAL_KEYS = {
    (spec["shape"][0], spec["shape"][1], spec["pieces"]): profile
    for profile, spec in _GENERAL_SPECS.items()
}


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color not in (2, 5) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and (nr, nc) not in seen and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            row0 = min(r for r, _ in cells)
            col0 = min(c for _, c in cells)
            normalized = tuple(sorted((r - row0, c - col0) for r, c in cells))
            shape_index = _SHAPE_INDEX.get(normalized)
            components.append({
                "color": color,
                "cells": tuple(cells),
                "row0": row0,
                "col0": col0,
                "shape_index": shape_index,
            })
    return components


def _shift(color: int, shape_index: int) -> tuple[int, int]:
    missing_row, missing_col = ((0, 0), (0, 1), (1, 0), (1, 1))[shape_index]
    dr = -1 if missing_row == 0 else 1
    dc = -1 if missing_col == 0 else 1
    return (dr, dc) if color == 5 else (-dr, -dc)


def _piece_cells(piece: tuple[int, int, int, int]) -> tuple[tuple[int, int], ...]:
    _color, shape_index, row0, col0 = piece
    return tuple((row0 + dr, col0 + dc) for dr, dc in _L_SHAPES[shape_index])


def _piece_targets(piece: tuple[int, int, int, int]) -> tuple[tuple[int, int], ...]:
    color, shape_index, _row0, _col0 = piece
    dr, dc = _shift(color, shape_index)
    return tuple((row + dr, col + dc) for row, col in _piece_cells(piece))


def _analysis(grid: list[list[int]]) -> dict[str, Any]:
    errors = _valid_grid(grid)
    result: dict[str, Any] = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if palette != {2, 5, 7}:
        errors.append(f"expected exact palette {{2,5,7}}, got {sorted(palette)}")
    components = _components(grid)
    if not 3 <= len(components) <= 16:
        errors.append(f"expected 3..16 L-trominoes, got {len(components)}")
    malformed = [component for component in components if component["shape_index"] is None]
    if malformed:
        errors.append(f"every active component must be a 3-cell 2x2 L-tromino; malformed={len(malformed)}")

    color_counts = Counter(component["color"] for component in components)
    if set(color_counts) != {2, 5}:
        errors.append("both red (2) and gray (5) source trominoes are required")
    orientation_counts = Counter(
        component["shape_index"] for component in components
        if component["shape_index"] is not None
    )
    if len(orientation_counts) < 2:
        errors.append("at least two missing-corner orientations are required")

    source_cells = {
        cell for component in components for cell in component["cells"]
    }
    target_records: defaultdict[tuple[int, int], list[int]] = defaultdict(list)
    clipped_cells = 0
    if not malformed:
        for component in components:
            dr, dc = _shift(component["color"], component["shape_index"])
            for row, col in component["cells"]:
                target = row + dr, col + dc
                if 0 <= target[0] < height and 0 <= target[1] < width:
                    target_records[target].append(component["color"])
                else:
                    clipped_cells += 1
    source_target_hits = sorted(set(target_records) & source_cells)
    if source_target_hits:
        errors.append(
            f"projected copies must not overwrite source trominoes; hits={len(source_target_hits)}"
        )
    overlap_cells = sum(len(colors) > 1 for colors in target_records.values())
    cross_color_overlap_cells = sum(
        len(set(colors)) > 1 for colors in target_records.values()
    )

    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None:
        profile = _GENERAL_KEYS.get((height, width, len(components)))
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared public/general scene profile")
    elif profile in GENERAL_PROFILES:
        spec = _GENERAL_SPECS[profile]
        if bool(clipped_cells) != spec["clip"]:
            errors.append(
                f"{profile} clipping branch mismatch: clipped_cells={clipped_cells}"
            )
        if bool(cross_color_overlap_cells) != spec["overlap"]:
            errors.append(
                f"{profile} cross-color overlap branch mismatch: cross={cross_color_overlap_cells}"
            )
        if not spec["overlap"] and overlap_cells:
            errors.append(f"{profile} must not contain any projection overlap")
        if spec["all_color_orientations"]:
            by_color = {
                color: {
                    component["shape_index"] for component in components
                    if component["color"] == color
                }
                for color in (2, 5)
            }
            if any(indices != {0, 1, 2, 3} for indices in by_color.values()):
                errors.append("orientation profile requires all four openings for each source color")

    output = None
    changed_cells = 0
    fill_counts: Counter[int] = Counter()
    if not malformed:
        output = _apply_rule(grid, components)
        changed_cells = sum(
            before != after
            for input_row, output_row in zip(grid, output)
            for before, after in zip(input_row, output_row)
        )
        fill_counts.update(value for row in output for value in row if value in (3, 4))
        if changed_cells == 0:
            errors.append("the projection must visibly change the grid")
        if not fill_counts[3] or not fill_counts[4]:
            errors.append("both green and yellow projected evidence must remain visible")

    result.update({
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "piece_count": len(components),
        "color_counts": dict(color_counts),
        "orientation_counts": dict(orientation_counts),
        "clipped_projection_cells": clipped_cells,
        "projection_overlap_cells": overlap_cells,
        "cross_color_overlap_cells": cross_color_overlap_cells,
        "source_target_hits": source_target_hits,
        "changed_cells": changed_cells,
        "fill_counts": dict(fill_counts),
        "scene_profile": profile,
        "output": output,
    })
    return result


def _apply_rule(grid: list[list[int]], components: list[dict[str, Any]] | None = None) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    components = _components(grid) if components is None else components
    output = [list(row) for row in grid]
    for source_color, fill_color in ((5, 4), (2, 3)):
        for component in components:
            if component["color"] != source_color or component["shape_index"] is None:
                continue
            dr, dc = _shift(source_color, component["shape_index"])
            for row, col in component["cells"]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = fill_color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror used only for tests; the Racket rule remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def canonical_profile_signature(grid: list[list[int]]) -> str | None:
    return _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid))


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "scene_profile": analysis["scene_profile"],
        "grid_shape": [analysis["height"], analysis["width"]],
        "piece_count": analysis["piece_count"],
        "gray_pieces": analysis["color_counts"].get(5, 0),
        "red_pieces": analysis["color_counts"].get(2, 0),
        "orientation_support": sorted(analysis["orientation_counts"]),
        "clipped_projection_cells": analysis["clipped_projection_cells"],
        "projection_overlap_cells": analysis["projection_overlap_cells"],
        "cross_color_overlap_cells": analysis["cross_color_overlap_cells"],
        "source_target_hits": len(analysis["source_target_hits"]),
        "yellow_cells": analysis["fill_counts"].get(4, 0),
        "green_cells": analysis["fill_counts"].get(3, 0),
        "changed_cells": analysis["changed_cells"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict manifold check (SEMANTIC_GATE_CONTRACT hook 1).

    Delegates to the full v3.2.0 `_analysis` grammar, which is already the
    reviewer-strict manifold for this task: exact palette {2,5,7}, 3..16
    well-formed 2x2 L-trominoes, both source colours, >=2 openings, no
    source overwrite, membership in a declared public/general scene profile
    with its clipping/overlap branch flags, and visible yellow AND green
    evidence.  All three canonical inputs are the public profiles and pass.
    """
    return list(_analysis(grid)["errors"])


def _facts_or_none(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_gray_projection(grid) -> bool:
    """At least one gray L whose yellow copy (one diagonal step TOWARD the
    opening) is visibly painted in-bounds."""
    analysis = _facts_or_none(grid)
    if analysis is None:
        return False
    for component in analysis["components"]:
        if component["color"] != 5:
            continue
        dr, dc = _shift(5, component["shape_index"])
        if any(
            0 <= r + dr < analysis["height"] and 0 <= c + dc < analysis["width"]
            for r, c in component["cells"]
        ):
            return True
    return False


def _witness_red_projection(grid) -> bool:
    """At least one red L whose green copy (one diagonal step AWAY from the
    opening) is visibly painted in-bounds."""
    analysis = _facts_or_none(grid)
    if analysis is None:
        return False
    for component in analysis["components"]:
        if component["color"] != 2:
            continue
        dr, dc = _shift(2, component["shape_index"])
        if any(
            0 <= r + dr < analysis["height"] and 0 <= c + dc < analysis["width"]
            for r, c in component["cells"]
        ):
            return True
    return False


def _witness_green_over_yellow(grid) -> bool:
    """A projection cell claimed by BOTH a gray and a red source, so the
    green-second pass order is load-bearing."""
    analysis = _facts_or_none(grid)
    return analysis is not None and analysis["cross_color_overlap_cells"] > 0


def _witness_edge_clip(grid) -> bool:
    """At least one projected cell falls off-grid and is clipped."""
    analysis = _facts_or_none(grid)
    return analysis is not None and analysis["clipped_projection_cells"] > 0


def _witness_all_openings(grid) -> bool:
    """Each source colour shows all four missing-corner orientations."""
    analysis = _facts_or_none(grid)
    if analysis is None:
        return False
    by_color: dict[int, set[int]] = {2: set(), 5: set()}
    for component in analysis["components"]:
        by_color[component["color"]].add(component["shape_index"])
    return all(openings == {0, 1, 2, 3} for openings in by_color.values())


SEMANTIC_WITNESSES = {
    "gray_toward_opening_yellow": _witness_gray_projection,
    "red_away_from_opening_green": _witness_red_projection,
    "green_over_yellow_collision": _witness_green_over_yellow,
    "edge_clipped_projection": _witness_edge_clip,
    "all_four_openings_each_color": _witness_all_openings,
}


def _apply_variant(
    grid: list[list[int]],
    *,
    gray_toward: bool,
    red_toward: bool,
    green_last: bool,
) -> list[list[int]]:
    """Competitor engine: same tromino parse, alternative direction/pass rules."""
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    if any(component["shape_index"] is None for component in components):
        raise ValueError("malformed tromino component")
    passes = ((5, 4), (2, 3)) if green_last else ((2, 3), (5, 4))
    output = [list(row) for row in grid]
    for source_color, fill_color in passes:
        toward = gray_toward if source_color == 5 else red_toward
        for component in components:
            if component["color"] != source_color:
                continue
            dr, dc = _shift(5, component["shape_index"])  # toward the opening
            if not toward:
                dr, dc = -dr, -dc
            for row, col in component["cells"]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = fill_color
    return output


_COMPETING_RULES = {
    "swapped_directions": lambda g: _apply_variant(
        g, gray_toward=False, red_toward=True, green_last=True
    ),
    "both_toward_opening": lambda g: _apply_variant(
        g, gray_toward=True, red_toward=True, green_last=True
    ),
    "both_away_from_opening": lambda g: _apply_variant(
        g, gray_toward=False, red_toward=False, green_last=True
    ),
    "yellow_wins_collisions": lambda g: _apply_variant(
        g, gray_toward=True, red_toward=False, green_last=False
    ),
}

# Executable semantic contract. Direction/color witnesses refute a named wrong
# rule on every generated firing. Clipping and all-orientation witnesses are
# positive branch-coverage claims rather than synthetic rival claims.
SEMANTIC_RIVALS = dict(_COMPETING_RULES)
WITNESS_RIVALS = {
    "gray_toward_opening_yellow": ["both_away_from_opening"],
    "red_away_from_opening_green": ["both_toward_opening"],
    "green_over_yellow_collision": ["yellow_wins_collisions"],
}
BRANCH_WITNESSES = (
    "edge_clipped_projection",
    "all_four_openings_each_color",
)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every declared competitor is already refuted by at least one canonical pair;
# none is a canonical-fitting shortcut requiring a generated counterexample.
CANONICAL_SHORTCUTS: dict[str, Any] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Demos must pin gray-toward/red-away and the green-last pass order
    against the documented shortcuts (SEMANTIC_GATE_CONTRACT hook 3)."""
    reasons: list[str] = []
    episodes = list(demos) + [query]
    labels = [f"demo {i}" for i in range(len(demos))] + ["query"]
    for label, episode in zip(labels, episodes):
        grid = episode.get("input")
        errors = _valid_grid(grid)
        if not errors and any(
            component["shape_index"] is None for component in _components(grid)
        ):
            errors = ["active components must all be 2x2 L-trominoes"]
        if errors:
            reasons.append(f"{label}: malformed input: {'; '.join(errors)}")
    if reasons:
        return reasons
    for i, demo in enumerate(demos):
        if demo.get("output") != _apply_rule(demo["input"]):
            reasons.append(f"demo {i}: output does not match the task rule")
    if reasons:
        return reasons
    truth = _apply_rule(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query: provided output does not match the task rule")
    for name, competitor in _COMPETING_RULES.items():
        if all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        ) and competitor(query["input"]) != truth:
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a "
                "different query answer"
            )
    return reasons


def _transform_pieces(
    pieces: list[tuple[int, int, int, int]], turns: int, mirror: bool
) -> list[tuple[int, int, int, int]]:
    transformed: list[tuple[int, list[tuple[int, int]]]] = []
    all_cells: list[tuple[int, int]] = []
    for color, _shape_index, _row0, _col0 in pieces:
        cells = list(_piece_cells((color, _shape_index, _row0, _col0)))
        out = []
        for row, col in cells:
            if mirror:
                col = -col
            for _ in range(turns % 4):
                row, col = col, -row
            out.append((row, col))
        transformed.append((color, out))
        all_cells.extend(out)
    min_row = min(row for row, _ in all_cells)
    min_col = min(col for _, col in all_cells)
    result = []
    for color, cells in transformed:
        shifted = [(row - min_row, col - min_col) for row, col in cells]
        row0 = min(row for row, _ in shifted)
        col0 = min(col for _, col in shifted)
        normalized = tuple(sorted((row - row0, col - col0) for row, col in shifted))
        result.append((color, _SHAPE_INDEX[normalized], row0, col0))
    return result


def _offset_pieces(
    pieces: list[tuple[int, int, int, int]], row_offset: int, col_offset: int
) -> list[tuple[int, int, int, int]]:
    return [
        (color, shape_index, row0 + row_offset, col0 + col_offset)
        for color, shape_index, row0, col0 in pieces
    ]


def _can_add(
    piece: tuple[int, int, int, int],
    pieces: list[tuple[int, int, int, int]],
    height: int,
    width: int,
    *,
    allow_projection_overlap: bool,
    require_projection_inside: bool,
) -> bool:
    color = piece[0]
    cells = set(_piece_cells(piece))
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    existing_cells = {cell for current in pieces for cell in _piece_cells(current)}
    if cells & existing_cells:
        return False
    same_color_cells = {
        cell for current in pieces if current[0] == color for cell in _piece_cells(current)
    }
    if any(
        (row + dr, col + dc) in same_color_cells
        for row, col in cells for dr, dc in _CARDINAL
    ):
        return False
    targets = set(_piece_targets(piece))
    inside_targets = {
        (row, col) for row, col in targets if 0 <= row < height and 0 <= col < width
    }
    if require_projection_inside and len(inside_targets) != 3:
        return False
    existing_targets = {
        target
        for current in pieces
        for target in _piece_targets(current)
        if 0 <= target[0] < height and 0 <= target[1] < width
    }
    if inside_targets & (existing_cells | cells):
        return False
    if cells & existing_targets:
        return False
    if not allow_projection_overlap and inside_targets & existing_targets:
        return False
    return True


def _collision_motif(rng, height: int, width: int) -> list[tuple[int, int, int, int]]:
    # One gray/yellow and one red/green projection share exactly one cell.
    base = [(5, 1, 1, 0), (2, 1, 0, 4)]
    motif = _transform_pieces(base, rng.randrange(4), bool(rng.randrange(2)))
    cells = [cell for piece in motif for cell in _piece_cells(piece)]
    motif_h = max(row for row, _ in cells) + 1
    motif_w = max(col for _, col in cells) + 1
    row_offset = rng.randint(1, height - motif_h - 2)
    col_offset = rng.randint(1, width - motif_w - 2)
    return _offset_pieces(motif, row_offset, col_offset)


def _edge_piece(rng, height: int, width: int) -> tuple[int, int, int, int]:
    candidates = []
    for color in (2, 5):
        for shape_index in range(4):
            for row0 in range(height - 1):
                for col0 in range(width - 1):
                    piece = (color, shape_index, row0, col0)
                    targets = _piece_targets(piece)
                    clipped = sum(
                        not (0 <= row < height and 0 <= col < width)
                        for row, col in targets
                    )
                    if clipped in (1, 2):
                        candidates.append(piece)
    return rng.choice(candidates)


def _draw_general(rng, profile: str) -> list[list[int]]:
    spec = _GENERAL_SPECS[profile]
    height, width = spec["shape"]
    count = spec["pieces"]
    for _scene_attempt in range(240):
        pieces: list[tuple[int, int, int, int]] = []
        if spec["overlap"]:
            motif = _collision_motif(rng, height, width)
            if all(
                _can_add(
                    piece, pieces, height, width,
                    allow_projection_overlap=True,
                    require_projection_inside=True,
                )
                for piece in motif
            ):
                pieces.extend(motif)
            else:
                continue
        if spec["clip"]:
            edge = _edge_piece(rng, height, width)
            if not _can_add(
                edge, pieces, height, width,
                allow_projection_overlap=spec["overlap"],
                require_projection_inside=False,
            ):
                continue
            pieces.append(edge)

        remaining = count - len(pieces)
        if spec["all_color_orientations"]:
            requested = [(color, shape) for color in (5, 2) for shape in range(4)]
            used = Counter((piece[0], piece[1]) for piece in pieces)
            requested = [item for item in requested if used[item] == 0]
        else:
            colors = [5, 2] * ((remaining + 1) // 2)
            shapes = list(range(4)) * ((remaining + 3) // 4)
            rng.shuffle(colors)
            rng.shuffle(shapes)
            requested = list(zip(colors[:remaining], shapes[:remaining]))
        rng.shuffle(requested)

        success = True
        for color, preferred_shape in requested:
            placed = False
            shape_order = [preferred_shape] + [shape for shape in range(4) if shape != preferred_shape]
            if spec["all_color_orientations"]:
                shape_order = [preferred_shape]
            for _placement_attempt in range(500):
                shape_index = rng.choice(shape_order)
                row0 = rng.randrange(height - 1)
                col0 = rng.randrange(width - 1)
                piece = (color, shape_index, row0, col0)
                if _can_add(
                    piece, pieces, height, width,
                    allow_projection_overlap=spec["overlap"],
                    require_projection_inside=True,
                ):
                    pieces.append(piece)
                    placed = True
                    break
            if not placed:
                success = False
                break
        if not success or len(pieces) != count:
            continue

        grid = [[7 for _ in range(width)] for _ in range(height)]
        for piece in pieces:
            color = piece[0]
            for row, col in _piece_cells(piece):
                grid[row][col] = color
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct valid {profile} scene")


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    choices = {
        "easy": [
            "public_sparse_3", "public_balanced_4",
            "general_sparse_4", "general_sparse_4", "general_edge_6",
        ],
        "medium": [
            "public_sparse_3", "public_balanced_4", "public_dense_16",
            "general_sparse_4", "general_orientation_8", "general_orientation_8",
            "general_edge_6", "general_overlap_8", "general_overlap_8",
        ],
        "hard": [
            "general_dense_14", "general_orientation_8", "general_overlap_8",
            "public_dense_16", "public_dense_16", "general_dense_14",
        ],
    }[band]
    if requested is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        lesson_slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
        if lesson_slot < EXAMPLES_NEEDED:
            profile = ctx.draw_choice(
                "scene_profile", [_LESSON_DEMO_PROFILES[lesson_slot]]
            )
        else:
            profile = ctx.draw_choice("scene_profile", choices)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _draw_general(ctx.draw_rng("layout"), profile)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analysis(grid)["errors"])


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Focused malformed scenes used by the task-local regression test."""
    base = [row[:] for row in _PUBLIC_INPUTS["public_balanced_4"]]

    wrong_palette = [row[:] for row in base]
    wrong_palette[0][0] = 0

    broken_tromino = [row[:] for row in base]
    broken_tromino[1][1] = 7

    one_color = [[7 if value == 2 else value for value in row] for row in base]

    square_component = [row[:] for row in base]
    square_component[1][2] = 5

    unrecognized_profile = [row[:] + [7] for row in base]

    return [
        ("wrong_palette", wrong_palette),
        ("broken_tromino", broken_tromino),
        ("one_source_color", one_color),
        ("square_component", square_component),
        ("unrecognized_profile", unrecognized_profile),
    ]
