"""Semantic generator for ARC task ba32e05911b0.

Each color-6 marker traces upward through the original grid.  Empty cells on
the path become 2.  On hitting a horizontal color-7 run, the trace either
rolls past its right end with the 8/4/2/3 pattern, or stops as 6 when the run
reaches the right edge or orange cells below obstruct the roll.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "ba32e05911b0"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "96b86f6cf562"
SUMMARY = "Trace color-6 markers upward; roll right across orange ledges or stop when the roll is blocked or reaches the edge."
INVARIANTS = [
    "inputs use literal-zero background and only colors 0, 6, and 7",
    "at least one marker produces a nonempty upward trace",
    "all collision decisions read the immutable input grid",
    "a clear ledge writes the exact 8/4/2/3 roll pattern before continuing",
    "blocked and right-edge ledges stop the current marker as color 6",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "clear_climb",
    "short_roll",
    "long_roll",
    "multi_roll",
    "blocked_stop",
    "edge_stop",
    "multiple_markers",
    "dense_distractors",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eight observable trace-event lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "00000000000000000000/00000000000000000000/00000000000000000000/00000000000000000000/00000000007777770000/00000000000000000000/00000000000000000000/00000000000000000000/00000000000000000000/00000007777700000000/00000000000000000000/00000000000000000000/00000000000077777700/00000000000000000000/00000000000000000000/07777777000000000000/00000000000000000000/00000000007777000000/00000000000000000000/00000000000000000000/00000007770000000000/00000000000000000000/00006000600000000000",
    "public_2": "00700000700000000770700000000/00000000007000000000000000000/70070000000000000000077777000/07700007000000700000007000007/00007007777707770000700000000/00070000000007000000000000000/00000000000700000070000770000/00000007000007000000000000007/70000000000000000070700000000/00000000000000000007000000700/00000700000077000000000077700/70000077700000000070000000000/00000000000000770000000000000/77000000070000000000000077777/00000000000000000000000000000/00077700000007000000000000000/00000000000777700000000000000/00000007000000000000000007000/00000000000000000000000000000/00700000000777007000007070070/00070000000000007777700000000/00000000007000000000000000700/00000070070007770000000000000/70077707000070000000077000000/00700000070000000000000700000/00700000000000000700000700000/70000007000000000070007770000/00600070000600000000700000070",
    "public_3": "0000000000/0000000000/0000000000/0000000000/0000000000/0000777000/0007707000/0000000000/0000000000/0000000000/0000000000/0777700000/0000000000/0000000000/0000000000/0000000000/0060000000",
    "public_4": "0007000070700000000/0000007770000000000/0070700000000000000/0700000000000000000/7000000777777000000/0000000000000000000/0000700000000000000/0000070000077777000/0000000000000000000/0000000700007070000/7007000000000000070/0700000777777700000/0700700000000000000/0000000000000000000/0007700070000077000/0000000000000000000/0070000000700000000/0000000000000070000/0007777700000000000/0000000000000000000/0000000700077770000/0000000000000000000/0000000000000000000/0777777000000000070/0000000007000000000/0007000000070077770/0000000000000000000/0600000000000000000",
    "public_5": "0070070000000000000070000/0000000000000700000070000/0070000000007070000000000/0000000707070007007777700/0070000007070077000000000/0000000000000000000000000/0077770007000000000000000/0000000070007770000000000/0000000000000000000000000/0000000000000007777770000/0000000000000070000000000/7000000000000000000000000/0070000777700000000070000/0000070000000000000000000/7000000000000007000000000/0000000000000000000000000/0007000000000000000000000/0000000077770000700000070/0000070000000000000000700/0000000000700000000000000/0000000000000000000000000/0700000000000000707077770/0000007000000000000000000/0000000000070000007000000/0000000000000000700000000/0000000000000000000070000/0060000607000070006007000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(v, bool) or not isinstance(v, int) or v not in (0, 6, 7) for row in grid for v in row):
        return ["input cells must be colors 0, 6, or 7"]
    return []


def _orange_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    count = 0
    while unseen:
        count += 1
        stack = [min(unseen)]
        while stack:
            r, c = stack.pop()
            if (r, c) not in unseen:
                continue
            unseen.remove((r, c))
            stack.extend((rr, cc) for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if (rr, cc) in unseen)
    return count


def _trace(grid):
    h, w = len(grid), len(grid[0])
    original = tuple(map(tuple, grid))
    output = [list(row) for row in grid]
    markers = [(r, c) for r in range(h) for c in range(w) if original[r][c] == 6]
    traces = []
    for mr, mc in markers:
        r, col = mr - 1, mc
        events = []
        path_cells = []
        while True:
            if r < 0:
                output[0][col] = 6
                events.append({"kind": "top_exit", "row": 0, "col": col})
                break
            if original[r][col] == 7:
                re = col
                while re + 1 < w and original[r][re + 1] == 7:
                    re += 1
                gc = re + 1
                if gc >= w:
                    output[r + 1][col] = 6
                    events.append({"kind": "edge_stop", "row": r, "col": col, "run_end": re})
                    break
                blocked = any(r + 1 < h and original[r + 1][cc] == 7 for cc in range(col + 1, gc + 1))
                if blocked:
                    output[r + 1][col] = 6
                    events.append({"kind": "blocked_stop", "row": r, "col": col, "run_end": re, "next_col": gc})
                    break
                output[r][col] = 8
                output[r + 1][col] = 4
                for cc in range(col + 1, re + 1):
                    output[r + 1][cc] = 2
                output[r + 1][gc] = 3
                events.append({"kind": "roll", "row": r, "col": col, "run_end": re, "next_col": gc, "length": re - col + 1})
                col = gc
                continue
            output[r][col] = 2
            path_cells.append((r, col))
            r -= 1
        traces.append({"marker": (mr, mc), "events": events, "path_cells": path_cells})
    return output, traces


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _trace(grid)[0]


def _profile(traces, grid):
    if len(traces) >= 2:
        return "multiple_markers"
    events = [event for trace in traces for event in trace["events"]]
    if any(event["kind"] == "blocked_stop" for event in events):
        return "blocked_stop"
    if any(event["kind"] == "edge_stop" for event in events):
        return "edge_stop"
    rolls = [event for event in events if event["kind"] == "roll"]
    if len(rolls) >= 2:
        return "multi_roll"
    if not rolls:
        return "clear_climb"
    orange_density = sum(value == 7 for row in grid for value in row) / (len(grid) * len(grid[0]))
    if orange_density >= 0.16:
        return "dense_distractors"
    return "short_roll" if rolls[0]["length"] <= 2 else "long_roll"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    if not 1 <= len(markers) <= 3:
        errors.append(f"expected 1..3 color-6 markers; got {len(markers)}")
        return result
    if any(row != len(grid) - 1 for row, _ in markers):
        errors.append("all color-6 markers must begin on the bottom row")
    orange_count = sum(value == 7 for row in grid for value in row)
    if orange_count < 8:
        errors.append(f"expected at least eight orange structure/distractor cells; got {orange_count}")
    if not any(value == 0 for row in grid for value in row):
        errors.append("expected literal-zero background")
    output, traces = _trace(grid)
    if output == [list(row) for row in grid]:
        errors.append("trace must change at least one cell")
    if any(not trace["events"] for trace in traces):
        errors.append("every marker trace must terminate with an observable event")
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _profile(traces, grid)
    if profile not in SCENE_PROFILES:
        errors.append("trace events do not match a declared scene profile")
    events = [event for trace in traces for event in trace["events"]]
    result.update({
        "markers": markers,
        "marker_count": len(markers),
        "traces": traces,
        "events": events,
        "rolls": [event for event in events if event["kind"] == "roll"],
        "event_kinds": [event["kind"] for event in events],
        "orange_count": orange_count,
        "orange_components": _orange_components(grid),
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def _isolated_noise(grid, rng, protected_cols, forbidden_rows, target):
    h, w = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(h - 1) for c in range(w) if c not in protected_cols and r not in forbidden_rows]
    rng.shuffle(candidates)
    placed = 0
    for r, c in candidates:
        if grid[r][c] != 0:
            continue
        if any(0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 7 for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))):
            continue
        grid[r][c] = 7
        placed += 1
        if placed >= target:
            break


def _paint_run(grid, row, start, length):
    for col in range(start, start + length):
        grid[row][col] = 7


def _general_scene(ctx, profile):
    ranges = {None: (17, 30), "easy": (12, 18), "medium": (18, 24), "hard": (24, 30)}
    lo, hi = ranges[ctx.difficulty]
    h = ctx.draw_int("canvas_height", lo, hi)
    w = ctx.draw_int("canvas_width", max(10, lo - 2), hi)
    rng = ctx.draw_rng("geometry")
    grid = [[0 for _ in range(w)] for _ in range(h)]
    protected = set()
    forbidden = set()

    if profile == "multiple_markers":
        cols = (rng.randint(1, max(1, w // 3)), rng.randint(max(2, 2 * w // 3), w - 2))
        for col in cols:
            grid[h - 1][col] = 6
        protected.update(cols)
    else:
        max_start = max(1, w - 8)
        col = rng.randint(1, max_start)
        grid[h - 1][col] = 6
        protected.add(col)
        if profile in ("short_roll", "long_roll", "dense_distractors"):
            length = rng.randint(1, 2) if profile == "short_roll" else (3 if profile == "dense_distractors" else rng.randint(4, min(6, w-col-2)))
            row = rng.randint(3, h - 4)
            _paint_run(grid, row, col, length)
            protected.add(col + length)
            forbidden.update((row, row + 1))
        elif profile == "multi_roll":
            length1 = rng.randint(1, 2)
            length2 = rng.randint(2, 3)
            lower = rng.randint(h // 2 + 2, h - 4)
            upper = rng.randint(2, max(2, lower - 4))
            _paint_run(grid, lower, col, length1)
            col2 = col + length1
            _paint_run(grid, upper, col2, length2)
            protected.update((col2, col2 + length2))
            forbidden.update((lower, lower + 1, upper, upper + 1))
        elif profile == "blocked_stop":
            row = rng.randint(3, h - 4)
            _paint_run(grid, row, col, 3)
            grid[row + 1][col + 1] = 7
            forbidden.update((row, row + 1))
        elif profile == "edge_stop":
            col = rng.randint(max(1, w - 6), w - 2)
            grid[h - 1] = [0 for _ in range(w)]
            grid[h - 1][col] = 6
            protected = {col}
            row = rng.randint(3, h - 4)
            _paint_run(grid, row, col, w - col)
            forbidden.update((row, row + 1))

    area = h * w
    target = max(12, area // (5 if profile == "dense_distractors" else 11))
    _isolated_noise(grid, rng, protected, forbidden, target)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile construction drift: {profile} -> {analysis['scene_profile']}")
    return grid
