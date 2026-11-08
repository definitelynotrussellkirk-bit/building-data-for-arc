"""Semantic generator for ARC task 96ebf3053dbe.

A full row of 9 is a mirror.  Each 6-bar below it has an adjacent 2 at
one endpoint, mirrored by a 5 above the line.  Erase the old 2/5 pair and
move it to the bar's opposite endpoint, recoloring that endpoint 2 and its
reflection 5.  All remaining 6 cells disappear into background 7.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "96ebf3053dbe"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "87e4b1b6db30"
SUMMARY = "Move every reflected 2/5 endpoint pair across its adjacent 6-bar, preserving the full 9 mirror row."
INVARIANTS = [
    "the grid has odd height and one central full row of color 9",
    "all ordinary background cells are color 7",
    "each 6-component below the divider is a straight bar or singleton",
    "each 6-component has exactly one adjacent color-2 endpoint marker",
    "the color-5 cells above are exactly the reflections of the color-2 markers",
]
PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "vertical_top", "vertical_bottom", "horizontal_left", "horizontal_right",
    "singleton_cycle", "mixed_sparse", "mixed_dense", "balanced",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and endpoint-transfer lessons",
        "valid": "public_1|public_2|public_3|public_4|vertical_top|vertical_bottom|horizontal_left|horizontal_right|singleton_cycle|mixed_sparse|mixed_dense|balanced",
    }
}

_PUBLIC_BLOBS = {
    "public_1": "775777777/777777777/777777775/777775777/999999999/777772777/777776762/777776777/772677777",
    "public_2": "7777577/7577777/7777777/9999999/7777777/7267677/7777277",
    "public_3": "577777757/777777777/775577777/777777777/999999999/777677777/772277767/776777767/267777727",
    "public_4": "77777775757/77777777777/77777775777/77777777777/77757777775/99999999999/77727777662/77767777777/77777772667/77777777777/77766662726",
}
_PUBLIC_INPUTS = {name: [[int(v) for v in row] for row in blob.split("/")] for name, blob in _PUBLIC_BLOBS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be ARC colors"]
    return []


def _components(grid, divider):
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(divider + 1, h):
        for c in range(w):
            if grid[r][c] != 6 or (r, c) in seen:
                continue
            todo, cells = [(r, c)], set()
            while todo:
                rr, cc = todo.pop()
                if not (divider < rr < h and 0 <= cc < w) or (rr, cc) in seen or grid[rr][cc] != 6:
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                todo.extend((rr + dr, cc + dc) for dr, dc in _DIRS)
            result.append(cells)
    return result


def _profile(records):
    orientations = [x["orientation"] for x in records]
    directions = [x["anchor_direction"] for x in records]
    if all(x == "singleton" for x in orientations):
        return "singleton_cycle"
    if all(x == "vertical" for x in orientations) and all(x == "top" for x in directions):
        return "vertical_top"
    if all(x == "vertical" for x in orientations) and all(x == "bottom" for x in directions):
        return "vertical_bottom"
    if all(x == "horizontal" for x in orientations) and all(x == "left" for x in directions):
        return "horizontal_left"
    if all(x == "horizontal" for x in orientations) and all(x == "right" for x in directions):
        return "horizontal_right"
    if len(records) == 2 and set(orientations) == {"vertical", "horizontal"}:
        return "mixed_sparse"
    if len(records) == 5:
        return "mixed_dense"
    if len(records) == 4 and set(directions) == {"top", "bottom", "left", "right"} and "singleton" not in orientations:
        return "balanced"
    return None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    dividers = [r for r, row in enumerate(grid) if all(v == 9 for v in row)]
    if len(dividers) != 1:
        errors.append("grid must have exactly one full color-9 divider row")
        return result
    divider = dividers[0]
    if h % 2 != 1 or divider != h // 2:
        errors.append("divider must be the central row of an odd-height grid")
    if any(v not in (7, 5) for row in grid[:divider] for v in row):
        errors.append("upper half may contain only background 7 and marker 5")
    if any(v not in (7, 6, 2) for row in grid[divider + 1:] for v in row):
        errors.append("lower half may contain only background 7, bars 6, and markers 2")
    if any(v == 9 for r, row in enumerate(grid) if r != divider for v in row):
        errors.append("color 9 may occur only on the divider")
    components = _components(grid, divider)
    if len(components) < 2:
        errors.append("scene must contain at least two 6-components")
    twos = {(r, c) for r in range(divider + 1, h) for c in range(w) if grid[r][c] == 2}
    fives = {(r, c) for r in range(divider) for c in range(w) if grid[r][c] == 5}
    records, used_anchors = [], set()
    for cells in components:
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if len(rows) > 1 and len(cols) > 1:
            errors.append("every 6-component must be a straight bar")
            continue
        orientation = "singleton" if len(cells) == 1 else ("vertical" if len(cols) == 1 else "horizontal")
        adjacent = {(r + dr, c + dc) for r, c in cells for dr, dc in _DIRS} & twos
        if len(adjacent) != 1:
            errors.append("each 6-component must have exactly one adjacent color-2 marker")
            continue
        anchor = next(iter(adjacent))
        if anchor in used_anchors:
            errors.append("every lower color-2 marker must anchor exactly one 6-component")
        used_anchors.add(anchor)
        minr, maxr = min(rows), max(rows)
        minc, maxc = min(cols), max(cols)
        if orientation == "vertical":
            if anchor == (minr - 1, minc):
                direction, chosen = "top", (maxr, minc)
            elif anchor == (maxr + 1, minc):
                direction, chosen = "bottom", (minr, minc)
            else:
                errors.append("vertical bar marker must extend one endpoint")
                continue
        elif orientation == "horizontal":
            if anchor == (minr, minc - 1):
                direction, chosen = "left", (minr, maxc)
            elif anchor == (minr, maxc + 1):
                direction, chosen = "right", (minr, minc)
            else:
                errors.append("horizontal bar marker must extend one endpoint")
                continue
        else:
            dr, dc = anchor[0] - minr, anchor[1] - minc
            direction = {(-1, 0): "top", (1, 0): "bottom", (0, -1): "left", (0, 1): "right"}.get((dr, dc))
            chosen = (minr, minc)
        reflected = (2 * divider - chosen[0], chosen[1])
        records.append({"cells": cells, "orientation": orientation, "anchor": anchor, "anchor_direction": direction, "chosen": chosen, "reflected": reflected})
    if used_anchors != twos:
        errors.append("every lower color-2 marker must anchor exactly one 6-component")
    expected_fives = {(2 * divider - r, c) for r, c in twos}
    if fives != expected_fives:
        errors.append("upper color-5 markers must exactly reflect lower color-2 markers")
    output = [list(row) for row in grid]
    for r in range(divider):
        for c in range(w):
            if grid[r][c] == 5:
                output[r][c] = 7
    for r in range(divider + 1, h):
        for c in range(w):
            if grid[r][c] in (2, 6):
                output[r][c] = 7
    for record in records:
        rr, cc = record["chosen"]
        output[rr][cc] = 2
        rr, cc = record["reflected"]
        if 0 <= rr < divider:
            output[rr][cc] = 5
        else:
            errors.append("chosen endpoint reflection must lie above the divider")
    signature = tuple(map(tuple, grid))
    profile = _PUBLIC_SIGNATURES.get(signature) or _profile(records)
    if profile not in SCENE_PROFILES:
        errors.append("component composition does not match a declared scene profile")
    result.update({"divider": divider, "components": components, "records": records, "twos": twos, "fives": fives, "output": output, "scene_profile": profile, "errors": errors})
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _specs(rng, profile, band):
    length_hi = {"easy": 2, "medium": 4, "hard": 6}[band]
    length = lambda: rng.randint(2, length_hi)
    if profile.startswith("vertical_"):
        direction = profile.split("_", 1)[1]
        return [("vertical", direction, length()) for _ in range(rng.randint(2, 4))]
    if profile.startswith("horizontal_"):
        direction = profile.split("_", 1)[1]
        return [("horizontal", direction, length()) for _ in range(rng.randint(2, 4))]
    if profile == "singleton_cycle":
        directions = ["top", "bottom", "left", "right"]
        rng.shuffle(directions)
        return [("singleton", directions[i % 4], 1) for i in range(rng.randint(2, 4))]
    if profile == "mixed_sparse":
        return [("vertical", rng.choice(("top", "bottom")), length()), ("horizontal", rng.choice(("left", "right")), length())]
    if profile == "mixed_dense":
        specs = [("vertical", "top", length()), ("vertical", "bottom", length()), ("horizontal", "left", length()), ("horizontal", "right", length()), ("singleton", rng.choice(("top", "bottom", "left", "right")), 1)]
        rng.shuffle(specs)
        return specs
    specs = [("vertical", "top", length()), ("vertical", "bottom", length()), ("horizontal", "left", length()), ("horizontal", "right", length())]
    rng.shuffle(specs)
    return specs


def _candidate(rng, divider, width, spec):
    orientation, direction, length = spec
    if orientation == "vertical":
        top = rng.randint(divider + 1 + (direction == "top"), 2 * divider - length - (direction == "bottom") + 1)
        col = rng.randrange(width)
        cells = {(top + i, col) for i in range(length)}
        anchor = (top - 1, col) if direction == "top" else (top + length, col)
    elif orientation == "horizontal":
        row = rng.randint(divider + 1, 2 * divider)
        left = rng.randint(1 if direction == "left" else 0, width - length - (1 if direction == "right" else 0))
        cells = {(row, left + i) for i in range(length)}
        anchor = (row, left - 1) if direction == "left" else (row, left + length)
    else:
        dr, dc = {"top": (-1, 0), "bottom": (1, 0), "left": (0, -1), "right": (0, 1)}[direction]
        row = rng.randint(divider + 1 + (direction == "top"), 2 * divider - (direction == "bottom"))
        col = rng.randint(1 if direction == "left" else 0, width - 2 if direction == "right" else width - 1)
        cells = {(row, col)}
        anchor = (row + dr, col + dc)
    return cells, anchor


def _general(rng, profile, band):
    specs = _specs(rng, profile, band)
    minimum_divider = max(5 if profile in ("mixed_dense", "balanced") or band == "hard" else 4, max(length for _, _, length in specs) + 1)
    for _ in range(120):
        divider = rng.randint(minimum_divider, 7)
        width = rng.randint(9 if len(specs) >= 4 else 7, 17)
        components, anchor_list, anchors = [], [], set()
        for spec in specs:
            placed = False
            for _ in range(600):
                cells, anchor = _candidate(rng, divider, width, spec)
                if anchor in anchors or (components and anchor in set().union(*components)):
                    continue
                if any(any(abs(r - rr) + abs(c - cc) == 1 for rr, cc in old) for r, c in cells for old in components):
                    continue
                if any(abs(anchor[0] - rr) + abs(anchor[1] - cc) == 1 for old in components for rr, cc in old):
                    continue
                if any(any(abs(ar - r) + abs(ac - c) == 1 for r, c in cells) for ar, ac in anchors):
                    continue
                components.append(cells)
                anchor_list.append(anchor)
                anchors.add(anchor)
                placed = True
                break
            if not placed:
                break
        if len(components) != len(specs):
            continue
        grid = [[7] * width for _ in range(2 * divider + 1)]
        grid[divider] = [9] * width
        for cells, anchor in zip(components, anchor_list):
            for r, c in cells:
                grid[r][c] = 6
            r, c = anchor
            grid[r][c] = 2
            grid[2 * divider - r][c] = 5
        if not _analysis(grid)["errors"]:
            return grid
    raise RuntimeError(f"could not lay out profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    profile = requested or ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) + [p for p in GENERAL_PROFILES for _ in range(4)])
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
