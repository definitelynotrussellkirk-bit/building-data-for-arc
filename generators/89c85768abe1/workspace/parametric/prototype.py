"""Constructive, episode-fixed rectangle completion/component-selection family.

The first two demonstrations reverse the winning role: a connected pair beats
a larger individual rectangle, then an isolated rectangle beats that pair.
Inputs are matched across rule settings. The production generator is untouched.
Python outputs are claims; native qualification/export re-executes them in Racket.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("all", "largest_component")


def _adjacent_module(name):
    path = HERE / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "_rectangle_component_" + hashlib.sha256(str(path).encode()).hexdigest(), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RULES = _adjacent_module("racket_rules")


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must be exactly {'mode': 'all'|'largest_component'}")
    return settings["mode"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    mode = _settings(settings)
    if mode == "all":
        return (HERE / "canonical.rkt").read_text(encoding="utf-8")
    return RULES.variant_program()


def _positions(grid):
    colors = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                colors.setdefault(value, []).append((r, c))
    return colors


def _box(cells):
    return (min(p[0] for p in cells), min(p[1] for p in cells),
            max(p[0] for p in cells), max(p[1] for p in cells))


def _box_cells(box):
    r0, c0, r1, c1 = box
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def _grid_errors(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        return ["expected a 1..30 by 1..30 list grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        return ["grid must be rectangular with exact integer colors 0..9"]
    return []


def validate_input(grid):
    errors = _grid_errors(grid)
    if errors:
        return errors
    colors = _positions(grid)
    if not 2 <= len(colors) <= 4:
        return ["expected 2..4 nonzero colors"]
    occupied = set()
    for color, cells in colors.items():
        if len(cells) != 2 or cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            return [f"color {color} needs two non-collinear opposite corners"]
        region = _box_cells(_box(cells))
        if occupied & region:
            return ["completed rectangles must not overlap"]
        occupied.update(region)
    return []


def _fill(grid, predicate=None):
    out = deepcopy(grid)
    for color, cells in _positions(grid).items():
        if len(cells) < 2 or (predicate is not None and not predicate(color, cells)):
            continue
        for r, c in _box_cells(_box(cells)):
            out[r][c] = color
    return out


def components(grid, connectivity=4):
    height, width = len(grid), len(grid[0])
    neighbors = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        neighbors += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    elif connectivity != 4:
        raise ValueError("connectivity must be 4 or 8")
    seen, groups = set(), []
    for r in range(height):
        for c in range(width):
            if not grid[r][c] or (r, c) in seen:
                continue
            queue, cells = deque([(r, c)]), set()
            seen.add((r, c))
            while queue:
                p = queue.popleft()
                cells.add(p)
                for dr, dc in neighbors:
                    q = (p[0] + dr, p[1] + dc)
                    if (0 <= q[0] < height and 0 <= q[1] < width and q not in seen
                            and grid[q[0]][q[1]]):
                        seen.add(q)
                        queue.append(q)
            groups.append(cells)
    return groups


def _keep(grid, cells):
    return [[value if (r, c) in cells else 0 for c, value in enumerate(row)]
            for r, row in enumerate(grid)]


def solve(grid, settings):
    mode = _settings(settings)
    errors = validate_input(grid)
    if errors:
        raise ValueError("; ".join(errors))
    filled = _fill(grid)
    if mode == "all":
        return filled
    # Components are discovered in reading order. max preserves the first tie.
    return _keep(filled, max(components(filled), key=len))


def observables(grid):
    errors = validate_input(grid)
    if errors:
        raise ValueError("; ".join(errors))
    filled = _fill(grid)
    groups = components(filled)
    return {
        "shape": [len(grid), len(grid[0])],
        "rectangles": len(_positions(grid)),
        "input_component_sizes": [len(c) for c in components(grid)],
        "completed_components": [
            {"size": len(c), "bbox": list(_box(c)), "first_cell": list(min(c)),
             "colors": sorted({filled[r][col] for r, col in c})} for c in groups],
        "winner_first_cell": list(min(max(groups, key=len))),
        "completed_cells": sum(map(len, groups)),
    }


RIVALS = ("all", "largest_component", "identity", "largest_rectangle", "eight_connected",
          "component_bbox_area", "most_rectangles", "newly_painted_area", "select_before_fill", "first_component",
          "last_component", "smallest_color_component", "largest_color_component",
          "main_diagonal_only", "homogeneous_orientation_only", "selected_markers_only")


def rival_output(grid, name):
    if name in MODES:
        return solve(grid, {"mode": name})
    filled = _fill(grid)
    groups = components(filled)
    if name == "identity":
        return deepcopy(grid)
    if name == "largest_rectangle":
        rectangles = sorted((_box_cells(_box(p)) for p in _positions(grid).values()), key=min)
        return _keep(filled, max(rectangles, key=len))
    if name == "eight_connected":
        return _keep(filled, max(components(filled, 8), key=len))
    if name == "component_bbox_area":
        return _keep(filled, max(groups, key=lambda c: len(_box_cells(_box(c)))))
    if name == "most_rectangles":
        return _keep(filled, max(groups, key=lambda c: len({filled[r][col] for r, col in c})))
    if name == "newly_painted_area":
        return _keep(filled, max(groups, key=lambda c: sum(grid[r][col] == 0 for r, col in c)))
    if name == "select_before_fill":
        return _fill(_keep(grid, max(components(grid), key=len)))
    if name == "first_component":
        return _keep(filled, groups[0])
    if name == "last_component":
        return _keep(filled, groups[-1])
    if name in ("smallest_color_component", "largest_color_component"):
        selected_color = (min if name.startswith("smallest") else max)(_positions(grid))
        return _keep(filled, next(c for c in groups if any(filled[r][col] == selected_color for r, col in c)))
    main = lambda _color, p: sorted(p)[0][1] < sorted(p)[1][1]
    if name == "main_diagonal_only":
        return _fill(grid, main)
    if name == "homogeneous_orientation_only":
        orientations = {main(color, cells) for color, cells in _positions(grid).items()}
        return filled if len(orientations) == 1 else deepcopy(grid)
    if name == "selected_markers_only":
        return _keep(grid, max(groups, key=len))
    raise ValueError(f"undeclared rival {name!r}")


def teaching_report(episode, settings):
    mode = _settings(settings)
    errors, survivors, conflicts = [], [], []
    train, test = episode.get("train", []), episode.get("test", [])
    if not 2 <= len(train) <= 6 or not 1 <= len(test) <= 4:
        errors.append("unsupported demonstration/query count")
    for i, pair in enumerate(train + test):
        try:
            if _grid_errors(pair["output"]):
                errors.append(f"pair {i} output is not a strict ARC grid")
            elif solve(pair["input"], settings) != pair["output"]:
                errors.append(f"pair {i} has an incorrect claimed label")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"pair {i}: {exc}")
    if not errors:
        for name in RIVALS:
            if all(rival_output(p["input"], name) == p["output"] for p in train):
                survivors.append(name)
                changed = [i for i, p in enumerate(test)
                           if rival_output(p["input"], name) != p["output"]]
                if changed:
                    conflicts.append({"rival": name, "queries": changed})
        # Native settings must be unique even if an accidentally trivial query agrees.
        if [name for name in survivors if name in MODES] != [mode]:
            errors.append("demonstrations do not identify the selected declared setting")
    return {"accepted": not errors and not conflicts, "errors": errors,
            "surviving_demo_rivals": survivors, "query_conflicts": conflicts,
            "tested_rivals": list(RIVALS),
            "scope": "Finite declared rivals; no universal rule uniqueness claim."}


def _rng(seed, role, index=0, attempt=0):
    digest = hashlib.sha256(f"89c85768abe1-components-v1:{seed}:{role}:{index}:{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _transform(grid, transform):
    result = deepcopy(grid)
    if transform >= 4:
        result = [row[::-1] for row in result]
    for _ in range(transform % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _motif(kind, choice):
    # Boxes are (top, left, bottom, right, anti-diagonal-marker flag).
    # L-shaped union: first A's last row touches B's first row in one column.
    if kind in ("joined_wins", "single_wins"):
        profiles = ((2, 2, 2, 3, 3, 3), (2, 4, 2, 4, 3, 5), (3, 3, 2, 2, 3, 4))
        if kind == "single_wins":
            profiles = ((2, 3, 2, 3, 4, 4), (2, 4, 2, 4, 4, 5), (3, 3, 2, 3, 4, 5))
        ha, wa, hb, wb, hc, wc = profiles[choice % 3]
        h, w = ha + hb, wa + wb - 1
        # One blank column in D2 makes even diagonal connectivity separate C.
        # D1 retains diagonal-only contact, teaching the distinction in two demos.
        c_left = w + (kind == "single_wins")
        return [(0, 0, ha - 1, wa - 1, False),
                (ha, wa - 1, h - 1, w - 1, True),
                (h, c_left, h + hc - 1, c_left + wc - 1, False)]
    if kind == "two_boxes":
        return [(0, 0, 1, 2, True), (2, 3, 4, 6, False)]
    if kind == "four_boxes":
        fourth = ((4, 8, 5, 9, False), (7, 8, 8, 9, False), (7, 10, 8, 11, False))[choice % 3]
        return [(0, 0, 1, 2, False), (2, 2, 3, 4, True),
                (4, 5, 6, 7, False), fourth]
    raise ValueError(kind)


def _scene(seed, role, index, attempt=0):
    rng = _rng(seed, role, index, attempt)
    episode_rng = _rng(seed, "teaching")
    teaching_palette = sorted(episode_rng.sample(range(1, 10), 3))
    teaching_transform = episode_rng.randrange(8)
    if role == "demo" and index < 2:
        kind = "joined_wins" if index == 0 else "single_wins"
        boxes = _motif(kind, rng.randrange(3))
        colors, transform = teaching_palette, teaching_transform
        scale_r = scale_c = 1
        margins = (rng.randrange(3), rng.randrange(3), rng.randrange(3), rng.randrange(3))
        base_h = max(b[2] for b in boxes) + 1
        base_w = max(b[3] for b in boxes) + 1
        height = max(7, base_h + margins[0] + margins[2])
        width = max(9, base_w + margins[1] + margins[3])
        off_r, off_c = margins[:2]
    else:
        if role == "query":
            kind = ("joined_wins", "two_boxes", "four_boxes", "single_wins")[index]
            # The fourth query is actual large geometry, not a padded small scene.
            target = ((13, 16), (17, 20), (23, 26), (30, 30))[index]
        else:
            kind = ("four_boxes", "two_boxes", "joined_wins", "single_wins")[(index - 2) % 4]
            target = ((16, 19), (18, 21), (20, 24), (23, 27))[(index - 2) % 4]
        boxes = _motif(kind, rng.randrange(3))
        base_h = max(b[2] for b in boxes) + 1
        base_w = max(b[3] for b in boxes) + 1
        height, width = target
        if role == "query" and index == 3:
            scale_r, scale_c = height // base_h, width // base_w
        else:
            scale_r = rng.randint(1, max(1, height // base_h))
            scale_c = rng.randint(1, max(1, width // base_w))
        off_r = rng.randint(0, height - base_h * scale_r)
        off_c = rng.randint(0, width - base_w * scale_c)
        colors, transform = rng.sample(range(1, 10), len(boxes)), rng.randrange(8)
    grid = [[0] * width for _ in range(height)]
    for color, (r0, c0, r1, c1, anti) in zip(colors, boxes):
        top, left = off_r + r0 * scale_r, off_c + c0 * scale_c
        bottom, right = off_r + (r1 + 1) * scale_r - 1, off_c + (c1 + 1) * scale_c - 1
        grid[top][right if anti else left] = color
        grid[bottom][left if anti else right] = color
    grid = _transform(grid, transform)
    errors = validate_input(grid)
    if errors:
        raise AssertionError("constructive sampler produced invalid grid: " + "; ".join(errors))
    sizes = sorted((len(c) for c in components(_fill(grid))), reverse=True)
    if len(sizes) < 2 or sizes[0] == sizes[1]:
        raise AssertionError("sampler requires a unique largest completed component")
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _settings(settings)
    seen, splits, attempts = set(), {}, 0
    for role, count, split in (("demo", demos, "train"), ("query", queries, "test")):
        rows = []
        for index in range(count):
            for attempt in range(8):
                attempts += 1
                grid = _scene(seed, role, index, attempt)
                key = tuple(map(tuple, grid))
                if key not in seen:
                    seen.add(key)
                    rows.append({"input": grid, "output": solve(grid, settings)})
                    break
            else:
                raise RuntimeError("eight bounded attempts exhausted for a distinct input")
        splits[split] = rows
    episode = {**splits, "program_solution": program(settings),
               "private_sampler": {"attempts": attempts, "rejections": attempts - demos - queries}}
    report = teaching_report(episode, settings)
    if not report["accepted"]:
        raise RuntimeError("constructive lesson did not pass finite rivals: " + json.dumps(report))
    return episode


def public_challenge(episode):
    from reviewer_support import public_challenge_bytes
    return json.loads(public_challenge_bytes(episode))


def visible_turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge({"train": episode["train"], "test": [episode["test"][index]]})
