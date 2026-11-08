"""Largest MC8 object plus residual-cell votes: inputs, never reference labels.

The selected Racket program is unchanged. Python painting below supports named
rivals and witness diagnostics only; exported labels come from Racket. See
notes.md for the sampled envelope and the six-demonstration lesson contract.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "747486860e56"
TASK_ID = GENERATOR_ID
RULE_HASH = "0ab2a183017a"
VERSION = "4.1.0"
SUMMARY = (
    "Preserve the uniquely largest multicolor 8-connected nonzero object. "
    "Every other nonzero cell counts and votes, including small touching groups. "
    "The most frequent residual color wins, with row-major first occurrence "
    "breaking ties. The unique residual corner selects orientation. Erase all "
    "residual cells, then paint a triangle of leg residual-count minus one, "
    "overwriting any overlap with the preserved object."
)
INVARIANTS = [
    "rectangular integer grid, colors 0..9, background 0, dimensions 6..24",
    "one uniquely largest multicolor 8-connected object of at least 4 cells",
    "3..8 residual cells, counted individually regardless of their connectivity",
    "exactly one residual corner; triangle leg fits both canvas dimensions",
    "pluralities and row-major ties are legal; corner and object colors may vote",
]
CORNERS = ("tl", "tr", "bl", "br")
AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles plus 6..24", "valid": "6..24"},
    "grid_w": {"type": "int", "default": "canonical profiles plus 6..24", "valid": "6..24"},
    "corner": {"type": "str", "default": "uniform", "valid": "tl|tr|bl|br"},
    "n_markers": {"type": "int", "default": "corner vote: 3,5,6,7; tied votes: 6", "valid": "3..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": 6, "n_markers": 8},
    {"grid_w": 6, "n_markers": 8},
]
EXAMPLES_NEEDED = 6
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("corner_vote", "tie_low", "tie_high")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _lesson_context(seed):
    # The public materializer keeps one seed throughout an episode. These two
    # independent family choices prevent object palette from revealing voting
    # roles, while mono-only/neutral episodes keep the same law on every query.
    rng = stable_rng(seed, TASK_ID + "|lesson_context", VERSION)
    return rng.choice((False, True)), rng.choice((False, True))


def _components(grid, *, univalued=False):
    return [{pos for _, pos in obj} for obj in
            find_objects(grid, bg=0, diagonal=True, univalued=univalued)]


def _scene(grid, *, univalued=False):
    components = _components(grid, univalued=univalued)
    main = max(components, key=len) if components else set()
    residual = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                if v != 0 and (r, c) not in main]
    h, w = len(grid), len(grid[0])
    corners = {(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)}
    corner = next((p for p in residual if p in corners), None)
    return main, residual, corner


def _winner(grid, cells, *, tie="first"):
    counts = Counter(grid[r][c] for r, c in cells)
    if not counts:
        return None
    maximum = max(counts.values())
    tied = [color for color, count in counts.items() if count == maximum]
    if tie == "max":
        return max(tied)
    if tie == "min":
        return min(tied)
    return tied[0]  # cells are row-major; Counter preserves first occurrence


def _triangle(h, w, corner, leg):
    cr, cc = corner
    return {(i if cr == 0 else h-1-i, j if cc == 0 else w-1-j)
            for i in range(min(leg, h)) for j in range(min(leg-i, w))}


def _diagnostic_prediction(grid, *, univalued=False, exclude_corner=False,
                           preserve_last=False, tie="first", correlated=False):
    """Python diagnostic model; this is not the label authority."""
    main, residual, corner = _scene(grid, univalued=univalued)
    if not residual or corner is None:
        return [list(row) for row in grid]
    voters = [p for p in residual if p != corner] if exclude_corner else residual
    color = _winner(grid, voters, tie=tie)
    if correlated:
        pick = corner if len({grid[r][c] for r, c in main}) == 1 else residual[0]
        color = grid[pick[0]][pick[1]]
    if color is None:
        return [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    tri = _triangle(h, w, corner, len(residual)-1)
    out = full_grid(h, w, 0)
    for r, c in main:
        out[r][c] = grid[r][c]
    for r, c in tri:
        out[r][c] = color
    if preserve_last:
        for r, c in main:
            out[r][c] = grid[r][c]
    return out


def _without_corner_vote(grid):
    return _diagnostic_prediction(grid, exclude_corner=True)


def _monochrome_main(grid):
    return _diagnostic_prediction(grid, univalued=True)


def _preserve_on_top(grid):
    return _diagnostic_prediction(grid, preserve_last=True)


def _largest_color_tie(grid):
    return _diagnostic_prediction(grid, tie="max")


def _smallest_color_tie(grid):
    return _diagnostic_prediction(grid, tie="min")


def _correlated_shortcut(grid):
    return _diagnostic_prediction(grid, correlated=True)


def _corner_votes(grid):
    return _without_corner_vote(grid) != _diagnostic_prediction(grid)


def _multicolor_matters(grid):
    return _monochrome_main(grid) != _diagnostic_prediction(grid)


def _overlap_matters(grid):
    main, residual, corner = _scene(grid)
    if not residual or corner is None:
        return False
    color = _winner(grid, residual)
    return any(grid[r][c] != color for r, c in
               main & _triangle(len(grid), len(grid[0]), corner, len(residual)-1))


def _max_tie_wrong(grid):
    return _largest_color_tie(grid) != _diagnostic_prediction(grid)


def _min_tie_wrong(grid):
    return _smallest_color_tie(grid) != _diagnostic_prediction(grid)


def _correlation_matters(grid):
    return _correlated_shortcut(grid) != _diagnostic_prediction(grid)


SEMANTIC_RIVALS = {
    "exclude_corner_vote": _without_corner_vote,
    "monochrome_main": _monochrome_main,
    "preserve_on_top": _preserve_on_top,
    "largest_color_tie": _largest_color_tie,
    "smallest_color_tie": _smallest_color_tie,
    "monochrome_corner_else_first": _correlated_shortcut,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("exclude_corner_vote", "monochrome_main",
                        "preserve_on_top", "largest_color_tie")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "corner_vote_changes_winner": _corner_votes,
    "multicolor_component_matters": _multicolor_matters,
    "triangle_overwrites_pattern": _overlap_matters,
    "row_major_beats_max_color": _max_tie_wrong,
    "row_major_beats_min_color": _min_tie_wrong,
    "object_palette_does_not_choose_color": _correlation_matters,
}
WITNESS_RIVALS = {
    "corner_vote_changes_winner": ["exclude_corner_vote"],
    "multicolor_component_matters": ["monochrome_main"],
    "triangle_overwrites_pattern": ["preserve_on_top"],
    "row_major_beats_max_color": ["largest_color_tie"],
    "row_major_beats_min_color": ["smallest_color_tie"],
    "object_palette_does_not_choose_color": ["monochrome_corner_else_first"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival condition; not a claim of unique induction."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def self_check(grid, *, difficulty=None, meta=None):
    # Metadata never bypasses the pixel-domain check.
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty grid rows"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged or non-sequence row"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    h = len(grid)
    if not (6 <= h <= 24 and 6 <= w <= 24):
        return ["sampler domain requires dimensions 6..24"]
    components = _components(grid)
    if not components:
        return ["no nonzero object or residual cells"]
    sizes = sorted((len(obj) for obj in components), reverse=True)
    if sizes[0] < 4 or (len(sizes) > 1 and sizes[0] == sizes[1]):
        return ["expected a uniquely largest MC8 object of at least 4 cells"]
    _, residual, corner = _scene(grid)
    errors = []
    if not 3 <= len(residual) <= 8:
        errors.append(f"expected 3..8 residual cells, found {len(residual)}")
    corners = {(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)}
    if sum(p in corners for p in residual) != 1:
        errors.append("expected exactly one residual corner")
    if len(residual)-1 > min(h, w):
        errors.append("triangle leg exceeds canvas dimensions")
    return errors


def strict_canonical_like(grid):
    """Lawful declared rule envelope, including documented MC8/overlap extensions."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    _, residual, corner = _scene(grid)
    h, w = len(grid), len(grid[0])
    corner_names = {(0, 0): "tl", (0, w-1): "tr", (h-1, 0): "bl", (h-1, w-1): "br"}
    return {"grid_h": h, "grid_w": w, "corner": corner_names[corner],
            "n_markers": len(residual)}


