"""Generator for arc_puzzle_bank_third21:E20.

Canonical rule: every solid monochrome 2x2 block keeps its main diagonal
(top-left + bottom-right); the anti-diagonal cells are cleared to 0.  Other
objects are unchanged.

The teaching distribution deliberately uses exact 2x2 monochrome components as
targets and non-2x2 components as distractors.  It does *not* generate larger
same-color regions containing overlapping solid 2x2 windows because the selected
Racket program resolves overlapping writes in scan order while the written rule
does not specify a conflict policy.  self_check rejects that ambiguous grammar.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f98b43c1996b"
TASK_ID = "f98b43c1996b"
VERSION = "3.0.0"
RULE_HASH = "cbbce0964240"

SUMMARY = (
    "On a zero-background grid, several solid monochrome 2x2 components are "
    "mixed with non-2x2 distractor components.  For every solid 2x2 target, "
    "clear its top-right and bottom-left cells and keep its top-left and "
    "bottom-right cells.  Leave every distractor unchanged.  Targets may touch "
    "different-colored targets, so a full 2x2 window is not enough: all four "
    "cells must have the same nonzero color."
)

EXAMPLES_NEEDED = 2

INVARIANTS = [
    "background color is 0",
    "2..4 exact monochrome 2x2 target components on ordinary draws",
    "1..2 non-2x2 distractor components on ordinary draws",
    "every ordinary draw contains a mixed-color full 2x2 seam that must not fire",
    "every ordinary draw contains an L-tromino near-block that must remain unchanged",
    "every ordinary draw has a target colored 1, 8, or 9 to refute fixed canonical palettes",
    "larger same-color components containing overlapping solid 2x2 windows are outside the teaching grammar",
]

# Every declared axis is exact, keyed through GenCtx, and recovered from the
# returned grid by observe_overrides().  Difficulty changes layout/texture, not
# the legal axis domains, so every valid override remains valid in every band.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "7..9",
    },
    "n_blocks": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "2..4",
    },
    "n_distractors": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "1..2",
    },
}

_TARGET_SHAPE = ((0, 0), (0, 1), (1, 0), (1, 1))
_L_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_SECOND_DISTRACTORS = {
    "easy": (
        ((0, 0),),
        ((1, 1),),
        ((0, 0), (0, 1)),
    ),
    "medium": (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
        ((1, 0), (1, 1)),
        ((0, 1), (1, 1)),
    ),
    "hard": _L_SHAPES
    + (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
}


def _cells(anchor: tuple[int, int], shape) -> set[tuple[int, int]]:
    r0, c0 = anchor
    return {(r0 + dr, c0 + dc) for dr, dc in shape}


def _boxes_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Whether two 2x2 reserved footprints overlap."""
    ar, ac = a
    br, bc = b
    return not (ar + 1 < br or br + 1 < ar or ac + 1 < bc or bc + 1 < ac)


