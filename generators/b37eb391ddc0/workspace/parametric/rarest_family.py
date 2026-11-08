"""Matched-input diagonal completion lessons with an input-derived color gate.

The canonical setting completes every same-colored diagonal pair.  The
alternative first finds every color that participates in at least one diagonal
pair, selects the uniquely least frequent such color in the input, and completes
only that color's pairs.  Pair labels are Python claims; native qualification
re-executes every label through protected Racket.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
COMPLETIONS = ("all_colors", "rarest_active_color")
TRAIN_PROFILES = (
    (9, 11, (1, 2, 3)),
    (11, 13, (2, 3, 4)),
    (13, 15, (2, 4, 5)),
    (16, 18, (3, 5, 6)),
    (20, 22, (4, 6, 8)),
    (24, 26, (5, 8, 10)),
)
QUERY_PROFILES = (
    (10, 12, (2, 3, 4)),
    (17, 19, (3, 6, 8)),
    (30, 30, (8, 12, 16)),
    (25, 29, (6, 9, 12)),
)
DIAGONALS = ((1, 1), (1, -1))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _completion(settings):
    if (type(settings) is not dict or set(settings) != {"completion"}
            or type(settings["completion"]) is not str
            or settings["completion"] not in COMPLETIONS):
        raise ValueError(
            "settings must contain only completion='all_colors' or "
            "'rarest_active_color'"
        )
    return settings["completion"]


def program(settings):
    completion = _completion(settings)
    filename = "canonical.rkt" if completion == "all_colors" else "rarest_active.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(grid):
    if (type(grid) is not list or not 2 <= len(grid) <= 30
            or type(grid[0]) is not list or not 2 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 2..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _colors_reading(grid):
    seen = set()
    colors = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.add(value)
                colors.append(value)
    return colors


def _active_pairs(grid):
    h, w = len(grid), len(grid[0])
    pairs = []
    for r in range(h - 1):
        for c in range(w - 1):
            first = grid[r][c]
            if first and first == grid[r + 1][c + 1]:
                pairs.append({"color": first, "cells": ((r, c), (r + 1, c + 1))})
            second = grid[r][c + 1]
            if second and second == grid[r + 1][c]:
                pairs.append({"color": second, "cells": ((r, c + 1), (r + 1, c))})
    return pairs


def analyze(grid):
    grid = _grid(grid)
    counts = Counter(value for row in grid for value in row if value)
    pairs = _active_pairs(grid)
    active_set = {pair["color"] for pair in pairs}
    active_colors = [color for color in _colors_reading(grid) if color in active_set]
    if len(active_colors) < 2:
        raise ValueError("scene needs at least two active diagonal colors")
    active_counts = {color: counts[color] for color in active_colors}
    minimum = min(active_counts.values())
    rarest = [color for color, count in active_counts.items() if count == minimum]
    if len(rarest) != 1:
        raise ValueError("scene needs one uniquely rarest active color")
    return {
        "colors": _colors_reading(grid),
        "counts": dict(counts),
        "pairs": pairs,
        "active_colors": active_colors,
        "active_counts": active_counts,
        "rarest_active_color": rarest[0],
    }


def complete_colors(grid, colors):
    """Mirror the authority's original-grid detection and accumulated writes."""
    facts = analyze(grid)
    selected = set(colors)
    out = copy.deepcopy(grid)
    positions = {
        color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value == color}
        for color in facts["colors"]
    }
    for color in facts["colors"]:
        if color not in selected:
            continue
        cells = positions[color]
        for r, c in sorted(cells):
            for dr, dc in DIAGONALS:
                q = r + dr, c + dc
                if q in cells:
                    for rr in sorted((r, q[0])):
                        for cc in sorted((c, q[1])):
                            out[rr][cc] = color
    return out


def solve(grid, completion="all_colors"):
    if type(completion) is not str or completion not in COMPLETIONS:
        raise ValueError("unknown completion mode")
    facts = analyze(grid)
    colors = facts["active_colors"] if completion == "all_colors" else [facts["rarest_active_color"]]
    return complete_colors(grid, colors)


def _rng(seed, split, index):
    raw = f"b37eb391ddc0-parametric-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _slots(height, width):
    candidates = [(0, 0), (0, width - 2), (height - 2, 0), (height - 2, width - 2)]
    candidates.extend((r, c) for r in range(0, height - 1, 3)
                      for c in range(0, width - 1, 3))
    result = []
    for slot in candidates:
        if slot in result:
            continue
        if all(abs(slot[0] - other[0]) >= 3 or abs(slot[1] - other[1]) >= 3
               for other in result):
            result.append(slot)
    return result


