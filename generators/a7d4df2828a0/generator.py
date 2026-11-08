"""Inputs for a7d4df2828a0: a control-coded, lossless local motif transform.

Code at (0,0): 1=90 degrees clockwise, 2=180 degrees, 3=left/right
reflection, 4=up/down reflection. The separate single-color connected
motif is transformed about its bbox and re-anchored at that bbox's top-left.
Only inputs are produced here. Labels remain the canonical Racket rule's job.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a7d4df2828a0"
TASK_ID = "a7d4df2828a0"
VERSION = "2.1.0"
RULE_HASH = "089b88c1e5ad"

SUMMARY = (
    "A control at (0,0) selects a local transform of one separated, connected, "
    "single-color 3-6-cell motif: 1=90cw, 2=180, 3=flip-lr, 4=flip-ud. "
    "The motif and its transformed footprint both fit; the selected transform "
    "changes the motif. Other symmetries are allowed, including canonical T shapes. "
    "Paint on a fresh zero canvas at the original bbox top-left; discard the control."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "background is 0 and the control at (0,0) is in {1,2,3,4}",
    "all remaining nonzero cells form one 4-connected 3-6-cell motif",
    "the motif has one color distinct from background and control, with an 8-neighbor gap from control",
    "the motif bbox has at least two rows and two columns",
    "the selected transform changes the motif; unrelated symmetries are permitted",
    "the input and selected transformed footprint both fit on the same canvas",
]
AXES = {
    "grid_h": {"type": "int", "default": "compact 7..9 or difficulty band",
               "valid": "7..14", "doc": "Height; all values work in every band."},
    "grid_w": {"type": "int", "default": "compact 7..9 or difficulty band",
               "valid": "7..14", "doc": "Width; all values work in every band."},
    "motif_size": {"type": "int", "default": "compact 4 or difficulty band",
                   "valid": "3..6", "doc": "Exact motif cell count, independent of band when pinned."},
    "code": {"type": "int", "default": "rng 1..4", "valid": "1..4",
             "doc": "Control code: 1=90cw, 2=180, 3=flip-lr, 4=flip-ud."},
}
# No declared combination is infeasible. Opt into strict rejection accounting.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


@lru_cache(maxsize=6)
def _polyominoes(size):
    """All translation-normalized oriented connected shapes, not canonical templates.

    Each step adds one adjacent cell. A sorted immutable result makes sampling
    independent of hash randomization and cache warmness. Sizes never exceed six.
    """
    if not 1 <= size <= 6:
        raise ValueError("shape size must be in 1..6")
    if size == 1:
        return (((0, 0),),)
    shapes = set()
    for prior in _polyominoes(size - 1):
        occupied = set(prior)
        for r, c in prior:
            for dr, dc in _NEIGHBORS:
                point = (r + dr, c + dc)
                if point not in occupied:
                    shapes.add(_normalize((*prior, point)))
    return tuple(sorted(shapes))


def _changes_under_code(cells, code):
    """Input admissibility only: reject invariance under the SELECTED operation.

    This is not a Python label path. In particular it must not demand that a
    code-1 T motif change under code 3 as the previous all-transform filter did.
    """
    maxr = max(r for r, _ in cells)
    maxc = max(c for _, c in cells)
    if code == 1:
        moved = {(c, maxr - r) for r, c in cells}
    elif code == 2:
        moved = {(maxr - r, maxc - c) for r, c in cells}
    elif code == 3:
        moved = {(r, maxc - c) for r, c in cells}
    elif code == 4:
        moved = {(maxr - r, c) for r, c in cells}
    else:
        raise ValueError("code must be in 1..4")
    return set(cells) != moved


@lru_cache(maxsize=16)
def _motif_candidates(size, code):
    return tuple(cells for cells in _polyominoes(size)
                 if max(r for r, _ in cells) >= 1
                 and max(c for _, c in cells) >= 1
                 and _changes_under_code(cells, code))


def _motif_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value != 0 and (r, c) != (0, 0)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's chosen teaching domain, without executing its label rule."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be lists or tuples"]
    h, w = len(grid), len(grid[0])
    if not w or any(len(row) != w for row in grid):
        return ["grid must be nonempty and rectangular"]
    if h > 30 or w > 30:
        return ["grid dimensions must not exceed 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer colors 0..9, not booleans"]
    code = grid[0][0]
    if code not in (1, 2, 3, 4):
        return [f"(0,0) expected code in {{1,2,3,4}}; got {code}"]
    cells = _motif_cells(grid)
    if not 3 <= len(cells) <= 6:
        return [f"expected 3..6 motif cells outside (0,0); got {len(cells)}"]
    errors = []
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1 or code in colors:
        errors.append("motif must have one nonzero color distinct from the control")
    if any(r <= 1 and c <= 1 for r, c in cells):
        errors.append("motif must be 8-neighbor separated from the control")
    unseen = set(cells)
    pending = [unseen.pop()]
    while pending:
        r, c = pending.pop()
        for dr, dc in _NEIGHBORS:
            point = (r + dr, c + dc)
            if point in unseen:
                unseen.remove(point)
                pending.append(point)
    if unseen:
        errors.append("motif must be 4-connected")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    sh = max(r for r, _ in cells) - r0 + 1
    sw = max(c for _, c in cells) - c0 + 1
    if sh < 2 or sw < 2:
        errors.append("motif bbox must have at least two rows and columns")
    if not _changes_under_code(_normalize(cells), code):
        errors.append("selected transform must visibly change the motif")
    oh, ow = (sw, sh) if code == 1 else (sh, sw)
    if r0 + oh > h or c0 + ow > w:
        errors.append("selected transformed footprint would clip at the canvas boundary")
    return errors


def strict_canonical_like(grid):
    """The declared teaching manifold, broader than the three literal fixtures."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "motif_size": len(_motif_cells(grid)), "code": grid[0][0]}


