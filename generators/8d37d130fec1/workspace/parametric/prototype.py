"""Candidate-order parametric family for ARC task 8d37d130fec1.

Stage A discovers the ordered glyphs compatible with sparse evidence inside the
frame. Stage B selects the first or last compatible glyph, then expands that
mask blockwise into the framed output. Inputs are matched across settings.
Python labels are claims until native qualification re-executes them in Racket.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "8d37d130fec1"
CHOICES = ("first", "last")

_CANONICAL_SELECTOR = """(define glyph
               (first (sort-by candidates
                               (lambda (obj) (+ (* 1000 (obj-r1 obj)) (obj-c1 obj))))))"""
_LAST_SELECTOR = """(define glyph
               (last (sort-by candidates
                              (lambda (obj) (+ (* 1000 (obj-r1 obj)) (obj-c1 obj))))))"""
_GLOBAL_LAST_SELECTOR = """(define glyph
               (last (sort-by top-glyphs
                              (lambda (obj) (+ (* 1000 (obj-r1 obj)) (obj-c1 obj))))))"""


def _choice(settings):
    if (type(settings) is not dict or set(settings) != {"candidate_choice"}
            or type(settings["candidate_choice"]) is not str
            or settings["candidate_choice"] not in CHOICES):
        raise ValueError("settings must be exactly {'candidate_choice': 'first'|'last'}")
    return settings["candidate_choice"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _canonical():
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


def _replace_selector(source, replacement):
    if source.count(_CANONICAL_SELECTOR) != 1:
        raise ValueError("canonical selector marker is not unique")
    return source.replace(_CANONICAL_SELECTOR, replacement)


def program(settings):
    choice = _choice(settings)
    source = _canonical()
    return source if choice == "first" else _replace_selector(source, _LAST_SELECTOR)


def counterfactual_program(name="skip_candidate_filter_last"):
    if name != "skip_candidate_filter_last":
        raise ValueError(f"unknown counterfactual {name!r}")
    return _replace_selector(_canonical(), _GLOBAL_LAST_SELECTOR)


def _grid_errors(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30):
        return ["expected a 1..30 by 1..30 list grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        return ["grid must be rectangular with exact integer colors 0..9"]
    return []


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _components(grid, diagonal=False):
    height, width = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, result = set(), []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 8 or (r, c) in seen:
                continue
            todo, cells = [(r, c)], set()
            while todo:
                rr, cc = todo.pop()
                if ((rr, cc) in seen or not (0 <= rr < height and 0 <= cc < width)
                        or grid[rr][cc] != color):
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                todo.extend((rr + dr, cc + dc) for dr, dc in directions)
            if cells:
                result.append({"color": color, "cells": cells, "bbox": _bbox(cells)})
    return sorted(result, key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"]))


def _frame_cells(r0, c0, r1, c1):
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)}


def _mask(obj):
    r0, c0, r1, c1 = obj["bbox"]
    return tuple("".join("1" if (r, c) in obj["cells"] else "0"
                         for c in range(c0, c1 + 1))
                 for r in range(r0, r1 + 1))


def _render(frame_color, fill_color, mask, block_shape):
    bh, bw = block_shape
    inner_h, inner_w = len(mask) * bh, len(mask[0]) * bw
    output = []
    for r in range(inner_h + 2):
        row = []
        for c in range(inner_w + 2):
            if r in (0, inner_h + 1) or c in (0, inner_w + 1):
                row.append(frame_color)
            elif mask[(r - 1) // bh][(c - 1) // bw] == "1":
                row.append(fill_color)
            else:
                row.append(8)
        output.append(row)
    return output


def analyze(grid):
    errors = _grid_errors(grid)
    result = {"errors": errors}
    if errors:
        return result
    objects4 = _components(grid, diagonal=False)
    if not objects4:
        return {"errors": ["missing foreground objects"]}
    frame = max(objects4, key=lambda obj: len(obj["cells"]))
    fr0, fc0, fr1, fc1 = frame["bbox"]
    if frame["cells"] != _frame_cells(fr0, fc0, fr1, fc1):
        return {"errors": ["largest object is not an exact rectangular frame"]}
    frame_color = frame["color"]
    inner_h, inner_w = fr1 - fr0 - 1, fc1 - fc0 - 1
    if inner_h <= 0 or inner_w <= 0:
        return {"errors": ["frame has no interior"]}
    fill_values = [grid[r][c] for r in range(fr0 + 1, fr1) for c in range(fc0 + 1, fc1)
                   if grid[r][c] not in (8, frame_color)]
    if not fill_values:
        return {"errors": ["frame has no evidence"]}
    fill_color = Counter(fill_values).most_common(1)[0][0]
    if set(fill_values) != {fill_color}:
        errors.append("interior evidence uses more than one color")
    evidence = [(r - fr0 - 1, c - fc0 - 1)
                for r in range(fr0 + 1, fr1) for c in range(fc0 + 1, fc1)
                if grid[r][c] == fill_color]
    glyphs = []
    for obj in _components(grid, diagonal=True):
        if (obj["bbox"][2] < fr0 and obj["color"] not in (8, frame_color, fill_color)):
            glyph = dict(obj)
            glyph["mask"] = _mask(obj)
            glyphs.append(glyph)
    glyphs.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    candidates = []
    for index, glyph in enumerate(glyphs):
        mask = glyph["mask"]
        gh, gw = len(mask), len(mask[0])
        if inner_h % gh or inner_w % gw:
            continue
        bh, bw = inner_h // gh, inner_w // gw
        if all(mask[rr // bh][cc // bw] == "1" for rr, cc in evidence):
            candidates.append((index, glyph, bh, bw))
    if not candidates:
        errors.append("no glyph is compatible with the evidence")
        return {"errors": errors, "top_glyphs": glyphs}
    candidate_masks = [glyph["mask"] for _index, glyph, _bh, _bw in candidates]
    result.update({
        "errors": errors,
        "frame": frame,
        "frame_bbox": frame["bbox"],
        "frame_color": frame_color,
        "fill_color": fill_color,
        "inner_shape": (inner_h, inner_w),
        "evidence": evidence,
        "top_glyphs": glyphs,
        "candidate_indices": tuple(item[0] for item in candidates),
        "candidate_masks": tuple(candidate_masks),
        "candidate_areas": tuple(sum(row.count("1") for row in mask) for mask in candidate_masks),
        "candidate_colors": tuple(item[1]["color"] for item in candidates),
        "candidates": candidates,
    })
    return result


def _output_for_glyph(facts, glyph):
    mask = glyph["mask"]
    inner_h, inner_w = facts["inner_shape"]
    if inner_h % len(mask) or inner_w % len(mask[0]):
        raise ValueError("selected glyph dimensions do not divide the frame interior")
    return _render(facts["frame_color"], facts["fill_color"], mask,
                   (inner_h // len(mask), inner_w // len(mask[0])))


def solve(grid, settings):
    choice = _choice(settings)
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    item = facts["candidates"][0 if choice == "first" else -1]
    return _output_for_glyph(facts, item[1])


RIVALS = (
    "first", "last", "global_first", "global_last", "largest_candidate",
    "smallest_candidate", "min_color_candidate", "max_color_candidate",
    "largest_global", "smallest_global", "fixed_index_0", "fixed_index_1",
    "fixed_index_2", "fixed_index_3", "fixed_index_4", "intersection",
    "union", "frame_parity", "fill_parity",
)


def _candidate_by(facts, key, reverse=False):
    ordered = sorted(facts["candidates"], key=key, reverse=reverse)
    return ordered[0][1]


def _logical_mask(cells, height, width):
    return tuple("".join("1" if (r, c) in cells else "0" for c in range(width))
                 for r in range(height))


def rival_output(grid, name):
    if name in CHOICES:
        return solve(grid, {"candidate_choice": name})
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    glyphs, candidates = facts["top_glyphs"], facts["candidates"]
    if name == "global_first":
        glyph = glyphs[0]
    elif name == "global_last":
        glyph = glyphs[-1]
    elif name == "largest_candidate":
        glyph = _candidate_by(facts, lambda item: (-len(item[1]["cells"]), item[0]))
    elif name == "smallest_candidate":
        glyph = _candidate_by(facts, lambda item: (len(item[1]["cells"]), item[0]))
    elif name == "min_color_candidate":
        glyph = _candidate_by(facts, lambda item: (item[1]["color"], item[0]))
    elif name == "max_color_candidate":
        glyph = _candidate_by(facts, lambda item: (-item[1]["color"], item[0]))
    elif name == "largest_global":
        glyph = sorted(glyphs, key=lambda item: (-len(item["cells"]), item["bbox"][:2]))[0]
    elif name == "smallest_global":
        glyph = sorted(glyphs, key=lambda item: (len(item["cells"]), item["bbox"][:2]))[0]
    elif name.startswith("fixed_index_"):
        index = int(name.rsplit("_", 1)[1])
        glyph = glyphs[min(index, len(glyphs) - 1)]
    elif name in ("intersection", "union"):
        masks = facts["candidate_masks"]
        sets = [{(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value == "1"}
                for mask in masks]
        cells = (set.intersection if name == "intersection" else set.union)(*sets)
        mask = _logical_mask(cells, len(masks[0]), len(masks[0][0]))
        return _render(facts["frame_color"], facts["fill_color"], mask,
                       (facts["inner_shape"][0] // len(mask), facts["inner_shape"][1] // len(mask[0])))
    elif name == "frame_parity":
        glyph = candidates[0 if facts["frame_color"] % 2 == 0 else -1][1]
    elif name == "fill_parity":
        glyph = candidates[0 if facts["fill_color"] % 2 == 0 else -1][1]
    else:
        raise ValueError(f"undeclared rival {name!r}")
    return _output_for_glyph(facts, glyph)


def teaching_report(episode, settings):
    choice = _choice(settings)
    errors, survivors, conflicts = [], [], []
    train, test = episode.get("train", []), episode.get("test", [])
    if not 2 <= len(train) <= 6 or not 1 <= len(test) <= 4:
        errors.append("unsupported demonstration/query count")
    for index, pair in enumerate(train + test):
        try:
            if solve(pair["input"], settings) != pair["output"]:
                errors.append(f"pair {index} has an incorrect claimed label")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"pair {index}: {exc}")
    if not errors:
        for name in RIVALS:
            if all(rival_output(pair["input"], name) == pair["output"] for pair in train):
                survivors.append(name)
                changed = [index for index, pair in enumerate(test)
                           if rival_output(pair["input"], name) != pair["output"]]
                if changed:
                    conflicts.append({"rival": name, "queries": changed})
    declared = [name for name in survivors if name in CHOICES]
    if not errors and declared != [choice]:
        errors.append("demonstrations do not uniquely identify the declared setting")
    return {
        "accepted": not errors and not conflicts,
        "errors": errors,
        "declared_survivors": declared,
        "surviving_demo_rivals": survivors,
        "query_conflicts": conflicts,
        "tested_rivals": list(RIVALS),
        "scope": "Finite declared rivals only; no universal uniqueness claim.",
    }


def _connected(cells, height, width, diagonal):
    if not cells:
        return False
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    todo, seen = [next(iter(cells))], set()
    while todo:
        cell = todo.pop()
        if cell in seen or cell not in cells:
            continue
        seen.add(cell)
        r, c = cell
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                todo.append((rr, cc))
    return seen == cells


@lru_cache(maxsize=None)
def _mask_pool(height, width):
    masks = []
    for bits in range(1, 1 << (height * width)):
        cells = {(index // width, index % width) for index in range(height * width)
                 if bits & (1 << index)}
        if (not (3 <= len(cells) < height * width)
                or not _connected(cells, height, width, diagonal=True)
                or not any(r == 0 for r, _ in cells)
                or not any(r == height - 1 for r, _ in cells)
                or not any(c == 0 for _, c in cells)
                or not any(c == width - 1 for _, c in cells)):
            continue
        masks.append(frozenset(cells))
    return tuple(masks)


_PROFILE = {
    ("demo", 0): (15, 20, 3, 3, 2, 3, 5, (1, 3), "first_larger", "ascending", 6),
    ("demo", 1): (17, 23, 3, 4, 3, 3, 4, (0, 2), "first_smaller", "descending", 5),
    ("demo", 2): (19, 25, 4, 3, 3, 4, 5, (2, 4), "equal", "ascending", 5),
    ("demo", 3): (22, 27, 3, 3, 5, 5, 4, (1, 3), "first_larger", "descending", 5),
    ("demo", 4): (24, 29, 3, 4, 5, 5, 5, (0, 3), "first_smaller", "ascending", 6),
    ("demo", 5): (26, 30, 4, 3, 4, 6, 5, (1, 4), "equal", "descending", 6),
    ("query", 0): (14, 18, 3, 3, 2, 3, 4, (1, 2), "first_smaller", "descending", 5),
    ("query", 1): (18, 23, 3, 4, 3, 4, 4, (0, 2), "first_larger", "ascending", 6),
    ("query", 2): (24, 28, 4, 3, 4, 6, 5, (2, 4), "equal", "descending", 5),
    ("query", 3): (30, 30, 3, 3, 7, 7, 5, (1, 3), "first_smaller", "ascending", 7),
}


def _rng(seed, role, index, stream="scene"):
    digest = hashlib.sha256(f"{TASK_ID}-candidate-choice-v1:{seed}:{role}:{index}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _area_relation(a, b, relation):
    if relation == "first_larger":
        return len(a) > len(b)
    if relation == "first_smaller":
        return len(a) < len(b)
    if relation == "equal":
        return len(a) == len(b)
    raise ValueError(relation)


@lru_cache(maxsize=None)
def _pick_masks(seed, role, index, height, width, glyph_count, relation):
    rng = _rng(seed, role, index, "masks")
    pool = list(_mask_pool(height, width))
    for _ in range(2000):
        first, last = rng.sample(pool, 2)
        shared = first & last
        if (not _area_relation(first, last, relation) or not 2 <= len(shared) <= 5
                or not first - shared or not last - shared):
            continue
        # At least one compatible glyph uses diagonal-only connectivity in some
        # scenes, preserving the canonical objects-8 branch.
        if index % 2 == 0 and _connected(first, height, width, False) and _connected(last, height, width, False):
            continue
        decoys = [mask for mask in pool if mask not in (first, last) and not shared <= mask]
        if len(decoys) < glyph_count - 2:
            continue
        rng.shuffle(decoys)
        return first, last, tuple(decoys[:glyph_count - 2]), tuple(sorted(shared))
    raise RuntimeError("bounded mask search exhausted")


def _mask_text(cells, height, width):
    return tuple("".join("1" if (r, c) in cells else "0" for c in range(width))
                 for r in range(height))


def _draw_mask(grid, top, left, cells, color):
    for r, c in cells:
        grid[top + r][left + c] = color


def _scene(seed, role, index):
    spec = _PROFILE[(role, index)]
    height, width, gh, gw, bh, bw, glyph_count, candidate_positions, relation, color_order, frame_top = spec
    rng = _rng(seed, role, index)
    first, last, decoys, clues = _pick_masks(seed, role, index, gh, gw, glyph_count, relation)
    masks, decoy_index = [], 0
    for position in range(glyph_count):
        if position == candidate_positions[0]:
            masks.append(first)
        elif position == candidate_positions[1]:
            masks.append(last)
        else:
            masks.append(decoys[decoy_index])
            decoy_index += 1

    span = glyph_count * gw + (glyph_count - 1)
    glyph_left = rng.randint(0, width - span)
    frame_h, frame_w = gh * bh + 2, gw * bw + 2
    if frame_top + frame_h > height:
        raise AssertionError("profile frame does not fit")
    frame_left = rng.randint(0, width - frame_w)
    grid = [[8] * width for _ in range(height)]
    colors = (0, 1, 2, 3, 4, 5, 6, 7, 9)
    if role == "demo" and index < 2:
        # Demo 0 uses even frame/fill colors and demo 1 uses odd colors.
        # This constructively defeats frame/fill-parity selection shortcuts for
        # both declared settings within the minimum two demonstrations.
        parity = index % 2
        matching = [value for value in colors if value % 2 == parity]
        frame_color, fill_color = rng.sample(matching, 2)
        glyph_colors = rng.sample([value for value in colors
                                   if value not in (frame_color, fill_color)], glyph_count)
    else:
        palette = rng.sample(colors, glyph_count + 2)
        frame_color, fill_color = palette[:2]
        glyph_colors = palette[2:]
    left_pos, right_pos = candidate_positions
    if ((color_order == "ascending" and glyph_colors[left_pos] > glyph_colors[right_pos])
            or (color_order == "descending" and glyph_colors[left_pos] < glyph_colors[right_pos])):
        glyph_colors[left_pos], glyph_colors[right_pos] = glyph_colors[right_pos], glyph_colors[left_pos]
    for position, (mask, color) in enumerate(zip(masks, glyph_colors)):
        _draw_mask(grid, 1, glyph_left + position * (gw + 1), mask, color)

    fr0, fc0 = frame_top, frame_left
    fr1, fc1 = fr0 + frame_h - 1, fc0 + frame_w - 1
    for r, c in _frame_cells(fr0, fc0, fr1, fc1):
        grid[r][c] = frame_color
    for logical_r, logical_c in clues:
        rr = fr0 + 1 + logical_r * bh + rng.randrange(bh)
        cc = fc0 + 1 + logical_c * bw + rng.randrange(bw)
        grid[rr][cc] = fill_color

    facts = analyze(grid)
    if facts["errors"]:
        raise AssertionError("constructive scene invalid: " + "; ".join(facts["errors"]))
    if facts["candidate_indices"] != candidate_positions:
        raise AssertionError(f"candidate construction drift: {facts['candidate_indices']} != {candidate_positions}")
    if role == "query" and index == 3 and (height, width) != (30, 30):
        raise AssertionError("fourth query must remain exact 30x30")
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _choice(settings)
    seen, splits = set(), {}
    for role, count, split in (("demo", demos, "train"), ("query", queries, "test")):
        rows = []
        for index in range(count):
            grid = _scene(seed, role, index)
            key = tuple(map(tuple, grid))
            if key in seen:
                raise RuntimeError("constructive scene schedule produced a duplicate input")
            seen.add(key)
            rows.append({"input": grid, "output": solve(grid, settings)})
        splits[split] = rows
    episode = {**splits, "program_solution": program(settings),
               "private_sampler": {"version": 1, "candidate_choice": _choice(settings)}}
    report = teaching_report(episode, settings)
    if not report["accepted"]:
        raise RuntimeError("constructive lesson failed finite audit: " + json.dumps(report, sort_keys=True))
    return episode


def public_challenge(episode):
    from reviewer_support import public_challenge_bytes
    return json.loads(public_challenge_bytes(episode))


def visible_turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge({"train": episode["train"], "test": [episode["test"][index]]})
