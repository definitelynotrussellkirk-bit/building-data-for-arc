"""Native two-setting stripe episodes for 882c01c42710."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "882c01c42710"
HOME = Path(__file__).resolve().parent
MODES = ("canonical", "phase_locked")
DEMO_PROFILES = ((12, 13), (16, 17), (20, 21), (14, 19), (23, 24), (18, 22))
QUERY_PROFILES = ((15, 16), (21, 24), (27, 29), (30, 30))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("mode must be canonical or phase_locked")
    return {"mode": mode}


def program(settings):
    mode = settings_value(settings)["mode"]
    name = "canonical.rkt" if mode == "canonical" else "phase_locked.rkt"
    return (HOME / "rules" / name).read_text(encoding="utf-8")


def strict_grid(grid):
    if (type(grid) is not list or not grid or len(grid) > 30
            or type(grid[0]) is not list or not grid[0] or len(grid[0]) > 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid cells must be exact integers 0..9")
    return grid


def seed_axes(grid):
    strict_grid(grid)
    h, w = len(grid), len(grid[0])
    row_counts = [sum(value != 0 for value in row) for row in grid]
    col_counts = [sum(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    max_row, max_col = max(row_counts), max(col_counts)
    rows = [i for i, count in enumerate(row_counts) if count == max_row]
    cols = [i for i, count in enumerate(col_counts) if count == max_col]
    if max_row < 2 or max_col < 2 or len(rows) != 1 or len(cols) != 1:
        raise ValueError("input requires unique horizontal and vertical seed axes")
    return rows[0], cols[0]


def _periodic(sequence, offset):
    return sequence[offset % len(sequence)]


def python_oracle(grid, settings):
    """Independent deterministic label claim; protected Racket rechecks it."""
    mode = settings_value(settings)["mode"]
    strict_grid(grid)
    source = deepcopy(grid)
    h, w = len(source), len(source[0])
    cr, cc = seed_axes(source)
    h_positions = [c for c in range(w) if source[cr][c] != 0]
    v_positions = [r for r in range(h) if source[r][cc] != 0]
    h_seq = [source[cr][c] for c in h_positions]
    v_seq = [source[r][cc] for r in v_positions]
    h_start, v_start = h_positions[0], v_positions[0]
    result = deepcopy(source)
    if mode == "canonical":
        for r in range(h):
            result[r][cc] = _periodic(v_seq, r - v_start)
        for c in range(w):
            result[cr][c] = _periodic(h_seq, c - h_start)
        return result
    for c in range(w):
        result[cr][c] = _periodic(h_seq, c - h_start)
    cross_color = result[cr][cc]
    try:
        v_index = v_seq.index(cross_color)
    except ValueError as exc:
        raise ValueError("phase_locked inputs require the crossing color in the vertical seed") from exc
    for r in range(h):
        result[r][cc] = _periodic(v_seq, v_index + r - cr)
    return result


def _rng(seed, split, index, attempt=0):
    key = json.dumps([TASK_ID, seed, split, index, attempt], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _segment_start(rng, extent, length, avoid):
    candidates = [start for start in range(1, extent - length)
                  if not start <= avoid < start + length]
    if not candidates:
        raise ValueError("profile cannot place a seed away from the crossing")
    return rng.choice(candidates)


def sample_input(seed, split, index):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "demo":
        profiles = DEMO_PROFILES
    elif split == "query":
        profiles = QUERY_PROFILES
    else:
        raise ValueError("split must be demo or query")
    _integer(index, 0, len(profiles) - 1, "index")
    h, w = profiles[index]
    rng = _rng(seed, split, index)
    cr = rng.randint(max(3, h // 3), min(h - 4, (2 * h) // 3))
    cc = rng.randint(max(3, w // 3), min(w - 4, (2 * w) // 3))
    palette = rng.sample(range(1, 10), 4)
    h_shift = rng.randrange(4)
    v_shift = rng.randrange(4)
    h_seq = palette[h_shift:] + palette[:h_shift]
    v_seq = palette[v_shift:] + palette[:v_shift]
    h_start = _segment_start(rng, w, 4, cc)
    v_start = _segment_start(rng, h, 4, cr)
    cross_color = h_seq[(cc - h_start) % 4]
    if v_seq[(cr - v_start) % 4] == cross_color:
        v_seq = v_seq[1:] + v_seq[:1]
    grid = [[0] * w for _ in range(h)]
    for offset, color in enumerate(h_seq):
        grid[cr][h_start + offset] = color
    for offset, color in enumerate(v_seq):
        grid[v_start + offset][cc] = color
    seed_axes(grid)
    if python_oracle(grid, {"mode": "canonical"}) == python_oracle(grid, {"mode": "phase_locked"}):
        raise AssertionError("constructed scene failed to distinguish the two rules")
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    settings = settings_value(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": python_oracle(grid, settings)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": python_oracle(grid, settings)})
    return {"train": train, "test": test, "program_solution": program(settings)}
