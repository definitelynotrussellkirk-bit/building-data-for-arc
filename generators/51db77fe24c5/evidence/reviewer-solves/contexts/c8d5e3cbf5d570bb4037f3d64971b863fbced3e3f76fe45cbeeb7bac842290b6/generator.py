"""Semantic generator for ARC task 51db77fe24c5.

The input contains separated blue objects on a black background.  The rule
recolors exactly those blue connected components that are solid 2x2 squares to
red; every other blue object is preserved.

The sampler deliberately includes two independent negative controls in every
instance:

* a three-cell L whose bounding box is 2x2, defeating a bounding-box shortcut;
* a four-cell zigzag, defeating the shortcut "recolor every size-4 object";
* a broad distractor drawn from several shape families, including a large
  open-ended polyomino family, defeating memorization of a finite mask list.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "51db77fe24c5"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "06fb2695c6fe"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Recolor every exact blue 2x2-square component red while preserving every "
    "other blue component."
)

INVARIANTS = [
    "zero is the background and one is the only input object color",
    "all blue objects are separate four-connected components",
    "at least one component is exactly a solid 2x2 square",
    "at least one blue component is not an exact 2x2 square",
    "every generated input includes a 2x2-bounding-box L-triomino control",
    "every generated input includes a non-square four-cell control",
    "every generated input includes one additional broad distractor",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

DISTRACTOR_KINDS = ("domino", "line3", "line4", "t4", "polyomino")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted keyed choice over the full domain",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted keyed choice over the full domain",
        "valid": "8..14",
    },
    "square_count": {
        "type": "int",
        "default": "difficulty-weighted keyed choice over the full domain",
        "valid": "1..2",
    },
    "distractor_kind": {
        "type": "str",
        "default": "weighted keyed choice with broad polyomino coverage",
        "valid": "domino|line3|line4|t4|polyomino",
    },
}

_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_SIZE4_CONTROL = ((0, 1), (0, 2), (1, 0), (1, 1))
_NONLEGACY_LS = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_T_TETROMINOES = (
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
)
_LEGACY_DISTRACTOR_MASKS = frozenset(
    {
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (1, 1)),
    }
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for axis in ("grid_h", "grid_w", "square_count"):
        value = overrides.get(axis)
        if value is not None and type(value) is not int:
            raise TypeError(f"{axis} must be an integer, not {type(value).__name__}")
    value = overrides.get("distractor_kind")
    if value is not None and type(value) is not str:
        raise TypeError(
            "distractor_kind must be a string, "
            f"not {type(value).__name__}"
        )


def _weighted_int(ctx, label: str, lo: int, hi: int, favored: Iterable[int]) -> int:
    """Draw over the full override domain while only weighting defaults."""
    options = list(range(lo, hi + 1))
    options.extend(value for value in favored for _ in range(4))
    return ctx.draw_choice(label, options)


def _draw_axes(ctx, difficulty: str | None) -> tuple[int, int, int, str]:
    if difficulty == "easy":
        h_favored = w_favored = (8, 9)
        square_favored = (1,)
        kind_options = DISTRACTOR_KINDS + ("domino", "line3", "line4", "polyomino")
    elif difficulty == "hard":
        # Keep canonical-scale support in every band while hard mode adds
        # complexity through two targets and richer distractors.
        h_favored = w_favored = (8, 10, 12, 14)
        square_favored = (2,)
        kind_options = DISTRACTOR_KINDS + (
            "t4",
            "t4",
            "polyomino",
            "polyomino",
            "polyomino",
            "polyomino",
            "polyomino",
        )
    else:
        h_favored = w_favored = (9, 10, 11, 12)
        square_favored = (1, 2)
        kind_options = DISTRACTOR_KINDS + (
            "t4",
            "polyomino",
            "polyomino",
            "polyomino",
            "polyomino",
            "polyomino",
        )

    h = _weighted_int(ctx, "grid_h", 8, 14, h_favored)
    w = _weighted_int(ctx, "grid_w", 8, 14, w_favored)
    square_count = _weighted_int(ctx, "square_count", 1, 2, square_favored)
    kind = ctx.draw_choice("distractor_kind", kind_options)
    return h, w, square_count, kind


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _polyomino_mask(rng) -> tuple[tuple[int, int], ...]:
    """Grow a connected 5..8-cell mask inside a 4x4 bounding box.

    Growth, rather than a fixed catalogue, keeps the distractor support broad.
    The bounded box guarantees that even the smallest declared 8x8 canvas can
    place this shape alongside two squares and the mandatory L witness.
    """
    for _ in range(256):
        target_size = rng.randint(5, 8)
        cells = {(0, 0)}
        while len(cells) < target_size:
            frontier = sorted(
                {
                    (r + dr, c + dc)
                    for r, c in cells
                    for dr, dc in _CARDINAL
                    if (r + dr, c + dc) not in cells
                }
            )
            cells.add(rng.choice(frontier))
        mask = _normalize(cells)
        height = max(r for r, _ in mask) + 1
        width = max(c for _, c in mask) + 1
        if height <= 4 and width <= 4:
            return mask
    raise RuntimeError("could not grow a bounded polyomino")


def _broad_mask(kind: str, rng) -> tuple[tuple[int, int], ...]:
    if kind == "domino":
        return rng.choice(
            (
                ((0, 0), (0, 1)),
                ((0, 0), (1, 0)),
            )
        )
    if kind == "line3":
        return rng.choice(
            (
                ((0, 0), (0, 1), (0, 2)),
                ((0, 0), (1, 0), (2, 0)),
            )
        )
    if kind == "line4":
        return rng.choice(
            (
                ((0, 0), (0, 1), (0, 2), (0, 3)),
                ((0, 0), (1, 0), (2, 0), (3, 0)),
            )
        )
    if kind == "t4":
        return rng.choice(_T_TETROMINOES)
    if kind == "polyomino":
        return _polyomino_mask(rng)
    raise ValueError(f"unknown distractor kind: {kind!r}")


def _placements(mask: tuple[tuple[int, int], ...], h: int, w: int):
    shape_h = max(r for r, _ in mask) + 1
    shape_w = max(c for _, c in mask) + 1
    return [
        frozenset((r0 + r, c0 + c) for r, c in mask)
        for r0 in range(h - shape_h + 1)
        for c0 in range(w - shape_w + 1)
    ]


def _touches_orthogonally(cells: frozenset[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return any(
        (r + dr, c + dc) in occupied
        for r, c in cells
        for dr, dc in _CARDINAL
    )


def _place_shapes(
    h: int,
    w: int,
    masks: list[tuple[tuple[int, int], ...]],
    rng,
) -> list[list[int]]:
    """Constructively place every shape, backtracking rather than dropping one."""
    candidates: list[list[frozenset[tuple[int, int]]]] = []
    for mask in masks:
        options = _placements(mask, h, w)
        rng.shuffle(options)
        candidates.append(options)

    # Most constrained / largest shapes first substantially reduces backtracking
    # while preserving keyed randomness within each candidate list.
    order = sorted(
        range(len(masks)),
        key=lambda index: (len(candidates[index]), -len(masks[index]), index),
    )
    occupied: set[tuple[int, int]] = set()
    chosen: dict[int, frozenset[tuple[int, int]]] = {}

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for cells in candidates[index]:
            if cells & occupied or _touches_orthogonally(cells, occupied):
                continue
            occupied.update(cells)
            chosen[index] = cells
            if search(depth + 1):
                return True
            occupied.difference_update(cells)
            chosen.pop(index, None)
        return False

    if not search(0):
        raise RuntimeError(f"could not place {len(masks)} separated shapes in {h}x{w}")

    grid = full_grid(h, w, 0)
    for index in range(len(masks)):
        for r, c in chosen[index]:
            grid[r][c] = 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, square_count, kind = _draw_axes(ctx, difficulty)
    shape_rng = ctx.draw_rng("shape_family")
    mandatory_l = shape_rng.choice(_NONLEGACY_LS)
    broad = _broad_mask(kind, shape_rng)
    masks = [_SQUARE for _ in range(square_count)] + [
        mandatory_l,
        _SIZE4_CONTROL,
        broad,
    ]
    return _place_shapes(h, w, masks, ctx.draw_rng("layout"))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    invalid = [
        value
        for row in grid
        for value in row
        if type(value) is not int or value not in (0, 1)
    ]
    if invalid:
        return ["input cells must be integer colors 0 or 1"]
    return []


def _blue_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _component_masks(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    return [_normalize(component) for component in _blue_components(grid)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors
    found = _component_masks(grid)
    square_count = sum(mask == _SQUARE for mask in found)
    nonsquare_count = sum(mask != _SQUARE for mask in found)
    if square_count < 1:
        errors.append("no exact blue 2x2-square target component")
    if nonsquare_count < 1:
        errors.append("no non-square blue distractor component")
    return errors


def strict_canonical_like(grid):
    """Structural canonical manifold; curriculum controls live in witnesses."""
    return self_check(grid)


def _classify_broad(mask: tuple[tuple[int, int], ...]) -> str:
    if mask in {((0, 0), (0, 1)), ((0, 0), (1, 0))}:
        return "domino"
    if mask in {((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0))}:
        return "line3"
    if mask in {
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
    }:
        return "line4"
    if mask in _T_TETROMINOES:
        return "t4"
    if 5 <= len(mask) <= 8:
        return "polyomino"
    raise ValueError(f"unclassified broad distractor mask: {mask}")


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis solely from returned pixels."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    found = _component_masks(grid)
    squares = [mask for mask in found if mask == _SQUARE]
    nonsquares = [mask for mask in found if mask != _SQUARE]
    mandatory = [mask for mask in nonsquares if mask in _NONLEGACY_LS]
    if len(mandatory) != 1:
        raise ValueError(f"expected one nonlegacy L witness, found {len(mandatory)}")
    controls = [mask for mask in nonsquares if mask == _SIZE4_CONTROL]
    if len(controls) != 1:
        raise ValueError(f"expected one size-4 control, found {len(controls)}")
    broad = list(nonsquares)
    broad.remove(mandatory[0])
    broad.remove(controls[0])
    if len(broad) != 1:
        raise ValueError(f"expected one broad distractor, found {len(broad)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "square_count": len(squares),
        "distractor_kind": _classify_broad(broad[0]),
    }


def _rule_mirror(grid):
    """Independent-readable Python mirror used only by semantic contracts/tests."""
    out = [list(row) for row in grid]
    for component in _blue_components(grid):
        if _normalize(component) == _SQUARE:
            for r, c in component:
                out[r][c] = 2
    return out


def _legacy_mask_memorizer(grid):
    """Wrong historical shortcut: preserve only three memorized masks."""
    out = [list(row) for row in grid]
    for component in _blue_components(grid):
        if _normalize(component) not in _LEGACY_DISTRACTOR_MASKS:
            for r, c in component:
                out[r][c] = 2
    return out


def _bbox_2x2(grid):
    """Wrong shortcut: recolor any component whose bounding box is 2x2."""
    out = [list(row) for row in grid]
    for component in _blue_components(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        if max(rows) - min(rows) == 1 and max(cols) - min(cols) == 1:
            for r, c in component:
                out[r][c] = 2
    return out


def _all_blue(grid):
    return [[2 if value == 1 else value for value in row] for row in grid]


def _size4(grid):
    """Wrong shortcut: recolor every four-cell blue component."""
    out = [list(row) for row in grid]
    for component in _blue_components(grid):
        if len(component) == 4:
            for r, c in component:
                out[r][c] = 2
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _has_nonlegacy_l(grid) -> bool:
    return any(mask in _NONLEGACY_LS for mask in _component_masks(grid))


def _has_bbox_2x2_nonsquare(grid) -> bool:
    for component in _blue_components(grid):
        mask = _normalize(component)
        if mask == _SQUARE:
            continue
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        if max(rows) - min(rows) == 1 and max(cols) - min(cols) == 1:
            return True
    return False


def _has_size4_nonsquare(grid) -> bool:
    return _SIZE4_CONTROL in _component_masks(grid)


def _has_broad_distractor(grid) -> bool:
    return any(
        mask != _SQUARE
        and mask not in _NONLEGACY_LS
        and mask != _SIZE4_CONTROL
        for mask in _component_masks(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "nonlegacy_mask": _has_nonlegacy_l,
    "bbox_2x2_nonsquare": _has_bbox_2x2_nonsquare,
    "size4_nonsquare": _has_size4_nonsquare,
    "broad_distractor": _has_broad_distractor,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "legacy_mask_memorizer": _legacy_mask_memorizer,
    "bbox_2x2": _bbox_2x2,
    "all_blue": _all_blue,
    "size4": _size4,
    "identity": _identity,
}
WITNESS_RIVALS = {
    "nonlegacy_mask": ["legacy_mask_memorizer"],
    "bbox_2x2_nonsquare": ["bbox_2x2"],
    "size4_nonsquare": ["size4"],
    "broad_distractor": ["all_blue"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a named plausible wrong rule survives."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if not all(competitor(pair["input"]) == pair["output"] for pair in demos):
            continue
        if competitor(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demo but changes the query answer")
        else:
            reasons.append(f"{name} survives every demo and the query")
    return reasons
