"""Episode-fixed traversal of maximal identical-row runs.

The Python labels are claims; native qualification independently executes every
label with the exact selected Racket program. The canonical generator is untouched.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from itertools import groupby
import json
from pathlib import Path
import random

MODES = ("fixed3", "height_plus_one")
_HOME = Path(__file__).resolve().parent


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"step_mode"}
            or type(settings["step_mode"]) is not str or settings["step_mode"] not in MODES):
        raise ValueError("settings must contain exactly step_mode=fixed3|height_plus_one")
    return settings["step_mode"]


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")


def program(settings):
    mode = _mode(settings)
    return (_HOME / ("canonical.rkt" if mode == "fixed3" else "height_plus_one.rkt")).read_text()


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def run_table(grid):
    _grid(grid)
    result, start = [], 0
    for row, same in groupby(grid):
        height = sum(1 for _ in same)
        result.append({"start": start, "height": height, "row": list(row)})
        start += height
    return result


def selected_runs(heights, mode):
    if mode == "fixed3":
        return list(range(0, len(heights), 3))
    selected, index = [], 0
    while index < len(heights):
        selected.append(index)
        index += heights[index] + 1
    return selected


def _paint(grid, runs, selected, *, cells="nonzero", first_only=False):
    result = deepcopy(grid)
    for index in selected:
        run = runs[index]
        for r in range(run["start"], run["start"] + (1 if first_only else run["height"])):
            for c, value in enumerate(grid[r]):
                if cells == "all" or (cells == "nonzero" and value != 0) or value == cells:
                    result[r][c] = 2
    return result


def solve(grid, settings):
    mode = _mode(settings)
    runs = run_table(grid)
    return _paint(grid, runs, selected_runs([r["height"] for r in runs], mode))


def _rng(seed, role, index):
    payload = f"be5d9fa6fec1/row-run-v1/{seed}/{role}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _heights(total, count, rng):
    result = [1] * count
    # Capacity sampling allocates the exact height without rejection or clipping.
    tokens = [index for index in range(count) for _ in range(2)]
    for index in rng.sample(tokens, total - count):
        result[index] += 1
    return result


def _fresh_mask(width, rng, excluded, *, interior=False):
    maximum = (1 << width) - 1
    sizes = (1, 2, max(1, width // 3), max(1, width // 2), width - 1)
    size = rng.choice(sizes if interior else (*sizes, width))
    mask = sum(1 << c for c in rng.sample(range(width), size))
    # There are at most 18 runs and enough masks in every declared profile.
    # A bounded deterministic scan avoids random retry failures.
    for offset in range(len(excluded) + 2):
        candidate = (mask - 1 + offset) % maximum + 1
        if candidate not in excluded and (not interior or candidate != maximum):
            return candidate
    raise RuntimeError("row pattern support exhausted")


def _rows(width, count, rng):
    colors = [1, 1, 1, 8, 8, 1, 8, 1]
    colors.extend(rng.choice((1, 8)) for _ in range(max(0, count - len(colors))))
    patterns, used = [], {1: set(), 8: set()}
    for index, color in enumerate(colors[:count]):
        if index == 2:
            patterns.append(patterns[0][:])  # A-B-A counts as three maximal runs.
            continue
        mask = _fresh_mask(width, rng, used[color], interior=index in (0, 3))
        used[color].add(mask)
        patterns.append([color if mask & (1 << c) else 0 for c in range(width)])
    return patterns


def sample_input(seed, role, index):
    _integer(seed, "seed", 0, 2**63 - 1)
    rng = _rng(seed, role, index)
    if role == "train":
        profiles = [(11, 5, 8), (12, 7, 8), (20, 11, 12),
                    (24, 15, 14), (27, 23, 16), (30, 29, 18)]
        if not 0 <= index < len(profiles):
            raise ValueError("unsupported demonstration index")
        height, width, count = profiles[index]
        fixed = ([2, 1, 1, 3, 1, 1, 1, 1], [1, 2, 3, 1, 2, 1, 1, 1])
        heights = list(fixed[index]) if index < 2 else _heights(height, count, rng)
    elif role == "test":
        profiles = [(8, 3, 6), (17, 9, 10), (25, 19, 14), (30, 30, 16)]
        if not 0 <= index < len(profiles):
            raise ValueError("unsupported query index")
        height, width, count = profiles[index]
        heights = _heights(height, count, rng)
    else:
        raise ValueError("role must be train or test")
    patterns = _rows(width, count, rng)
    grid = [row[:] for row, h in zip(patterns, heights) for _ in range(h)]
    if len(run_table(grid)) != count or len(grid) != height:
        raise RuntimeError("constructive row-run invariant failed")
    return grid


def generate(seed, settings, demos, queries):
    _mode(settings)
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    episode = {"seed": seed, "settings": deepcopy(settings), "program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = sample_input(seed, split, index)
            episode[split].append({"input": grid, "output": solve(grid, settings)})
    return episode


def visible_turn(episode, index):
    _integer(index, "query index", 0, len(episode["test"]) - 1)
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                       for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}


def rival_names(settings):
    mode = _mode(settings)
    names = ["other_setting", "fixed2", "fixed4", "first_height_forever",
             "local_height_modulus", "height_without_one", "physical_rows",
             "one_based", "color_kind_boundaries", "first_row_only",
             "color1_only", "color8_only", "paint_all", "paint_zeros",
             "all_occurrences_of_selected_pattern", "only_first_two_hits", "identity"]
    if mode == "height_plus_one":
        names.append("height_capped_at_two")
    return names


def rival_output(name, grid, settings):
    mode = _mode(settings)
    runs = run_table(grid)
    heights = [r["height"] for r in runs]
    chosen = selected_runs(heights, mode)
    cells, first_only = "nonzero", False
    if name == "other_setting":
        chosen = selected_runs(heights, MODES[1 - MODES.index(mode)])
    elif name in ("fixed2", "fixed4"):
        chosen = list(range(0, len(runs), int(name[-1])))
    elif name == "first_height_forever":
        chosen = list(range(0, len(runs), heights[0] + 1))
    elif name == "local_height_modulus":
        chosen = [j for j, height in enumerate(heights) if j % (height + 1) == 0]
    elif name in ("height_without_one", "height_capped_at_two"):
        chosen, j = [], 0
        while j < len(runs):
            chosen.append(j)
            j += heights[j] if name == "height_without_one" else min(heights[j], 2) + 1
    elif name == "physical_rows":
        runs = [{"start": j, "height": 1, "row": row} for j, row in enumerate(grid)]
        chosen = selected_runs([1] * len(runs), mode)
    elif name == "one_based":
        if mode == "fixed3":
            chosen = list(range(2, len(runs), 3))
        else:
            chosen, j = [], 1
            while j < len(runs):
                chosen.append(j)
                j += heights[j] + 1
    elif name == "color_kind_boundaries":
        merged = []
        for row in grid:
            kind = tuple(sorted(set(row) - {0}))
            if merged and merged[-1]["kind"] == kind:
                merged[-1]["height"] += 1
            else:
                merged.append({"start": sum(x["height"] for x in merged),
                               "height": 1, "row": row, "kind": kind})
        runs = merged
        chosen = selected_runs([r["height"] for r in runs], mode)
    elif name == "first_row_only":
        first_only = True
    elif name in ("color1_only", "color8_only"):
        cells = int(name[5])
    elif name == "paint_all":
        chosen = list(range(len(runs)))
    elif name == "paint_zeros":
        cells = "all"
    elif name == "all_occurrences_of_selected_pattern":
        patterns = {tuple(runs[j]["row"]) for j in chosen}
        chosen = [j for j, run in enumerate(runs) if tuple(run["row"]) in patterns]
    elif name == "only_first_two_hits":
        chosen = chosen[:2]
    elif name == "identity":
        chosen = []
    else:
        raise ValueError(f"unknown rival: {name}")
    return _paint(grid, runs, chosen, cells=cells, first_only=first_only)


def teaching_report(train, settings):
    """Fit finite alternatives on demonstration labels only; queries are absent."""
    if not train:
        raise ValueError("demonstrations are required")
    rows = []
    for name in rival_names(settings):
        witness = next((i for i, pair in enumerate(train)
                        if rival_output(name, pair["input"], settings) != pair["output"]), None)
        rows.append({"name": name, "counterexample_demo": witness})
    return {"rival_count": len(rows), "all_refuted": all(r["counterexample_demo"] is not None for r in rows),
            "rivals": rows, "scope": "finite declared rivals, demonstration labels only"}


def write_batch(episodes, out):
    """Write masked controller bundles and separate one-query actor surfaces.

    This projects bytes; it does not certify labels. Use probe.py or native
    qualification before treating an episode as Racket-verified.
    """
    from reviewer_support import public_challenge_bytes
    staged = []
    seen = set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = hashlib.sha256(payload).hexdigest()
        if identifier in seen:
            raise ValueError("duplicate visible episode")
        seen.add(identifier)
        turns = []
        for index in range(len(episode["test"])):
            visible = public_challenge_bytes(visible_turn(episode, index))
            turns.append((hashlib.sha256(visible).hexdigest(), visible))
        staged.append((identifier, payload, turns, episode))
    if not staged:
        raise ValueError("at least one episode is required")
    staged.sort(key=lambda row: row[0])
    target = Path(out)
    target.mkdir(parents=True, exist_ok=False)
    (target / "public").mkdir()
    (target / "turns").mkdir()
    private = []
    for identifier, payload, turns, episode in staged:
        (target / "public" / f"{identifier}.json").write_bytes(payload)
        for turn_id, visible in turns:
            (target / "turns" / f"{turn_id}.json").write_bytes(visible)
        private.append({"public_id": identifier, "turn_ids": [row[0] for row in turns],
                        "episode": episode})
    (target / "private.json").write_text(json.dumps({"episodes": private}, sort_keys=True) + "\n")
    return {"public_ids": [row[0] for row in staged],
            "turn_count": sum(len(row[2]) for row in staged)}
