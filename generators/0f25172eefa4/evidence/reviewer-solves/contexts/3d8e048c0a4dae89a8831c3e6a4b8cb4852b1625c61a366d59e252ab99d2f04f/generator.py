"""Generator for ARC task 0f25172eefa4 — transform strip from key row.

The final row is an ordered transform program.  Crop the one colored body
above it, apply each code from left to right, and h-stack the transformed
crops with one blank column between pieces.  The executable/canonical mapping
is 2 or 5 -> identity, 3 -> rotate clockwise, and 4 -> rotate 180 degrees.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0f25172eefa4"
TASK_ID = "0f25172eefa4"
# 2.2.0 (2026-10-08): retain the alternating alias schedule, but move code 5
# behind a nonidentity code in every scheduled 5-family scene.  This falsifies
# the canonical-fitting shortcut "5 repeats the previous transform".  Every
# four default sample indices also include one 5x7 canonical-profile anchor in
# every difficulty band.  Distribution and semantic-contract change only — the
# Racket rule and RULE_HASH are untouched.
VERSION = "2.2.0"
RULE_HASH = "44e21d5003cc"

SUMMARY = (
    "Crop the single body above the last row; read the ordered key cells; "
    "map 2/5 to identity, 3 to clockwise rotation, and 4 to 180-degree "
    "rotation; then h-stack the results with one-column gaps."
)

INVARIANTS = [
    "literal color 0 is background",
    "the rows above the key row contain one single-color 4-connected body",
    "the cropped body distinguishes identity, clockwise, and 180-degree transforms",
    "the last row contains 3-4 ordered codes drawn only from 2, 3, 4, and 5",
    "generated draws contain all three executable transform classes",
    "code 5 is identity in the canonical examples and executable authority",
    "default key sequences alternate 2-family and 5-family by sample_index so"
    " every 3-demo window witnesses both identity aliases",
    "default 5-family draws use lr-asymmetric bodies so 5-as-flip is falsified",
    "scheduled code 5 follows code 3 or 4 so repeat-the-previous-transform is falsified",
    "every four consecutive default sample indices include a 5x7 canonical-profile anchor",
]

# Every generated sequence has four cells, includes identity/clockwise/180,
# and varies which semantic class is repeated.  Canonical inputs with three
# cells remain valid under self_check.
#
# SCHEDULE (2026-07-24, semantic-gate repair): the default key_sequence is no
# longer a free seed draw — it follows _SEQUENCE_SCHEDULE by sample_index so
# that every 3-consecutive-sample demo window contains BOTH identity aliases
# (a 2-family and a 5-family sequence).  Measured before the change: 19/200
# pinned lesson windows left the historical "5 means horizontal flip"
# competitor alive (no 5-demo, or the only 5-demo had the lr-symmetric t5
# body).  Explicit key_sequence overrides keep the full choice set.
_KEY_SEQUENCES = {
    "2-2-3-4": (2, 2, 3, 4),
    "2-3-3-4": (2, 3, 3, 4),
    "2-3-4-4": (2, 3, 4, 4),
    # Retained explicit override choices from 2.1.0.  They are lawful but are
    # no longer used by the default teaching schedule because code 5 appears
    # first and therefore cannot establish position-independent semantics.
    "5-5-3-4": (5, 5, 3, 4),
    "5-3-3-4": (5, 3, 3, 4),
    "5-3-4-4": (5, 3, 4, 4),
    # Default 5-family choices: code 5 follows a nonidentity transform, while
    # an adjacent duplicate still makes duplicate preservation observable.
    "3-3-5-4": (3, 3, 5, 4),
    "4-4-5-3": (4, 4, 5, 3),
    "3-5-4-4": (3, 5, 4, 4),
}

# Occupied-cell masks in their tight crop.  These include the three canonical
# body families (p5, l4, t5) plus related asymmetric variants.  All three
# executable transform classes produce distinct results for every profile.
_SHAPES = {
    "p5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "t5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "hook4": ((0, 0), (0, 1), (0, 2), (1, 0)),
    "stair5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "fork6": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    "skew6": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw, with a periodic 5-row canonical anchor",
        "valid": "5..8",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw, with a periodic 7-column canonical anchor",
        "valid": "7..10",
    },
    "body_color": {
        "type": "int",
        "default": "rng 1..9",
        "valid": "1..9",
    },
    "body_shape": {
        "type": "str",
        "default": "rng asymmetric canonical-like body",
        "valid": "p5|l4|t5|hook4|stair5|fork6|skew6",
    },
    "key_sequence": {
        "type": "str",
        "default": "rng four-code sequence covering all transform classes",
        "valid": "2-2-3-4|2-3-3-4|2-3-4-4|5-5-3-4|5-3-3-4|5-3-4-4|3-3-5-4|4-4-5-3|3-5-4-4",
    },
}

_VALID_CODES = frozenset((2, 3, 4, 5))

# Alternating identity-alias families: slots 0/2/4 contain code 2, slots
# 1/3/5 contain code 5, so ANY three consecutive samples witness both aliases
# alongside clockwise and 180-degree rotations.  In each scheduled 5-family
# sequence, code 5 follows code 3 or 4; this falsifies the canonical-fitting
# position shortcut "5 repeats the previous transform".
_SEQUENCE_SCHEDULE = (
    "2-2-3-4", "3-3-5-4", "2-3-3-4", "4-4-5-3", "2-3-4-4", "3-5-4-4",
)

_CANONICAL_ANCHOR_PERIOD = 4


def _tight_mask(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    pts = tuple(cells)
    if not pts:
        return tuple()
    min_r = min(r for r, _ in pts)
    min_c = min(c for _, c in pts)
    norm = {(r - min_r, c - min_c) for r, c in pts}
    h = max(r for r, _ in norm) + 1
    w = max(c for _, c in norm) + 1
    return tuple(
        tuple(1 if (r, c) in norm else 0 for c in range(w))
        for r in range(h)
    )


# Shapes whose tight mask equals its own left-right mirror cannot separate
# identity from horizontal flip.  Only t5 qualifies today; the set is derived,
# not hand-listed, so new shapes stay honest automatically.
def _flip_lr_mask(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in mask)


_LR_SYMMETRIC_SHAPES = frozenset(
    name
    for name, cells in _SHAPES.items()
    if _tight_mask(cells) == _flip_lr_mask(_tight_mask(cells))
)


def _rotate_cw(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    h = len(mask)
    w = len(mask[0])
    return tuple(tuple(mask[h - 1 - r][c] for r in range(h)) for c in range(w))


def _rotate_180(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in reversed(mask))


def _transform_class_count(mask: tuple[tuple[int, ...], ...]) -> int:
    return len({mask, _rotate_cw(mask), _rotate_180(mask)})


def _body_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid[:-1])
        for c, value in enumerate(row)
        if value != 0
    ]


def _component_count(cells: Iterable[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _shape_name(mask: tuple[tuple[int, ...], ...]) -> str:
    for name, cells in _SHAPES.items():
        if mask == _tight_mask(cells):
            return name
    return "custom"


def _key_sequence(grid: list[list[int]]) -> tuple[int, ...]:
    return tuple(value for value in grid[-1] if value != 0)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule remains oracle."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    # Scheduled default: any 3-consecutive-sample demo window covers both
    # identity aliases (2 AND 5).  Caller overrides win and keep full support.
    effective = dict(overrides)
    sample_index = int(sample_index)
    effective.setdefault(
        "key_sequence",
        _SEQUENCE_SCHEDULE[sample_index % len(_SEQUENCE_SCHEDULE)],
    )
    # Keep difficulty-aware scale on most samples, but guarantee an exact
    # canonical profile in every four-consecutive-index window.  Pairing the
    # dimensions avoids surprising a caller who explicitly controls either one.
    if (
        "grid_h" not in overrides
        and "grid_w" not in overrides
        and sample_index % _CANONICAL_ANCHOR_PERIOD == 0
    ):
        effective["grid_h"] = 5
        effective["grid_w"] = 7

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_diff("grid_h", 5, 8)
    w = ctx.draw_int_diff("grid_w", 7, 10)
    body_color = ctx.draw_int("body_color", 1, 9)
    sequence_name = ctx.draw_choice("key_sequence", tuple(_KEY_SEQUENCES))
    # A default-drawn 5-family scene must be able to falsify "5 = horizontal
    # flip", so its body pool excludes lr-symmetric shapes (t5).  t5 stays
    # available in 2-family defaults and under an explicit body_shape override.
    shape_pool = tuple(_SHAPES)
    if overrides.get("body_shape") is None and 5 in _KEY_SEQUENCES[sequence_name]:
        shape_pool = tuple(
            name for name in _SHAPES if name not in _LR_SYMMETRIC_SHAPES
        )
    shape_name = ctx.draw_choice("body_shape", shape_pool)

    shape = _SHAPES[shape_name]
    sequence = _KEY_SEQUENCES[sequence_name]
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    if shape_h > h - 2 or shape_w > w:
        raise ValueError(
            f"body_shape={shape_name!r} does not fit grid {h}x{w} "
            "with one blank separator row"
        )

    layout_rng = ctx.draw_rng("layout")
    top = layout_rng.randint(0, h - shape_h - 2)
    left = layout_rng.randint(0, w - shape_w)
    key_columns = sorted(layout_rng.sample(range(w), len(sequence)))

    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[top + dr][left + dc] = body_color
    for column, code in zip(key_columns, sequence):
        grid[-1][column] = code
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural teaching distribution, including canonicals."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]

    h = len(grid)
    errors: list[str] = []
    if not (5 <= h <= 8):
        errors.append(f"grid height must be 5..8, got {h}")
    if not (7 <= width <= 10):
        errors.append(f"grid width must be 7..10, got {width}")

    cells = _body_cells(grid)
    if not cells:
        errors.append("body rows contain no nonzero source object")
    else:
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            errors.append(f"body must use exactly one color, got {sorted(colors)}")
        components = _component_count(cells)
        if components != 1:
            errors.append(f"body must be one 4-connected component, got {components}")
        if len(cells) < 4:
            errors.append(f"body must contain at least four cells, got {len(cells)}")
        mask = _tight_mask(cells)
        if _transform_class_count(mask) != 3:
            errors.append(
                "body must distinguish identity, clockwise, and 180-degree transforms"
            )

    keys = _key_sequence(grid)
    if not (3 <= len(keys) <= 4):
        errors.append(f"expected 3..4 transform-code cells in last row, got {len(keys)}")
    invalid = [value for value in keys if value not in _VALID_CODES]
    if invalid:
        errors.append(f"invalid transform-code values in key row: {invalid}")
    if keys and len({"id" if value in (2, 5) else value for value in keys}) < 2:
        errors.append("key row must exercise at least two transform classes")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a returned generated grid."""
    cells = _body_cells(grid)
    body_colors = {grid[r][c] for r, c in cells}
    keys = _key_sequence(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "body_color": next(iter(body_colors)) if len(body_colors) == 1 else -1,
        "body_shape": _shape_name(_tight_mask(cells)),
        "key_sequence": "-".join(str(value) for value in keys),
    }


