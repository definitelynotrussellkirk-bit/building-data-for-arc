"""Generator for d30c6cb51dac — build a reflection-relation matrix.

The input is a single row of 5-column panels separated by one zero column.
Each panel is cropped and binarized by the canonical rule.  The output is an
N×N relation matrix: 8 on the diagonal; 2 off diagonal exactly when one
normalized panel is the left/right OR up/down reflection of the other; 0
otherwise.

The curriculum deliberately includes 90-degree rotation and exact-copy decoys.
Those examples distinguish the selected two-reflection rule from tempting
"any dihedral transform", equal-cell-count, and reflexive-equivalence shortcuts.
"""
from __future__ import annotations

from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d30c6cb51dac"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d70de3d5eaf9"

SUMMARY = (
    "Split the 5-row input into 5-column panels separated by one zero column, "
    "crop each panel to its nonzero bounding box, and binarize nonzero cells. "
    "Return an N×N matrix with 8 on the diagonal and 2 off diagonal exactly "
    "when the destination panel is the left/right or up/down reflection of "
    "the source panel; all other off-diagonal cells are 0. Ordinary draws "
    "contain a real reflection pair plus a 90-degree rotation decoy, and "
    "larger draws also contain an exact-copy decoy whose off-diagonal relation "
    "remains 0 for asymmetric motifs."
)

INVARIANTS = [
    "background is color 0",
    "input height is 5 and width is 6*N-1 for N in 3..5",
    "panels are exactly 5 columns wide and separator columns are entirely 0",
    "every panel contains one 4-connected single-color asymmetric motif",
    "ordinary draws contain both positive reflection relations and negative same-area decoys",
    "panel colors and in-panel translations are irrelevant after crop-and-binarize",
    "the canonical Racket program is the sole output authority",
]

