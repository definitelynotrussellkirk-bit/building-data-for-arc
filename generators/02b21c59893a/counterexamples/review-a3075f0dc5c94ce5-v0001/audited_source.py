"""Generator for arc_puzzle_bank_21_set18_bundle:medium_p05 (task 02b21c59893a).

THE RULE (what a solver must learn to see):
  The blue(1) cell is the SOURCE anchor; the last red(2) cell in scan
  order is the DESTINATION anchor. Everything that is not color 1 or 2
  is PAYLOAD. Output = fresh canvas with red(2) painted at the
  destination and every payload cell translated by (dst - src),
  keeping its own color; off-board cells clip. With no blue present,
  the source silently degrades to (0, 0).

  (The old docstring described a 'red->green vector moving yellow' —
  pure fiction: green and yellow are both just payload, and the old
  boards never contained a blue anchor at all, so every training pair
  only ever exercised the (0,0)-fallback.)

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - with_blue (default): blue anchor sits ON/NEXT TO the payload, red
    sits elsewhere — the payload visibly re-anchors from blue to red
  - payload is multi-colored (2-3 colors from {3..9}) — colors survive
  - no_blue: the legacy fallback (src = origin) stays reachable
  - clip: part of the translated payload falls off-board

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_payload  markers only: output is just the red dot
  - multi_red   several reds: the LAST in scan order wins
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "02b21c59893a"
VERSION = "3.0.1"
TASK_ID = "02b21c59893a"

SUMMARY = (
    "0-bg grid with a blue(1) source anchor on a 2-5 cell multicolor "
    "payload (colors 3-9) and one red(2) destination anchor; rule "
    "repaints red at the destination and translates the payload by "
    "(red - blue) onto a fresh canvas, colors kept, edges clipping. "
    "Without a blue the source degrades to (0,0)."
)

# Rivals: 'payload must be yellow' refuted by multicolor payloads.
# 'green is a marker' refuted (it translates like any payload).
# 'source is the payload bbox corner' refuted by blue anchors placed
# off-corner. 'first red wins' refuted by multi_red boards (LAST
# wins). 4 demos: >=2 with blue anchors, >=1 no_blue fallback.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one blue source anchor (with_blue path) and >=1 red cell",
    "payload cells use colors 3-9 only (1/2 are the anchors)",
    "plain boards: the translated payload stays in-bounds",
    "clip boards: part of the payload falls off-board",
]

DEGENERATE_TEXTURES = ("no_payload", "multi_red")
HELPFUL_TEXTURES = ("with_blue", "no_blue", "clip")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 7..10 (hard 10..13)",
                  "valid": "5..14", "doc": "Grid height."},
    "grid_w":    {"type": "int", "default": "rng 10..14 (hard 14..17)",
                  "valid": "8..18", "doc": "Grid width."},
    "n_payload": {"type": "int", "default": "rng 2..5", "valid": "1..6",
                  "doc": "Payload cells (multicolor)."},
    "texture":   {"type": "str", "default": "rng (with_blue 60%)",
                  "valid": "with_blue|no_blue|clip|no_payload|multi_red",
                  "doc": "Anchor flavor or a degenerate name."},
}

_PAYLOAD_COLORS = (3, 4, 5, 6, 7, 8, 9)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("with_blue", "with_blue", "with_blue", "no_blue", "clip"))

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 14, 17)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 14)
    n_payload = int(overrides.get("n_payload", ctx.draw_int("n_payload", 2, 5)))
    rng = ctx.draw_rng("layout")

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        # payload blob near the top-left half
        cells = {(rng.randint(1, max(1, h // 2)), rng.randint(1, max(1, w // 2)))}
        while len(cells) < n_payload:
            r, c = list(cells)[rng.randrange(len(cells))]
            dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
            if 0 <= r + dr < h and 0 <= c + dc < w:
                cells.add((r + dr, c + dc))
        colors = rng.sample(_PAYLOAD_COLORS, min(len(cells), rng.randint(2, 3)))
        for i, (r, c) in enumerate(sorted(cells)):
            g[r][c] = colors[i % len(colors)]

        if texture == "no_blue":
            src = (0, 0)  # the rule's silent fallback
        else:
            # blue anchor adjacent to (or on the edge of) the payload
            ring = sorted({(r + dr, c + dc)
                           for r, c in cells
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                           if 0 <= r + dr < h and 0 <= c + dc < w
                           and (r + dr, c + dc) not in cells})
            if not ring:
                continue
            src = ring[rng.randrange(len(ring))]
            g[src[0]][src[1]] = 1

        placed = False
        for _try in range(60):
            dst = (rng.randrange(h), rng.randrange(w))
            if g[dst[0]][dst[1]] != 0:
                continue
            dr, dc = dst[0] - src[0], dst[1] - src[1]
            if (dr, dc) == (0, 0):
                continue
            moved = [(r + dr, c + dc) for r, c in cells]
            oob = sum(1 for r, c in moved if not (0 <= r < h and 0 <= c < w))
            if texture == "clip":
                if oob == 0 or oob == len(moved):
                    continue
            else:
                if oob:
                    continue
            g[dst[0]][dst[1]] = 2
            placed = True
            break
        if placed:
            return g
    raise ValueError("could not realize anchor-translate board")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (>=1 red always: an
    empty red list would make `last` misbehave).

    no_payload — anchors only: output is the lone red dot.
    multi_red  — several reds: the LAST in scan order is the anchor.
    """
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_payload":
        g[rng.randrange(h)][rng.randrange(w // 2)] = 1
        g[rng.randrange(h)][rng.randint(w // 2, w - 1)] = 2
        return g
    # multi_red: payload + blue + several reds
    r0, c0 = rng.randint(1, h - 2), rng.randint(1, 3)
    g[r0][c0] = rng.choice(_PAYLOAD_COLORS)
    g[r0][c0 + 1] = rng.choice(_PAYLOAD_COLORS)
    g[r0 - 1][c0] = 1
    placed = 0
    for _ in range(60):
        if placed >= rng.randint(2, 3):
            break
        r, c = rng.randrange(h), rng.randint(w // 2, w - 1)
        if g[r][c] == 0:
            g[r][c] = 2
            placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 red(2) destination anchor; <=1 blue(1) source anchor;
    all payload cells use colors 3-9 only."""
    msgs = []
    h, w = len(grid), len(grid[0])
    reds = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if reds < 1:
        msgs.append("no red(2) destination anchor found")
    if blues > 1:
        msgs.append(f"expected <=1 blue(1) source anchor, found {blues}")
    # Payload must only use colors 3-9 (1=blue anchor, 2=red anchor, 0=bg)
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)]
    if bad:
        msgs.append(f"out-of-range cell values: {bad[:3]}")
    return msgs