def _boxes_edge_touch(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Whether cells in two non-overlapping 2x2 footprints share an edge."""
    ar, ac = a
    br, bc = b
    rows_overlap = not (ar + 1 < br or br + 1 < ar)
    cols_overlap = not (ac + 1 < bc or bc + 1 < ac)
    horizontal_touch = rows_overlap and (ac + 2 == bc or bc + 2 == ac)
    vertical_touch = cols_overlap and (ar + 2 == br or br + 2 == ar)
    return horizontal_touch or vertical_touch


def _color_slots(anchors: list[tuple[int, int]], n_colors: int) -> list[int] | None:
    """Properly color touching footprints, using every requested color slot."""
    n = len(anchors)
    if not 1 <= n_colors <= n:
        return None
    if n_colors == n:
        return list(range(n))
    neighbors = [set() for _ in anchors]
    for i in range(n):
        for j in range(i + 1, n):
            if _boxes_edge_touch(anchors[i], anchors[j]):
                neighbors[i].add(j)
                neighbors[j].add(i)

    colors = [-1] * n
    colors[0] = 0  # the first target is always the noncanonical-palette witness
    order = [i for i in sorted(range(1, n), key=lambda i: (-len(neighbors[i]), i))]

    def search(pos: int) -> bool:
        if pos == len(order):
            return set(colors) == set(range(n_colors))
        vertex = order[pos]
        forbidden = {colors[j] for j in neighbors[vertex] if colors[j] >= 0}
        for color in range(n_colors):
            if color in forbidden:
                continue
            colors[vertex] = color
            if search(pos + 1):
                return True
        colors[vertex] = -1
        return False

    return list(colors) if search(0) else None


def _adjacent_pair_candidates(h: int, w: int, orientation: str):
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    if orientation == "horizontal":
        for r in range(h - 1):
            for c in range(w - 3):
                pairs.append(((r, c), (r, c + 2)))
    else:
        for r in range(h - 3):
            for c in range(w - 1):
                pairs.append(((r, c), (r + 2, c)))
    return pairs


def _plan_anchors(
    h: int, w: int, n_objects: int, orientation: str, rng, *, color_count: int
) -> list[tuple[int, int]]:
    """Pick non-overlapping 2x2 footprints, with the first two edge-adjacent.

    Reserving whole 2x2 footprints keeps the deliberate L-tromino hole empty,
    while edge-adjacent first target footprints create a 2x2 mixed-color seam.
    """
    all_anchors = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    order = list(all_anchors)
    rng.shuffle(order)
    pair_candidates = _adjacent_pair_candidates(h, w, orientation)
    rng.shuffle(pair_candidates)

    def extend(chosen: list[tuple[int, int]], start: int) -> list[tuple[int, int]] | None:
        if len(chosen) == n_objects:
            return list(chosen) if _color_slots(chosen, color_count) is not None else None
        for index in range(start, len(order)):
            anchor = order[index]
            if anchor in chosen or any(_boxes_overlap(anchor, other) for other in chosen):
                continue
            chosen.append(anchor)
            found = extend(chosen, index + 1)
            if found is not None:
                return found
            chosen.pop()
        return None

    for first, second in pair_candidates:
        found = extend([first, second], 0)
        if found is not None:
            return found

    # This should be unreachable for the declared 6..9 x 7..9 / <=6-object
    # contract.  Fail loudly rather than silently dropping a requested object.
    raise RuntimeError(
        f"cannot place {n_objects} reserved 2x2 footprints in {h}x{w} "
        f"with a {orientation} adjacent target pair"
    )


def _paint(grid: list[list[int]], anchor: tuple[int, int], shape, color: int) -> None:
    for r, c in _cells(anchor, shape):
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid for the canonical Racket rule."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    if difficulty is None:
        band = "medium"
    elif difficulty in {"easy", "medium", "hard"}:
        band = difficulty
    else:
        raise ValueError(f"unknown difficulty band: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 6, 9)
    w = ctx.draw_int("grid_w", 7, 9)
    n_blocks = ctx.draw_int("n_blocks", 2, 4)
    n_distractors = ctx.draw_int("n_distractors", 1, 2)
    n_objects = n_blocks + n_distractors

    # Canonical profile (8, 8, 4) means an 8x8 grid with three nonzero
    # colors.  Reusing colors on disconnected components makes that profile
    # a healthy, explicit part of the teaching distribution without changing
    # any semantic axis.  Other sizes use one color per reserved object.
    color_count = 3 if (h, w) == (8, 8) else n_objects

    # Alternate the mixed-seam orientation by sequential sample index so every
    # sliding two-example lesson sees both spatial realizations.  This is not an
    # exact override axis; it changes only layout, not the rule grammar.
    orientation = "horizontal" if sample_index % 2 == 0 else "vertical"
    layout_rng = ctx.draw_rng(f"layout_{band}")
    anchors = _plan_anchors(
        h, w, n_objects, orientation, layout_rng, color_count=color_count
    )

    # Canonical examples only use colors 2..7.  Force one target onto 1/8/9 and
    # vary the remaining palette colors.  On 8x8 scenes, a proper footprint
    # coloring safely reuses exactly three nonzero colors, anchoring the
    # canonical (8,8,palette-size=4) morphology profile.
    novel = ctx.draw_choice("novel_target_color", (1, 8, 9))
    other_colors = list(
        ctx.draw_distinct_colors(
            "remaining_palette_colors", n=color_count - 1, exclude={0, novel}
        )
    )
    palette = [novel, *other_colors]
    slots = _color_slots(anchors, color_count)
    if slots is None:
        raise AssertionError("planned footprints are not colorable by requested palette")
    colors = [palette[slot] for slot in slots]

    grid = full_grid(h, w, 0)
    for index in range(n_blocks):
        _paint(grid, anchors[index], _TARGET_SHAPE, colors[index])

    # The first distractor is always a three-of-four L inside a reserved 2x2
    # footprint.  It is the minimal counterexample to "almost-solid also fires".
    first_distractor = n_blocks
    l_shape = _L_SHAPES[(sample_index + {"easy": 0, "medium": 1, "hard": 2}[band]) % 4]
    _paint(grid, anchors[first_distractor], l_shape, colors[first_distractor])

    if n_distractors == 2:
        shape_rng = ctx.draw_rng(f"distractor_shape_{band}")
        second_shape = shape_rng.choice(_SECOND_DISTRACTORS[band])
        second = n_blocks + 1
        _paint(grid, anchors[second], second_shape, colors[second])

    # Generation-time assertions are deliberate: exact axes may never be
    # silently degraded by placement fallback.
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_blocks": n_blocks,
        "n_distractors": n_distractors,
    }
    if observed != expected:
        raise AssertionError(f"exact-axis realization mismatch: {observed} != {expected}")
    if not _has_mixed_color_full_window(grid):
        raise AssertionError("missing mixed-color full-2x2 shortcut witness")
    if not _has_near_solid_window(grid):
        raise AssertionError("missing L-tromino near-solid shortcut witness")
    if not _has_novel_target(grid):
        raise AssertionError("missing noncanonical target-color shortcut witness")
    return grid


def _fires(grid: list[list[int]]) -> set[tuple[int, int]]:
    """Top-left positions of solid same-color nonzero 2x2 windows."""
    h, w = len(grid), len(grid[0])
    hits: set[tuple[int, int]] = set()
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if (
                v != 0
                and grid[r][c + 1] == v
                and grid[r + 1][c] == v
                and grid[r + 1][c + 1] == v
            ):
                hits.add((r, c))
    return hits


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells: set[tuple[int, int]] = {(sr, sc)}
            seen.add((sr, sc))
            stack = [(sr, sc)]
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _is_exact_block(cells: set[tuple[int, int]]) -> bool:
    if len(cells) != 4:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    return r1 - r0 == 1 and c1 - c0 == 1 and len(cells) == 4


def _component_contains_solid_2x2(cells: set[tuple[int, int]]) -> bool:
    return any(
        (r, c + 1) in cells and (r + 1, c) in cells and (r + 1, c + 1) in cells
        for r, c in cells
    )


def _classify_components(grid):
    targets = []
    distractors = []
    ambiguous = []
    for color, cells in _components(grid):
        if _is_exact_block(cells):
            targets.append((color, cells))
        elif _component_contains_solid_2x2(cells):
            ambiguous.append((color, cells))
        else:
            distractors.append((color, cells))
    return targets, distractors, ambiguous


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from a generated returned grid."""
    targets, distractors, _ = _classify_components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blocks": len(targets),
        "n_distractors": len(distractors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar gate; accepts every canonical train/test input."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be non-empty and rectangular"]

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("zero background must be present")

    targets, _, ambiguous = _classify_components(grid)
    # Every canonical scene contains multiple independently colored targets.
    # Treat a lone block as an under-specified recombination outside this ARC
    # input grammar (the oracle can still execute it; see the negative-probe
    # evidence).  Multiple targets keep the scene structural rather than a
    # one-object toy while remaining canonical-complete.
    if len(targets) < 2:
        errors.append("at least two exact monochrome 2x2 target components are required")
    for color, cells in ambiguous:
        errors.append(
            f"color {color} component with {len(cells)} cells contains an overlapping/non-maximal "
            "solid 2x2 window; conflict semantics are outside this task grammar"
        )
    return errors


def mutation_fixtures():
    """Task-local malformed/recombined scenes that self_check must reject."""
    def blank():
        return [[0] * 7 for _ in range(6)]

    one_block = blank()
    _paint(one_block, (1, 1), _TARGET_SHAPE, 2)

    no_target = blank()
    _paint(no_target, (1, 1), _L_SHAPES[0], 2)
    _paint(no_target, (3, 4), ((0, 0), (0, 1)), 3)

    overlapping = blank()
    for r in range(3):
        for c in range(3):
            overlapping[r + 1][c + 1] = 2
    _paint(overlapping, (4, 4), _TARGET_SHAPE, 3)

    fused_blocks = blank()
    for r in (1, 2):
        for c in range(1, 5):
            fused_blocks[r][c] = 4
    _paint(fused_blocks, (4, 4), _TARGET_SHAPE, 5)

    return [
        ("single_target_under_specified", one_block),
        ("no_solid_target", no_target),
        ("overlapping_3x3_windows", overlapping),
        ("fused_same_color_blocks", fused_blocks),
    ]


def strict_canonical_like(grid) -> list[str]:
    """Teaching-manifold predicate, broader enough to include all canonicals."""
    errors = list(self_check(grid))
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 9 and 7 <= w <= 9):
        errors.append(f"expected canonical-scale dimensions 6..9x7..9, got {h}x{w}")
    targets, distractors, _ = _classify_components(grid)
    if not 2 <= len(targets) <= 4:
        errors.append(f"expected 2..4 target blocks, got {len(targets)}")
    if not 0 <= len(distractors) <= 2:
        errors.append(f"expected 0..2 distractor components, got {len(distractors)}")
    if any(len(cells) > 4 for _, cells in [*targets, *distractors]):
        errors.append("teaching components must have at most four cells")
    nonzero_colors = {value for row in grid for value in row if value != 0}
    if not 2 <= len(nonzero_colors) <= 6:
        errors.append(f"expected 2..6 non-background colors, got {len(nonzero_colors)}")
    return errors


