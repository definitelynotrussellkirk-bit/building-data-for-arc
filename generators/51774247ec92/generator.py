"""Generator for ``51774247ec92`` — commanded motif extraction.

A single command cell in row 0 selects one of five transforms.  The lone
4-connected motif below a blank separator row is cropped to its bounding box
and transformed as follows: 2=identity, 3=rotate clockwise, 4=rotate 180,
5=flip left/right, and 6=flip up/down.

The ordinary schedule cycles through all five commands in every five
consecutive examples.  Generated motifs are deliberately asymmetric, so all
five transforms have different outputs; this prevents command-blind or
fixed-transform shortcuts from fitting the teaching distribution.  Every
third ordinary draw is anchored to the empirical canonical profile.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "51774247ec92"
TASK_ID = "51774247ec92"
VERSION = "3.0.0"  # exact axes, canonical anchors, and command-identifying lessons
RULE_HASH = "c74447a07e12"

SUMMARY = (
    "A zero-background grid has one command cell in row 0 and one multicolour "
    "4-connected motif below a blank separator. Crop the motif to its bounding "
    "box, then apply 2=identity, 3=90° clockwise, 4=180°, 5=left/right flip, "
    "or 6=up/down flip."
)

INVARIANTS = [
    "background is 0",
    "row 0 contains exactly one command cell with value 2..6",
    "at least one all-zero row separates the command row from the motif",
    "the top-leftmost body component has a bbox containing every body cell",
    "ordinary generated motifs distinguish all five command transforms",
]

_H_LO, _H_HI = 8, 13
_W_LO, _W_HI = 10, 15
_COMMANDS = (2, 3, 4, 5, 6)
_CANONICAL_PROFILES = ((8, 11), (8, 12), (9, 12), (9, 13))

# Each occupied cell stores a palette-symbol index.  The symbol assignments
# were exhaustively checked for 2, 3, and 4 motif colours: the five commanded
# transforms are pairwise distinct for every profile and colour count.
_PROFILE_DATA: dict[str, tuple[int, int, tuple[tuple[int, int, int], ...]]] = {
    "canonical_a": (
        3,
        3,
        ((0, 0, 0), (1, 0, 0), (1, 1, 1), (1, 2, 2), (2, 1, 3)),
    ),
    "canonical_b": (
        3,
        3,
        ((0, 0, 0), (0, 2, 0), (1, 0, 0), (1, 1, 2), (1, 2, 1), (2, 1, 3)),
    ),
    "canonical_c": (
        3,
        3,
        ((0, 0, 0), (0, 2, 0), (1, 0, 0), (1, 1, 1), (2, 1, 2), (2, 2, 3)),
    ),
    "rect_2x3": (
        2,
        3,
        ((0, 0, 0), (0, 1, 1), (1, 1, 2), (1, 2, 3)),
    ),
    "rect_3x2": (
        3,
        2,
        ((0, 0, 0), (1, 0, 1), (1, 1, 2), (2, 1, 3)),
    ),
    "wide_3x4": (
        3,
        4,
        ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 2, 1), (2, 2, 2), (2, 3, 3)),
    ),
    "tall_4x3": (
        4,
        3,
        ((0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 1), (2, 2, 2), (3, 2, 3)),
    ),
}
_PROFILE_NAMES = tuple(_PROFILE_DATA)
_CANONICAL_PROFILE_NAMES = ("canonical_a", "canonical_b", "canonical_c")
_PROFILE_BY_MASK = {
    frozenset((r, c) for r, c, _ in cells): name
    for name, (_, _, cells) in _PROFILE_DATA.items()
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 8..13; every third ordinary draw uses a canonical joint profile",
        "valid": "8..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 10..15; every third ordinary draw uses a canonical joint profile",
        "valid": "10..15",
    },
    "command": {
        "type": "int",
        "default": "sample_index cycle 2,3,4,5,6",
        "valid": "2..6",
    },
    "motif_profile": {
        "type": "enum",
        "default": "canonical anchor or keyed profile cycle",
        "valid": "canonical_a|canonical_b|canonical_c|rect_2x3|rect_3x2|wide_3x4|tall_4x3",
    },
    "motif_color_count": {
        "type": "int",
        "default": "keyed cycle 2..4; canonical anchors use 2..3",
        "valid": "2..4",
    },
    "command_in_motif": {
        "type": "bool",
        "default": "alternates across ordinary draws",
        "valid": "false|true",
    },
}

# Every Cartesian combination of the exact axes above is supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.30


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def _apply_transform(grid: list[list[int]], command: int) -> list[list[int]]:
    if command == 2:
        return [row[:] for row in grid]
    if command == 3:
        return _rotate_cw(grid)
    if command == 4:
        return _rotate_180(grid)
    if command == 5:
        return _flip_lr(grid)
    if command == 6:
        return _flip_ud(grid)
    raise ValueError(f"unsupported command {command!r}")


def _components4(grid: list[list[int]], *, start_row: int = 1) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(start_row, h)
        for c in range(w)
        if grid[r][c] != 0
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    queue.append((nr, nc))
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def _crop_cells(grid: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _motif_facts(grid: list[list[int]]) -> dict[str, Any]:
    components = _components4(grid)
    if not components:
        return {"components": components, "external_cells": []}
    selected = components[0]
    rows = [r for r, _ in selected]
    cols = [c for _, c in selected]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    all_body_cells = [
        (r, c)
        for r in range(1, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != 0
    ]
    external = [
        (r, c)
        for r, c in all_body_cells
        if not (top <= r <= bottom and left <= c <= right)
    ]
    enclosed = [
        (r, c)
        for r, c in all_body_cells
        if top <= r <= bottom and left <= c <= right
    ]
    normalized = frozenset((r - top, c - left) for r, c in enclosed)
    crop = [row[left : right + 1] for row in grid[top : bottom + 1]]
    colors = {grid[r][c] for r, c in enclosed}
    return {
        "components": components,
        "selected_component": selected,
        "cells": enclosed,
        "external_cells": external,
        "top": top,
        "left": left,
        "motif_height": bottom - top + 1,
        "motif_width": right - left + 1,
        "profile": _PROFILE_BY_MASK.get(normalized),
        "crop": crop,
        "colors": colors,
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not _is_arc_grid(grid):
        return {"errors": ["grid must be a nonempty rectangular ARC grid"]}
    h, w = len(grid), len(grid[0])
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(f"dimensions {h}x{w} outside {_H_LO}..{_H_HI} by {_W_LO}..{_W_HI}")

    row0 = [(c, value) for c, value in enumerate(grid[0]) if value != 0]
    command = row0[0][1] if len(row0) == 1 else None
    command_col = row0[0][0] if len(row0) == 1 else None
    if len(row0) != 1:
        errors.append(f"expected exactly one command cell in row 0, found {len(row0)}")
    elif command not in _COMMANDS:
        errors.append(f"command value {command} is not in 2..6")

    facts = _motif_facts(grid)
    components = facts.get("components", [])
    if not components:
        errors.append("expected at least one nonzero body component")
    else:
        if facts["external_cells"]:
            errors.append(
                f"found {len(facts['external_cells'])} body cell(s) outside the selected component bbox"
            )
        if facts["top"] < 2:
            errors.append("at least one all-zero separator row must precede the motif")
        if not (2 <= facts["motif_height"] <= 4 and 2 <= facts["motif_width"] <= 4):
            errors.append(
                f"motif bbox {facts['motif_height']}x{facts['motif_width']} outside supported 2..4 dimensions"
            )
        if not (2 <= len(facts["colors"]) <= 4):
            errors.append(
                f"motif must use 2-4 distinct colours, found {len(facts['colors'])}"
            )

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "command": command,
        "command_col": command_col,
        **facts,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar while accepting all canonical inputs."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid) -> list[str]:
    """Match the empirical canonical joint profile, not just loose marginals."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    h, w = analysis["grid_h"], analysis["grid_w"]
    if (h, w) not in _CANONICAL_PROFILES:
        reasons.append(f"dimensions {h}x{w} are not a canonical joint profile")
    if analysis["command_col"] != 1:
        reasons.append("canonical command cell is in column 1")
    if analysis["top"] != h - 5:
        reasons.append("canonical motif top row is h-5")
    if (analysis["motif_height"], analysis["motif_width"]) != (3, 3):
        reasons.append("canonical motif bbox is 3x3")
    if len(analysis["cells"]) not in (5, 6):
        reasons.append("canonical motif has 5 or 6 occupied cells")
    if len(analysis["colors"]) not in (2, 3):
        reasons.append("canonical motif uses 2 or 3 colours")
    return reasons


