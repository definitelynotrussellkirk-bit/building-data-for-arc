"""Curriculum sampler for simultaneous 2x2 diagonal completion.

The selected Racket rule is the label authority.  This generator emits lawful
positive diagonal pairs together with three deliberately different near-misses:

* a same-colour diagonal with one opposite corner occupied;
* a diagonal whose two colours differ; and
* a same-colour orthogonal pair.

Those controls make the exact preconditions observable in every ordinary
example instead of teaching only the positive completion pattern.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b4d9320e0d9d"
TASK_ID = "b4d9320e0d9d"
RULE_HASH = "e1a9213544fb"
VERSION = "3.0.0"

SUMMARY = (
    "Complete a 2x2 square only when one diagonal contains the same nonzero "
    "colour and both opposite corners are empty; apply the symmetric main- "
    "and anti-diagonal cases simultaneously without overwriting occupied cells."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "0 is background and colours are integers 1..9",
    "every teaching grid has 2 or 3 legal diagonal pairs in distinct colours",
    "both diagonal orientations occur in every teaching grid",
    "every teaching grid also contains blocked-corner, mixed-colour, and orthogonal near-misses",
    "the authority reads the original input, so newly completed squares do not cascade",
]

AXES = {
    "grid_h": {"type": "int", "default": "four-slot curriculum", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "four-slot curriculum", "valid": "7..10"},
    "n_pairs": {"type": "int", "default": "four-slot curriculum", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "canonical_7x7_two_pairs",
    "canonical_8x8_two_pairs",
    "canonical_9x9_three_pairs",
    "wide_9x10_three_pairs",
)
_PROFILE_VALUES = (
    (7, 7, 2),
    (8, 8, 2),
    (9, 9, 3),
    (9, 10, 3),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """A four-slot cycle covers every exact axis endpoint at every band."""
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _profile_values(seed, sample_index):
    return _PROFILE_VALUES[(int(seed) + int(sample_index)) % len(_PROFILE_VALUES)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    bounds = {"grid_h": (7, 9), "grid_w": (7, 10), "n_pairs": (2, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = bounds[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool, float, or string)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override must be in [{lo}, {hi}]")


def _scheduled_int(ctx, label, scheduled, lo, hi, overrides):
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _clean_template(n_pairs, colors):
    """Canonical-scale scene containing only the legal diagonal pairs."""
    a, b = colors[0], colors[1]
    cells = {
        (0, 0): a,
        (1, 1): a,
        (4, 1): b,
        (5, 0): b,
    }
    if n_pairs == 3:
        c = colors[2]
        cells[(4, 5)] = c
        cells[(5, 6)] = c
    return cells, 6, 7


def _teaching_template(n_pairs, colors):
    """Return sparse cells in a 6x7 template with no accidental trigger.

    Slot geometry deliberately leaves a gap except between slots whose boundary
    colours are guaranteed distinct.  This gives a constructive joint override
    contract rather than relying on a rejection loop.
    """
    a, b = colors[0], colors[1]
    c = colors[2] if n_pairs == 3 else a
    blocker = colors[-1]
    cells = {
        # Legal main-diagonal pair.
        (0, 0): a,
        (1, 1): a,
        # Blocked same-colour main diagonal: one opposite corner is occupied.
        (0, 3): a,
        (1, 4): a,
        (0, 4): blocker,
        # Mixed-colour main diagonal.
        (0, 5): b,
        (1, 6): c,
        # Legal anti-diagonal pair.
        (4, 1): b,
        (5, 0): b,
        # Same-colour orthogonal pair.
        (4, 3): a,
        (4, 4): a,
    }
    if n_pairs == 3:
        # Third legal pair; its colour differs across the only touching slot edge.
        cells[(4, 5)] = c
        cells[(5, 6)] = c
    return cells, 6, 7


def _transform(cells, height, width, code):
    transformed = dict(cells)
    h, w = height, width
    if code & 1:
        transformed = {(c, r): value for (r, c), value in transformed.items()}
        h, w = w, h
    if code & 2:
        transformed = {(r, w - 1 - c): value for (r, c), value in transformed.items()}
    if code & 4:
        transformed = {(h - 1 - r, c): value for (r, c), value in transformed.items()}
    return transformed, h, w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled_h, scheduled_w, scheduled_pairs = _profile_values(seed, sample_index)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = _scheduled_int(ctx, "grid_h", scheduled_h, 7, 9, overrides)
    w = _scheduled_int(ctx, "grid_w", scheduled_w, 7, 10, overrides)
    n_pairs = _scheduled_int(ctx, "n_pairs", scheduled_pairs, 2, 3, overrides)

    rng = ctx.draw_rng(f"layout:{difficulty or 'unbanded'}")
    sparse_slot = int(sample_index) % 20 == 4
    colors = rng.sample(range(1, 10), n_pairs)
    if sparse_slot:
        cells, template_h, template_w = _clean_template(n_pairs, colors)
    else:
        cells, template_h, template_w = _teaching_template(n_pairs, colors)
    cells, template_h, template_w = _transform(
        cells, template_h, template_w, rng.randrange(8))
    row_offset = rng.randint(0, h - template_h)
    col_offset = rng.randint(0, w - template_w)

    grid = full_grid(h, w, 0)
    for (r, c), value in cells.items():
        grid[row_offset + r][col_offset + c] = value
    return grid


def _window_scan(grid):
    positives = []
    blocked = []
    mixed = []
    orthogonal = []
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                positives.append((r, c, a, "main"))
            if b != 0 and b == d and a == 0 and e == 0:
                positives.append((r, c, b, "anti"))

            if a != 0 and a == e and ((b == 0) != (d == 0)):
                blocked.append((r, c, "main"))
            if b != 0 and b == d and ((a == 0) != (e == 0)):
                blocked.append((r, c, "anti"))

            if a != 0 and e != 0 and a != e and b == 0 and d == 0:
                mixed.append((r, c, "main"))
            if b != 0 and d != 0 and b != d and a == 0 and e == 0:
                mixed.append((r, c, "anti"))

            nonzero = [((0, 0), a), ((0, 1), b), ((1, 0), d), ((1, 1), e)]
            occupied = [(point, value) for point, value in nonzero if value != 0]
            if len(occupied) == 2 and occupied[0][1] == occupied[1][1]:
                (r1, c1), _ = occupied[0]
                (r2, c2), _ = occupied[1]
                if abs(r1 - r2) + abs(c1 - c2) == 1:
                    orthogonal.append((r, c))
    return {
        "positives": positives,
        "blocked": blocked,
        "mixed": mixed,
        "orthogonal": orthogonal,
    }


def observe_overrides(grid):
    scan = _window_scan(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(scan["positives"]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer colours 0..9 (not bool or float)"]
    h, w = len(grid), width
    if not (7 <= h <= 9 and 7 <= w <= 10):
        return ["grid dimensions must be h=7..9 and w=7..10"]

    scan = _window_scan(grid)
    positives = scan["positives"]
    n_pairs = len(positives)
    errors = []
    if not 2 <= n_pairs <= 3:
        errors.append(f"expected 2..3 legal diagonal pairs, got {n_pairs}")
    colors = [entry[2] for entry in positives]
    if len(colors) != len(set(colors)):
        errors.append(f"legal diagonal-pair colours must be distinct: {colors}")

    nonzero_count = sum(value != 0 for row in grid for value in row)
    has_decoys = {
        "blocked": bool(scan["blocked"]),
        "mixed": bool(scan["mixed"]),
        "orthogonal": bool(scan["orthogonal"]),
    }
    clean_canonical = (
        nonzero_count == 2 * n_pairs
        and not any(has_decoys.values())
    )
    teaching = (
        nonzero_count == 2 * n_pairs + 7
        and all(has_decoys.values())
        and {entry[3] for entry in positives} == {"main", "anti"}
    )
    if not clean_canonical and not teaching:
        errors.append(
            "grid is neither a clean canonical pair scene nor the complete "
            "blocked/mixed/orthogonal teaching curriculum"
        )
    return errors


def strict_canonical_like(grid):
    """Task-local lawful-input predicate used by semantic/profile gates."""
    return self_check(grid)


def diagnostic_output(grid):
    """Pure diagnostic mirror; the selected Racket program remains authority."""
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                out[r][c + 1] = a
                out[r + 1][c] = a
            if b != 0 and b == d and a == 0 and e == 0:
                out[r][c] = b
                out[r + 1][c + 1] = b
    return out


def _partial_blocker_rival(grid):
    """Wrong: fill each empty opposite corner even if the other is occupied."""
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e:
                if b == 0:
                    out[r][c + 1] = a
                if d == 0:
                    out[r + 1][c] = a
            if b != 0 and b == d:
                if a == 0:
                    out[r][c] = b
                if e == 0:
                    out[r + 1][c + 1] = b
    return out


def _mixed_colour_rival(grid):
    """Wrong: diagonal occupancy is enough; equality of colours is ignored."""
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and e != 0 and b == 0 and d == 0:
                out[r][c + 1] = a
                out[r + 1][c] = a
            if b != 0 and d != 0 and a == 0 and e == 0:
                out[r][c] = b
                out[r + 1][c + 1] = b
    return out


def _orthogonal_pair_rival(grid):
    """Wrong: apply the true rule, then also complete orthogonal pairs."""
    out = diagnostic_output(grid)
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            occupied = [(rr, cc, grid[rr][cc]) for rr, cc in coords if grid[rr][cc] != 0]
            if len(occupied) != 2 or occupied[0][2] != occupied[1][2]:
                continue
            r1, c1, color = occupied[0]
            r2, c2, _ = occupied[1]
            if abs(r1 - r2) + abs(c1 - c2) != 1:
                continue
            for rr, cc in coords:
                if grid[rr][cc] == 0:
                    out[rr][cc] = color
    return out


def _main_only_rival(grid):
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                out[r][c + 1] = a
                out[r + 1][c] = a
    return out


def _anti_only_rival(grid):
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if b != 0 and b == d and a == 0 and e == 0:
                out[r][c] = b
                out[r + 1][c + 1] = b
    return out


def _has_blocked_corner(grid):
    return bool(_window_scan(grid)["blocked"])


def _has_mixed_diagonal(grid):
    return bool(_window_scan(grid)["mixed"])


def _has_orthogonal_pair(grid):
    return bool(_window_scan(grid)["orthogonal"])


def _has_both_orientations(grid):
    return {entry[3] for entry in _window_scan(grid)["positives"]} == {"main", "anti"}


SEMANTIC_WITNESSES = {
    "occupied_opposite_corner": _has_blocked_corner,
    "mixed_colour_diagonal": _has_mixed_diagonal,
    "orthogonal_pair": _has_orthogonal_pair,
    "both_diagonal_orientations": _has_both_orientations,
}
SEMANTIC_RIVALS = {
    "fill_with_one_empty_corner": _partial_blocker_rival,
    "ignore_diagonal_colour_equality": _mixed_colour_rival,
    "complete_orthogonal_pair": _orthogonal_pair_rival,
    "main_diagonal_only": _main_only_rival,
    "anti_diagonal_only": _anti_only_rival,
}
WITNESS_RIVALS = {
    "occupied_opposite_corner": ["fill_with_one_empty_corner"],
    "mixed_colour_diagonal": ["ignore_diagonal_colour_equality"],
    "orthogonal_pair": ["complete_orthogonal_pair"],
    "both_diagonal_orientations": ["main_diagonal_only", "anti_diagonal_only"],
}
# The first three rules fit all selected canonical pairs, which contain only
# positive examples. Generated near-misses are therefore necessary evidence.
CANONICAL_SHORTCUTS = {
    "fill_with_one_empty_corner": _partial_blocker_rival,
    "ignore_diagonal_colour_equality": _mixed_colour_rival,
    "complete_orthogonal_pair": _orthogonal_pair_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Return named surviving competitors; [] means demos identify the query."""
    survivors = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    if survivors:
        return ["competitors fit every demonstration: " + ", ".join(survivors)]
    return []
