#!/usr/bin/env python3
"""Deterministic two-stage parametric family for ARC task ``dfc3ce537883``.

Every input uses the canonical full-height color-9 divider grammar.  The
canonical setting mirrors all non-background source cells.  The alternate
setting performs that same mirror first, then uses the newly mirrored color-2
probe to select one right-side hollow frame and fills its bounding box with a
color derived from frame perimeter size.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "dfc3ce537883"
ALLOWED_FOLLOWUPS = ("mirror_only", "fill_contacted_frame")
DEFAULT_FOLLOWUP = "mirror_only"
ALTERNATE_FOLLOWUP = "fill_contacted_frame"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.1.0"

_HOME = Path(__file__).resolve().parent
_RULES = _HOME / "rules"
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Each episode uses up to six demonstrations followed by exactly four queries.
# Dimensions are deliberately all distinct, and the last query is the required
# substantive 30x30 stress surface.
_DEMO_PROFILES = (
    ((11, 17), 3, 3, "top", 4),
    ((13, 19), 4, 4, "bottom", 3),
    ((15, 21), 3, 4, "bottom", 3),
    ((17, 23), 4, 4, "top", 3),
    ((19, 25), 3, 3, "bottom", 4),
    ((21, 27), 4, 4, "bottom", 3),
)
_QUERY_PROFILES = (
    ((12, 18), 3, 3, "top", 4),
    ((18, 24), 4, 4, "bottom", 3),
    ((24, 28), 4, 3, "top", 4),
    ((30, 30), 3, 4, "bottom", 3),
)


def _validate_followup(value: str) -> None:
    if type(value) is not str or value not in ALLOWED_FOLLOWUPS:
        raise ValueError(f"followup must be one of {ALLOWED_FOLLOWUPS}, got {value!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1; bool is forbidden")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6; bool is forbidden")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4; bool is forbidden")


def _validate_settings(settings: dict[str, Any] | None) -> str:
    if settings is None:
        return DEFAULT_FOLLOWUP
    if type(settings) is not dict or set(settings) != {"followup"}:
        raise ValueError("settings must contain exactly {'followup'}")
    value = settings["followup"]
    _validate_followup(value)
    return value


def _read_rule(name: str) -> str:
    path = _RULES / f"{name}.rkt"
    source = path.read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty Racket rule: {path}")
    return source


def program_for(followup: str = DEFAULT_FOLLOWUP) -> str:
    """Return exact, episode-fixed Racket source for one declared setting."""
    _validate_followup(followup)
    return _read_rule(followup)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must be at most 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors 0..9")
    return len(grid), width


def divider_column(grid: list[list[int]]) -> int:
    """Return the unique full-height color-9 divider column."""
    height, width = _validate_grid(grid)
    hits = [col for col in range(width) if all(grid[row][col] == 9 for row in range(height))]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one full-height color-9 divider, found {hits}")
    return hits[0]


def mirror_python(grid: list[list[int]]) -> list[list[int]]:
    """Faithfully mirror the canonical program's left-side colored cells."""
    height, width = _validate_grid(grid)
    divider = divider_column(grid)
    result = deepcopy(grid)
    for row in range(height):
        for col in range(divider):
            value = grid[row][col]
            mirror_col = 2 * divider - col
            if value not in (0, 9) and 0 <= mirror_col < width:
                result[row][mirror_col] = value
    return result


def _candidate_info(mirrored: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(mirrored)
    touching: list[tuple[int, list[tuple[int, int]]]] = []
    for color in (3, 4):
        cells = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if mirrored[row][col] == color
        ]
        if cells and any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and mirrored[row + dr][col + dc] == 2
            for row, col in cells
            for dr, dc in _CARDINAL
        ):
            touching.append((color, cells))
    if len(touching) != 1:
        raise ValueError(f"expected exactly one color-3/4 frame contacted by mirrored color 2, found {len(touching)}")
    color, cells = touching[0]
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    count = len(cells)
    if count not in (8, 12):
        raise ValueError(f"contacted candidate must be a 3x3 or 4x4 hollow frame, found {count} cells")
    bbox = [min(rows), min(cols), max(rows), max(cols)]
    expected_side = 3 if count == 8 else 4
    if bbox[2] - bbox[0] + 1 != expected_side or bbox[3] - bbox[1] + 1 != expected_side:
        raise ValueError("contacted candidate cells do not form the expected square-frame bounding box")
    return {
        "candidate_color": color,
        "candidate_cells": count,
        "bbox": bbox,
        "fill_color": 1 if count == 8 else 5,
    }