def _global(point, h, w, corner):
    r, c = point
    return (r if corner[0] == "t" else h-1-r,
            c if corner[1] == "l" else w-1-c)


def _pattern(rng, h, w, corner, count, leg, overlap):
    corners = {(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)}
    allowed = {(r, c) for r in range(h) for c in range(w)
               if (r, c) not in corners and not (r <= 1 and c <= 1)
               and (overlap or r+c >= leg)}
    start = (0, 2) if overlap else rng.choice(sorted(allowed))
    cells = {start}
    # Seed diagonal connections as well as growing branches/cardinal runs.
    diagonal = (start[0]+1, start[1]+1)
    if diagonal in allowed and count >= 2:
        cells.add(diagonal)
    while len(cells) < count:
        frontier = sorted({(r+dr, c+dc) for r, c in cells
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                           if (dr or dc) and (r+dr, c+dc) in allowed} - cells)
        if not frontier:
            return None
        cells.add(rng.choice(frontier))
    return {_global(p, h, w, corner) for p in cells}


def _marker_positions(rng, h, w, main, corner, count, contact):
    all_corners = {(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)}
    halo = {(r+dr, c+dc) for r, c in main
            for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
    if corner in halo:
        return None
    free = [(r, c) for r in range(h) for c in range(w)
            if (r, c) not in halo and (r, c) not in all_corners]
    if len(free) < count-1:
        return None
    chosen = [corner]
    if contact and count >= 3:
        available = set(free)
        pairs = [(p, (p[0]+dr, p[1]+dc)) for p in free
                 for dr, dc in ((0, 1), (1, -1), (1, 0), (1, 1))
                 if (p[0]+dr, p[1]+dc) in available]
        if not pairs:
            return None
        chosen.extend(rng.choice(pairs))
    remaining = [p for p in free if p not in chosen]
    chosen.extend(rng.sample(remaining, count-len(chosen)))
    return sorted(chosen)


def _paint_markers(rng, grid, positions, corner, palette, profile, critical):
    count = len(positions)
    if profile == "corner_vote":
        a, b = palette[:2]
        counts = (Counter({a: count//2+1, b: count//2}) if count % 2 else
                  Counter([a, a] + palette[1:count-1]))
        corner_color = a if critical else b
        grid[corner[0]][corner[1]] = corner_color
        counts[corner_color] -= 1
        others = [p for p in positions if p != corner]
        # Critical families need a losing color first after removing the corner.
        # Neutral families instead teach that the corner may have a losing role.
        first = next((color for color in palette[1:] if counts[color]), a)
        colors = [first]
        counts[first] -= 1
        tail = list(counts.elements())
        rng.shuffle(tail)
        colors.extend(tail)
        for (r, c), color in zip(others, colors):
            grid[r][c] = color
        return a
    tied = sorted(palette[:2])
    a, b = tied if profile == "tie_low" else tied[::-1]
    if count == 3:
        tied = sorted(palette[:3])
        a = tied[0] if profile == "tie_low" else tied[-1]
        colors = [a] + [v for v in tied if v != a]
    elif count == 4:
        colors = [a, a, b, b] + palette[2:count-2]
        tail = colors[1:]
        rng.shuffle(tail)
        colors = [a] + tail
    else:
        # Default six-cell scenes begin with a losing singleton and give the
        # corner a losing role too. The winner is the first TIED color, which
        # is deliberately not the first residual color. This breaks v4.0's
        # palette/role shortcut in both mono and multicolor families.
        extras = palette[2:count-2]
        assigned = {corner: extras[0]}
        if positions[0] != corner and len(extras) > 1:
            assigned[positions[0]] = extras[1]
        used = set(assigned.values())
        tail = [a, b, b] + [color for color in extras if color not in used]
        rng.shuffle(tail)
        colors = iter([a] + tail)
        for r, c in positions:
            grid[r][c] = assigned[(r, c)] if (r, c) in assigned else next(colors)
        return a
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    return a


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_markers"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} requires an integer, not {type(value).__name__}")
        low, high = (3, 8) if name == "n_markers" else (6, 24)
        if value is not None and not low <= value <= high:
            raise ValueError(f"{name} outside {low}..{high}")
    if overrides.get("corner") is not None and overrides["corner"] not in CORNERS:
        raise ValueError("corner must be tl, tr, bl, or br")
    for dimension in ("grid_h", "grid_w"):
        if overrides.get(dimension) == 6 and overrides.get("n_markers") == 8:
            raise ValueError(f"incompatible {dimension}=6 and n_markers=8: triangle leg is 7")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    multicolor, critical = _lesson_context(seed)
    profile = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("n_markers") is not None:
        count = ctx.draw_int_strict("n_markers", 3, 8)
    else:
        count = ctx.draw_choice("n_markers", (3, 5, 6, 7) if profile == "corner_vote" else (6,))
    # Linked canonical (height,width,palette-size) profiles, with broad support
    # in every band. Shapes, positions and colors are freshly drawn, never copied.
    palette_four = profile == "corner_vote" and count % 2 == 1
    profiles = ((6, 9), (15, 14)) if palette_four else ((11, 11), (10, 10), (12, 11))
    target_h, target_w = rng.choice(profiles)
    lo = max(6, count-1)
    h = ctx.draw_choice("grid_h", list(range(lo, 25)) + [max(lo, target_h)]*100)
    w = ctx.draw_choice("grid_w", list(range(lo, 25)) + [max(lo, target_w)]*100)
    corner_name = ctx.draw_choice("corner", CORNERS)
    corner = _global((0, 0), h, w, corner_name)
    overlap = profile != "corner_vote" and count >= 4
    palette = rng.sample(list(range(1, 10)), 9)
    if profile == "corner_vote":
        pattern_colors = [palette[2], palette[1]] if count % 2 else palette[1:3]
    else:
        # Reuse one residual color in a multicolor main object, but retain a
        # distinct base color so actual default palette size is exactly six.
        residual_colors = 3 if count == 3 else count-2
        pattern_colors = [palette[residual_colors], palette[residual_colors-1]]
    if not multicolor:
        pattern_colors = pattern_colors[:1]
    sizes = [5, 7, 9, 11, 15]
    if difficulty == "easy":
        sizes += [5, 7]*3
    elif difficulty == "hard":
        sizes += [11, 15]*3
    for _ in range(240):
        size = min(rng.choice(sizes), max(5, h*w//4))
        main = _pattern(rng, h, w, corner_name, size, count-1, overlap)
        if main is None:
            continue
        positions = _marker_positions(rng, h, w, main, corner, count, overlap)
        if positions is None:
            continue
        grid = full_grid(h, w, 0)
        for i, (r, c) in enumerate(sorted(main)):
            grid[r][c] = pattern_colors[i % len(pattern_colors)]
        if overlap:
            r, c = _global((0, 2), h, w, corner_name)
            grid[r][c] = pattern_colors[0]
        _paint_markers(rng, grid, positions, corner, palette, profile, critical)
        selected_main, residual, _ = _scene(grid)
        if selected_main != main or len(residual) != count:
            continue
        if self_check(grid):
            continue
        if profile == "corner_vote" and critical and not _corner_votes(grid):
            continue
        if overlap and not _overlap_matters(grid):
            continue
        if multicolor and not _multicolor_matters(grid):
            continue
        return grid
    raise RuntimeError("could not realize the declared MC8/residual-cell layout")
