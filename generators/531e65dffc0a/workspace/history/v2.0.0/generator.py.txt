"""Generator for 531e65dffc0a — anchor-coded rotation stamps.

A single monochrome prototype and isolated anchor cells share one input grid.
Anchor colors are transform codes: 2 is identity, 3 is 90 degrees clockwise,
4 is 180 degrees, and 5 is 90 degrees counter-clockwise.  The output starts
blank and stamps the transformed prototype at each anchor's row/column origin
using the prototype color.

This review version keeps the selected Racket rule unchanged while repairing
four distribution defects in the previous sampler: inert overrides, symmetric
or clipped demonstrations, repeated/under-covered codes, and a validator that
accepted nearly empty impostors.  Ordinary three-example windows now expose
all four code branches and eliminate explicit executable rivals, including the
canonical-only shortcut that treats code 4 as identity.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "531e65dffc0a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4acd30f1e03a"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "One 3-5 cell prototype plus 2-4 isolated anchors. Anchor colors encode "
    "identity/CW90/180/CCW90; output is a fresh grid of non-clipped, "
    "non-overlapping prototype-color stamps at the anchor origins."
)

INVARIANTS = [
    "background is 0 and the grid is 10-12 cells on each side",
    "exactly one 4-connected monochrome prototype uses a non-anchor color",
    "the prototype has 3-5 cells in a compact at-most-3x3 bounding box",
    "2-4 isolated anchor cells use distinct colors from {2,3,4,5}",
    "every stamped footprint is in bounds and footprints are pairwise disjoint",
    "ordinary prototypes have four distinct rotational orientations",
    "every three consecutive ordinary samples expose all four transform codes",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile 10|11|12",
        "valid": "10..12",
        "doc": "Exact output/input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile 10|11|12",
        "valid": "10..12",
        "doc": "Exact output/input grid width.",
    },
    "n_anchors": {
        "type": "int",
        "default": "scheduled 2|3 with occasional 4",
        "valid": "2..4",
        "doc": "Exact number of distinct transform-code anchors.",
    },
    "proto_size": {
        "type": "int",
        "default": "scheduled 3|4|5",
        "valid": "3..5",
        "doc": "Exact number of cells in the prototype polyomino.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ANCHOR_CODES = (2, 3, 4, 5)
_PROTO_COLORS = (1, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

# Any three consecutive rows of either schedule cover all four codes.  The
# two-code schedule is used by canonical-profile examples with two anchors.
_CODE_SCHEDULE_2 = (
    (2, 3),
    (4, 5),
    (2, 5),
    (3, 4),
)
_CODE_SCHEDULE_3 = (
    (2, 3, 4),
    (5, 2, 3),
    (4, 5, 2),
    (3, 4, 5),
)
_CODE_SCHEDULE_4 = ((2, 3, 4, 5),)

# Profiles reproduce the canonical (height, width, palette-size) signatures.
# One sample in twelve uses all four codes so the full anchor-count axis has
# ordinary support without materially lowering canonical-profile coverage.
_CANONICAL_PROFILES = (
    (10, 10, 2),
    (11, 11, 3),
    (12, 12, 3),
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (10, 12),
        "grid_w": (10, 12),
        "n_anchors": (2, 4),
        "proto_size": (3, 5),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = bounds[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _draw_scheduled(ctx, label: str, domain: tuple[int, ...], scheduled: int) -> int:
    """Record every public axis while keeping deterministic lesson profiles."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return int(ctx.draw_choice(label, domain))
    return int(ctx.draw_choice(label, (scheduled,)))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _rotated(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    shape = _normalize(cells)
    if not shape:
        return ()
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    if code == 2:
        transformed = shape
    elif code == 3:
        transformed = tuple((col, height - 1 - row) for row, col in shape)
    elif code == 4:
        transformed = tuple(
            (height - 1 - row, width - 1 - col) for row, col in shape
        )
    elif code == 5:
        transformed = tuple((width - 1 - col, row) for row, col in shape)
    else:
        transformed = shape
    return _normalize(transformed)


def _rotation_signatures(
    cells: Iterable[tuple[int, int]],
) -> set[tuple[tuple[int, int], ...]]:
    return {_rotated(cells, code) for code in _ANCHOR_CODES}


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    unseen = set(cells)
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def _prototype_components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 2, 3, 4, 5)
        }
    )
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for color in colors:
        cells = {
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        }
        components.extend((color, comp) for comp in _components(cells))
    return components


