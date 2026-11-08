"""Generator for task 94549757a7f3 — cap horizontal green runs on the right.

Every horizontal color-3 component whose immediate right neighbour is an
in-bounds zero receives one color-2 cell there.  The teaching distribution also
contains explicit non-target controls: horizontal objects of another color,
vertical green objects, green runs at the right edge, and green runs blocked by
a nonzero cell.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94549757a7f3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a56ad928ddca"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "A zero-background grid contains two or three separated horizontal green "
    "(color-3) runs. Append exactly one red (color-2) cell immediately to the "
    "right of each run when that cell is in bounds and zero. Do not alter "
    "horizontal non-green runs, vertical green objects, green runs ending at "
    "the right edge, or green runs whose right neighbour is occupied."
)

INVARIANTS = [
    "the input palette is a subset of {0,3,8}; red 2 is output-only",
    "there are 2-3 horizontal green target runs with an empty in-bounds right cell",
    "target runs have lengths 2-4 and are separate 4-connected components",
    "any distractor has one of four explicit skip reasons: wrong color, vertical, right edge, or occupied right",
    "the output preserves the input and adds one red cell at every target right end",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_LENGTH_PROFILES = ("all_2", "all_3", "all_4", "canonical_mix")
_DISTRACTOR_MODES = ("mixed", "right_edge", "occupied_right", "none", "vertical")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-keyed 6..10",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-keyed 7..14",
        "valid": "7..14",
    },
    "n_targets": {
        "type": "int",
        "default": "balanced 2|3 schedule",
        "valid": "2..3",
    },
    "length_profile": {
        "type": "str",
        "default": "balanced schedule",
        "valid": "|".join(_LENGTH_PROFILES),
    },
    "distractor_mode": {
        "type": "str",
        "default": "five-step semantic schedule",
        "valid": "|".join(_DISTRACTOR_MODES),
    },
}

# A canonical-mix scene is defined as three target lengths [2,2,3].
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_targets": 2, "length_profile": "canonical_mix"},
]

Cell = tuple[int, int]

# Every five consecutive sample indices contain all decisive controls.  The
# canonical-like slot is deliberately included in every window as well.
_SCHEDULE = (
    {"n_targets": 2, "length_profile": "all_2", "distractor_mode": "mixed"},
    {"n_targets": 3, "length_profile": "all_3", "distractor_mode": "right_edge"},
    {"n_targets": 2, "length_profile": "all_4", "distractor_mode": "occupied_right"},
    {"n_targets": 3, "length_profile": "canonical_mix", "distractor_mode": "none"},
    {"n_targets": 2, "length_profile": "all_3", "distractor_mode": "vertical"},
)

_CANONICAL_DIMS = ((7, 7), (6, 8), (7, 9))
_GENERAL_DIMS = {
    "easy": ((6, 9), (7, 10), (8, 11)),
    "medium": ((7, 10), (8, 12), (9, 13)),
    "hard": ((8, 12), (9, 13), (10, 14)),
    None: ((6, 9), (7, 10), (8, 12), (9, 13), (10, 14)),
}


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


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def _draw_int_axis(ctx, overrides: dict[str, Any], label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: tuple[str, ...],
) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[Cell] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            out.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "r0": min(rows),
                    "r1": max(rows),
                    "c0": min(cols),
                    "c1": max(cols),
                }
            )
    return out


def _contiguous_row(component: dict[str, Any]) -> bool:
    return (
        component["r0"] == component["r1"]
        and len(component["cells"]) == component["c1"] - component["c0"] + 1
    )


def _contiguous_col(component: dict[str, Any]) -> bool:
    return (
        component["c0"] == component["c1"]
        and len(component["cells"]) == component["r1"] - component["r0"] + 1
    )


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "targets": [],
        "vertical": [],
        "right_edge": [],
        "occupied_right": [],
        "wrong_color": [],
        "blockers": [],
        "distractor_mode": None,
        "output": None,
    }
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts["height"], facts["width"] = h, w
    if not 6 <= h <= 10:
        errors.append(f"grid height must be 6..10, got {h}")
    if not 7 <= w <= 14:
        errors.append(f"grid width must be 7..14, got {w}")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 3, 8}:
        errors.append(f"input palette must be a subset of {{0,3,8}}, got {sorted(palette)}")
    if errors:
        return facts

    components = _components(grid)
    green_components: list[dict[str, Any]] = []
    color8_components: list[dict[str, Any]] = []
    for component in components:
        if component["color"] == 3:
            green_components.append(component)
        elif component["color"] == 8:
            color8_components.append(component)
        else:
            errors.append(f"unexpected foreground color {component['color']}")

    occupied_blocker_cells: set[Cell] = set()
    for component in green_components:
        if _contiguous_row(component):
            length = len(component["cells"])
            if not 2 <= length <= 4:
                errors.append(f"horizontal green run length must be 2..4, got {length}")
                continue
            row, right = component["r0"], component["c1"] + 1
            component["length"] = length
            component["right"] = (row, right)
            if right >= w:
                facts["right_edge"].append(component)
            elif grid[row][right] == 0:
                facts["targets"].append(component)
            elif grid[row][right] == 8:
                facts["occupied_right"].append(component)
                occupied_blocker_cells.add((row, right))
            else:
                errors.append(
                    f"horizontal green run at row {row} has unsupported right neighbour {grid[row][right]}"
                )
        elif _contiguous_col(component):
            length = len(component["cells"])
            if not 2 <= length <= 4:
                errors.append(f"vertical green run length must be 2..4, got {length}")
            else:
                component["length"] = length
                facts["vertical"].append(component)
        else:
            errors.append(f"green component is neither a straight row nor a straight column: {component['cells']}")

    for component in color8_components:
        if not _contiguous_row(component) or not 1 <= len(component["cells"]) <= 4:
            errors.append(f"color-8 component must be a horizontal run of length 1..4: {component['cells']}")
            continue
        cells = set(component["cells"])
        matched = cells & occupied_blocker_cells
        if matched:
            if cells != matched or len(cells) != 1:
                errors.append("an occupied-right blocker must be one singleton color-8 cell")
            else:
                facts["blockers"].append(component)
        else:
            facts["wrong_color"].append(component)

    if len(facts["targets"]) not in (2, 3):
        errors.append(f"expected 2 or 3 target runs, got {len(facts['targets'])}")
    if len(facts["vertical"]) > 1:
        errors.append("at most one vertical green distractor is allowed")
    if len(facts["right_edge"]) > 1:
        errors.append("at most one right-edge green distractor is allowed")
    if len(facts["occupied_right"]) > 1 or len(facts["blockers"]) > 1:
        errors.append("at most one occupied-right green distractor and blocker are allowed")
    if len(facts["occupied_right"]) != len(facts["blockers"]):
        errors.append("occupied-right green distractor and color-8 blocker counts disagree")
    if len(facts["wrong_color"]) > 1:
        errors.append("at most one wrong-color distractor is allowed")

    branch_counts = (
        len(facts["vertical"]),
        len(facts["right_edge"]),
        len(facts["occupied_right"]),
        len(facts["wrong_color"]),
    )
    mode_by_counts = {
        (1, 0, 0, 1): "mixed",
        (0, 1, 0, 0): "right_edge",
        (0, 0, 1, 0): "occupied_right",
        (0, 0, 0, 0): "none",
        (1, 0, 0, 0): "vertical",
    }
    mode = mode_by_counts.get(branch_counts)
    if mode is None:
        errors.append(f"unsupported distractor combination {branch_counts}")
    facts["distractor_mode"] = mode

    output = deepcopy(grid)
    for target in facts["targets"]:
        row, col = target["right"]
        output[row][col] = 2
    facts["output"] = output
    if output == grid:
        errors.append("the right-cap transformation is an identity")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful teaching grammar, including skip controls."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def _length_profile(lengths: Iterable[int]) -> str | None:
    values = tuple(sorted(int(value) for value in lengths))
    if values and len(set(values)) == 1 and values[0] in (2, 3, 4):
        return f"all_{values[0]}"
    if values == (2, 2, 3):
        return "canonical_mix"
    return None


def observe_overrides(grid) -> dict[str, int | str]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    profile = _length_profile(target["length"] for target in facts["targets"])
    if profile is None:
        raise ValueError("target lengths do not identify one declared length_profile")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_targets": len(facts["targets"]),
        "length_profile": profile,
        "distractor_mode": facts["distractor_mode"],
    }


def _canonical_linked_signature(facts: dict[str, Any]) -> tuple[Any, ...]:
    return (
        facts["height"],
        facts["width"],
        len(facts["targets"]),
        tuple(sorted(target["length"] for target in facts["targets"])),
        facts["distractor_mode"],
    )


_CANONICAL_LINKED_SIGNATURES = {
    (7, 7, 3, (2, 2, 3), "none"),
    (6, 8, 3, (2, 2, 3), "none"),
    (7, 9, 3, (2, 2, 3), "none"),
}


def strict_canonical_like(grid) -> list[str]:
    facts = _analyze(grid)
    if facts["errors"]:
        return list(facts["errors"])
    signature = _canonical_linked_signature(facts)
    if signature not in _CANONICAL_LINKED_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return []


def canonical_profile_signature(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return None
    return _canonical_linked_signature(facts)


def semantic_signature(grid) -> dict[str, Any]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "height": facts["height"],
        "width": facts["width"],
        "target_count": len(facts["targets"]),
        "target_lengths": tuple(sorted(target["length"] for target in facts["targets"])),
        "target_columns": tuple(sorted(target["c0"] for target in facts["targets"])),
        "distractor_mode": facts["distractor_mode"],
        "vertical_count": len(facts["vertical"]),
        "right_edge_count": len(facts["right_edge"]),
        "occupied_right_count": len(facts["occupied_right"]),
        "wrong_color_count": len(facts["wrong_color"]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _profile_lengths(profile: str, n_targets: int) -> tuple[int, ...]:
    if profile == "canonical_mix":
        if n_targets != 3:
            raise ValueError(
                "incompatible overrides n_targets/length_profile: canonical_mix requires n_targets=3"
            )
        return (2, 2, 3)
    if profile in ("all_2", "all_3", "all_4"):
        return (int(profile[-1]),) * n_targets
    raise ValueError(f"unknown length_profile {profile!r}")


def _default_dimensions(seed: int, sample_index: int, difficulty: str | None, slot: int) -> tuple[int, int]:
    if slot in (1, 3, 4):
        return _CANONICAL_DIMS[(sample_index // 5 + int(seed) + slot) % len(_CANONICAL_DIMS)]
    options = _GENERAL_DIMS[difficulty]
    return options[(sample_index + int(seed)) % len(options)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    slot = int(sample_index) % len(_SCHEDULE)
    scheduled = dict(_SCHEDULE[slot])
    # Single-axis overrides remain independently realizable.  Only the explicit
    # pair n_targets=2 + canonical_mix is incompatible.
    requested_n = overrides.get("n_targets")
    requested_profile = overrides.get("length_profile")
    if requested_profile == "canonical_mix" and requested_n is None:
        scheduled["n_targets"] = 3
    if requested_n == 2 and requested_profile is None and scheduled["length_profile"] == "canonical_mix":
        scheduled["length_profile"] = "all_2"
    default_h, default_w = _default_dimensions(int(seed), int(sample_index), difficulty, slot)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_int_axis(ctx, overrides, "grid_h", default_h, 6, 10)
    w = _draw_int_axis(ctx, overrides, "grid_w", default_w, 7, 14)
    n_targets = _draw_int_axis(ctx, overrides, "n_targets", scheduled["n_targets"], 2, 3)
    length_profile = _draw_choice_axis(
        ctx,
        overrides,
        "length_profile",
        scheduled["length_profile"],
        _LENGTH_PROFILES,
    )
    distractor_mode = _draw_choice_axis(
        ctx,
        overrides,
        "distractor_mode",
        scheduled["distractor_mode"],
        _DISTRACTOR_MODES,
    )
    lengths = _profile_lengths(length_profile, n_targets)

    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    row_offset = rng.randint(0, h - 6)
    target_rows = [row_offset, row_offset + 2, row_offset + 4][:n_targets]

    for index, (row, length) in enumerate(zip(target_rows, lengths)):
        max_start = w - length - 1
        if row == row_offset + 4:
            if distractor_mode in ("vertical", "mixed"):
                max_start = min(max_start, w - length - 3)
            elif distractor_mode == "right_edge":
                max_start = min(max_start, w - length - 2)
            elif distractor_mode == "occupied_right":
                max_start = min(max_start, w - length - 3)
        if max_start < 0:
            raise ValueError(
                "incompatible overrides grid_w/length_profile/distractor_mode: target does not fit"
            )
        start = rng.randint(0, max_start)
        # A small deterministic offset avoids repeated fixed columns when room exists.
        if max_start > 0:
            start = (start + index + int(seed)) % (max_start + 1)
        for col in range(start, start + length):
            grid[row][col] = 3

    if distractor_mode in ("vertical", "mixed"):
        # Keep one empty column to the right so an orientation-blind rival
        # would visibly add red caps to the two vertical cells.
        grid[row_offset + 4][w - 2] = 3
        grid[row_offset + 5][w - 2] = 3
    if distractor_mode == "right_edge":
        grid[row_offset + 5][w - 2] = 3
        grid[row_offset + 5][w - 1] = 3
    if distractor_mode == "occupied_right":
        grid[row_offset + 5][w - 3] = 3
        grid[row_offset + 5][w - 2] = 3
        grid[row_offset + 5][w - 1] = 8
    if distractor_mode == "mixed":
        wrong_start = rng.randint(0, w - 3)
        grid[row_offset + 1][wrong_start] = 8
        grid[row_offset + 1][wrong_start + 1] = 8

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator emitted invalid grid: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_targets": n_targets,
        "length_profile": length_profile,
        "distractor_mode": distractor_mode,
    }
    if observed != expected:
        raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
    return grid


def rule_mirror(grid):
    """Diagnostic Python mirror of the Racket authority; never output authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return deepcopy(facts["output"])


