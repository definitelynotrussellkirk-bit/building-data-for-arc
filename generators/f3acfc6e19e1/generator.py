"""Generator for ``arc_puzzle_bank_21_set10_e:hard_j20``.

The first row is an executable key sequence.  In the body, the unique largest
connected object is the payload.  The output crops that object, then packs a
left-to-right gallery containing the original and every cumulative transform
stage, separated by one background column.

Key dictionary:
    2 -> rotate clockwise
    3 -> flip left/right
    4 -> transpose
    5 -> rotate 180 degrees

The four-profile schedule is deliberate: every three consecutive demonstrations
cover every key, cumulative composition, varied placements, and at least one
smaller distractor object.  Shapes are drawn from fully asymmetric D4 orbits so
operator aliases cannot hide behind a symmetric payload.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f3acfc6e19e1"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "708e3724b016"

SUMMARY = (
    "Read the contiguous non-zero keys in row 0 from left to right. Select the "
    "unique largest connected body object, crop it, and emit a horizontal "
    "gallery containing the original shape followed by every cumulative "
    "transform stage. Key 2 rotates clockwise, 3 flips left/right, 4 "
    "transposes, and 5 rotates 180 degrees. Adjacent gallery stages are "
    "separated by one background column. Generated three-demo windows expose "
    "all four keys, cumulative composition, placement irrelevance, and the "
    "largest-object selection rule."
)

INVARIANTS = [
    "background is 0 and every cell is an ARC color 0..9",
    "row 0 contains 1-4 contiguous keys from {2,3,4,5}, starting at column 0",
    "the body contains one unique largest 4-connected monochrome object",
    "smaller distractor objects, when present, lie outside the target bbox",
    "ordinary generated payloads are fully asymmetric under D4 transforms",
    "every three consecutive samples expose all four key meanings and composition",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15

CODES = (2, 3, 4, 5)
CODE_PROFILES: dict[str, tuple[int, ...]] = {
    "cw_then_lr": (2, 3),
    "transpose_then_180": (4, 5),
    "cw_180_transpose": (2, 5, 4),
    "lr_transpose_cw": (3, 4, 2),
}
CODE_PROFILE_NAMES = tuple(CODE_PROFILES)

# Each base shape has an eight-element D4 orbit (no reflection/rotation
# symmetry), and no two profiles are D4-equivalent.
MOTIF_PROFILES: dict[str, tuple[tuple[int, int], ...]] = {
    "l_tetromino": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "p_pentomino": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "f_pentomino": ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    "zig_hexomino": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (3, 2)),
}
MOTIF_PROFILE_NAMES = tuple(MOTIF_PROFILES)

PLACEMENT_PROFILES = ("upper_left", "upper_right", "lower_left", "lower_right")
DECOY_PROFILES = ("none", "one_singleton", "two_small")
DECOY_SCHEDULE = ("none", "one_singleton", "two_small", "one_singleton")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded; canonical anchor 8/9", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "difficulty-banded; canonical anchor 12", "valid": "10..14"},
    "code_profile": {
        "type": "str",
        "default": "four-profile cyclic teaching schedule",
        "valid": "cw_then_lr|transpose_then_180|cw_180_transpose|lr_transpose_cw",
    },
    "motif_profile": {
        "type": "str",
        "default": "seed-shifted asymmetric-shape schedule",
        "valid": "l_tetromino|p_pentomino|f_pentomino|zig_hexomino",
    },
    "motif_color": {"type": "color", "default": "rng non-zero", "valid": "1..9"},
    "placement_profile": {
        "type": "str",
        "default": "seed-shifted quadrant schedule",
        "valid": "upper_left|upper_right|lower_left|lower_right",
    },
    "decoy_profile": {
        "type": "str",
        "default": "seed-shifted none/singleton/domino schedule",
        "valid": "none|one_singleton|two_small",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _seed_phase(seed: int, label: str, period: int) -> int:
    """Stable seed-only phase for cyclic schedules.

    Keeping the phase independent of ``sample_index`` preserves sliding-window
    guarantees, while hashing the seed avoids affine seed/index aliases such as
    ``seed=i, sample_index=37*i`` collapsing an axis to one value.
    """
    digest = hashlib.sha256(
        f"{TASK_ID}|{VERSION}|{label}|{seed}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") % period


def _normalize_cells(cells: Any) -> tuple[tuple[int, int], ...]:
    cells = tuple((int(r), int(c)) for r, c in cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform_cells(cells: Any, transform: int) -> tuple[tuple[int, int], ...]:
    transformed: list[tuple[int, int]] = []
    for r, c in cells:
        if transform == 0:      # identity
            point = (r, c)
        elif transform == 1:    # rotate clockwise
            point = (c, -r)
        elif transform == 2:    # rotate 180
            point = (-r, -c)
        elif transform == 3:    # rotate counter-clockwise
            point = (-c, r)
        elif transform == 4:    # flip left/right
            point = (r, -c)
        elif transform == 5:    # flip up/down
            point = (-r, c)
        elif transform == 6:    # transpose
            point = (c, r)
        elif transform == 7:    # anti-transpose
            point = (-c, -r)
        else:
            raise ValueError(f"unknown D4 transform: {transform}")
        transformed.append(point)
    return _normalize_cells(transformed)


def _shape_signature(cells: Any) -> tuple[tuple[int, int], ...]:
    normalized = _normalize_cells(cells)
    return min(_transform_cells(normalized, transform) for transform in range(8))


_PROFILE_BY_SIGNATURE = {
    _shape_signature(cells): name for name, cells in MOTIF_PROFILES.items()
}


def _draw_dimension(ctx, label: str, band: str, anchor: bool, overrides: dict[str, Any]) -> int:
    if label in overrides:
        lo, hi = (8, 12) if label == "grid_h" else (10, 14)
        return ctx.draw_int(label, lo, hi)
    if anchor:
        if label == "grid_h":
            return ctx.draw_choice(label, [9 if band == "hard" else 8])
        return ctx.draw_choice(label, [12])
    choices = {
        "grid_h": {
            "easy": [8, 9],
            "medium": [8, 9, 10],
            "hard": [9, 10, 11, 12],
        },
        "grid_w": {
            "easy": [10, 11, 12],
            "medium": [11, 12, 13],
            "hard": [12, 13, 14],
        },
    }[label][band]
    return ctx.draw_choice(label, choices)


def _draw_choice_axis(
    ctx,
    label: str,
    options: tuple[str, ...],
    default: str,
    overrides: dict[str, Any],
) -> str:
    if label in overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, [default])


def _draw_motif_color(
    ctx,
    *,
    anchor: bool,
    keys: tuple[int, ...],
    overrides: dict[str, Any],
) -> int:
    if "motif_color" in overrides:
        return ctx.draw_color("motif_color", exclude={0})
    if anchor:
        # Keep the canonical anchor at four total colors. Two-key profiles need
        # a new motif color; three-key profiles need a color already used by a
        # key, exactly as two official examples do.
        if len(set(keys)) == 2:
            choices = [color for color in (1, 6, 7, 8, 9) if color not in keys]
        else:
            choices = list(dict.fromkeys(keys))
        return ctx.draw_choice("motif_color", choices)
    return ctx.draw_choice("motif_color", [1, 6, 7, 8, 9])


def _placement_origin(
    profile: str, h: int, w: int, shape_h: int, shape_w: int
) -> tuple[int, int]:
    upper = 2
    lower = h - shape_h - 1
    left = 1
    right = w - shape_w - 1
    positions = {
        "upper_left": (upper, left),
        "upper_right": (upper, right),
        "lower_left": (lower, left),
        "lower_right": (lower, right),
    }
    row, col = positions[profile]
    if row < 2 or col < 0 or row + shape_h > h or col + shape_w > w:
        raise ValueError(
            f"placement {profile!r} cannot fit {shape_h}x{shape_w} in {h}x{w}"
        )
    return row, col


def _adjacent_to(cells: set[tuple[int, int]], cell: tuple[int, int]) -> bool:
    r, c = cell
    return any((r + dr, c + dc) in cells for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)))


def _place_decoys(
    grid: list[list[int]],
    *,
    profile: str,
    target_cells: set[tuple[int, int]],
    target_bbox: tuple[int, int, int, int],
    target_color: int,
    rng: Any,
) -> None:
    if profile == "none":
        return

    h, w = len(grid), len(grid[0])
    r0, c0, r1, c1 = target_bbox
    outside_bbox = [
        (r, c)
        for r in range(2, h)
        for c in range(w)
        if not (r0 <= r <= r1 and c0 <= c <= c1)
        and not _adjacent_to(target_cells, (r, c))
    ]
    rng.shuffle(outside_bbox)
    if not outside_bbox:
        raise ValueError("no legal cell remains for distractor placement")

    decoy_colors = [color for color in range(1, 10) if color != target_color]
    used = set(target_cells)

    singleton = outside_bbox.pop()
    singleton_color = rng.choice(decoy_colors)
    grid[singleton[0]][singleton[1]] = singleton_color
    used.add(singleton)
    if profile == "one_singleton":
        return
    if profile != "two_small":
        raise ValueError(f"unknown decoy profile: {profile!r}")

    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(2, h):
        for c in range(w):
            for dr, dc in ((0, 1), (1, 0)):
                a, b = (r, c), (r + dr, c + dc)
                if b[0] >= h or b[1] >= w:
                    continue
                if any(r0 <= x <= r1 and c0 <= y <= c1 for x, y in (a, b)):
                    continue
                if _adjacent_to(used, a) or _adjacent_to(used, b):
                    continue
                pairs.append((a, b))
    if not pairs:
        raise ValueError("no legal domino remains for distractor placement")
    a, b = rng.choice(pairs)
    domino_color = rng.choice(decoy_colors)
    grid[a[0]][a[1]] = domino_color
    grid[b[0]][b[1]] = domino_color


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    # Independent of the four-profile key schedule, roughly one fifth of the
    # default draws pin the exact official (height, width, palette, object-size)
    # profile. A seed-only hashed phase prevents common affine replay patterns
    # from collapsing this support.
    anchor = (sample_index + _seed_phase(seed, "anchor", 5)) % 5 == 0
    h = _draw_dimension(ctx, "grid_h", band, anchor, overrides)
    w = _draw_dimension(ctx, "grid_w", band, anchor, overrides)

    code_profile = _draw_choice_axis(
        ctx,
        "code_profile",
        CODE_PROFILE_NAMES,
        CODE_PROFILE_NAMES[sample_index % len(CODE_PROFILE_NAMES)],
        overrides,
    )
    keys = CODE_PROFILES[code_profile]

    motif_default = (
        "l_tetromino"
        if anchor
        else MOTIF_PROFILE_NAMES[
            (
                3 * sample_index
                + _seed_phase(seed, "motif_schedule", len(MOTIF_PROFILE_NAMES))
            )
            % len(MOTIF_PROFILE_NAMES)
        ]
    )
    motif_profile = _draw_choice_axis(
        ctx, "motif_profile", MOTIF_PROFILE_NAMES, motif_default, overrides
    )
    placement_default = PLACEMENT_PROFILES[
        (
            sample_index
            + _seed_phase(seed, "placement_schedule", len(PLACEMENT_PROFILES))
        )
        % len(PLACEMENT_PROFILES)
    ]
    placement_profile = _draw_choice_axis(
        ctx,
        "placement_profile",
        PLACEMENT_PROFILES,
        placement_default,
        overrides,
    )
    decoy_default = (
        "none"
        if anchor
        else DECOY_SCHEDULE[
            (
                sample_index
                + _seed_phase(seed, "decoy_schedule", len(DECOY_SCHEDULE))
            )
            % len(DECOY_SCHEDULE)
        ]
    )
    decoy_profile = _draw_choice_axis(
        ctx, "decoy_profile", DECOY_PROFILES, decoy_default, overrides
    )
    motif_color = _draw_motif_color(
        ctx, anchor=anchor, keys=keys, overrides=overrides
    )

    grid = full_grid(h, w, 0)
    for col, key in enumerate(keys):
        grid[0][col] = key

    orientation = ctx.draw_rng("motif_orientation").randrange(8)
    motif_cells = _transform_cells(MOTIF_PROFILES[motif_profile], orientation)
    shape_h = max(r for r, _ in motif_cells) + 1
    shape_w = max(c for _, c in motif_cells) + 1
    top, left = _placement_origin(
        placement_profile, h, w, shape_h, shape_w
    )
    target_cells = {(top + r, left + c) for r, c in motif_cells}
    for row, col in target_cells:
        grid[row][col] = motif_color

    _place_decoys(
        grid,
        profile=decoy_profile,
        target_cells=target_cells,
        target_bbox=(top, left, top + shape_h - 1, left + shape_w - 1),
        target_color=motif_color,
        rng=ctx.draw_rng("decoy_layout"),
    )
    return grid


def _components_nonzero_body(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(1, h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _bbox(cells: Any) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []
    r0, c0, r1, c1 = _bbox(cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


_TRANSFORMS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "rotate_cw": _rotate_cw,
    "flip_lr": _flip_lr,
    "transpose": _transpose,
    "rotate_180": _rotate_180,
}
_DEFAULT_KEY_MAP = {
    2: "rotate_cw",
    3: "flip_lr",
    4: "transpose",
    5: "rotate_180",
}


def _apply_key(
    shape: list[list[int]],
    key: int,
    key_map: dict[int, str] | None = None,
) -> list[list[int]]:
    mapping = dict(_DEFAULT_KEY_MAP)
    if key_map:
        mapping.update(key_map)
    return _crop(_TRANSFORMS[mapping[key]](shape))


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    info.update({"grid_h": h, "grid_w": w})
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if not (5 <= h <= 30 and 5 <= w <= 30):
        errors.append(f"grid dimensions must be within 5..30, got {h}x{w}")

    flat = [value for row in grid for value in row]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not (0 <= value <= 9)
        for value in flat
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return info, errors

    if h > 1 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator between keys and body")

    nonzero_cols = [col for col, value in enumerate(grid[0]) if value != 0]
    keys = tuple(grid[0][col] for col in nonzero_cols)
    info["keys"] = keys
    if not (1 <= len(keys) <= 4):
        errors.append(f"expected 1-4 row-0 keys, found {len(keys)}")
    if nonzero_cols != list(range(len(nonzero_cols))):
        errors.append("row-0 keys must be contiguous from column 0")
    if any(key not in CODES for key in keys):
        errors.append("row-0 keys must be in {2,3,4,5}")

    components = _components_nonzero_body([list(row) for row in grid])
    info["components"] = components
    if not components:
        errors.append("body must contain a non-zero object")
        return info, errors
    max_size = max(len(component["cells"]) for component in components)
    largest = [component for component in components if len(component["cells"]) == max_size]
    if len(largest) != 1:
        errors.append(f"body must have one unique largest object, found {len(largest)} tied at size {max_size}")
        return info, errors
    target = largest[0]
    info["target"] = target
    if len(target["cells"]) < 3:
        errors.append(f"largest object must have at least 3 cells, got {len(target['cells'])}")

    target_bbox = _bbox(target["cells"])
    info["target_bbox"] = target_bbox
    r0, c0, r1, c1 = target_bbox
    target_set = set(target["cells"])
    contaminating = [
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if grid[r][c] != 0 and (r, c) not in target_set
    ]
    if contaminating:
        errors.append("a smaller body object lies inside the largest-object bbox")

    if keys and not errors:
        # Analyse the already-selected target directly. Calling the public
        # gallery helper here would recurse through _extract_shape -> _analyse.
        start = _crop(
            [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]
        )
        current = start
        changed = False
        for key in keys:
            current = _apply_key(current, key)
            changed = changed or current != start
        if not changed:
            errors.append(
                "the complete key pipeline leaves the target visually unchanged"
            )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid input grammar; accepts every official train/test input."""
    return _analyse(grid)[1]