def canonical_like(grid) -> bool:
    """Boolean adapter for the pinned uniform-census protocol."""
    return not strict_canonical_like(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact semantic axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "command": analysis["command"],
        "motif_profile": analysis["profile"],
        "motif_color_count": len(analysis["colors"]),
        "command_in_motif": analysis["command"] in analysis["colors"],
    }


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _ordinary_defaults(seed: int, sample_index: int) -> dict[str, Any]:
    profile_rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|profile", VERSION)
    return {
        "command": _COMMANDS[sample_index % len(_COMMANDS)],
        "motif_profile": _PROFILE_NAMES[(sample_index + profile_rng.randrange(len(_PROFILE_NAMES))) % len(_PROFILE_NAMES)],
        "motif_color_count": 2 + ((seed + sample_index) % 3),
        "command_in_motif": bool((seed + sample_index) % 2),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    explicit = any(value is not None for value in overrides.values())
    effective = _ordinary_defaults(int(seed), int(sample_index))
    effective.update({key: value for key, value in overrides.items() if value is not None})

    canonical_anchor = not explicit and sample_index % 3 == 0
    anchor_profile: tuple[int, int] | None = None
    if canonical_anchor:
        anchor_rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|canonical-anchor", VERSION)
        anchor_profile = anchor_rng.choice(_CANONICAL_PROFILES)
        effective.update(
            {
                "grid_h": anchor_profile[0],
                "grid_w": anchor_profile[1],
                "motif_profile": anchor_rng.choice(_CANONICAL_PROFILE_NAMES),
                "motif_color_count": 2 + anchor_rng.randrange(2),
            }
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_diff("grid_h", _H_LO, _H_HI)
    w = ctx.draw_int_diff("grid_w", _W_LO, _W_HI)
    command = ctx.draw_int("command", 2, 6)
    motif_profile = ctx.draw_choice("motif_profile", _PROFILE_NAMES)
    motif_color_count = ctx.draw_int("motif_color_count", 2, 4)
    command_in_motif = ctx.draw_choice("command_in_motif", (False, True))

    motif_h, motif_w, template = _PROFILE_DATA[motif_profile]
    if motif_h > h - 3 or motif_w > w:
        raise ValueError(f"motif profile {motif_profile!r} does not fit {h}x{w}")

    palette_rng = ctx.draw_rng("motif_palette")
    if command_in_motif:
        other = [c for c in range(1, 10) if c != command]
        palette = [command, *palette_rng.sample(other, motif_color_count - 1)]
    else:
        legal = [c for c in range(1, 10) if c != command]
        palette = palette_rng.sample(legal, motif_color_count)

    grid = full_grid(h, w, 0)
    if canonical_anchor:
        assert anchor_profile == (h, w)
        command_col = 1
        motif_row = h - 5
    else:
        command_col = ctx.draw_int("command_col", 0, w - 1)
        motif_row = ctx.draw_int("motif_row", 2, h - motif_h - 1)
    motif_col = ctx.draw_int("motif_col", 0, w - motif_w)
    grid[0][command_col] = command
    for dr, dc, symbol in template:
        grid[motif_row + dr][motif_col + dc] = palette[symbol % motif_color_count]

    # Fail closed if a future edit accidentally makes an ordinary scene hide a
    # command branch. Canonical inputs are accepted by self_check even when two
    # transforms happen to be answer-equivalent; generated scenes are stricter.
    crop = _motif_facts(grid)["crop"]
    outputs = {_grid_key(_apply_transform(crop, cmd)) for cmd in _COMMANDS}
    if len(outputs) != len(_COMMANDS):
        raise AssertionError("generated motif does not distinguish all five command transforms")
    return grid


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python oracle mirror; the canonical Racket program remains authoritative.

    This intentionally accepts some lesson-invalid recombinations, matching the
    Racket rule's behavior: it takes the first row-0 command and the bbox of the
    top-leftmost body component.  ``self_check`` remains the teaching-distribution
    gate and rejects outside components or other malformed scenes.
    """
    if not _is_arc_grid(grid):
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    row0 = [value for value in grid[0] if value != 0]
    if not row0 or row0[0] not in _COMMANDS:
        raise ValueError("rule_mirror requires a row-0 command in 2..6")
    facts = _motif_facts(grid)
    if not facts.get("components"):
        raise ValueError("rule_mirror requires at least one body component")
    return _apply_transform(facts["crop"], row0[0])


def _fixed_transform(command: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def solve(grid: list[list[int]]) -> list[list[int]]:
        analysis = _analysis(grid)
        if analysis["errors"]:
            raise ValueError("malformed competitor input")
        return _apply_transform(analysis["crop"], command)

    return solve


def _shifted_command_map(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed competitor input")
    shifted = {2: 3, 3: 4, 4: 5, 5: 6, 6: 2}
    return _apply_transform(analysis["crop"], shifted[analysis["command"]])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_command_identity": _fixed_transform(2),
    "always_rotate_cw": _fixed_transform(3),
    "always_rotate_180": _fixed_transform(4),
    "always_flip_lr": _fixed_transform(5),
    "always_flip_ud": _fixed_transform(6),
    "shifted_command_map": _shifted_command_map,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _command_is(value: int) -> Callable[[list[list[int]]], bool]:
    return lambda grid: _analysis(grid).get("command") == value


def _command_reused(grid: list[list[int]]) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["command"] in analysis["colors"]


def _command_absent(grid: list[list[int]]) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["command"] not in analysis["colors"]


def _non_square_motif(grid: list[list[int]]) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["motif_height"] != analysis["motif_width"]


def _all_transforms_distinct(grid: list[list[int]]) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    outputs = {_grid_key(_apply_transform(analysis["crop"], cmd)) for cmd in _COMMANDS}
    return len(outputs) == len(_COMMANDS)


SEMANTIC_WITNESSES = {
    "command_2_identity": _command_is(2),
    "command_3_rotate_cw": _command_is(3),
    "command_4_rotate_180": _command_is(4),
    "command_5_flip_lr": _command_is(5),
    "command_6_flip_ud": _command_is(6),
    "command_colour_reused_in_motif": _command_reused,
    "command_colour_absent_from_motif": _command_absent,
    "non_square_motif": _non_square_motif,
    "all_five_transform_outputs_distinct": _all_transforms_distinct,
}

_FIXED_RIVALS = {
    2: ["always_rotate_cw", "always_rotate_180", "always_flip_lr", "always_flip_ud", "shifted_command_map"],
    3: ["ignore_command_identity", "always_rotate_180", "always_flip_lr", "always_flip_ud", "shifted_command_map"],
    4: ["ignore_command_identity", "always_rotate_cw", "always_flip_lr", "always_flip_ud", "shifted_command_map"],
    5: ["ignore_command_identity", "always_rotate_cw", "always_rotate_180", "always_flip_ud", "shifted_command_map"],
    6: ["ignore_command_identity", "always_rotate_cw", "always_rotate_180", "always_flip_lr", "shifted_command_map"],
}
WITNESS_RIVALS = {
    f"command_{command}_{name}": rivals
    for command, name, rivals in (
        (2, "identity", _FIXED_RIVALS[2]),
        (3, "rotate_cw", _FIXED_RIVALS[3]),
        (4, "rotate_180", _FIXED_RIVALS[4]),
        (5, "flip_lr", _FIXED_RIVALS[5]),
        (6, "flip_ud", _FIXED_RIVALS[6]),
    )
}
WITNESS_RIVALS.update(
    {
        "command_colour_reused_in_motif": ["shifted_command_map"],
        "command_colour_absent_from_motif": ["shifted_command_map"],
        "non_square_motif": ["shifted_command_map"],
        "all_five_transform_outputs_distinct": ["shifted_command_map"],
    }
)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every command mapping to be demonstrated and refute named rivals."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is malformed: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output does not match the commanded transform")
    if reasons:
        return reasons

    demo_commands = {_analysis(pair["input"])["command"] for pair in demos}
    missing = sorted(set(_COMMANDS) - demo_commands)
    if missing:
        reasons.append(f"demonstrations do not expose command mapping(s): {missing}")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not refute rival rule: {name}")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _COMMANDS[int(sample_index) % len(_COMMANDS)]


SCHEDULE_PROFILES = _COMMANDS