def _palette(seed, split, index):
    offset = 0 if split == "train" else 3
    rare = 1 + ((seed + index + offset) % 8)
    remaining = [color for color in range(1, 9) if color != rare]
    mid = remaining[(2 * seed + index + offset) % len(remaining)]
    high = next(color for color in remaining if color != mid)
    return rare, mid, high


def _place_pair(grid, slot, color, orientation, guard=False):
    r, c = slot
    if orientation == 0:
        cells = ((r, c), (r + 1, c + 1))
        companions = ((r, c + 1), (r + 1, c))
    else:
        cells = ((r, c + 1), (r + 1, c))
        companions = ((r, c), (r + 1, c + 1))
    for rr, cc in cells:
        if grid[rr][cc] != 0:
            raise ValueError("pair placement collision")
        grid[rr][cc] = color
    if guard:
        rr, cc = companions[orientation]
        if grid[rr][cc] != 0:
            raise ValueError("guard placement collision")
        grid[rr][cc] = 9


def _scene(seed, split, index, profile):
    height, width, pair_counts = profile
    rng = _rng(seed, split, index)
    rare, mid, high = _palette(seed, split, index)
    role_colors = (rare, mid, high)
    slots = _slots(height, width)
    needed = sum(pair_counts) + 3
    if len(slots) < needed:
        raise ValueError("profile lacks enough separated motif slots")

    top_left = (0, 0)
    top_right = (0, width - 2)
    bottom_right = (height - 2, width - 2)
    available = [slot for slot in slots if slot not in (top_left, top_right, bottom_right)]
    rng.shuffle(available)
    # Row-major discovery sees a nonselected color first, then the rare color,
    # so neither first-active nor last-active is a hidden equivalent rule.
    assigned = {0: [top_right], 1: [top_left], 2: [bottom_right]}
    for role, count in enumerate(pair_counts):
        while len(assigned[role]) < count:
            if role == 2:
                index = next(i for i in range(len(available) - 1, -1, -1) if available[i][0] > 0)
                assigned[role].append(available.pop(index))
            else:
                assigned[role].append(available.pop())

    grid = [[0] * width for _ in range(height)]
    guard_used = False
    placed = {0: [], 1: [], 2: []}
    for role, color in enumerate(role_colors):
        for position, slot in enumerate(assigned[role]):
            orientation = rng.randrange(2)
            use_guard = role == 0 and position == 0 and not guard_used
            _place_pair(grid, slot, color, orientation, guard=use_guard)
            placed[role].append((slot, orientation))
            guard_used = guard_used or use_guard

    # Distinct total counts identify the rarest active color without tying it to
    # pair count alone.  Put each extra into an unused companion of a separate
    # motif.  This cannot create another diagonal pair, and the high-count
    # color remains below the rare color's row-zero anchor for every seed.
    for role, extra_count in enumerate((0, 1, 2)):
        for slot, orientation in placed[role][:extra_count]:
            r, c = slot
            companions = (
                ((r, c + 1), (r + 1, c))
                if orientation == 0
                else ((r, c), (r + 1, c + 1))
            )
            rr, cc = companions[0]
            if grid[rr][cc] != 0:
                rr, cc = companions[1]
            if grid[rr][cc] != 0:
                raise ValueError("extra-cell placement collision")
            grid[rr][cc] = role_colors[role]

    facts = analyze(grid)
    if facts["rarest_active_color"] != rare or len(facts["active_colors"]) != 3:
        raise RuntimeError("constructed scene lost its selected active color")
    if len(set(facts["active_counts"].values())) != 3:
        raise RuntimeError("constructed scene lost distinct active counts")
    return grid


def _input(seed, split, index):
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    try:
        profile = profiles[index]
    except (IndexError, TypeError) as error:
        raise ValueError("unsupported split/index") from error
    return _scene(seed, split, index, profile)


def sample_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [_input(seed, "train", index) for index in range(demos)],
        "test": [_input(seed, "test", index) for index in range(queries)],
    }
    serialized = [repr(grid) for split in ("train", "test") for grid in result[split]]
    if len(serialized) != len(set(serialized)):
        raise ValueError("authored episode inputs must be distinct")
    return result


def generate(seed, settings, demos=3, queries=4):
    completion = _completion(settings)
    sampled = sample_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": solve(grid, completion)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": solve(grid, completion)}
            for grid in sampled["test"]
        ],
        "program_solution": program(settings),
        "seed": seed,
        "settings": copy.deepcopy(settings),
    }


def public_turn(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query")
    try:
        train = [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ]
        query = {"input": copy.deepcopy(episode["test"][query_index]["input"])}
    except (KeyError, TypeError) as error:
        raise ValueError("episode lacks private train/test pairs") from error
    return {"train": train, "test": [query]}
