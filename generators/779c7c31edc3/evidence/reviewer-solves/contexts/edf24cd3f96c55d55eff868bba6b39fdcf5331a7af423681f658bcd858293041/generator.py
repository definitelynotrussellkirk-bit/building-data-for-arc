"""Constructive inputs for turning each solid monochrome rectangle into a frame.

Racket remains the label authority. The Python output-producing functions below
are explicitly WRONG rivals, used only to test lesson quality. The three-profile
schedule supplies multi-component, repeated-color and large-interior evidence
in every three consecutive unoverridden draws at a fixed seed and difficulty.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "779c7c31edc3"
TASK_ID = "779c7c31edc3"
RULE_HASH = "8f9e53b42241"
VERSION = "3.0.0"
SUMMARY = (
    "Zero-background grids with 1..4 solid monochrome rectangles, each at least "
    "3x3. Separate components may share a color; different colors may touch. "
    "The unchanged Racket rule preserves each component's one-cell border and "
    "erases its interior. Three-draw lessons mix canonical-scale, repeated-color "
    "and broader scenes, including 5x3 rectangles, edge contact and larger interiors."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "rectangular 0..9 integer grid with literal zero background",
    "every nonzero monochrome 4-connected component is a filled rectangle at least 3x3",
    "same-color rectangles are separated; different-color rectangles may touch",
    "every requested component and foreground color is realized exactly",
]
AXES = {
    "grid_h": {"type": "int", "default": "12 in anchor; 9..18 otherwise", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "12 in anchor; 9..18 otherwise", "valid": "9..18"},
    "rectangles": {"type": "int", "default": "3 in anchor; 1..4 otherwise", "valid": "1..4"},
    "n_distinct_colors": {"type": "int", "default": "1..rectangles; repeat profile uses fewer", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"rectangles": 1, "n_distinct_colors": [2, 3, 4]},
    {"rectangles": 2, "n_distinct_colors": [3, 4]},
    {"rectangles": 3, "n_distinct_colors": 4},
]
# Historical texture/palette aliases were ignored or bypassed validation. They
# are deliberately not advertised or silently accepted in this version.
SCHEDULE_PROFILES = ("anchor", "repeated_color", "broad")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw(ctx, key, defaults, lo, hi):
    """Curriculum changes defaults, never the domain of an explicit control."""
    choices = list(range(lo, hi + 1)) if ctx.overrides.get(key) is not None else list(defaults)
    return ctx.draw_choice(key, choices)


def _segments(length, count, gap, rng, *, balanced=False):
    available = length - gap * (count - 1)
    if available < 3 * count:
        raise ValueError("internal infeasible rectangle partition")
    if balanced:
        sizes = [available // count + (i < available % count) for i in range(count)]
    else:
        sizes = [3] * count
        for _ in range(available - 3 * count):
            sizes[rng.randrange(count)] += 1
    result = []
    offset = 0
    for size in sizes:
        result.append((offset, size))
        offset += size + gap
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for key, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{key} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    anchored = profile == "anchor"
    favored = {None: [12], "easy": [9,10,11], "medium": [11,12,13], "hard": [15,16,17,18]}[difficulty]
    dimensions = [12] if anchored else (list(range(9,19)) + [12] * 18 + favored * 6)
    h = _draw(ctx, "grid_h", dimensions, 9, 18)
    w = _draw(ctx, "grid_w", dimensions, 9, 18)
    requested_colors = overrides.get("n_distinct_colors")
    minimum = max(1, requested_colors or 1)
    defaults = [3] if anchored else ([2,3,4] if profile == "repeated_color" else [1,2,3,4])
    if profile == "broad":
        defaults += [1,2] * 3 if difficulty == "easy" else ([3,4] * 3 if difficulty == "hard" else [2,3] * 3)
    defaults = [n for n in defaults if n >= minimum] or [minimum]
    # Validate before using a supplied color count to construct defaults.
    if requested_colors is not None and not 1 <= requested_colors <= 4:
        raise ValueError("n_distinct_colors must be in 1..4")
    count = _draw(ctx, "rectangles", defaults, 1, 4)
    if requested_colors is not None and requested_colors > count:
        raise ValueError("n_distinct_colors cannot exceed rectangles")
    if anchored:
        color_defaults = [count]
    elif profile == "repeated_color":
        color_defaults = list(range(1, max(2, count)))
    else:
        color_defaults = list(range(1, count + 1))
    color_count = _draw(ctx, "n_distinct_colors", color_defaults, 1, 4)
    rng = ctx.draw_rng("layout")
    # Partitioning guarantees exact counts, unlike the old capped rejection loop.
    repeated = color_count < count
    gap = 1 if repeated or count == 4 else rng.choice((0, 1))
    shapes = [(rr,cc) for rr in range(1,3) for cc in range(1,5)
              if rr*cc >= count and rr*cc <= count+1
              and 3*rr+gap*(rr-1) <= h and 3*cc+gap*(cc-1) <= w]
    rows, cols = (2,2) if anchored and count >= 3 else rng.choice(shapes)
    row_slots = _segments(h, rows, gap, rng, balanced=anchored)
    col_slots = _segments(w, cols, gap, rng, balanced=anchored)
    slots = [(r,c,rh,cw) for r,rh in row_slots for c,cw in col_slots]
    rng.shuffle(slots)
    palette = ctx.draw_rng("palette").sample(list(range(1,10)), color_count)
    colors = palette + [rng.choice(palette) for _ in range(count - color_count)]
    rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for index, (r0,c0,slot_h,slot_w) in enumerate(slots[:count]):
        rh, rw = rng.randint(3, min(7,slot_h)), rng.randint(3, min(7,slot_w))
        if anchored and index == 0 and slot_h >= 5:
            rh, rw = 5, 3
        r0 += rng.randint(0, slot_h-rh)
        c0 += rng.randint(0, slot_w-rw)
        for r in range(r0, r0+rh):
            for c in range(c0, c0+rw):
                grid[r][c] = colors[index]
    return grid


def _regions(grid):
    """Input-only monochrome connectivity analysis; not an output oracle."""
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen:
                continue
            color = grid[r][c]
            pending = [(r,c)]
            seen.add((r,c))
            cells = []
            while pending:
                rr,cc = pending.pop()
                cells.append((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc))
                        pending.append((nr,nc))
            rs, cs = zip(*cells)
            result.append((color,cells,(min(rs),min(cs),max(rs),max(cs))))
    return result


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid,(list,tuple)) or not grid or not isinstance(grid[0],(list,tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row,(list,tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid dimensions exceed 30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9 (booleans are not colors)"]
    if not any(v == 0 for row in grid for v in row):
        return ["literal-zero background is required"]
    regions = _regions(grid)
    if not regions:
        return ["no nonzero rectangle"]
    errors = []
    for color,cells,(r0,c0,r1,c1) in regions:
        rh,rw = r1-r0+1,c1-c0+1
        if len(cells) != rh*rw:
            errors.append(f"color {color} at ({r0},{c0}) is not solid")
        if rh < 3 or rw < 3:
            errors.append(f"rectangle at ({r0},{c0}) is smaller than 3x3")
    return errors


def strict_canonical_like(grid):
    """The rule's solid-rectangle manifold, not literal canonical grid replay."""
    return self_check(grid)


