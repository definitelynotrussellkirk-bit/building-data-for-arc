"""Input sampler for the k-step orbit rule, task 4b8e135e77e3.

The fixed Racket authority counts colour-1 markers in row 0, uses the unique
colour-9 cell as a rotation centre, and stamps every colour-2..8 shape cell at
the first K clockwise quarter-turns.  This module constructs only lawful inputs;
it does not generate labels.

The teaching schedule puts a scattered non-6 counterexample in every
consecutive two draws.  It refutes the canonical-fitting ``colour 6 only`` and
``leading prefix`` shortcuts, plus conditional variants that exploit a palette /
tally-layout correlation.

All six advertised controls are exact, jointly constructible, and recoverable
from the returned grid by :func:`observe_overrides`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b8e135e77e3"
TASK_ID = GENERATOR_ID
RULE_HASH = "a44e14a9fb6c"
VERSION = "3.0.0"
SUMMARY = (
    "Row 0 contains K colour-1 markers; one colour-9 anchor centres a 2..8 "
    "shape. The authority returns the union of the first K clockwise "
    "quarter-turns. Every two-draw window contains a scattered non-6 shape "
    "to refute prefix, colour-only, and cross-axis conditional shortcuts."
)

INVARIANTS = [
    "7..16 by 7..18 rectangular ARC grid with row 0 reserved for 1-markers",
    "1..4 colour-1 tally cells occur only in row 0; exactly one colour-9 anchor occurs below it",
    "2..8 shape cells use colours 2..8 and every quarter-turn remains in bounds",
    "one asymmetric witness offset has no rotated duplicate in the source shape",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical 7/9 anchors plus banded 7..16", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "canonical 7/9 anchors plus banded 7..18", "valid": "7..18"},
    "k_rot": {"type": "int", "default": "scheduled 2..4", "valid": "1..4"},
    "shape_size": {"type": "int", "default": "banded 2..8", "valid": "2..8"},
    "palette_kind": {"type": "enum", "default": "scheduled canonical/monochrome/multicolor", "valid": "canonical|monochrome|multicolor"},
    "tally_layout": {"type": "enum", "default": "scheduled prefix/scattered", "valid": "prefix|scattered"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_INT_DOMAINS = {
    "grid_h": (7, 16),
    "grid_w": (7, 18),
    "k_rot": (1, 4),
    "shape_size": (2, 8),
}
_ENUM_DOMAINS = {
    "palette_kind": ("canonical", "monochrome", "multicolor"),
    "tally_layout": ("prefix", "scattered"),
}
_ALLOWED_KEYS = frozenset(_INT_DOMAINS) | frozenset(_ENUM_DOMAINS)

# Rotations of (1, 0), except the source representative.  Excluding these from
# the source guarantees that every additional quarter contributes a fresh cell,
# even when the rest of a large shape contains rotationally related points.
_WITNESS_OFFSET = (1, 0)
_WITNESS_ROTATES = frozenset({(-1, 0), (0, 1), (0, -1)})

SCHEDULE_PROFILES = (
    "prefix_canonical",
    "scattered_monochrome",
    "prefix_multicolor",
    "scattered_multicolor",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Named semantic schedule; seed/difficulty do not alter its two-draw guarantee."""
    residue = sample_index % 4
    if residue == 0:
        return "prefix_canonical"
    if residue == 1:
        return "scattered_monochrome"
    if residue == 2:
        return "prefix_multicolor"
    return "scattered_multicolor"


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - _ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    for name, (lo, hi) in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} override must be an integer in {lo}..{hi}, got {value!r}")
    for name, domain in _ENUM_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str or value not in domain:
            raise ValueError(f"{name} override must be one of {domain}, got {value!r}")


def _band_ranges(difficulty):
    if difficulty == "easy":
        return {"h": (7, 10), "w": (7, 11), "k": (2, 3), "size": (2, 5)}
    if difficulty == "hard":
        return {"h": (9, 16), "w": (9, 18), "k": (3, 4), "size": (5, 8)}
    return {"h": (8, 13), "w": (8, 15), "k": (2, 4), "size": (3, 6)}


def _default_values(seed, sample_index, difficulty):
    """Derive defaults with keyed RNG, then feed them through exact GenCtx draws."""
    draft = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                    task_id=TASK_ID, difficulty=difficulty, overrides={})
    rng = draft.draw_rng("default_schedule")
    ranges = _band_ranges(difficulty)

    # Half the population is pinned to the two canonical dimensions.  The
    # remaining half spans difficulty bands, so canonical support is guaranteed
    # without collapsing size diversity.
    residue = sample_index % 4
    if residue == 0:
        h, w = 7, 7
    elif residue == 1:
        h, w = 9, 9
    else:
        h = rng.randint(*ranges["h"])
        w = rng.randint(*ranges["w"])

    k = 2 + (sample_index % 3)
    size = rng.randint(*ranges["size"])
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "prefix_canonical":
        palette_kind, tally_layout = "canonical", "prefix"
    elif profile == "scattered_monochrome":
        palette_kind, tally_layout = "monochrome", "scattered"
    elif profile == "prefix_multicolor":
        palette_kind, tally_layout = "multicolor", "prefix"
    else:
        palette_kind, tally_layout = "multicolor", "scattered"
    return {
        "grid_h": h,
        "grid_w": w,
        "k_rot": k,
        "shape_size": size,
        "palette_kind": palette_kind,
        "tally_layout": tally_layout,
    }