def semantic_observables(grid) -> dict[str, object]:
    """Task-linked observables used by focused tests and census evidence."""
    cells = _body_cells(grid)
    mask = _tight_mask(cells)
    keys = _key_sequence(grid)
    source_h = len(mask)
    source_w = len(mask[0]) if mask else 0
    widths = [source_w if code in (2, 4, 5) else source_h for code in keys]
    predicted_output_width = sum(widths) + max(0, len(widths) - 1)
    return {
        **observe_overrides(grid),
        "body_cells": len(cells),
        "source_h": source_h,
        "source_w": source_w,
        "key_count": len(keys),
        "has_identity": any(code in (2, 5) for code in keys),
        "has_clockwise": 3 in keys,
        "has_180": 4 in keys,
        "five_after_nonidentity": any(
            index > 0 and keys[index - 1] not in (2, 5)
            for index, code in enumerate(keys)
            if code == 5
        ),
        "canonical_profile_anchor": len(grid) == 5 and len(grid[0]) == 7,
        "transform_class_count": _transform_class_count(mask) if mask else 0,
        "predicted_output_width": predicted_output_width,
        "output_wider_than_input": predicted_output_width > len(grid[0]),
    }


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md)
# ---------------------------------------------------------------------------

def _crop_body(grid: list[list[int]]) -> list[list[int]]:
    """Tight colored crop of the body above the key row.  Pure."""
    cells = _body_cells(grid)
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _rot_cw_grid(piece: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*piece[::-1])]