def inspect_contact(grid: list[list[int]]) -> dict[str, Any]:
    """Expose the A→intermediate boundary for tests and causal evidence."""
    return _candidate_info(mirror_python(grid))


def apply_from_intermediate(
    mirrored: list[list[int]], intermediate: dict[str, Any]
) -> list[list[int]]:
    """Apply step B to a mirrored grid using an explicit selected-frame record."""
    height, width = _validate_grid(mirrored)
    if type(intermediate) is not dict:
        raise ValueError("intermediate must be an object")
    bbox = intermediate.get("bbox")
    fill = intermediate.get("fill_color")
    if (
        type(bbox) is not list
        or len(bbox) != 4
        or any(type(value) is not int for value in bbox)
        or type(fill) is not int
        or not 0 <= fill <= 9
    ):
        raise ValueError("intermediate needs integer bbox[4] and fill_color")
    r0, c0, r1, c1 = bbox
    if not (0 <= r0 <= r1 < height and 0 <= c0 <= c1 < width):
        raise ValueError("intermediate bbox lies outside the grid")
    result = deepcopy(mirrored)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            result[row][col] = fill
    return result


def apply_python(grid: list[list[int]], settings: dict[str, Any] | None = None) -> list[list[int]]:
    """Reference semantics used only to construct labels before Racket replay."""
    followup = _validate_settings(settings)
    mirrored = mirror_python(grid)
    if followup == DEFAULT_FOLLOWUP:
        return mirrored
    return apply_from_intermediate(mirrored, _candidate_info(mirrored))


def _draw_hollow_frame(
    grid: list[list[int]], row0: int, col0: int, side: int, color: int
) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for dr in range(side):
        for dc in range(side):
            if dr in (0, side - 1) or dc in (0, side - 1):
                row, col = row0 + dr, col0 + dc
                if grid[row][col] != 0:
                    raise AssertionError("frame placement collision")
                grid[row][col] = color
                cells.add((row, col))
    return cells


def _rectangle_cells(row0: int, col0: int, side: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(row0, row0 + side)
        for col in range(col0, col0 + side)
    }


