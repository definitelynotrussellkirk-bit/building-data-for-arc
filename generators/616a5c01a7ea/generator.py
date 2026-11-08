"""Semantic generator for ARC task 616a5c01a7ea (source 8e5a5113).

The input is an ``n x (3n+2)`` strip.  A square source panel occupies the
left section, two full color-5 separator columns divide the strip, and the
middle/right target sections are blank.  The Racket rule preserves the source,
places its 90-degree clockwise rotation in the middle, and places its
180-degree rotation on the right.

Version 2 rebuilds the teaching distribution around the actual transform.
Every ordinary source panel has enough colors and occupied cells to expose
spatial structure, and its four rotations are distinct.  A pinned canonical
anchor reproduces the demonstrated 3x3/full/three-color morphology in every
difficulty band; generalized dense and sparse panels vary size and palette
without introducing no-op, monochrome, or rotationally ambiguous lessons.

Version 2.1 decouples the ordinary palette-size draw from the difficulty-
skewed panel-size draw.  The previous pair used identical normalized bands,
which made the two declared axes move in lockstep despite their separate
semantics and exact override surfaces.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "616a5c01a7ea"
TASK_ID = "616a5c01a7ea"
VERSION = "2.1.0"
RULE_HASH = "79b7067ac64d"

SUMMARY = (
    "Read the square panel left of the first color-5 separator; keep it in "
    "place, fill the middle square with its 90-degree clockwise rotation, "
    "and fill the right square with its 180-degree rotation."
)

INVARIANTS = [
    "height n is in 3..7 and width is exactly 3*n+2",
    "columns n and 2*n+1 are entirely color 5",
    "the middle and right n-by-n target sections are entirely zero",
    "the source section excludes separator color 5 and uses exactly 3..6 nonzero colors",
    "the source is dense or at least half occupied and its 0/90/180/270 rotations are distinct",
    "ordinary draws include a canonical 3x3 dense three-color anchor in every difficulty band",
]

AXES = {
    "grid_n": {
        "type": "int",
        "default": "difficulty-skewed 3..7 with a canonical 3x3 anchor",
        "valid": "3..7",
    },
    "palette_size": {
        "type": "int",
        "default": "independent uniform 3..6 with a canonical three-color anchor",
        "valid": "3..6",
    },
    "fill_mode": {
        "type": "str",
        "default": "dense|sparse, with canonical anchors dense",
        "valid": "dense|sparse",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CANONICAL_COUNT_PROFILES = ((1, 3, 5), (1, 2, 6))
_CANONICAL_ANCHOR_RATE = 0.30


def _rotate90(panel):
    return [list(row) for row in zip(*panel[::-1])]


def _rotation_signatures(panel):
    signatures = []
    current = [list(row) for row in panel]
    for _ in range(4):
        signatures.append(tuple(tuple(row) for row in current))
        current = _rotate90(current)
    return tuple(signatures)


def _d4_signature_count(panel):
    signatures = set()
    current = [list(row) for row in panel]
    for _ in range(4):
        signatures.add(tuple(tuple(row) for row in current))
        signatures.add(tuple(tuple(reversed(row)) for row in current))
        current = _rotate90(current)
    return len(signatures)


def _rotations_are_distinct(panel):
    return len(set(_rotation_signatures(panel))) == 4


def _canonical_panel(palette, rng):
    """Create a strict demonstrated-manifold panel with generalized placement."""
    cells = [(r, c) for r in range(3) for c in range(3)]
    corners = ((0, 0), (0, 2), (2, 0), (2, 2))
    for _ in range(512):
        colors = list(palette)
        rng.shuffle(colors)
        singleton, secondary, modal = colors
        counts = rng.choice(_CANONICAL_COUNT_PROFILES)
        singleton_pos = rng.choice(corners)
        remaining = [cell for cell in cells if cell != singleton_pos]
        rng.shuffle(remaining)
        secondary_count = counts[1]
        panel = [[modal for _ in range(3)] for _ in range(3)]
        panel[singleton_pos[0]][singleton_pos[1]] = singleton
        for r, c in remaining[:secondary_count]:
            panel[r][c] = secondary
        if _rotations_are_distinct(panel) and _d4_signature_count(panel) == 8:
            return panel
    raise RuntimeError("failed to construct a rotationally discriminative canonical panel")


def _general_panel(n, palette, fill_mode, rng):
    cell_count = n * n
    palette_size = len(palette)
    for _ in range(512):
        if fill_mode == "dense":
            occupied = list(range(cell_count))
        else:
            minimum = max(palette_size + 1, (cell_count + 1) // 2)
            occupied_count = rng.randint(minimum, cell_count - 1)
            occupied = rng.sample(range(cell_count), occupied_count)

        values = list(palette)
        values.extend(rng.choice(palette) for _ in range(len(occupied) - palette_size))
        rng.shuffle(values)
        panel = [[0 for _ in range(n)] for _ in range(n)]
        for index, value in zip(occupied, values):
            panel[index // n][index % n] = value

        # A generalized 3x3 dense three-color draw must not accidentally be
        # counted as the strict empirical profile reserved for the anchor.
        counts = sorted(Counter(value for row in panel for value in row if value).values())
        if n == 3 and palette_size == 3 and fill_mode == "dense" and tuple(counts) in _CANONICAL_COUNT_PROFILES:
            continue
        if _rotations_are_distinct(panel) and _d4_signature_count(panel) == 8:
            return panel
    raise RuntimeError("failed to construct a rotationally discriminative source panel")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    has_semantic_override = any(
        name in overrides and overrides[name] is not None for name in AXES
    )
    canonical_anchor = (
        not has_semantic_override
        and ctx.draw_rng("canonical_anchor").random() < _CANONICAL_ANCHOR_RATE
    )

    if canonical_anchor:
        n = ctx.draw_int("grid_n", 3, 3)
        palette_size = ctx.draw_int("palette_size", 3, 3)
        fill_mode = ctx.draw_choice("fill_mode", ("dense",))
    else:
        n = ctx.draw_int_diff("grid_n", 3, 7)
        # Palette complexity is a real, separately observable axis.  Using a
        # second draw_int_diff here mapped the same normalized difficulty band
        # onto 3..6 and made palette_size follow grid_n one-for-one in the
        # ordinary lint cohort.  Keep size difficulty-aware, but sample the
        # palette independently so the two axes span a genuine product space.
        palette_size = ctx.draw_int("palette_size", 3, 6)
        fill_mode = ctx.draw_choice("fill_mode", ("dense", "sparse"))

    rng = ctx.draw_rng("layout")
    palette = rng.sample(list(_COLORS), palette_size)
    panel = (
        _canonical_panel(palette, rng)
        if canonical_anchor
        else _general_panel(n, palette, fill_mode, rng)
    )

    grid = full_grid(n, 3 * n + 2, 0)
    for r in range(n):
        grid[r][:n] = panel[r]
        grid[r][n] = 5
        grid[r][2 * n + 1] = 5
    return grid


def observe_overrides(grid):
    """Recover every declared axis exactly from a returned grid."""
    n = len(grid)
    source = [row[:n] for row in grid]
    colors = {value for row in source for value in row if value not in (0, 5)}
    return {
        "grid_n": n,
        "palette_size": len(colors),
        "fill_mode": "dense" if all(value != 0 for row in source for value in row) else "sparse",
    }


def strict_canonical_like(grid):
    """Strict linked empirical-manifold predicate for count-backed audits."""
    if _grid_shape_errors(grid):
        return False
    if len(grid) != 3 or len(grid[0]) != 11:
        return False
    source = [list(row[:3]) for row in grid]
    if any(value == 0 or value == 5 for row in source for value in row):
        return False
    if any(grid[r][3] != 5 or grid[r][7] != 5 for r in range(3)):
        return False
    if any(
        grid[r][c] != 0
        for r in range(3)
        for c in (*range(4, 7), *range(8, 11))
    ):
        return False
    counts = Counter(value for row in source for value in row)
    if tuple(sorted(counts.values())) not in _CANONICAL_COUNT_PROFILES:
        return False
    singleton = next((color for color, count in counts.items() if count == 1), None)
    if singleton is None:
        return False
    return any(source[r][c] == singleton for r, c in ((0, 0), (0, 2), (2, 0), (2, 2)))


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md, v1).
# strict_canonical_like above predates the contract and lawfully returns a
# bool (amended contract, dispatched on type) — kept as is.
# ---------------------------------------------------------------------------

def _witness_canonical_anchor(grid) -> bool:
    """The pinned canonical 3x3 dense three-color anchor actually appears."""
    return bool(strict_canonical_like(grid))


def _witness_larger_panel(grid) -> bool:
    """Generalized branch: a source panel larger than the canonical 3x3."""
    return len(grid) > 3 if isinstance(grid, list) and grid else False


def _witness_dense_source(grid) -> bool:
    """Dense branch: the source panel has no zero cells."""
    if not isinstance(grid, list) or not grid:
        return False
    n = len(grid)
    return all(value != 0 for row in grid for value in row[:n])


def _witness_sparse_source(grid) -> bool:
    """Sparse branch: the source panel keeps at least one zero cell."""
    if not isinstance(grid, list) or not grid:
        return False
    n = len(grid)
    return any(value == 0 for row in grid for value in row[:n])


def _witness_rotation_discriminative(grid) -> bool:
    """The source's 8 D4 transforms are pairwise distinct, so clockwise vs
    counter-clockwise vs mirror are all distinguishable from the demo."""
    if not isinstance(grid, list) or not grid:
        return False
    n = len(grid)
    source = [list(row[:n]) for row in grid]
    return _rotations_are_distinct(source) and _d4_signature_count(source) == 8


SEMANTIC_WITNESSES = {
    "canonical_3x3_anchor": _witness_canonical_anchor,
    "generalized_larger_panel": _witness_larger_panel,
    "dense_source_panel": _witness_dense_source,
    "sparse_source_panel": _witness_sparse_source,
    "rotation_discriminative_source": _witness_rotation_discriminative,
}


def _flip_lr(panel):
    return [list(reversed(row)) for row in panel]


def _flip_ud(panel):
    return [list(row) for row in reversed(panel)]


def _slot_variant(grid, middle_fn, right_fn):
    """Fill the two target slots from transforms of the source panel, or None
    when the grid does not have the n x (3n+2) two-separator shape."""
    if _grid_shape_errors(grid):
        return None
    n = len(grid)
    if len(grid[0]) != 3 * n + 2:
        return None
    source = [list(row[:n]) for row in grid]
    middle = middle_fn(source)
    right = right_fn(source)
    output = [list(row) for row in grid]
    for r in range(n):
        output[r][n + 1:2 * n + 1] = middle[r]
        output[r][2 * n + 2:3 * n + 2] = right[r]
    return output


def _rot180(panel):
    return _rotate90(_rotate90(panel))


def _rot270(panel):
    return _rotate90(_rot180(panel))


def _competitor_ccw_middle(grid):
    """Competing rule: rotate the middle slot COUNTER-clockwise (right slot
    still 180)."""
    return _slot_variant(grid, _rot270, _rot180)


def _competitor_180_middle(grid):
    """Competing rule: the slots swapped — 180 in the MIDDLE slot, clockwise
    on the right."""
    return _slot_variant(grid, _rot180, _rotate90)


def _competitor_mirror(grid):
    """Competing rule: MIRROR instead of rotate — left-right mirror in the
    middle slot, up-down mirror on the right."""
    return _slot_variant(grid, _flip_lr, _flip_ud)


_LESSON_COMPETITORS = {
    "rotate the middle slot counter-clockwise": _competitor_ccw_middle,
    "180 in the middle slot, clockwise on the right": _competitor_180_middle,
    "mirror instead of rotate": _competitor_mirror,
}


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos uniquely determine the query answer.

    Every generated source has 8 distinct D4 transforms, so any correct demo
    falsifies all three competitors; a symmetric-panel regression would make
    a competitor survive and be reported here. Pure: no mutation, no RNG."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if _grid_shape_errors(demo["input"]) or len(demo["input"][0]) != 3 * len(demo["input"]) + 2:
            reasons.append(f"demo {index} input is not an n x (3n+2) strip")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(
                f"demo {index} output does not match the keep/rotate-cw/"
                "rotate-180 rule"
            )
    if _grid_shape_errors(query["input"]) or len(query["input"][0]) != 3 * len(query["input"]) + 2:
        reasons.append("query input is not an n x (3n+2) strip")
        return reasons
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' is consistent with every demo but "
                "answers the query differently"
            )
    return reasons


def rule_mirror(grid):
    """Diagnostic Python mirror; the canonical Racket rule remains authority."""
    n = len(grid)
    source = [list(row[:n]) for row in grid]
    clockwise = _rotate90(source)
    half_turn = _rotate90(clockwise)
    output = [row[:] for row in grid]
    for r in range(n):
        output[r][n + 1:2 * n + 1] = clockwise[r]
        output[r][2 * n + 2:3 * n + 2] = half_turn[r]
    return output


def _grid_shape_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the transform-bearing input grammar, not merely dimensions."""
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    n = len(grid)
    width = len(grid[0])
    if not 3 <= n <= 7:
        errors.append(f"height must be in 3..7, got {n}")
    expected_width = 3 * n + 2
    if width != expected_width:
        errors.append(f"width must be 3*n+2={expected_width}, got {width}")
        return errors

    for separator in (n, 2 * n + 1):
        if any(grid[r][separator] != 5 for r in range(n)):
            errors.append(f"separator column {separator} must be entirely color 5")

    for r in range(n):
        for c in range(n + 1, 2 * n + 1):
            if grid[r][c] != 0:
                errors.append(f"middle target section must be blank; found {grid[r][c]} at ({r},{c})")
                break
        if errors and errors[-1].startswith("middle target"):
            break
    for r in range(n):
        for c in range(2 * n + 2, 3 * n + 2):
            if grid[r][c] != 0:
                errors.append(f"right target section must be blank; found {grid[r][c]} at ({r},{c})")
                break
        if errors and errors[-1].startswith("right target"):
            break

    source = [list(row[:n]) for row in grid]
    if any(value == 5 for row in source for value in row):
        errors.append("source section must not reuse separator color 5")
    colors = {value for row in source for value in row if value not in (0, 5)}
    if not 3 <= len(colors) <= 6:
        errors.append(f"source must use exactly 3..6 nonzero non-separator colors, got {len(colors)}")
    occupied = sum(value != 0 for row in source for value in row)
    minimum_occupied = max(len(colors) + 1, (n * n + 1) // 2)
    if occupied < minimum_occupied:
        errors.append(
            f"source must be structurally populated: {occupied} occupied cells < {minimum_occupied}"
        )
    if not _rotations_are_distinct(source):
        errors.append("source must have distinct 0/90/180/270-degree rotations")
    return errors


def _blank_valid_grid(n=3):
    grid = full_grid(n, 3 * n + 2, 0)
    for r in range(n):
        grid[r][n] = 5
        grid[r][2 * n + 1] = 5
    return grid


def mutation_fixtures():
    """Task-linked impostors that self_check must reject."""
    valid = generate(616051, 7, difficulty="medium", grid_n=3, palette_size=3, fill_mode="dense")

    wrong_width = [row[:-1] for row in valid]

    broken_separator = [row[:] for row in valid]
    broken_separator[0][3] = 0

    prefilled_target = [row[:] for row in valid]
    prefilled_target[1][4] = 2

    separator_leak = [row[:] for row in valid]
    separator_leak[0][0] = 5

    rotationally_ambiguous = _blank_valid_grid(3)
    symmetric_panel = (
        (1, 2, 1),
        (3, 1, 3),
        (1, 2, 1),
    )
    for r in range(3):
        rotationally_ambiguous[r][:3] = list(symmetric_panel[r])

    return [
        ("wrong_width", wrong_width),
        ("broken_separator", broken_separator),
        ("prefilled_target", prefilled_target),
        ("separator_color_leaks_into_source", separator_leak),
        ("rotationally_ambiguous_source", rotationally_ambiguous),
    ]
