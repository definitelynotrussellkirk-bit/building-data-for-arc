"""Generator for ARC task 8881f54cf3c8 — keyed shape Boolean algebra.

The selected executable authority has one important, demonstrated wrinkle:
``(0, 0)`` is the operation key, A is every color-2 cell except the key, but B
is *every* color-3 cell.  Therefore an op-3 key is itself part of B.  The third
canonical training pair proves this by producing a large XOR canvas that keeps
the remote color-3 motif at its original offset from the key.  This generator
teaches that selected behavior explicitly instead of the tempting "clean XOR"
shortcut that discards the key from both motifs.

A and the non-key color-3 motif are otherwise generated as separated input
objects whose independently normalized shapes partially overlap.  The partial
overlap makes union, intersection, XOR, and A-minus-B all visibly nontrivial.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8881f54cf3c8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d4cbbd7307ee"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read (0,0) as op key. Normalize color-2 cells (excluding the key) as A "
    "and every color-3 cell as B; thus an op-3 key participates in B. Apply "
    "1=union, 2=intersection, 3=xor, 4=A-minus-B, then paint the result color 4."
)

INVARIANTS = [
    "background is 0 and (0,0) is an operation key in 1..4",
    "there are at least three non-key color-2 cells and three non-key color-3 cells",
    "no colors occur except 0, 2, 3, and the key color",
    "ordinary draws use two separated motifs whose clean normalized forms partially overlap",
    "every four-example ordinary window contains operations 1, 2, 3, and 4",
    "when op=3 the selected authority deliberately treats the key itself as a B cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical 8..9", "valid": "8..9"},
    "grid_w": {"type": "int", "default": "scheduled canonical 13..14", "valid": "13..14"},
    "op": {"type": "int", "default": "four-example schedule", "valid": "1..4"},
    "a_size": {"type": "int", "default": "scheduled 4..6", "valid": "4..6"},
    "b_size": {"type": "int", "default": "scheduled 4..6", "valid": "4..6"},
    "overlap_cells": {"type": "int", "default": "scheduled 1..2", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Negative mutation fixtures only; they are deliberately outside AXES and must
# be rejected by self_check rather than admitted to the ordinary curriculum.
DEGENERATE_TEXTURES = ("no_op", "missing_color", "identical_sets")
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORHOOD = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Every four consecutive ordinary samples cover all operation branches."""
    del seed, difficulty
    return 1 + (int(sample_index) % 4)


SCHEDULE_PROFILES = (1, 2, 3, 4)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name, value in overrides.items():
        if value is None or name == "texture":
            continue
        if name == "grid_h" and (type(value) is not int or not 8 <= value <= 9):
            raise ValueError("grid_h must be an integer in 8..9")
        if name == "grid_w" and (type(value) is not int or not 13 <= value <= 14):
            raise ValueError("grid_w must be an integer in 13..14")
        if name == "op" and (type(value) is not int or not 1 <= value <= 4):
            raise ValueError("op must be an integer in 1..4")
        if name in {"a_size", "b_size"} and (
            type(value) is not int or not 4 <= value <= 6
        ):
            raise ValueError(f"{name} must be an integer in 4..6")
        if name == "overlap_cells" and (
            type(value) is not int or not 1 <= value <= 2
        ):
            raise ValueError("overlap_cells must be an integer in 1..2")


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    r0 = min(row for row, _ in points)
    c0 = min(col for _, col in points)
    return tuple(sorted((row - r0, col - c0) for row, col in points))