def observe_overrides(grid):
    reasons = self_check(grid)
    if reasons:
        raise ValueError("; ".join(reasons))
    regions = _regions(grid)
    return {"grid_h":len(grid), "grid_w":len(grid[0]), "rectangles":len(regions),
            "n_distinct_colors":len({color for color,_,_ in regions})}


def _one_box_per_color(grid):
    """WRONG rival: merges disconnected same-colored rectangles into one box."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for color in sorted({v for row in grid for v in row} - {0}):
        positions = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color]
        rs,cs = zip(*positions)
        for r in range(min(rs), max(rs)+1):
            for c in range(min(cs), max(cs)+1):
                if r in (min(rs),max(rs)) or c in (min(cs),max(cs)):
                    out[r][c] = color
    return out


def _largest_only(grid):
    """WRONG rival: hollow only the first largest component."""
    out = [list(row) for row in grid]
    regions = _regions(grid)
    if regions:
        _,_,(r0,c0,r1,c1) = max(regions, key=lambda item: len(item[1]))
        for r in range(r0+1,r1):
            for c in range(c0+1,c1):
                out[r][c] = 0
    return out


def _one_center_per_rectangle(grid):
    """WRONG rival: erase one central pixel rather than the whole interior."""
    out = [list(row) for row in grid]
    for _,_,(r0,c0,r1,c1) in _regions(grid):
        out[(r0+r1)//2][(c0+c1)//2] = 0
    return out


def _has_repeated_color(grid):
    regions = _regions(grid)
    return len({color for color,_,_ in regions}) < len(regions)


def _has_multiple_rectangles(grid):
    return len(_regions(grid)) >= 2


def _has_large_interior(grid):
    return any((r1-r0-1)*(c1-c0-1) > 1 for _,_,(r0,c0,r1,c1) in _regions(grid))


SEMANTIC_RIVALS = {
    "one_box_per_color": _one_box_per_color,
    "largest_only": _largest_only,
    "one_center_per_rectangle": _one_center_per_rectangle,
}
SEMANTIC_WITNESSES = {
    "repeated_color": _has_repeated_color,
    "multiple_rectangles": _has_multiple_rectangles,
    "large_interior": _has_large_interior,
}
WITNESS_RIVALS = {
    "repeated_color": ["one_box_per_color"],
    "multiple_rectangles": ["largest_only"],
    "large_interior": ["one_center_per_rectangle"],
}
CANONICAL_SHORTCUTS = {"one_box_per_color": _one_box_per_color}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query):
    """Finite-rival coverage only; makes no universal induction claim."""
    return [f"rival survives all demonstrations: {name}"
            for name,rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
