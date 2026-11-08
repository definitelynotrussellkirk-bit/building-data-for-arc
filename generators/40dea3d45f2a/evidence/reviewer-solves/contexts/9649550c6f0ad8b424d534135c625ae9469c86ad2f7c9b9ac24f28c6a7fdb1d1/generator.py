"""Four fixed panels; teach binary shape equivalence under the full D4 group.

The unchanged Racket authority supplies labels. This module samples inputs and
exposes falsifiable rival/witness hooks; it never labels a training example.
Every three consecutive default draws contain a same-area, same-bounding-box
negative and a reflection-only positive. Other draws cover all 15 partitions.
"""
from __future__ import annotations

from functools import lru_cache
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40dea3d45f2a"
TASK_ID = "40dea3d45f2a"
VERSION = "3.0.0"
RULE_HASH = "d5ddd0abae4d"
SUMMARY = "D4-equivalence matrix of four binary panel shapes, with equal-area hard negatives and reflected positives."
EXPECTED_OUTPUT_CODOMAIN = 15  # Bell(4): all equivalence relations on four panels.
SOLID_OUTPUT_JUSTIFICATION = (
    "A 4x4 all-8 matrix is the lawful one-block equivalence relation: all four "
    "nonempty panels have the same shape up to D4. It is only one of 15 output "
    "partitions, and every default three-demo window also has a nontrivial "
    "same-area negative. See the retained Racket cases and lesson census."
)
INVARIANTS = [
    "9x9 grid with zero separator row and column at index 4",
    "four 4x4 panels at (0,0), (0,5), (5,0), (5,5)",
    "ordinary samples have connected monochrome shapes with 3..8 cells",
    "shape classes are distinct under D4, not under a cell-count proxy",
    "panel colors, within-panel translations, and ordering do not encode classes",
]
AXES = {
    "grid_h": {"type": "int", "default": "9", "valid": "9", "probe": "diagnostic"},
    "grid_w": {"type": "int", "default": "9", "valid": "9", "probe": "diagnostic"},
    "n_classes": {"type": "int", "default": "2 in teaching profile; broad partitions otherwise", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "2..3 in teaching profile; 1..4 otherwise", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("teaching", "broad")
_STARTS = ((0, 0), (0, 5), (5, 0), (5, 5))
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells):
    if not cells:
        return ()
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return tuple(sorted((r-rmin, c-cmin) for r, c in cells))


def _dihedral(cells, transform):
    points = tuple(cells)
    if transform >= 4:
        points = tuple((r, -c) for r, c in points)
    for _ in range(transform % 4):
        points = tuple((c, -r) for r, c in points)
    return _norm(points)


def _key(cells):
    return min(_dihedral(cells, t) for t in range(8))


def _rot_key(cells):
    return min(_dihedral(cells, t) for t in range(4))


def _extent(cells):
    if not cells:
        return (0, 0)
    return tuple(sorted((max(r for r,c in cells)+1, max(c for r,c in cells)+1)))


@lru_cache(maxsize=1)
def _banks():
    """Finite constructive growth: all free polyominoes fitting a 4x4 panel.

    Negative growth coordinates are normalized before the bounding-box check;
    no seed-dependent retries, clipping, or disconnected accidental motifs.
    """
    bank = {1: (((0, 0),),)}
    for size in range(2, 9):
        shapes = set()
        for cells in bank[size-1]:
            occupied = set(cells)
            for r, c in cells:
                for dr, dc in _CARD:
                    q = (r+dr, c+dc)
                    if q in occupied:
                        continue
                    grown = _norm(occupied | {q})
                    if max(_extent(grown)) <= 4:
                        shapes.add(_key(grown))
        bank[size] = tuple(sorted(shapes))
    return bank


@lru_cache(maxsize=6)
def _teaching_pairs(size):
    shapes = _banks()[size]
    return tuple((a,b) for a in shapes
                 if _rot_key(a) != _rot_key(_dihedral(a,4))
                 for b in shapes if a != b and _extent(a) == _extent(b))


def _partitions():
    result = []
    def visit(cur):
        if len(cur) == 4:
            result.append(tuple(cur))
            return
        for label in range(max(cur, default=-1)+2):
            visit(cur+[label])
    visit([])
    return tuple(result)


_PARTITIONS = _partitions()


def schedule_profile(seed, sample_index, difficulty=None):
    return "teaching" if (int(seed)+int(sample_index)) % 3 == 0 else "broad"


def _control(ctx, key, default, lo, hi):
    value = ctx.overrides.get(key, default)
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{key} must be an integer in [{lo}, {hi}], got {value!r}")
    # Derived curriculum values still use named, fixed-range public draws.
    # This records the actual realized control without silently clamping it.
    return ctx.draw_int(key, value, value)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    _control(ctx, "grid_h", 9, 9, 9)
    _control(ctx, "grid_w", 9, 9, 9)
    rng = ctx.draw_rng("layout")
    teaching = schedule_profile(seed, sample_index, difficulty) == "teaching"
    default_partition = (0,0,1,1) if teaching else rng.choice(_PARTITIONS)
    n_classes = _control(ctx, "n_classes", len(set(default_partition)), 1, 4)
    palette_size = _control(ctx, "palette_size",
                            rng.choice((2,3) if teaching else (1,2,3,4)), 1, 4)
    palette = rng.sample(list(range(1,10)), palette_size)
    # Exact caller controls remain authoritative; the default teaching promise
    # deliberately does not claim to cover a pinned all-equivalent partition.
    teaching = teaching and n_classes == 2
    size_options = {"easy": (4,5), "medium": (5,6,7), "hard": (6,7,8)}
    if teaching:
        size = rng.choice(size_options.get(difficulty, (4,5,6,7,8)))
        a,b = rng.choice(_teaching_pairs(size))
        transform = rng.randrange(4)
        cells = [_dihedral(a,transform), _dihedral(a,transform+4),
                 _dihedral(b,rng.randrange(8)), _dihedral(b,rng.randrange(8))]
        if palette_size == 4:
            colors = palette[:]
        else:
            colors = [palette[0],palette[min(1,palette_size-1)],palette[0],palette[-1]]
    else:
        matching = [p for p in _PARTITIONS if len(set(p)) == n_classes]
        partition = rng.choice(matching)
        sizes = {"easy": (3,4,5), "medium": (4,5,6,7), "hard": (5,6,7,8)}.get(difficulty,(3,4,5,6,7,8))
        candidates = [s for k in sizes for s in _banks()[k]]
        # Each bank entry is its own D4 representative; sampling without
        # replacement permits equal areas but cannot merge two named classes.
        bases = rng.sample(candidates,n_classes)
        cells = [_dihedral(bases[label],rng.randrange(8)) for label in partition]
        colors = palette[:] + [rng.choice(palette) for _ in range(4-palette_size)]
        rng.shuffle(colors)
    panel_items = list(zip(cells,colors))
    rng.shuffle(panel_items)
    grid = full_grid(9,9,0)
    for (r0,c0),(shape,color) in zip(_STARTS,panel_items):
        height = max(r for r,c in shape)+1
        width = max(c for r,c in shape)+1
        top,left = rng.randrange(5-height),rng.randrange(5-width)
        for r,c in shape:
            grid[r0+top+r][c0+left+c] = color
    return grid


def _panel_cells(grid):
    return [tuple((r,c) for r in range(4) for c in range(4) if grid[r0+r][c0+c])
            for r0,c0 in _STARTS]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the rule's fixed-panel input domain, not a diversity proxy.

    Require four visible nonempty shapes, as in every canonical input.
    Multicolored, disconnected, and all-equivalent panels remain admissible;
    the ordinary sampler uses connected monochrome shapes. The total Racket
    function also handles empty panels, outside this declared input domain.
    """
    if not isinstance(grid,(list,tuple)) or len(grid) != 9:
        return ["grid must have 9 rows"]
    if any(not isinstance(row,(list,tuple)) or len(row) != 9 for row in grid):
        return ["grid must be rectangular and 9x9"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    if any(grid[4][i] or grid[i][4] for i in range(9)):
        return ["separator row and column must be zero"]
    if any(not cells for cells in _panel_cells(grid)):
        return ["each of the four panels must contain a visible shape"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    for (r0,c0),cells in zip(_STARTS,_panel_cells(grid)):
        if not 3 <= len(cells) <= 8:
            return ["canonical-profile shapes have 3..8 cells"]
        if len({grid[r0+r][c0+c] for r,c in cells}) != 1:
            return ["canonical-profile panels are monochrome"]
        reached = {cells[0]}
        todo = [cells[0]]
        occupied = set(cells)
        while todo:
            r,c = todo.pop()
            for dr,dc in _CARD:
                q=(r+dr,c+dc)
                if q in occupied and q not in reached:
                    reached.add(q); todo.append(q)
        if reached != occupied:
            return ["canonical-profile shapes are four-connected"]
    return []


def observe_overrides(grid):
    return {"grid_h":len(grid), "grid_w":len(grid[0]),
            "n_classes":len({_key(s) for s in _panel_cells(grid)}),
            "palette_size":len({v for row in grid for v in row if v})}


def _relation(features):
    return [[8 if a == b else 0 for b in features] for a in features]


def _count_only(grid):
    return _relation([len(s) for s in _panel_cells(grid)])


def _bbox_only(grid):
    return _relation([_extent(_norm(s)) for s in _panel_cells(grid)])


def _rotations_only(grid):
    return _relation([_rot_key(s) for s in _panel_cells(grid)])


def _exact_crop_only(grid):
    return _relation([_norm(s) for s in _panel_cells(grid)])


def _color_only(grid):
    return _relation([tuple(sorted({grid[r0+r][c0+c] for r,c in cells}))
                      for (r0,c0),cells in zip(_STARTS,_panel_cells(grid))])


def _same_area_negative(grid):
    cells = _panel_cells(grid)
    return any(len(a)==len(b) and _key(a)!=_key(b) for a in cells for b in cells)


def _same_box_negative(grid):
    cells = [_norm(s) for s in _panel_cells(grid)]
    return any(_extent(a)==_extent(b) and _key(a)!=_key(b) for a in cells for b in cells)


def _reflection_positive(grid):
    cells = _panel_cells(grid)
    return any(_key(a)==_key(b) and _rot_key(a)!=_rot_key(b) for a in cells for b in cells)


def _color_decoupled(grid):
    return _color_only(grid) != _relation([_key(s) for s in _panel_cells(grid)])


SEMANTIC_WITNESSES = {
    "same_area_negative":_same_area_negative,
    "same_box_negative":_same_box_negative,
    "reflection_positive":_reflection_positive,
    "color_decoupled":_color_decoupled,
}
SEMANTIC_RIVALS = {
    "count_only":_count_only, "bbox_only":_bbox_only,
    "rotations_only":_rotations_only, "exact_crop_only":_exact_crop_only,
    "color_only":_color_only,
}
WITNESS_RIVALS = {
    "same_area_negative":["count_only"],
    "same_box_negative":["bbox_only"],
    "reflection_positive":["rotations_only","exact_crop_only"],
    "color_decoupled":["color_only"],
}
CANONICAL_SHORTCUTS = {"count_only":_count_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival test only, never a universal induction claim."""
    return [f"rival survives all demos: {name}"
            for name,rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
