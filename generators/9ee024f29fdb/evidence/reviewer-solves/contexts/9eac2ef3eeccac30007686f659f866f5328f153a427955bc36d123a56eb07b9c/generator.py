"""Generator for the periodic-lattice / erase-cyan ARC task.

Canonical rule (unchanged): every row or column whose zero-based index is a
multiple of four is cleared to background; elsewhere color 8 is erased and
all other values are painted red (2).

The sampler deliberately alternates two teaching profiles:

* ``canonical_core`` keeps the canonical {0, 8} palette and clean periodic
  lattice, with a heavy prior on the four canonical shapes.
* ``joint_counterexample`` adds observable interior decoy colors and puts
  nonzero values on every periodic row and column.  The authority still clears
  those cells, but this profile falsifies both "preserve unknown colors" and
  "find the lattice as all-zero lines" shortcuts.

``eight_density`` and ``eight_layout`` remain useful construction controls, but
are explicitly diagnostic rather than exact axes: finite grids quantize a
requested density, and several geometric layouts are not uniquely recoverable
from pixels.  Every exact public axis is recoverable by ``observe_overrides``.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9ee024f29fdb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "82f439b3efb8"

SUMMARY = (
    "Periodic 4-spaced lattice task. On zero-based coordinates, output 0 when "
    "r%4==0 or c%4==0; otherwise erase input color 8 to 0 and paint every "
    "other value red (2). Default lessons alternate a canonical {0,8}, clean-"
    "lattice profile with a joint counterexample profile containing interior "
    "decoys and nonzero values on every periodic row/column."
)

INVARIANTS = [
    "grid dimensions are one of 5, 9, 13, 17 on each axis",
    "at least one interior cell is color 8 and at least one is not color 8",
    "interior decoy palette has 0..2 distinct colors outside {0,8}",
    "lattice is either entirely zero or every periodic row and column has noise",
]

SIZES = (5, 9, 13, 17)
CANONICAL_SHAPES = frozenset({(9, 13), (5, 13), (9, 9), (13, 13)})
EIGHT_LAYOUTS = ("random", "cluster", "aligned_to_4grid", "column", "row")
DECOY_COLORS = (1, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 5|9|13|17",
        "valid": "5|9|13|17",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 5|9|13|17",
        "valid": "5|9|13|17",
    },
    "decoy_palette_size": {
        "type": "int",
        "default": "0 on canonical_core; keyed 1..2 on joint_counterexample",
        "valid": "0..2",
    },
    "lattice_noise": {
        "type": "bool",
        "default": "false on canonical_core; true on joint_counterexample",
        "valid": "false|true",
    },
    "eight_density": {
        "type": "float",
        "default": "difficulty-weighted 0.25..0.70",
        "valid": "0.10..0.80",
        "probe": "diagnostic",
        "exact": False,
    },
    "eight_layout": {
        "type": "enum",
        "default": "keyed choice",
        "valid": "|".join(EIGHT_LAYOUTS),
        "probe": "diagnostic",
        "exact": False,
    },
}

# Every Cartesian combination of the four exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = ("canonical_core", "joint_counterexample")
MIN_STRICT_FRAC = 0.20
EXAMPLES_NEEDED = 3


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Alternate profiles so every two consecutive samples include a rebuttal."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int or value not in SIZES:
            raise ValueError(f"{label} must be one of {SIZES}, got {value!r}")

    value = overrides.get("decoy_palette_size")
    if value is not None and (type(value) is not int or not 0 <= value <= 2):
        raise ValueError(
            f"decoy_palette_size must be an integer in [0,2], got {value!r}"
        )

    value = overrides.get("lattice_noise")
    if value is not None and type(value) is not bool:
        raise ValueError(f"lattice_noise must be bool, got {value!r}")

    value = overrides.get("eight_density")
    if value is not None:
        if type(value) not in (int, float) or isinstance(value, bool):
            raise ValueError(f"eight_density must be numeric, got {value!r}")
        if not 0.10 <= float(value) <= 0.80:
            raise ValueError(f"eight_density must be in [0.10,0.80], got {value!r}")

    value = overrides.get("eight_layout")
    if value is not None and (type(value) is not str or value not in EIGHT_LAYOUTS):
        raise ValueError(
            f"eight_layout must be one of {EIGHT_LAYOUTS}, got {value!r}"
        )


def _dimension_options(difficulty: Any, axis: str) -> tuple[int, ...]:
    """Canonical-heavy weights; every valid endpoint remains reachable."""
    if difficulty == "easy":
        return (
            (5, 5, 5, 5, 9, 9, 9, 9, 13, 17)
            if axis == "h"
            else (13, 13, 13, 13, 13, 13, 9, 9, 5, 17)
        )
    if difficulty == "hard":
        return (
            (13, 13, 13, 13, 13, 9, 9, 9, 5, 17)
            if axis == "h"
            else (13, 13, 13, 13, 13, 9, 9, 9, 5, 17)
        )
    return (
        (9, 9, 9, 9, 13, 13, 13, 5, 5, 17)
        if axis == "h"
        else (13, 13, 13, 13, 13, 9, 9, 9, 5, 17)
    )


def _density(ctx: Any, difficulty: Any) -> float:
    override = ctx.overrides.get("eight_density")
    if override is not None:
        # Consume and record the diagnostic override through the public draw API.
        return float(ctx.draw_choice("eight_density", (float(override),)))
    lo, hi = {
        "easy": (0.25, 0.45),
        "medium": (0.35, 0.60),
        "hard": (0.45, 0.70),
    }.get(difficulty, (0.25, 0.65))
    return ctx.draw_rng("eight_density").uniform(lo, hi)


def _profiled_choice(
    ctx: Any,
    label: str,
    scheduled: Any,
    valid: Sequence[Any],
) -> Any:
    options = tuple(valid) if ctx.overrides.get(label) is not None else (scheduled,)
    return ctx.draw_choice(label, options)


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    h = ctx.draw_choice("grid_h", _dimension_options(difficulty, "h"))
    w = ctx.draw_choice("grid_w", _dimension_options(difficulty, "w"))
    density = _density(ctx, difficulty)
    layout = ctx.draw_choice("eight_layout", EIGHT_LAYOUTS)

    if profile == "canonical_core":
        default_decoys = 0
        default_lattice_noise = False
    else:
        default_decoys = 1 + ctx.draw_rng("counterexample_decoys").randrange(2)
        default_lattice_noise = True

    n_decoys = int(
        _profiled_choice(ctx, "decoy_palette_size", default_decoys, (0, 1, 2))
    )
    lattice_noise = bool(
        _profiled_choice(ctx, "lattice_noise", default_lattice_noise, (False, True))
    )

    grid = full_grid(h, w, 0)
    interior = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r % 4 != 0 and c % 4 != 0
    ]
    cells_rng = ctx.draw_rng("cells")
    eight_cells = _eight_layout(layout, density, interior, cells_rng)
    eight_set = set(eight_cells)
    for r, c in eight_cells:
        grid[r][c] = 8

    remaining = [cell for cell in interior if cell not in eight_set]
    palette_rng = ctx.draw_rng("decoys")
    palette = list(DECOY_COLORS)
    palette_rng.shuffle(palette)
    palette = palette[:n_decoys]
    palette_rng.shuffle(remaining)
    for color, (r, c) in zip(palette, remaining):
        grid[r][c] = color
    if palette:
        for r, c in remaining[len(palette) :]:
            if palette_rng.random() < 0.20:
                grid[r][c] = palette_rng.choice(palette)

    if lattice_noise:
        _add_lattice_noise(grid)

    return grid


def _eight_layout(layout: str, density: float, interior: list[tuple[int, int]], rng):
    if not interior:
        return []
    target = max(1, min(len(interior) - 1, int(len(interior) * density)))

    if layout == "cluster":
        center_r, center_c = rng.choice(interior)
        cells = list(interior)
        rng.shuffle(cells)  # random tie order at equal Manhattan radius
        cells.sort(key=lambda rc: abs(rc[0] - center_r) + abs(rc[1] - center_c))
        return cells[:target]

    if layout == "aligned_to_4grid":
        aligned = [cell for cell in interior if cell[0] % 4 == 2 and cell[1] % 4 == 2]
        aligned_set = set(aligned)
        remainder = [cell for cell in interior if cell not in aligned_set]
        rng.shuffle(aligned)
        rng.shuffle(remainder)
        return (aligned + remainder)[:target]

    if layout == "column":
        columns = sorted({c for _, c in interior})
        rng.shuffle(columns)
        ordered = []
        for c in columns:
            cells = [cell for cell in interior if cell[1] == c]
            rng.shuffle(cells)
            ordered.extend(cells)
        return ordered[:target]

    if layout == "row":
        rows = sorted({r for r, _ in interior})
        rng.shuffle(rows)
        ordered = []
        for r in rows:
            cells = [cell for cell in interior if cell[0] == r]
            rng.shuffle(cells)
            ordered.extend(cells)
        return ordered[:target]

    if layout != "random":
        raise ValueError(f"unsupported eight_layout {layout!r}")
    cells = list(interior)
    rng.shuffle(cells)
    return cells[:target]


def _add_lattice_noise(grid: list[list[int]]) -> None:
    """Make every periodic row and column nonzero without touching interiors."""
    h, w = len(grid), len(grid[0])
    cells = {(r, 0) for r in range(0, h, 4)}
    cells.update({(0, c) for c in range(0, w, 4)})
    for index, (r, c) in enumerate(sorted(cells)):
        grid[r][c] = 8 if index % 2 == 0 else 1


def _shape_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], 0, 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], len(grid), width
    return [], len(grid), width


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the actual generated manifold, including its two lattice modes."""
    del difficulty, meta
    errors, h, w = _shape_errors(grid)
    if errors:
        return errors

    errors = []
    if h not in SIZES or w not in SIZES:
        errors.append(f"dimensions must each be one of {SIZES}, got {(h, w)}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    interior = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r % 4 != 0 and c % 4 != 0
    ]
    n_eights = sum(grid[r][c] == 8 for r, c in interior)
    if n_eights == 0:
        errors.append("no color-8 cell in the interior")
    if n_eights == len(interior):
        errors.append("all interior cells are color 8; no red-producing complement")

    decoys = {grid[r][c] for r, c in interior if grid[r][c] not in (0, 8)}
    if len(decoys) > 2:
        errors.append(f"interior uses {len(decoys)} decoy colors; maximum is 2")

    lattice = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r % 4 == 0 or c % 4 == 0
    ]
    if any(grid[r][c] != 0 for r, c in lattice):
        for r in range(0, h, 4):
            if not any(value != 0 for value in grid[r]):
                errors.append(f"noisy lattice row {r} is still all zero")
        for c in range(0, w, 4):
            if not any(grid[r][c] != 0 for r in range(h)):
                errors.append(f"noisy lattice column {c} is still all zero")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis solely from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors[0]}")
    h, w = len(grid), len(grid[0])
    decoys = {
        grid[r][c]
        for r in range(h)
        for c in range(w)
        if r % 4 != 0 and c % 4 != 0 and grid[r][c] not in (0, 8)
    }
    lattice_noise = any(
        grid[r][c] != 0
        for r in range(h)
        for c in range(w)
        if r % 4 == 0 or c % 4 == 0
    )
    return {
        "grid_h": h,
        "grid_w": w,
        "decoy_palette_size": len(decoys),
        "lattice_noise": lattice_noise,
    }


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical shape, binary palette, and clean periodic lattice."""
    errors = list(self_check(grid))
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in CANONICAL_SHAPES:
        errors.append(f"shape {(h, w)} is outside canonical profiles")
    if {value for row in grid for value in row} != {0, 8}:
        errors.append("canonical profile palette must be exactly {0,8}")
    if any(
        grid[r][c] != 0
        for r in range(h)
        for c in range(w)
        if r % 4 == 0 or c % 4 == 0
    ):
        errors.append("canonical profile lattice must be all zero")
    return errors


def _rule_mirror(grid):
    return [
        [
            0 if r % 4 == 0 or c % 4 == 0 or value == 8 else 2
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def _global_binary_inversion(grid):
    """Wrong: ignores coordinates and maps every non-8 value to red."""
    return [[0 if value == 8 else 2 for value in row] for row in grid]


def _erase_eights_only(grid):
    """Wrong: erases cyan but never repaints the other interior cells."""
    return [[0 if value == 8 else value for value in row] for row in grid]


def _preserve_decoys(grid):
    """Canonical-fitting wrong rule: preserves non-{0,8} interior colors."""
    return [
        [
            0
            if r % 4 == 0 or c % 4 == 0 or value == 8
            else (2 if value == 0 else value)
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def _zero_line_lattice(grid):
    """Canonical-fitting wrong rule: infers the lattice from all-zero lines."""
    h, w = len(grid), len(grid[0])
    zero_rows = {r for r, row in enumerate(grid) if all(value == 0 for value in row)}
    zero_cols = {
        c for c in range(w) if all(grid[r][c] == 0 for r in range(h))
    }
    return [
        [
            0 if r in zero_rows or c in zero_cols or value == 8 else 2
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def _has_periodic_lattice(grid) -> bool:
    return bool(grid and grid[0]) and any(
        r % 4 == 0 or c % 4 == 0
        for r in range(len(grid))
        for c in range(len(grid[0]))
    )


def _has_red_producing_interior(grid) -> bool:
    return any(
        value != 8
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r % 4 != 0 and c % 4 != 0
    )


def _has_interior_decoy(grid) -> bool:
    return any(
        value not in (0, 8)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r % 4 != 0 and c % 4 != 0
    )


def _has_nonzero_lattice(grid) -> bool:
    return any(
        value != 0
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r % 4 == 0 or c % 4 == 0
    )


SEMANTIC_WITNESSES = {
    "periodic_coordinate_lattice": _has_periodic_lattice,
    "interior_repaint": _has_red_producing_interior,
    "decoy_repaint": _has_interior_decoy,
    "nonzero_lattice": _has_nonzero_lattice,
}
SEMANTIC_RIVALS = {
    "global_binary_inversion": _global_binary_inversion,
    "erase_eights_only": _erase_eights_only,
    "preserve_decoys": _preserve_decoys,
    "zero_line_lattice": _zero_line_lattice,
}
WITNESS_RIVALS = {
    "periodic_coordinate_lattice": ["global_binary_inversion"],
    "interior_repaint": ["erase_eights_only"],
    "decoy_repaint": ["preserve_decoys"],
    "nonzero_lattice": ["zero_line_lattice"],
}
CANONICAL_SHORTCUTS = {
    "preserve_decoys": _preserve_decoys,
    "zero_line_lattice": _zero_line_lattice,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid labels and demonstrations that refute each named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
        elif _rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif _rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons
