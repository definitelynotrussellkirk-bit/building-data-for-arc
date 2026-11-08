"""Generator for Commanded Crop Rotation (task ``f505996a2fdc``).

The top-left cell is a command.  Clear that cell, crop the remaining nonzero
object, and apply the selected transform:

``1`` identity, ``2`` rotate clockwise, ``3`` rotate 180 degrees,
``4`` transpose, ``5`` flip left/right, ``6`` flip up/down.

The public canonical examples only exercise commands 1..4.  The six-slot
curriculum below deliberately includes commands 5 and 6 in every complete
lesson so a learner cannot silently guess their meanings.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f505996a2fdc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9bbe263d873a"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read command 1..6 from the top-left cell, clear it, tightly crop the "
    "remaining colored object, then apply identity / rotate-cw / rotate-180 / "
    "transpose / flip-left-right / flip-up-down respectively.  A deterministic "
    "six-slot lesson cycle exposes every command and anchors every canonical "
    "input profile."
)

INVARIANTS = [
    "background is 0 and all values are integer ARC colors 0..9",
    "row 0 contains exactly one nonzero command at column 0",
    "row 1 is blank and separates the command from the object",
    "the object has a tight 2..4 by 2..4 crop and 1..3 colors",
    "the object is transform-sensitive; its colored D4 orbit has size at least 4",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-slot canonical-profile curriculum",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "six-slot canonical-profile curriculum",
        "valid": "8..10",
    },
    "cmd": {
        "type": "int",
        "default": "family-permuted six-command cycle",
        "valid": "1..6",
    },
    "blob_h": {
        "type": "int",
        "default": "six-slot transform-sensitive curriculum",
        "valid": "2..4",
    },
    "blob_w": {
        "type": "int",
        "default": "six-slot transform-sensitive curriculum",
        "valid": "2..4",
    },
    "n_colors": {
        "type": "int",
        "default": "six-slot curriculum over 1..2",
        "valid": "1..3",
    },
}

# Every boundary cross-product is constructible on an 8x8 or larger canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

# Five slots exactly match the five canonical (height, width, palette-size)
# profiles.  The sixth repeats a canonical profile while adding a taller crop.
# Command assignment is a seed-stable permutation of 1..6, independent of this
# morphology cycle, so every six consecutive examples expose every command.
_SCHEDULE = (
    {"name": "canonical_8x9", "h": 8, "w": 9, "blob_h": 2, "blob_w": 3, "n_colors": 2},
    {"name": "canonical_9x10", "h": 9, "w": 10, "blob_h": 3, "blob_w": 3, "n_colors": 2},
    {"name": "canonical_8x8", "h": 8, "w": 8, "blob_h": 3, "blob_w": 2, "n_colors": 2},
    {"name": "canonical_10x10", "h": 10, "w": 10, "blob_h": 3, "blob_w": 3, "n_colors": 2},
    {"name": "canonical_9x9_single_color", "h": 9, "w": 9, "blob_h": 2, "blob_w": 3, "n_colors": 1},
    {"name": "canonical_8x9_tall", "h": 8, "w": 9, "blob_h": 4, "blob_w": 3, "n_colors": 2},
)
SCHEDULE_PROFILES = tuple(slot["name"] for slot in _SCHEDULE)

# Tight masks with at least three cells.  Most have full D4 orbit 8 even when
# monochrome; color assignment breaks the remaining symmetries.  The 2x2 case
# necessarily has a smaller orbit when monochrome but still distinguishes both
# reflection axes.
_MASKS: dict[tuple[int, int], tuple[tuple[str, ...], ...]] = {
    (2, 2): (("10", "11"), ("11", "01")),
    (2, 3): (("111", "100"), ("110", "101")),
    (2, 4): (("1111", "1000"), ("1110", "1001")),
    (3, 2): (("11", "10", "10"), ("11", "10", "01")),
    (3, 3): (("110", "011", "010"), ("111", "100", "010")),
    (3, 4): (("1111", "1000", "1000"), ("1111", "1000", "0100")),
    (4, 2): (("11", "10", "10", "10"), ("11", "10", "10", "01")),
    (4, 3): (("111", "100", "100", "100"), ("111", "100", "100", "010")),
    (4, 4): (("1111", "0100", "0100", "0100"), ("1111", "1000", "1000", "0100")),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool or a coercible value)")


def _scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int, overrides: dict[str, Any]) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _command_cycle(seed: int, difficulty: Any) -> tuple[int, ...]:
    """A family-level permutation: six consecutive indexes always cover 1..6."""
    rng = stable_rng(
        seed,
        f"{TASK_ID}|command-cycle|{difficulty or 'unbanded'}",
        VERSION,
    )
    commands = [1, 2, 3, 4, 5, 6]
    rng.shuffle(commands)
    return tuple(commands)


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: _identity,
    2: _rotate_cw,
    3: _rotate_180,
    4: _transpose,
    5: _flip_lr,
    6: _flip_ud,
}


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _d4_variants(grid: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    variants: set[tuple[tuple[int, ...], ...]] = set()
    state = _identity(grid)
    for _ in range(4):
        variants.add(_grid_key(state))
        variants.add(_grid_key(_flip_lr(state)))
        state = _rotate_cw(state)
    return variants


def _mask_variants(rows: tuple[str, ...]) -> list[list[list[int]]]:
    original_h, original_w = len(rows), len(rows[0])
    state = [[int(value) for value in row] for row in rows]
    found: dict[tuple[tuple[int, ...], ...], list[list[int]]] = {}
    for _ in range(4):
        for candidate in (state, _flip_lr(state)):
            if len(candidate) == original_h and len(candidate[0]) == original_w:
                found[_grid_key(candidate)] = _identity(candidate)
        state = _rotate_cw(state)
    return [found[key] for key in sorted(found)]


def _colored_motif(blob_h: int, blob_w: int, n_colors: int, cmd: int, rng) -> list[list[int]]:
    masks = _MASKS[(blob_h, blob_w)]
    candidates: list[list[list[int]]] = []
    for rows in masks:
        candidates.extend(_mask_variants(rows))
    rng.shuffle(candidates)

    palette = rng.sample([color for color in range(1, 10) if color != cmd], n_colors)
    target_orbit = 4 if (blob_h, blob_w, n_colors) == (2, 2, 1) else 8

    best: list[list[int]] | None = None
    best_score = -1
    for attempt in range(256):
        mask = candidates[attempt % len(candidates)]
        points = [(r, c) for r in range(blob_h) for c in range(blob_w) if mask[r][c]]
        values = list(palette)
        while len(values) < len(points):
            values.append(rng.choice(palette))
        rng.shuffle(values)
        motif = full_grid(blob_h, blob_w, 0)
        for (r, c), value in zip(points, values):
            motif[r][c] = value

        transformed = {_grid_key(fn(motif)) for fn in _TRANSFORMS.values()}
        orbit = len(_d4_variants(motif))
        reflections_visible = (
            _grid_key(_flip_lr(motif)) != _grid_key(_flip_ud(motif))
            and _grid_key(_flip_lr(motif)) != _grid_key(motif)
            and _grid_key(_flip_ud(motif)) != _grid_key(motif)
        )
        score = 100 * int(reflections_visible) + 10 * len(transformed) + orbit
        if score > best_score:
            best, best_score = motif, score
        if reflections_visible and orbit >= target_orbit and len(transformed) >= min(6, target_orbit):
            return motif

    if best is None:  # Static mask table guarantees this is unreachable.
        raise RuntimeError("failed to construct a colored motif")
    return best


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one lawful input grid; every declared override is exact or rejected."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = _SCHEDULE[sample_index % len(_SCHEDULE)]
    cycle = _command_cycle(seed, difficulty)

    h = _scheduled_int(ctx, "grid_h", slot["h"], 8, 10, overrides)
    w = _scheduled_int(ctx, "grid_w", slot["w"], 8, 10, overrides)
    cmd = _scheduled_int(
        ctx, "cmd", cycle[sample_index % len(cycle)], 1, 6, overrides
    )
    blob_h = _scheduled_int(ctx, "blob_h", slot["blob_h"], 2, 4, overrides)
    blob_w = _scheduled_int(ctx, "blob_w", slot["blob_w"], 2, 4, overrides)
    n_colors = _scheduled_int(ctx, "n_colors", slot["n_colors"], 1, 3, overrides)

    motif = _colored_motif(
        blob_h,
        blob_w,
        n_colors,
        cmd,
        ctx.draw_rng(f"motif:{difficulty or 'unbanded'}"),
    )
    placement_rng = ctx.draw_rng(f"placement:{difficulty or 'unbanded'}")
    top = placement_rng.randint(2, h - blob_h)
    left = placement_rng.randint(0, w - blob_w)

    grid = full_grid(h, w, 0)
    grid[0][0] = cmd
    for r, row in enumerate(motif):
        for c, value in enumerate(row):
            grid[top + r][left + c] = value
    return grid


def _crop_after_clearing_command(grid: list[list[int]]) -> list[list[int]]:
    clean = [list(row) for row in grid]
    clean[0][0] = 0
    points = [
        (r, c)
        for r, row in enumerate(clean)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        raise ValueError("no nonzero object remains after clearing the command")
    r1, r2 = min(r for r, _ in points), max(r for r, _ in points)
    c1, c2 = min(c for _, c in points), max(c for _, c in points)
    return [row[c1 : c2 + 1] for row in clean[r1 : r2 + 1]]


def _solve_with_map(
    grid: list[list[int]],
    transform_map: dict[int, Callable[[list[list[int]]], list[list[int]]]],
) -> list[list[int]]:
    cmd = grid[0][0]
    return transform_map[cmd](_crop_after_clearing_command(grid))


def _authority_output(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_map(grid, _TRANSFORMS)


_SWAP_UNSEEN_FLIPS = dict(_TRANSFORMS)
_SWAP_UNSEEN_FLIPS[5] = _flip_ud
_SWAP_UNSEEN_FLIPS[6] = _flip_lr

_UNSEEN_AS_IDENTITY = dict(_TRANSFORMS)
_UNSEEN_AS_IDENTITY[5] = _identity
_UNSEEN_AS_IDENTITY[6] = _identity

_WRONG_CODEBOOK = {
    1: _identity,
    2: _rotate_180,
    3: _rotate_cw,
    4: _flip_lr,
    5: _flip_ud,
    6: _rotate_180,
}

_IGNORE_COMMAND = {code: _identity for code in range(1, 7)}


def _swap_unseen_flips(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_map(grid, _SWAP_UNSEEN_FLIPS)


def _unseen_as_identity(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_map(grid, _UNSEEN_AS_IDENTITY)


def _wrong_codebook(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_map(grid, _WRONG_CODEBOOK)


def _ignore_command(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_map(grid, _IGNORE_COMMAND)


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "cmd": None,
        "blob_h": None,
        "blob_w": None,
        "n_colors": None,
        "body_cells": 0,
        "bbox": None,
        "orbit_size": 0,
    }
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        result["errors"].append("grid must be rectangular and nonempty")
        return result
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        result["errors"].append("grid values must be integer ARC colors 0..9")
        return result

    height = len(grid)
    if not 8 <= height <= 10:
        result["errors"].append(f"grid height must be 8..10, got {height}")
    if not 8 <= width <= 10:
        result["errors"].append(f"grid width must be 8..10, got {width}")

    cmd = grid[0][0]
    result["cmd"] = cmd
    if cmd not in _TRANSFORMS:
        result["errors"].append(f"top-left command must be 1..6, got {cmd}")
    if any(value != 0 for value in grid[0][1:]):
        result["errors"].append("row 0 may contain no nonzero value except the command")
    if height >= 2 and any(value != 0 for value in grid[1]):
        result["errors"].append("row 1 must be blank")

    body = [
        (r, c, grid[r][c])
        for r in range(2, height)
        for c in range(width)
        if grid[r][c] != 0
    ]
    result["body_cells"] = len(body)
    if not body:
        result["errors"].append("a nonzero object is required below the separator")
        return result
    if len(body) < 3:
        result["errors"].append(f"object must contain at least 3 cells, got {len(body)}")

    colors = {value for _, _, value in body}
    result["n_colors"] = len(colors)
    if not 1 <= len(colors) <= 3:
        result["errors"].append(f"object must use 1..3 colors, got {sorted(colors)}")
    if cmd in colors:
        result["errors"].append("object colors must exclude the command value")

    r1, r2 = min(r for r, _, _ in body), max(r for r, _, _ in body)
    c1, c2 = min(c for _, c, _ in body), max(c for _, c, _ in body)
    blob_h, blob_w = r2 - r1 + 1, c2 - c1 + 1
    result["blob_h"], result["blob_w"] = blob_h, blob_w
    result["bbox"] = (r1, c1, r2, c2)
    if not (2 <= blob_h <= 4 and 2 <= blob_w <= 4):
        result["errors"].append(
            f"object crop must be 2..4 by 2..4, got {blob_h}x{blob_w}"
        )

    crop = [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]
    orbit_size = len(_d4_variants(crop))
    result["orbit_size"] = orbit_size
    if orbit_size < 4:
        result["errors"].append("colored object hides too many transform meanings")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible teaching grammar without mutation."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The generated teaching manifold; all five official inputs are included."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe axes on malformed grid: " + "; ".join(analysis["errors"])
        )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "cmd": analysis["cmd"],
        "blob_h": analysis["blob_h"],
        "blob_w": analysis["blob_w"],
        "n_colors": analysis["n_colors"],
    }


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]["name"]


def _rival_visible(grid, rival: Callable[[list[list[int]]], list[list[int]]], *, commands=None) -> bool:
    try:
        cmd = grid[0][0]
        return (commands is None or cmd in commands) and rival(grid) != _authority_output(grid)
    except Exception:
        return False


SEMANTIC_RIVALS = {
    "swap_unseen_flips": _swap_unseen_flips,
    "unseen_as_identity": _unseen_as_identity,
    "wrong_codebook": _wrong_codebook,
    "ignore_command": _ignore_command,
}

SEMANTIC_WITNESSES = {
    "swap_unseen_flips_visible": lambda grid: _rival_visible(
        grid, _swap_unseen_flips, commands={5, 6}
    ),
    "unseen_as_identity_visible": lambda grid: _rival_visible(
        grid, _unseen_as_identity, commands={5, 6}
    ),
    "wrong_codebook_visible": lambda grid: _rival_visible(grid, _wrong_codebook),
    "command_effect_visible": lambda grid: _rival_visible(grid, _ignore_command),
}

WITNESS_RIVALS = {
    "swap_unseen_flips_visible": ["swap_unseen_flips"],
    "unseen_as_identity_visible": ["unseen_as_identity"],
    "wrong_codebook_visible": ["wrong_codebook"],
    "command_effect_visible": ["ignore_command"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Both fit every official pair because the canonical inputs use only commands
# 1..4.  Generated command-5/6 examples are explicit counterexamples.
CANONICAL_SHORTCUTS = {
    "swap_unseen_flips": _swap_unseen_flips,
    "unseen_as_identity": _unseen_as_identity,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each five-demo window to eliminate every named rival."""
    reasons: list[str] = []
    demo_commands = {_analysis(demo["input"])["cmd"] for demo in demos}
    if not demo_commands.intersection({5, 6}):
        reasons.append("demos contain no command-5/6 counterexample")
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
