"""Generator for 01bdf9b8d2db — fill each wall-bounded chamber from its seed.

Color 5 is an impermeable wall.  Every 4-connected non-5 region contains
exactly one nonzero seed; the selected Racket authority paints that entire
region with the seed color while preserving walls.  Divider gaps are scheduled
counterexamples to the tempting but wrong "fill independent rectangles" rule.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01bdf9b8d2db"
TASK_ID = GENERATOR_ID
RULE_HASH = "816bf3c1378a"
VERSION = "3.0.0"
SUMMARY = (
    "Color-5 perimeter and divider walls partition the input into chambers. "
    "Every 4-connected non-wall chamber has exactly one colored seed, and the "
    "output floods the whole chamber with that seed color. Scheduled divider "
    "gaps merge neighboring rectangles and make connectivity observable."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the outer border and every uncarved divider cell are color 5",
    "1..3 vertical and 0..2 horizontal dividers are spaced by at least one cell",
    "0..2 observable divider gaps may merge rectangular compartments",
    "every 4-connected non-5 chamber contains exactly one non-{0,5} seed",
    "seed colors may repeat across different chambers, as in the canonical test",
]

AXES = {
    "grid_h": {
        "type": "int", "default": "canonical-profile schedule", "valid": "7..10",
        "doc": "Grid height; the range is the canonical height envelope.",
    },
    "grid_w": {
        "type": "int", "default": "canonical-profile schedule", "valid": "10..13",
        "doc": "Grid width; the range is the canonical width envelope.",
    },
    "n_vdivs": {
        "type": "int", "default": "canonical-profile schedule", "valid": "1..3",
        "doc": "Exact number of vertical divider lines.",
    },
    "n_hdivs": {
        "type": "int", "default": "canonical-profile schedule", "valid": "0..2",
        "doc": "Exact number of horizontal divider lines.",
    },
    "n_gaps": {
        "type": "int", "default": "0, with one scheduled gapped demo per 3", "valid": "0..2",
        "doc": "Exact number of non-crossing cells carved from divider lines.",
    },
}
# Every combination in the advertised Cartesian domain is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# (name, height, width, vertical dividers, horizontal dividers,
#  distinct seed colors on a plain board).  These are abstractions of the five
# canonical input profiles, not stored puzzle grids or coordinate templates.
_PROFILES = {
    "p8x10_4": (8, 10, 1, 1, 4),
    "p9x11_6": (9, 11, 2, 1, 6),
    "p10x10_6": (10, 10, 1, 2, 6),
    "p7x13_6": (7, 13, 2, 1, 6),
    "p9x13_9": (9, 13, 2, 2, 7),
}
_PROFILE_BANDS = {
    "easy": ("p8x10_4", "p8x10_4", "p7x13_6"),
    "medium": ("p9x11_6", "p10x10_6", "p7x13_6"),
    "hard": ("p9x13_9", "p9x13_9", "p9x11_6", "p10x10_6"),
    None: tuple(_PROFILES),
}
_MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

# Every consecutive three sample indexes contain a decisive gap example.  The
# lesson builder uses consecutive indexes inside each training episode.
SCHEDULE_PROFILES = ("plain", "gapped")


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return "gapped" if int(sample_index) % 3 == 1 else "plain"


def _regions(grid):
    """Return all 4-connected non-5 regions in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 5 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _axis_int(ctx, overrides, name, lo, hi, default):
    """Draw a full-domain override or record the scheduled default exactly."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _spaced_positions(ctx, label, start, stop, count):
    """Choose exactly count positions from range(start, stop), spacing >= 2."""
    choices = [
        option for option in combinations(range(start, stop), count)
        if all(b - a >= 2 for a, b in zip(option, option[1:]))
    ]
    if not choices:
        raise ValueError(
            f"cannot place {count} spaced dividers in coordinates {start}..{stop - 1}"
        )
    return list(ctx.draw_rng(label).choice(choices))


def _divider_positions(grid):
    """Recover divider rows/columns even when up to two cells are carved."""
    h, w = len(grid), len(grid[0])
    h_divs = [
        r for r in range(1, h - 1)
        if sum(grid[r][c] == 5 for c in range(w)) >= w - 2
    ]
    v_divs = [
        c for c in range(1, w - 1)
        if sum(grid[r][c] == 5 for r in range(h)) >= h - 2
    ]
    return h_divs, v_divs


def observe_overrides(grid):
    """Recover every exact public axis from returned pixels."""
    h, w = len(grid), len(grid[0])
    h_divs, v_divs = _divider_positions(grid)
    gaps = 0
    h_set, v_set = set(h_divs), set(v_divs)
    for c in v_divs:
        gaps += sum(grid[r][c] != 5 for r in range(1, h - 1) if r not in h_set)
    for r in h_divs:
        gaps += sum(grid[r][c] != 5 for c in range(1, w - 1) if c not in v_set)
    return {
        "grid_h": h,
        "grid_w": w,
        "n_vdivs": len(v_divs),
        "n_hdivs": len(h_divs),
        "n_gaps": gaps,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    profile_names = _PROFILE_BANDS.get(difficulty, _PROFILE_BANDS[None])
    profile_name = ctx.draw_choice("curriculum_profile", profile_names)
    ph, pw, pv, pr, target_distinct = _PROFILES[profile_name]

    h = _axis_int(ctx, overrides, "grid_h", 7, 10, ph)
    w = _axis_int(ctx, overrides, "grid_w", 10, 13, pw)
    n_v = _axis_int(ctx, overrides, "n_vdivs", 1, 3, pv)
    n_h = _axis_int(ctx, overrides, "n_hdivs", 0, 2, pr)
    default_gaps = 0
    if schedule_profile(seed, sample_index, difficulty) == "gapped":
        default_gaps = 1 + ctx.draw_rng("gap_count_schedule").randrange(2)
    n_gaps = _axis_int(ctx, overrides, "n_gaps", 0, 2, default_gaps)

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = 5
        grid[h - 1][c] = 5
    for r in range(h):
        grid[r][0] = 5
        grid[r][w - 1] = 5

    v_divs = _spaced_positions(ctx, "vertical_dividers", 2, w - 2, n_v)
    h_divs = _spaced_positions(ctx, "horizontal_dividers", 2, h - 2, n_h)
    for c in v_divs:
        for r in range(h):
            grid[r][c] = 5
    for r in h_divs:
        for c in range(w):
            grid[r][c] = 5

    # Intersections remain walls, so each advertised gap independently opens
    # one divider and is exactly recoverable from pixels.
    crossings = {(r, c) for r in h_divs for c in v_divs}
    gap_candidates = [
        (r, c) for c in v_divs for r in range(1, h - 1)
        if (r, c) not in crossings
    ] + [
        (r, c) for r in h_divs for c in range(1, w - 1)
        if (r, c) not in crossings
    ]
    if n_gaps > len(gap_candidates):
        raise ValueError(
            f"n_gaps={n_gaps} exceeds {len(gap_candidates)} realizable divider cells"
        )
    for r, c in ctx.draw_rng("divider_gaps").sample(gap_candidates, n_gaps):
        grid[r][c] = 0

    chambers = _regions(grid)
    marker_rng = ctx.draw_rng("chamber_markers")
    marker_rng.shuffle(chambers)
    structural_defaults = (h, w, n_v, n_h) == (ph, pw, pv, pr)
    distinct = min(
        len(chambers),
        target_distinct if structural_defaults else len(_MARKER_COLORS),
    )
    colors = marker_rng.sample(_MARKER_COLORS, distinct)
    assignments = [colors[index % distinct] for index in range(len(chambers))]
    marker_rng.shuffle(assignments)
    for cells, color in zip(chambers, assignments):
        r, c = marker_rng.choice(cells)
        grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (not isinstance(grid, (list, tuple)) or not grid or
            not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    h, w = len(grid), len(grid[0])
    errors = []
    if not 7 <= h <= 10:
        errors.append(f"grid height {h} outside 7..10")
    if not 10 <= w <= 13:
        errors.append(f"grid width {w} outside 10..13")
    if not (
        all(grid[0][c] == 5 and grid[h - 1][c] == 5 for c in range(w)) and
        all(grid[r][0] == 5 and grid[r][w - 1] == 5 for r in range(h))
    ):
        errors.append("outer border must be entirely color 5")

    h_divs, v_divs = _divider_positions(grid)
    if not 1 <= len(v_divs) <= 3:
        errors.append(f"expected 1..3 vertical dividers, found {len(v_divs)}")
    if not 0 <= len(h_divs) <= 2:
        errors.append(f"expected 0..2 horizontal dividers, found {len(h_divs)}")
    if any(c < 2 or c > w - 3 for c in v_divs) or any(
        b - a < 2 for a, b in zip(v_divs, v_divs[1:])
    ):
        errors.append("vertical dividers must be interior and spaced by at least one column")
    if any(r < 2 or r > h - 3 for r in h_divs) or any(
        b - a < 2 for a, b in zip(h_divs, h_divs[1:])
    ):
        errors.append("horizontal dividers must be interior and spaced by at least one row")

    h_set, v_set = set(h_divs), set(v_divs)
    stray = [
        (r, c) for r in range(1, h - 1) for c in range(1, w - 1)
        if grid[r][c] == 5 and r not in h_set and c not in v_set
    ]
    if stray:
        errors.append(f"found {len(stray)} stray interior wall cell(s)")
    try:
        observed_gaps = observe_overrides(grid)["n_gaps"]
    except Exception as exc:  # defensive: validators return reasons, not raises
        errors.append(f"could not recover divider gaps: {exc}")
        observed_gaps = -1
    if not 0 <= observed_gaps <= 2:
        errors.append(f"expected 0..2 divider gaps, found {observed_gaps}")

    for index, region in enumerate(_regions(grid)):
        markers = [grid[r][c] for r, c in region if grid[r][c] not in (0, 5)]
        if len(markers) != 1:
            errors.append(
                f"chamber {index} must contain exactly one marker; found {len(markers)}"
            )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _rectangle_partition_rival(grid):
    """Wrong rival: fills rectangular compartments and treats gaps as walls."""
    h, w = len(grid), len(grid[0])
    h_divs, v_divs = _divider_positions(grid)
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    row_bounds = [0, *h_divs, h - 1]
    col_bounds = [0, *v_divs, w - 1]
    for top, bottom in zip(row_bounds, row_bounds[1:]):
        for left, right in zip(col_bounds, col_bounds[1:]):
            cells = [
                (r, c) for r in range(top + 1, bottom)
                for c in range(left + 1, right) if grid[r][c] != 5
            ]
            marker = next(
                (grid[r][c] for r, c in cells if grid[r][c] not in (0, 5)),
                0,
            )
            for r, c in cells:
                out[r][c] = marker
    return out


def _has_divider_gap(grid):
    try:
        return observe_overrides(grid)["n_gaps"] > 0
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "divider_gap_requires_connectivity": _has_divider_gap,
}
SEMANTIC_RIVALS = {
    "independent_rectangles": _rectangle_partition_rival,
}
WITNESS_RIVALS = {
    "divider_gap_requires_connectivity": ["independent_rectangles"],
}
CANONICAL_SHORTCUTS = {
    "independent_rectangles": _rectangle_partition_rival,
}
LESSON_COMPETITORS = {
    "independent_rectangles": _rectangle_partition_rival,
}


def lesson_identifiable(demos, query):
    del query
    survivors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    if survivors:
        return [
            "demos do not refute declared competitor(s): " + ", ".join(sorted(survivors))
        ]
    return []
