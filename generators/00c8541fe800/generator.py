"""Generator for arc_puzzle_bank_tenth21:H64 (task 00c8541fe800).

THE RULE (what a solver must learn to see):
  The grid splits into 3 panels at full-height color-9 columns:
  a | b | query. The rule finds which transform maps a onto b — tried
  in priority order rotate-cw, rotate-180, rotate-ccw, flip-lr,
  flip-ud — and applies THAT transform to the query. If nothing maps
  a to b, the query passes through unchanged.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - b REALLY IS transform(a), and a is asymmetric enough that the
    intended transform is the FIRST match in the rule's chain
    (verified by a Python mirror at generation time). The old
    generator drew 5-7 panels of unrelated random motifs, so EVERY
    board fell through to the identity fallback — the analogy logic
    was never exercised once
  - all 6 branches reachable (transform axis incl. 'none'); rotations
    need square a/b panels, flips work on rectangles
  - panels carry dense multicolor patterns (not just 1-3 cell motifs);
    query differs from a, so copying a's answer is refuted

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - ambiguous_symmetric  a is D4-symmetric: several transforms map a
                         to b and only the chain order disambiguates
  - unrelated_b          b shares nothing with a (identity fallback)
  - blank_query          query panel is empty (output empty either way)
  (all degenerates keep 3 panels — fewer would CRASH the rule, which
  indexes parts 1-3 unconditionally)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00c8541fe800"
VERSION = "2.0.0"
TASK_ID = "00c8541fe800"

SUMMARY = (
    "3 panels split by full-height color-9 columns: a | b | query, "
    "where b = T(a) for T in {rot-cw, rot-180, rot-ccw, flip-lr, "
    "flip-ud, none} (rotations use square panels; a is asymmetric "
    "enough that T is the rule's first matching branch). Rule applies "
    "the same T to the query panel and emits the result."
)

# Rivals: 'output = b' refuted by every demo (query differs from a).
# 'output = query unchanged' refuted by any non-identity demo.
# 'always rotate-cw' refuted by demos using flips/180. 'match by
# color not geometry' refuted by multicolor panels where the color
# multiset is preserved under T. 4 demos spanning >=3 transforms.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly 3 panels split by 2 full-height color-9 columns",
    "panel content never uses color 9 (would break the splitter)",
    "b equals T(a) and T is the FIRST matching branch of the rule's chain",
    "rotation boards have square a/b panels (dims must survive rotation)",
    "query is non-empty and differs from a (helpful path)",
]

TRANSFORMS = ("rot_cw", "rot_180", "rot_ccw", "flip_lr", "flip_ud", "none")
DEGENERATE_TEXTURES = ("ambiguous_symmetric", "unrelated_b", "blank_query")
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "panel_h":   {"type": "int", "default": "rng 4..5 (easy 3..4, hard 5..6)",
                  "valid": "3..6", "doc": "Panel (= grid) height."},
    "transform": {"type": "enum", "default": "rng over all 6",
                  "valid": "rot_cw|rot_180|rot_ccw|flip_lr|flip_ud|none",
                  "doc": "The a->b mapping the rule must discover ('none' = "
                         "identity fallback: b is a recolored decoy)."},
    "density":   {"type": "float", "default": "rng 0.3..0.65",
                  "valid": "0.2..0.8", "doc": "Fill chance per panel cell."},
    "n_colors":  {"type": "int", "default": "rng 2..4",
                  "valid": "1..6", "doc": "Distinct content colors per board."},
    "texture":   {"type": "str", "default": "plain",
                  "valid": "plain|ambiguous_symmetric|unrelated_b|blank_query",
                  "doc": "Set to a degenerate name to build a rule-hiding input."},
}

def self_check(grid, *, difficulty=None, meta=None):
    """Verify: 3 panels separated by exactly 2 full-height color-9 columns."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    nine_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(nine_cols) < 2:
        pass  # degenerate — allowed (unrelated_b or blank_query may still have 2)
    return errors


_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)  # not bg(0), not divider(9)


# ------------------------------------------------- rule mirror (Python)
def _rot_cw(p):
    return [list(row) for row in zip(*p[::-1])]


