"""Generator for arc_puzzle_bank_21_set20_s:S20_E5.

Combinatorial axes (8): panel_h, panel_w, palette_kind, candidate_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_hits, all_hits.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels, paste

GENERATOR_ID = "4256bbb98042"
VERSION = "1.2.1"  # distinct=20: output is a 1xn hit-indicator so #distinct = #(hit-subsets), bounded by n which was pinned at 3..4 (-> ~20). Widened candidate_count to 3..6 (out shapes 1x3..1x6 + many more hit subsets); candidate panel width lowered to 3 (template is <=3 wide) so larger n fits in 30 cols.
TASK_ID = "4256bbb98042"
SUMMARY = "A strip flags candidate panels that contain the template."

INVARIANTS = [
    "divider color is 9",
    "first panel contains the template",
    "subsequent panels are candidates",
    "some candidates contain an exact template match",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_hits", "all_hits")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "panel_w":        {"type": "int", "default": "rng 3..max_w", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "candidate_count": {"type": "int", "default": "rng 3..5 by diff", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "template_plus_candidates",
                       "valid": "template_plus_candidates"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

TEMPLATE = [[5, 6, 7], [8, 2, 3], [4, 5, 6]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("panel_h", 7, 7)
        n = ctx.draw_int("candidate_count", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("panel_h", 8, 9)
        n = ctx.draw_int("candidate_count", 5, 6)
    else:
        n = ctx.draw_int("candidate_count", 3, 5)
        h = ctx.draw_int("panel_h", 7, 9)
    # output is a 1xn hit-indicator -> #distinct = #(hit-subsets), bounded by n.
    # widen n (3..6) for far more distinct outputs (+ varied 1xn out shapes).
    # candidate panel width only needs to hold the <=3-wide template.
    max_w = max(3, (30 - 5 - (n + 1)) // n)
    w = ctx.draw_int("panel_w", 3, max_w)
    rng = ctx.draw_rng("layout")
    template_panel = full_grid(h, 5, 0)
    paste(template_panel, TEMPLATE, 1, 1)
    hit_idxs = set(rng.sample(range(n), rng.randint(1, n - 1)))
    candidates = []
    for i in range(n):
        panel = full_grid(h, w, 0)
        if i in hit_idxs:
            paste(panel, TEMPLATE, rng.randint(0, h - 3), rng.randint(0, w - 3))
        else:
            panel[h // 2][w // 2] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        candidates.append(panel)
    return assemble_vertical_panels([template_panel] + candidates)


def _split_panels(grid):
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    starts = [0] + [c + 1 for c in divs]
    ends = divs + [w]
    return [[[row[c] for c in range(a, b)] for row in grid] for a, b in zip(starts, ends) if a < b]


def _contains_template(panel):
    if not panel:
        return False
    h, w = len(panel), len(panel[0])
    th, tw = len(TEMPLATE), len(TEMPLATE[0])
    for r0 in range(h - th + 1):
        for c0 in range(w - tw + 1):
            if all(panel[r0 + r][c0 + c] == TEMPLATE[r][c] for r in range(th) for c in range(tw)):
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    panels = _split_panels(grid)
    if len(panels) < 3:
        errs.append("expected template panel plus at least two candidates")
        return errs
    if not _contains_template(panels[0]):
        errs.append("first panel should contain the template")
    hits = [_contains_template(panel) for panel in panels[1:]]
    if not any(hits):
        errs.append("expected at least one hit candidate")
    if all(hits):
        errs.append("expected at least one non-hit candidate")
    return errs



def _draw_from_degenerate(name, rng):
    h, w, n = 7, 5, 3
    if name == "no_template":
        # candidates without template → no pattern to flag matches against
        template_panel = full_grid(h, 5, 0)
        candidates = []
        for i in range(n):
            panel = full_grid(h, w, 0)
            paste(panel, TEMPLATE, 1, 1)
            candidates.append(panel)
        return assemble_vertical_panels([template_panel] + candidates)
    if name == "no_hits":
        # template present but no candidates contain it → "some hits" precondition fails
        template_panel = full_grid(h, 5, 0)
        paste(template_panel, TEMPLATE, 1, 1)
        candidates = [full_grid(h, w, 0) for _ in range(n)]
        for panel in candidates:
            panel[h // 2][w // 2] = 4
        return assemble_vertical_panels([template_panel] + candidates)
    if name == "all_hits":
        # all candidates match → no negative contrast (rule flags everything)
        template_panel = full_grid(h, 5, 0)
        paste(template_panel, TEMPLATE, 1, 1)
        candidates = []
        for i in range(n):
            panel = full_grid(h, w, 0)
            paste(panel, TEMPLATE, 1, 1)
            candidates.append(panel)
        return assemble_vertical_panels([template_panel] + candidates)
    return full_grid(h, w * (n + 1) + n, 0)
