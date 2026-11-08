"""Reviewed generator for arc_puzzle_bank_twelfth21:E83.

Canonical rule
--------------
For every horizontal or vertical one-cell pattern ``x 0 x`` whose two
non-background endpoints have the same color ``x``, paint the middle cell
``x``.  All matching gaps are repaired from the original input grid.

The four-sample curriculum alternates canonical-style positive-only scenes
with compact negative-control scenes.  Every three consecutive samples expose
both orientations, multiple colors, and at least one control bundle containing
an unequal one-cell sandwich, an equal-color diagonal sandwich, and an equal-
color two-cell gap.  Those controls rule out common over-generalizations while
remaining unchanged under the canonical transformation.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7cf07bea34b"
TASK_ID = "d7cf07bea34b"
VERSION = "3.0.0"
RULE_HASH = "4f5cf8e5d0d6"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.05

SUMMARY = (
    "A sparse zero-background grid contains 2..4 same-color horizontal or "
    "vertical one-cell x 0 x gaps. Repair every such gap by painting its "
    "middle cell with the endpoint color. Some curriculum samples also "
    "contain unequal, diagonal, and two-cell-gap negative controls that must "
    "remain unchanged."
)

INVARIANTS = [
    "background is 0 and every target endpoint color is in 1..9",
    "there are exactly n_gaps unambiguous same-color orthogonal x 0 x motifs",
    "target centers and target endpoints are pairwise distinct",
    "at least two target colors are present",
    "negative-control scenes contain unequal, diagonal, and two-cell-gap controls",
    "grid_h, grid_w, and n_gaps are exactly recoverable from the returned grid",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased 7..8",
        "valid": "7..8",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased 8..9",
        "valid": "8..9",
    },
    "n_gaps": {
        "type": "int",
        "default": "difficulty-biased 2..4",
        "valid": "2..4",
    },
}

_VALID_H = (7, 8)
_VALID_W = (8, 9)
_VALID_N = (2, 4)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Exact empirical profiles of the two train inputs and held-out test input.
# Palette sizes include background 0.  Position and color identities are
# nuisance variables; only dimensions, target count, and palette cardinality
# are pinned here.
_CANONICAL_PROFILES = {
    (7, 9): {"n_gaps": 3, "palette_size": 4},
    (8, 8): {"n_gaps": 3, "palette_size": 4},
    (8, 9): {"n_gaps": 4, "palette_size": 5},
}

Grid = list[list[int]]
Cell = tuple[int, int]
Motif = dict[str, Any]


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _gap_motifs(grid: Grid) -> list[Motif]:
    """Return all same-color orthogonal one-cell gaps in stable order."""
    h, w = len(grid), len(grid[0])
    motifs: list[Motif] = []
    for r in range(h):
        for c in range(1, w - 1):
            color = grid[r][c - 1]
            if color != 0 and grid[r][c] == 0 and grid[r][c + 1] == color:
                motifs.append(
                    {
                        "axis": "horizontal",
                        "center": (r, c),
                        "endpoints": ((r, c - 1), (r, c + 1)),
                        "color": color,
                    }
                )
    for r in range(1, h - 1):
        for c in range(w):
            color = grid[r - 1][c]
            if color != 0 and grid[r][c] == 0 and grid[r + 1][c] == color:
                motifs.append(
                    {
                        "axis": "vertical",
                        "center": (r, c),
                        "endpoints": ((r - 1, c), (r + 1, c)),
                        "color": color,
                    }
                )
    return motifs


def _motif_key(motif: Motif) -> tuple[Any, ...]:
    return (
        motif["axis"],
        motif["center"],
        motif["endpoints"],
        motif["color"],
    )


def _unequal_controls(grid: Grid) -> list[tuple[Cell, Cell, Cell]]:
    """Orthogonal a 0 b triples with nonzero a != b."""
    h, w = len(grid), len(grid[0])
    out: list[tuple[Cell, Cell, Cell]] = []
    for r in range(h):
        for c in range(1, w - 1):
            left, right = grid[r][c - 1], grid[r][c + 1]
            if grid[r][c] == 0 and left != 0 and right != 0 and left != right:
                out.append(((r, c - 1), (r, c), (r, c + 1)))
    for r in range(1, h - 1):
        for c in range(w):
            top, bottom = grid[r - 1][c], grid[r + 1][c]
            if grid[r][c] == 0 and top != 0 and bottom != 0 and top != bottom:
                out.append(((r - 1, c), (r, c), (r + 1, c)))
    return out


def _diagonal_controls(grid: Grid) -> list[tuple[Cell, Cell, Cell]]:
    """Equal nonzero endpoints diagonally opposite around a zero center."""
    h, w = len(grid), len(grid[0])
    out: list[tuple[Cell, Cell, Cell]] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            for a, b in (
                ((r - 1, c - 1), (r + 1, c + 1)),
                ((r - 1, c + 1), (r + 1, c - 1)),
            ):
                color = grid[a[0]][a[1]]
                if color != 0 and grid[b[0]][b[1]] == color:
                    out.append((a, (r, c), b))
    return out


def _long_gap_controls(grid: Grid) -> list[tuple[Cell, Cell, Cell, Cell]]:
    """Equal-color x 0 0 x horizontal or vertical controls."""
    h, w = len(grid), len(grid[0])
    out: list[tuple[Cell, Cell, Cell, Cell]] = []
    for r in range(h):
        for c in range(w - 3):
            color = grid[r][c]
            if (
                color != 0
                and grid[r][c + 1] == 0
                and grid[r][c + 2] == 0
                and grid[r][c + 3] == color
            ):
                out.append(((r, c), (r, c + 1), (r, c + 2), (r, c + 3)))
    for r in range(h - 3):
        for c in range(w):
            color = grid[r][c]
            if (
                color != 0
                and grid[r + 1][c] == 0
                and grid[r + 2][c] == 0
                and grid[r + 3][c] == color
            ):
                out.append(((r, c), (r + 1, c), (r + 2, c), (r + 3, c)))
    return out


def _analysis(grid: Grid) -> dict[str, Any]:
    motifs = _gap_motifs(grid)
    unequal = _unequal_controls(grid)
    diagonal = _diagonal_controls(grid)
    long_gap = _long_gap_controls(grid)

    motif_endpoints = {
        cell for motif in motifs for cell in motif["endpoints"]
    }
    motif_centers = {motif["center"] for motif in motifs}
    control_endpoints: set[Cell] = set()
    for triple in unequal:
        control_endpoints.update((triple[0], triple[2]))
    for triple in diagonal:
        control_endpoints.update((triple[0], triple[2]))
    for quartet in long_gap:
        control_endpoints.update((quartet[0], quartet[3]))
    nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    decisive_unequal = [item for item in unequal if item[1] not in motif_centers]
    decisive_diagonal = [item for item in diagonal if item[1] not in motif_centers]
    decisive_long_gap = [
        item for item in long_gap
        if item[1] not in motif_centers or item[2] not in motif_centers
    ]
    return {
        "motifs": motifs,
        "motif_endpoints": motif_endpoints,
        "motif_centers": motif_centers,
        "unequal": unequal,
        "diagonal": diagonal,
        "long_gap": long_gap,
        "decisive_unequal": decisive_unequal,
        "decisive_diagonal": decisive_diagonal,
        "decisive_long_gap": decisive_long_gap,
        "control_endpoints": control_endpoints,
        "nonzero": nonzero,
        "uncovered": nonzero - motif_endpoints - control_endpoints,
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python semantic mirror; Racket remains the output authority."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    # Match the canonical Racket source: both predicates read the original grid.
    for r in range(h):
        for c in range(1, w - 1):
            color = grid[r][c - 1]
            if color != 0 and grid[r][c] == 0 and grid[r][c + 1] == color:
                out[r][c] = color
    for r in range(1, h - 1):
        for c in range(w):
            color = grid[r - 1][c]
            if color != 0 and grid[r][c] == 0 and grid[r + 1][c] == color:
                out[r][c] = color
    return out


def _transform_control_coords(coords: dict[str, Cell], transform: int) -> dict[str, Cell]:
    """Apply one of eight dihedral transforms to a 5x5 coordinate bundle."""
    def tx(cell: Cell) -> Cell:
        r, c = cell
        if transform == 0:
            return r, c
        if transform == 1:
            return c, 4 - r
        if transform == 2:
            return 4 - r, 4 - c
        if transform == 3:
            return 4 - c, r
        if transform == 4:
            return r, 4 - c
        if transform == 5:
            return 4 - r, c
        if transform == 6:
            return c, r
        return 4 - c, 4 - r

    return {name: tx(cell) for name, cell in coords.items()}


def _place_control_bundle(grid: Grid, rng) -> None:
    """Place compact unequal, diagonal, and length-two negative controls."""
    h, w = len(grid), len(grid[0])
    coords = _transform_control_coords(
        {
            "unequal_a": (0, 0),
            "unequal_b": (0, 2),
            "diagonal_a": (1, 1),
            "diagonal_b": (3, 3),
            "long_a": (4, 0),
            "long_b": (4, 3),
        },
        rng.randrange(8),
    )
    top = rng.randint(0, h - 5)
    left = rng.randint(0, w - 5)
    colors = rng.sample(range(1, 10), 4)
    values = {
        "unequal_a": colors[0],
        "unequal_b": colors[1],
        "diagonal_a": colors[2],
        "diagonal_b": colors[2],
        "long_a": colors[3],
        "long_b": colors[3],
    }
    for name, (r, c) in coords.items():
        grid[top + r][left + c] = values[name]


def _orientation_schedule(slot: int, n_gaps: int) -> list[str]:
    if slot == 1:
        return ["horizontal"] * n_gaps
    if slot == 2:
        return ["vertical"] * n_gaps
    # Mixed slots always contain both orientations, including n_gaps == 2.
    return ["horizontal" if i % 2 == 0 else "vertical" for i in range(n_gaps)]


def _candidate_centers(h: int, w: int, axis: str) -> list[Cell]:
    if axis == "horizontal":
        return [(r, c) for r in range(h) for c in range(1, w - 1)]
    return [(r, c) for r in range(1, h - 1) for c in range(w)]


def _endpoint_cells(center: Cell, axis: str) -> tuple[Cell, Cell]:
    r, c = center
    if axis == "horizontal":
        return (r, c - 1), (r, c + 1)
    return (r - 1, c), (r + 1, c)


def _build_scene(
    h: int,
    w: int,
    n_gaps: int,
    slot: int,
    rng,
) -> Grid:
    include_controls = slot in (1, 2)
    orientations = _orientation_schedule(slot, n_gaps)

    # Restart the whole layout rather than accepting an accidental motif or a
    # damaged control.  Bounds are tiny (<= 8x9, <= 4 motifs), so this remains
    # fast and deterministic.
    for _restart in range(700):
        grid = full_grid(h, w, 0)
        if include_controls:
            _place_control_bundle(grid, rng)
            initial = _analysis(grid)
            if initial["motifs"]:
                continue
            if not (
                initial["decisive_unequal"]
                and initial["decisive_diagonal"]
                and initial["decisive_long_gap"]
            ):
                continue

        colors = rng.sample(range(1, 10), n_gaps)
        placed_keys: set[tuple[Any, ...]] = set()
        ok = True
        for axis, color in zip(orientations, colors):
            centers = _candidate_centers(h, w, axis)
            rng.shuffle(centers)
            placed = False
            before_keys = {_motif_key(m) for m in _gap_motifs(grid)}
            for center in centers:
                endpoints = _endpoint_cells(center, axis)
                if grid[center[0]][center[1]] != 0:
                    continue
                if any(grid[r][c] != 0 for r, c in endpoints):
                    continue
                candidate = [row[:] for row in grid]
                for r, c in endpoints:
                    candidate[r][c] = color
                after = _gap_motifs(candidate)
                after_keys = {_motif_key(m) for m in after}
                expected = (
                    axis,
                    center,
                    endpoints,
                    color,
                )
                if expected not in after_keys:
                    continue
                # Preserve every prior target and create exactly one new one.
                if not before_keys <= after_keys or len(after_keys) != len(before_keys) + 1:
                    continue
                endpoint_list = [cell for motif in after for cell in motif["endpoints"]]
                center_list = [motif["center"] for motif in after]
                if len(endpoint_list) != len(set(endpoint_list)):
                    continue
                if len(center_list) != len(set(center_list)):
                    continue
                grid = candidate
                placed_keys.add(expected)
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok or len(placed_keys) != n_gaps:
            continue

        observed = _analysis(grid)
        if len(observed["motifs"]) != n_gaps:
            continue
        has_controls = bool(observed["nonzero"] - observed["motif_endpoints"])
        if has_controls != include_controls:
            continue
        if include_controls and not (
            observed["decisive_unequal"]
            and observed["decisive_diagonal"]
            and observed["decisive_long_gap"]
        ):
            continue
        if not self_check(grid):
            return grid

    raise ValueError(
        f"could not place {n_gaps} reviewed motifs on {h}x{w} for curriculum slot {slot}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    slot = (sample_index + band_offset) % 4

    # Ordinary anchor slots are pinned to one of the three empirical profiles.
    # Explicit overrides always retain the full declared boundary contract.
    if not overrides and slot in (0, 3):
        profiles = tuple(_CANONICAL_PROFILES.items())
        pick = ctx.draw_rng("canonical_profile").randrange(len(profiles))
        (profile_h, profile_w), profile = profiles[pick]
        h = ctx.draw_int("grid_h", profile_h, profile_h)
        w = ctx.draw_int("grid_w", profile_w, profile_w)
        n_gaps = ctx.draw_int("n_gaps", profile["n_gaps"], profile["n_gaps"])
    else:
        h = ctx.draw_int_diff("grid_h", *_VALID_H)
        w = ctx.draw_int_diff("grid_w", *_VALID_W)
        n_gaps = ctx.draw_int_diff("n_gaps", *_VALID_N)
    rng = ctx.draw_rng("scene")
    return _build_scene(h, w, n_gaps, slot, rng)


def observe_overrides(grid: Grid) -> dict[str, int]:
    """Recover every declared exact axis directly from the returned grid."""
    if _grid_shape_errors(grid):
        return {"grid_h": 0, "grid_w": 0, "n_gaps": 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_gaps": len(_gap_motifs(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Mutation-sensitive structural checker for the teaching distribution."""
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")

    info = _analysis(grid)
    motifs = info["motifs"]
    if not (_VALID_N[0] <= len(motifs) <= _VALID_N[1]):
        errors.append(f"expected 2..4 target gaps, got {len(motifs)}")
        return errors

    centers = [motif["center"] for motif in motifs]
    endpoints = [cell for motif in motifs for cell in motif["endpoints"]]
    if len(centers) != len(set(centers)):
        errors.append("a target center participates in multiple gap motifs")
    if len(endpoints) != len(set(endpoints)):
        errors.append("a target endpoint participates in multiple gap motifs")
    if set(centers) & set(endpoints):
        errors.append("a target center is reused as another target endpoint")

    target_colors = {motif["color"] for motif in motifs}
    if len(target_colors) < 2:
        errors.append("at least two target colors are required")

    if info["uncovered"]:
        errors.append(
            "nonzero cells are neither target endpoints nor recognized control endpoints"
        )

    distractors = info["nonzero"] - info["motif_endpoints"]
    if distractors:
        if not info["decisive_unequal"]:
            errors.append("control scene lacks a rule-inert unequal one-cell sandwich")
        if not info["decisive_diagonal"]:
            errors.append("control scene lacks a rule-inert equal-color diagonal sandwich")
        if not info["decisive_long_gap"]:
            errors.append("control scene lacks a rule-inert equal-color two-cell gap")

    if rule_mirror(grid) == grid:
        errors.append("scene is a no-op under the canonical repair rule")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the three linked empirical input profiles exactly."""
    errors = self_check(grid)
    if errors:
        return errors
    info = _analysis(grid)
    if info["nonzero"] != info["motif_endpoints"]:
        return ["strict canonical profiles contain target endpoints only"]
    h, w = len(grid), len(grid[0])
    profile = _CANONICAL_PROFILES.get((h, w))
    if profile is None:
        return [f"dimensions {h}x{w} are not a canonical profile"]
    if len(info["motifs"]) != profile["n_gaps"]:
        return [
            f"canonical {h}x{w} profile needs {profile['n_gaps']} gaps, "
            f"got {len(info['motifs'])}"
        ]
    palette_size = len({value for row in grid for value in row})
    if palette_size != profile["palette_size"]:
        return [
            f"canonical {h}x{w} profile needs palette size "
            f"{profile['palette_size']}, got {palette_size}"
        ]
    return []


def _horizontal_only(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(1, w - 1):
            color = grid[r][c - 1]
            if color != 0 and grid[r][c] == 0 and grid[r][c + 1] == color:
                out[r][c] = color
    return out


def _vertical_only(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(w):
            color = grid[r - 1][c]
            if color != 0 and grid[r][c] == 0 and grid[r + 1][c] == color:
                out[r][c] = color
    return out


def _first_gap_only(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    motifs = _gap_motifs(grid)
    if motifs:
        r, c = motifs[0]["center"]
        out[r][c] = motifs[0]["color"]
    return out


def _one_color_only(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    motifs = _gap_motifs(grid)
    if not motifs:
        return out
    chosen = min(motif["color"] for motif in motifs)
    for motif in motifs:
        if motif["color"] == chosen:
            r, c = motif["center"]
            out[r][c] = chosen
    return out


def _fill_unequal_too(grid: Grid) -> Grid:
    out = rule_mirror(grid)
    for left, center, _right in _unequal_controls(grid):
        out[center[0]][center[1]] = grid[left[0]][left[1]]
    return out


def _fill_diagonal_too(grid: Grid) -> Grid:
    out = rule_mirror(grid)
    for left, center, _right in _diagonal_controls(grid):
        out[center[0]][center[1]] = grid[left[0]][left[1]]
    return out


def _fill_long_gaps_too(grid: Grid) -> Grid:
    out = rule_mirror(grid)
    for left, middle_a, middle_b, _right in _long_gap_controls(grid):
        color = grid[left[0]][left[1]]
        out[middle_a[0]][middle_a[1]] = color
        out[middle_b[0]][middle_b[1]] = color
    return out


LESSON_COMPETITORS: dict[str, Callable[[Grid], Grid]] = {
    "leave every gap unchanged": lambda grid: [row[:] for row in grid],
    "repair horizontal gaps only": _horizontal_only,
    "repair vertical gaps only": _vertical_only,
    "repair only the first gap": _first_gap_only,
    "repair only one endpoint color": _one_color_only,
    "also fill unequal one-cell sandwiches": _fill_unequal_too,
    "also fill equal-color diagonal sandwiches": _fill_diagonal_too,
    "also fill equal-color two-cell gaps": _fill_long_gaps_too,
}

# The semantic gate verifies each witness claim against the Racket oracle.
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)

WITNESS_RIVALS = {
    "horizontal_target": ["repair vertical gaps only"],
    "vertical_target": ["repair horizontal gaps only"],
    "multiple_target_colors": ["repair only one endpoint color"],
    "unequal_one_cell_control": ["also fill unequal one-cell sandwiches"],
    "diagonal_equal_control": ["also fill equal-color diagonal sandwiches"],
    "two_cell_equal_gap_control": ["also fill equal-color two-cell gaps"],
    "strict_canonical_anchor": ["repair only the first gap"],
}

SCHEDULE_PROFILES = (
    "anchor_mixed_a",
    "controls_horizontal",
    "controls_vertical",
    "anchor_mixed_b",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the curriculum residue used by generation and lesson audits."""
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return SCHEDULE_PROFILES[(sample_index + band_offset) % 4]


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named shortcut fits every demo but changes query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        input_grid = demo.get("input")
        output_grid = demo.get("output")
        structural = self_check(input_grid)
        if structural:
            reasons.append(f"demo {index} fails self_check: {structural[0]}")
            continue
        if rule_mirror(input_grid) != output_grid:
            reasons.append(f"demo {index} output does not match the canonical repair rule")
    query_input = query.get("input")
    query_output = query.get("output")
    if self_check(query_input):
        reasons.append("query input fails self_check")
    elif rule_mirror(query_input) != query_output:
        reasons.append("query output does not match the canonical repair rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"]
            for demo in demos
        )
        if survives and competitor(query_input) != query_output:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def _has_horizontal(grid: Grid) -> bool:
    return any(motif["axis"] == "horizontal" for motif in _gap_motifs(grid))


def _has_vertical(grid: Grid) -> bool:
    return any(motif["axis"] == "vertical" for motif in _gap_motifs(grid))


def _has_multiple_target_colors(grid: Grid) -> bool:
    return len({motif["color"] for motif in _gap_motifs(grid)}) >= 2


def _has_unequal_control(grid: Grid) -> bool:
    return bool(_analysis(grid)["decisive_unequal"])


def _has_diagonal_control(grid: Grid) -> bool:
    return bool(_analysis(grid)["decisive_diagonal"])


def _has_long_gap_control(grid: Grid) -> bool:
    return bool(_analysis(grid)["decisive_long_gap"])


def _is_strict_anchor(grid: Grid) -> bool:
    return not strict_canonical_like(grid)


SEMANTIC_WITNESSES = {
    "horizontal_target": _has_horizontal,
    "vertical_target": _has_vertical,
    "multiple_target_colors": _has_multiple_target_colors,
    "unequal_one_cell_control": _has_unequal_control,
    "diagonal_equal_control": _has_diagonal_control,
    "two_cell_equal_gap_control": _has_long_gap_control,
    "strict_canonical_anchor": _is_strict_anchor,
}
