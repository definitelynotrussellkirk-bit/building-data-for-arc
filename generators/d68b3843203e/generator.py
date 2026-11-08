"""M93: count red cells inside each yellow rectangle, then fill with 5 + count.

The Racket rule is unchanged. Ordinary draws have 2..3 separated frames,
variable aspect ratios/positions, a mixture of count-coverage and independent
1..3 marker counts, and one irrelevant 1..2-cell cue of color 5..9. Marker
connectivity is deliberately NOT a proxy for count. No canonical grids are
loaded or copied by generation.
"""
from __future__ import annotations

from numbers import Integral

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "d68b3843203e"
TASK_ID = GENERATOR_ID
VERSION = "1.3.0"
RULE_HASH = "90de3c06fb83"
SUMMARY = "Count 1..3 red markers in canonical-weighted 2..3 variable yellow frames."
INVARIANTS = [
    "2..3 disjoint, non-touching rectangular color-4 components",
    "frame sides >=3; interior area >=2; 1..3 red cells per interior",
    "interiors contain only 0 and 2; every red cell is inside a frame",
    "irrelevant exterior cue uses color 5..9 and is preserved by the rule",
]
AXES = {
    "grid_h": {"type": "int", "default": "weighted 10..12; support 8..16", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "weighted 11..13; support 8..18", "valid": "8..18"},
    "n_frames": {"type": "int", "default": "weighted 20% two / 80% three", "valid": "2..3"},
    "cue_size": {"type": "int", "default": "weighted 80% one / 20% two", "valid": "1..2"},
}
# Every combination in these four declared domains is constructively feasible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Match the observed canonical marginals while drawing the axes independently,
# so the canonical (3 frames, 1 cue) / (2 frames, 2 cues) correlation is not copied.
_DEFAULT_N_FRAMES = (2, 3, 3, 3, 3)
_DEFAULT_CUE_SIZES = (1, 1, 1, 1, 2)


def _slots(h, w, n, rng, need_three=False):
    """Separated slots: no retry/fallback, including the 8x8 / three-frame case."""
    # Prefer slots that can hold ordinary 4x4 frames when space permits.
    # The 8-cell boundary still uses the feasible 3 + gap + 4 split.
    cut_r = rng.randint(4, h - 5) if h >= 9 else rng.randint(3, h - 4)
    cut_c = rng.randint(4, w - 5) if w >= 9 else rng.randint(3, w - 4)
    mode = rng.choice(("horizontal", "vertical", "quadrants")) if n == 2 else "quadrants"
    if mode == "horizontal":
        return [(0, 0, cut_r, w), (cut_r + 1, 0, h - cut_r - 1, w)]
    if mode == "vertical":
        return [(0, 0, h, cut_c), (0, cut_c + 1, h, w - cut_c - 1)]
    slots = [(r, c, sh, sw)
             for r, sh in ((0, cut_r), (cut_r + 1, h - cut_r - 1))
             for c, sw in ((0, cut_c), (cut_c + 1, w - cut_c - 1))
             if (sh - 2) * (sw - 2) >= 2]
    # At most one slot is 3x3: an 8-cell axis splits into 3 + gap + 4.
    if need_three:
        primary = rng.choice([slot for slot in slots if (slot[2]-2)*(slot[3]-2) >= 3])
        return [primary] + rng.sample([slot for slot in slots if slot != primary], n-1)
    return rng.sample(slots, n)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    for key, value in overrides.items():
        if value is not None and (isinstance(value, bool) or not isinstance(value, Integral)):
            raise ValueError(f"{key} must be an integer, not {value!r}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Weight canonical scale without copying exact examples or changing support.
    h = ctx.draw_choice("grid_h", tuple(range(10, 13)) * 5 + tuple(range(8, 17)))
    w = ctx.draw_choice("grid_w", tuple(range(11, 14)) * 5 + tuple(range(8, 19)))
    n = ctx.draw_choice("n_frames", _DEFAULT_N_FRAMES)
    cue_size = ctx.draw_choice("cue_size", _DEFAULT_CUE_SIZES)
    g = full_grid(h, w, 0)
    layout = ctx.draw_rng("layout")
    occupied = set()
    max_side = {"easy": 5, "medium": 6, "hard": 7, None: 6}[difficulty]
    # Three-quarters of lessons contain 1/3 (two frames) or 1/2/3 (three),
    # matching the canonical emphasis on color 8. The remaining quarter keeps
    # independent ties and missing-color lessons in material support.
    cover_counts = ctx.draw_rng("count_profile").randrange(4) != 0
    minimum = 9 if n == 3 else 8
    inset = layout.randrange(2) if min(h,w) >= minimum + 2 else 0
    slots = [(r+inset,c+inset,sh,sw) for r,c,sh,sw in
             _slots(h-2*inset, w-2*inset, n, layout, need_three=cover_counts)]
    layout.shuffle(slots)
    forced_counts = {}
    if cover_counts:
        eligible = [i for i, (_, _, sh, sw) in enumerate(slots) if (sh-2)*(sw-2) >= 3]
        three = layout.choice(eligible)
        forced_counts[three] = 3
        others = [i for i in range(n) if i != three]
        layout.shuffle(others)
        forced_counts.update({index: count for index, count in zip(others, range(1, n))})
    for i, (sr, sc, sh, sw) in enumerate(slots):
        sizes = [(fh, fw) for fh in range(3, min(sh, max_side) + 1)
                 for fw in range(3, min(sw, max_side) + 1)
                 if (fh - 2) * (fw - 2) >= max(2, forced_counts.get(i, 1))]
        # Thin frames remain reachable, but do not dominate merely because
        # there are many skinny aspect-ratio combinations in the domain.
        ordinary = [(fh,fw) for fh,fw in sizes if fh >= 4 and fw >= 4]
        fh, fw = layout.choice(sizes + ordinary * 3)
        r0, c0 = sr + layout.randrange(sh - fh + 1), sc + layout.randrange(sw - fw + 1)
        draw_rect_outline(g, r0, c0, fh, fw, 4)
        occupied.update((r, c) for r in range(r0, r0 + fh) for c in range(c0, c0 + fw))
        inside = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
                  for c in range(c0 + 1, c0 + fw - 1)]
        markers = ctx.draw_rng(f"frame/{i}/markers")
        count = forced_counts[i] if i in forced_counts else markers.randint(1, min(3, len(inside)))
        for r, c in markers.sample(inside, count):
            g[r][c] = 2
    # The cue is independent of all marker draws and may touch an outer edge.
    # It never occupies the empty part of a frame's interior.
    cue_rng = ctx.draw_rng("cue")
    directions = [(0, 0)] if cue_size == 1 else [(0, 1), (1, 0)]
    placements = []
    for r in range(h):
        for c in range(w):
            for dr, dc in directions:
                cells = [(r + k * dr, c + k * dc) for k in range(cue_size)]
                if all(0 <= rr < h and 0 <= cc < w and (rr, cc) not in occupied
                       for rr, cc in cells):
                    placements.append(cells)
    color = cue_rng.choice((5, 6, 7, 8, 9))
    for r, c in cue_rng.choice(placements):
        g[r][c] = color
    return g


