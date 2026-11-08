"""Complete the sole sparse color-6 component's bounding box; erase all else.

Default samples follow an eight-residue curriculum with four canonical core slots and
four scenes with varied object ranks. Exact overrides select a compact
constructive population; they preserve the domain but narrow lesson witnesses.
"""
from __future__ import annotations

from functools import partial
from fractions import Fraction

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "f9cd85012aa8"
VERSION = "3.1.0"
RULE_HASH = "35becc0ed855"
SUMMARY = "Complete the sole connected sparse color-6 component to its solid bounding box and erase every distractor."
INVARIANTS = ["background is 0", "exactly one 4-connected sparse color-6 component",
              "legal integer colors 0..9", "distinct distractor colors, isolated from color 6 at 8-neighbor distance"]
EXAMPLES_NEEDED = 7
LESSON_SCHEDULE_PERIOD = 8
AXES = {
    "grid_h": {"type": "int", "default": "canonical 7/8/9 or broad 17..20 by difficulty", "valid": "5..20"},
    "grid_w": {"type": "int", "default": "canonical 8/9/10 or broad 6..12 by difficulty", "valid": "6..24"},
    "shape_size": {"type": "int", "default": "canonical 4/5 or broad 7..10", "valid": "3..10"},
    "n_distractor": {"type": "int", "default": "canonical 0 or broad 2", "valid": "0..4"},
}
_BOUNDS = {"grid_h": (5, 20), "grid_w": (6, 24), "shape_size": (3, 10), "n_distractor": (0, 4)}
_CANONICAL = ((7, 8, 4), (8, 9, 4), (9, 10, 5))
_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _bbox(cells):
    return (max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
            max(c for _, c in cells) - min(c for _, c in cells) + 1)


def _normalize(cells):
    mr, mc = min(r for r, _ in cells), min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _bounded_poly(rng, size, h, w):
    """An L backbone pins all bbox edges; growth keeps the exact cell count."""
    if not h + w - 1 <= size < h * w:
        raise ValueError("requested sparse shape cannot have this bounding box")
    cells = {(r, 0) for r in range(h)} | {(h - 1, c) for c in range(w)}
    while len(cells) < size:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _CARD
                           if 0 <= r + dr < h and 0 <= c + dc < w} - cells)
        cells.add(rng.choice(frontier))
    return sorted(cells)


def _sparse_poly(rng, size, maxdim=5):
    """Bounded random growth, followed by an exact-size constructive fallback."""
    options = [(h, w) for h in range(2, maxdim + 1) for w in range(2, maxdim + 1)
               if h + w - 1 <= size < h * w]
    if not options:
        raise ValueError("no sparse connected shape fits the requested bounds")
    for _ in range(40):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _CARD} - cells)
            cells.add(rng.choice(frontier))
        norm = _normalize(cells)
        h, w = _bbox(norm)
        if h <= maxdim and w <= maxdim and len(norm) < h * w:
            return norm
    h, w = min(options, key=lambda hw: (hw[0] * hw[1], hw))
    return _bounded_poly(rng, size, h, w)


def _transform(rng, cells):
    h, w = _bbox(cells)
    if rng.choice((False, True)):
        cells = [(h - 1 - r, c) for r, c in cells]
    if rng.choice((False, True)):
        cells = [(r, w - 1 - c) for r, c in cells]
    if rng.choice((False, True)):
        cells = [(c, r) for r, c in cells]
    return _normalize(cells)


def _stamp(grid, cells, color, row, col):
    for r, c in cells:
        grid[row + r][col + c] = color


def _compact_grid(ctx, h, w, size, count):
    """Exhaustive placement; a corner 3-by-4 fallback proves the full product.

    For h>=5,w>=6,size<=10 a <=3-by-4 target at the top left leaves
    the entire last row outside its 8-neighborhood: >=6 singleton slots.
    Distinct-colored distractors can touch each other without merging.
    """
    rng = ctx.draw_rng("compact_geometry")
    shape = _sparse_poly(rng, size)
    fallback_bounds = [(sh, sw) for sh in range(2, 4) for sw in range(2, 5)
                       if sh + sw - 1 <= size < sh * sw]
    sh, sw = min(fallback_bounds, key=lambda hw: (hw[0] * hw[1], hw))
    fallback = _bounded_poly(rng, size, sh, sw)
    for cells in (shape, fallback):
        sh, sw = _bbox(cells)
        positions = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
        rng.shuffle(positions)
        for row, col in positions:
            source = {(row + r, col + c) for r, c in cells}
            free = [(r, c) for r in range(h) for c in range(w)
                    if all((r + dr, c + dc) not in source
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1))]
            if len(free) < count:
                continue
            rng.shuffle(free)
            colors = [1, 2, 3, 4, 5, 7, 8, 9]
            ctx.draw_rng("compact_colors").shuffle(colors)
            grid = full_grid(h, w, 0)
            _stamp(grid, cells, 6, row, col)
            for (r, c), color in zip(free[:count], colors):
                grid[r][c] = color
            return grid
    raise ValueError("no placement satisfies the exact controls")  # unreachable in AXES product


