"""Native matched-input parametric family for ARC task ``2da4094bc0e1``.

``both_sides`` is the byte-exact canonical rule. ``cue_controlled_side``
uses a visible red cue to select the nearest wrong-length yellow control bar;
its input-derived length (4 or 5) chooses whether every exact yellow length-3
target receives only a left or a right magenta cap.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "2da4094bc0e1"
HERE = Path(__file__).resolve().parent
SETTINGS = ("both_sides", "cue_controlled_side")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

RIVALS = (
    "both_sides",
    "cue_controlled_side",
    "left_only",
    "right_only",
    "farthest_control_side",
    "opposite_cue_side",
    "shortest_control_side",
    "longest_control_side",
    "cue_row_parity",
    "cue_column_half",
    "alternating_targets",
    "all_colors_both",
    "all_colors_selected_side",
    "yellow_at_least3_both",
    "yellow_at_least3_selected_side",
    "identity",
)

# height, width, target count, decoy count, top control length, selected length.
# Top controls live on the right; bottom controls live on the left.  Thus the
# first two demonstrations reverse incidental position cues while teaching
# length 4 -> left and length 5 -> right.
_DEMO_PROFILES = (
    (10, 15, 2, 2, 4, 4),
    (12, 18, 3, 2, 4, 5),
    (14, 20, 4, 3, 5, 4),
    (16, 22, 6, 4, 5, 5),
    (18, 24, 8, 5, 4, 5),
    (20, 26, 10, 6, 5, 4),
)
_QUERY_PROFILES = (
    (10, 14, 3, 1, 5, 4),
    (16, 20, 6, 4, 4, 5),
    (24, 27, 11, 7, 5, 5),
    (30, 30, 16, 12, 4, 4),
)
_DECOY_COLORS = (5, 7, 9)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"cap_policy"}:
        raise ValueError("settings must contain only cap_policy")
    value = settings["cap_policy"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("cap_policy must be both_sides or cue_controlled_side")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "both_sides" else "cue_controlled_side.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _validate_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    allowed = {0, 2, 4, 5, 7, 9}
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in allowed for cell in row)
        for row in value
    ):
        raise ValueError("input must be rectangular and use only declared ARC colors")
    return value


def _runs(grid: list[list[int]]) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            color = row[col]
            start = col
            while col < len(row) and row[col] == color:
                col += 1
            if color != 0:
                result.append(
                    {
                        "color": color,
                        "row": row_index,
                        "start": start,
                        "end": col - 1,
                        "length": col - start,
                    }
                )
    return result


def _distance_to_run(cue: tuple[int, int], run: dict[str, int]) -> int:
    row, col = cue
    horizontal = run["start"] - col if col < run["start"] else col - run["end"] if col > run["end"] else 0
    return abs(row - run["row"]) + horizontal


def analyze(value: Any) -> dict[str, Any]:
    grid = _validate_grid(value)
    height, width = len(grid), len(grid[0])
    cue_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(cue_cells) != 1:
        raise ValueError("grammar requires exactly one red cue")
    cue = cue_cells[0]
    runs = _runs(grid)
    cue_runs = [run for run in runs if run["color"] == 2]
    if len(cue_runs) != 1 or cue_runs[0]["length"] != 1:
        raise ValueError("red cue must be isolated horizontally")
    controls = [run for run in runs if run["color"] == 4 and run["length"] in (4, 5)]
    targets = [run for run in runs if run["color"] == 4 and run["length"] == 3]
    decoys = [run for run in runs if run["color"] in _DECOY_COLORS and run["length"] == 3]
    if sorted(run["length"] for run in controls) != [4, 5]:
        raise ValueError("grammar requires exactly one yellow length-4 and one length-5 control")
    if len(targets) < 2:
        raise ValueError("grammar requires at least two yellow exact-3 targets")
    if len(decoys) < 1:
        raise ValueError("grammar requires at least one non-yellow exact-3 decoy")
    claimed = {(cue[0], cue[1])}
    for run in controls + targets + decoys:
        claimed.update((run["row"], col) for col in range(run["start"], run["end"] + 1))
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    if claimed != nonzero:
        raise ValueError("stray, malformed, or overlapping nonzero cells")
    for run in targets + decoys:
        if run["start"] == 0 or run["end"] == width - 1:
            raise ValueError("target and decoy bars require two in-bounds cap cells")
        if grid[run["row"]][run["start"] - 1] != 0 or grid[run["row"]][run["end"] + 1] != 0:
            raise ValueError("target and decoy cap cells must start empty")
    ranked = sorted(controls, key=lambda run: (_distance_to_run(cue, run), run["row"], run["start"]))
    if _distance_to_run(cue, ranked[0]) == _distance_to_run(cue, ranked[1]):
        raise ValueError("cue must select a unique nearest control")
    nearest, farthest = ranked
    side = "left" if nearest["length"] == 4 else "right"
    farthest_side = "left" if farthest["length"] == 4 else "right"
    touches_boundary = any(
        run["row"] in (0, height - 1) or run["start"] == 0 or run["end"] == width - 1
        for run in controls + targets + decoys
    )
    return {
        "height": height,
        "width": width,
        "cue": list(cue),
        "runs": runs,
        "controls": controls,
        "targets": targets,
        "decoys": decoys,
        "target_count": len(targets),
        "decoy_count": len(decoys),
        "nearest_control": nearest,
        "farthest_control": farthest,
        "nearest_control_length": nearest["length"],
        "farthest_control_length": farthest["length"],
        "selected_side": side,
        "farthest_side": farthest_side,
        "nonzero_count": len(nonzero),
        "touches_boundary": touches_boundary,
    }


def _side_for(summary: dict[str, Any], hypothesis: str) -> str | None:
    if hypothesis == "cue_controlled_side":
        return summary["selected_side"]
    if hypothesis == "left_only":
        return "left"
    if hypothesis == "right_only":
        return "right"
    if hypothesis == "farthest_control_side":
        return summary["farthest_side"]
    if hypothesis == "opposite_cue_side":
        return "right" if summary["selected_side"] == "left" else "left"
    if hypothesis == "shortest_control_side":
        return "left"
    if hypothesis == "longest_control_side":
        return "right"
    if hypothesis == "cue_row_parity":
        return "left" if summary["cue"][0] % 2 == 0 else "right"
    if hypothesis == "cue_column_half":
        return "left" if summary["cue"][1] < summary["width"] / 2 else "right"
    if hypothesis in ("all_colors_selected_side", "yellow_at_least3_selected_side"):
        return summary["selected_side"]
    if hypothesis in ("both_sides", "all_colors_both", "yellow_at_least3_both"):
        return "both"
    if hypothesis in ("alternating_targets", "identity"):
        return None
    raise ValueError("unknown declared hypothesis")


def _paint_cap(out: list[list[int]], source: list[list[int]], run: dict[str, int], side: str) -> None:
    if side in ("left", "both") and run["start"] > 0 and source[run["row"]][run["start"] - 1] == 0:
        out[run["row"]][run["start"] - 1] = 6
    if side in ("right", "both") and run["end"] + 1 < len(source[0]) and source[run["row"]][run["end"] + 1] == 0:
        out[run["row"]][run["end"] + 1] = 6


def apply_rule(value: Any, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in RIVALS:
        raise ValueError("unknown declared hypothesis")
    grid = _validate_grid(value)
    summary = analyze(grid)
    out = deepcopy(grid)
    if hypothesis == "identity":
        return out
    if hypothesis == "alternating_targets":
        for index, run in enumerate(summary["targets"]):
            _paint_cap(out, grid, run, "left" if index % 2 == 0 else "right")
        return out
    side = _side_for(summary, hypothesis)
    assert side is not None
    if hypothesis.startswith("all_colors"):
        selected_runs = summary["targets"] + summary["decoys"]
    elif hypothesis.startswith("yellow_at_least3"):
        selected_runs = summary["targets"] + summary["controls"]
    else:
        selected_runs = summary["targets"]
    for run in selected_runs:
        _paint_cap(out, grid, run, side)
    return out


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError("grids must have equal dimensions")
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _stream_seed(seed: int, split: str, index: int) -> int:
    raw = f"{TASK_ID}:parametric-v1:{seed}:{split}:{index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _candidate_slots(height: int, width: int) -> list[tuple[int, int]]:
    rows = list(range(3, height - 3, 2))
    starts = list(range(1, width - 3, 5))
    return [(row, start) for row in rows for start in starts if start + 3 < width]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, target_count, decoy_count, top_length, selected_length = profiles[index]
    rng = random.Random(_stream_seed(seed, split, index))
    grid = _blank(height, width)

    top_start = width - top_length - 1
    bottom_length = 9 - top_length
    bottom_start = 1
    grid[0][top_start : top_start + top_length] = [4] * top_length
    grid[height - 1][bottom_start : bottom_start + bottom_length] = [4] * bottom_length

    selected_top = top_length == selected_length
    if selected_top:
        cue_row = 1
        cue_col = top_start + top_length // 2
    else:
        cue_row = height - 2
        cue_col = bottom_start + bottom_length // 2
    grid[cue_row][cue_col] = 2

    slots = _candidate_slots(height, width)
    rng.shuffle(slots)
    required = target_count + decoy_count
    if len(slots) < required:
        raise RuntimeError(f"profile lacks bar slots: {len(slots)} < {required}")
    target_slots = slots[:target_count]
    decoy_slots = slots[target_count:required]
    for row, start in target_slots:
        grid[row][start : start + 3] = [4, 4, 4]
    for offset, (row, start) in enumerate(decoy_slots):
        color = _DECOY_COLORS[(offset + seed + index) % len(_DECOY_COLORS)]
        grid[row][start : start + 3] = [color] * 3

    summary = analyze(grid)
    if summary["nearest_control_length"] != selected_length:
        raise RuntimeError("construction failed to select intended control")
    if summary["selected_side"] == summary["farthest_side"]:
        raise RuntimeError("controls must encode opposite sides")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    policy = _policy(settings)
    demos = _exact_int(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _exact_int(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [{"input": grid, "output": apply_rule(grid, policy)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_rule(grid, policy)} for grid in test_inputs],
        "program_solution": program({"cap_policy": policy}),
    }


def audit_episode(episode: dict[str, Any], selected_setting: str) -> dict[str, Any]:
    if selected_setting not in SETTINGS:
        raise ValueError("selected setting is undeclared")
    survivors = []
    for hypothesis in RIVALS:
        if all(apply_rule(pair["input"], hypothesis) == pair["output"] for pair in episode["train"]):
            survivors.append(hypothesis)
    harmful = [
        hypothesis
        for hypothesis in survivors
        if hypothesis != selected_setting
        and any(apply_rule(pair["input"], hypothesis) != pair["output"] for pair in episode["test"])
    ]
    return {
        "selected_setting": selected_setting,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "queries_checked": len(episode["test"]),
    }