def _draw_axes(seed, sample_index, difficulty, overrides):
    defaults = _default_values(seed, sample_index, difficulty)
    effective = {**defaults, **{key: value for key, value in overrides.items() if value is not None}}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    values = {
        name: ctx.draw_int(name, lo, hi)
        for name, (lo, hi) in _INT_DOMAINS.items()
    }
    values.update({name: ctx.draw_choice(name, domain)
                   for name, domain in _ENUM_DOMAINS.items()})
    return ctx, values


def _tally_columns(width, k, layout, rng):
    if layout == "prefix":
        return list(range(k))
    # A non-prefix set guarantees the leading-prefix rival reads a smaller K.
    if k == 1:
        return [width - 1]
    choices = list(range(width))
    for _ in range(32):
        columns = sorted(rng.sample(choices, k))
        if columns != list(range(k)):
            return columns
    # Deterministic fallback (reachable only under an adversarial RNG stub).
    columns = list(range(k - 1)) + [width - 1]
    return sorted(set(columns))


def _shape_offsets(size, rng):
    candidates = [
        (dr, dc)
        for dr in range(-2, 3)
        for dc in range(-2, 3)
        if (dr, dc) != (0, 0)
        and (dr, dc) != _WITNESS_OFFSET
        and (dr, dc) not in _WITNESS_ROTATES
    ]
    chosen = [_WITNESS_OFFSET]
    chosen.extend(rng.sample(candidates, size - 1))
    return sorted(chosen)


def _shape_colors(offsets, palette_kind, rng):
    if palette_kind == "canonical":
        return [6] * len(offsets)
    non_six = [2, 3, 4, 5, 7, 8]
    primary = rng.choice(non_six)
    if palette_kind == "monochrome":
        return [primary] * len(offsets)
    secondary_choices = [value for value in range(2, 9) if value != primary]
    secondary = rng.choice(secondary_choices)
    colors = [primary if index % 2 == 0 else secondary for index in range(len(offsets))]
    # The designated witness offset must carry a non-6 color so color6_only is
    # guaranteed to disagree rather than relying on random overlap/collisions.
    witness_index = offsets.index(_WITNESS_OFFSET)
    colors[witness_index] = primary
    if len(set(colors)) < 2:  # defensive, though secondary is distinct
        colors[0] = secondary
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx, axes = _draw_axes(seed, sample_index, difficulty, overrides)
    h, w = axes["grid_h"], axes["grid_w"]
    k, size = axes["k_rot"], axes["shape_size"]
    layout_rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    for column in _tally_columns(w, k, axes["tally_layout"], layout_rng):
        grid[0][column] = 1

    # Radius two around this anchor lies below the tally row and inside all four
    # grid boundaries, including the minimum 7x7 canvas.
    anchor_r = layout_rng.randint(3, h - 3)
    anchor_c = layout_rng.randint(2, w - 3)
    grid[anchor_r][anchor_c] = 9

    offsets = _shape_offsets(size, layout_rng)
    colors = _shape_colors(offsets, axes["palette_kind"], layout_rng)
    for (dr, dc), color in zip(offsets, colors):
        grid[anchor_r + dr][anchor_c + dc] = color

    problems = self_check(grid)
    if problems:  # construction bug: fail loudly, never leak an invalid sample
        raise RuntimeError("constructed invalid orbit input: " + "; ".join(problems))
    return grid