def _bbox_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    if not points:
        return 1, 1
    return max(row for row, _ in points) + 1, max(col for _, col in points) + 1


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _random_motif(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Grow a compact connected motif in a 4x4 local frame containing (0,0)."""
    cells = {(0, 0)}
    for _ in range(2000):
        if len(cells) >= size:
            return tuple(sorted(cells))
        row, col = rng.choice(tuple(sorted(cells)))
        dr, dc = rng.choice(_CARDINAL)
        nr, nc = row + dr, col + dc
        if 0 <= nr < 4 and 0 <= nc < 4:
            cells.add((nr, nc))
    raise ValueError("could not grow compact motif")


def _motif_pair(rng, a_size: int, b_size: int, overlap_cells: int):
    """Find two connected normalized motifs with an exact partial overlap."""
    for _ in range(8000):
        a = set(_random_motif(rng, a_size))
        b = set(_random_motif(rng, b_size))
        if len(a & b) != overlap_cells:
            continue
        if not (a - b) or not (b - a):
            continue
        if not _connected(a) or not _connected(b):
            continue
        if min(_shape_dims(a)) < 2 or min(_shape_dims(b)) < 2:
            continue
        return tuple(sorted(a)), tuple(sorted(b))
    raise ValueError(
        f"could not realize motif relation a={a_size} b={b_size} overlap={overlap_cells}"
    )


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(shape)
    return max(row for row, _ in points) + 1, max(col for _, col in points) + 1


def _translate(shape: Iterable[tuple[int, int]], top: int, left: int):
    return tuple((top + row, left + col) for row, col in shape)


def _well_separated(first, second) -> bool:
    first_set = set(first)
    second_set = set(second)
    if first_set & second_set:
        return False
    return not any(
        (row + dr, col + dc) in second_set
        for row, col in first_set
        for dr, dc in _NEIGHBORHOOD
    )


def _place_pair(rng, h: int, w: int, a_shape, b_shape, *, op: int):
    ah, aw = _shape_dims(a_shape)
    bh, bw = _shape_dims(b_shape)
    candidates_a = [
        (top, left)
        for top in range(2, h - ah + 1)
        for left in range(0, w - aw + 1)
    ]
    candidates_b = [
        (top, left)
        for top in range(2, h - bh + 1)
        for left in range(0, w - bw + 1)
    ]
    rng.shuffle(candidates_a)
    rng.shuffle(candidates_b)
    for atop, aleft in candidates_a:
        a_cells = _translate(a_shape, atop, aleft)
        for btop, bleft in candidates_b:
            # For op=3, keep the remote B motif visibly separated from the key
            # and from the small normalized A neighborhood.  This guarantees a
            # decisive counterexample to the tempting clean-XOR shortcut.
            if op == 3 and btop <= 3 and bleft <= 4:
                continue
            b_cells = _translate(b_shape, btop, bleft)
            if _well_separated(a_cells, b_cells):
                return a_cells, b_cells
    raise ValueError("could not place separated motif pair")


def _clean_shape_cells(grid, color: int) -> tuple[tuple[int, int], ...]:
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color and (row, col) != (0, 0)
    ]
    return tuple(points)


def _authority_sets(grid, *, include_op3_key: bool = True):
    a = _normalize(_clean_shape_cells(grid, 2))
    b_raw = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
        and (include_op3_key or (row, col) != (0, 0))
    ]
    b = _normalize(b_raw)
    return set(a), set(b)


def _apply_boolean(
    grid,
    *,
    forced_op: int | None = None,
    include_op3_key: bool = True,
) -> list[list[int]]:
    op = int(grid[0][0] if forced_op is None else forced_op)
    a, b = _authority_sets(grid, include_op3_key=include_op3_key)
    h1, w1 = _bbox_dims(a)
    h2, w2 = _bbox_dims(b)
    height, width = max(h1, h2), max(w1, w2)
    if op == 1:
        result = a | b
    elif op == 2:
        result = a & b
    elif op == 3:
        result = a ^ b
    else:
        result = a - b
    out = full_grid(height, width, 0)
    for row, col in result:
        out[row][col] = 4
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror of the selected Racket authority, including op-3 key leakage."""
    return _apply_boolean(grid)


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 13, 0)
    if name == "no_op":
        for row, col in ((2, 1), (2, 2), (3, 1), (3, 2)):
            grid[row][col] = 2
        for row, col in ((2, 8), (2, 9), (3, 8), (3, 9)):
            grid[row][col] = 3
    elif name == "missing_color":
        grid[0][0] = 1
        for row, col in ((2, 1), (2, 2), (3, 1), (3, 2)):
            grid[row][col] = 2
    elif name == "identical_sets":
        grid[0][0] = 1
        for row, col in ((2, 1), (2, 2), (3, 1), (3, 2)):
            grid[row][col] = 2
        for row, col in ((5, 8), (5, 9), (6, 8), (6, 9)):
            grid[row][col] = 3
    else:
        raise ValueError(f"unknown texture fixture: {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture fixture: {texture!r}")
        conflicting = sorted(set(overrides) & set(AXES))
        if conflicting:
            raise ValueError(
                "texture fixture is incompatible with exact axes: " + ", ".join(conflicting)
            )
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    difficulty_phase = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    dim_slot = (int(seed) + int(sample_index) + difficulty_phase) % 2
    h = _draw_scheduled_int(ctx, "grid_h", 8, 9, 8 + dim_slot)
    w = _draw_scheduled_int(ctx, "grid_w", 13, 14, 13 + dim_slot)
    op = _draw_scheduled_int(ctx, "op", 1, 4, profile)
    # Independent keyed draws keep the two motif-size axes semantically
    # distinct; difficulty varies the dimension/overlap schedule instead.
    a_size = ctx.draw_int("a_size", 4, 6)
    b_size = ctx.draw_int("b_size", 4, 6)
    overlap = _draw_scheduled_int(
        ctx, "overlap_cells", 1, 2, 1 + ((int(seed) + sample_index + difficulty_phase) % 2)
    )

    motif_rng = ctx.draw_rng("motifs")
    a_shape, b_shape = _motif_pair(motif_rng, a_size, b_size, overlap)
    placement_rng = ctx.draw_rng("placement")
    a_cells, b_cells = _place_pair(placement_rng, h, w, a_shape, b_shape, op=op)

    grid = full_grid(h, w, 0)
    grid[0][0] = op
    for row, col in a_cells:
        grid[row][col] = 2
    for row, col in b_cells:
        grid[row][col] = 3

    # Fail closed if an implementation change accidentally makes a scheduled
    # ordinary draw rule-hiding.  This is a generation obligation, not a
    # self_check restriction on external canonical inputs.
    facts = semantic_observables(grid)
    if facts["clean_overlap_cells"] < 1 or not facts["a_only_cells"] or not facts["b_only_cells"]:
        raise ValueError("generated motifs do not expose partial Boolean overlap")
    if not any(value == 4 for row in rule_mirror(grid) for value in row):
        raise ValueError("generated operation produced an empty teaching output")
    if op == 3 and rule_mirror(grid) == _clean_boolean(grid):
        raise ValueError("op-3 draw failed to expose key participation in B")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def semantic_observables(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    op = grid[0][0]
    a_raw = _clean_shape_cells(grid, 2)
    b_raw = _clean_shape_cells(grid, 3)
    a = set(_normalize(a_raw)) if a_raw else set()
    b_clean = set(_normalize(b_raw)) if b_raw else set()
    overlap = a & b_clean
    allowed = {0, 2, 3, op}
    unexpected = sorted({value for row in grid for value in row if value not in allowed})
    a_bbox = _bbox_dims(a) if a else (0, 0)
    b_bbox = _bbox_dims(b_clean) if b_clean else (0, 0)
    return {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "op": op,
        "a_size": len(a_raw),
        "b_size": len(b_raw),
        "a_normalized": tuple(sorted(a)),
        "b_clean_normalized": tuple(sorted(b_clean)),
        "clean_overlap_cells": len(overlap),
        "a_only_cells": len(a - b_clean),
        "b_only_cells": len(b_clean - a),
        "a_bbox": a_bbox,
        "b_bbox": b_bbox,
        "unexpected_colors": unexpected,
        "op3_key_participates": op == 3,
        "clean_xor_differs": op == 3 and rule_mirror(grid) != _clean_boolean(grid),
    }


def observe_overrides(grid) -> dict[str, int]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError(str(facts["errors"][0]))
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "op": int(facts["op"]),
        "a_size": int(facts["a_size"]),
        "b_size": int(facts["b_size"]),
        "overlap_cells": int(facts["clean_overlap_cells"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible input grammar, including canonical pairs."""
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    op = grid[0][0]
    if op not in (1, 2, 3, 4):
        errors.append(f"operation key at (0,0) must be 1..4, found {op}")
        return errors
    facts = semantic_observables(grid)
    if facts["unexpected_colors"]:
        errors.append(f"unexpected input colors: {facts['unexpected_colors']}")
    if facts["a_size"] < 3:
        errors.append(f"expected at least 3 non-key color-2 cells, found {facts['a_size']}")
    if facts["b_size"] < 3:
        errors.append(f"expected at least 3 non-key color-3 cells, found {facts['b_size']}")
    if op in (1, 4):
        same_as_key = sum(value == op for row in grid for value in row)
        if same_as_key != 1:
            errors.append(f"key color {op} must occur only at (0,0)")
    # The demonstrated scene layout isolates the key from both shape bodies.
    if any(grid[row][col] != 0 for row in range(min(2, h)) for col in range(w) if (row, col) != (0, 0)):
        errors.append("the key must be isolated by an empty top band")
    if facts["a_bbox"][0] < 2 or facts["a_bbox"][1] < 2:
        errors.append("color-2 motif must span at least a 2x2 bounding box")
    if facts["b_bbox"][0] < 2 or facts["b_bbox"][1] < 2:
        errors.append("color-3 motif must span at least a 2x2 bounding box")
    if facts["a_normalized"] == facts["b_clean_normalized"]:
        errors.append("the two normalized motifs must not be identical")

    if isinstance(meta, dict) and not errors:
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and requested[axis] is not None and requested[axis] != observed[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked grammar covering all canonical inputs and ordinary draws."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if not 8 <= facts["grid_h"] <= 9:
        reasons.append(f"canonical height is 8..9, got {facts['grid_h']}")
    if not 13 <= facts["grid_w"] <= 14:
        reasons.append(f"canonical width is 13..14, got {facts['grid_w']}")
    if not 3 <= facts["a_size"] <= 6:
        reasons.append(f"canonical color-2 motif size is 3..6, got {facts['a_size']}")
    if not 3 <= facts["b_size"] <= 6:
        reasons.append(f"canonical color-3 motif size is 3..6, got {facts['b_size']}")
    return reasons


def _clean_boolean(grid) -> list[list[int]]:
    """Tempting rival: discard the op marker from both motifs before Boolean algebra."""
    return _apply_boolean(grid, include_op3_key=False)


def _always_union(grid) -> list[list[int]]:
    return _apply_boolean(grid, forced_op=1)


def _always_intersection(grid) -> list[list[int]]:
    return _apply_boolean(grid, forced_op=2)


def _always_difference(grid) -> list[list[int]]:
    return _apply_boolean(grid, forced_op=4)


def _marker_as_answer(grid) -> list[list[int]]:
    return [[4 if grid[0][0] else 0]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "clean_boolean_excludes_key": _clean_boolean,
    "always_union": _always_union,
    "always_intersection": _always_intersection,
    "always_a_minus_b": _always_difference,
    "marker_as_answer": _marker_as_answer,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # The written solution naturally suggests this rival, but canonical op-3
    # output falsifies it. Keep it explicit so future edits cannot erase that
    # contradiction without a gate becoming loud.
    "clean_boolean_excludes_key": _clean_boolean,
}


def _op_is(value: int):
    return lambda grid: bool(semantic_observables(grid).get("op") == value)


def _partial_overlap(grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and facts["clean_overlap_cells"] >= 1
        and facts["a_only_cells"] >= 1
        and facts["b_only_cells"] >= 1
    )


def _op3_marker_visible(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and bool(facts["clean_xor_differs"])


SEMANTIC_WITNESSES = {
    "union_branch": _op_is(1),
    "intersection_branch": _op_is(2),
    "op3_key_contaminated_xor_branch": _op3_marker_visible,
    "a_minus_b_branch": _op_is(4),
    "partial_overlap_exposes_set_logic": _partial_overlap,
}
BRANCH_WITNESSES = {"union_branch", "intersection_branch", "a_minus_b_branch"}
WITNESS_RIVALS = {
    "union_branch": ["always_intersection", "always_a_minus_b", "marker_as_answer"],
    "intersection_branch": ["always_union", "always_a_minus_b", "marker_as_answer"],
    "op3_key_contaminated_xor_branch": ["clean_boolean_excludes_key", "always_union", "marker_as_answer"],
    "a_minus_b_branch": ["always_union", "always_intersection", "marker_as_answer"],
    "partial_overlap_exposes_set_logic": ["marker_as_answer"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    validated = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        malformed = self_check(pair["input"])
        if malformed:
            reasons.append(f"demo {index} malformed: {malformed[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with selected Boolean authority")
            continue
        validated.append(pair)

    malformed_query = self_check(query["input"])
    if malformed_query:
        reasons.append(f"query malformed: {malformed_query[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with selected Boolean authority")

    if reasons or len(validated) != len(demos):
        return reasons
    operations = {int(pair["input"][0][0]) for pair in validated}
    missing = sorted(set(SCHEDULE_PROFILES) - operations)
    if missing:
        reasons.append(f"demonstrations do not cover operation key(s): {missing}")
    if not any(_op3_marker_visible(pair["input"]) for pair in validated):
        reasons.append("no demonstration exposes the op-3 key-as-B behavior")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in validated):
            reasons.append(f"named rival survives all demonstrations: {name}")
    return reasons
