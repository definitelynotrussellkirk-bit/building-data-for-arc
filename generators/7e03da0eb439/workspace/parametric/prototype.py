"""Deterministic authoring prototype for selective self-tiling.

The canonical setting self-tiles at every color-2 cell.  The alternative first
reads the center cell's color, binds that cue, and then self-tiles at every cell
matching the cue.  Inputs are sampled independently of the selected setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    "color_2": HOME / "canonical.rkt",
    "center_cue": HOME / "center_cue.rkt",
}
SETTINGS = tuple(PROGRAM_FILES)
ANCHOR_CUE_RIVALS = {
    "top_left_cue": (0, 0),
    "top_middle_cue": (0, 1),
    "top_right_cue": (0, 2),
    "middle_left_cue": (1, 0),
    "middle_right_cue": (1, 2),
    "bottom_left_cue": (2, 0),
    "bottom_middle_cue": (2, 1),
    "bottom_right_cue": (2, 2),
}
MODE_RIVALS = tuple(
    [f"global_mode_{tie}" for tie in ("first", "min", "max")]
    + [
        f"{axis}_{anchor}_mode_{tie}"
        for axis in ("row", "col")
        for anchor in range(3)
        for tie in ("first", "min", "max")
    ]
)
RIVALS = (
    "value_gt_one",
    "nonzero",
    "center_position_only",
    *ANCHOR_CUE_RIVALS,
    *MODE_RIVALS,
    "fixed_color_1",
    "fixed_color_3",
    "fixed_color_4",
    "fixed_color_5",
    "fixed_color_6",
    "fixed_color_7",
    "fixed_color_8",
    "fixed_color_9",
)


def _exact_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: object) -> str:
    if not isinstance(settings, dict) or set(settings) != {"trigger_mode"}:
        raise ValueError("settings must contain exactly trigger_mode")
    value = settings["trigger_mode"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("unknown trigger_mode")
    return value


def program(settings: dict) -> str:
    return PROGRAM_FILES[_mode(settings)].read_text(encoding="utf-8")


def _validate_grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be rectangular and 1..30")
    width = len(grid[0])
    out: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        checked_row: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid cells must be exact ARC integers")
            checked_row.append(value)
        out.append(checked_row)
    return out


def _self_tile_positions(
    grid: list[list[int]], positions: list[tuple[int, int]]
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w * w)] for _ in range(h * h)]
    for tile_r, tile_c in positions:
        for r in range(h):
            for c in range(w):
                out[tile_r * h + r][tile_c * w + c] = grid[r][c]
    return out


def _self_tile_value(grid: list[list[int]], trigger: int) -> list[list[int]]:
    positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == trigger
    ]
    return _self_tile_positions(grid, positions)


def apply_python(grid: list[list[int]], settings: dict) -> list[list[int]]:
    checked = _validate_grid(grid)
    mode = _mode(settings)
    if mode == "color_2":
        trigger = 2
    else:
        trigger = checked[len(checked) // 2][len(checked[0]) // 2]
    return _self_tile_value(checked, trigger)


def _mode_value(values: list[int], tie: str) -> int:
    counts = {value: values.count(value) for value in set(values)}
    best = max(counts.values())
    if tie == "first":
        return next(value for value in values if counts[value] == best)
    tied = [value for value, count in counts.items() if count == best]
    if tie == "min":
        return min(tied)
    if tie == "max":
        return max(tied)
    raise ValueError("unknown mode tie")


def _anchor_index(anchor: int, length: int) -> int:
    return anchor * (length - 1) // 2


def apply_rival(grid: list[list[int]], rival: str) -> list[list[int]]:
    checked = _validate_grid(grid)
    h, w = len(checked), len(checked[0])
    if rival == "value_gt_one":
        positions = [
            (r, c)
            for r, row in enumerate(checked)
            for c, value in enumerate(row)
            if value > 1
        ]
        return _self_tile_positions(checked, positions)
    if rival == "nonzero":
        positions = [
            (r, c)
            for r, row in enumerate(checked)
            for c, value in enumerate(row)
            if value != 0
        ]
        return _self_tile_positions(checked, positions)
    if rival == "center_position_only":
        return _self_tile_positions(checked, [(h // 2, w // 2)])
    if rival in ANCHOR_CUE_RIVALS:
        row_anchor, col_anchor = ANCHOR_CUE_RIVALS[rival]
        trigger = checked[_anchor_index(row_anchor, h)][_anchor_index(col_anchor, w)]
        return _self_tile_value(checked, trigger)
    if rival.startswith("global_mode_"):
        tie = rival.removeprefix("global_mode_")
        trigger = _mode_value([value for row in checked for value in row], tie)
        return _self_tile_value(checked, trigger)
    parts = rival.split("_")
    if len(parts) == 4 and parts[0] in {"row", "col"} and parts[2] == "mode":
        axis, anchor_text, _, tie = parts
        if anchor_text in {"0", "1", "2"}:
            anchor = int(anchor_text)
            if axis == "row":
                values = checked[_anchor_index(anchor, h)]
            else:
                col = _anchor_index(anchor, w)
                values = [row[col] for row in checked]
            return _self_tile_value(checked, _mode_value(values, tie))
    prefix = "fixed_color_"
    if rival.startswith(prefix):
        suffix = rival[len(prefix) :]
        if suffix.isdigit() and int(suffix) in range(10):
            return _self_tile_value(checked, int(suffix))
    raise ValueError("unknown rival")


def _derived_seed(seed: int, split: str, index: int) -> int:
    raw = f"7e03da0eb439|{seed}|{split}|{index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _rotate(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(grid))]


def _symmetry(grid: list[list[int]], rng: random.Random) -> list[list[int]]:
    out = deepcopy(grid)
    for _ in range(rng.randrange(4)):
        out = _rotate(out)
    if rng.randrange(2):
        out = [list(reversed(row)) for row in out]
    return out


def _palette(seed: int) -> dict[int, int]:
    colors = [1, 3, 4, 5, 6, 7, 8, 9]
    shuffled = list(colors)
    random.Random(_derived_seed(seed, "palette", 0)).shuffle(shuffled)
    mapping = {0: 0, 2: 2}
    mapping.update(dict(zip(colors, shuffled)))
    return mapping


def _transform(
    grid: list[list[int]], seed: int, split: str, index: int, mapping: dict[int, int]
) -> list[list[int]]:
    recolored = [[mapping[value] for value in row] for row in grid]
    return _symmetry(recolored, random.Random(_derived_seed(seed, split, index)))


# The first two 3x3 scenes are a constructive teaching certificate.  They use
# one shared D4 transform per seed.  Their color-2 coordinate sets are disjoint,
# while their center-cue coordinate sets intersect only at the center.  Therefore
# no non-center fixed-coordinate cue can fit both settings.  A distinct modal
# distractor and line layouts also reject global/row/column mode shortcuts.
TRAIN_TEMPLATES: tuple[list[list[int]], ...] = (
    [
        [3, 2, 2],
        [8, 3, 8],
        [8, 1, 0],
    ],
    [
        [4, 4, 6],
        [2, 6, 2],
        [4, 9, 0],
    ],
    [
        [9, 4, 8],
        [2, 4, 2],
        [7, 4, 1],
    ],
    [
        [3, 2, 8, 1, 9],
        [5, 0, 2, 5, 4],
        [2, 7, 5, 6, 5],
        [8, 5, 0, 2, 1],
        [4, 9, 5, 3, 7],
    ],
    [
        [4, 7, 9],
        [2, 7, 2],
        [7, 1, 8],
    ],
    [
        [1, 8, 2, 4, 9],
        [8, 0, 6, 2, 3],
        [2, 5, 8, 7, 8],
        [4, 2, 1, 8, 6],
        [9, 3, 8, 5, 7],
    ],
)

QUERY_TEMPLATES: tuple[list[list[int]], ...] = (
    [
        [4, 2, 8],
        [0, 5, 1],
        [2, 5, 5],
    ],
    [
        [2, 4, 6, 2, 8],
        [3, 7, 3, 1, 5],
        [9, 2, 3, 2, 4],
        [6, 3, 0, 3, 7],
        [8, 1, 2, 5, 9],
    ],
    [
        [6, 9, 2],
        [4, 1, 2],
        [1, 1, 7],
    ],
    [
        [2, 9, 4, 7, 2],
        [8, 6, 5, 6, 3],
        [4, 9, 6, 1, 7],
        [5, 6, 8, 6, 9],
        [2, 3, 1, 4, 2],
    ],
)


def _all_train_inputs(seed: int) -> list[list[list[int]]]:
    _exact_int("seed", seed, 0, 2**63 - 1)
    mapping = _palette(seed)
    values = []
    for index, grid in enumerate(TRAIN_TEMPLATES):
        # Preserve the first two templates' coordinate-intersection certificate
        # by applying the same seed-dependent D4 transform to both.
        split, transform_index = ("teaching", 0) if index < 2 else ("train", index)
        values.append(_transform(grid, seed, split, transform_index, mapping))
    return values


def _all_query_inputs(seed: int) -> list[list[list[int]]]:
    _exact_int("seed", seed, 0, 2**63 - 1)
    mapping = _palette(seed)
    return [
        _transform(grid, seed, "query", index, mapping)
        for index, grid in enumerate(QUERY_TEMPLATES)
    ]


def teaching_report(train: list[dict], settings: dict) -> dict:
    intended = _mode(settings)
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty pair list")
    pairs: list[tuple[list[list[int]], list[list[int]]]] = []
    for pair in train:
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            raise ValueError("invalid teaching pair")
        pairs.append((_validate_grid(pair["input"]), _validate_grid(pair["output"])))
    setting_survivors = [
        candidate
        for candidate in SETTINGS
        if all(
            apply_python(grid, {"trigger_mode": candidate}) == output
            for grid, output in pairs
        )
    ]
    rival_survivors = [
        rival
        for rival in RIVALS
        if all(apply_rival(grid, rival) == output for grid, output in pairs)
    ]
    return {
        "fit_scope": "demonstrations_only",
        "intended_setting": intended,
        "setting_survivors": setting_survivors,
        "plausible_rival_survivors": rival_survivors,
        "rivals_checked": list(RIVALS),
    }


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    _exact_int("seed", seed, 0, 2**63 - 1)
    _exact_int("demos", demos, 2, 6)
    _exact_int("queries", queries, 1, 4)
    mode = _mode(settings)
    train_inputs = _all_train_inputs(seed)[:demos]
    test_inputs = _all_query_inputs(seed)[:queries]
    serialized = [
        json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs
    ]
    if len(serialized) != len(set(serialized)):
        raise ValueError("all demonstration/query inputs must be distinct")
    chosen = {"trigger_mode": mode}
    train = [
        {"input": grid, "output": apply_python(grid, chosen)} for grid in train_inputs
    ]
    test = [
        {"input": grid, "output": apply_python(grid, chosen)} for grid in test_inputs
    ]
    report = teaching_report(train, chosen)
    if report["setting_survivors"] != [mode] or report["plausible_rival_survivors"]:
        raise ValueError("constructive demonstrations failed to identify the intended rule")
    return {"train": train, "test": test, "program_solution": program(chosen)}