def _rich_grid(ctx, h, w, size, residue):
    """Strict count/area/color/scan ranks, with target position and shape variation.

    Count ranks (low, middle, high, middle) differ from bbox-area ranks
    (high, middle, low, high). Color ranks are (high, middle, low, middle);
    scan order uses (middle, low, middle, high). Every eight-sample window contains all
    four scenes, so each min/max/median shortcut has >=2 refuting samples.
    """
    rng = ctx.draw_rng("rich_geometry")
    if residue == 1:
        specs = ((7, 4, 4), (8, 3, 3), (9, 3, 4))
        color_options = [1, 2, 3, 4, 5]
        colors = ctx.draw_rng("rich_colors").sample(color_options, 2)
    elif residue == 5:
        specs = ((size, 5, 3), (7, 4, 4), (8, 4, 5))
        colors = ctx.draw_rng("rich_colors").sample([7, 8, 9], 2)
    else:
        specs = ((size, 3, 4) if residue == 3 else (size, 4, 5),
                 (3, 2, 2), (9, 5, 5) if residue == 3 else (9, 3, 5))
        crng = ctx.draw_rng("rich_colors")
        colors = [crng.choice([1, 2, 3, 4, 5]), crng.choice([7, 8, 9])]
    cells = [_transform(rng, _bounded_poly(rng, n, bh, bw)) for n, bh, bw in specs]
    target_slot = {1: 1, 3: 0, 5: 1, 7: 2}[residue]
    others = [slot for slot in range(3) if slot != target_slot]
    rng.shuffle(others)
    slots = [target_slot, *others]
    row_offset = rng.randint(0, h - 17)
    grid = full_grid(h, w, 0)
    for obj, color, slot in zip(cells, [6, *colors], slots):
        _, bw = _bbox(obj)
        _stamp(grid, obj, color, row_offset + 6 * slot, rng.randint(0, w - bw))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    residue = sample_index % LESSON_SCHEDULE_PERIOD
    exact = any(value is not None for value in overrides.values())
    core = residue % 2 == 0
    if core:
        profile = _CANONICAL[ctx.draw_int_strict("canonical_profile", 0, 2)]
        defaults = dict(zip(("grid_h", "grid_w", "shape_size"), ((v, v) for v in profile)))
        defaults["n_distractor"] = (0, 0)
    else:
        hr, wr = {"easy": ((17, 18), (6, 8)),
                  "medium": ((18, 19), (7, 10)),
                  "hard": ((19, 20), (9, 12))}.get(difficulty, ((18, 19), (7, 10)))
        defaults = {"grid_h": hr, "grid_w": wr,
                    "shape_size": {1: (7, 7), 3: (7, 8), 5: (9, 10), 7: (8, 8)}[residue],
                    "n_distractor": (2, 2)}
    values = {axis: ctx.draw_int_strict(axis, *(_BOUNDS[axis] if overrides.get(axis) is not None else defaults[axis]))
              for axis in AXES}
    h, w, size, count = (values[axis] for axis in AXES)
    if exact or core:
        return _compact_grid(ctx, h, w, size, count)
    return _rich_grid(ctx, h, w, size, residue)


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty rectangular list of rows"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid cells must be Python integers 0..9"]
    return []