MIN_STRICT_FRAC = 1.0


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for checks/rivals; Racket remains output authority."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if (
                v != 0
                and grid[r][c + 1] == v
                and grid[r + 1][c] == v
                and grid[r + 1][c + 1] == v
            ):
                out[r][c] = v
                out[r][c + 1] = 0
                out[r + 1][c] = 0
                out[r + 1][c + 1] = v
    return out


def _identity_rival(grid):
    return [row[:] for row in grid]


def _all_nonzero_window_rival(grid):
    """Shortcut: any fully occupied 2x2 fires, ignoring monochrome equality."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            a = grid[r][c]
            b = grid[r][c + 1]
            d = grid[r + 1][c]
            e = grid[r + 1][c + 1]
            if a and b and d and e:
                out[r][c] = a
                out[r][c + 1] = 0
                out[r + 1][c] = 0
                out[r + 1][c + 1] = e
    return out


def _near_solid_rival(grid):
    """Shortcut: three-of-four same-color cells are treated like a solid block."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            positions = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            values = [grid[rr][cc] for rr, cc in positions]
            counts = Counter(v for v in values if v != 0)
            majority = next((v for v, count in counts.items() if count >= 3), None)
            if majority is None:
                continue
            if grid[r][c + 1] == majority:
                out[r][c + 1] = 0
            if grid[r + 1][c] == majority:
                out[r + 1][c] = 0
    return out