# Only exact properties recoverable from the returned grid are public axes.
AXES = {
    "n_panels": {
        "type": "int",
        "default": "scheduled 3,4,3,5",
        "valid": "3..5",
    },
    "color_mode": {
        "type": "str",
        "default": "scheduled monochrome/panelwise",
        "valid": "monochrome|panelwise",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95
# Reachable relation matrices under the scheduled 3/4/5-panel graph families:
# 3 labeled single-edge graphs + 12 labeled K1,2+isolated graphs + 15 labeled
# K2,2+isolated graphs. The finite output alphabet is intrinsic.
EXPECTED_OUTPUT_CODOMAIN = 30

SCHEDULE_PROFILES = (
    "canonical_lr",
    "copy_decoy_ud",
    "canonical_lr_shifted",
    "rich_ud",
)

Grid = list[list[int]]
Shape = tuple[tuple[int, int], ...]
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-slot schedule; every two-demo window covers both rule branches.

    Slots 0/2 are 3-panel monochrome canonical-profile anchors.  Slots 1/3
    are larger exact-copy decoys.  LR and UD positive branches alternate, so
    every consecutive two-demo lesson contains both reflection directions and
    at least one exact-copy negative witness.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _norm(cells) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return tuple(sorted((r - rmin, c - cmin) for r, c in cells))


def _flip_lr(cells) -> Shape:
    cells = _norm(cells)
    if not cells:
        return ()
    maxc = max(c for _, c in cells)
    return _norm((r, maxc - c) for r, c in cells)


def _flip_ud(cells) -> Shape:
    cells = _norm(cells)
    if not cells:
        return ()
    maxr = max(r for r, _ in cells)
    return _norm((maxr - r, c) for r, c in cells)


def _rot_cw(cells) -> Shape:
    cells = _norm(cells)
    if not cells:
        return ()
    maxr = max(r for r, _ in cells)
    return _norm((c, maxr - r) for r, c in cells)


def _dihedral(cells) -> set[Shape]:
    r0 = _norm(cells)
    r1 = _rot_cw(r0)
    r2 = _rot_cw(r1)
    r3 = _rot_cw(r2)
    return {r0, r1, r2, r3, _flip_lr(r0), _flip_lr(r1), _flip_lr(r2), _flip_lr(r3)}


def _connected(cells: Shape) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    stack = [next(iter(remaining))]
    seen = {stack[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARD:
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == len(remaining)


def _asym_motif(rng, k: int, s: int = 5) -> Shape:
    """Return a connected motif with all eight dihedral variants distinct."""
    for _ in range(300):
        start = (rng.randrange(s), rng.randrange(s))
        cells = [start]
        seen = {start}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice(_CARD)
            nxt = (r + dr, c + dc)
            if 0 <= nxt[0] < s and 0 <= nxt[1] < s and nxt not in seen:
                cells.append(nxt)
                seen.add(nxt)
        shape = _norm(cells)
        bh = 1 + max(r for r, _ in shape)
        bw = 1 + max(c for _, c in shape)
        if bh >= 2 and bw >= 2 and len(_dihedral(shape)) == 8:
            return shape
    # Chiral L tetromino: orbit size 8 under D4.
    return _norm(((0, 0), (1, 0), (2, 0), (2, 1)))


def _panel_shapes(grid: Any) -> tuple[list[Shape], list[int], list[str]]:
    """Parse fixed 5-wide panels; return normalized shapes, colors, errors."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], [], ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return [], [], ["grid rows must be non-empty sequences"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return [], [], ["grid must be rectangular"]
    h = len(grid)
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                return [], [], errors
    if h != 5:
        errors.append(f"expected height 5; found {h}")
    if (w + 1) % 6 != 0:
        errors.append(f"width {w} is not 6*N-1 for fixed 5-wide panels")
        return [], [], errors
    n = (w + 1) // 6
    if not 3 <= n <= 5:
        errors.append(f"expected 3..5 panels; width {w} encodes {n}")
        return [], [], errors

    for sep in (6 * i + 5 for i in range(n - 1)):
        if any(grid[r][sep] != 0 for r in range(h)):
            errors.append(f"separator column {sep} must be all background 0")

    shapes: list[Shape] = []
    colors: list[int] = []
    for i in range(n):
        c0 = 6 * i
        entries = [
            (r, c - c0, grid[r][c])
            for r in range(h)
            for c in range(c0, c0 + 5)
            if grid[r][c] != 0
        ]
        if not entries:
            errors.append(f"panel {i} is empty")
            shapes.append(())
            colors.append(0)
            continue
        palette = {value for _, _, value in entries}
        if len(palette) != 1:
            errors.append(f"panel {i} must use one nonzero color; found {sorted(palette)}")
        colors.append(min(palette))
        shape = _norm((r, c) for r, c, _ in entries)
        shapes.append(shape)
        if not 4 <= len(shape) <= 10:
            errors.append(f"panel {i} must contain 4..10 nonzero cells; found {len(shape)}")
        if shape:
            bh = 1 + max(r for r, _ in shape)
            bw = 1 + max(c for _, c in shape)
            if bh < 2 or bw < 2:
                errors.append(f"panel {i} motif must span at least 2 rows and 2 columns")
            if not _connected(shape):
                errors.append(f"panel {i} motif must be 4-connected")
    return shapes, colors, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar shared by canonical and generated inputs."""
    del difficulty, meta
    _, _, errors = _panel_shapes(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-input predicate used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public exact-axis value from the returned input."""
    shapes, colors, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(f"cannot observe overrides on malformed grid: {errors[0]}")
    n = len(shapes)
    distinct = len(set(colors))
    if distinct == 1:
        color_mode = "monochrome"
    elif distinct == n:
        color_mode = "panelwise"
    else:
        color_mode = "mixed"
    return {"n_panels": n, "color_mode": color_mode}


def _is_lr(a: Shape, b: Shape) -> bool:
    return bool(a) and b == _flip_lr(a)


def _is_ud(a: Shape, b: Shape) -> bool:
    return bool(a) and b == _flip_ud(a)


def _true_relation(a: Shape, b: Shape) -> bool:
    return _is_lr(a, b) or _is_ud(a, b)


def _matrix_from_shapes(shapes: list[Shape], relation: Callable[[Shape, Shape], bool]) -> Grid:
    n = len(shapes)
    return [
        [8 if i == j else 2 if relation(shapes[i], shapes[j]) else 0 for j in range(n)]
        for i in range(n)
    ]


def rule_mirror(grid) -> Grid:
    """Audit-only Python mirror; the Racket rule remains the output authority."""
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, _true_relation)


def _rival_diag_only(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, lambda a, b: False)


def _rival_lr_only(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, _is_lr)


def _rival_ud_only(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, _is_ud)


def _rival_full_dihedral(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, lambda a, b: b in _dihedral(a))


def _rival_same_cell_count(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, lambda a, b: len(a) == len(b))


def _rival_identity_plus_reflections(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    return _matrix_from_shapes(shapes, lambda a, b: a == b or _true_relation(a, b))


def _rival_fixed_first_pair(grid) -> Grid:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        raise ValueError(errors[0])
    n = len(shapes)
    return [
        [8 if i == j else 2 if {i, j} == {0, 1} else 0 for j in range(n)]
        for i in range(n)
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "diagonal_only": _rival_diag_only,
    "horizontal_only": _rival_lr_only,
    "vertical_only": _rival_ud_only,
    "full_dihedral": _rival_full_dihedral,
    "same_cell_count": _rival_same_cell_count,
    "identity_plus_reflections": _rival_identity_plus_reflections,
    "fixed_first_pair": _rival_fixed_first_pair,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid: Grid, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


def _has_lr_positive(grid: Grid) -> bool:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        return False
    return any(_is_lr(shapes[i], shapes[j]) and not _is_ud(shapes[i], shapes[j])
               for i in range(len(shapes)) for j in range(i + 1, len(shapes)))


def _has_ud_positive(grid: Grid) -> bool:
    shapes, _, errors = _panel_shapes(grid)
    if errors:
        return False
    return any(_is_ud(shapes[i], shapes[j]) and not _is_lr(shapes[i], shapes[j])
               for i in range(len(shapes)) for j in range(i + 1, len(shapes)))


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "positive_relation_present": lambda grid: _rival_differs(grid, "diagonal_only"),
    "horizontal_reflection_branch": lambda grid: _has_lr_positive(grid) and _rival_differs(grid, "vertical_only"),
    "vertical_reflection_branch": lambda grid: _has_ud_positive(grid) and _rival_differs(grid, "horizontal_only"),
    "rotation_is_not_a_match": lambda grid: _rival_differs(grid, "full_dihedral"),
    "equal_cell_count_is_not_enough": lambda grid: _rival_differs(grid, "same_cell_count"),
    "identity_is_not_automatically_related": lambda grid: _rival_differs(grid, "identity_plus_reflections"),
    "fixed_position_shortcut_refuted": lambda grid: _rival_differs(grid, "fixed_first_pair"),
}
WITNESS_RIVALS = {
    "positive_relation_present": ["diagonal_only"],
    "horizontal_reflection_branch": ["vertical_only"],
    "vertical_reflection_branch": ["horizontal_only"],
    "rotation_is_not_a_match": ["full_dihedral"],
    "equal_cell_count_is_not_enough": ["same_cell_count"],
    "identity_is_not_automatically_related": ["identity_plus_reflections"],
    "fixed_position_shortcut_refuted": ["fixed_first_pair"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a two-demo window that falsifies every named rival program."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with reflection-matrix rule")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input is invalid: {query_errors[0]}")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"competitor {name} fits every demonstration")
        except Exception as exc:
            reasons.append(f"competitor {name} errored: {type(exc).__name__}: {exc}")
    return reasons


def _default_axis_overrides(sample_index: int, overrides: dict[str, Any]) -> dict[str, Any]:
    """Pin the pedagogical schedule while still honoring caller overrides."""
    profile = int(sample_index) % 4
    defaults = {
        "n_panels": (3, 4, 3, 5)[profile],
        "color_mode": ("monochrome", "panelwise", "monochrome", "panelwise")[profile],
    }
    merged = dict(defaults)
    merged.update(overrides)
    return merged


def _order_selector(seed: int, sample_index: int) -> int:
    """Stride-safe deterministic selector for panel-order states.

    Training materialization commonly advances ``seed`` and ``sample_index``
    together.  Purely linear combinations alias against the 3/12/15-state
    relation families under that stride.  The schedule-block term breaks that
    alias: a same-profile +4/+4 advance changes this selector by 13, which is
    coprime to 3, 12, and 15.  Independent seed sweeps still cycle all states.
    """
    return int(seed) + 2 * int(sample_index) + int(sample_index) // 4


def _choose_order(variants: list[Shape], selector: int) -> list[Shape]:
    """Enumerate distinct labeled relation matrices and select one evenly.

    Permutations that produce the same matrix (because exact-copy vertices are
    interchangeable) are deduplicated.  Three-panel anchors therefore cover
    all three possible positive-pair locations, including the canonical 0↔1
    placement; the larger scheduled neighbor in every two-demo window still
    refutes the fixed-position shortcut.
    """
    unique: dict[tuple[tuple[int, ...], ...], list[Shape]] = {}
    for candidate in permutations(variants):
        shapes = list(candidate)
        truth = _matrix_from_shapes(shapes, _true_relation)
        key = tuple(tuple(row) for row in truth)
        unique.setdefault(key, shapes)
    choices = [unique[key] for key in sorted(unique)]
    if not choices:
        raise RuntimeError("no panel ordering is available")
    return list(choices[int(selector) % len(choices)])


def _place_shape(grid: Grid, c0: int, shape: Shape, color: int, rng) -> None:
    bh = 1 + max(r for r, _ in shape)
    bw = 1 + max(c for _, c in shape)
    top = rng.randint(0, 5 - bh)
    left = rng.randint(0, 5 - bw)
    for r, c in shape:
        grid[top + r][c0 + left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    scheduled = _default_axis_overrides(sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=scheduled,
    )
    n_panels = ctx.draw_int("n_panels", 3, 5)
    color_mode = ctx.draw_choice("color_mode", ("monochrome", "panelwise"))
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        k = rng.randint(4, 5)
    elif difficulty == "medium":
        k = rng.randint(5, 7)
    elif difficulty == "hard":
        k = rng.randint(7, 8)
    else:
        k = rng.randint(4, 8)
    base = _asym_motif(rng, k)
    lr = _flip_lr(base)
    ud = _flip_ud(base)
    rot = _rot_cw(base)

    # LR and UD alternate by sample_index so every consecutive two-demo lesson
    # contains both branches.  The 90-degree rotation is always a hard negative.
    positive = lr if int(sample_index) % 2 == 0 else ud
    variants: list[Shape] = [base, positive, rot]
    if n_panels >= 4:
        variants.append(base)  # exact-copy negative for asymmetric motifs
    if n_panels >= 5:
        variants.append(ud if positive == lr else lr)  # second reflection branch
    variants = _choose_order(variants, _order_selector(int(seed), int(sample_index)))

    if color_mode == "monochrome":
        color = rng.choice(range(1, 10))
        colors = [color] * n_panels
    else:
        colors = rng.sample(range(1, 10), n_panels)

    grid = full_grid(5, 6 * n_panels - 1, 0)
    for i, (shape, color) in enumerate(zip(variants, colors)):
        _place_shape(grid, 6 * i, shape, color, rng)

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generation error: {errors[0]}")
    return grid


def mutation_fixtures():
    """Task-specific malformed scenes that structural self_check must reject."""
    base = generate(99173, 1, difficulty="medium")
    fixtures: list[tuple[str, Grid]] = []

    painted_separator = [row[:] for row in base]
    painted_separator[2][5] = 9
    fixtures.append(("painted_separator", painted_separator))

    empty_panel = [row[:] for row in base]
    for r in range(5):
        for c in range(6, 11):
            empty_panel[r][c] = 0
    fixtures.append(("empty_panel", empty_panel))

    disconnected_panel = [row[:] for row in base]
    for r in range(5):
        for c in range(0, 5):
            disconnected_panel[r][c] = 0
    for r, c in ((0, 0), (0, 1), (4, 3), (4, 4)):
        disconnected_panel[r][c] = 1
    fixtures.append(("disconnected_panel", disconnected_panel))

    multicolor_panel = [row[:] for row in base]
    changed = False
    for r in range(5):
        for c in range(0, 5):
            if multicolor_panel[r][c] != 0:
                multicolor_panel[r][c] = 9 if multicolor_panel[r][c] != 9 else 8
                changed = True
                break
        if changed:
            break
    fixtures.append(("multicolor_panel", multicolor_panel))

    too_small_panel = [row[:] for row in base]
    for r in range(5):
        for c in range(12, 17):
            too_small_panel[r][c] = 0
    for r, c in ((1, 12), (1, 13), (2, 12)):
        too_small_panel[r][c] = 3
    fixtures.append(("three_cell_panel", too_small_panel))
    return fixtures
