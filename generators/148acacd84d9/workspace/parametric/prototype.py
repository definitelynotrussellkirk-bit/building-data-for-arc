"""Deterministic setting-neutral scenes for the rotation relay family."""
from __future__ import annotations

import copy
import hashlib
import math
import random

TASK_ID = "148acacd84d9"
VERSION = "rotate-marker-relay-v1"
CANONICAL_PROGRAM = "(rule! (rotate-cw g))"

# Profiles describe the grid *after* the canonical clockwise rotation. The
# returned input is the inverse rotation, so the alternate rule's first step
# reconstructs this deliberately controlled state.
_DEMO_PROFILES = (
    (7, "right", 12, 1),
    (8, "bottom", 14, 2),
    (9, "left", 18, 1),
    (10, "top", 20, 2),
    (12, "right", 28, 2),
    (14, "bottom", 32, 1),
)
_QUERY_PROFILES = (
    (11, "left", 24, 2),
    (16, "top", 36, 1),
    (22, "right", 50, 2),
    (30, "bottom", 72, 1),
)


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _rng(seed, split, index):
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _marker_position(size, edge, rng):
    offset = rng.randrange(1, size - 1)
    return {
        "top": (0, offset),
        "right": (offset, size - 1),
        "bottom": (size - 1, offset),
        "left": (offset, 0),
    }[edge]


def _cue_position(size, edge, marker, rng):
    distance = rng.randrange(2, size - 1)
    r, c = marker
    return {
        "top": (distance, c),
        "right": (r, size - 1 - distance),
        "bottom": (size - 1 - distance, c),
        "left": (r, distance),
    }[edge]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _scene(seed, split, index, profile):
    size, edge, payload_count, cue = profile
    rng = _rng(seed, split, index)
    after = [[0 for _ in range(size)] for _ in range(size)]
    marker = _marker_position(size, edge, rng)
    cue_pos = _cue_position(size, edge, marker, rng)
    after[marker[0]][marker[1]] = 9
    after[cue_pos[0]][cue_pos[1]] = cue

    def allowed(cell):
        r, c = cell
        if cell in {marker, cue_pos}:
            return False
        # Keep the marker's gravity line free except for the cue, guaranteeing
        # that cue 1/2 becomes the first settled contact cell.
        if edge in {"top", "bottom"} and c == marker[1]:
            return False
        if edge in {"left", "right"} and r == marker[0]:
            return False
        return 0 < r < size - 1 and 0 < c < size - 1

    candidates = [(r, c) for r in range(1, size - 1)
                  for c in range(1, size - 1) if allowed((r, c))]
    rng.shuffle(candidates)
    chosen = [cue_pos]
    used = {cue_pos}

    # First cover as many interior rows and columns as the payload budget allows.
    for r in range(1, size - 1):
        if len(chosen) >= payload_count:
            break
        options = [cell for cell in candidates if cell[0] == r and cell not in used]
        if options:
            cell = options[0]
            chosen.append(cell); used.add(cell)
    for c in range(1, size - 1):
        if len(chosen) >= payload_count:
            break
        options = [cell for cell in candidates if cell[1] == c and cell not in used]
        if options:
            cell = options[0]
            chosen.append(cell); used.add(cell)
    for cell in candidates:
        if len(chosen) >= payload_count:
            break
        if cell not in used:
            chosen.append(cell); used.add(cell)
    if len(chosen) != payload_count:
        raise RuntimeError("profile cannot place the requested payload")

    other_colors = [3 + (i % 6) for i in range(payload_count - 1)]
    rng.shuffle(other_colors)
    for (r, c), color in zip(chosen[1:], other_colors):
        after[r][c] = color
    return _rotate_ccw(after)


def build_inputs(seed, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    return {
        "train": [_scene(seed, "train", i, profile)
                  for i, profile in enumerate(_DEMO_PROFILES[:demos])],
        "test": [_scene(seed, "test", i, profile)
                 for i, profile in enumerate(_QUERY_PROFILES[:queries])],
    }


def public_turn(episode, query_index=0):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
