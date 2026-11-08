"""Generator for ARC task 5f4098cd075a — keyed prototype library lookup.

The input contains a source library above a full color-9 divider and target
frames below it.  Every source panel has a key marker in its top row and a
single-color connected prototype inside a color-5 frame.  Every target panel
has a key marker and an empty color-5 frame.  The oracle copies the complete
3x3 prototype belonging to each target key into that target frame.

Version 3 repairs three teaching-distribution defects in the previous source:

* it pins the canonical Racket rule hash;
* it replaces dead palette/texture metadata with three exact observable axes;
* it covers the canonical full-target and repeated-key branches (the public
  test uses target keys [1, 3, 1]), while forcing target/source position
  mismatches and distinct prototypes so fixed-position, key-as-answer, and
  modal-prototype shortcuts fail.

With no overrides, sample_index modulo four schedules a canonical-profile
anchor, a full unique target row, a full repeated target row, and a partial
unique target row.  Thus every four-pair downstream lesson exposes all major
semantic branches without relying on chance.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5f4098cd075a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "27d29e43e3ba"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Read the keyed prototype library above the color-9 divider. For each "
    "keyed empty frame below it, copy the complete 3x3 prototype from the "
    "source frame carrying the same key, preserving target order and repeats."
)

EXAMPLES_NEEDED = 3

FRAME = 5
PITCH = FRAME + 1
DIVIDER_ROW = FRAME + 1
TARGET_KEY_ROW = DIVIDER_ROW + 1
TARGET_FRAME_TOP = TARGET_KEY_ROW + 1
GRID_H = TARGET_FRAME_TOP + FRAME
STRUCTURAL_COLORS = {0, 5, 9}
CONTENT_COLORS = (1, 2, 3, 4, 6, 7, 8)

INVARIANTS = [
    "background is 0; every frame is color 5; all panel separators and the middle divider are color 9",
    "source keys are distinct non-structural colors and each source frame contains one nonempty connected single-color prototype",
    "source prototype binary shapes and prototype colors are pairwise distinct, and a prototype color never equals its own key",
    "target panels are left-packed empty frames whose keys all occur in the source library",
    "there are at least two target panels and at least two distinct target keys; repeated target keys are lawful and intentionally generated",
    "at least one target panel requests a source prototype from a different panel index, defeating fixed-position copying",
]

AXES = {
    "n_src": {
        "type": "int",
        "default": "scheduled/difficulty-aware 3..5 source panels",
        "valid": "3..5",
    },
    "n_tgt": {
        "type": "int",
        "default": "scheduled 2..n_src left-packed target panels",
        "valid": "2..5",
    },
    "target_repeats": {
        "type": "bool",
        "default": "scheduled false,false,true,false",
        "valid": "false|true",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# The exact canonical profile occupies one of four scheduled default branches.
MIN_STRICT_FRAC = 0.20


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        row, col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen == cells


def _motif_catalog() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    positions = tuple((row, col) for row in range(3) for col in range(3))
    catalog: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 8):
        motifs = [tuple(combo) for combo in combinations(positions, size) if _is_connected(combo)]
        catalog[size] = tuple(motifs)
    return catalog


_MOTIFS_BY_SIZE = _motif_catalog()


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for name, lo, hi in (("n_src", 3, 5), ("n_tgt", 2, 5)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")

    if "target_repeats" in overrides and overrides["target_repeats"] is not None:
        if not isinstance(overrides["target_repeats"], bool):
            raise ValueError("target_repeats must be a bool")

    n_src = overrides.get("n_src")
    n_tgt = overrides.get("n_tgt")
    repeats = overrides.get("target_repeats")
    if n_src is not None and n_tgt is not None and n_tgt > n_src:
        raise ValueError("n_tgt cannot exceed n_src because targets share the source canvas width")
    if repeats is True and n_tgt is not None and n_tgt < 3:
        raise ValueError("target_repeats=True requires n_tgt >= 3 so two distinct keys remain visible")


def _draw_axes(ctx, sample_index: int, difficulty: Any, overrides: dict[str, Any]) -> tuple[int, int, bool, bool]:
    """Return exact axes plus whether this is the canonical-profile branch."""
    has_override = any(overrides.get(name) is not None for name in AXES)
    scenario = sample_index % 4

    if not has_override:
        if scenario == 0:
            n_src = ctx.draw_int("n_src", 3, 3)
            n_tgt = ctx.draw_int("n_tgt", 2, 2)
            repeats = ctx.draw_choice("target_repeats", (False,))
            return n_src, n_tgt, repeats, True
        if scenario == 1:
            n_src = ctx.draw_int_diff("n_src", 3, 5)
            n_tgt = ctx.draw_int("n_tgt", n_src, n_src)
            repeats = ctx.draw_choice("target_repeats", (False,))
            return n_src, n_tgt, repeats, False
        if scenario == 2:
            n_src = ctx.draw_int_diff("n_src", 3, 5)
            n_tgt = ctx.draw_int("n_tgt", n_src, n_src)
            repeats = ctx.draw_choice("target_repeats", (True,))
            return n_src, n_tgt, repeats, False
        n_src = ctx.draw_int_diff("n_src", 4, 5)
        n_tgt = ctx.draw_int("n_tgt", 2, n_src - 1)
        repeats = ctx.draw_choice("target_repeats", (False,))
        return n_src, n_tgt, repeats, False

    requested_n_src = overrides.get("n_src")
    requested_n_tgt = overrides.get("n_tgt")
    requested_repeats = overrides.get("target_repeats")

    # A single n_tgt boundary override must remain feasible in every band.
    min_src = max(3, int(requested_n_tgt or 3))
    if requested_n_src is not None:
        n_src = ctx.draw_int("n_src", 3, 5)
    else:
        n_src = ctx.draw_int_diff("n_src", min_src, 5)

    if requested_repeats is not None:
        repeats = ctx.draw_choice("target_repeats", (False, True))
    elif requested_n_tgt == 2:
        # The n_tgt=2 boundary is independently lawful.  Do not let the
        # scheduled repeated-target branch make this single-axis override
        # spuriously fail; repeats require at least three visible targets.
        repeats = ctx.draw_choice("target_repeats", (False,))
    else:
        repeats = ctx.draw_choice("target_repeats", (scenario == 2,))

    if requested_n_tgt is not None:
        n_tgt = ctx.draw_int("n_tgt", 2, n_src)
    elif repeats:
        n_tgt = ctx.draw_int("n_tgt", 3, n_src)
    else:
        n_tgt = ctx.draw_int("n_tgt", 2, n_src)

    if repeats and n_tgt < 3:
        raise ValueError("target_repeats=True requires n_tgt >= 3")
    return n_src, n_tgt, repeats, False


def _draw_frame(grid: list[list[int]], top: int, left: int) -> None:
    for col in range(left, left + FRAME):
        grid[top][col] = 5
        grid[top + FRAME - 1][col] = 5
    for row in range(top, top + FRAME):
        grid[row][left] = 5
        grid[row][left + FRAME - 1] = 5


def _draw_distinct_motifs(rng, n_src: int, difficulty: Any, canonical_anchor: bool):
    if canonical_anchor:
        sizes = (4, 5, 5)
        motifs = []
        used = set()
        for size in sizes:
            choices = [motif for motif in _MOTIFS_BY_SIZE[size] if motif not in used]
            motif = rng.choice(choices)
            motifs.append(motif)
            used.add(motif)
        return motifs

    if difficulty == "easy":
        min_size, max_size = 3, 5
    elif difficulty == "hard":
        min_size, max_size = 4, 7
    else:
        min_size, max_size = 3, 6

    motifs = [rng.choice(_MOTIFS_BY_SIZE[min_size]), rng.choice(_MOTIFS_BY_SIZE[max_size])]
    used = set(motifs)
    pool = [
        motif
        for size in range(min_size, max_size + 1)
        for motif in _MOTIFS_BY_SIZE[size]
        if motif not in used
    ]
    rng.shuffle(pool)
    motifs.extend(pool[: n_src - len(motifs)])
    rng.shuffle(motifs)
    return motifs


def _draw_keys_and_colors(rng, n_src: int, canonical_anchor: bool):
    if canonical_anchor:
        return [1, 2, 3], [4, 7, 8]

    keys = rng.sample(list(CONTENT_COLORS), n_src)
    for _ in range(128):
        proto_colors = rng.sample(list(CONTENT_COLORS), n_src)
        if all(proto_colors[index] != keys[index] for index in range(n_src)):
            return keys, proto_colors
    raise ValueError("could not draw a distinct deranged prototype palette")


def _has_position_mismatch(target_keys: list[int], source_keys: list[int]) -> bool:
    source_index = {key: index for index, key in enumerate(source_keys)}
    return any(source_index[key] != index for index, key in enumerate(target_keys))


def _draw_target_keys(rng, source_keys: list[int], n_tgt: int, repeats: bool) -> list[int]:
    if repeats:
        first, second = rng.sample(source_keys, 2)
        target_keys = [first, first, second]
        target_keys.extend(rng.choice(source_keys) for _ in range(n_tgt - 3))
        rng.shuffle(target_keys)
    else:
        target_keys = rng.sample(source_keys, n_tgt)
        if not _has_position_mismatch(target_keys, source_keys):
            target_keys = target_keys[1:] + target_keys[:1]

    if len(set(target_keys)) < 2:
        raise ValueError("target schedule must expose at least two source keys")
    if repeats != (len(set(target_keys)) < len(target_keys)):
        raise ValueError("target repeat schedule did not realize its exact axis")
    if not _has_position_mismatch(target_keys, source_keys):
        raise ValueError("target schedule accidentally admits fixed-position copying")
    return target_keys


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-degenerate keyed-library input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_src, n_tgt, repeats, canonical_anchor = _draw_axes(
        ctx, sample_index, difficulty, overrides
    )
    rng = ctx.draw_rng("layout")

    keys, prototype_colors = _draw_keys_and_colors(rng, n_src, canonical_anchor)
    motifs = _draw_distinct_motifs(rng, n_src, difficulty, canonical_anchor)
    target_keys = _draw_target_keys(rng, keys, n_tgt, repeats)

    width = n_src * PITCH - 1
    grid = full_grid(GRID_H, width, 0)

    for index, (key, color, motif) in enumerate(zip(keys, prototype_colors, motifs)):
        left = index * PITCH
        grid[0][left + FRAME // 2] = key
        _draw_frame(grid, 1, left)
        for inner_row, inner_col in motif:
            grid[2 + inner_row][left + 1 + inner_col] = color
        if index < n_src - 1:
            separator = left + FRAME
            for row in range(0, FRAME + 1):
                grid[row][separator] = 9

    for col in range(width):
        grid[DIVIDER_ROW][col] = 9

    for index, key in enumerate(target_keys):
        left = index * PITCH
        grid[TARGET_KEY_ROW][left + FRAME // 2] = key
        _draw_frame(grid, TARGET_FRAME_TOP, left)
        if index < n_tgt - 1:
            separator = left + FRAME
            for row in range(TARGET_KEY_ROW, GRID_H):
                grid[row][separator] = 9

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["grid cells must be integer ARC colors 0..9"]
    return []


def _frame_errors(grid, top: int, left: int, *, empty: bool) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    border = []
    for row in range(top, top + FRAME):
        for col in range(left, left + FRAME):
            if row in (top, top + FRAME - 1) or col in (left, left + FRAME - 1):
                border.append(grid[row][col])
    if any(value != 5 for value in border):
        errors.append(f"frame at ({top},{left}) does not have an exact color-5 border")

    interior = [
        [grid[row][col] for col in range(left + 1, left + FRAME - 1)]
        for row in range(top + 1, top + FRAME - 1)
    ]
    cells = {
        (row, col)
        for row in range(3)
        for col in range(3)
        if interior[row][col] != 0
    }
    colors = {interior[row][col] for row, col in cells}
    if empty:
        if cells:
            errors.append(f"target frame at ({top},{left}) is not empty")
    else:
        if not 3 <= len(cells) <= 7:
            errors.append(f"source prototype at ({top},{left}) has {len(cells)} cells, expected 3..7")
        if len(colors) != 1 or colors & STRUCTURAL_COLORS:
            errors.append(f"source prototype at ({top},{left}) must use one non-structural color")
        if cells and not _is_connected(cells):
            errors.append(f"source prototype at ({top},{left}) is not 4-connected")
    return errors, {
        "interior": interior,
        "cells": tuple(sorted(cells)),
        "colors": tuple(sorted(colors)),
        "size": len(cells),
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_shape_errors(grid)
    if errors:
        return {"errors": errors}

    height = len(grid)
    width = len(grid[0])
    if height != GRID_H:
        errors.append(f"expected height {GRID_H}, got {height}")
    if width < 17 or width > 29 or (width + 1) % PITCH != 0:
        errors.append(f"expected width 17, 23, or 29, got {width}")
    if errors:
        return {"errors": errors, "grid_h": height, "grid_w": width}

    n_src = (width + 1) // PITCH
    if not 3 <= n_src <= 5:
        errors.append(f"expected 3..5 source panels, got {n_src}")
    if any(value != 9 for value in grid[DIVIDER_ROW]):
        errors.append("middle divider row must be entirely color 9")

    source_keys: list[int] = []
    prototypes: list[dict[str, Any]] = []
    for index in range(n_src):
        left = index * PITCH
        center = left + FRAME // 2
        key_row = list(grid[0][left : left + FRAME])
        key = key_row[FRAME // 2]
        if any(value != 0 for offset, value in enumerate(key_row) if offset != FRAME // 2):
            errors.append(f"source panel {index} key row has non-center marks")
        if key in STRUCTURAL_COLORS:
            errors.append(f"source panel {index} has invalid key {key}")
        source_keys.append(key)
        frame_errors, prototype = _frame_errors(grid, 1, left, empty=False)
        errors.extend(frame_errors)
        prototypes.append(prototype)
        if index < n_src - 1:
            separator = left + FRAME
            if any(grid[row][separator] != 9 for row in range(0, FRAME + 1)):
                errors.append(f"source separator after panel {index} is not full color 9")

    if len(set(source_keys)) != len(source_keys):
        errors.append("source keys must be pairwise distinct")
    prototype_shapes = [prototype["cells"] for prototype in prototypes]
    if len(set(prototype_shapes)) != len(prototype_shapes):
        errors.append("source prototype binary shapes must be pairwise distinct")
    prototype_colors = [prototype["colors"][0] for prototype in prototypes if len(prototype["colors"]) == 1]
    if len(prototype_colors) == n_src and len(set(prototype_colors)) != n_src:
        errors.append("source prototype colors must be pairwise distinct")
    if len(prototype_colors) == n_src:
        for index, (key, color) in enumerate(zip(source_keys, prototype_colors)):
            if key == color:
                errors.append(f"source panel {index} prototype color equals its key")

    center_values = [grid[TARGET_KEY_ROW][index * PITCH + FRAME // 2] for index in range(n_src)]
    n_tgt = 0
    while n_tgt < n_src and center_values[n_tgt] != 0:
        n_tgt += 1
    if any(value != 0 for value in center_values[n_tgt:]):
        errors.append("target panels must be left-packed")
    if not 2 <= n_tgt <= n_src:
        errors.append(f"expected 2..{n_src} target panels, got {n_tgt}")

    target_keys: list[int] = []
    for index in range(n_tgt):
        left = index * PITCH
        key_row = list(grid[TARGET_KEY_ROW][left : left + FRAME])
        key = key_row[FRAME // 2]
        if any(value != 0 for offset, value in enumerate(key_row) if offset != FRAME // 2):
            errors.append(f"target panel {index} key row has non-center marks")
        if key in STRUCTURAL_COLORS:
            errors.append(f"target panel {index} has invalid key {key}")
        target_keys.append(key)
        frame_errors, _ = _frame_errors(grid, TARGET_FRAME_TOP, left, empty=True)
        errors.extend(frame_errors)
        if index < n_tgt - 1:
            separator = left + FRAME
            if any(grid[row][separator] != 9 for row in range(TARGET_KEY_ROW, GRID_H)):
                errors.append(f"target separator after panel {index} is not full color 9")

    active_width = n_tgt * FRAME + max(0, n_tgt - 1)
    if n_tgt < n_src and any(
        grid[row][col] != 0
        for row in range(TARGET_KEY_ROW, GRID_H)
        for col in range(active_width, width)
    ):
        errors.append("trailing bottom region after the last target must be background")

    missing = sorted(set(target_keys) - set(source_keys))
    if missing:
        errors.append(f"target keys absent from source library: {missing}")
    if target_keys and len(set(target_keys)) < 2:
        errors.append("targets must expose at least two distinct source keys")
    position_mismatch = False
    if not missing and len(set(source_keys)) == len(source_keys):
        position_mismatch = _has_position_mismatch(target_keys, source_keys)
        if target_keys and not position_mismatch:
            errors.append("target order admits fixed-position copying")

    target_repeats = len(set(target_keys)) < len(target_keys) if target_keys else False
    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "n_src": n_src,
        "n_tgt": n_tgt,
        "target_repeats": target_repeats,
        "source_keys": source_keys,
        "target_keys": target_keys,
        "prototype_colors": prototype_colors,
        "prototype_shapes": prototype_shapes,
        "prototype_sizes": [prototype["size"] for prototype in prototypes],
        "position_mismatch": position_mismatch,
        "has_trailing_blank": n_tgt < n_src,
        "full_target_row": n_tgt == n_src,
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Recover exact axes and linked semantic facts from a returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {key: value for key, value in analysis.items() if key != "errors"}


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, shortcut-friendly, or rule-hiding scenes."""
    del difficulty
    errors = list(_analyze(grid)["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for key in AXES:
            if key in meta:
                requested[key] = meta[key]
    if requested:
        observed = observe_overrides(grid)
        for key, value in requested.items():
            if key in observed and value is not None and observed[key] != value:
                errors.append(f"{key} requested {value!r}, observed {observed[key]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] for the exact public morphology plus lawful shape variation."""
    facts = _analyze(grid)
    if facts["errors"]:
        return list(facts["errors"])
    reasons: list[str] = []
    if facts["grid_w"] != 17 or facts["n_src"] != 3:
        reasons.append("canonical canvas has three 5x5 source panels (13x17 input)")
    if facts["n_tgt"] not in (2, 3):
        reasons.append("canonical target row has two or three active frames")
    if set(facts["source_keys"]) != {1, 2, 3}:
        reasons.append("canonical source key set is {1,2,3}")
    if set(facts["prototype_colors"]) != {4, 7, 8}:
        reasons.append("canonical prototype color set is {4,7,8}")
    if sorted(facts["prototype_sizes"]) != [4, 5, 5]:
        reasons.append("canonical prototype cell-count multiset is [4,5,5]")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python diagnostic mirror; canonical Racket remains authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))

    mapping: dict[int, list[list[int]]] = {}
    for index, key in enumerate(facts["source_keys"]):
        left = index * PITCH
        mapping[key] = [
            list(grid[row][left + 1 : left + FRAME - 1])
            for row in range(2, 5)
        ]

    output = full_grid(FRAME, facts["grid_w"], 0)
    for index, key in enumerate(facts["target_keys"]):
        left = index * PITCH
        _draw_frame(output, 0, left)
        interior = mapping[key]
        for row in range(3):
            for col in range(3):
                if interior[row][col] != 0:
                    output[1 + row][left + 1 + col] = interior[row][col]
        if index < facts["n_tgt"] - 1:
            separator = left + FRAME
            for row in range(FRAME):
                output[row][separator] = 9
    return output


def _competitor_output(grid: list[list[int]], mode: str) -> list[list[int]]:
    facts = semantic_observables(grid)
    mapping_by_key: dict[int, list[list[int]]] = {}
    source_interiors: list[list[list[int]]] = []
    for index, key in enumerate(facts["source_keys"]):
        left = index * PITCH
        interior = [list(grid[row][left + 1 : left + 4]) for row in range(2, 5)]
        source_interiors.append(interior)
        mapping_by_key[key] = interior

    output = full_grid(FRAME, facts["grid_w"], 0)
    for index, key in enumerate(facts["target_keys"]):
        left = index * PITCH
        _draw_frame(output, 0, left)
        if mode == "fixed_position":
            interior = source_interiors[index % len(source_interiors)]
        elif mode == "reverse_position":
            interior = source_interiors[-1 - (index % len(source_interiors))]
        elif mode == "first_prototype":
            interior = source_interiors[0]
        elif mode == "key_as_answer":
            interior = [[0, 0, 0], [0, key, 0], [0, 0, 0]]
        elif mode == "modal_color_echo":
            proto = mapping_by_key[key]
            color = next(value for row in proto for value in row if value != 0)
            interior = [[color] * 3 for _ in range(3)]
        else:
            raise ValueError(f"unknown competitor mode {mode}")
        for row in range(3):
            for col in range(3):
                if interior[row][col] != 0:
                    output[1 + row][left + 1 + col] = interior[row][col]
        if index < facts["n_tgt"] - 1:
            separator = left + FRAME
            for row in range(FRAME):
                output[row][separator] = 9
    return output


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut survives but changes query output."""
    modes = (
        "fixed_position",
        "reverse_position",
        "first_prototype",
        "key_as_answer",
        "modal_color_echo",
    )
    reasons: list[str] = []
    rows = list(demos) + [query]
    for index, pair in enumerate(rows):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is not a lawful keyed-library scene: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output disagrees with the keyed-library rule mirror")
    if reasons:
        return sorted(set(reasons))

    query_truth = query["output"]
    for mode in modes:
        if all(_competitor_output(pair["input"], mode) == pair["output"] for pair in demos):
            if _competitor_output(query["input"], mode) != query_truth:
                reasons.append(
                    f"competing rule '{mode}' matches every demonstration but changes the query answer"
                )
    return reasons


def _witness_partial(grid) -> bool:
    return semantic_observables(grid)["has_trailing_blank"]


def _witness_full(grid) -> bool:
    return semantic_observables(grid)["full_target_row"]


def _witness_repeated(grid) -> bool:
    return semantic_observables(grid)["target_repeats"]


def _witness_unique(grid) -> bool:
    return not semantic_observables(grid)["target_repeats"]


def _witness_position_mismatch(grid) -> bool:
    return semantic_observables(grid)["position_mismatch"]


SEMANTIC_WITNESSES = {
    "partial_target_row": _witness_partial,
    "full_target_row": _witness_full,
    "repeated_target_key": _witness_repeated,
    "unique_target_keys": _witness_unique,
    "target_source_position_mismatch": _witness_position_mismatch,
}