def _canonical_palette_rival(grid):
    """Shortcut: perform the rule only for colors observed canonically (2..7)."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if (
                v in {2, 3, 4, 5, 6, 7}
                and grid[r][c + 1] == v
                and grid[r + 1][c] == v
                and grid[r + 1][c + 1] == v
            ):
                out[r][c + 1] = 0
                out[r + 1][c] = 0
    return out


def _has_mixed_color_full_window(grid) -> bool:
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            vals = {
                grid[r][c],
                grid[r][c + 1],
                grid[r + 1][c],
                grid[r + 1][c + 1],
            }
            if 0 not in vals and len(vals) > 1:
                return True
    return False


def _has_near_solid_window(grid) -> bool:
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [
                grid[r][c],
                grid[r][c + 1],
                grid[r + 1][c],
                grid[r + 1][c + 1],
            ]
            counts = Counter(v for v in vals if v != 0)
            if any(count == 3 for count in counts.values()):
                return True
    return False


def _has_novel_target(grid) -> bool:
    for r, c in _fires(grid):
        if grid[r][c] in {1, 8, 9}:
            return True
    return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "solid_2x2_transformation": lambda grid: _solve_grid(grid) != grid,
    "monochrome_required": _has_mixed_color_full_window,
    "solid_required": _has_near_solid_window,
    "palette_invariant": _has_novel_target,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity_rival,
    "ignore_monochrome": _all_nonzero_window_rival,
    "near_solid_is_block": _near_solid_rival,
    "canonical_palette_only": _canonical_palette_rival,
}

WITNESS_RIVALS = {
    "solid_2x2_transformation": ["identity"],
    "monochrome_required": ["ignore_monochrome"],
    "solid_required": ["near_solid_is_block"],
    "palette_invariant": ["canonical_palette_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_monochrome": _all_nonzero_window_rival,
    "near_solid_is_block": _near_solid_rival,
    "canonical_palette_only": _canonical_palette_rival,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demos still admit a named shortcut solution."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        expected = _solve_grid(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the solid-monochrome-2x2 rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(
                    f"demonstrations leave rival answer-equivalent on this query: {name}"
                )
    return reasons
