"""Deterministic local-statistic frame family for source 7ef325b21961.

A discovers every closed frame and computes its input-dependent local dot
statistics.  B consumes the selected local color and fills exactly that frame's
interior while preserving borders and erasing all outside distractors.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "7ef325b21961"
SCHEMA = "arcpuzzles-local-frame-parametric-v1"
HOME = Path(__file__).resolve().parent
FILL_CHOICES = ("majority", "minority")
DEMO_PROFILES = (
    (14, 18, 2),
    (18, 14, 2),
    (20, 20, 3),
    (24, 18, 3),
    (18, 24, 3),
    (26, 26, 3),
)
QUERY_PROFILES = (
    (15, 21, 2),
    (21, 15, 3),
    (24, 27, 3),
    (30, 30, 3),
)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"fill_choice"}
            or type(settings["fill_choice"]) is not str
            or settings["fill_choice"] not in FILL_CHOICES):
        raise ValueError("settings must contain exactly fill_choice=majority|minority")
    return {"fill_choice": settings["fill_choice"]}


def program(settings):
    choice = settings_value(settings)["fill_choice"]
    filename = "canonical.rkt" if choice == "majority" else "minority.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def strict_grid(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a 5..30 by 5..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid requires exact integer colors 0..9")
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                pr, pc = queue.popleft()
                cells.append((pr, pc))
                for dr, dc in _NEIGHBORS:
                    nr, nc = pr + dr, pc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells)})
    return result


def _frame_bbox(cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    if r2 - r1 + 1 < 5 or c2 - c1 + 1 < 5:
        return None
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return (r1, c1, r2, c2) if set(cells) == border else None


def analyze(grid):
    strict_grid(grid)
    frames = []
    non_frames = []
    for component in _components(grid):
        bbox = _frame_bbox(component["cells"])
        if bbox is None:
            non_frames.append(component)
            continue
        r1, c1, r2, c2 = bbox
        counts = Counter(
            grid[r][c]
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
            if grid[r][c] != 0
        )
        if component["color"] in counts:
            raise ValueError(f"frame {bbox} reuses its border color inside")
        if len(counts) != 2:
            raise ValueError(f"frame {bbox} needs exactly two dot colors")
        ordered = counts.most_common()
        if ordered[0][1] <= ordered[1][1] or ordered[1][1] < 1:
            raise ValueError(f"frame {bbox} needs a strict local majority")
        frames.append({
            "bbox": bbox,
            "frame_color": component["color"],
            "counts": counts,
            "majority": ordered[0][0],
            "minority": ordered[1][0],
        })
    frames.sort(key=lambda row: row["bbox"])
    if not frames:
        raise ValueError("input needs at least one closed rectangular frame")
    if any(len(component["cells"]) != 1 for component in non_frames):
        raise ValueError("all non-frame colored components must be isolated dots")
    majorities = [frame["majority"] for frame in frames]
    minorities = [frame["minority"] for frame in frames]
    if len(set(majorities)) != len(majorities):
        raise ValueError("frame-local majority colors must differ")
    if len(set(minorities)) != len(minorities):
        raise ValueError("frame-local minority colors must differ")
    return {"frames": frames, "non_frames": non_frames}


def _paint_base(grid, analysis, selected):
    height, width = len(grid), len(grid[0])
    result = [[0 for _ in range(width)] for _ in range(height)]
    for frame in analysis["frames"]:
        r1, c1, r2, c2 = frame["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r in (r1, r2) or c in (c1, c2):
                    result[r][c] = frame["frame_color"]
                else:
                    result[r][c] = selected(frame)
    return result


def transform(grid, settings):
    choice = settings_value(settings)["fill_choice"]
    analysis = analyze(grid)
    return _paint_base(grid, analysis, lambda frame: frame[choice])


def _rng(seed, domain, index, profile):
    raw = json.dumps([TASK_ID, SCHEMA, seed, domain, index, profile],
                     separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _draw_frame(grid, r0, c0, rh, rw, color):
    for r in range(r0, r0 + rh):
        grid[r][c0] = color
        grid[r][c0 + rw - 1] = color
    for c in range(c0, c0 + rw):
        grid[r0][c] = color
        grid[r0 + rh - 1][c] = color


def _slots(height, width, count):
    if count == 1:
        rows, cols = 1, 1
    elif count == 2:
        rows, cols = ((1, 2) if width >= height else (2, 1))
    else:
        rows, cols = 2, 2
    result = []
    for index in range(count):
        sr, sc = divmod(index, cols)
        result.append((sr * height // rows, sc * width // cols,
                       (sr + 1) * height // rows, (sc + 1) * width // cols))
    return result


def sample_input(seed, domain, index, profile):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    if (type(profile) not in (tuple, list) or len(profile) != 3
            or any(type(value) is not int for value in profile)):
        raise ValueError("profile must contain exact integer height, width and frame count")
    height, width, frame_count = profile
    integer(height, 14, 30, "height")
    integer(width, 14, 30, "width")
    integer(frame_count, 2, 3, "frame_count")

    rng = _rng(seed, domain, index, tuple(profile))
    palette = list(range(1, 10))
    rng.shuffle(palette)
    colors = palette[:3 * frame_count]
    frame_colors = colors[:frame_count]
    majority_colors = colors[frame_count:2 * frame_count]
    minority_colors = colors[2 * frame_count:]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    frame_boxes = []
    for frame_index, (sr1, sc1, sr2, sc2) in enumerate(_slots(height, width, frame_count)):
        local = _rng(seed, f"{domain}-frame", index * 10 + frame_index, tuple(profile))
        max_h = min(9, sr2 - sr1 - 2)
        max_w = min(9, sc2 - sc1 - 2)
        if max_h < 5 or max_w < 5:
            raise ValueError("profile cannot hold separated 5x5 frames")
        rh = local.randint(5, max_h)
        rw = local.randint(5, max_w)
        r0 = local.randint(sr1 + 1, sr2 - rh - 1)
        c0 = local.randint(sc1 + 1, sc2 - rw - 1)
        _draw_frame(grid, r0, c0, rh, rw, frame_colors[frame_index])
        frame_boxes.append((r0, c0, r0 + rh - 1, c0 + rw - 1))

        interior = [(r, c) for r in range(r0 + 1, r0 + rh - 1)
                    for c in range(c0 + 1, c0 + rw - 1)]
        parity = {
            0: [point for point in interior if sum(point) % 2 == 0],
            1: [point for point in interior if sum(point) % 2 == 1],
        }
        major_parity = max(parity, key=lambda value: len(parity[value]))
        major_slots = parity[major_parity]
        minor_slots = parity[1 - major_parity]
        local.shuffle(major_slots)
        local.shuffle(minor_slots)
        n_major = local.randint(3, min(5, len(major_slots)))
        n_minor = local.randint(1, min(2, n_major - 1, len(minor_slots)))
        for r, c in major_slots[:n_major]:
            grid[r][c] = majority_colors[frame_index]
        for r, c in minor_slots[:n_minor]:
            grid[r][c] = minority_colors[frame_index]

    unused = [color for color in range(1, 10) if color not in colors]
    if unused:
        candidates = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == 0
            and not any(r1 - 1 <= r <= r2 + 1 and c1 - 1 <= c <= c2 + 1
                        for r1, c1, r2, c2 in frame_boxes)
        ]
        rng.shuffle(candidates)
        remaining = rng.randint(1, min(6, len(candidates)))
        for r, c in candidates:
            if remaining == 0:
                break
            if any(0 <= r + dr < height and 0 <= c + dc < width
                   and grid[r + dr][c + dc] != 0 for dr, dc in _NEIGHBORS):
                continue
            grid[r][c] = rng.choice(unused)
            remaining -= 1

    strict_grid(grid)
    analysis = analyze(grid)
    if len(analysis["frames"]) != frame_count:
        raise ValueError("sampler emitted the wrong number of frames")
    return grid


def check_teaching(train, settings):
    chosen = settings_value(settings)["fill_choice"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    survivors = []
    for candidate in FILL_CHOICES:
        setting = {"fill_choice": candidate}
        if all(type(pair) is dict and {"input", "output"} <= set(pair)
               and transform(pair["input"], setting) == pair["output"] for pair in train):
            survivors.append(candidate)
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify {chosen}; survivors={survivors}")
    return {
        "fit_scope": "demonstrations_only",
        "survivors": survivors,
        "declared_settings": list(FILL_CHOICES),
        "limits": "Finite declared setting family only; not universal uniqueness.",
    }


def generate(seed, settings, demos=3, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    settings = settings_value(settings)
    result = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": settings,
        "program_solution": program(settings),
        "train": [],
        "test": [],
    }
    seen = set()
    for split, domain, count, profiles in (
        ("train", "demo", demos, DEMO_PROFILES),
        ("test", "query", queries, QUERY_PROFILES),
    ):
        for index in range(count):
            grid = sample_input(seed, domain, index, profiles[index])
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("sampler produced duplicate inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    check_teaching(result["train"], settings)
    return result


def _global_color(analysis, choice):
    totals = Counter()
    for frame in analysis["frames"]:
        totals.update(frame["counts"])
    ordering = sorted(totals.items(), key=lambda pair: ((-pair[1]) if choice == "majority" else pair[1], pair[0]))
    return ordering[0][0]


def _rival_output(grid, name, choice):
    analysis = analyze(grid)
    if name == "global_statistic":
        color = _global_color(analysis, choice)
        return _paint_base(grid, analysis, lambda frame: color)
    if name == "border_color":
        return _paint_base(grid, analysis, lambda frame: frame["frame_color"])
    if name == "fixed_color":
        return _paint_base(grid, analysis, lambda frame: 1)
    if name == "keep_dots":
        result = deepcopy(grid)
        frame_cells = set()
        for frame in analysis["frames"]:
            r1, c1, r2, c2 = frame["bbox"]
            frame_cells.update((r, c) for r in range(r1, r2 + 1)
                               for c in range(c1, c2 + 1))
        for r, row in enumerate(result):
            for c, value in enumerate(row):
                if (r, c) not in frame_cells:
                    result[r][c] = 0
        return result
    if name == "skip_selection":
        selected = analysis["frames"][0][choice]
        return _paint_base(grid, analysis, lambda frame: selected)
    raise ValueError("unknown rival")


def audit(seed=47, demos=3, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    rivals = ("global_statistic", "border_color", "fixed_color", "keep_dots", "skip_selection")
    report = {
        "schema": "arcpuzzles-local-frame-self-audit-v1",
        "status": "passed",
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "settings": {},
    }
    for chosen in FILL_CHOICES:
        setting = {"fill_choice": chosen}
        episode = generate(seed, setting, demos, queries)
        row = {
            "chosen": chosen,
            "survivors": check_teaching(episode["train"], setting)["survivors"],
            "query_count": len(episode["test"]),
            "rivals": {},
        }
        all_pairs = episode["train"] + episode["test"]
        for rival in rivals:
            mismatches = [index for index, pair in enumerate(all_pairs)
                          if _rival_output(pair["input"], rival, chosen) != pair["output"]]
            row["rivals"][rival] = {
                "rejected": bool(mismatches),
                "mismatch_indices": mismatches,
                "scope": "finite generated demonstrations and queries",
            }
            if not mismatches:
                report["status"] = "failed"
        report["settings"][chosen] = row
    return report