SEMANTIC_WITNESSES = {
    "code_1": lambda grid: grid[0][0] == 1,
    "code_2": lambda grid: grid[0][0] == 2,
    "code_3": lambda grid: grid[0][0] == 3,
    "code_4": lambda grid: grid[0][0] == 4,
}
# Coverage only, not a claim of lesson identifiability or rival elimination.
BRANCH_WITNESSES = ("code_1", "code_2", "code_3", "code_4")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for key, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"override {key} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    # Half the default draws in EVERY band retain compact, four-cell support.
    # This is a generic size stratum, not a copied canonical input or output.
    compact = rng.random() < 0.5
    if compact:
        dim_lo, dim_hi, size_lo, size_hi = 7, 9, 4, 4
    elif difficulty == "easy":
        dim_lo, dim_hi, size_lo, size_hi = 7, 9, 3, 4
    elif difficulty == "hard":
        dim_lo, dim_hi, size_lo, size_hi = 11, 14, 4, 6
    else:
        dim_lo, dim_hi, size_lo, size_hi = 9, 11, 3, 5
    hb = (7, 14) if overrides.get("grid_h") is not None else (dim_lo, dim_hi)
    wb = (7, 14) if overrides.get("grid_w") is not None else (dim_lo, dim_hi)
    kb = (3, 6) if overrides.get("motif_size") is not None else (size_lo, size_hi)
    h = ctx.draw_int("grid_h", *hb)
    w = ctx.draw_int("grid_w", *wb)
    size = ctx.draw_int("motif_size", *kb)
    code = ctx.draw_int("code", 1, 4)
    color = rng.choice([c for c in range(1, 10) if c != code])
    cells = rng.choice(_motif_candidates(size, code))
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    oh, ow = (sw, sh) if code == 1 else (sh, sw)
    # A 90-degree rotation swaps extents. Reserve the UNION of the two bboxes,
    # not just the input bbox. Bounds include all four canvas edges.
    anchors = [(r0, c0)
               for r0 in range(h - max(sh, oh) + 1)
               for c0 in range(w - max(sw, ow) + 1)
               if all(r0 + r > 1 or c0 + c > 1 for r, c in cells)]
    if not anchors:
        raise ValueError("no legal anchor for the requested footprint")
    r0, c0 = rng.choice(anchors)
    grid = full_grid(h, w, 0)
    grid[0][0] = code
    for r, c in cells:
        grid[r0 + r][c0 + c] = color
    return grid
