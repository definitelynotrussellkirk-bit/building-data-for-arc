"""Generator for Right-Hand Echo (task 2c35533cc389).

Selected rule: keep the input grid, then for every red(2) cell in the INPUT,
paint blue(1) one column to its right when that destination is in bounds.
A red cell on the right edge therefore paints nothing.  If the destination is
another red cell, the blue paint overwrites that destination in the OUTPUT;
the set of source red cells is read from the original input, not incrementally.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c35533cc389"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "6c442aca44f9"

SUMMARY = (
    "A sparse black grid contains red(2) source cells. Starting from an exact "
    "copy of the input, every source red cell paints blue(1) one column to its "
    "right when that cell is in bounds. Right-edge reds paint nothing. A blue "
    "write may overwrite a red destination, but every source is determined "
    "from the original input."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

INVARIANTS = [
    "background is 0 and the input palette is exactly a subset of {0, 2}",
    "grid height is 5..8 and width is 6..10",
    "there are 2..8 red(2) source cells",
    "right-edge red cells are lawful and exercise the in-bounds branch",
    "ordinary sources are horizontally isolated; overwrite lessons contain exactly one adjacent red-red pair",
]

COUNTER_HYPOTHESES = [
    "return the input unchanged",
    "shift reds right instead of preserving the source reds",
    "paint left instead of right",
    "paint only the first red source",
    "wrap a right-edge red to column zero",
    "paint right only when the destination is background",
]

_H_LO, _H_HI = 5, 8
_W_LO, _W_HI = 6, 10
_N_LO, _N_HI = 2, 8
_EDGE_MODES = ("absent", "present")
_RIGHT_NEIGHBOR_RELATIONS = ("empty", "red")
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

# Every declared axis is exact, independently overrideable in every difficulty
# band, and recoverable from the returned grid via observe_overrides().
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor/control profile",
        "valid": "5..8",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor/control profile",
        "valid": "6..10",
        "doc": "Exact returned grid width.",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 4..6; exact override 2..8",
        "valid": "2..8",
        "doc": "Exact number of red(2) source cells.",
    },
    "right_edge_mode": {
        "type": "enum",
        "default": "scheduled absent/present",
        "valid": "absent|present",
        "doc": "Whether at least one source red occupies the rightmost column.",
    },
    "right_neighbor_relation": {
        "type": "enum",
        "default": "scheduled empty/red",
        "valid": "empty|red",
        "doc": "Whether any source red has another source red immediately right.",
    },
}

# Three consecutive examples always contain one ordinary canonical anchor, one
# right-edge clipping witness, and one occupied-destination overwrite witness.
SCHEDULE_PROFILES = ("anchor", "edge", "overwrite")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Cycle profiles by sample index; every three-example window sees all."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _default_controls(ctx, sample_index: int, difficulty) -> dict[str, object]:
    profile = schedule_profile(ctx.seed, sample_index, difficulty=difficulty)
    rng = ctx.draw_rng("default_controls")

    if profile == "anchor":
        # Canonical rows are 6x7 or 6x8 with 4..6 reds and no horizontal red-red
        # pair. This slot intentionally remains very close to those examples.
        return {
            "grid_h": 6,
            "grid_w": rng.choice((7, 8)),
            "n_cells": rng.choice((4, 5, 6)),
            "right_edge_mode": "absent",
            "right_neighbor_relation": "empty",
        }

    if profile == "edge":
        # Two of the three canonical inputs contain a right-edge red. Preserve
        # that no-write boundary branch explicitly instead of banning it.
        return {
            "grid_h": 6,
            "grid_w": rng.choice((7, 8)),
            "n_cells": rng.choice((4, 5, 6)),
            "right_edge_mode": "present",
            "right_neighbor_relation": "empty",
        }

    # The selected Racket program paints unconditionally onto the destination,
    # so a red-red horizontal pair is the smallest counterexample to the
    # tempting but wrong "only fill empty cells" interpretation. Keep the easy
    # band canonical-sized; let medium/hard broaden only this control slot.
    if difficulty == "hard":
        height, width = 8, 10
        n_cells = rng.choice((6, 7, 8))
    elif difficulty == "medium":
        height, width = 7, 9
        n_cells = rng.choice((5, 6, 7))
    else:
        height, width = 6, rng.choice((7, 8))
        n_cells = rng.choice((4, 5, 6))
    return {
        "grid_h": height,
        "grid_w": width,
        "n_cells": n_cells,
        "right_edge_mode": rng.choice(_EDGE_MODES),
        "right_neighbor_relation": "red",
    }


def _horizontal_red_edges(cells: set[tuple[int, int]]) -> int:
    return sum((row, col + 1) in cells for row, col in cells)


def _has_horizontal_red_pair(cells: set[tuple[int, int]]) -> bool:
    return _horizontal_red_edges(cells) > 0


def _place_sources(
    height: int,
    width: int,
    count: int,
    edge_mode: str,
    neighbor_relation: str,
    rng,
) -> set[tuple[int, int]]:
    """Place exactly ``count`` sources while making both semantic axes exact."""
    chosen: set[tuple[int, int]] = set()

    if neighbor_relation == "red":
        if edge_mode == "present":
            # One pair can witness both the overwrite and the boundary branch.
            pair_candidates = [
                ((row, width - 2), (row, width - 1))
                for row in range(height)
            ]
        else:
            pair_candidates = [
                ((row, col), (row, col + 1))
                for row in range(height)
                for col in range(width - 2)
            ]
        first, second = rng.choice(pair_candidates)
        chosen.update((first, second))
    elif edge_mode == "present":
        chosen.add((rng.randrange(height), width - 1))

    # When right_edge_mode is present the mandatory edge source was seeded
    # above. Filler sources stay off the edge, matching the canonical support
    # (zero or one right-edge red) and making the boundary witness exact.
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width - 1)
    ]
    rng.shuffle(candidates)

    for cell in candidates:
        if len(chosen) >= count:
            break
        if cell in chosen:
            continue
        # The ordinary grammar is sparse. The overwrite profile has exactly
        # one deliberate horizontal red-red edge (seeded above); all filler
        # sources remain horizontally isolated. This keeps the decisive
        # overwrite branch without drifting into bars/solid blobs.
        row, col = cell
        if (row, col - 1) in chosen or (row, col + 1) in chosen:
            continue
        chosen.add(cell)

    if len(chosen) != count:
        raise ValueError(
            "could not place exact source controls: "
            f"grid={height}x{width}, n_cells={count}, "
            f"right_edge_mode={edge_mode!r}, "
            f"right_neighbor_relation={neighbor_relation!r}"
        )
    if (any(col == width - 1 for _, col in chosen)) != (edge_mode == "present"):
        raise AssertionError("right_edge_mode construction invariant failed")
    expected_edges = 1 if neighbor_relation == "red" else 0
    if _horizontal_red_edges(chosen) != expected_edges:
        raise AssertionError("right_neighbor_relation construction invariant failed")
    return chosen


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    """Fail closed on public scalar arguments before GenCtx can coerce them."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; valid axes: "
            f"{', '.join(AXES)}"
        )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Schedule defaults first, then consume them through the same typed GenCtx
    # draw API as explicit overrides. This keeps the full declared override
    # domain valid in every difficulty band while retaining exact provenance.
    for axis, value in _default_controls(ctx, sample_index, difficulty).items():
        if ctx.overrides.get(axis) is None:
            ctx.overrides[axis] = value

    height = ctx.draw_int_strict("grid_h", _H_LO, _H_HI)
    width = ctx.draw_int_strict("grid_w", _W_LO, _W_HI)
    n_cells = ctx.draw_int_strict("n_cells", _N_LO, _N_HI)
    edge_mode = ctx.draw_choice("right_edge_mode", _EDGE_MODES)
    neighbor_relation = ctx.draw_choice(
        "right_neighbor_relation", _RIGHT_NEIGHBOR_RELATIONS
    )

    sources = _place_sources(
        height,
        width,
        n_cells,
        edge_mode,
        neighbor_relation,
        ctx.draw_rng("layout"),
    )
    grid = full_grid(height, width, 0)
    for row, col in sources:
        grid[row][col] = 2
    return grid