def _extract_shape(grid: list[list[int]], *, selection: str) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if selection == "largest":
        cells = info["target"]["cells"]
    elif selection == "all_body":
        cells = [
            (r, c)
            for r in range(1, len(grid))
            for c, value in enumerate(grid[r])
            if value != 0
        ]
    else:
        raise ValueError(f"unknown selection mode: {selection!r}")
    r0, c0, r1, c1 = _bbox(cells)
    return _crop([list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]])


def _gallery_stages(
    grid: list[list[int]],
    *,
    selection: str = "largest",
    key_map: dict[int, str] | None = None,
    independent: bool = False,
    reverse_keys: bool = False,
) -> list[list[list[int]]]:
    keys = [value for value in grid[0] if value != 0]
    if reverse_keys:
        keys = list(reversed(keys))
    start = _extract_shape(grid, selection=selection)
    stages = [[list(row) for row in start]]
    current = start
    for key in keys:
        source = start if independent else current
        current = _apply_key(source, key, key_map)
        stages.append(current)
    return stages


def _pack_stages(stages: list[list[list[int]]]) -> list[list[int]]:
    out_h = max(len(stage) for stage in stages)
    out_w = sum(len(stage[0]) for stage in stages) + len(stages) - 1
    output = full_grid(out_h, out_w, 0)
    left = 0
    for stage in stages:
        for row, values in enumerate(stage):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][left + col] = value
        left += len(stage[0]) + 1
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for semantic tests; Racket remains authority."""
    return _pack_stages(_gallery_stages(grid))


def _rival_final_stage_only(grid: list[list[int]]) -> list[list[int]]:
    return _gallery_stages(grid)[-1]


def _rival_independent_non_cumulative(grid: list[list[int]]) -> list[list[int]]:
    return _pack_stages(_gallery_stages(grid, independent=True))


def _rival_reverse_key_order(grid: list[list[int]]) -> list[list[int]]:
    return _pack_stages(_gallery_stages(grid, reverse_keys=True))


def _rival_crop_all_body_content(grid: list[list[int]]) -> list[list[int]]:
    return _pack_stages(_gallery_stages(grid, selection="all_body"))


def _mapped_rival(mapping: dict[int, str]):
    def rival(grid: list[list[int]]) -> list[list[int]]:
        return _pack_stages(_gallery_stages(grid, key_map=mapping))

    return rival


_rival_code_2_as_transpose = _mapped_rival({2: "transpose"})
_rival_code_3_as_rotate_180 = _mapped_rival({3: "rotate_180"})
_rival_code_4_as_flip_lr = _mapped_rival({4: "flip_lr"})
_rival_code_5_as_rotate_cw = _mapped_rival({5: "rotate_cw"})

SEMANTIC_RIVALS = {
    "final_stage_only": _rival_final_stage_only,
    "independent_non_cumulative": _rival_independent_non_cumulative,
    "reverse_key_order": _rival_reverse_key_order,
    "crop_all_body_content": _rival_crop_all_body_content,
    "code_2_as_transpose": _rival_code_2_as_transpose,
    "code_3_as_rotate_180": _rival_code_3_as_rotate_180,
    "code_4_as_flip_lr": _rival_code_4_as_flip_lr,
    "code_5_as_rotate_cw": _rival_code_5_as_rotate_cw,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All official inputs contain only one body object, so canonical examples
    # alone cannot distinguish this shortcut from the selected largest-object
    # rule. Generated decoys are the required counterexample.
    "crop_all_body_content": _rival_crop_all_body_content,
}


def _witness_against(rival_name: str, *, required_code: int | None = None, require_decoy: bool = False):
    rival = SEMANTIC_RIVALS[rival_name]

    def predicate(grid: list[list[int]]) -> bool:
        info, errors = _analyse(grid)
        if errors:
            return False
        if required_code is not None and required_code not in info["keys"]:
            return False
        if require_decoy and len(info["components"]) < 2:
            return False
        return rule_mirror(grid) != rival(grid)

    return predicate


SEMANTIC_WITNESSES = {
    "code_2_means_rotate_cw": _witness_against("code_2_as_transpose", required_code=2),
    "code_3_means_flip_lr": _witness_against("code_3_as_rotate_180", required_code=3),
    "code_4_means_transpose": _witness_against("code_4_as_flip_lr", required_code=4),
    "code_5_means_rotate_180": _witness_against("code_5_as_rotate_cw", required_code=5),
    "gallery_keeps_intermediate_stages": _witness_against("final_stage_only"),
    "pipeline_is_cumulative": _witness_against("independent_non_cumulative"),
    "keys_are_read_left_to_right": _witness_against("reverse_key_order"),
    "unique_largest_object_is_selected": _witness_against(
        "crop_all_body_content", require_decoy=True
    ),
}
WITNESS_RIVALS = {
    "code_2_means_rotate_cw": ["code_2_as_transpose"],
    "code_3_means_flip_lr": ["code_3_as_rotate_180"],
    "code_4_means_transpose": ["code_4_as_flip_lr"],
    "code_5_means_rotate_180": ["code_5_as_rotate_cw"],
    "gallery_keeps_intermediate_stages": ["final_stage_only"],
    "pipeline_is_cumulative": ["independent_non_cumulative"],
    "keys_are_read_left_to_right": ["reverse_key_order"],
    "unique_largest_object_is_selected": ["crop_all_body_content"],
}


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (info["grid_h"], info["grid_w"]) not in {(8, 12), (9, 12)}:
        reasons.append("official inputs are 8x12 or 9x12")
    if len(info["keys"]) not in (2, 3):
        reasons.append("official inputs use two or three transform keys")
    if len(info["components"]) != 1:
        reasons.append("official inputs contain exactly one body object")
    if len(info["target"]["cells"]) != 4:
        reasons.append("official payload objects have four cells")
    palette_size = len({value for row in grid for value in row})
    if palette_size != 4:
        reasons.append("official inputs use exactly four colors including background")
    return reasons


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every exact generated axis from the returned grid."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))

    keys = tuple(info["keys"])
    code_profile = next(
        (name for name, sequence in CODE_PROFILES.items() if sequence == keys),
        None,
    )
    if code_profile is None:
        raise ValueError(f"unrecognized generated code sequence: {keys}")

    target = info["target"]
    r0, c0, r1, c1 = info["target_bbox"]
    local_cells = [(r - r0, c - c0) for r, c in target["cells"]]
    motif_profile = _PROFILE_BY_SIGNATURE.get(_shape_signature(local_cells))
    if motif_profile is None:
        raise ValueError("target shape is not one of the generated motif profiles")

    shape_h, shape_w = r1 - r0 + 1, c1 - c0 + 1
    placement_profile = next(
        (
            name
            for name in PLACEMENT_PROFILES
            if _placement_origin(name, info["grid_h"], info["grid_w"], shape_h, shape_w)
            == (r0, c0)
        ),
        None,
    )
    if placement_profile is None:
        raise ValueError("target position is not one of the generated placement profiles")

    decoy_sizes = sorted(
        len(component["cells"])
        for component in info["components"]
        if component is not target
    )
    decoy_profile = {
        (): "none",
        (1,): "one_singleton",
        (1, 2): "two_small",
    }.get(tuple(decoy_sizes))
    if decoy_profile is None:
        raise ValueError(f"unrecognized generated distractor sizes: {decoy_sizes}")

    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "code_profile": code_profile,
        "motif_profile": motif_profile,
        "motif_color": target["color"],
        "placement_profile": placement_profile,
        "decoy_profile": decoy_profile,
    }


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    keys_seen: set[int] = set()
    valid_pairs: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the cumulative gallery rule")
            continue
        keys_seen.update(value for value in pair["input"][0] if value != 0)
        valid_pairs.append(pair)

    missing_keys = set(CODES) - keys_seen
    if missing_keys:
        reasons.append(f"demonstrations do not expose keys: {sorted(missing_keys)}")

    if valid_pairs:
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(pair["input"]) == pair["output"] for pair in valid_pairs):
                reasons.append(f"competitor survives every demonstration: {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the cumulative gallery rule")
    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    return CODE_PROFILE_NAMES[sample_index % len(CODE_PROFILE_NAMES)]


SCHEDULE_PROFILES = CODE_PROFILE_NAMES
