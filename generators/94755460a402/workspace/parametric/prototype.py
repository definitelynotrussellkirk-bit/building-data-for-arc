"""Matched command-source lessons for ARC task 94755460a402.

The canonical setting reads the transformation command from input cell ``(0,1)``.
The alternative first selects and crops the selector-colored frame, then reads the
cropped motif's top-left marker to choose the transformation.  Inputs are sampled
independently of the hidden setting; Python outputs are authoring claims that the
native worker replays through the returned Racket program.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "94755460a402"
HERE = Path(__file__).resolve().parent
SOURCES = ("header", "selected_marker")
DEFAULT = {"command_source": "header"}
ALTERNATIVE = {"command_source": "selected_marker"}

# Profile entries are fixed by split/index, while incidental geometry/palette is
# seed-dependent.  The first two demonstrations are constructive separators.
_DEMO_PROFILES = (
    dict(height=15, width=20, count=3, selected=1, duplicate=False,
         header_offset=0, marker_offset=2, selected_inset=True),
    dict(height=18, width=22, count=4, selected=0, duplicate=True,
         header_offset=3, marker_offset=1, selected_inset=True),
    dict(height=13, width=18, count=2, selected=1, duplicate=False,
         header_offset=1, marker_offset=4, selected_inset=False),
    dict(height=20, width=24, count=3, selected=2, duplicate=False,
         header_offset=4, marker_offset=1, selected_inset=True),
    dict(height=24, width=26, count=4, selected=1, duplicate=True,
         header_offset=2, marker_offset=0, selected_inset=False),
    dict(height=28, width=28, count=4, selected=3, duplicate=False,
         header_offset=0, marker_offset=3, selected_inset=True),
)
_QUERY_PROFILES = (
    dict(height=16, width=21, count=3, selected=0, duplicate=False,
         header_offset=1, marker_offset=4, selected_inset=False),
    dict(height=21, width=25, count=4, selected=2, duplicate=False,
         header_offset=4, marker_offset=0, selected_inset=True),
    dict(height=24, width=29, count=3, selected=1, duplicate=True,
         header_offset=2, marker_offset=2, selected_inset=False),
    dict(height=30, width=30, count=4, selected=0, duplicate=True,
         header_offset=0, marker_offset=3, selected_inset=False, stress=True),
)


def _setting(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"command_source"}
            or type(settings["command_source"]) is not str
            or settings["command_source"] not in SOURCES):
        raise ValueError(
            "settings must contain exactly command_source='header' or 'selected_marker'"
        )
    return settings["command_source"]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: dict[str, Any]) -> str:
    source = _setting(settings)
    name = "canonical.rkt" if source == "header" else "selected-marker.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def counterfactual_program(ablation: str) -> str:
    if ablation != "skip_a":
        raise ValueError("only the skip_a causal ablation is declared")
    return program(DEFAULT)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 2 <= len(grid[0]) <= 30):
        raise ValueError("input must be a 3..30 by 2..30 list grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("input must be rectangular with exact integer ARC colors")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                if (not 0 <= rr < height or not 0 <= cc < width
                        or (rr, cc) in seen or grid[rr][cc] != color):
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                stack.extend(((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            result.append({"color": color, "cells": cells, "bbox": (r1, c1, r2, c2)})
    return result


def _frame_cells(r1: int, c1: int, r2: int, c2: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if row in (r1, r2) or col in (c1, c2)
    }


def _crop(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        raise ValueError("frame interior must contain nonzero content")
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _apply(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 2:
        return [row[::-1] for row in grid[::-1]]
    if code == 3:
        return [row[::-1] for row in grid]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    return [row[:] for row in grid]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    selector = grid[0][0]
    header = grid[0][1]
    if selector not in range(6, 10):
        raise ValueError("selector must be a frame color in 6..9")
    if header not in range(1, 6):
        raise ValueError("header command must be in 1..5")
    frames = []
    for obj in _components(grid):
        r1, c1, r2, c2 = obj["bbox"]
        if r2 - r1 + 1 >= 3 and c2 - c1 + 1 >= 3:
            perimeter = _frame_cells(r1, c1, r2, c2)
            if obj["cells"] == perimeter:
                interior = [row[c1 + 1:c2] for row in grid[r1 + 1:r2]]
                cropped = _crop(interior)
                marker = cropped[0][0]
                if marker not in range(1, 6):
                    raise ValueError("each cropped frame motif must start with a command marker 1..5")
                frames.append({**obj, "interior": interior, "cropped": cropped, "marker": marker})
    if not 2 <= len(frames) <= 4:
        raise ValueError("scene must contain two through four exact rectangular frames")
    matching = [index for index, frame in enumerate(frames) if frame["color"] == selector]
    if not matching:
        raise ValueError("selector must match at least one frame")
    selected_index = matching[0]
    chosen = frames[selected_index]
    cropped = chosen["cropped"]
    palette = {value for row in cropped for value in row if value}
    strict_top_left = chosen["interior"][0][0]
    return {
        "height": height,
        "width": width,
        "selector": selector,
        "header_command": header,
        "frames": frames,
        "frame_count": len(frames),
        "matching_indices": matching,
        "selected_index": selected_index,
        "chosen": chosen,
        "cropped": cropped,
        "selected_marker": chosen["marker"],
        "first_frame_marker": frames[0]["marker"],
        "last_matching_marker": frames[matching[-1]]["marker"],
        "strict_interior_top_left": strict_top_left,
        "bottom_right_marker": cropped[-1][-1],
        "palette_command": ((len(palette) - 1) % 5) + 1,
    }


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    source = _setting(settings)
    info = analyze(grid)
    code = info["header_command"] if source == "header" else info["selected_marker"]
    return _apply(info["cropped"], code)


def _command_output(grid: list[list[int]], code: int) -> list[list[int]]:
    return _apply(analyze(grid)["cropped"], code)


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    info = analyze(grid)
    outputs = {
        "header": _apply(info["cropped"], info["header_command"]),
        "selected_marker": _apply(info["cropped"], info["selected_marker"]),
        "first_frame_marker": _apply(info["cropped"], info["first_frame_marker"]),
        "last_matching_marker": _apply(info["cropped"], info["last_matching_marker"]),
        "strict_interior_top_left": _apply(info["cropped"], info["strict_interior_top_left"]),
        "selected_bottom_right": _apply(info["cropped"], info["bottom_right_marker"]),
        "selected_palette_size": _apply(info["cropped"], info["palette_command"]),
        "selector_mod_five": _apply(info["cropped"], ((info["selector"] - 1) % 5) + 1),
        "header_plus_one": _apply(info["cropped"], (info["header_command"] % 5) + 1),
        "marker_plus_one": _apply(info["cropped"], (info["selected_marker"] % 5) + 1),
    }
    for code in range(1, 6):
        outputs[f"fixed_{code}"] = _apply(info["cropped"], code)
    return outputs


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    predictions = [rival_outputs(pair["input"]) for pair in train]
    names = list(predictions[0])
    survivors = [
        name for name in names
        if all(prediction[name] == pair["output"]
               for prediction, pair in zip(predictions, train))
    ]
    selected = [
        source for source in SOURCES
        if program({"command_source": source}) == episode.get("program_solution")
    ]
    query_predictions = [rival_outputs(pair["input"]) for pair in test]
    ambiguities = []
    for name in survivors:
        disagreements = [
            index for index, (prediction, pair) in enumerate(zip(query_predictions, test))
            if prediction[name] != pair["output"]
        ]
        if disagreements:
            ambiguities.append({"rival": name, "queries": disagreements})
    return {
        "ok": len(selected) == 1 and survivors == selected and not ambiguities,
        "selected": selected,
        "survivors": survivors,
        "ambiguities": ambiguities,
        "rivals_tested": len(names),
        "basis": "demonstrations_only",
        "scope": "Finite declared command-source and shortcut rivals; not universal uniqueness.",
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:command-source-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    gap = 1
    usable_h = height - 2
    upper = (usable_h - gap) // 2
    lower = usable_h - gap - upper
    left = (width - gap) // 2
    right = width - gap - left
    return [
        (2, 0, upper, left),
        (2, left + gap, upper, right),
        (2 + upper + gap, 0, lower, left),
        (2 + upper + gap, left + gap, lower, right),
    ]


def _frame_rect(slot: tuple[int, int, int, int], rng: random.Random, stress: bool) -> tuple[int, int, int, int]:
    row, col, slot_h, slot_w = slot
    if slot_h < 5 or slot_w < 6:
        raise ValueError("profile slot too small for admitted frame grammar")
    if stress:
        return row, col, row + slot_h - 1, col + slot_w - 1
    frame_h = slot_h - rng.randint(0, min(1, slot_h - 5))
    frame_w = slot_w - rng.randint(0, min(2, slot_w - 6))
    # Keep the scan order equal to the declared slot order.  Vary dimensions
    # and horizontal placement, but never let a right-hand frame begin on an
    # earlier row than its left-hand neighbor.
    top = row
    left = col + rng.randint(0, slot_w - frame_w)
    return top, left, top + frame_h - 1, left + frame_w - 1


def _paint_frame(grid: list[list[int]], bbox: tuple[int, int, int, int], color: int) -> None:
    for row, col in _frame_cells(*bbox):
        grid[row][col] = color


def _motif_dimensions(interior_h: int, interior_w: int, rng: random.Random,
                      *, stress: bool, inset: bool) -> tuple[int, int, int, int]:
    if stress:
        return interior_h, interior_w, 0, 0
    max_h = interior_h - (1 if inset and interior_h >= 4 else 0)
    max_w = interior_w - (1 if inset and interior_w >= 5 else 0)
    motif_h = max(3, max_h - rng.randint(0, min(1, max_h - 3)))
    motif_w = max(4, max_w - rng.randint(0, min(2, max_w - 4)))
    if motif_h == motif_w:
        if motif_w < max_w:
            motif_w += 1
        elif motif_w > 4:
            motif_w -= 1
        elif motif_h > 3:
            motif_h -= 1
    row_offset = 1 if inset and motif_h < interior_h else rng.randint(0, interior_h - motif_h)
    col_offset = 1 if inset and motif_w < interior_w else rng.randint(0, interior_w - motif_w)
    return motif_h, motif_w, row_offset, col_offset


def _build_motif(height: int, width: int, marker: int, rng: random.Random,
                 *, dense: bool) -> list[list[int]]:
    if not (height >= 3 and width >= 4 and height != width and marker in range(1, 6)):
        raise ValueError("motif dimensions/marker outside admitted grammar")
    anchors = [
        ((0, 0), marker),
        ((0, width - 1), (marker % 5) + 1),
        ((height - 1, 1), ((marker + 1) % 5) + 1),
        ((height - 1, width - 1), ((marker + 2) % 5) + 1),
        ((max(1, height // 2), max(1, width // 2)), ((marker + 3) % 5) + 1),
    ]
    occupied = {cell for cell, _ in anchors}
    blocked = {(height - 2, width - 1), (height - 1, width - 2)}
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in occupied | blocked
    ]
    rng.shuffle(candidates)
    target = max(len(occupied), round(height * width * (0.42 if dense else 0.28)))
    occupied.update(candidates[:max(0, target - len(occupied))])
    fixed = dict(anchors)
    motif = [[0] * width for _ in range(height)]
    for row, col in sorted(occupied):
        if (row, col) in fixed:
            value = fixed[(row, col)]
        else:
            forbidden = {
                motif[row - 1][col] if row else 0,
                motif[row][col - 1] if col else 0,
            }
            choices = [value for value in range(1, 6) if value not in forbidden]
            value = rng.choice(choices)
        motif[row][col] = value
    variants = {tuple(map(tuple, _apply(motif, code))) for code in range(1, 6)}
    if len(variants) != 5:
        raise ValueError("constructed motif does not distinguish all five transformations")
    return motif


def _scene(seed: int, split: str, index: int, profile: dict[str, Any]) -> list[list[int]]:
    rng = _rng(seed, split, index)
    height, width = profile["height"], profile["width"]
    count, selected = profile["count"], profile["selected"]
    stress = bool(profile.get("stress", False))
    grid = [[0] * width for _ in range(height)]
    base = seed % 5
    header = ((base + profile["header_offset"]) % 5) + 1
    selected_marker = ((base + profile["marker_offset"]) % 5) + 1
    if index < 2 and split == "demo" and header == selected_marker:
        raise ValueError("constructive demonstrations must separate command sources")
    frame_colors = [6, 7, 8, 9]
    rng.shuffle(frame_colors)
    frame_colors = frame_colors[:count]
    if index < 2 and split == "demo":
        # Constructively refute the shortcut that maps selector color 6..9 to
        # command 1..4.  One selected color must disagree with both lawful
        # command sources, so the same visible demonstrations teach either
        # setting without relying on a lucky seed.
        alternatives = [
            position for position, color in enumerate(frame_colors)
            if ((color - 1) % 5) + 1 not in {header, selected_marker}
        ]
        if not alternatives:
            raise ValueError("constructive demonstrations lack a separating selector color")
        position = alternatives[0]
        frame_colors[selected], frame_colors[position] = frame_colors[position], frame_colors[selected]
    if profile["duplicate"]:
        duplicate_index = count - 1
        if duplicate_index <= selected:
            raise ValueError("duplicate selector must occur after the selected frame")
        frame_colors[duplicate_index] = frame_colors[selected]
    selector = frame_colors[selected]
    grid[0][0] = selector
    grid[0][1] = header
    selected_slots = {2: (0, 3), 3: (0, 1, 3), 4: (0, 1, 2, 3)}[count]
    slot_values = [_slots(height, width)[slot_index] for slot_index in selected_slots]
    for frame_index, (slot, color) in enumerate(zip(slot_values, frame_colors)):
        bbox = _frame_rect(slot, rng, stress)
        _paint_frame(grid, bbox, color)
        r1, c1, r2, c2 = bbox
        interior_h, interior_w = r2 - r1 - 1, c2 - c1 - 1
        marker = selected_marker if frame_index == selected else (
            ((base + index + frame_index * 2 + (1 if split == "query" else 0)) % 5) + 1
        )
        if frame_index != selected and marker == selected_marker:
            marker = (marker % 5) + 1
        inset = bool(profile.get("selected_inset", False) and frame_index == selected)
        motif_h, motif_w, off_r, off_c = _motif_dimensions(
            interior_h, interior_w, rng,
            stress=stress and frame_index == selected,
            inset=inset,
        )
        motif = _build_motif(
            motif_h, motif_w, marker, rng,
            dense=stress or (frame_index + index) % 2 == 0,
        )
        for mr, row in enumerate(motif):
            for mc, value in enumerate(row):
                grid[r1 + 1 + off_r + mr][c1 + 1 + off_c + mc] = value
    info = analyze(grid)
    if (info["frame_count"] != count or info["selected_index"] != selected
            or (len(info["matching_indices"]) > 1) != profile["duplicate"]
            or info["header_command"] != header
            or info["selected_marker"] != selected_marker):
        raise ValueError("constructed scene failed its declared frame/command profile")
    return grid


def _labeled(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": solve(grid, settings)}


def generate(seed: int, settings: dict[str, Any], demos: int = 3,
             queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    _setting(settings)
    train = [
        _labeled(_scene(seed, "demo", index, _DEMO_PROFILES[index]), settings)
        for index in range(demos)
    ]
    test = [
        _labeled(_scene(seed, "query", index, _QUERY_PROFILES[index]), settings)
        for index in range(queries)
    ]
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("episode contains duplicate inputs")
    episode = {"train": train, "test": test, "program_solution": program(settings)}
    report = teaching_check(episode)
    if not report["ok"]:
        raise ValueError("constructive demonstrations did not identify the selected setting: " + repr(report))
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index outside stored controller queries")
    public = public_challenge(episode)
    return {"train": public["train"], "test": [public["test"][query_index]]}


def controller_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    return [public_turn(episode, index) for index in range(len(episode.get("test", [])))]
