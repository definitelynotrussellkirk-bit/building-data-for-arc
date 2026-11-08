"""Task-specific generator for ARC task 007bbfb7 (self-tiling).

Authority: ``(rule! (lambda (g) (self-tile g)))``.

For a 3x3 input ``g``, the output is a 3x3 grid of 3x3 blocks.  Block
``(br, bc)`` is an exact copy of ``g`` when ``g[br][bc]`` is foreground and is
all background when that mask cell is zero.  The input bitmap is therefore
both the block mask and the copied template; every occupied offset matters.

The official six inputs are all 3x3, use background 0 plus one foreground
colour, and contain three through seven foreground cells.  Default generation
keeps half of each difficulty band on the exact official bitmap orbits (under
D4 symmetries, which preserve self-tiling) and uses the other half for lawful
non-canonical masks.  This anchors training to the demonstrated manifold while
still refuting memorisation of the six public bitmaps.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a9f315ca9cc7"
VERSION = "2.1.0"
TASK_ID = "a9f315ca9cc7"
RULE_HASH = "813a5290113c"

SUMMARY = (
    "A 3x3 binary-colour mask is self-tiled into a 9x9 output: each foreground "
    "mask cell selects an exact copy of the input, while each background mask "
    "cell selects a blank 3x3 block."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "input is exactly 3x3, matching every canonical train/test input",
    "palette is background 0 plus exactly one foreground colour in 1..9",
    "foreground count is 3..7, so both copied and blank output blocks occur",
    "foreground spans all rows or all columns and has at least two row and column patterns",
    "default draws include canonical D4-orbit masks in every difficulty band",
]

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng canonical|generalized",
        "valid": "canonical|generalized",
    },
    "fg_color": {
        "type": "color",
        "default": "rng",
        "valid": "1..9",
    },
}

SCHEDULE_PROFILES = ("canonical", "generalized")

# Canonical train inputs followed by the canonical test input, colour-normalized.
_CANONICAL_MASKS = (
    ((1, 1, 0), (1, 0, 0), (0, 1, 1)),
    ((1, 0, 1), (0, 0, 0), (0, 1, 0)),
    ((0, 0, 0), (0, 0, 1), (1, 0, 1)),
    ((1, 1, 1), (0, 0, 0), (0, 1, 1)),
    ((0, 1, 1), (1, 1, 1), (0, 1, 1)),
    ((1, 0, 1), (1, 0, 1), (1, 1, 0)),
)


def _rot90(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(mask[len(mask) - 1 - r][c] for r in range(len(mask)))
                 for c in range(len(mask[0])))


def _flip(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in mask)


def _d4(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    variants = []
    current = mask
    for _ in range(4):
        variants.append(current)
        variants.append(_flip(current))
        current = _rot90(current)
    return tuple(dict.fromkeys(variants))


_CANONICAL_ORBIT = frozenset(variant for mask in _CANONICAL_MASKS for variant in _d4(mask))


def _mask_from_code(code: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple((code >> (8 - (r * 3 + c))) & 1 for c in range(3))
        for r in range(3)
    )


def _mask_code(mask: tuple[tuple[int, ...], ...]) -> int:
    code = 0
    for row in mask:
        for value in row:
            code = (code << 1) | int(bool(value))
    return code


def _mask_grammar_errors(mask: tuple[tuple[int, ...], ...]) -> list[str]:
    errors: list[str] = []
    count = sum(sum(row) for row in mask)
    if not 3 <= count <= 7:
        errors.append(f"foreground count must be 3..7, got {count}")
    for role, wanted in (("foreground", 1), ("background", 0)):
        cells = [(r, c) for r in range(3) for c in range(3) if mask[r][c] == wanted]
        if cells:
            bbox_h = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
            bbox_w = max(c for _, c in cells) - min(c for _, c in cells) + 1
            if bbox_h != 3 and bbox_w != 3:
                errors.append(
                    f"{role} must span all rows or columns, bbox={bbox_h}x{bbox_w}"
                )
    row_patterns = len(set(mask))
    col_patterns = len({tuple(mask[r][c] for r in range(3)) for c in range(3)})
    if row_patterns < 2:
        errors.append("foreground mask needs at least two distinct row patterns")
    if col_patterns < 2:
        errors.append("foreground mask needs at least two distinct column patterns")
    return errors


_LAWFUL_CODES_BY_COUNT: dict[int, tuple[int, ...]] = {}
for _count in range(3, 8):
    _LAWFUL_CODES_BY_COUNT[_count] = tuple(
        code
        for code in range(1, 511)
        if sum(sum(row) for row in _mask_from_code(code)) == _count
        and not _mask_grammar_errors(_mask_from_code(code))
        and _mask_from_code(code) not in _CANONICAL_ORBIT
    )


def _generalized_counts(difficulty: str | None) -> tuple[int, ...]:
    if difficulty == "easy":
        return (3, 4)
    if difficulty == "medium":
        return (4, 5, 6)
    if difficulty == "hard":
        return (6, 7)
    return (3, 4, 5, 6, 7)


def _colourize(mask: tuple[tuple[int, ...], ...], fg: int) -> list[list[int]]:
    return [[fg if value else 0 for value in row] for row in mask]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    # Alternate the default semantic profile by sample index.  Every sliding
    # window of EXAMPLES_NEEDED=3 consecutive demonstrations therefore contains
    # both a public-orbit anchor and a non-public mask, so public-mask
    # memorisation cannot survive a generated lesson.  An explicit caller
    # override still takes precedence.
    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "scene_profile", SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    fg = ctx.draw_color("fg_color", exclude={0})

    if profile == "canonical":
        base = ctx.draw_choice("canonical_mask", _CANONICAL_MASKS)
        mask = ctx.draw_choice("canonical_transform", _d4(base))
    else:
        counts = _generalized_counts(difficulty)
        count = ctx.draw_choice("generalized_fg_count", counts)
        code = ctx.draw_choice("generalized_mask_code", _LAWFUL_CODES_BY_COUNT[count])
        mask = _mask_from_code(code)

    grid = _colourize(mask, fg)
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid self-tile input: " + "; ".join(errors))
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or len(grid) != 3:
        return {"errors": ["input must be a 3-row list"]}
    if any(not isinstance(row, list) or len(row) != 3 for row in grid):
        return {"errors": ["input must be rectangular 3x3"]}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colours 0..9")
        return {"errors": errors}

    nonzero = sorted({value for row in grid for value in row if value != 0})
    if len(nonzero) != 1:
        errors.append(f"expected exactly one foreground colour, got {nonzero}")
        return {"errors": errors}
    fg = nonzero[0]
    mask = tuple(tuple(1 if value == fg else 0 for value in row) for row in grid)
    errors.extend(_mask_grammar_errors(mask))
    return {
        "errors": errors,
        "fg_color": fg,
        "mask": mask,
        "mask_code": _mask_code(mask),
        "fg_count": sum(sum(row) for row in mask),
        "scene_profile": "canonical" if mask in _CANONICAL_ORBIT else "generalized",
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "scene_profile": facts["scene_profile"],
        "fg_color": facts["fg_color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete active input grammar and requested exact axes."""
    del difficulty
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {name: candidate[name] for name in AXES if name in candidate}
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if observed[name] != value:
                errors.append(f"override {name}={value!r} realized as {observed[name]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact canonical bitmap orbit, with foreground colour treated as nuisance."""
    facts = _analyze(grid)
    if facts["errors"]:
        return list(facts["errors"])
    if facts["mask"] not in _CANONICAL_ORBIT:
        return [f"mask code {facts['mask_code']} is outside the six canonical D4 orbits"]
    return []


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for tests; Racket remains authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid self-tile input: " + "; ".join(facts["errors"]))
    h = w = 3
    output = full_grid(h * h, w * w, 0)
    for block_r in range(h):
        for block_c in range(w):
            if grid[block_r][block_c] == 0:
                continue
            for r in range(h):
                for c in range(w):
                    output[block_r * h + r][block_c * w + c] = grid[r][c]
    return output


def _rival_pixel_scale(grid) -> list[list[int]]:
    output = full_grid(9, 9, 0)
    for r in range(3):
        for c in range(3):
            for rr in range(3):
                for cc in range(3):
                    output[r * 3 + rr][c * 3 + cc] = grid[r][c]
    return output


def _rival_repeat_every_block(grid) -> list[list[int]]:
    return [[grid[r % 3][c % 3] for c in range(9)] for r in range(9)]


def _rival_single_copy_top_left(grid) -> list[list[int]]:
    output = full_grid(9, 9, 0)
    for r in range(3):
        for c in range(3):
            output[r][c] = grid[r][c]
    return output


def _rival_invert_mask(grid) -> list[list[int]]:
    output = full_grid(9, 9, 0)
    for block_r in range(3):
        for block_c in range(3):
            if grid[block_r][block_c] != 0:
                continue
            for r in range(3):
                for c in range(3):
                    output[block_r * 3 + r][block_c * 3 + c] = grid[r][c]
    return output


def _rival_memorize_public_masks(grid) -> list[list[int]]:
    """Fit every public bitmap orbit, but use the upscale shortcut elsewhere."""
    facts = _analyze(grid)
    if not facts["errors"] and facts["mask"] in _CANONICAL_ORBIT:
        return rule_mirror(grid)
    return _rival_pixel_scale(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "pixel_scale_3": _rival_pixel_scale,
    "repeat_template_everywhere": _rival_repeat_every_block,
    "single_copy_top_left": _rival_single_copy_top_left,
    "copy_on_background_cells": _rival_invert_mask,
    "memorize_public_masks_else_pixel_scale": _rival_memorize_public_masks,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _lawful(grid) -> bool:
    return not self_check(grid)


SEMANTIC_WITNESSES = {
    "active_blocks_copy_mixed_template": _lawful,
    "background_blocks_are_blank": _lawful,
    "more_than_one_active_block": lambda grid: _lawful(grid) and _analyze(grid)["fg_count"] >= 3,
    "foreground_and_background_masks_both_present": _lawful,
    "generalized_bitmap_refutes_public_mask_memorization": (
        lambda grid: _lawful(grid) and bool(strict_canonical_like(grid))
    ),
}

WITNESS_RIVALS = {
    "active_blocks_copy_mixed_template": ["pixel_scale_3"],
    "background_blocks_are_blank": ["repeat_template_everywhere"],
    "more_than_one_active_block": ["single_copy_top_left"],
    "foreground_and_background_masks_both_present": ["copy_on_background_cells"],
    "generalized_bitmap_refutes_public_mask_memorization": [
        "memorize_public_masks_else_pixel_scale"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible wrong rule survives all demos."""
    if not demos:
        return ["lesson has no demonstrations"]
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return observe_overrides(generate(seed, sample_index, difficulty=difficulty))["scene_profile"]
