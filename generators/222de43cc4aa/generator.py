"""Generator for puzzle eb281b96.

Rule: vertical pingpong extension. Output height = 4*(h-1)+1 (two full
zigzag periods of 2*(h-1)). Output row i copies input row k, where
pos = i mod 2*(h-1) and k = pos if pos <= h-1 else 2*(h-1) - pos.

The v2.x distribution emitted dense multi-color texture fills — wrong
background prior (canonical modal color is 0), far too few objects
(~3 vs ~17 isolated marks), no self_check, and no RULE_HASH pin. The
canonical inputs (both rows: training + augmented) are DOTTED LATTICES:
sparse single-color marks on a 0 background, each row a short-period
pattern (top/bottom rows period 4, middle rows period 2), width 17,
height 3-5.

v3.0.0 rebuilds the distribution on that structure: 0-background grids
with 1-2 foreground colors, every row a short-period (2-4) dotted
pattern of isolated single-cell or domino marks, vertically asymmetric
so the pingpong is visible. Adds a structural self_check (with the
declared degenerate modes accepted as edge-but-valid), an
observe_overrides hook, and pins RULE_HASH to the canonical rule.

v3.1.0 (KRF-0003): 30% of default draws reproduce the exact canonical
lattice (h 3-5, w 17, one color, official phase profile), so the joint
canonical-like rate is substantial (>= 25% pooled) while the remaining
draws explore the wider lawful family. Overrides that disagree with
the profile skip the prior, staying exact-or-loud.

Combinatorial axes: grid_h, grid_w, n_fg_colors, per-row
period/phase/mark-width, fg colors, texture family, canonical prior.
Degenerates: ud_symmetric, monochrome, single_row (all rule-valid:
the pingpong still runs, the output just degenerates to tiling).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "222de43cc4aa"
RULE_HASH = "ce9518b81cf8"  # canonical rule this generator was written against
VERSION = "3.1.1"  # KRF-0004: canonical-prior returns now record final grid_h/w/n_fg via pinned typed draws (byte-identical grids). KRF-0005: self_check rejects all-background, validates the ud_symmetric/single_row dotted-row grammars (modal-0, every row marked, short mark-period), and the ud_symmetric/single_row builders keep periods >=3 so their own controls stay 0-modal.
TASK_ID = "222de43cc4aa"
SUMMARY = (
    "0-background grid (h in [3, 8], w in [9, 21]) holding a DOTTED "
    "LATTICE: 1-2 foreground colors, and every row a short-period "
    "(2-4) pattern of isolated marks — single cells, sometimes domino "
    "clusters — so the grid holds many small objects (~12-35) like the "
    "canonical dotted rows (width 17, period-2 middle rows, period-4 "
    "top/bottom rows). The grid is NOT vertically symmetric, so the "
    "reflection is visible. Rule (VERTICAL PINGPONG / ZIGZAG "
    "EXTENSION): output height = 4*(h-1)+1 covering TWO full pingpong "
    "periods of 2*(h-1); output width = input width. For each output "
    "row i: pos = i mod (2*(h-1)); if pos <= h-1 the source row is "
    "input row pos, else it is input row 2*(h-1)-pos (reflection). "
    "Net: the input zigzags up-down vertically through two full "
    "reflection cycles."
)

INVARIANTS = [
    "background is modal color 0; foreground is 1-2 colors of sparse dotted marks",
    "input height in [3, 8] (rule needs h>=2; output height 4*(h-1)+1 stays <= 29), width in [9, 21]",
    "every row carries at least one foreground mark and follows a short-period (<=5) pattern",
    "normal draws are not vertically symmetric (top row differs from bottom row)",
    "declared degenerate modes (ud_symmetric, monochrome, single_row) are edge-but-valid: the pingpong rule still runs",
]

HELPFUL_TEXTURES = ("lattice", "clusters", "tight_rows")
DEGENERATE_TEXTURES = ("ud_symmetric", "monochrome", "single_row")

AXES = {
    "grid_h":      {"type": "int", "default": "difficulty-skewed 3..8 (easy low, hard high)", "valid": "3..8"},
    "grid_w":      {"type": "int", "default": "difficulty-skewed 9..21", "valid": "9..21"},
    "n_fg_colors": {"type": "int", "default": "1 easy / 1-2 med / 2 hard", "valid": "1..2"},
    "texture":     {"type": "str", "default": "none",
                    "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


# ---------------------------------------------------------------------------
# Dotted-lattice construction
# ---------------------------------------------------------------------------

def _row_cells(w, phase, mark_w, step):
    """Columns of one dotted row: marks of width mark_w on a period-`step`
    residue lattice ((c - phase) mod step < mark_w). Exact period `step`
    across the whole row, no partial marks at the edges."""
    return [c for c in range(w) if (c - phase) % step < mark_w]


def _is_ud_sym(g):
    h = len(g)
    w = len(g[0])
    return all(g[r][c] == g[h - 1 - r][c] for r in range(h) for c in range(w))


def _repair_bottom_row(g, color, budget):
    """Rebuild the bottom row as an exact-period dotted lattice so it differs
    from the top row, the grid keeps >= 2 distinct rows, no vertical symmetry
    remains, and the density budget still holds."""
    h, w = len(g), len(g[0])
    total = sum(1 for row in g for v in row if v)
    cur = sum(1 for v in g[h - 1] if v)
    for step in (4, 3, 2, 5):
        for phase in range(step - 1, -1, -1):
            cells = _row_cells(w, phase, 1, step)
            if total - cur + len(cells) > budget:
                continue
            row = [0] * w
            for c in cells:
                row[c] = color
            if row == list(g[0]):
                continue
            trial = [list(r) for r in g[: h - 1]] + [row]
            if not _is_ud_sym(trial) and len({tuple(r) for r in trial}) >= 2:
                return trial
    return None


def _row_period(row, max_p=5):
    """Smallest period p <= max_p exactly repeating across the row, else w."""
    w = len(row)
    for p in range(1, max_p + 1):
        if all(row[c] == row[c + p] for c in range(w - p)):
            return p
    return w


def _mark_period(row, max_p=5):
    """Smallest period p <= max_p of the BINARY mark lattice (nonzero
    positions), else w.  The degenerate dotted-row grammars are about mark
    positions; color assignment may cycle independently."""
    w = len(row)
    for p in range(1, max_p + 1):
        if all((row[c] != 0) == (row[c + p] != 0) for c in range(w - p)):
            return p
    return w


def _lattice_row_params(tex, rng, shared_period):
    if tex == "lattice":
        mw = 1
    elif tex == "clusters":
        mw = rng.choice((1, 2))
    else:
        mw = rng.choice((1, 1, 1, 2))
    if tex == "tight_rows" and shared_period is not None:
        period = shared_period
    else:
        period = rng.choice((2, 3, 4))
    step = period if mw == 1 else max(4, mw + 2)
    phase = rng.randrange(step - mw + 1)
    return period, step, phase, mw


def _build_lattice(tex, h, w, fg, rng):
    # Density budget: foreground marks stay strictly below half the cells so
    # color 0 is always the unique modal color (the canonical background prior).
    budget = (w * h + 1) // 2 - 1
    for _full in range(6):
        g = full_grid(h, w, 0)
        total = 0
        shared_period = None
        ok = True
        for r in range(h):
            row_cap = budget - total - (h - 1 - r)  # keep >= 1 mark per later row
            cells = None
            for _try in range(8):
                period, step, phase, mw = _lattice_row_params(tex, rng, shared_period)
                cand = _row_cells(w, phase, mw, step)
                if len(cand) <= row_cap:
                    cells = cand
                    break
            if cells is None:
                ok = False
                break
            if r == 0:
                shared_period = period
            color = fg[0] if len(fg) == 1 or r in (0, h - 1) else fg[1]
            for c in cells:
                g[r][c] = color
            total += len(cells)
        if not ok:
            continue
        # Guarantee the pingpong is visible: bottom row differs from top row,
        # at least two distinct rows, and no full vertical symmetry.
        if (list(g[0]) == list(g[-1])
                or len({tuple(row) for row in g}) < 2
                or _is_ud_sym(g)):
            g2 = _repair_bottom_row(g, fg[0], budget)
            if g2 is not None:
                g = g2
        if (list(g[0]) != list(g[-1])
                and len({tuple(row) for row in g}) >= 2
                and not _is_ud_sym(g)):
            return g
    raise RuntimeError(f"{TASK_ID}: could not build a sparse dotted lattice")


def _draw_degenerate(tex, h, w, fg, rng):
    """Edge-but-valid modes: the pingpong rule still runs (its output just
    degenerates to plain tiling or a solid extension), so self_check
    accepts them as lawful edge cases."""
    if tex == "ud_symmetric":
        # Mirrored dotted rows; periods are kept sparse (>=3) so background
        # 0 stays the unique modal color (the declared grammar).
        g = full_grid(h, w, 0)
        half = (h + 1) // 2
        for r in range(half):
            period = rng.choice((3, 4))
            phase = rng.randrange(period)
            color = fg[r % len(fg)]
            for c in _row_cells(w, phase, 1, period):
                g[r][c] = color
        for r in range(half, h):
            g[r] = list(g[h - 1 - r])
        return g
    if tex == "monochrome":
        return full_grid(h, w, fg[0])
    if tex == "single_row":
        # One sparse short-period dotted row repeated; periods >=3 keep
        # background 0 unique-modal (the declared grammar).
        period = rng.choice((3, 4))
        phase = rng.randrange(period)
        row = [0] * w
        for i, c in enumerate(_row_cells(w, phase, 1, period)):
            row[c] = fg[i % len(fg)]
        return [list(row) for _ in range(h)]
    return full_grid(h, w, 0)


def _build_canonical_lattice(h, fg):
    """The exact official canonical profile: width 17, one foreground color,
    top row period-4 phase-2, middle rows period-2 phase-1, bottom row
    period-4 phase-0 (the dotted weave of every canonical train/test input)."""
    g = full_grid(h, 17, 0)
    for r in range(h):
        if r == 0:
            period, phase = 4, 2
        elif r == h - 1:
            period, phase = 4, 0
        else:
            period, phase = 2, 1
        for c in _row_cells(17, phase, 1, period):
            g[r][c] = fg[0]
    return g


# Default draws reproduce the canonical lattice (h 3-5, w 17, one color,
# official phase profile) with this probability; the remaining draws explore
# the wider lawful family (KRF-0003: substantial canonical prior >= 25%
# pooled, generalization augments rather than replaces the task manifold).
_CANONICAL_PRIOR_PROB = 0.30


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    tex = overrides.get("texture")
    if tex is not None and tex not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(
            f"texture must be one of {HELPFUL_TEXTURES + DEGENERATE_TEXTURES}, "
            f"got {tex!r}"
        )
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout" if tex is None else f"layout:{tex}")
    # Full declared ranges; difficulty only skews the free draws, so every
    # single-axis boundary override is accepted exactly on every band.
    h = ctx.draw_int_diff("grid_h", 3, 8)
    w = ctx.draw_int_diff("grid_w", 9, 21)
    n_fg = ctx.draw_int_diff("n_fg_colors", 1, 2)
    fg = list(ctx.draw_distinct_colors("fg_colors", n=n_fg, exclude={0}))
    if tex in DEGENERATE_TEXTURES:
        honored = {"texture", "grid_h", "grid_w", "n_fg_colors"}
        extra = sorted(k for k, v in overrides.items()
                       if v is not None and k not in honored)
        if extra:
            raise ValueError(f"texture={tex} does not honor overrides {extra}")
        if tex == "monochrome" and overrides.get("n_fg_colors") not in (None, 1):
            raise ValueError("texture=monochrome is single-color: n_fg_colors=2 is meaningless")
        return _draw_degenerate(tex, h, w, fg, rng)
    # Canonical-lattice prior: only when every overridden axis already agrees
    # with the official profile (overrides stay exact-or-loud).
    if (tex is None
            and rng.random() < _CANONICAL_PRIOR_PROB
            and (overrides.get("grid_h") is None or 3 <= h <= 5)
            and (overrides.get("grid_w") is None or w == 17)
            and overrides.get("n_fg_colors") in (None, 1)):
        hc = h if 3 <= h <= 5 else rng.randint(3, 5)
        # KRF-0004 provenance: record the final canonical-lattice values
        # under their declared axis labels before returning (pinned typed
        # draws; the returned grid is unchanged by these records).
        ctx.draw_int("grid_h", hc, hc)
        ctx.draw_int("grid_w", 17, 17)
        ctx.draw_int("n_fg_colors", 1, 1)
        return _build_canonical_lattice(hc, fg[:1])
    return _build_lattice(tex, h, w, fg, rng)


# ---------------------------------------------------------------------------
# Contract hooks
# ---------------------------------------------------------------------------

def observe_overrides(grid) -> dict:
    """Report the realized per-draw values of the exact semantic axes.

    grid_h/grid_w are the input dimensions (the rule's output height is
    derived from grid_h); n_fg_colors counts the distinct foreground
    (non-zero) colors, which construction guarantees all appear."""
    out: dict = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return out
    out["grid_h"] = len(grid)
    out["grid_w"] = len(grid[0])
    out["n_fg_colors"] = len({v for row in grid for v in row if v != 0})
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants for the dotted-lattice pingpong inputs.

    The declared degenerate modes are lawful edge cases (the rule still
    runs on them): monochrome (single color), single_row (all rows
    identical), ud_symmetric (vertically mirrored). Normal draws must
    have a modal-0 background, short-period dotted rows, at least one
    mark per row, and no vertical symmetry. Always rejects grids whose
    height the rule cannot handle (h < 2 divides by zero; h > 8
    overflows the 30-row ARC limit on output)."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (3 <= h <= 8):
        errors.append(f"input height {h} outside declared envelope 3..8")
    if not (9 <= w <= 21):
        errors.append(f"input width {w} outside declared envelope 9..21")
    colors = sorted({v for row in grid for v in row})
    if any(not isinstance(v, int) or v < 0 or v > 9 for v in colors):
        errors.append(f"colors outside 0..9: {colors}")
    if len(colors) <= 1:
        # The declared monochrome degenerate mode is a full NONZERO grid;
        # an all-background (all-0) grid is a no-op impostor, not that
        # mode (KRF-0005 narrowing).
        if not any(v for row in grid for v in row):
            errors.append("all-background grid: the monochrome degenerate "
                          "mode is a full nonzero grid, never all-zero")
        return errors
    counts = {v: sum(row.count(v) for row in grid) for v in colors}
    zero_modal = counts.get(0, 0) > max(
        (v for k, v in counts.items() if k != 0), default=0)
    if all(list(row) == list(grid[0]) for row in grid):
        # single_row grammar: ONE sparse (0-modal) short-period dotted row
        # repeated - nothing else.
        if not any(grid[0]):
            errors.append("single_row mode requires a marked row")
        elif not zero_modal:
            errors.append("single_row mode requires a sparse (0-modal) row")
        elif _mark_period(grid[0]) > 5:
            errors.append("single_row row is not a short-period dotted "
                          "pattern")
        return errors
    if _is_ud_sym(grid):
        # ud_symmetric grammar: vertically mirrored rows that are EACH
        # short-period dotted rows carrying marks (no empty row), on a
        # modal-zero background; a lone center-row singleton or short
        # line is not this branch (KRF-0005 narrowing).
        if not zero_modal:
            errors.append("ud_symmetric mode requires background 0 to be "
                          "the unique modal color")
        for r in range(h):
            if not any(grid[r]):
                errors.append(
                    f"ud_symmetric row {r} has no foreground mark")
            elif _mark_period(grid[r]) > 5:
                errors.append(
                    f"ud_symmetric row {r} is not a short-period dotted "
                    f"pattern")
        return errors
    # --- normal dotted-lattice mode --------------------------------------
    if counts.get(0, 0) <= max((v for k, v in counts.items() if k != 0), default=0):
        errors.append("background color 0 must be the unique modal color")
    if list(grid[0]) == list(grid[-1]):
        errors.append("top and bottom rows must differ (pingpong would be invisible)")
    for r in range(h):
        if not any(grid[r]):
            errors.append(f"row {r} has no foreground mark")
        elif _row_period(grid[r]) > 5:
            errors.append(f"row {r} is not a short-period dotted pattern")
    return errors