def _grid_shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None, ["every row must be a list or tuple"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return None, ["grid must be nonempty and rectangular"]
    return (len(grid), next(iter(widths))), []


def _rotate(dr, dc, quarter):
    for _ in range(quarter):
        dr, dc = dc, -dr
    return dr, dc


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the exact generated domain while accepting all canonical inputs."""
    shape, problems = _grid_shape(grid)
    if problems:
        return problems
    h, w = shape
    if not 7 <= h <= 16:
        problems.append(f"grid height {h} outside 7..16")
    if not 7 <= w <= 18:
        problems.append(f"grid width {w} outside 7..18")

    bad_cells = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                bad_cells.append((r, c, value))
    if bad_cells:
        problems.append(f"grid contains non-ARC cells: {bad_cells[:3]}")
        return problems

    row0_ones = [c for c, value in enumerate(grid[0]) if value == 1]
    if not 1 <= len(row0_ones) <= 4:
        problems.append(f"row 0 must contain 1..4 colour-1 tally cells, found {len(row0_ones)}")
    if any(value not in (0, 1) for value in grid[0]):
        problems.append("row 0 is reserved for background and colour-1 tally cells")
    below_ones = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 1]
    if below_ones:
        problems.append(f"colour-1 tally cell occurs below row 0 at {below_ones[0]}")

    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        problems.append(f"expected exactly one colour-9 anchor, found {len(anchors)}")
        return problems
    anchor_r, anchor_c = anchors[0]
    if anchor_r == 0:
        problems.append("colour-9 anchor may not occupy the tally row")

    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if 2 <= value <= 8]
    if not 2 <= len(cells) <= 8:
        problems.append(f"expected 2..8 shape cells in colours 2..8, found {len(cells)}")
    if any(r == 0 for r, _, _ in cells):
        problems.append("shape cells may not occupy the tally row")

    for r, c, _ in cells:
        dr, dc = r - anchor_r, c - anchor_c
        if (dr, dc) == (0, 0):
            problems.append("shape cell overlaps the anchor")
            continue
        for quarter in range(4):
            rr_off, cc_off = _rotate(dr, dc, quarter)
            rr, cc = anchor_r + rr_off, anchor_c + cc_off
            if not (0 <= rr < h and 0 <= cc < w):
                problems.append(f"shape cell {(r, c)} clips at quarter {quarter}")
                break
            if rr == 0:
                problems.append(f"shape cell {(r, c)} rotates into the tally row")
                break
    return problems


def observe_overrides(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError("cannot observe invalid grid: " + "; ".join(problems))
    ones = [column for column, value in enumerate(grid[0]) if value == 1]
    colors = [value for row in grid for value in row if 2 <= value <= 8]
    palette = set(colors)
    palette_kind = ("canonical" if palette == {6} else
                    "monochrome" if len(palette) == 1 else "multicolor")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "k_rot": len(ones),
        "shape_size": len(colors),
        "palette_kind": palette_kind,
        "tally_layout": "prefix" if ones == list(range(len(ones))) else "scattered",
    }


def strict_canonical_like(grid):
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def _apply_rule(grid, *, tally_mode="count", shape_mode="all"):
    """Small task-local functions used only to define executable rivals."""
    h, w = len(grid), len(grid[0])
    anchor_r, anchor_c = next((r, c) for r, row in enumerate(grid)
                              for c, value in enumerate(row) if value == 9)
    if tally_mode == "prefix":
        k = 0
        for value in grid[0]:
            if value != 1:
                break
            k += 1
    else:
        k = sum(value == 1 for value in grid[0])
    allowed = {6} if shape_mode == "six_only" else set(range(2, 9))
    shape = [(r - anchor_r, c - anchor_c, value)
             for r, row in enumerate(grid) for c, value in enumerate(row)
             if value in allowed]
    out = full_grid(h, w, 0)
    out[anchor_r][anchor_c] = 9
    for quarter in range(k):
        for dr, dc, value in shape:
            rr_off, cc_off = _rotate(dr, dc, quarter)
            rr, cc = anchor_r + rr_off, anchor_c + cc_off
            if 0 <= rr < h and 0 <= cc < w and (rr, cc) != (anchor_r, anchor_c):
                out[rr][cc] = value
    return out


def _prefix_tally_only(grid):
    return _apply_rule(grid, tally_mode="prefix")


def _color6_only(grid):
    return _apply_rule(grid, shape_mode="six_only")


def _palette_gated_tally(grid):
    noncanonical = any(value not in (0, 1, 6, 9) for row in grid for value in row)
    return _apply_rule(grid, tally_mode="prefix" if noncanonical else "count")


def _layout_gated_shape(grid):
    columns = [column for column, value in enumerate(grid[0]) if value == 1]
    scattered = columns != list(range(len(columns)))
    return _apply_rule(grid, shape_mode="six_only" if scattered else "all")


def _has_scattered_tally(grid):
    columns = [column for column, value in enumerate(grid[0]) if value == 1]
    return bool(columns) and columns != list(range(len(columns)))


def _has_noncanonical_shape_color(grid):
    return any(value not in (0, 1, 6, 9) for row in grid for value in row)


def _has_joint_scattered_noncanonical(grid):
    return _has_scattered_tally(grid) and _has_noncanonical_shape_color(grid)


SEMANTIC_WITNESSES = {
    "scattered_tally": _has_scattered_tally,
    "noncanonical_shape_color": _has_noncanonical_shape_color,
    "joint_scattered_noncanonical": _has_joint_scattered_noncanonical,
}
SEMANTIC_RIVALS = {
    "prefix_tally_only": _prefix_tally_only,
    "color6_only": _color6_only,
    "palette_gated_tally": _palette_gated_tally,
    "layout_gated_shape": _layout_gated_shape,
}
WITNESS_RIVALS = {
    "scattered_tally": ["prefix_tally_only"],
    "noncanonical_shape_color": ["color6_only"],
    "joint_scattered_noncanonical": ["palette_gated_tally", "layout_gated_shape"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
