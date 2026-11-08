"""Generator for arc_puzzle_bank_seventeenth21:E116.

Rule: keep each monochrome 4-connected object iff it touches any outer
border; erase every fully interior object to background 0.

The teaching distribution varies all four border sides, object counts,
component geometry, and whether one color appears in both a kept and an
erased component.  Every ordinary draw contains both rule branches.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "721810839902"
TASK_ID = "721810839902"
VERSION = "3.0.0"  # exact side/shape observability plus 8-connectivity-safe decoys
RULE_HASH = "e3401b50999e"
SUMMARY = (
    "An 8-12 by 8-12 zero-background grid contains 1-3 border-touching "
    "monochrome 4-connected objects and 1-3 fully interior objects. Objects "
    "vary across every border side, sizes, and shapes; some scenes reuse one "
    "color across a kept and erased component. Keep exactly the components "
    "that touch any outer row or column and erase the interior components."
)

INVARIANTS = [
    "background is 0",
    "ordinary draws contain at least one border-touching component",
    "ordinary draws contain at least one fully interior component",
    "components are monochrome, have at least two cells, and do not touch orthogonally",
    "output preserves dimensions, positions, and colors of border-touching components only",
]

BORDER_SIDES = ("top", "right", "bottom", "left")
SHAPE_MIXES = ("dominoes", "triominoes", "varied")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 8..12", "valid": "8..12"},
    "n_border": {"type": "int", "default": "difficulty-skewed 1..3", "valid": "1..3"},
    "n_interior": {"type": "int", "default": "difficulty-skewed 1..3", "valid": "1..3"},
    "border_side": {
        "type": "enum",
        "default": "sequential top|right|bottom|left",
        "valid": "top|right|bottom|left",
    },
    "shape_mix": {
        "type": "enum",
        "default": "rng",
        "valid": "dominoes|triominoes|varied",
    },
    "same_color_decoy": {"type": "bool", "default": "rng", "valid": "false|true"},
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True)
class _Spec:
    index: int
    color: int
    shape: frozenset[tuple[int, int]]
    target: str


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _transform(
    shape: frozenset[tuple[int, int]], quarter_turns: int, mirror: bool
) -> frozenset[tuple[int, int]]:
    cells = set(shape)
    for _ in range(quarter_turns % 4):
        cells = {(c, -r) for r, c in cells}
    if mirror:
        cells = {(r, -c) for r, c in cells}
    return _normalize(cells)


def _grown_shape(size: int, rng) -> frozenset[tuple[int, int]]:
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _DIR4
                if (r + dr, c + dc) not in cells
            }
        )
        cells.add(rng.choice(frontier))
    return _transform(_normalize(cells), rng.randrange(4), bool(rng.randrange(2)))


def _shape_for(index: int, mix: str, rng) -> frozenset[tuple[int, int]]:
    if mix == "dominoes":
        size = 2
    elif mix == "triominoes":
        size = 3
    else:
        size = (2, 4, 3)[index % 3]
    return _grown_shape(size, rng)


def _shape_dims(shape: frozenset[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _translate(
    shape: frozenset[tuple[int, int]], top: int, left: int
) -> frozenset[tuple[int, int]]:
    return frozenset((top + r, left + c) for r, c in shape)


def _orthogonal_guard(cells: frozenset[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for r, c in cells
        for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= rr < h and 0 <= cc < w
    }


def _candidate_cells(
    shape: frozenset[tuple[int, int]], target: str, h: int, w: int
) -> list[frozenset[tuple[int, int]]]:
    sh, sw = _shape_dims(shape)
    if sh > h or sw > w:
        return []
    offsets: list[tuple[int, int]] = []
    if target == "interior":
        offsets = [
            (top, left)
            for top in range(1, h - sh)
            for left in range(1, w - sw)
        ]
    elif target == "top":
        offsets = [(0, left) for left in range(1, w - sw)]
    elif target == "bottom":
        offsets = [(h - sh, left) for left in range(1, w - sw)]
    elif target == "left":
        offsets = [(top, 0) for top in range(1, h - sh)]
    elif target == "right":
        offsets = [(top, w - sw) for top in range(1, h - sh)]
    return [_translate(shape, top, left) for top, left in offsets]



def _place_specs(
    specs: list[_Spec], h: int, w: int, ctx, attempt: int
) -> dict[int, frozenset[tuple[int, int]]] | None:
    entries = []
    for spec in specs:
        candidates = _candidate_cells(spec.shape, spec.target, h, w)
        rng = ctx.draw_rng(f"placement_{attempt}_{spec.index}")
        rng.shuffle(candidates)
        entries.append((spec, candidates))
    entries.sort(key=lambda item: (len(item[1]), item[0].index))
    placements: dict[int, frozenset[tuple[int, int]]] = {}
    node_budget = 250_000
    visited = 0

    def search(pos: int, forbidden: set[tuple[int, int]]) -> bool:
        nonlocal visited
        if pos == len(entries):
            return True
        spec, candidates = entries[pos]
        for cells in candidates:
            visited += 1
            if visited > node_budget:
                return False
            if cells & forbidden:
                continue
            placements[spec.index] = cells
            if search(pos + 1, forbidden | _orthogonal_guard(cells, h, w)):
                return True
            placements.pop(spec.index, None)
        return False

    return placements if search(0, set()) else None


def components(grid) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    """Return row-major monochrome 4-connected non-zero components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, frozenset[tuple[int, int]]]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, frozenset(cells)))
    return out


