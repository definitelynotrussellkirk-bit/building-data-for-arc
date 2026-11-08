"""Generator for arc_additional_puzzle_bank_volume13:E87.

Rule: a 0-cell becomes 7 iff BOTH its horizontal neighbors are 6, or
BOTH its vertical neighbors are 6. Non-zero cells never convert; gaps
wider than 1 don't fill; reads the input (no cascade).

Combinatorial axes: grid_h/w, n_gaps, texture
(plain|wide_gap|filled_gap|cross|seven_decoy).
Degenerates: no_gaps (scatter without any sandwich -> identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a0dded71c43"
VERSION = "2.4.0"  # exact observable axes; pin canonical rule
TASK_ID = "0a0dded71c43"
RULE_HASH = "c9b982c51cbf"
SUMMARY = (
    "Scattered 6s with one-cell gaps fill orange. wide_gap boards "
    "show 6-0-0-6 spans that DON'T fill; filled_gap boards put a "
    "non-zero cell between 6s (stays); cross boards fill one cell "
    "from both directions and chain 6-0-6-0-6; seven_decoy boards "
    "carry pre-existing 7s (7-0-7 does NOT fill - only 6 endpoints "
    "count). Decoy color blocks survive. (Was: clean isolated pairs "
    "only - every near-miss was absent and degenerates frozen.)"
)

# Rivals: 'fill any span between 6s' refuted by wide_gap. 'sandwiched
# cells recolor' refuted by filled_gap (non-zero stays). 'any color
# pair sandwiches' refuted by seven_decoy. 3-4 demos incl. >=1
# near-miss board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 actual one-cell 6-gap on every non-degenerate board",
    "wide_gap boards: >=1 6-00-6 span left unfilled",
    "filled_gap boards: >=1 non-zero cell between two 6s, unchanged",
]

DEGENERATE_TEXTURES = ("no_gaps",)
HELPFUL_TEXTURES = ("plain", "wide_gap", "filled_gap", "cross",
                    "seven_decoy")

AXES = {
    "grid_h":  {"type": "int", "default": "difficulty-skewed 8..18", "valid": "8..18"},
    "grid_w":  {"type": "int", "default": "difficulty-skewed 8..18", "valid": "8..18"},
    "n_gaps":  {"type": "int", "default": "difficulty-skewed 1..6", "valid": "1..6"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|wide_gap|filled_gap|cross|seven_decoy|"
                         "no_gaps",
                "doc": "wide_gap: 2-cell gaps stay; filled_gap: occupied "
                       "gap stays; cross: plus of 6s fills center from "
                       "both axes + 6-0-6-0-6 chain; seven_decoy: input "
                       "7s present, 7-endpoints don't sandwich."},
}

# A no-gap identity scene cannot simultaneously realize a positive exact
# n_gaps request.  The override checker recognizes this value-specific
# incompatibility rather than treating the explicit rejection as a fallback.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "no_gaps", "n_gaps": None},
]


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0:
                continue
            if (0 < c < w - 1 and g[r][c - 1] == 6 and g[r][c + 1] == 6) or \
               (0 < r < h - 1 and g[r - 1][c] == 6 and g[r + 1][c] == 6):
                out[r][c] = 7
    return out


def _free(g, cells, reserved=()):
    h, w = len(g), len(g[0])
    blocked = set(reserved)
    return all(0 <= r < h and 0 <= c < w and g[r][c] == 0 and (r, c) not in blocked
               for r, c in cells)


def _place_pattern(g, rng, footprint, colored_cells, reserved=None):
    """Place a small teaching pattern, scanning all positions in seeded order.

    Footprint cells include zero gaps that must stay zero.  Add those cells to
    `reserved` so later filler pairs/scatter cannot erase the counterexample.
    """
    h, w = len(g), len(g[0])
    ph = max(r for r, _c in footprint) + 1
    pw = max(c for _r, c in footprint) + 1
    starts = [(r, c) for r in range(h - ph + 1) for c in range(w - pw + 1)]
    rng.shuffle(starts)
    for r0, c0 in starts:
        cells = [(r0 + r, c0 + c) for r, c in footprint]
        if not _free(g, cells, reserved or ()):  # also protects prior zero-gaps
            continue
        for r, c, val in colored_cells:
            g[r0 + r][c0 + c] = val
        if reserved is not None:
            reserved.update(cells)
        return True
    return False


def _place_pattern_exact(g, rng, footprint, colored_cells, reserved, expected_delta):
    """Place a teaching motif while preserving an exact bridge-count delta."""
    h, w = len(g), len(g[0])
    ph = max(r for r, _c in footprint) + 1
    pw = max(c for _r, c in footprint) + 1
    starts = [(r, c) for r in range(h - ph + 1) for c in range(w - pw + 1)]
    rng.shuffle(starts)
    before = len(_fill_cells(g))
    for r0, c0 in starts:
        cells = [(r0 + r, c0 + c) for r, c in footprint]
        if not _free(g, cells, reserved):
            continue
        changed = []
        for r, c, val in colored_cells:
            rr, cc = r0 + r, c0 + c
            changed.append((rr, cc, g[rr][cc]))
            g[rr][cc] = val
        if len(_fill_cells(g)) == before + expected_delta:
            reserved.update(cells)
            return True
        for rr, cc, old in changed:
            g[rr][cc] = old
    return False


def _place_one_exact_gap(g, rng, reserved):
    """Add one 6-0-6 motif and reject placements with side effects."""
    h, w = len(g), len(g[0])
    candidates = []
    for r in range(h):
        for c in range(1, w - 1):
            candidates.append(((r, c), ((r, c - 1), (r, c + 1))))
    for r in range(1, h - 1):
        for c in range(w):
            candidates.append(((r, c), ((r - 1, c), (r + 1, c))))
    rng.shuffle(candidates)
    before = len(_fill_cells(g))
    for center, ends in candidates:
        cells = [center, *ends]
        if not _free(g, cells, reserved):
            continue
        for r, c in ends:
            g[r][c] = 6
        if len(_fill_cells(g)) == before + 1:
            reserved.update(cells)
            return True
        for r, c in ends:
            g[r][c] = 0
    return False


def _paint_without_changing_gap_count(g, cells, value, reserved):
    """Paint a decoy only when it leaves the exact semantic axis unchanged."""
    if not _free(g, cells, reserved):
        return False
    before = len(_fill_cells(g))
    for r, c in cells:
        g[r][c] = value
    if len(_fill_cells(g)) == before:
        reserved.update(cells)
        return True
    for r, c in cells:
        g[r][c] = 0
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if overrides.get("texture") == "no_gaps" and overrides.get("n_gaps") is not None:
        raise ValueError("n_gaps is incompatible with texture=no_gaps")

    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
    else:
        texture = ctx.draw_choice("texture", ("plain", "plain", "wide_gap",
                                              "filled_gap", "cross",
                                              "seven_decoy"))
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)

    h = ctx.draw_int_diff("grid_h", 8, 18)
    w = ctx.draw_int_diff("grid_w", 8, 18)
    target_n_gaps = ctx.draw_int_diff("n_gaps", 1, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved = set()

    if texture == "cross":
        if not _place_pattern_exact(
            g, rng,
            [(r, c) for r in range(3) for c in range(3)],
            [(0, 1, 6), (1, 0, 6), (1, 2, 6), (2, 1, 6)],
            reserved, 1,
        ):
            raise ValueError("could not realize cross teaching motif")
        # When the exact count permits, also teach a two-gap chain.
        if target_n_gaps >= 3 and not _place_pattern_exact(
            g, rng, [(0, i) for i in range(5)],
            [(0, 0, 6), (0, 2, 6), (0, 4, 6)], reserved, 2,
        ):
            raise ValueError("could not realize chain teaching motif")
    elif texture == "wide_gap":
        if not _place_pattern_exact(
            g, rng, [(0, i) for i in range(4)],
            [(0, 0, 6), (0, 3, 6)], reserved, 0,
        ):
            raise ValueError("could not realize wide-gap teaching motif")
    elif texture == "filled_gap":
        mid = rng.choice([1, 2, 3, 4, 5, 8, 9])
        if not _place_pattern_exact(
            g, rng, [(0, 0), (0, 1), (0, 2)],
            [(0, 0, 6), (0, 1, mid), (0, 2, 6)], reserved, 0,
        ):
            raise ValueError("could not realize occupied-gap teaching motif")
    elif texture == "seven_decoy":
        if not _place_pattern_exact(
            g, rng, [(0, 0), (0, 1), (0, 2)],
            [(0, 0, 7), (0, 2, 7)], reserved, 0,
        ):
            raise ValueError("could not realize seven-decoy teaching motif")

    while len(_fill_cells(g)) < target_n_gaps:
        if not _place_one_exact_gap(g, rng, reserved):
            raise ValueError(
                f"could not realize n_gaps={target_n_gaps} on {h}x{w} canvas"
            )
    if len(_fill_cells(g)) != target_n_gaps:
        raise AssertionError("exact n_gaps construction overshot its target")

    # Scatter singleton 6s, but never allow a decoration to create another
    # eligible bridge.  This makes the exact count recoverable from the grid.
    single_candidates = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(single_candidates)
    wanted_singles = rng.randint(1, 4)
    placed_singles = 0
    for cell in single_candidates:
        if _paint_without_changing_gap_count(g, [cell], 6, reserved):
            placed_singles += 1
            if placed_singles == wanted_singles:
                break

    if rng.random() < 0.4:
        block_color = rng.choice([1, 2, 3, 4, 5, 8, 9])
        starts = [(r, c) for r in range(h - 1) for c in range(w - 1)]
        rng.shuffle(starts)
        for r, c in starts:
            cells = [(r + dr, c + dc) for dr in (0, 1) for dc in (0, 1)]
            if _paint_without_changing_gap_count(g, cells, block_color, reserved):
                break

    if len(_fill_cells(g)) != target_n_gaps:
        raise AssertionError("decoration changed exact n_gaps")
    return g


def _draw_from_degenerate(name, ctx):
    """no_gaps — scattered 6 singles, no one-cell sandwich anywhere:
    identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int_diff("grid_h", 8, 18)
    w = ctx.draw_int_diff("grid_w", 8, 18)
    g = full_grid(h, w, 0)
    for _ in range(rng.randint(3, 6)):
        for _t in range(80):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = 6
                if _mirror(g) != g:
                    g[r][c] = 0
                    continue
                break
    return g


def _fill_cells(grid):
    h, w = len(grid), len(grid[0])
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if ((0 < c < w - 1 and grid[r][c - 1] == 6 and grid[r][c + 1] == 6)
                    or (0 < r < h - 1 and grid[r - 1][c] == 6 and grid[r + 1][c] == 6)):
                out.append((r, c))
    return out


def _meta_overrides(meta):
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid):
    """Recover all declared exact semantic axes from a lawful grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("cannot observe an empty or ragged grid")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_gaps": len(_fill_cells(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    observed = observe_overrides(grid)
    requested = _meta_overrides(meta)
    texture = requested.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if observed["n_gaps"] != 0:
            msgs.append("no_gaps scene contains a one-cell 6-gap")
    elif observed["n_gaps"] == 0:
        msgs.append("non-degenerate board has no one-cell 6-gap to fill")
    for name, value in requested.items():
        if name in observed and observed[name] != value:
            msgs.append(
                f"override {name}={value!r} realized as {observed[name]!r}"
            )
    return msgs
