"""Curriculum-safe input sampler for first-nonzero parity painting.

The selected Racket authority scans row-major for the first nonzero cell, paints
color 4 above it in columns of matching parity, and moves the seed color down
one row.  Generated labels remain Racket-derived; the Python rule below exists
only as an executable *wrong* competitor for lesson-identifiability checks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "033db13a9d37"
TASK_ID = GENERATOR_ID
RULE_HASH = "3773168d1737"
VERSION = "2.0.0"
SUMMARY = (
    "A row-major first nonzero seed controls a parity-striped color-4 canopy "
    "and drops one row. Alternating later-decoy witnesses make every three-demo "
    "rotation refute the canonical-fitting last-nonzero shortcut."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular 3..18 by 3..18 grid with integer ARC colors",
    "exactly one seed or one seed plus one visually distinct later decoy",
    "the first nonzero seed is above the bottom row so its one-row echo is visible",
    "input never contains color 4, which is reserved for the output canopy",
    "every four consecutive samples alternate two decoy witnesses and two single-seed anchors",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-weighted full domain",
        "valid": "3..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-weighted full domain",
        "valid": "3..18",
    },
    "fg_color": {
        "type": "color",
        "default": "uniform legal seed color",
        "valid": "1..3,5..9",
    },
    "scene_profile": {
        "type": "enum",
        "default": "alternating decoy/single lesson schedule",
        "valid": ["single", "decoy"],
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CANONICAL_SIZES = (3, 5, 9, 12)
_LEGAL_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
_DIFFICULTY_OPTIONS = {
    None: tuple(range(3, 19)),
    "easy": tuple(range(3, 19)) + tuple(range(3, 9)) * 3,
    "medium": tuple(range(3, 19)) + tuple(range(5, 15)) * 3,
    "hard": tuple(range(3, 19)) + tuple(range(10, 19)) * 3,
}
SCHEDULE_PROFILES = ("decoy_witness", "canonical_anchor")


def schedule_profile(seed, sample_index, difficulty=None):
    """Two-residue schedule: every length-four window has two witnesses."""
    del seed
    if difficulty not in _DIFFICULTY_OPTIONS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % 2]


def _validate_override_surface(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not 3 <= value <= 18:
            raise ValueError(f"{name}={value} outside [3, 18]")
    value = overrides.get("fg_color")
    if value is not None:
        if type(value) is not int:
            raise ValueError(f"fg_color must be an integer, not {type(value).__name__}")
        if value not in _LEGAL_COLORS:
            raise ValueError(f"fg_color={value} must be one of {_LEGAL_COLORS}")
    value = overrides.get("scene_profile")
    if value is not None:
        if type(value) is not str:
            raise ValueError(
                f"scene_profile must be a string, not {type(value).__name__}"
            )
        if value not in ("single", "decoy"):
            raise ValueError("scene_profile must be 'single' or 'decoy'")


def _draw_dimension(ctx, name, *, scheduled_size, difficulty, overridden):
    if overridden:
        return ctx.draw_int(name, 3, 18)
    if scheduled_size is not None:
        return ctx.draw_choice(name, (scheduled_size,))
    return ctx.draw_choice(name, _DIFFICULTY_OPTIONS[difficulty])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTY_OPTIONS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")
    _validate_override_surface(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_size = (
        _CANONICAL_SIZES[(sample_index // 2) % len(_CANONICAL_SIZES)]
        if profile == "canonical_anchor"
        else None
    )
    h = _draw_dimension(
        ctx,
        "grid_h",
        scheduled_size=scheduled_size,
        difficulty=difficulty,
        overridden=overrides.get("grid_h") is not None,
    )
    w = _draw_dimension(
        ctx,
        "grid_w",
        scheduled_size=scheduled_size,
        difficulty=difficulty,
        overridden=overrides.get("grid_w") is not None,
    )
    fg = ctx.draw_choice("fg_color", _LEGAL_COLORS)
    scheduled_scene = "decoy" if profile == "decoy_witness" else "single"
    scene = (
        ctx.draw_choice("scene_profile", ("single", "decoy"))
        if overrides.get("scene_profile") is not None
        else ctx.draw_choice("scene_profile", (scheduled_scene,))
    )

    grid = full_grid(h, w, 0)
    seed_candidates = [(r, c) for r in range(h - 1) for c in range(w)]
    seed_r, seed_c = ctx.draw_rng("seed_position").choice(seed_candidates)
    grid[seed_r][seed_c] = fg

    if scene == "decoy":
        flat_seed = seed_r * w + seed_c
        later = [divmod(index, w) for index in range(flat_seed + 1, h * w)]
        decoy_r, decoy_c = ctx.draw_rng("decoy_position").choice(later)
        decoy_color = ctx.draw_choice(
            "decoy_color", tuple(color for color in _LEGAL_COLORS if color != fg)
        )
        grid[decoy_r][decoy_c] = decoy_color
    return grid


def _shape_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "expected a nonempty rectangular grid"
    return None


def _nonzero_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the exact sampler manifold while accepting all canonical inputs."""
    del meta
    errors = []
    if difficulty not in _DIFFICULTY_OPTIONS:
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")
    shape = _shape_error(grid)
    if shape:
        return [shape, *errors]
    h, w = len(grid), len(grid[0])
    if not (3 <= h <= 18 and 3 <= w <= 18):
        errors.append("grid dimensions must each be in [3, 18]")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be literal ARC color integers 0..9")
        return errors
    cells = _nonzero_cells(grid)
    if len(cells) not in (1, 2):
        errors.append("expected exactly one seed or one seed plus one later decoy")
        return errors
    if any(value == 4 for _, _, value in cells):
        errors.append("color 4 is reserved for the output canopy")
    if cells[0][0] >= h - 1:
        errors.append("first nonzero seed must be above the bottom row")
    if len(cells) == 2 and cells[0][2] == cells[1][2]:
        errors.append("later decoy must use a color distinct from the seed")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    cells = _nonzero_cells(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "fg_color": cells[0][2],
        "scene_profile": "single" if len(cells) == 1 else "decoy",
    }


def _render_from_cell(grid, cell):
    """Executable rival support only; generated labels remain Racket-derived."""
    h, w = len(grid), len(grid[0])
    row, col, color = cell
    out = full_grid(h, w, 0)
    for r in range(row + 1):
        for c in range(col % 2, w, 2):
            out[r][c] = 4
    if row + 1 < h:
        out[row + 1][col] = color
    return out


def _last_nonzero_seed(grid):
    cells = _nonzero_cells(grid)
    if not cells:
        raise ValueError("last-nonzero rival requires a nonzero cell")
    return _render_from_cell(grid, cells[-1])


def _has_later_decoy(grid):
    try:
        return len(_nonzero_cells(grid)) == 2 and not self_check(grid)
    except Exception:
        return False


def lesson_identifiable(demos, query):
    """Return named surviving competitors; query is intentionally label-blind."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"{name} survives every demonstration")
    return reasons


SEMANTIC_WITNESSES = {"later_decoy": _has_later_decoy}
SEMANTIC_RIVALS = {"last_nonzero_seed": _last_nonzero_seed}
WITNESS_RIVALS = {"later_decoy": ["last_nonzero_seed"]}
CANONICAL_SHORTCUTS = {"last_nonzero_seed": _last_nonzero_seed}
LESSON_COMPETITORS = {"last_nonzero_seed": _last_nonzero_seed}