def _apply_to_components(
    grid: list[list[int]],
    predicate: Callable[[dict[str, Any]], bool],
    *, overwrite: bool = False,
    wrap: bool = False,
) -> list[list[int]]:
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for component in _components(grid):
        if not predicate(component) or not _contiguous_row(component):
            continue
        row, col = component["r0"], component["c1"] + 1
        if col >= w:
            if wrap:
                out[row][0] = 2
            continue
        if overwrite or grid[row][col] == 0:
            out[row][col] = 2
    return out


def _color_blind_horizontal(grid):
    return _apply_to_components(grid, lambda component: component["color"] != 0)


def _green_rows_not_objects(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for row in range(h):
        cols = [col for col in range(w) if grid[row][col] == 3]
        if cols and max(cols) + 1 < w and grid[row][max(cols) + 1] == 0:
            out[row][max(cols) + 1] = 2
    return out


def _overwrite_blocked(grid):
    return _apply_to_components(
        grid,
        lambda component: component["color"] == 3,
        overwrite=True,
    )


def _wrap_right_edge(grid):
    return _apply_to_components(
        grid,
        lambda component: component["color"] == 3,
        wrap=True,
    )


def _only_lengths(*allowed: int):
    allowed_set = set(allowed)

    def competitor(grid):
        return _apply_to_components(
            grid,
            lambda component: component["color"] == 3 and len(component["cells"]) in allowed_set,
        )

    return competitor


def _first_target_only(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    out = deepcopy(grid)
    first = min(facts["targets"], key=lambda target: (target["r0"], target["c0"]))
    row, col = first["right"]
    out[row][col] = 2
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_target_only": _first_target_only,
    "skip_length_2": _only_lengths(3, 4),
    "skip_length_3": _only_lengths(2, 4),
    "skip_length_4": _only_lengths(2, 3),
    "color_blind_horizontal": _color_blind_horizontal,
    "green_rows_not_objects": _green_rows_not_objects,
    "overwrite_blocked": _overwrite_blocked,
    "wrap_right_edge": _wrap_right_edge,
}


_LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "leave the input unchanged": lambda grid: deepcopy(grid),
    "cap every horizontal object regardless of color": _color_blind_horizontal,
    "cap the rightmost green cell in every occupied row": _green_rows_not_objects,
    "overwrite a nonzero right neighbour": _overwrite_blocked,
    "wrap right-edge caps to column zero": _wrap_right_edge,
    "cap only length-2 or length-3 runs": _only_lengths(2, 3),
    "cap only the first target": _first_target_only,
}


