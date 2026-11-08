"""Generator for ARC task 1a259ef9a7e7.

The canonical input grammar is a 3x2 binary-colored grid: background 0 plus
one foreground color.  The Racket rule mirrors each row horizontally to form a
4-column strip, then stacks vertically flipped, original, and vertically
flipped copies of that strip.

Ordinary generated inputs use every lawful 3x2 binary mask for which both the
left/right mirror and the up/down strip alternation are visible.  Canonical
symmetric inputs remain valid and are accepted by ``self_check``; they are
excluded only from ordinary draws so generated lessons do not hide a branch.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "1a259ef9a7e7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "091b7cbaf545"
SUMMARY = (
    "Mirror a 3x2 binary source left-to-right into a 3x4 strip, then stack "
    "[vertical-flip, original, vertical-flip] to make a 9x4 output."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is exactly 3x2, matching every canonical train/test input",
    "background is color 0 and exactly one nonzero foreground color is used",
    "ordinary draws are non-monochrome and expose both LR and UD mirror branches",
    "canonical symmetric inputs remain valid even when one branch is invisible in that pair",
]

AXES = {
    "grid_h": {"type": "int", "default": "3", "valid": "3..3"},
    "grid_w": {"type": "int", "default": "2", "valid": "2..2"},
    "color": {"type": "color", "default": "keyed rng 1..9", "valid": "1..9"},
    "mask_index": {
        "type": "int",
        "default": "difficulty-aware index over all branch-visible 3x2 masks",
        "valid": "0..43",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _is_lr_symmetric(mask) -> bool:
    return all(row[0] == row[1] for row in mask)


def _is_ud_symmetric(mask) -> bool:
    return mask[0] == mask[2]


def _mask_from_bits(bits: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        tuple((bits >> (5 - (2 * row + col))) & 1 for col in range(2))
        for row in range(3)
    )


def _mask_complexity(mask) -> tuple[int, int, int]:
    """Order masks from sparse/simple to dense/transition-rich."""
    foreground = sum(sum(row) for row in mask)
    transitions = sum(row[0] != row[1] for row in mask)
    transitions += sum(mask[row][col] != mask[row + 1][col]
                       for row in range(2) for col in range(2))
    bits = sum(mask[row][col] << (5 - (2 * row + col))
               for row in range(3) for col in range(2))
    return foreground, transitions, bits


# 64 total binary 3x2 masks minus the union of LR-symmetric and UD-symmetric
# masks leaves 44 branch-visible masks.  Sorting by a semantic complexity key
# makes draw_int_diff's easy/medium/hard bands meaningful and reproducible.
BRANCH_VISIBLE_MASKS = tuple(sorted(
    (
        mask
        for bits in range(64)
        if (mask := _mask_from_bits(bits))
        and not _is_lr_symmetric(mask)
        and not _is_ud_symmetric(mask)
    ),
    key=_mask_complexity,
))
_MASK_TO_INDEX = {mask: index for index, mask in enumerate(BRANCH_VISIBLE_MASKS)}
assert len(BRANCH_VISIBLE_MASKS) == 44

_CANONICAL_ROLE_MASKS = {
    ((1, 0), (1, 1), (1, 0)): "train_0",
    ((0, 1), (0, 0), (0, 1)): "train_1",
    ((0, 0), (0, 1), (1, 0)): "train_2",
    ((1, 1), (1, 0), (1, 1)): "test_0",
}


def _validate_grid(grid) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], len(grid), 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                return errors, height, width
    return errors, height, width


def _role_mask(grid) -> tuple[tuple[int, int], ...] | None:
    values = {value for row in grid for value in row}
    foreground = values - {0}
    if len(foreground) != 1:
        return None
    color = next(iter(foreground))
    return tuple(tuple(1 if value == color else 0 for value in row) for row in grid)


def canonical_profile_signature(grid) -> str | None:
    errors, height, width = _validate_grid(grid)
    if errors or (height, width) != (3, 2):
        return None
    return _CANONICAL_ROLE_MASKS.get(_role_mask(grid))


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact generated semantic axis from the returned grid."""
    errors, height, width = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    observed: dict[str, int] = {"grid_h": height, "grid_w": width}
    role_mask = _role_mask(grid)
    if role_mask is None:
        return observed
    foreground = {value for row in grid for value in row if value != 0}
    observed["color"] = next(iter(foreground))
    if role_mask in _MASK_TO_INDEX:
        observed["mask_index"] = _MASK_TO_INDEX[role_mask]
    return observed


def rule_mirror(grid) -> list[list[int]]:
    """Python parity oracle used only by focused tests and semantic censuses."""
    height, width = len(grid), len(grid[0])
    output: list[list[int]] = []
    for block in range(3):
        source_rows = range(height - 1, -1, -1) if block % 2 == 0 else range(height)
        for row in source_rows:
            output.append(list(reversed(grid[row])) + list(grid[row]))
    assert len(output) == 3 * height and all(len(row) == 2 * width for row in output)
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int("grid_h", 3, 3)
    width = ctx.draw_int("grid_w", 2, 2)
    color = ctx.draw_int("color", 1, 9)
    mask_index = ctx.draw_int_diff("mask_index", 0, len(BRANCH_VISIBLE_MASKS) - 1)
    mask = BRANCH_VISIBLE_MASKS[mask_index]
    grid = [[color if mask[row][col] else 0 for col in range(width)]
            for row in range(height)]

    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "color": color,
        "mask_index": mask_index,
    }
    if observed != expected:
        raise RuntimeError(f"constructed grid does not realize keyed axes: {expected} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input grammar without rejecting official symmetry."""
    errors, height, width = _validate_grid(grid)
    if errors:
        return errors
    if (height, width) != (3, 2):
        errors.append(f"canonical input must be 3x2, got {height}x{width}")

    values = {value for row in grid for value in row}
    if 0 not in values:
        errors.append("background color 0 is absent")
    foreground = values - {0}
    if len(foreground) != 1:
        errors.append(
            f"expected exactly one nonzero foreground color, got {sorted(foreground)}"
        )
    if len(values) < 2:
        errors.append("input is monochrome")

    role_mask = _role_mask(grid)
    if (
        role_mask is not None
        and role_mask not in _MASK_TO_INDEX
        and role_mask not in _CANONICAL_ROLE_MASKS
    ):
        errors.append(
            "binary mask is outside the canonical examples and the branch-visible teaching domain"
        )

    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
        unknown = set(requested) - set(AXES)
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors and requested:
            observed = observe_overrides(grid)
            for axis, expected in requested.items():
                if observed.get(axis) != expected:
                    errors.append(
                        f"requested {axis}={expected!r}, observed {observed.get(axis)!r}"
                    )
    return errors
