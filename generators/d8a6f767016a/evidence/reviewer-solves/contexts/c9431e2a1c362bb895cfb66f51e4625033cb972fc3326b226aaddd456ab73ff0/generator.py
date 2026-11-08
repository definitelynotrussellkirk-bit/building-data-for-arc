"""Generator for ARC task d8a6f767016a.

For every 4-connected color-8 object, count the enclosed 0-regions inside
that object's own bounding box and recolor the whole object by
1->1, 2->3, 3->2, 4->4; every other count stays color 8.

The four-sample curriculum deliberately overlaps object-size ranges.  Every
ordinary input contains a 14-cell one-hole frame, which refutes the strongest
training-demo shortcut: classifying objects only by their number of 8-cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d8a6f767016a"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "feb6e892870b"
SUMMARY = (
    "Separated color-8 objects are recolored by their enclosed 0-region count: "
    "1->1, 2->3, 3->2, 4->4, else stays 8. Every lesson includes component-size "
    "counterexamples and cycles through counts 2, 3, 4, and 0."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "inputs use only colors 0 and 8, with 0 as strict modal background",
    "at least two 4-connected color-8 objects are separated by a full 0 ring",
    "every object has at least 8 cells and encloses at most 6 zero-regions",
    "every ordinary draw contains a 14-cell one-hole frame that defeats the canonical-demo size shortcut",
]

# Only controls that are exact for every accepted combination are public.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled by band", "valid": "9..16"},
    "grid_w": {"type": "int", "default": "scheduled by band", "valid": "11..18"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = ("count_2", "count_3", "count_4", "else_0")
_BAND_SIZES = {
    "easy": ((9, 11), (10, 13), (11, 14), (12, 15)),
    "medium": ((14, 11), (14, 14), (13, 15), (12, 16)),
    "hard": ((15, 14), (15, 17), (16, 18), (14, 14)),
}
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _copy_grid(grid):
    return [list(row) for row in grid]


def _objects4(grid):
    """Maximal 4-connected nonzero components as lists of global cells."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            seen[r][c] = True
            stack = [(r, c)]
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != 0):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _enclosed_regions(cells):
    """Return the enclosed 0-components in an object's local bounding box."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    hh, ww = r1 - r0 + 1, c1 - c0 + 1
    solid = {(r - r0, c - c0) for r, c in cells}
    exterior = set()
    stack = []
    for r in range(hh):
        for c in range(ww):
            if (r in (0, hh - 1) or c in (0, ww - 1)) and (r, c) not in solid:
                exterior.add((r, c))
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        for dr, dc in _DIRS4:
            nxt = (r + dr, c + dc)
            if (0 <= nxt[0] < hh and 0 <= nxt[1] < ww
                    and nxt not in solid and nxt not in exterior):
                exterior.add(nxt)
                stack.append(nxt)
    remaining = {
        (r, c) for r in range(hh) for c in range(ww)
        if (r, c) not in solid and (r, c) not in exterior
    }
    regions = []
    while remaining:
        first = remaining.pop()
        region = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in _DIRS4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    region.add(nxt)
                    stack.append(nxt)
        regions.append(region)
    return regions


def _count_holes(cells):
    return len(_enclosed_regions(cells))


def _color_for_holes(count):
    return {1: 1, 2: 3, 3: 2, 4: 4}.get(count, 8)


def rule_mirror(grid):
    """Independent Python mirror used only by tests and semantic diagnostics."""
    out = _copy_grid(grid)
    for cells in _objects4(grid):
        color = _color_for_holes(_count_holes(cells))
        for r, c in cells:
            out[r][c] = color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors = []
    if not (9 <= h <= 16 and 11 <= w <= 18):
        errors.append(f"grid shape {h}x{w} outside 9..16 by 11..18")
    flat = [value for row in grid for value in row]
    if any(type(value) is not int or value not in (0, 8) for value in flat):
        errors.append("input cells must be integer colors 0 or 8")
        return errors
    if 0 not in flat:
        errors.append("missing background color 0")
    if 8 not in flat:
        errors.append("missing color-8 objects")
    if flat.count(0) <= flat.count(8):
        errors.append("background 0 must be strictly modal")

    components = _objects4(grid)
    if len(components) < 2:
        errors.append("need at least two separated color-8 objects")
    occupied = {}
    for index, cells in enumerate(components):
        if len(cells) < 8:
            errors.append(f"undersized object ({len(cells)} cells) at {cells[0]}")
        holes = _count_holes(cells)
        if holes > 6:
            errors.append(f"object at {cells[0]} encloses {holes} regions (>6)")
        for cell in cells:
            occupied[cell] = index
    for (r, c), index in occupied.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                other = occupied.get((r + dr, c + dc))
                if other is not None and other != index:
                    errors.append(f"objects {index} and {other} violate full 0-ring separation")
                    return errors
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _ring_cells(height, width):
    return {
        (r, c) for r in range(height) for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    }


def _solid_cells(height, width):
    return {(r, c) for r in range(height) for c in range(width)}


def _line_chambers(count, *, vertical=False):
    """Compact rectangle split into `count` singleton chambers."""
    height, width = (2 * count + 1, 3) if vertical else (3, 2 * count + 1)
    cells = _ring_cells(height, width)
    if vertical:
        for r in range(2, height - 1, 2):
            cells.add((r, 1))
    else:
        for c in range(2, width - 1, 2):
            cells.add((1, c))
    return cells


def _four_chambers(*, cross):
    if not cross:
        return _line_chambers(4, vertical=False)
    cells = _ring_cells(5, 5)
    for r in range(1, 4):
        cells.add((r, 2))
    for c in range(1, 4):
        cells.add((2, c))
    return cells


def _bbox(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _transpose(cells):
    return {(c, r) for r, c in cells}


def _placement_candidates(rng, h, w, cells):
    oh, ow = _bbox(cells)
    positions = [(r, c) for r in range(h - oh + 1) for c in range(w - ow + 1)]
    rng.shuffle(positions)
    return positions


def _place_objects(rng, h, w, specs):
    """Backtracking packer with Chebyshev distance >=2 between components."""
    ordered = sorted((set(cells) for cells in specs), key=lambda x: -(_bbox(x)[0] * _bbox(x)[1]))
    if sum(len(cells) for cells in ordered) * 2 >= h * w:
        return None
    occupied = set()
    placed = []

    def search(index):
        if index == len(ordered):
            return True
        cells = ordered[index]
        for r0, c0 in _placement_candidates(rng, h, w, cells):
            shifted = {(r + r0, c + c0) for r, c in cells}
            if any((r + dr, c + dc) in occupied
                   for r, c in shifted for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
                continue
            occupied.update(shifted)
            placed.append(shifted)
            if search(index + 1):
                return True
            placed.pop()
            occupied.difference_update(shifted)
        return False

    if not search(0):
        return None
    grid = full_grid(h, w, 0)
    for cells in placed:
        for r, c in cells:
            grid[r][c] = 8
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_shape(sample_index, band):
    sizes = _BAND_SIZES[band]
    return sizes[sample_index % len(sizes)]


def _draw_dimension(ctx, overrides, name, scheduled, lo, hi):
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, [scheduled])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    band = difficulty or "medium"
    if band not in _BAND_SIZES:
        raise ValueError(f"difficulty must be easy, medium, or hard, got {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    scheduled_h, scheduled_w = _scheduled_shape(sample_index, band)
    h = _draw_dimension(ctx, overrides, "grid_h", scheduled_h, 9, 16)
    w = _draw_dimension(ctx, overrides, "grid_w", scheduled_w, 11, 18)
    rng = ctx.draw_rng("layout")

    # 14 cells and one hole: canonical-demo size bins predict color 3, while
    # the intended topology rule predicts color 1. This is mandatory per draw.
    # Orientations are selected jointly with the companion so every advertised
    # canvas remains constructive (notably 9x11 with a four-hole object).
    witnesses = [_ring_cells(rh, rw) for rh, rw in ((4, 5), (5, 4), (3, 6), (6, 3))]
    rng.shuffle(witnesses)

    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "count_2":
        companions = [_line_chambers(2, vertical=False), _line_chambers(2, vertical=True)]
    elif profile == "count_3":
        companions = [_line_chambers(3, vertical=False), _line_chambers(3, vertical=True)]
    elif profile == "count_4":
        companions = [
            _line_chambers(4, vertical=False),
            _line_chambers(4, vertical=True),
            _four_chambers(cross=True),
        ]
    else:
        companions = [_solid_cells(3, 3)]
    rng.shuffle(companions)

    # A compact third object keeps object multiplicity close to the canonical
    # 3-4 object scenes without becoming an exact public override. Try every
    # orientation pair before dropping only this optional extra object.
    extra = _ring_cells(3, 3)
    for include_extra in (True, False):
        for witness in witnesses:
            for companion in companions:
                specs = [witness, companion, extra] if include_extra else [witness, companion]
                grid = _place_objects(rng, h, w, specs)
                if grid is not None:
                    return grid
    raise RuntimeError(f"constructive placement failed for lawful {h}x{w} profile {profile}")


def _rival_canonical_size_bins(grid):
    """Plausible shortcut fitting every visible canonical training object.

    The four demonstrations separate component sizes perfectly:
      8..12 -> 1, 13..17 -> 3, 18..25 -> 2, 26+ -> 4.
    It never inspects enclosed regions and fails on a 14-cell one-hole frame.
    """
    out = _copy_grid(grid)
    for cells in _objects4(grid):
        size = len(cells)
        color = 1 if size <= 12 else 3 if size <= 17 else 2 if size <= 25 else 4
        for r, c in cells:
            out[r][c] = color
    return out


def _witness_size_shortcut_counterexample(grid):
    try:
        return _rival_canonical_size_bins(grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "component_size_overlap": _witness_size_shortcut_counterexample,
}
SEMANTIC_RIVALS = {
    "canonical_demo_component_size_bins": _rival_canonical_size_bins,
}
WITNESS_RIVALS = {
    "component_size_overlap": ["canonical_demo_component_size_bins"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The shortcut fits the visible demonstrations but is already refuted by the
# labelled canonical test pair, so it is intentionally not claimed here.
CANONICAL_SHORTCUTS = {}


def lesson_identifiable(demos, query):
    reasons = []
    for index, demo in enumerate(demos):
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with enclosed-region rule")
    query_expected = rule_mirror(query["input"])
    if query_expected != query["output"]:
        reasons.append("query output disagrees with enclosed-region rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_expected:
            reasons.append(f"competing rule {name!r} fits every demo but answers query differently")
    return reasons