def _rot_180_grid(piece: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in piece[::-1]]


def _flip_lr_grid(piece: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in piece]


def _pieces(grid: list[list[int]], *, five: str = "identity") -> list[list[list[int]]]:
    """Transformed crops for each key code, left to right, duplicates kept.

    `five` selects the semantics of code 5: "identity" (canonical, verified
    by execution) or "hflip" (the historical wrong prose, used only to build
    the competing rule).  Pure.
    """
    source = _crop_body(grid)
    pieces: list[list[list[int]]] = []
    for code in _key_sequence(grid):
        if code == 2:
            pieces.append(source)
        elif code == 5:
            pieces.append(source if five == "identity" else _flip_lr_grid(source))
        elif code == 3:
            pieces.append(_rot_cw_grid(source))
        elif code == 4:
            pieces.append(_rot_180_grid(source))
        else:
            raise ValueError(f"unsupported teaching key code {code}")
    return pieces


def _pieces_five_copies_previous(grid: list[list[int]]) -> list[list[list[int]]]:
    """Canonical-fitting rival: code 5 repeats the previous transform.

    A leading 5 defaults to identity.  All five canonical pairs fit this rule,
    because each 5 is leading or follows code 2.  Pure.
    """
    source = _crop_body(grid)
    pieces: list[list[list[int]]] = []
    previous = source
    for code in _key_sequence(grid):
        if code == 2:
            piece = source
        elif code == 3:
            piece = _rot_cw_grid(source)
        elif code == 4:
            piece = _rot_180_grid(source)
        elif code == 5:
            piece = previous if pieces else source
        else:
            raise ValueError(f"unsupported teaching key code {code}")
        pieces.append(piece)
        previous = piece
    return pieces


