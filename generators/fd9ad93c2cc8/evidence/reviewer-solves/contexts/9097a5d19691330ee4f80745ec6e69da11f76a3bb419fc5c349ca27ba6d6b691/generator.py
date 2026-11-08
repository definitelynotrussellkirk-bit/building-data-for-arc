"""Generator for ``fd9ad93c2cc8`` — mark centers of template matches.

The canonical task supplies a fixed red 3×3 V-shaped template in a left panel.
The board contains two or three copies in that orientation and one same-color
rotated decoy.  The output is a zero grid with color 8 at the true-copy centers.
"""
from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "fd9ad93c2cc8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0e1f3bb74fc4"

SUMMARY = (
    "A three-column left panel shows the red 3×3 V template (left arm plus "
    "bottom arm), followed by one full-height color-9 divider and a zero-"
    "background board. The board contains two or three exact copies of the "
    "shown orientation and exactly one rotated same-color V decoy. Mark color "
    "8 at the center of every true copy on an otherwise zero board-sized output."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the left panel is exactly three columns wide and contains the canonical red V template",
    "one full-height color-9 divider separates the template from the board",
    "the board has exactly two or three exact template matches",
    "the board has exactly one rotated red V decoy and at most one foreign-color singleton",
    "input color 8 is absent, so the rule visibly introduces every output mark",
]

COUNTER_HYPOTHESES = [
    "mark every red V regardless of orientation",
    "count red cells or connected components instead of matching the shown template",
    "copy the board or preserve the decoy in the output",
    "use a fixed location or fixed number of marks",
    "treat the optional foreign-color singleton as an answer marker",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "uniform 6..8 in every difficulty band",
        "valid": "6..8",
    },
    "board_w": {
        "type": "int",
        "default": "uniform 7..9 in every difficulty band",
        "valid": "7..9",
    },
    "match_count": {
        "type": "int",
        "default": "uniform 2..3 in every difficulty band",
        "valid": "2..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Canonical orientation: left vertical arm plus bottom horizontal arm.
_V_MASKS: tuple[frozenset[tuple[int, int]], ...] = (
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)}),
    frozenset({(0, 2), (1, 2), (2, 0), (2, 1), (2, 2)}),
)
_TEMPLATE_MASK = _V_MASKS[0]
_TEMPLATE_COLOR = 2
_MARK_COLOR = 8
_DIVIDER_COLOR = 9
_FOREIGN_COLORS = (3, 7)

# Strict linked signatures extracted from every canonical input.  Position is a
# nuisance; dimensions, target count, decoy orientation, and palette roles are
# linked exactly.  See canonical_profile_signature().
_CANONICAL_PROFILE_SIGNATURES = frozenset(
    {
        (6, 7, 2, (1, 0, 0), (7,)),
        (7, 7, 2, (0, 1, 0), (3,)),
        (7, 8, 3, (1, 0, 0), ()),
    }
)
_PROFILE_BY_AXES = {
    (6, 7, 2): (1, 7),
    (7, 7, 2): (2, 3),
    (7, 8, 3): (1, None),
}


class _Layout(NamedTuple):
    target_anchors: tuple[tuple[int, int], ...]
    decoy_anchor: tuple[int, int]
    occupied: tuple[tuple[int, int], ...]


class _Scene(NamedTuple):
    height: int
    board_width: int
    board: list[list[int]]
    target_hits: tuple[tuple[int, int], ...]
    decoy_hits: tuple[tuple[tuple[int, int], ...], ...]
    foreign_cells: tuple[tuple[int, int, int], ...]