def _pair_analysis(pair, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    facts = _analyze(pair["input"])
    if facts["errors"]:
        return None, [f"{label}: {error}" for error in facts["errors"]]
    if pair["output"] != facts["output"]:
        return None, [f"{label} output is not the horizontal-green right-cap result"]
    return facts, []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits every demo but changes the query."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    analyses: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, pair in enumerate(demos):
        facts, pair_errors = _pair_analysis(pair, f"demo {index}")
        reasons.extend(pair_errors)
        if facts is not None:
            analyses.append((pair, facts))
    _query_facts, query_errors = _pair_analysis(query, "query")
    reasons.extend(query_errors)
    if reasons:
        return reasons

    modes = {facts["distractor_mode"] for _pair, facts in analyses}
    profiles = {
        _length_profile(target["length"] for target in facts["targets"])
        for _pair, facts in analyses
    }
    required_modes = {"mixed", "right_edge", "occupied_right", "none", "vertical"}
    if modes != required_modes:
        reasons.append(f"demonstrations miss scheduled distractor controls: {sorted(required_modes - modes)}")
    if "all_4" not in profiles:
        reasons.append("no demonstration requires capping a length-4 target run")
    if "canonical_mix" not in profiles:
        reasons.append("no demonstration shows mixed target lengths in one scene")

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair, _facts in analyses)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"competing rule '{name}' fits every demo but changes the query answer")
    return reasons


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid):
        facts = _analyze(grid)
        return not facts["errors"] and bool(predicate(facts))

    return wrapped