def _build_scene(
    seed: int,
    ordinal: int,
    profile: tuple[tuple[int, int], int, int, str, int],
) -> list[list[int]]:
    (height, width), target_color, target_side, target_location, distractor_side = profile
    divider = width // 2
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        grid[row][divider] = 9

    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{ordinal}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    max_side = max(target_side, distractor_side)
    base_col = divider + 3
    max_shift = max(0, min(2, width - max_side - base_col))
    frame_col = base_col + (digest[8] % (max_shift + 1))

    if target_location == "top":
        target_row = 1
        distractor_row = height - distractor_side - 1
    elif target_location == "bottom":
        target_row = height - target_side - 1
        distractor_row = 1
    else:
        raise AssertionError(f"unknown target location {target_location!r}")
    if target_row + target_side >= distractor_row and distractor_row + distractor_side >= target_row:
        raise AssertionError("candidate frames overlap vertically")

    distractor_color = 4 if target_color == 3 else 3
    _draw_hollow_frame(grid, target_row, frame_col, target_side, target_color)
    _draw_hollow_frame(grid, distractor_row, frame_col, distractor_side, distractor_color)

    # Step A creates this two-cell probe exactly one column left of the target.
    mirror_col = frame_col - 1
    source_col = 2 * divider - mirror_col
    probe_rows = (target_row + 1, target_row + target_side - 1)
    if not 0 <= source_col < divider:
        raise AssertionError("probe source does not fit left of divider")
    for row in probe_rows:
        if grid[row][source_col] != 0 or grid[row][mirror_col] != 0:
            raise AssertionError("probe placement collision")
        grid[row][source_col] = 2

    forbidden_right = _rectangle_cells(target_row, frame_col, target_side)
    forbidden_right |= _rectangle_cells(distractor_row, frame_col, distractor_side)
    forbidden_right |= {(row, mirror_col) for row in probe_rows}

    # Additional colors make the canonical mirror lesson substantive.  Their
    # destinations span the right side but never intrude into either frame.
    desired = min(18, max(5, (height * width) // 45))
    pool = [
        (row, col)
        for row in range(height)
        for col in range(divider)
        if grid[row][col] == 0
        and 0 <= 2 * divider - col < width
        and (row, 2 * divider - col) not in forbidden_right
    ]
    rng.shuffle(pool)
    chosen = pool[:desired]
    if len(chosen) != desired:
        raise AssertionError("not enough collision-free decoy cells")
    for index, (row, col) in enumerate(chosen):
        grid[row][col] = (6, 7, 8)[(index + digest[9]) % 3]

    # Assertions here are production safeguards: they detect any future scene
    # profile that silently stops expressing the intended dependency.
    info = inspect_contact(grid)
    if info["candidate_color"] != target_color or info["candidate_cells"] != 4 * target_side - 4:
        raise AssertionError(f"scene contact metadata disagrees with profile: {info}")
    return grid


def _sample_inputs(seed: int, demos: int, queries: int) -> list[list[list[int]]]:
    inputs = [
        _build_scene(seed, index, _DEMO_PROFILES[index])
        for index in range(demos)
    ]
    inputs.extend(
        _build_scene(seed, demos + index, _QUERY_PROFILES[index])
        for index in range(queries)
    )
    serialized = [repr(grid) for grid in inputs]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("parametric sampler emitted duplicate inputs")
    return inputs


def make_episode(
    seed: int,
    *,
    followup: str = DEFAULT_FOLLOWUP,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict[str, Any]:
    """Build one matched-input episode with labels for one fixed setting."""
    _validate_seed(seed)
    _validate_followup(followup)
    _validate_counts(demos, queries)
    settings = {"followup": followup}
    inputs = _sample_inputs(seed, demos, queries)
    pairs = [
        {"input": deepcopy(grid), "output": apply_python(grid, settings)}
        for grid in inputs
    ]
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": settings,
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program": program_for(followup),
    }


def surviving_followups(pairs: list[dict[str, Any]]) -> list[str]:
    """Return declared settings whose Python semantics fit all visible pairs."""
    if type(pairs) is not list or not pairs:
        raise ValueError("pairs must be a nonempty list")
    survivors: list[str] = []
    for followup in ALLOWED_FOLLOWUPS:
        settings = {"followup": followup}
        fits = True
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            if apply_python(pair["input"], settings) != pair["output"]:
                fits = False
                break
        if fits:
            survivors.append(followup)
    return survivors


def audit_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Summarize count, uniqueness, and large-canvas content for review evidence."""
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train and test lists")
    pairs = train + test
    inputs = [pair["input"] for pair in pairs]
    serialized = [repr(grid) for grid in inputs]
    query_shapes = [[len(pair["input"]), len(pair["input"][0])] for pair in test]
    large = test[-1]["input"]
    height, width = _validate_grid(large)
    divider = divider_column(large)
    content = [
        (row, col, large[row][col])
        for row in range(height)
        for col in range(width)
        if col != divider and large[row][col] != 0
    ]
    if not content:
        raise ValueError("large query has no non-divider content")
    return {
        "query_shapes": query_shapes,
        "all_inputs_distinct": len(serialized) == len(set(serialized)),
        "large_query": {
            "shape": [height, width],
            "content_bbox": [
                min(row for row, _, _ in content),
                min(col for _, col, _ in content),
                max(row for row, _, _ in content),
                max(col for _, col, _ in content),
            ],
            "content_cells": len(content),
            "left_content_cells": sum(col < divider for _, col, _ in content),
            "right_content_cells": sum(col > divider for _, col, _ in content),
            "palette": sorted({value for _, _, value in content}),
        },
    }


def _frame_info_for_color(mirrored: list[list[int]], color: int) -> dict[str, Any]:
    height, width = _validate_grid(mirrored)
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if mirrored[row][col] == color
    ]
    if not cells:
        raise ValueError(f"no candidate cells for color {color}")
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    count = len(cells)
    if count not in (8, 12):
        raise ValueError(f"candidate color {color} has unsupported perimeter size {count}")
    return {
        "candidate_color": color,
        "candidate_cells": count,
        "bbox": [min(rows), min(cols), max(rows), max(cols)],
        "fill_color": 1 if count == 8 else 5,
    }


def counterfactual_program() -> str:
    """Return the source-bound wrong-intermediate Racket ablation."""
    return _read_rule("fill_wrong_frame")


def build_dependency_case(grid: list[list[int]]) -> dict[str, Any]:
    """Build one private wrong-intermediate witness case from a lawful input."""
    mirrored = mirror_python(grid)
    actual = _candidate_info(mirrored)
    wrong_color = 4 if actual["candidate_color"] == 3 else 3
    wrong = _frame_info_for_color(mirrored, wrong_color)
    output = apply_from_intermediate(mirrored, actual)
    counterfactual_output = apply_from_intermediate(mirrored, wrong)
    if output == counterfactual_output:
        raise AssertionError("wrong-intermediate ablation did not change the final output")
    return {
        "input": deepcopy(grid),
        "settings": {"followup": ALTERNATE_FOLLOWUP},
        "intermediate_value": deepcopy(actual),
        "program": program_for(ALTERNATE_FOLLOWUP),
        "output": output,
        "counterfactual_program": counterfactual_program(),
        "counterfactual_output": counterfactual_output,
        "ablation": "wrong_intermediate",
    }


PLAUSIBLE_SHORTCUTS = ("constant_fill_1", "fixed_color_3", "fixed_color_4")


def apply_shortcut_python(grid: list[list[int]], shortcut: str) -> list[list[int]]:
    """Execute one explicit wrong rule used by the bounded learnability audit."""
    if shortcut not in PLAUSIBLE_SHORTCUTS:
        raise ValueError(f"unknown shortcut {shortcut!r}")
    mirrored = mirror_python(grid)
    if shortcut == "constant_fill_1":
        info = _candidate_info(mirrored)
        info = {**info, "fill_color": 1}
    elif shortcut == "fixed_color_3":
        info = _frame_info_for_color(mirrored, 3)
    else:
        info = _frame_info_for_color(mirrored, 4)
    return apply_from_intermediate(mirrored, info)


def plausible_shortcut_survivors(pairs: list[dict[str, Any]]) -> list[str]:
    """Return the named wrong rules still consistent with every visible pair."""
    if type(pairs) is not list or not pairs:
        raise ValueError("pairs must be a nonempty list")
    survivors: list[str] = []
    for shortcut in PLAUSIBLE_SHORTCUTS:
        if all(
            type(pair) is dict
            and {"input", "output"} <= set(pair)
            and apply_shortcut_python(pair["input"], shortcut) == pair["output"]
            for pair in pairs
        ):
            survivors.append(shortcut)
    return survivors


def _guarded_replace(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"alternate Racket source no longer matches {label} template")
    return source.replace(old, new, 1)


def shortcut_program(shortcut: str) -> str:
    """Materialize a bounded plausible-wrong Racket rival for self-review."""
    if shortcut not in PLAUSIBLE_SHORTCUTS:
        raise ValueError(f"unknown shortcut {shortcut!r}")
    source = program_for(ALTERNATE_FOLLOWUP)
    if shortcut == "constant_fill_1":
        return _guarded_replace(
            source,
            "(fill-color (if (= (length cells) 8) 1 5))",
            "(fill-color 1)",
            shortcut,
        )
    candidate = """(candidate (cond
                       ((f14-color-touches-probe? mirrored 3) 3)
                       ((f14-color-touches-probe? mirrored 4) 4)
                       (else #f)))"""
    fixed = 3 if shortcut == "fixed_color_3" else 4
    return _guarded_replace(source, candidate, f"(candidate {fixed})", shortcut)
