"""Native blocker-gravity family with an input-derived cue-side alternative."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "a0e364b16592"
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
CUE_SIDE = (HERE / "cue_side.rkt").read_text(encoding="utf-8")
MODES = ("canonical_down", "cue_side")
RIVALS = (
    "identity",
    "global_bottom",
    "always_up_fixed_cue",
    "always_down_fixed_cue",
    "reverse_payload_order",
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"gravity_rule"}:
        raise ValueError("settings must contain exactly gravity_rule")
    mode = settings["gravity_rule"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("gravity_rule is undeclared")
    return mode


def validate_grid(grid: object) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")
    return deepcopy(grid)


def program(settings: object) -> str:
    return CANONICAL if _mode(settings) == "canonical_down" else CUE_SIDE


def dependency_intermediate(grid: object) -> dict[str, Any]:
    checked = validate_grid(grid)
    cues = [[r, c] for r, row in enumerate(checked) for c, value in enumerate(row) if value == 9]
    if len(cues) != 1:
        raise ValueError("cue_side inputs need exactly one color-9 cue")
    cue = cues[0]
    if cue[0] not in (0, len(checked) - 1):
        raise ValueError("the color-9 cue must be on the top or bottom border")
    return {"cue": cue, "direction": "up" if cue[0] == 0 else "down"}


def _segment_pack(
    grid: list[list[int]],
    direction: str,
    *,
    fixed_values: frozenset[int],
    reverse_values: bool = False,
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        start = 0
        while start < h:
            stop = start
            while stop < h and grid[stop][c] not in fixed_values:
                stop += 1
            values = [grid[r][c] for r in range(start, stop) if grid[r][c] != 0]
            if reverse_values:
                values.reverse()
            base = start if direction == "up" else stop - len(values)
            for offset, value in enumerate(values):
                out[base + offset][c] = value
            if stop < h:
                out[stop][c] = grid[stop][c]
            start = stop + 1
    return out


def _global_bottom(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        fixed = {r for r in range(h) if grid[r][c] == 5}
        for r in fixed:
            out[r][c] = 5
        values = [grid[r][c] for r in range(h) if grid[r][c] not in (0, 5)]
        slots = [r for r in range(h) if r not in fixed][-len(values):]
        for r, value in zip(slots, values):
            out[r][c] = value
    return out


def solve(grid: object, mode: str) -> list[list[int]]:
    checked = validate_grid(grid)
    if mode == "canonical_down":
        return _segment_pack(checked, "down", fixed_values=frozenset({5}))
    if mode == "cue_side":
        intermediate = dependency_intermediate(checked)
        return _segment_pack(
            checked,
            intermediate["direction"],
            fixed_values=frozenset({5, 9}),
        )
    raise ValueError("unknown mode")


def _rng(seed: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(seed: int, index: int, h: int, w: int, cue_at_top: bool) -> list[list[int]]:
    rng = _rng(seed, f"scene:{index}")
    grid = [[0] * w for _ in range(h)]
    cue_col = (3 * index + rng.randrange(w)) % w
    grid[0 if cue_at_top else h - 1][cue_col] = 9

    # One blocker in most columns, and a second in tall scenes. The phase varies
    # by seed/index but leaves at least two cells in every resulting segment.
    for c in range(w):
        if c == cue_col and h <= 8:
            continue
        r1 = 2 + ((3 * c + 2 * index + rng.randrange(max(1, h - 4))) % (h - 4))
        grid[r1][c] = 5
        if h >= 15 and c % 3 == index % 3:
            candidates = [r for r in range(2, h - 2) if abs(r - r1) >= 4]
            if candidates:
                r2 = candidates[(c + index + rng.randrange(len(candidates))) % len(candidates)]
                grid[r2][c] = 5

    palette = [1, 2, 3, 4, 6, 7, 8]
    for c in range(w):
        fixed = sorted(r for r in range(h) if grid[r][c] in (5, 9))
        bounds = [-1, *fixed, h]
        for seg_index, (lo, hi) in enumerate(zip(bounds, bounds[1:])):
            rows = list(range(lo + 1, hi))
            if not rows:
                continue
            # Dense enough to make the 30x30 case substantive while retaining
            # blank landing space and nontrivial motion in both directions.
            target = min(len(rows), max(1, (len(rows) + 1) // 2))
            if len(rows) > 2:
                target = min(target, len(rows) - 1)
            order = rows[:]
            rng.shuffle(order)
            chosen = sorted(order[:target])
            if len(rows) > 1 and chosen == rows[:target]:
                chosen[-1] = rows[-1]
                chosen = sorted(set(chosen))
            for j, r in enumerate(chosen):
                if grid[r][c] == 0:
                    grid[r][c] = palette[(c + r + seg_index + j + index + rng.randrange(len(palette))) % len(palette)]

    # Explicit payload on both sides of at least one color-5 blocker defeats
    # the historical global-bottom shortcut on every scene.
    witness_col = next(c for c in range(w) if any(grid[r][c] == 5 for r in range(2, h - 2)))
    blocker = next(r for r in range(2, h - 2) if grid[r][witness_col] == 5)
    for r, value in ((blocker - 1, 1), (blocker + 1, 2)):
        if grid[r][witness_col] == 0:
            grid[r][witness_col] = value

    validate_grid(grid)
    dependency_intermediate(grid)
    return grid


_PROFILES = (
    (8, 8, True),
    (9, 10, False),
    (12, 9, True),
    (15, 14, False),
    (20, 18, True),
    (30, 30, False),
    (7, 11, True),
    (16, 13, False),
    (24, 27, True),
    (30, 30, True),
)


def input_bank(seed: object) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    seed_i = _integer(seed, 0, 2**63 - 1, "seed")
    grids = [_scene(seed_i, index, *profile) for index, profile in enumerate(_PROFILES)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(keys) != len(set(keys)):
        raise ValueError("constructed inputs must be distinct")
    return grids[:6], grids[6:]


def generate(seed: object, settings: object, demos: object = 3, queries: object = 4) -> dict[str, Any]:
    seed_i = _integer(seed, 0, 2**63 - 1, "seed")
    demos_i = _integer(demos, 2, 6, "demos")
    queries_i = _integer(queries, 1, 4, "queries")
    mode = _mode(settings)
    train, test = input_bank(seed_i)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": solve(grid, mode)}

    return {
        "train": [pair(grid) for grid in train[:demos_i]],
        "test": [pair(grid) for grid in test[:queries_i]],
        "program_solution": program({"gravity_rule": mode}),
        "meta": {"settings": {"gravity_rule": mode}, "seed": seed_i},
    }


def rival_output(grid: object, name: str, chosen_mode: str) -> list[list[int]]:
    checked = validate_grid(grid)
    if name == "identity":
        return checked
    if name == "global_bottom":
        return _global_bottom(checked)
    if name == "always_up_fixed_cue":
        dependency_intermediate(checked)
        return _segment_pack(checked, "up", fixed_values=frozenset({5, 9}))
    if name == "always_down_fixed_cue":
        dependency_intermediate(checked)
        return _segment_pack(checked, "down", fixed_values=frozenset({5, 9}))
    if name == "reverse_payload_order":
        if chosen_mode == "canonical_down":
            return _segment_pack(checked, "down", fixed_values=frozenset({5}), reverse_values=True)
        direction = dependency_intermediate(checked)["direction"]
        return _segment_pack(checked, direction, fixed_values=frozenset({5, 9}), reverse_values=True)
    raise ValueError(name)


def public_turn(episode: object, query_index: object) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode is malformed")
    index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }


def public_id(episode: object, query_index: object) -> str:
    raw = json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _program_with_forced_direction(up: bool) -> str:
    needle = "(up? (= (first cue) 0))"
    replacement = "(up? #t)" if up else "(up? #f)"
    if CUE_SIDE.count(needle) != 1:
        raise ValueError("cue-side program template changed")
    return CUE_SIDE.replace(needle, replacement)


def causal_case(grid: object) -> dict[str, Any]:
    checked = validate_grid(grid)
    intermediate = dependency_intermediate(checked)
    wrong = "down" if intermediate["direction"] == "up" else "up"
    intended = solve(checked, "cue_side")
    counterfactual = _segment_pack(checked, wrong, fixed_values=frozenset({5, 9}))
    return {
        "input": checked,
        "settings": {"gravity_rule": "cue_side"},
        "intermediate_value": {**intermediate, "wrong_direction": wrong},
        "program": CUE_SIDE,
        "output": intended,
        "counterfactual_program": _program_with_forced_direction(wrong == "up"),
        "counterfactual_output": counterfactual,
        "ablation": "wrong_intermediate",
    }