def _touches_border(cells: frozenset[tuple[int, int]], h: int, w: int) -> bool:
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)


def _same_color_diagonal_contact(grid) -> bool:
    """Reject same-color role decoys that merge under 8-connectivity."""
    comps = components(grid)
    for i, (left_color, left_cells) in enumerate(comps):
        for right_color, right_cells in comps[i + 1 :]:
            if left_color != right_color:
                continue
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) == 1
                for r1, c1 in left_cells
                for r2, c2 in right_cells
            ):
                return True
    return False


def _component_border_sides(cells, h: int, w: int) -> set[str]:
    sides: set[str] = set()
    if any(r == 0 for r, _ in cells):
        sides.add("top")
    if any(c == w - 1 for _, c in cells):
        sides.add("right")
    if any(r == h - 1 for r, _ in cells):
        sides.add("bottom")
    if any(c == 0 for _, c in cells):
        sides.add("left")
    return sides


def observe_overrides(grid) -> dict[str, int | bool | str]:
    h, w = len(grid), len(grid[0])
    comps = components(grid)
    border = [(color, cells) for color, cells in comps if _touches_border(cells, h, w)]
    interior = [(color, cells) for color, cells in comps if not _touches_border(cells, h, w)]
    border_colors = {color for color, _ in border}
    interior_colors = {color for color, _ in interior}
    side_sets = {frozenset(_component_border_sides(cells, h, w)) for _, cells in border}
    border_side = next(iter(next(iter(side_sets)))) if len(side_sets) == 1 and len(next(iter(side_sets))) == 1 else "mixed"
    sizes = [len(cells) for _, cells in comps]
    shape_mix = "dominoes" if sizes and set(sizes) == {2} else "triominoes" if sizes and set(sizes) == {3} else "varied"
    return {
        "grid_h": h,
        "grid_w": w,
        "n_border": len(border),
        "n_interior": len(interior),
        "border_side": border_side,
        "shape_mix": shape_mix,
        "same_color_decoy": bool(border_colors & interior_colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty rectangular list of rows"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid colors must be integers in 0..9"]
    h = len(grid)
    comps = components(grid)
    errors: list[str] = []
    border = 0
    interior = 0
    for _, cells in comps:
        if len(cells) < 2:
            errors.append("every non-zero component must contain at least two cells")
        if _touches_border(cells, h, w):
            border += 1
        else:
            interior += 1
    if border < 1:
        errors.append("expected at least one border-touching component")
    if interior < 1:
        errors.append("expected at least one fully interior component")
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other not in (0, value):
                        errors.append("different-colored components touch orthogonally")
    if _same_color_diagonal_contact(grid):
        errors.append("same-colored components must remain separate under 8-connectivity")
    return sorted(set(errors))


def apply_rule(grid) -> list[list[int]]:
    """Independent Python test mirror; the Racket rule remains output authority."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for color, cells in components(grid):
        if _touches_border(cells, h, w):
            for r, c in cells:
                out[r][c] = color
    return out


def _scheduled_choice(ctx, label: str, options: tuple, sample_index: int):
    """Cycle ordinary lessons; explicit overrides still use the full domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    scheduled = options[sample_index % len(options)]
    return ctx.draw_choice(label, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 12)
    w = ctx.draw_int_diff("grid_w", 8, 12)
    n_border = ctx.draw_int_diff("n_border", 1, 3)
    n_interior = ctx.draw_int_diff("n_interior", 1, 3)
    border_side = _scheduled_choice(ctx, "border_side", BORDER_SIDES, sample_index)
    shape_mix = _scheduled_choice(ctx, "shape_mix", SHAPE_MIXES, sample_index)
    same_color_decoy = _scheduled_choice(
        ctx, "same_color_decoy", (False, True), sample_index
    )

    total = n_border + n_interior
    color_rng = ctx.draw_rng("colors")
    palette = color_rng.sample(list(range(1, 10)), total)
    if same_color_decoy:
        palette[n_border] = palette[0]

    targets = [border_side] * n_border + ["interior"] * n_interior
    for attempt in range(48):
        specs = [
            _Spec(
                index=i,
                color=palette[i],
                shape=_shape_for(i, shape_mix, ctx.draw_rng(f"shape_{attempt}_{shape_mix}_{i}")),
                target=targets[i],
            )
            for i in range(total)
        ]
        placed = _place_specs(specs, h, w, ctx, attempt)
        if placed is None:
            continue
        grid = full_grid(h, w, 0)
        for spec in specs:
            for r, c in sorted(placed[spec.index]):
                grid[r][c] = spec.color
        observed = observe_overrides(grid)
        if (
            observed["n_border"] == n_border
            and observed["n_interior"] == n_interior
            and observed["border_side"] == border_side
            and observed["shape_mix"] == shape_mix
            and observed["same_color_decoy"] is same_color_decoy
            and not self_check(grid, difficulty=difficulty)
        ):
            return grid
    raise ValueError(
        "could not realize requested border/interior component layout "
        f"in {h}x{w} after 48 deterministic attempts"
    )