def _yellow_components(grid):
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    components = []
    while todo:
        start = min(todo)
        todo.remove(start)
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in todo:
                    todo.remove(q)
                    component.add(q)
                    pending.append(q)
        components.append(component)
    return components


def _frame_box(component):
    r0, r1 = min(r for r, _ in component), max(r for r, _ in component)
    c0, c1 = min(c for _, c in component), max(c for _, c in component)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    return (r0, c0, r1, c1) if component == border else None


def frame_facts(grid):
    """Parse complete color-4 components, matching Racket's 4-connectivity.

    Unlike the old all-border scan, a closed border with an attached yellow
    spur is not silently accepted as a frame. No input is mutated.
    """
    facts = []
    for component in _yellow_components(grid):
        box = _frame_box(component)
        if box is None:
            continue
        r0, c0, r1, c1 = box
        interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        markers = [(r, c) for r, c in interior if grid[r][c] == 2]
        mset = set(markers)
        adjacent = any((r+1,c) in mset or (r,c+1) in mset for r,c in markers)
        facts.append({"box": box, "interior": interior, "markers": markers,
                      "count": len(markers), "adjacent": adjacent})
    return facts


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return ["grid must have nonempty rows"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid must be at most 30x30"]
    if any(isinstance(v, bool) or not isinstance(v, Integral) or not 0 <= v <= 9
           for row in grid for v in row):
        return ["cells must be integers in 0..9 (not booleans)"]
    facts = frame_facts(grid)
    messages = []
    if not 2 <= len(facts) <= 3:
        messages.append(f"expected 2..3 closed frames, got {len(facts)}")
    if len(facts) != len(_yellow_components(grid)):
        messages.append("every yellow component must be a complete rectangular border")
    boxes, interiors = set(), set()
    for fact in facts:
        r0, c0, r1, c1 = fact["box"]
        area = {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}
        if boxes & area:
            messages.append("frame rectangles overlap or are nested")
        boxes |= area
        interiors.update(fact["interior"])
        if len(fact["interior"]) < 2:
            messages.append("frame interior needs at least two cells")
        if not 1 <= fact["count"] <= 3:
            messages.append(f"frame needs 1..3 red markers, got {fact['count']}")
        if any(grid[r][c] not in (0,2) for r,c in fact["interior"]):
            messages.append("frame interior must contain only background and red markers")
    if any(v == 2 and (r,c) not in interiors for r,row in enumerate(grid) for c,v in enumerate(row)):
        messages.append("red marker outside all valid frames")
    if any(v in (1,3) for row in grid for v in row):
        messages.append("unexpected non-task color")
    return messages


def strict_canonical_like(grid):
    """Structural task-domain check, not an empirical distribution claim."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_frames": len(frame_facts(grid)),
            "cue_size": sum(v in (5,6,7,8,9) for row in grid for v in row)}


def rule_mirror(grid):
    """Review/testing oracle only; production labels still execute pinned Racket."""
    out = [list(row) for row in grid]
    for fact in frame_facts(grid):
        for r,c in fact["interior"]:
            out[r][c] = 5 + fact["count"]
    return out


def rival_marker_topology(grid):
    """Canonical-fitting rival: cluster ->8, multiple isolated cells ->7, else6."""
    out = [list(row) for row in grid]
    for fact in frame_facts(grid):
        color = 8 if fact["adjacent"] else (7 if fact["count"] >= 2 else 6)
        for r,c in fact["interior"]:
            out[r][c] = color
    return out


def _touching_pair(grid):
    return any(f["count"] == 2 and f["adjacent"] for f in frame_facts(grid))


def _separated_three(grid):
    return any(f["count"] == 3 and not f["adjacent"] for f in frame_facts(grid))


SEMANTIC_RIVALS = {"marker_topology": rival_marker_topology}
CANONICAL_SHORTCUTS = {"marker_topology": rival_marker_topology}
SEMANTIC_WITNESSES = {"touching_pair": _touching_pair, "separated_three": _separated_three}
WITNESS_RIVALS = {name: ["marker_topology"] for name in SEMANTIC_WITNESSES}