def _authority_facts(grid: list[list[int]]) -> dict[str, Any]:
    components = _prototype_components(grid)
    if not components:
        raise ValueError("input has no non-anchor prototype object")
    # The Racket authority selects the largest non-anchor object.  Row-major
    # component order provides a deterministic tie break for malformed inputs.
    proto_color, proto_cells = max(
        components,
        key=lambda item: (len(item[1]), -min(item[1])[0], -min(item[1])[1]),
    )
    anchors = tuple(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in _ANCHOR_CODES
    )
    shape = _normalize(proto_cells)
    return {
        "proto_color": proto_color,
        "proto_cells": set(proto_cells),
        "shape": shape,
        "anchors": anchors,
    }


def _stamp_footprint(
    anchor: tuple[int, int], shape: Iterable[tuple[int, int]], code: int
) -> set[tuple[int, int]]:
    row, col = anchor
    return {(row + dr, col + dc) for dr, dc in _rotated(shape, code)}


def _render(
    grid: list[list[int]],
    *,
    code_map: dict[int, int] | None = None,
    fresh: bool = True,
    anchor_colors: bool = False,
    align_first_cell: bool = False,
) -> list[list[int]]:
    facts = _authority_facts(grid)
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0) if fresh else [list(row) for row in grid]
    shape = facts["shape"]
    proto_color = facts["proto_color"]
    for anchor_row, anchor_col, source_code in facts["anchors"]:
        code = code_map.get(source_code, source_code) if code_map else source_code
        transformed = list(_rotated(shape, code))
        if align_first_cell and transformed:
            first_row, first_col = min(transformed)
            transformed = [
                (row - first_row, col - first_col) for row, col in transformed
            ]
        color = source_code if anchor_colors else proto_color
        for dr, dc in transformed:
            row, col = anchor_row + dr, anchor_col + dc
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket authority."""
    return _render(grid)


def _rival_no_rotation(grid: list[list[int]]) -> list[list[int]]:
    return _render(grid, code_map={2: 2, 3: 2, 4: 2, 5: 2})


def _rival_swap_quarter_turns(grid: list[list[int]]) -> list[list[int]]:
    return _render(grid, code_map={2: 2, 3: 5, 4: 4, 5: 3})


def _rival_code4_identity(grid: list[list[int]]) -> list[list[int]]:
    return _render(grid, code_map={2: 2, 3: 3, 4: 2, 5: 5})


def _rival_preserve_input(grid: list[list[int]]) -> list[list[int]]:
    return _render(grid, fresh=False)


def _rival_anchor_colors(grid: list[list[int]]) -> list[list[int]]:
    return _render(grid, anchor_colors=True)


def _rival_align_first_cell(grid: list[list[int]]) -> list[list[int]]:
    return _render(grid, align_first_cell=True)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_rotation_codes": _rival_no_rotation,
    "swap_clockwise_counterclockwise": _rival_swap_quarter_turns,
    "code_4_as_identity": _rival_code4_identity,
    "stamp_on_input_instead_of_fresh_canvas": _rival_preserve_input,
    "paint_stamps_with_anchor_colors": _rival_anchor_colors,
    "align_first_occupied_cell_instead_of_bbox_origin": _rival_align_first_cell,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# The only canonical code-4 exemplar is 180-degree symmetric, so the public
# task alone cannot distinguish code 4 from identity. Generated asymmetric
# code-4 witnesses are therefore essential rather than cosmetic diversity.
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "code_4_as_identity": _rival_code4_identity,
}


def _structural_facts(grid: list[list[int]]) -> dict[str, Any]:
    anchors = tuple(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in _ANCHOR_CODES
    )
    components = _prototype_components(grid)
    proto_colors = {
        value
        for row in grid
        for value in row
        if value not in (0, 2, 3, 4, 5)
    }
    proto_cells = set().union(*(component for _, component in components)) if components else set()
    shape = _normalize(proto_cells)
    return {
        "anchors": anchors,
        "components": components,
        "proto_colors": proto_colors,
        "proto_cells": proto_cells,
        "shape": shape,
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis directly from a generated input."""
    errors = _grid_errors(grid)
    if errors:
        return {}
    facts = _structural_facts([list(row) for row in grid])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_anchors": len(facts["anchors"]),
        "proto_size": len(facts["proto_cells"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's actual object/stamp grammar and exact overrides."""
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors
    source = [list(row) for row in grid]
    height, width = len(source), len(source[0])
    if not 10 <= height <= 12 or not 10 <= width <= 12:
        errors.append(f"grid dimensions must each be in 10..12, got {height}x{width}")

    facts = _structural_facts(source)
    anchors = facts["anchors"]
    anchor_codes = [code for _, _, code in anchors]
    if not 2 <= len(anchors) <= 4:
        errors.append(f"expected 2-4 anchor cells, found {len(anchors)}")
    if len(set(anchor_codes)) != len(anchor_codes):
        errors.append("anchor transform codes must be distinct")

    if len(facts["proto_colors"]) != 1:
        errors.append("prototype must use exactly one non-anchor color")
    if len(facts["components"]) != 1:
        errors.append("prototype must be exactly one 4-connected object")
    proto_cells = facts["proto_cells"]
    if not 3 <= len(proto_cells) <= 5:
        errors.append(f"prototype must contain 3-5 cells, found {len(proto_cells)}")
    if proto_cells and not _connected(proto_cells):
        errors.append("prototype must be 4-connected")
    shape = facts["shape"]
    if shape:
        bbox_height = max(row for row, _ in shape) + 1
        bbox_width = max(col for _, col in shape) + 1
        if bbox_height > 3 or bbox_width > 3:
            errors.append(
                f"prototype bounding box must be at most 3x3, got {bbox_height}x{bbox_width}"
            )

    nonzero = {
        (row, col)
        for row, values in enumerate(source)
        for col, value in enumerate(values)
        if value != 0
    }
    for row, col, _code in anchors:
        if any((row + dr, col + dc) in nonzero for dr, dc in _CARDINAL):
            errors.append(f"anchor at {(row, col)} must be 4-neighbor isolated")

    footprints: list[set[tuple[int, int]]] = []
    anchor_positions = {(row, col) for row, col, _ in anchors}
    for row, col, code in anchors:
        footprint = _stamp_footprint((row, col), shape, code) if shape else set()
        if any(not (0 <= rr < height and 0 <= cc < width) for rr, cc in footprint):
            errors.append(f"stamp for anchor {(row, col)} is clipped by the grid")
        if footprint & proto_cells:
            errors.append(f"stamp for anchor {(row, col)} overlaps the prototype")
        other_anchors = anchor_positions - {(row, col)}
        if footprint & other_anchors:
            errors.append(f"stamp for anchor {(row, col)} covers another anchor")
        if any(footprint & earlier for earlier in footprints):
            errors.append(f"stamp for anchor {(row, col)} overlaps another stamp")
        footprints.append(footprint)

    if isinstance(meta, dict) and not errors:
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(source)
            for axis in AXES:
                if axis in requested and requested[axis] is not None:
                    if observed.get(axis) != requested[axis]:
                        errors.append(
                            f"override {axis}={requested[axis]!r} realized as "
                            f"{observed.get(axis)!r}"
                        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict grammar intentionally includes all three canonical inputs."""
    return self_check(grid)


def semantic_observables(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    source = [list(row) for row in grid]
    facts = _authority_facts(source)
    height, width = len(source), len(source[0])
    footprints = [
        _stamp_footprint((row, col), facts["shape"], code)
        for row, col, code in facts["anchors"]
    ]
    all_cells = set().union(*footprints) if footprints else set()
    full = all(0 <= row < height and 0 <= col < width for row, col in all_cells)
    pairwise = all(
        not footprints[i] & footprints[j]
        for i in range(len(footprints))
        for j in range(i + 1, len(footprints))
    )
    output = rule_mirror(source)
    return {
        "errors": [],
        "codes": tuple(code for _, _, code in facts["anchors"]),
        "proto_size": len(facts["shape"]),
        "proto_color": facts["proto_color"],
        "rotation_signature_count": len(_rotation_signatures(facts["shape"])),
        "stamps_full_and_disjoint": (
            full
            and pairwise
            and not all_cells & facts["proto_cells"]
        ),
        "rivals_eliminated": tuple(
            name for name, rival in LESSON_COMPETITORS.items() if rival(source) != output
        ),
    }


def _code_present(code: int):
    return lambda grid: not self_check(grid) and code in semantic_observables(grid)["codes"]


def _rival_differs(name: str):
    def witness(grid) -> bool:
        if self_check(grid):
            return False
        return LESSON_COMPETITORS[name](grid) != rule_mirror(grid)

    return witness


SEMANTIC_WITNESSES = {
    "code_2_identity_branch": _code_present(2),
    "code_3_clockwise_branch": _code_present(3),
    "code_4_half_turn_branch": _code_present(4),
    "code_5_counterclockwise_branch": _code_present(5),
    "rotation_codes_change_output": _rival_differs("ignore_rotation_codes"),
    "quarter_turn_direction_changes_output": _rival_differs(
        "swap_clockwise_counterclockwise"
    ),
    "code_4_is_not_identity": _rival_differs("code_4_as_identity"),
    "fresh_canvas_erases_source": _rival_differs(
        "stamp_on_input_instead_of_fresh_canvas"
    ),
    "prototype_color_is_reused": _rival_differs("paint_stamps_with_anchor_colors"),
    "anchor_is_bbox_origin": _rival_differs(
        "align_first_occupied_cell_instead_of_bbox_origin"
    ),
}
BRANCH_WITNESSES = {
    "code_2_identity_branch",
    "code_3_clockwise_branch",
    "code_4_half_turn_branch",
    "code_5_counterclockwise_branch",
}
WITNESS_RIVALS = {
    "rotation_codes_change_output": ["ignore_rotation_codes"],
    "quarter_turn_direction_changes_output": ["swap_clockwise_counterclockwise"],
    "code_4_is_not_identity": ["code_4_as_identity"],
    "fresh_canvas_erases_source": ["stamp_on_input_instead_of_fresh_canvas"],
    "prototype_color_is_reused": ["paint_stamps_with_anchor_colors"],
    "anchor_is_bbox_origin": [
        "align_first_occupied_cell_instead_of_bbox_origin"
    ],
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose a stable four-position code schedule to lesson audits."""
    del seed, difficulty
    return int(sample_index) % 4


SCHEDULE_PROFILES = (0, 1, 2, 3)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    validated = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        malformed = self_check(pair["input"])
        if malformed:
            reasons.append(f"demo {index} malformed: {malformed[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with selected authority")
            continue
        validated.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with selected authority")

    if reasons or len(validated) != len(demos):
        return reasons

    seen_codes = {
        code
        for pair in validated
        for code in semantic_observables(pair["input"])["codes"]
    }
    missing = sorted(set(_ANCHOR_CODES) - seen_codes)
    if missing:
        reasons.append(f"demonstrations do not cover transform code(s): {missing}")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in validated):
            reasons.append(f"named rival survives all demonstrations: {name}")
    return reasons


def _grow_asymmetric_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    allowed = {(row, col) for row in range(3) for col in range(3)}
    for _ in range(3000):
        cells = {rng.choice(sorted(allowed))}
        while len(cells) < size:
            frontier = sorted(
                {
                    (row + dr, col + dc)
                    for row, col in cells
                    for dr, dc in _CARDINAL
                    if (row + dr, col + dc) in allowed
                    and (row + dr, col + dc) not in cells
                }
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != size:
            continue
        shape = _normalize(cells)
        if len(_rotation_signatures(shape)) != 4:
            continue
        # Randomize which bbox corner/edge is empty while retaining the free
        # polyomino. This makes placement-origin semantics observable.
        shape = _rotated(shape, rng.choice(_ANCHOR_CODES))
        return shape
    raise ValueError(f"could not grow asymmetric connected prototype of size {size}")


def _codes_for(sample_index: int, n_anchors: int) -> tuple[int, ...]:
    schedule = {
        2: _CODE_SCHEDULE_2,
        3: _CODE_SCHEDULE_3,
        4: _CODE_SCHEDULE_4,
    }[n_anchors]
    return schedule[int(sample_index) % len(schedule)]


def _placement_candidates(
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
    code: int,
) -> list[tuple[tuple[int, int], set[tuple[int, int]]]]:
    transformed = _rotated(shape, code)
    max_row = max(row for row, _ in transformed)
    max_col = max(col for _, col in transformed)
    return [
        (
            (row, col),
            {(row + dr, col + dc) for dr, dc in transformed},
        )
        for row in range(height - max_row)
        for col in range(width - max_col)
    ]


def _place_scene(
    rng,
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
    proto_color: int,
    codes: tuple[int, ...],
) -> list[list[int]] | None:
    proto_height = max(row for row, _ in shape) + 1
    proto_width = max(col for _, col in shape) + 1
    proto_origins = [
        (row, col)
        for row in range(height - proto_height + 1)
        for col in range(width - proto_width + 1)
    ]
    rng.shuffle(proto_origins)

    for proto_row, proto_col in proto_origins:
        proto_cells = {
            (proto_row + dr, proto_col + dc) for dr, dc in shape
        }
        per_code = {
            code: _placement_candidates(height, width, shape, code)
            for code in codes
        }
        for candidates in per_code.values():
            rng.shuffle(candidates)

        chosen: list[tuple[int, int, int, set[tuple[int, int]]]] = []

        def search(index: int) -> bool:
            if index == len(codes):
                return True
            code = codes[index]
            for (row, col), footprint in per_code[code]:
                anchor = (row, col)
                if anchor in proto_cells or footprint & proto_cells:
                    continue
                if any(
                    abs(row - rr) + abs(col - cc) == 1
                    for rr, cc in proto_cells
                ):
                    continue
                valid = True
                for other_row, other_col, _other_code, other_footprint in chosen:
                    other_anchor = (other_row, other_col)
                    if abs(row - other_row) + abs(col - other_col) == 1:
                        valid = False
                        break
                    if footprint & other_footprint:
                        valid = False
                        break
                    if anchor in other_footprint or other_anchor in footprint:
                        valid = False
                        break
                if not valid:
                    continue
                chosen.append((row, col, code, footprint))
                if search(index + 1):
                    return True
                chosen.pop()
            return False

        if not search(0):
            continue
        grid = full_grid(height, width, 0)
        for row, col in proto_cells:
            grid[row][col] = proto_color
        for row, col, code, _footprint in chosen:
            grid[row][col] = code
        return grid
    return None


def _default_profile(sample_index: int) -> tuple[int, int, int]:
    if int(sample_index) % 12 == 11:
        return (12, 12, 4)
    return _CANONICAL_PROFILES[int(sample_index) % len(_CANONICAL_PROFILES)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w, scheduled_n = _default_profile(int(sample_index))
    height = _draw_scheduled(ctx, "grid_h", (10, 11, 12), scheduled_h)
    width = _draw_scheduled(ctx, "grid_w", (10, 11, 12), scheduled_w)
    n_anchors = _draw_scheduled(ctx, "n_anchors", (2, 3, 4), scheduled_n)

    scheduled_size = (3, 4, 5)[int(sample_index) % 3]
    if difficulty == "easy":
        scheduled_size = (3, 3, 4)[int(sample_index) % 3]
    elif difficulty == "hard":
        scheduled_size = (4, 5, 5)[int(sample_index) % 3]
    proto_size = _draw_scheduled(ctx, "proto_size", (3, 4, 5), scheduled_size)

    rng = ctx.draw_rng("layout")
    proto_color = rng.choice(_PROTO_COLORS)
    codes = list(_codes_for(int(sample_index), n_anchors))
    rng.shuffle(codes)
    code_tuple = tuple(codes)

    for _ in range(600):
        shape = _grow_asymmetric_shape(rng, proto_size)
        grid = _place_scene(
            rng, height, width, shape, proto_color, code_tuple
        )
        if grid is None or self_check(grid):
            continue
        output = rule_mirror(grid)
        # Each example must expose all rivals whose distinguishing branch it
        # contains. Code 4 is scheduled into every three-example lesson.
        required = set(LESSON_COMPETITORS)
        if 4 not in code_tuple:
            required.remove("code_4_as_identity")
        if any(LESSON_COMPETITORS[name](grid) == output for name in required):
            continue
        return grid
    raise ValueError("could not realize a decisive non-overlapping stamp lesson")
