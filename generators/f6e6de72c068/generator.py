"""Generator for arc_puzzle_bank_21_set5_e:easy_e02 — bridge A-0-A row gaps.

Rule (single pass over the ORIGINAL grid): for every horizontal triple where
g[r][c]=A (non-zero), g[r][c+1]=0, g[r][c+2]=A, set the middle cell to A. So a
same-color pair flanking a one-cell gap gets bridged.

PRIOR GAP: the SUMMARY/INVARIANTS claimed decoy cells (a selectivity test), but
generate() only ever placed A-0-A motifs — the rule's "don't bridge" behavior was
never exercised. This version places BOTH firing motifs (A-0-A and A-0-A-0-A
chains) AND non-firing decoys (A-0-B mismatched, A-0-0-A two-gap, adjacent A-A,
isolated singletons). Each group gets a 1-cell horizontal halo so groups never
combine into unintended triples (the rule is per-row horizontal).

Rule-safe diversity: grid size, number of motifs/chains, number/kind of decoys,
colors, positions.
Degenerates: no_motifs, motif_already_filled, mismatched_endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f6e6de72c068"
VERSION = "3.0.0"  # add real non-firing decoys (selectivity was never exercised) + chains + bigger grids
TASK_ID = "f6e6de72c068"
SUMMARY = (
    "0-bg grid (size varies). Several FIRING motifs per row — A-0-A (a same-color "
    "pair flanking one gap) and A-0-A-0-A chains (two gaps) — PLUS non-firing "
    "DECOYS: A-0-B (mismatched colors), A-0-0-A (two-cell gap), adjacent A-A, and "
    "isolated singletons. Each group is horizontally isolated by a 1-cell halo. "
    "Rule: bridge every A-0-A by setting the middle cell to A; decoys are left "
    "untouched. Net: single-cell gaps between equal colors close; everything else "
    "stays. (Was: only A-0-A motifs, no decoys -> selectivity never tested.)"
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=2 firing A-0-A motifs (the rule bridges them; output differs)",
    ">=1 non-firing decoy (A-0-B / A-0-0-A / A-A / singleton) — selectivity test",
    "groups are horizontally isolated by a 1-cell halo so none combine accidentally",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "motif_already_filled", "mismatched_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":   {"type": "int", "default": "5-7 easy / 6-10 med / 9-14 hard", "valid": "3..16"},
    "grid_w":   {"type": "int", "default": "8-11 easy / 10-15 med / 13-20 hard", "valid": "5..22"},
    "motifs":   {"type": "int", "default": "2-3 easy / 3-5 med / 4-7 hard", "valid": "1..14"},
    "decoys":   {"type": "int", "default": "1-2 easy / 2-3 med / 2-4 hard", "valid": "0..6"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _place_group(g, occ, rng, cells_fn):
    """Place a horizontal group; cells_fn(color, color2) -> list of (dcol, value).
    Reserves the group span + 1-cell halo on each side within the row."""
    h, w = len(g), len(g[0])
    for _ in range(40):
        a = rng.randint(1, 9)
        b = rng.choice([x for x in range(1, 10) if x != a])
        cells = cells_fn(a, b)
        gw = max(dc for dc, _ in cells) + 1
        r = rng.randrange(h)
        c = rng.randint(0, w - gw)
        span = range(c - 1, c + gw + 1)            # group + horizontal halo
        if any((r, cc) in occ for cc in span):
            continue
        for dc, v in cells:
            if v:
                g[r][c + dc] = v
        for cc in span:
            occ.add((r, cc))
        return True
    return False


_MOTIFS = [
    lambda a, b: [(0, a), (2, a)],                 # A-0-A  -> bridges
    lambda a, b: [(0, a), (2, a), (4, a)],         # A-0-A-0-A -> two bridges
]
_DECOYS = [
    lambda a, b: [(0, a), (2, b)],                 # A-0-B  mismatched
    lambda a, b: [(0, a), (3, a)],                 # A-0-0-A two-gap
    lambda a, b: [(0, a), (1, a)],                 # A-A adjacent
    lambda a, b: [(0, a)],                         # singleton
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, mr, dr = (5, 7), (8, 11), (2, 3), (1, 2)
    elif difficulty == "hard":
        hr, wr, mr, dr = (9, 14), (13, 20), (4, 7), (2, 4)
    else:
        hr, wr, mr, dr = (6, 10), (10, 15), (3, 5), (2, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(30):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = set()
        fired = 0
        for _ in range(rng.randint(*mr)):
            if _place_group(g, occ, rng, rng.choice(_MOTIFS)):
                fired += 1
        decoyed = 0
        for _ in range(rng.randint(*dr)):
            if _place_group(g, occ, rng, rng.choice(_DECOYS)):
                decoyed += 1
        if fired >= 2 and decoyed >= 1:
            return g

    # deterministic fallback: 2 motifs + 1 decoy
    g = full_grid(6, 10, 0)
    g[1][1] = 4; g[1][3] = 4          # A-0-A
    g[3][5] = 6; g[3][7] = 6          # A-0-A
    g[5][2] = 3; g[5][4] = 8          # A-0-B decoy
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # only single colored cells, never an A-0-A triple -> rule fires zero times
        g[1][2] = 4; g[3][6] = 6; g[5][1] = 3
        return g
    if name == "motif_already_filled":
        # A-A-A (middle already A, not 0) -> nothing to fill
        g[2][1] = 4; g[2][2] = 4; g[2][3] = 4
        g[4][3] = 6; g[4][4] = 6; g[4][5] = 6
        return g
    if name == "mismatched_endpoints":
        # A-0-B (different colors) -> predicate fails, middle stays 0
        g[1][1] = 4; g[1][3] = 6
        g[3][2] = 3; g[3][4] = 8
        return g
    return g


def _count_firing_triples(grid):
    total = 0
    for row in grid:
        for c in range(len(row) - 2):
            a = row[c]
            if a != 0 and row[c + 1] == 0 and row[c + 2] == a:
                total += 1
    return total


def _has_non_firing_decoy(grid):
    firing_colored = set()
    for r, row in enumerate(grid):
        for c in range(len(row) - 2):
            a = row[c]
            if a != 0 and row[c + 1] == 0 and row[c + 2] == a:
                firing_colored.add((r, c))
                firing_colored.add((r, c + 2))

    for r, row in enumerate(grid):
        w = len(row)
        # Mismatched endpoints A-0-B.
        for c in range(w - 2):
            if row[c] != 0 and row[c + 1] == 0 and row[c + 2] != 0 and row[c + 2] != row[c]:
                return True
        # Two-cell gap A-0-0-A.
        for c in range(w - 3):
            if row[c] != 0 and row[c + 1] == 0 and row[c + 2] == 0 and row[c + 3] == row[c]:
                return True
        # Adjacent pair A-A.
        for c in range(w - 1):
            if row[c] != 0 and row[c + 1] == row[c]:
                return True
        # Horizontally isolated singleton that is not just an endpoint of a firing motif.
        for c, v in enumerate(row):
            if v != 0 and (r, c) not in firing_colored:
                left = row[c - 1] if c > 0 else 0
                right = row[c + 1] if c + 1 < w else 0
                if left == 0 and right == 0:
                    return True
    return False


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("grid values must be digits 0..9")
    firing = _count_firing_triples(grid)
    if firing < 2:
        errs.append("expected at least two firing A-0-A triples")
    if not _has_non_firing_decoy(grid):
        errs.append("expected at least one non-firing horizontal decoy")
    return errs