def _pieces_with_wrong_code(
    grid: list[list[int]], *, target_code: int, replacement: str
) -> list[list[list[int]]]:
    """Apply one deliberately wrong code mapping for a declared rival. Pure."""
    source = _crop_body(grid)
    pieces: list[list[list[int]]] = []
    for code in _key_sequence(grid):
        if code == target_code:
            if replacement == "identity":
                piece = source
            elif replacement == "clockwise":
                piece = _rot_cw_grid(source)
            else:
                raise ValueError(f"unsupported replacement transform {replacement!r}")
        elif code in (2, 5):
            piece = source
        elif code == 3:
            piece = _rot_cw_grid(source)
        elif code == 4:
            piece = _rot_180_grid(source)
        else:
            raise ValueError(f"unsupported teaching key code {code}")
        pieces.append(piece)
    return pieces


def _hstack_center(pieces: list[list[list[int]]], *, gap: int = 1) -> list[list[int]]:
    """Vertically centre (floor) and h-stack with `gap` blank columns.  Pure."""
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + gap * (len(pieces) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(piece[0]) + gap
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for hook logic; Racket stays authoritative."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _hstack_center(_pieces(grid))


def strict_canonical_like(grid) -> list[str]:
    """[] when `grid` is a lawful canonical-like scene for THIS task.

    Structural teaching grammar shared with self_check: one single-color
    4-connected >=4-cell body above the key row whose crop separates the
    identity / clockwise / 180 transform classes, and 3..4 ordered key codes
    drawn only from {2,3,4,5} spanning at least two transform classes.
    Canonical three-code inputs are lawful; codes 6..8 (oracle-only) are not
    part of the teaching grammar and are rejected.  Pure.
    """
    return list(self_check(grid))


def _lawful_observables(grid) -> dict[str, object] | None:
    if self_check(grid):
        return None
    return semantic_observables(grid)


def _witness_field(grid, extract) -> bool:
    obs = _lawful_observables(grid)
    return False if obs is None else bool(extract(obs))


def _has_adjacent_duplicate_piece(grid) -> bool:
    pieces = _pieces(grid)
    return any(pieces[i] == pieces[i - 1] for i in range(1, len(pieces)))


SEMANTIC_WITNESSES = {
    # both identity aliases and both rotations must be demonstrated
    "code_2_identity": lambda grid: _witness_field(
        grid, lambda o: "2" in str(o["key_sequence"]).split("-")
    ),
    "code_5_identity": lambda grid: _witness_field(
        grid, lambda o: "5" in str(o["key_sequence"]).split("-")
    ),
    "code_3_clockwise": lambda grid: _witness_field(grid, lambda o: o["has_clockwise"]),
    "code_4_180": lambda grid: _witness_field(grid, lambda o: o["has_180"]),
    # duplicates must appear so merge-duplicates is demonstrably wrong
    "adjacent_duplicate_piece": lambda grid: (
        not self_check(grid) and _has_adjacent_duplicate_piece(grid)
    ),
    # a 5-code on an lr-asymmetric body falsifies 5-as-horizontal-flip
    "five_on_flip_discriminating_body": lambda grid: _witness_field(
        grid,
        lambda o: "5" in str(o["key_sequence"]).split("-")
        and o["body_shape"] not in _LR_SYMMETRIC_SHAPES,
    ),
    "five_after_nonidentity": lambda grid: _witness_field(
        grid, lambda o: o["five_after_nonidentity"]
    ),
    "output_wider_than_input": lambda grid: _witness_field(
        grid, lambda o: o["output_wider_than_input"]
    ),
}


def _rival_code_2_is_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return _hstack_center(
        _pieces_with_wrong_code(grid, target_code=2, replacement="clockwise")
    )


def _rival_code_3_is_identity(grid: list[list[int]]) -> list[list[int]]:
    return _hstack_center(
        _pieces_with_wrong_code(grid, target_code=3, replacement="identity")
    )


def _rival_code_4_is_identity(grid: list[list[int]]) -> list[list[int]]:
    return _hstack_center(
        _pieces_with_wrong_code(grid, target_code=4, replacement="identity")
    )


def _rival_five_is_hflip(grid: list[list[int]]) -> list[list[int]]:
    return _hstack_center(_pieces(grid, five="hflip"))


def _rival_five_copies_previous_transform(grid: list[list[int]]) -> list[list[int]]:
    return _hstack_center(_pieces_five_copies_previous(grid))


def _rival_merge_adjacent_duplicates(grid: list[list[int]]) -> list[list[int]]:
    pieces = _pieces(grid)
    merged = [
        piece for index, piece in enumerate(pieces)
        if index == 0 or piece != pieces[index - 1]
    ]
    return _hstack_center(merged)


def _rival_no_separator_column(grid: list[list[int]]) -> list[list[int]]:
    return _hstack_center(_pieces(grid), gap=0)


SEMANTIC_RIVALS = {
    "code_2_is_clockwise": _rival_code_2_is_clockwise,
    "code_3_is_identity": _rival_code_3_is_identity,
    "code_4_is_identity": _rival_code_4_is_identity,
    "five_is_hflip": _rival_five_is_hflip,
    "five_copies_previous_transform": _rival_five_copies_previous_transform,
    "merge_adjacent_duplicates": _rival_merge_adjacent_duplicates,
    "no_separator_column": _rival_no_separator_column,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "five_copies_previous_transform": _rival_five_copies_previous_transform,
}
WITNESS_RIVALS = {
    "code_2_identity": ["code_2_is_clockwise"],
    "code_3_clockwise": ["code_3_is_identity"],
    "code_4_180": ["code_4_is_identity"],
    "code_5_identity": ["five_is_hflip", "five_copies_previous_transform"],
    "five_on_flip_discriminating_body": ["five_is_hflip"],
    "five_after_nonidentity": ["five_copies_previous_transform"],
    "adjacent_duplicate_piece": ["merge_adjacent_duplicates"],
    "output_wider_than_input": ["no_separator_column"],
}


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    """Outputs of every declared plausible rival on a lawful scene, else None."""
    if self_check(grid):
        return None
    return {name: rival(grid) for name, rival in LESSON_COMPETITORS.items()}


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos force the canonical code semantics on the query.

    A competitor that reproduces EVERY demo output yet answers the query
    differently means the lesson underdetermines the rule.  The default
    schedule alternates identity aliases, places code 5 after a nonidentity
    transform, preserves adjacent duplicates, and uses visible separator
    columns so each declared rival is refuted in every production lesson. Pure.
    """
    reasons: list[str] = []
    query_competitors = _competitor_outputs(query.get("input"))
    if query_competitors is None:
        return ["query input is not a lawful scene for this task"]
    query_truth = rule_mirror(query.get("input"))

    demo_rows: list[tuple[dict, dict[str, list[list[int]]]]] = []
    for index, demo in enumerate(demos):
        competitors = _competitor_outputs(demo.get("input"))
        if competitors is None:
            reasons.append(f"demo {index} input is not a lawful scene for this task")
            continue
        if demo.get("output") != rule_mirror(demo.get("input")):
            reasons.append(
                f"demo {index} output disagrees with the transform-strip rule mirror"
            )
            continue
        demo_rows.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        survives = all(
            competitors[name] == demo["output"] for demo, competitors in demo_rows
        )
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo yet answers the "
                "query differently"
            )
    return sorted(set(reasons))