def _components(grid):
    todo = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color != 0}
    result = []
    while todo:
        cell = min(todo)
        color = grid[cell[0]][cell[1]]
        todo.remove(cell)
        cells, stack = {cell}, [cell]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in todo and grid[nxt[0]][nxt[1]] == color:
                    todo.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append((color, cells))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors
    parts = _components(grid)
    sixes = [cells for color, cells in parts if color == 6]
    if len(sixes) != 1:
        errors.append(f"expected exactly one 4-connected color-6 component, got {len(sixes)}")
    if sixes:
        for cells in sixes:
            h, w = _bbox(cells)
            if len(cells) == h * w:
                errors.append("color-6 component fills its bounding box")
            for r, c in cells:
                for nr in range(max(0, r - 1), min(len(grid), r + 2)):
                    for nc in range(max(0, c - 1), min(len(grid[0]), c + 2)):
                        if grid[nr][nc] not in (0, 6):
                            return errors + ["distractor touches color 6 at 8-neighbor distance"]
    colors = [color for color, _ in parts if color != 6]
    if len(colors) != len(set(colors)):
        errors.append("distractor objects must have distinct colors")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    parts = _components(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "shape_size": sum(len(cells) for color, cells in parts if color == 6),
            "n_distractor": sum(color != 6 for color, _ in parts)}


def canonical_profile_signature(grid):
    values = observe_overrides(grid)
    return (values["grid_h"], values["grid_w"], values["shape_size"],
            values["n_distractor"], tuple(sorted({v for row in grid for v in row})))


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    signatures = {(h, w, n, 0, (0, 6)) for h, w, n in _CANONICAL}
    return [] if canonical_profile_signature(grid) in signatures else ["outside the linked canonical dimension/count/palette profiles"]


MIN_STRICT_FRAC = 0.25
SCHEDULE_PROFILES = ("core_a", "low_count", "core_b", "middle_first",
                     "core_c", "high_count", "core_d", "middle_last")


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic modes repeat; grids, shapes, colors and positions remain seeded."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _box_output(grid, cells, *, preserve=False, cap=None):
    """Python authoring mirror used by rival checks, never to label generation."""
    result = [list(row) for row in grid] if preserve else full_grid(len(grid), len(grid[0]), 0)
    if cells:
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        if cap is not None:
            r1, c1 = min(r1, r0 + cap - 1), min(c1, c0 + cap - 1)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                result[r][c] = 6
    return result


def _target_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]


def _all_nonzero_box(grid):
    return _box_output(grid, [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value])


def _all_component_boxes(grid):
    result = full_grid(len(grid), len(grid[0]), 0)
    for _, cells in _components(grid):
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                result[r][c] = 6
    return result


def _keep_distractors(grid):
    return _box_output(grid, _target_cells(grid), preserve=True)


def _cap_three(grid):
    return _box_output(grid, _target_cells(grid), cap=3)


def _cap_four(grid):
    return _box_output(grid, _target_cells(grid), cap=4)


def _ranked_box(grid, *, feature, rank):
    def key(obj):
        color, cells = obj
        height, width = _bbox(cells)
        values = {"count": len(cells), "area": height * width,
                  "scan": min(cells), "color": color,
                  "aspect": Fraction(max(height, width), min(height, width))}
        return values[feature], min(cells), color
    parts = sorted(_components(grid), key=key)
    if not parts:
        return _box_output(grid, [])
    index = {"min": 0, "max": len(parts) - 1, "median": len(parts) // 2}[rank]
    return _box_output(grid, parts[index][1])


def _sole_else_unique_area12(grid):
    """Color-blind shortcut: sole foreground part, otherwise unique bbox area12."""
    parts = _components(grid)
    if len(parts) == 1:
        return _box_output(grid, parts[0][1])
    candidates = [cells for _, cells in parts if _bbox(cells)[0] * _bbox(cells)[1] == 12]
    return _box_output(grid, candidates[0] if len(candidates) == 1 else [])


# Every declaration fits all three labeled canonical pairs. These are finite
# alternatives, not a complete hypothesis class. Aliases share callable identity
# so the shared census can avoid scoring the same rival three times.
CANONICAL_SHORTCUTS = {
    "all_nonzero_box": _all_nonzero_box,
    "all_component_boxes": _all_component_boxes,
    "keep_distractors": _keep_distractors,
    "cap_three": _cap_three,
    "cap_four": _cap_four,
    "sole_else_unique_area12": _sole_else_unique_area12,
}
CANONICAL_SHORTCUTS.update({
    f"{feature}_{rank}": partial(_ranked_box, feature=feature, rank=rank)
    for feature in ("count", "area", "scan", "color", "aspect")
    for rank in ("min", "max", "median")
})
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)


def _rival_witness(grid, *, rival):
    return rival(grid) != _box_output(grid, _target_cells(grid))


SEMANTIC_WITNESSES = {name: partial(_rival_witness, rival=rival)
                      for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Score actual labels, including overrides and rejected-index windows."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but disagrees on the query")
    return reasons
