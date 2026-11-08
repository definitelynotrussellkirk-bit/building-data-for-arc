"""Curriculum generator for ARC task 00a3a71adae9.

Rule
====
Find the four-connected color-2 objects.  For each object, hypothetically grow
all of its cells by the 3x3 square neighbourhood.  Rank candidates by:

1. more overlap between that grown region and the color-1 mask;
2. then smaller Manhattan distance from the grown region to the mask;
3. then the object's top-left reading order.

Output the selected *original* object as a tight crop recolored 8.

The scheduled teaching profiles isolate all three comparator levels.  They are
not alternate rules: every profile is solved by the one canonical ranking above.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00a3a71adae9"
TASK_ID = "00a3a71adae9"
VERSION = "2.0.0"
RULE_HASH = "cdd6424b9ac7"

SUMMARY = (
    "Two to four separated color-2 motifs and a color-1 mask teach the full "
    "canonical selector precedence: square-growth overlap, then Manhattan "
    "distance, then top-left scan order.  The selected original motif is "
    "cropped and recolored 8."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are mask 1 and motifs 2",
    "there are exactly 2-4 four-connected color-2 motifs",
    "every ordinary lesson is a counterexample to one plausible shortened selector",
    "the output is the selected original motif, not its hypothetical growth",
]

SCHEDULE_PROFILES = (
    "overlap_priority",
    "distance_priority",
    "scan_tiebreak",
)
HELPFUL_TEXTURES = SCHEDULE_PROFILES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed draw 10..12",
        "valid": "10..12",
        "doc": "Exact grid height.  The domain contains every canonical height.",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed draw 12..14",
        "valid": "12..14",
        "doc": "Exact grid width.  The domain contains every canonical width.",
    },
    "n": {
        "type": "int",
        "default": "keyed draw 2..4",
        "valid": "2..4",
        "doc": "Exact number of color-2 motifs.",
    },
    "motif_size": {
        "type": "int",
        "default": "weighted keyed draw 1..10",
        "valid": "1..10",
        "doc": "Exact cell count (1-10) of the motif selected by the canonical rule.",
    },
    "mask_cells": {
        "type": "int",
        "default": "keyed draw 3..6",
        "valid": "3..6",
        "doc": "Exact total number of color-1 mask cells.",
    },
    "texture": {
        "type": "str",
        "default": "three-profile cyclic semantic schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
        "doc": (
            "overlap_priority makes overlap beat proximity; distance_priority "
            "makes proximity break an overlap tie; scan_tiebreak makes reading "
            "order break a score-and-distance tie."
        ),
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Enumerate every fixed connected polyomino of size 1-10 that fits a 3x4
# teaching slot.  Sorting the normalized tuples makes the bank deterministic
# across Python hash seeds while providing a much richer output alphabet than a
# small hand-picked 3x3 catalogue.
_SLOT_H = 3
_SLOT_W = 4


def _normalise(cells: Any) -> tuple[tuple[int, int], ...]:
    points = tuple((int(r), int(c)) for r, c in cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _enumerated_shapes() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    banks: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
        1: (((0, 0),),)
    }
    current = {((0, 0),)}
    for size in range(2, 11):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in current:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in _DIR4:
                    point = (r + dr, c + dc)
                    if point in occupied:
                        continue
                    candidate = _normalise(occupied | {point})
                    if (
                        max(rr for rr, _ in candidate) < _SLOT_H
                        and max(cc for _, cc in candidate) < _SLOT_W
                    ):
                        expanded.add(candidate)
        current = expanded
        banks[size] = tuple(sorted(expanded))
    return banks


_SHAPES = _enumerated_shapes()


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic comparator profile for an ordinary draw."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return SCHEDULE_PROFILES[(int(sample_index) + offsets[difficulty]) % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    integer_domains = {
        "grid_h": (10, 12),
        "grid_w": (12, 14),
        "n": (2, 4),
        "motif_size": (1, 10),
        "mask_cells": (3, 6),
    }
    for name, (lo, hi) in integer_domains.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    texture = overrides.get("texture")
    if texture is not None:
        if not isinstance(texture, str):
            raise TypeError("texture override must be a string")
        if texture not in SCHEDULE_PROFILES:
            raise ValueError(f"texture override {texture!r} not in {SCHEDULE_PROFILES}")


def _shape_for(size: int, rng) -> tuple[tuple[int, int], ...]:
    return rng.choice(_SHAPES[size])


def _bbox_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _place_in_slot(
    shape: tuple[tuple[int, int], ...],
    origin: tuple[int, int],
    *,
    vertical: str = "free",
    horizontal: str = "free",
    rng=None,
) -> tuple[tuple[int, int], ...]:
    sh, sw = _bbox_size(shape)
    if vertical == "top":
        roff = 0
    elif vertical == "bottom":
        roff = _SLOT_H - sh
    elif vertical == "free":
        roff = 0 if rng is None else rng.randint(0, _SLOT_H - sh)
    else:
        raise ValueError(f"unknown vertical alignment {vertical!r}")
    if horizontal == "left":
        coff = 0
    elif horizontal == "right":
        coff = _SLOT_W - sw
    elif horizontal == "free":
        coff = 0 if rng is None else rng.randint(0, _SLOT_W - sw)
    else:
        raise ValueError(f"unknown horizontal alignment {horizontal!r}")
    r0, c0 = origin
    return tuple(sorted((r0 + roff + r, c0 + coff + c) for r, c in shape))


def _grown_square(cells: tuple[tuple[int, int], ...], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    }


def _object_components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    motifs: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _DIR4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        motifs.append(tuple(sorted(cells)))
    return sorted(
        motifs,
        key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)),
    )


def _object_stats(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    mask = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    if not mask:
        raise ValueError("mask is empty")
    rows = []
    for index, cells in enumerate(_object_components(grid)):
        halo = _grown_square(cells, h, w)
        distance = min(
            abs(r - mr) + abs(c - mc)
            for r, c in halo
            for mr, mc in mask
        )
        rows.append({
            "index": index,
            "cells": cells,
            "grown": halo,
            "score": len(halo & mask),
            "distance": distance,
        })
    if not rows:
        raise ValueError("no color-2 objects")
    return rows


def _select(grid: list[list[int]], mode: str = "authority") -> dict[str, Any]:
    rows = _object_stats(grid)
    if mode == "authority":
        key: Callable[[dict[str, Any]], tuple[int, int, int]] = (
            lambda row: (-row["score"], row["distance"], row["index"])
        )
    elif mode == "distance_only":
        key = lambda row: (row["distance"], row["index"], 0)
    elif mode == "overlap_then_scan":
        key = lambda row: (-row["score"], row["index"], 0)
    elif mode == "reverse_scan_tie":
        key = lambda row: (-row["score"], row["distance"], -row["index"])
    else:
        raise ValueError(f"unknown selector mode {mode!r}")
    return min(rows, key=key)


def _crop(cells: tuple[tuple[int, int], ...]) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    occupied = set(cells)
    return [
        [8 if (r, c) in occupied else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _solve(grid: list[list[int]], mode: str = "authority") -> list[list[int]]:
    return _crop(_select(grid, mode)["cells"])


def _profile(grid: list[list[int]]) -> str:
    rows = _object_stats(grid)
    best_score = max(row["score"] for row in rows)
    score_tied = [row for row in rows if row["score"] == best_score]
    if len(score_tied) == 1:
        return "overlap_priority"
    best_distance = min(row["distance"] for row in score_tied)
    distance_tied = [row for row in score_tied if row["distance"] == best_distance]
    return "distance_priority" if len(distance_tied) == 1 else "scan_tiebreak"


def _different_sizes(target_size: int, count: int, rng) -> list[int]:
    choices = [size for size in range(1, 11) if size != target_size]
    rng.shuffle(choices)
    return choices[:count]


def _draw_objects(
    h: int,
    w: int,
    n: int,
    target_size: int,
    texture: str,
    ctx,
    difficulty: Any,
) -> tuple[list[tuple[tuple[int, int], ...]], int, int | None]:
    """Return (motifs, target_position, named_rival_position)."""
    sizes_rng = ctx.draw_rng(f"other_sizes:{texture}:{difficulty}")
    other_sizes = iter(_different_sizes(target_size, n - 1, sizes_rng))

    if texture == "overlap_priority":
        roles = ["distractor"]
        if n >= 3:
            roles.append("extra_top")
        if n >= 4:
            roles.append("extra_bottom")
        roles.append("target")
        slot_by_role = {
            "distractor": ((1, 1), "free", "free"),
            "extra_top": ((1, w - 5), "free", "free"),
            "extra_bottom": ((h - 4, 1), "free", "free"),
            "target": ((h - 4, w - 5), "free", "free"),
        }
        target_role = "target"
        rival_role = "distractor"
    elif texture == "distance_priority":
        roles = ["distractor", "target"]
        if n >= 3:
            roles.append("extra_bottom_left")
        if n >= 4:
            roles.append("extra_bottom_right")
        slot_by_role = {
            "distractor": ((0, 0), "top", "left"),
            "target": ((0, w - 4), "bottom", "left"),
            "extra_bottom_left": ((h - 3, 0), "top", "left"),
            "extra_bottom_right": ((h - 3, w - 4), "top", "left"),
        }
        target_role = "target"
        rival_role = "distractor"
    else:  # scan_tiebreak
        roles = []
        if n >= 3:
            roles.append("extra_top_left")
        roles.append("target")
        if n >= 4:
            roles.append("extra_bottom_left")
        roles.append("rival")
        slot_by_role = {
            "extra_top_left": ((0, 0), "top", "left"),
            "target": ((0, w - 4), "bottom", "left"),
            "extra_bottom_left": ((h - 3, 0), "top", "left"),
            "rival": ((h - 3, w - 4), "top", "left"),
        }
        target_role = "target"
        rival_role = "rival"

    motifs: list[tuple[tuple[int, int], ...]] = []
    target_index = -1
    rival_index: int | None = None
    for position, role in enumerate(roles):
        size = target_size if role == target_role else next(other_sizes)
        shape_rng = ctx.draw_rng(f"shape:{texture}:{difficulty}:{position}:{role}")
        shape = _shape_for(size, shape_rng)
        origin, vertical, horizontal = slot_by_role[role]
        cells = _place_in_slot(
            shape,
            origin,
            vertical=vertical,
            horizontal=horizontal,
            rng=shape_rng,
        )
        motifs.append(cells)
        if role == target_role:
            target_index = position
        if role == rival_role:
            rival_index = position
    if target_index < 0:
        raise RuntimeError("internal target placement failure")
    return motifs, target_index, rival_index


def _paint_masks(
    grid: list[list[int]],
    motifs: list[tuple[tuple[int, int], ...]],
    target_index: int,
    rival_index: int | None,
    mask_cells: int,
    texture: str,
    ctx,
    difficulty: Any,
) -> None:
    h, w = len(grid), len(grid[0])
    rng = ctx.draw_rng(f"mask_layout:{texture}:{difficulty}")
    occupied = {point for cells in motifs for point in cells}
    halos = [_grown_square(cells, h, w) for cells in motifs]

    if texture == "overlap_priority":
        if rival_index is None:
            raise RuntimeError("overlap profile lacks its distance-only rival")
        target_only = sorted(
            halos[target_index] - occupied - set().union(
                *(halo for i, halo in enumerate(halos) if i != target_index)
            )
        )
        rival_only = sorted(
            halos[rival_index] - occupied - set().union(
                *(halo for i, halo in enumerate(halos) if i != rival_index)
            )
        )
        need_target = mask_cells - 1
        if len(target_only) < need_target or not rival_only:
            raise RuntimeError("internal overlap witness has insufficient exclusive mask cells")
        selected = rng.sample(target_only, need_target) + rng.sample(rival_only, 1)
    elif texture == "distance_priority":
        # Anchor from an actual bottommost target cell, not merely its bbox's
        # left edge: irregular polyominoes need not occupy the bbox corner.
        target = motifs[target_index]
        bottom = max(r for r, _ in target)
        anchor_col = min(c for r, c in target if r == bottom)
        anchor = (bottom + 2, anchor_col)
        candidates = [
            (anchor[0], c)
            for c in range(w - 6, w)
            if (anchor[0], c) != anchor
        ]
        rng.shuffle(candidates)
        selected = [anchor] + candidates[: mask_cells - 1]
    else:  # scan_tiebreak
        # Derive each one-step-away anchor from a genuinely occupied extreme
        # cell.  This keeps arbitrary L/T/stair polyominoes tied exactly.
        if rival_index is None:
            raise RuntimeError("scan profile lacks its reverse-order rival")
        target = motifs[target_index]
        rival = motifs[rival_index]
        target_bottom = max(r for r, _ in target)
        rival_top = min(r for r, _ in rival)
        target_col = min(c for r, c in target if r == target_bottom)
        rival_col = min(c for r, c in rival if r == rival_top)
        anchors = [(target_bottom + 2, target_col), (rival_top - 2, rival_col)]
        candidates = [
            (row, col)
            for row in (anchors[0][0], anchors[1][0])
            for col in range(w - 4, w)
            if (row, col) not in anchors
        ]
        rng.shuffle(candidates)
        selected = anchors + candidates[: mask_cells - 2]

    if len(selected) != mask_cells or len(set(selected)) != mask_cells:
        raise RuntimeError("internal mask cardinality failure")
    for r, c in selected:
        if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
            raise RuntimeError(f"internal mask placement collision at {(r, c)}")
        grid[r][c] = 1


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_strict("grid_h", 10, 12)
    w = ctx.draw_int_strict("grid_w", 12, 14)
    n = ctx.draw_int_strict("n", 2, 4)
    target_size = ctx.draw_choice(
        "motif_size",
        (1, 2, 3, 4, 5, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10),
    )
    mask_count = ctx.draw_int_strict("mask_cells", 3, 6)
    if "texture" in overrides and overrides["texture"] is not None:
        texture = ctx.draw_choice("texture", SCHEDULE_PROFILES)
    else:
        texture = ctx.draw_choice(
            "texture",
            (schedule_profile(seed, sample_index, difficulty),),
        )

    grid = full_grid(h, w, 0)
    motifs, target_index, rival_index = _draw_objects(
        h, w, n, target_size, texture, ctx, difficulty
    )
    for cells in motifs:
        for r, c in cells:
            if grid[r][c] != 0:
                raise RuntimeError(f"internal motif collision at {(r, c)}")
            grid[r][c] = 2
    _paint_masks(
        grid, motifs, target_index, rival_index, mask_count, texture, ctx, difficulty
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"generated invalid grid: {errors}")
    chosen = _select(grid)
    expected = set(motifs[target_index])
    if set(chosen["cells"]) != expected or _profile(grid) != texture:
        raise RuntimeError(
            f"internal semantic witness failure: expected {texture} target {target_index}, "
            f"got {_profile(grid)} object {chosen['index']}"
        )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostic reasons when the canonical Racket rule could not apply."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), width
    errors: list[str] = []
    if not (1 <= h <= 30 and 1 <= w <= 30):
        errors.append(f"ARC dimensions must lie in 1..30, got {h}x{w}")
    invalid_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid_cells:
        errors.append(f"cells must be integer ARC colors; first invalid cell {invalid_cells[0]}")
        return errors
    colors = {value for row in grid for value in row}
    extra = sorted(colors - {0, 1, 2})
    if extra:
        errors.append(f"only colors 0, 1, and 2 are valid inputs; found {extra}")
    mask_count = sum(value == 1 for row in grid for value in row)
    if mask_count == 0:
        errors.append("at least one color-1 mask cell is required")
    motifs = _object_components([list(row) for row in grid])
    if not 2 <= len(motifs) <= 4:
        errors.append(f"expected 2-4 color-2 objects, found {len(motifs)}")
    bad_sizes = [len(cells) for cells in motifs if not 1 <= len(cells) <= 10]
    if bad_sizes:
        errors.append(f"color-2 object sizes must lie in 1..10, found {bad_sizes}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    reasons: list[str] = []
    if not 10 <= h <= 12:
        reasons.append(f"height {h} outside canonical teaching envelope 10..12")
    if not 12 <= w <= 14:
        reasons.append(f"width {w} outside canonical teaching envelope 12..14")
    masks = sum(value == 1 for row in grid for value in row)
    if not 3 <= masks <= 6:
        reasons.append(f"mask count {masks} outside canonical teaching envelope 3..6")
    if not reasons:
        try:
            profile = _profile([list(row) for row in grid])
            if profile not in SCHEDULE_PROFILES:
                reasons.append(f"unrecognized comparator profile {profile!r}")
        except (TypeError, ValueError) as exc:
            reasons.append(f"selector analysis failed: {exc}")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    normalized = [list(row) for row in grid]
    chosen = _select(normalized)
    return {
        "grid_h": len(normalized),
        "grid_w": len(normalized[0]),
        "n": len(_object_components(normalized)),
        "motif_size": len(chosen["cells"]),
        "mask_cells": sum(value == 1 for row in normalized for value in row),
        "texture": _profile(normalized),
    }


def _distance_only(grid):
    return _solve(grid, "distance_only")


def _overlap_then_scan(grid):
    return _solve(grid, "overlap_then_scan")


def _reverse_scan_tie(grid):
    return _solve(grid, "reverse_scan_tie")


SEMANTIC_RIVALS = {
    "distance_only": _distance_only,
    "overlap_then_scan": _overlap_then_scan,
    "reverse_scan_tie": _reverse_scan_tie,
}


def _witness(profile: str, rival: str, grid) -> bool:
    if self_check(grid):
        return False
    try:
        return _profile(grid) == profile and SEMANTIC_RIVALS[rival](grid) != _solve(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "overlap_priority": lambda grid: _witness("overlap_priority", "distance_only", grid),
    "distance_priority": lambda grid: _witness("distance_priority", "overlap_then_scan", grid),
    "scan_tiebreak": lambda grid: _witness("scan_tiebreak", "reverse_scan_tie", grid),
}
WITNESS_RIVALS = {
    "overlap_priority": ["distance_only"],
    "distance_priority": ["overlap_then_scan"],
    "scan_tiebreak": ["reverse_scan_tie"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "distance_only": _distance_only,
    "reverse_scan_tie": _reverse_scan_tie,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that fits every demo but changes the query."""
    reasons: list[str] = []
    for name, solve in LESSON_COMPETITORS.items():
        try:
            fits = all(solve(pair["input"]) == pair["output"] for pair in demos)
            changes_query = solve(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError):
            continue
        if fits and changes_query:
            reasons.append(f"competitor {name!r} fits every demonstration but changes the query")
    return reasons
