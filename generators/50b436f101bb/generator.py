"""Generator for da6e95e5.

Rule: background = the most frequent color. Cluster the non-bg cells (with a
2-cell gap bridge). Take the LARGEST one-color cluster, shrink its bbox by 2
cells on each side, and output that inner region (cells equal to the cluster's
color stay, everything else becomes bg).

The old generator drew the large object as a SOLID rectangle, so its inner
region was solid -> the output was always a solid block (distinct only via size
+ color, ~26). The rule's output is the object's INNER PATTERN, so now: a 2-wide
color RING (fixing the bbox + giving the largest cluster) with a RANDOM color
pattern inside -> the (size-4)×(size-4) output pattern varies, and the object
size varies the output dims.

Combinatorial axes: object size (-> output dims), the inner color pattern,
color, grid size, distractor clusters.
Degenerates: solid_object, no_object, two_equal_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "50b436f101bb"
# 3.2.0: defect-lint canonical-coverage/drift/axis — canonical demos are 30x30
# fields on a NONZERO background with ~30 small motif objects in ~7 colors; we
# were 0-bg, <=27, ~4 objects, 3 colors. Now: bg nonzero 70% of the time (the
# rule takes the mode), dims reach 30, and 4-7 distractor motif GROUPS (dot
# clusters, some two-colored) replace the two 2x2 blocks. AXES made honest.
# (3.1.0: 2-cell margin guard on distractors.)
VERSION = "3.2.1"
TASK_ID = "50b436f101bb"
SUMMARY = (
    "0-bg grid (size varies). The LARGEST object is a 2-wide RING of one color "
    "forming a size×size bounding box (size 7-11) with a RANDOM pattern of that "
    "color filling its (size-4)×(size-4) INTERIOR. A couple of small distractor "
    "clusters in other colors sit elsewhere. Rule: background = most frequent "
    "color; cluster non-bg cells; take the largest one-color cluster; shrink its "
    "bbox by 2; output the inner region (the color's cells stay, else bg). "
    "Output = the ring's interior pattern, dims (size-4)×(size-4)."
)

INVARIANTS = [
    "background 0 is the most frequent color",
    "the largest one-color cluster is a size×size ring with a patterned interior",
    "distractor clusters are smaller than the ring",
    "the interior pattern is non-trivial (some on, some off)",
]

SIZE_KINDS = ("s7", "s9", "s11")
PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("solid_object", "no_object", "two_equal_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "size+8 .. 30", "valid": "15..30"},
    "grid_w":         {"type": "int", "default": "size+8 .. 30", "valid": "15..30"},
    "rect_size":      {"type": "int", "default": "rng 7..11 (odd)", "valid": "7..11"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5-8 (ring + distractor groups)", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "ring_plus_distractors",
                       "valid": "ring_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "5-8", "valid": "3..8"},
    "texture":        {"type": "str", "default": "alias for rect_size",
                       "valid": "|".join(SIZE_KINDS + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    tx = overrides.get("texture")
    if tx in SIZE_KINDS:
        size = int(tx[1:])
    elif difficulty == "easy":
        size = rng.choice([7, 9])
    elif difficulty == "hard":
        size = rng.choice([9, 11])
    else:
        size = rng.choice([7, 9, 11])

    # Canonical demos use a NONZERO background (the rule takes the mode).
    bg = 0 if rng.random() < 0.3 else rng.choice([1, 3, 4, 8])
    n_distract = rng.randint(4, 7)
    picks = ctx.draw_distinct_colors("colors", n=min(1 + n_distract, 8),
                                     exclude={0, bg})
    color = picks[0]
    distractor_colors = list(picks[1:])
    # canonical demos are all exactly 30x30 (area median 900) — hit the full
    # canvas 40% of the time so the area envelope reliably reaches them
    # (without this the coverage check is borderline sample-dependent)
    if rng.random() < 0.4:
        h = w = 30
    else:
        h = ctx.draw_int("grid_h", size + 8, min(30, size + 19))
        w = ctx.draw_int("grid_w", size + 8, min(30, size + 19))
    g = full_grid(h, w, bg)
    r0 = rng.randint(0, h - size)
    c0 = rng.randint(0, w - size)
    # DOTTED frame of `color` (canonical groups are small motifs, max component
    # ~4-7 cells, chained by the rule's chebyshev<=2 clustering): 2x2 corner
    # blocks + every-other-cell edge dots. The chain spacing is exactly 2, so
    # the whole frame + interior lattice is ONE cluster — and the largest.
    key_cells = 0
    for (rr, cc) in ((r0, c0), (r0, c0 + size - 2), (r0 + size - 2, c0),
                     (r0 + size - 2, c0 + size - 2)):
        draw_rect(g, rr, cc, 2, 2, color)
        key_cells += 4
    for x in range(3, size - 3, 2):
        for (rr, cc) in ((r0, c0 + x), (r0 + size - 1, c0 + x),
                         (r0 + x, c0), (r0 + x, c0 + size - 1)):
            g[rr][cc] = color
            key_cells += 1
    # interior pattern on a spaced-2 lattice (keeps the cluster chained even at
    # size 11) + random extras — this inset-2 region IS the rule's output
    for i in range(2, size - 2, 2):
        for j in range(2, size - 2, 2):
            g[r0 + i][c0 + j] = color
            key_cells += 1
    inner = [(r0 + 2 + i, c0 + 2 + j) for i in range(size - 4) for j in range(size - 4)
             if g[r0 + 2 + i][c0 + 2 + j] == bg]
    k = rng.randint(0, max(1, len(inner) // 3))
    for (r, c) in rng.sample(inner, k):
        g[r][c] = color
        key_cells += 1

    # Distractor motif GROUPS elsewhere (canonical scenes carry ~30 small
    # objects): each group is 3-6 scattered dots in a small box, sometimes
    # two-colored (the rule ignores multi-color clusters). Every group stays
    # SMALLER than the ring and keeps a 3-cell margin from everything — the
    # rule's clustering bridges chebyshev gaps <= 2, so 3 keeps clusters apart.
    ring_cells = key_cells
    for dc in distractor_colors:
        for _ in range(60):
            gs = rng.randint(3, 4)                       # group box side
            dr = rng.randint(0, h - gs)
            dcc = rng.randint(0, w - gs)
            margin = [(r, c)
                      for r in range(max(0, dr - 3), min(h, dr + gs + 3))
                      for c in range(max(0, dcc - 3), min(w, dcc + gs + 3))]
            if not all(g[r][c] == bg for r, c in margin):
                continue
            spots = [(dr + a, dcc + b) for a in range(gs) for b in range(gs)]
            n_dots = min(rng.randint(3, 6), max(2, ring_cells - 1), len(spots))
            second = rng.choice(distractor_colors) if rng.random() < 0.3 else dc
            for i, (r, c) in enumerate(rng.sample(spots, n_dots)):
                g[r][c] = dc if i % 2 == 0 else second
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """The MODE is the background (0 or nonzero); the ring color dominates every
    other non-bg color so it stays the rule's largest single-color cluster."""
    from collections import Counter
    errs = []
    h, w = len(grid), len(grid[0])
    freq = Counter(grid[r][c] for r in range(h) for c in range(w))
    bg = freq.most_common(1)[0][0]
    nz = {c: n for c, n in freq.items() if c != bg}
    if not nz:
        return errs  # degenerate, skip further checks
    dominant, dom_count = max(nz.items(), key=lambda kv: kv[1])
    if dom_count < 20:
        errs.append(f"dominant non-bg color {dominant} has only {dom_count} cells (expected >=20 for ring)")
    for c, n in nz.items():
        if c != dominant and n >= dom_count:
            errs.append(f"distractor color {c} has {n} cells — rivals the ring "
                        f"({dominant}: {dom_count}); the rule's pick becomes ambiguous")
    return errs


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    g = full_grid(18, 18, 0)
    if name == "solid_object":
        draw_rect(g, 3, 3, 9, 9, 4)
        return g
    if name == "no_object":
        g[1][1] = 2
        return g
    if name == "two_equal_objects":
        draw_rect(g, 2, 2, 7, 7, 4)
        draw_rect(g, 2, 10, 7, 7, 6)
        return g
    return g