SEMANTIC_WITNESSES = {
    "multiple_targets": _witness(lambda facts: len(facts["targets"]) >= 2),
    "length_2_targets": _witness(
        lambda facts: any(target["length"] == 2 for target in facts["targets"])
    ),
    "length_3_targets": _witness(
        lambda facts: any(target["length"] == 3 for target in facts["targets"])
    ),
    "length_4_targets": _witness(
        lambda facts: any(target["length"] == 4 for target in facts["targets"])
    ),
    "wrong_color_distractor": _witness(lambda facts: bool(facts["wrong_color"])),
    "vertical_green_distractor": _witness(lambda facts: bool(facts["vertical"])),
    "right_edge_green_distractor": _witness(lambda facts: bool(facts["right_edge"])),
    "occupied_right_green_distractor": _witness(lambda facts: bool(facts["occupied_right"])),
    "canonical_linked_profile": _witness(
        lambda facts: _canonical_linked_signature(facts) in _CANONICAL_LINKED_SIGNATURES
    ),
}

WITNESS_RIVALS = {
    "multiple_targets": ["first_target_only"],
    "length_2_targets": ["skip_length_2"],
    "length_3_targets": ["skip_length_3"],
    "length_4_targets": ["skip_length_4"],
    "wrong_color_distractor": ["color_blind_horizontal"],
    "vertical_green_distractor": ["green_rows_not_objects"],
    "right_edge_green_distractor": ["wrap_right_edge"],
    "occupied_right_green_distractor": ["overwrite_blocked"],
    "canonical_linked_profile": ["first_target_only", "skip_length_3"],
}