def _shape_errors(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["empty row"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["ragged grid"]
    return len(grid), width, []


def _red_cells(grid) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact declared axis from the returned INPUT grid."""
    height, width = len(grid), len(grid[0])
    reds = _red_cells(grid)
    return {
        "grid_h": height,
        "grid_w": width,
        "n_cells": len(reds),
        "right_edge_mode": (
            "present" if any(col == width - 1 for _, col in reds) else "absent"
        ),
        "right_neighbor_relation": (
            "red" if _has_horizontal_red_pair(reds) else "empty"
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible sparse 0/2 input grammar."""
    del difficulty
    height, width, errors = _shape_errors(grid)
    if errors:
        return errors

    if not (_H_LO <= height <= _H_HI and _W_LO <= width <= _W_HI):
        errors.append(
            f"dims {height}x{width} outside {_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}"
        )

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if type(value) is not int or value not in (0, 2):
                errors.append(
                    f"input cell {(row, col)} must be black(0) or red(2), got {value!r}"
                )
                return errors

    reds = _red_cells(grid)
    if not (_N_LO <= len(reds) <= _N_HI):
        errors.append(
            f"expected {_N_LO}..{_N_HI} red(2) sources, found {len(reds)}"
        )
    horizontal_edges = _horizontal_red_edges(reds)
    if horizontal_edges > 1:
        errors.append(
            "sparse grammar permits at most one horizontal red-red adjacency; "
            f"found {horizontal_edges}"
        )

    requested: dict[str, object] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"{axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked profile supported by the three canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if observed["grid_h"] != 6 or observed["grid_w"] not in (7, 8):
        reasons.append(
            f"canonical shapes are 6x7 or 6x8, got {observed['grid_h']}x{observed['grid_w']}"
        )
    if observed["n_cells"] not in (4, 5, 6):
        reasons.append(
            f"canonical inputs contain 4..6 red sources, found {observed['n_cells']}"
        )
    if observed["right_neighbor_relation"] != "empty":
        reasons.append("canonical inputs contain no horizontally adjacent red sources")
    edge_reds = sum(1 for row in grid if row[-1] == 2)
    if edge_reds > 1:
        reasons.append(f"canonical inputs contain at most one right-edge red, found {edge_reds}")
    return reasons


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    del height
    # Read ALL sources before painting so an overwritten red still acts as a
    # source exactly as it does in the selected functional Racket program.
    sources = sorted(_red_cells(grid))
    for row, col in sources:
        if col + 1 < width:
            output[row][col + 1] = 1
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_shift_right(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    width = len(grid[0])
    for row, col in _red_cells(grid):
        if col + 1 < width:
            output[row][col + 1] = 1
    return output


def _rival_paint_left(grid):
    output = [list(row) for row in grid]
    for row, col in _red_cells(grid):
        if col > 0:
            output[row][col - 1] = 1
    return output


def _rival_first_red_only(grid):
    output = [list(row) for row in grid]
    width = len(grid[0])
    sources = sorted(_red_cells(grid))
    if sources:
        row, col = sources[0]
        if col + 1 < width:
            output[row][col + 1] = 1
    return output


def _rival_wrap_right_edge(grid):
    output = [list(row) for row in grid]
    width = len(grid[0])
    for row, col in _red_cells(grid):
        output[row][(col + 1) % width] = 1
    return output


def _rival_only_empty_right(grid):
    output = [list(row) for row in grid]
    width = len(grid[0])
    for row, col in _red_cells(grid):
        if col + 1 < width and grid[row][col + 1] == 0:
            output[row][col + 1] = 1
    return output


def _valid(grid) -> bool:
    return not self_check(grid)


def _actionable_count(grid) -> int:
    width = len(grid[0])
    return sum(col + 1 < width for _, col in _red_cells(grid))


def _witness_actionable_red(grid) -> bool:
    return _valid(grid) and _actionable_count(grid) >= 1


def _witness_multiple_actionable_reds(grid) -> bool:
    return _valid(grid) and _actionable_count(grid) >= 2


def _witness_right_edge_red(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["right_edge_mode"] == "present"


def _witness_red_destination(grid) -> bool:
    return (
        _valid(grid)
        and observe_overrides(grid)["right_neighbor_relation"] == "red"
    )


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "actionable_red_changes_output": _witness_actionable_red,
    "multiple_red_sources_act": _witness_multiple_actionable_reds,
    "right_edge_red_is_clipped": _witness_right_edge_red,
    "red_right_neighbor_is_overwritten": _witness_red_destination,
}

SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _rival_identity,
    "shift_right_delete_sources": _rival_shift_right,
    "paint_left": _rival_paint_left,
    "first_red_only": _rival_first_red_only,
    "wrap_right_edge": _rival_wrap_right_edge,
    "only_empty_right": _rival_only_empty_right,
}

WITNESS_RIVALS = {
    "actionable_red_changes_output": ["identity", "shift_right_delete_sources"],
    "multiple_red_sources_act": ["first_red_only"],
    "right_edge_red_is_clipped": ["wrap_right_edge"],
    "red_right_neighbor_is_overwritten": ["only_empty_right"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# This tempting interpretation fits every canonical pair because canonical
# destinations are either black or out of bounds. The scheduled overwrite slot
# supplies the generated counterexample that the canonical data cannot.
CANONICAL_SHORTCUTS = {
    "only_empty_right": _rival_only_empty_right,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo lesson to eliminate all named rival rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    killed = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the selected rule")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            killed[name] = killed[name] or rival(demo["input"]) != expected

    for name, was_killed in killed.items():
        if not was_killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