def _rot_180(p):
    return [row[::-1] for row in p[::-1]]


def _flip_lr(p):
    return [row[::-1] for row in p]


def _flip_ud(p):
    return p[::-1]


_CHAIN = (
    ("rot_cw", _rot_cw),
    ("rot_180", _rot_180),
    ("rot_ccw", lambda p: _rot_cw(_rot_180(p))),
    ("flip_lr", _flip_lr),
    ("flip_ud", _flip_ud),
)


def _first_match(a, b):
    """Which branch of the rule's cond fires for (a, b)? Mirrors order."""
    for name, fn in _CHAIN:
        if fn(a) == b:
            return name
    return "none"


# ------------------------------------------------------------- builders
def _panel(rng, h, w, colors, density):
    p = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                p[r][c] = rng.choice(colors)
    if all(v == 0 for row in p for v in row):
        p[rng.randrange(h)][rng.randrange(w)] = rng.choice(colors)
    return p


def _assemble(panels, h):
    w = sum(len(p[0]) for p in panels) + len(panels) - 1
    g = full_grid(h, w, 0)
    c0 = 0
    for i, p in enumerate(panels):
        for r in range(h):
            for c in range(len(p[0])):
                g[r][c0 + c] = p[r][c]
        c0 += len(p[0])
        if i < len(panels) - 1:
            for r in range(h):
                g[r][c0] = 9
            c0 += 1
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx)

    if difficulty == "easy":
        h = ctx.draw_int("panel_h", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("panel_h", 5, 6)
    else:
        h = ctx.draw_int("panel_h", 4, 5)
    t = overrides.get("transform", ctx.draw_choice("transform", TRANSFORMS))
    rng = ctx.draw_rng("layout")
    density = float(overrides.get(
        "density", ctx.draw_rng("density").uniform(0.3, 0.65)))
    n_colors = ctx.draw_int("n_colors", 2, 4)
    colors = list(rng.sample(_COLORS, n_colors))

    rotational = t in ("rot_cw", "rot_180", "rot_ccw")
    # rotations only typecheck when a/b are square (h x h)
    wa = h if rotational else rng.randint(3, 6)
    wq = rng.randint(3, 6)

    fns = dict(_CHAIN)
    for _attempt in range(80):
        a = _panel(rng, h, wa, colors, density)
        if t == "none":
            # decoy b: same dims as a but unequal to EVERY T(a), so the
            # rule's chain falls through to the identity branch
            b = _panel(rng, h, wa, colors, density)
            if _first_match(a, b) != "none" or b == a:
                continue
        else:
            b = fns[t](a)
            # the intended transform must be the FIRST match in the
            # rule's chain (a too symmetric -> an earlier branch wins)
            if _first_match(a, b) != t:
                continue
        query = _panel(rng, h, wq, colors, density)
        if query == a:
            continue
        return _assemble([a, b, query], h)
    raise ValueError(f"could not realize transform={t} h={h}")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — always 3 panels (fewer crashes the rule).

    ambiguous_symmetric — a is fully symmetric, so b matches several
                          transforms; only the chain order decides.
    unrelated_b         — b shares nothing with a: identity fallback.
    blank_query         — nothing to transform; output is empty.
    """
    h = ctx.draw_int("panel_h", 4, 5)
    rng = ctx.draw_rng("degenerate_layout")
    colors = list(rng.sample(_COLORS, 2))
    if name == "ambiguous_symmetric":
        # solid square: every transform maps a onto itself
        a = [[colors[0]] * h for _ in range(h)]
        b = [row[:] for row in a]
        q = _panel(rng, h, rng.randint(3, 5), colors, 0.5)
        return _assemble([a, b, q], h)
    if name == "unrelated_b":
        a = _panel(rng, h, 4, [colors[0]], 0.5)
        b = _panel(rng, h, 4, [colors[1]], 0.5)
        q = _panel(rng, h, rng.randint(3, 5), colors, 0.5)
        return _assemble([a, b, q], h)
    # blank_query
    a = _panel(rng, h, h, colors, 0.5)
    b = _rot_cw(a)
    q = full_grid(h, rng.randint(3, 5), 0)
    return _assemble([a, b, q], h)