def _valid_grid_shape(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _mask_hits(
    board: list[list[int]],
    mask: frozenset[tuple[int, int]],
    *,
    exact: bool = False,
) -> tuple[tuple[int, int], ...]:
    """Find 3×3 anchors matching the red required cells.

    ``exact=False`` mirrors the canonical Racket rule: template zeros are
    don't-care cells.  ``exact=True`` additionally requires those cells to be
    zero.  Generated target copies satisfy both interpretations because the
    canonical demonstrations do not disambiguate them.
    """
    h, w = len(board), len(board[0])
    found: list[tuple[int, int]] = []
    for r in range(h - 2):
        for c in range(w - 2):
            ok = True
            for dr in range(3):
                for dc in range(3):
                    value = board[r + dr][c + dc]
                    if (dr, dc) in mask:
                        if value != _TEMPLATE_COLOR:
                            ok = False
                            break
                    elif exact and value != 0:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                found.append((r, c))
    return tuple(found)


def _split_grid(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    h, w = len(grid), len(grid[0])
    divider_cols = [
        c for c in range(w) if all(grid[r][c] == _DIVIDER_COLOR for r in range(h))
    ]
    if divider_cols != [3]:
        raise ValueError(f"expected exactly one full-height divider at column 3, got {divider_cols}")
    if any(
        grid[r][c] == _DIVIDER_COLOR
        for r in range(h)
        for c in range(w)
        if c != 3
    ):
        raise ValueError("color 9 may appear only in the divider column")
    return [row[:3] for row in grid], [row[4:] for row in grid]


def _inspect_scene(grid) -> _Scene:
    if not _valid_grid_shape(grid):
        raise ValueError("expected a non-empty rectangular list-of-lists grid")
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 8):
        raise ValueError(f"expected grid height in 6..8, got {h}")
    if not (11 <= w <= 13):
        raise ValueError(f"expected total input width in 11..13, got {w}")
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                raise ValueError("grid contains a non-integer or color outside 0..9")
    if any(value == _MARK_COLOR for row in grid for value in row):
        raise ValueError("input color 8 is forbidden; it is reserved for output marks")

    left, board = _split_grid(grid)
    board_w = len(board[0])
    if not (7 <= board_w <= 9):
        raise ValueError(f"expected board width in 7..9, got {board_w}")

    template_cells = {
        (r, c)
        for r in range(h)
        for c in range(3)
        if left[r][c] != 0
    }
    if template_cells != set(_TEMPLATE_MASK):
        raise ValueError("left panel is not the canonical top-left 3×3 V template")
    if any(left[r][c] != _TEMPLATE_COLOR for r, c in template_cells):
        raise ValueError("template cells must all be color 2")

    target_hits = _mask_hits(board, _TEMPLATE_MASK)
    exact_hits = _mask_hits(board, _TEMPLATE_MASK, exact=True)
    if len(target_hits) not in (2, 3):
        raise ValueError(f"expected exactly two or three target matches, got {len(target_hits)}")
    if target_hits != exact_hits:
        raise ValueError("a target match relies on a wildcard-zero overlap rather than an exact 3×3 copy")

    decoy_hits = tuple(_mask_hits(board, mask) for mask in _V_MASKS[1:])
    if sum(len(hits) for hits in decoy_hits) != 1:
        raise ValueError("expected exactly one rotated same-color V decoy")

    foreign_cells = tuple(
        (r, c, board[r][c])
        for r in range(h)
        for c in range(board_w)
        if board[r][c] not in (0, _TEMPLATE_COLOR)
    )
    if len(foreign_cells) > 1:
        raise ValueError("expected at most one foreign-color singleton")
    if any(value not in _FOREIGN_COLORS for _, _, value in foreign_cells):
        raise ValueError("foreign singleton must use canonical distractor color 3 or 7")

    covered: set[tuple[int, int]] = set()
    for r, c in target_hits:
        covered.update((r + dr, c + dc) for dr, dc in _TEMPLATE_MASK)
    for variant_index, hits in enumerate(decoy_hits, start=1):
        for r, c in hits:
            covered.update((r + dr, c + dc) for dr, dc in _V_MASKS[variant_index])
    red_cells = {
        (r, c)
        for r in range(h)
        for c in range(board_w)
        if board[r][c] == _TEMPLATE_COLOR
    }
    if red_cells != covered:
        raise ValueError("every red board cell must belong to a target copy or the single rotated decoy")

    centers = {(r + 1, c + 1) for r, c in target_hits}
    if len(centers) != len(target_hits):
        raise ValueError("target matches must have distinct center cells")

    return _Scene(h, board_w, board, target_hits, decoy_hits, foreign_cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject inputs outside the canonical target-plus-rotated-decoy grammar."""
    del difficulty, meta
    try:
        _inspect_scene(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authoritative."""
    scene = _inspect_scene(grid)
    out = full_grid(scene.height, scene.board_width, 0)
    for r, c in scene.target_hits:
        out[r + 1][c + 1] = _MARK_COLOR
    return out


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    scene = _inspect_scene(grid)
    return {
        "grid_h": scene.height,
        "board_w": scene.board_width,
        "match_count": len(scene.target_hits),
    }


def canonical_profile_signature(grid):
    """Return the strict linked canonical signature, or ``None`` for broader draws."""
    try:
        scene = _inspect_scene(grid)
    except (TypeError, ValueError):
        return None
    signature = (
        scene.height,
        scene.board_width,
        len(scene.target_hits),
        tuple(len(hits) for hits in scene.decoy_hits),
        tuple(sorted(value for _, _, value in scene.foreign_cells)),
    )
    return signature if signature in _CANONICAL_PROFILE_SIGNATURES else None


def is_canonical_profile(grid) -> bool:
    return canonical_profile_signature(grid) is not None


def _painted_cells(anchor: tuple[int, int], mask: frozenset[tuple[int, int]]):
    r, c = anchor
    return {(r + dr, c + dc) for dr, dc in mask}


@lru_cache(maxsize=None)
def _layout_bank(
    h: int,
    w: int,
    target_count: int,
    decoy_variant: int,
) -> tuple[_Layout, ...]:
    """Build a deterministic bank of valid target/decoy arrangements.

    Required cells may share empty 3×3 bounding-box space, as in the canonical
    test example, but every target window remains exact and the only rotated
    mask occurrence is the intended decoy.
    """
    if decoy_variant not in (1, 2, 3):
        raise ValueError(f"invalid decoy variant {decoy_variant}")
    anchors = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    rng = stable_rng(
        0,
        f"{TASK_ID}|layout-bank|{h}|{w}|{target_count}|{decoy_variant}",
        VERSION,
    )
    layouts: list[_Layout] = []
    seen: set[tuple] = set()
    desired = 16
    max_attempts = 150_000

    for _ in range(max_attempts):
        target_anchors = tuple(sorted(rng.sample(anchors, target_count)))
        decoy_anchor = rng.choice(anchors)
        occupied: set[tuple[int, int]] = set()
        for anchor in target_anchors:
            occupied.update(_painted_cells(anchor, _TEMPLATE_MASK))
        occupied.update(_painted_cells(decoy_anchor, _V_MASKS[decoy_variant]))
        signature = (target_anchors, decoy_anchor, tuple(sorted(occupied)))
        if signature in seen:
            continue

        board = full_grid(h, w, 0)
        for r, c in occupied:
            board[r][c] = _TEMPLATE_COLOR
        if set(_mask_hits(board, _TEMPLATE_MASK)) != set(target_anchors):
            continue
        if set(_mask_hits(board, _TEMPLATE_MASK, exact=True)) != set(target_anchors):
            continue
        valid_decoys = True
        for variant in (1, 2, 3):
            expected = {decoy_anchor} if variant == decoy_variant else set()
            if set(_mask_hits(board, _V_MASKS[variant])) != expected:
                valid_decoys = False
                break
        if not valid_decoys:
            continue

        seen.add(signature)
        layouts.append(
            _Layout(target_anchors, decoy_anchor, tuple(sorted(occupied)))
        )
        if len(layouts) >= desired:
            break

    if not layouts:
        raise RuntimeError(
            f"no valid layouts for {h}x{w}, matches={target_count}, decoy={decoy_variant}"
        )
    return tuple(layouts)


def _safe_singleton_positions(
    h: int,
    w: int,
    layout: _Layout,
) -> tuple[tuple[int, int], ...]:
    occupied = set(layout.occupied)
    target_windows: set[tuple[int, int]] = set()
    for r, c in layout.target_anchors:
        target_windows.update(
            (rr, cc)
            for rr in range(r, r + 3)
            for cc in range(c, c + 3)
        )
    return tuple(
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in occupied and (r, c) not in target_windows
    )


def _choose_generalized_decoy(difficulty, rng) -> int:
    if difficulty == "easy":
        return rng.choice((1, 2))
    if difficulty == "hard":
        return rng.choice((1, 2, 3, 3))
    return rng.choice((1, 2, 3))


def _choose_generalized_singleton(difficulty, rng) -> int | None:
    if difficulty == "easy":
        return rng.choice((3, 7))
    if difficulty == "hard":
        return rng.choice((None, None, 3, 7))
    return rng.choice((None, 3, 7))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
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
    h = ctx.draw_int("grid_h", 6, 8)
    board_w = ctx.draw_int("board_w", 7, 9)
    target_count = ctx.draw_int("match_count", 2, 3)
    rng = ctx.draw_rng("layout")

    profile = _PROFILE_BY_AXES.get((h, board_w, target_count))
    if profile is None:
        decoy_variant = _choose_generalized_decoy(difficulty, rng)
        singleton_color = _choose_generalized_singleton(difficulty, rng)
    else:
        decoy_variant, singleton_color = profile

    layouts = _layout_bank(h, board_w, target_count, decoy_variant)
    layout = rng.choice(layouts)
    board = full_grid(h, board_w, 0)
    for r, c in layout.occupied:
        board[r][c] = _TEMPLATE_COLOR

    if singleton_color is not None:
        safe = _safe_singleton_positions(h, board_w, layout)
        if not safe:
            raise RuntimeError("selected layout has no safe foreign-singleton position")
        r, c = rng.choice(safe)
        board[r][c] = singleton_color

    template_panel = full_grid(h, 3, 0)
    for r, c in _TEMPLATE_MASK:
        template_panel[r][c] = _TEMPLATE_COLOR
    grid = assemble_vertical_panels([template_panel, board], divider=_DIVIDER_COLOR)

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors[0]}")
    return grid
