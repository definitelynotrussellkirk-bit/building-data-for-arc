"""Source-bound parametric family for 204213f10aff.

The input grammar is independent of the episode-fixed ``piece_order`` setting.
Stage A decodes the sparse top-row legend and crops exactly the listed body
components.  Stage B either preserves legend order (the byte-exact canonical
rule) or stable-sorts those crops by occupied area descending before packing.
"""
from __future__ import annotations

import copy
from collections import defaultdict, deque
import hashlib
import itertools
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "204213f10aff"
PARAMETER = "piece_order"
PIECE_ORDERS = ("legend", "area_descending")
DEFAULT = {PARAMETER: "legend"}
SETTINGS = [{PARAMETER: value} for value in PIECE_ORDERS]
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERIES = 4
MAX_SEED = 2**63 - 1

_PROGRAM_FILES = {
    "legend": HERE / "canonical.rkt",
    "area_descending": HERE / "area_descending.rkt",
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Named connected footprints with deliberately crossed occupied area, bbox area,
# width, height, and density.  A/B/C are the minimum-lesson discriminator set.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "A_ring8": tuple((r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)),
    "B_dense7": tuple((r, c) for r in range(2) for c in range(4) if (r, c) != (1, 1)),
    "C_hook6": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3)),
    "D_block12": tuple((r, c) for r in range(3) for c in range(4)),
    "E_frame10": ((0, 0), (0, 1), (0, 2), (0, 3),
                  (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
    "F_stair9": ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3),
                 (2, 2), (2, 3), (2, 4)),
    "G_frame12": tuple((r, c) for r in range(4) for c in range(4)
                       if r in (0, 3) or c in (0, 3)),
    "H_t5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "I_z6": ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3)),
}

_DEMO_DIMS = ((14, 16), (15, 18), (17, 20), (19, 22), (22, 25), (25, 28))
_QUERY_DIMS = ((16, 17), (20, 21), (25, 25), (30, 30))
_SELECTED_COUNTS = {"demo": (3, 3, 4, 3, 4, 4), "query": (3, 4, 4, 4)}
_DISTRACTOR_COUNTS = {"demo": (2, 2, 2, 3, 3, 3), "query": (2, 2, 3, 3)}
_SHAPE_CYCLES = (
    ("A_ring8", "B_dense7", "C_hook6", "D_block12"),
    ("D_block12", "F_stair9", "B_dense7", "C_hook6"),
    ("E_frame10", "A_ring8", "B_dense7", "C_hook6"),
    ("G_frame12", "E_frame10", "F_stair9", "B_dense7"),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in PIECE_ORDERS:
        raise ValueError(f"{PARAMETER} must be one of {PIECE_ORDERS!r}")
    return {PARAMETER: value}


def _grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    return grid


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    raw = f"{TASK_ID}|piece-order-v1|{seed}|{domain}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return _PROGRAM_FILES[chosen[PARAMETER]].read_text(encoding="utf-8")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(shape: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    if code >= 4:
        cells = [(r, -c) for r, c in cells]
        code -= 4
    for _ in range(code):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(2, height) for c in range(width) if grid[r][c] == color}
    found: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        found.append(comp)
    return found


def _piece(grid: list[list[int]], color: int, cells: set[tuple[int, int]]) -> dict[str, Any]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top, bottom, left, right = min(rows), max(rows), min(cols), max(cols)
    crop = [row[left:right + 1] for row in grid[top:bottom + 1]]
    return {
        "color": color,
        "cells": tuple(sorted(cells)),
        "bbox": [top, left, bottom, right],
        "top": top,
        "left": left,
        "height": bottom - top + 1,
        "width": right - left + 1,
        "occupied_area": len(cells),
        "bbox_area": (bottom - top + 1) * (right - left + 1),
        "crop": crop,
    }


def analyze_scene(grid: Any) -> dict[str, Any]:
    grid = _grid(grid)
    if len(grid) < 3:
        raise ValueError("scene must contain legend, separator, and body rows")
    if any(grid[1]):
        raise ValueError("row 1 must be a blank legend/body separator")
    legend_positions = [c for c, value in enumerate(grid[0]) if value]
    legend_colors = [grid[0][c] for c in legend_positions]
    if not 2 <= len(legend_colors) <= 4:
        raise ValueError("legend must contain 2..4 colors")
    if len(set(legend_colors)) != len(legend_colors):
        raise ValueError("legend colors must be unique")

    body_colors = sorted({value for row in grid[2:] for value in row if value})
    pieces_by_color: dict[int, dict[str, Any]] = {}
    for color in body_colors:
        comps = _components(grid, color)
        if len(comps) != 1:
            raise ValueError(f"body color {color} must form exactly one component")
        pieces_by_color[color] = _piece(grid, color, comps[0])
    missing = [color for color in legend_colors if color not in pieces_by_color]
    if missing:
        raise ValueError(f"legend colors have no body component: {missing}")
    selected = [pieces_by_color[color] for color in legend_colors]
    body = sorted(pieces_by_color.values(), key=lambda p: (p["top"], p["left"], p["color"]))
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "legend_positions": legend_positions,
        "legend_colors": legend_colors,
        "body_colors": body_colors,
        "selected": selected,
        "body": body,
        "distractor_colors": sorted(set(body_colors) - set(legend_colors)),
        "spatial_colors": [p["color"] for p in sorted(selected, key=lambda p: (p["left"], p["top"]))],
        "top_down_colors": [p["color"] for p in sorted(selected, key=lambda p: (p["top"], p["left"]))],
    }


def _pack(pieces: list[dict[str, Any]], *, gap: int = 1, filled: bool = False) -> list[list[int]]:
    if not pieces:
        return [[0]]
    out_h = max(piece["height"] for piece in pieces)
    out_w = sum(piece["width"] for piece in pieces) + gap * (len(pieces) - 1)
    if not 1 <= out_h <= 30 or not 1 <= out_w <= 30:
        raise ValueError("packed output exceeds ARC bounds")
    out = [[0] * out_w for _ in range(out_h)]
    left = 0
    for piece in pieces:
        crop = piece["crop"]
        for r in range(piece["height"]):
            for c in range(piece["width"]):
                value = piece["color"] if filled else crop[r][c]
                if value:
                    out[r][left + c] = value
        left += piece["width"] + gap
    return out


def _pack_wrapped(pieces: list[dict[str, Any]], *, max_width: int = 30) -> list[list[int]]:
    """Total gallery rival: pack every piece, wrapping before ARC width 30."""
    if not pieces:
        return [[0]]
    lines: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_width = 0
    for piece in pieces:
        width = piece["width"]
        if width > max_width:
            raise ValueError("piece itself exceeds wrapped output width")
        proposed = width if not current else current_width + 1 + width
        if current and proposed > max_width:
            lines.append(current)
            current = [piece]
            current_width = width
        else:
            current.append(piece)
            current_width = proposed
    lines.append(current)
    line_heights = [max(piece["height"] for piece in line) for line in lines]
    out_h = sum(line_heights) + len(lines) - 1
    out_w = max(sum(piece["width"] for piece in line) + len(line) - 1 for line in lines)
    if out_h > 30:
        raise ValueError("wrapped rival exceeds ARC height")
    out = [[0] * out_w for _ in range(out_h)]
    top = 0
    for line, line_h in zip(lines, line_heights):
        left = 0
        for piece in line:
            for r, row in enumerate(piece["crop"]):
                for c, value in enumerate(row):
                    if value:
                        out[top + r][left + c] = value
            left += piece["width"] + 1
        top += line_h + 1
    return out


def _ordered(selected: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    if mode == "legend":
        return list(selected)
    if mode == "area_descending":
        return sorted(selected, key=lambda p: -p["occupied_area"])
    raise ValueError(f"piece order must be one of {PIECE_ORDERS!r}")


def apply_rule(grid: Any, mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in PIECE_ORDERS:
        raise ValueError(f"piece order must be one of {PIECE_ORDERS!r}")
    analysis = analyze_scene(grid)
    return _pack(_ordered(analysis["selected"], mode))


def _slot_origin(slot: str, shape: tuple[tuple[int, int], ...], h: int, w: int) -> tuple[int, int]:
    sh, sw = _dims(shape)
    rows = {"T": 2, "M": max(2, (h + 2 - sh) // 2), "B": h - sh}
    cols = {"L": 0, "C": max(0, (w - sw) // 2), "R": w - sw}
    return rows[slot[0]], cols[slot[1]]


def _paint_objects(
    h: int,
    w: int,
    objects: list[dict[str, Any]],
    slots: list[str],
    rng: random.Random,
) -> list[list[int]]:
    grid = [[0] * w for _ in range(h)]
    occupied: set[tuple[int, int]] = set()
    for index, obj in enumerate(objects):
        shape = obj["shape"]
        sh, sw = _dims(shape)
        preferred = _slot_origin(slots[index % len(slots)], shape, h, w)
        candidates = [preferred]
        others = [(r, c) for r in range(2, h - sh + 1) for c in range(0, w - sw + 1)]
        rng.shuffle(others)
        candidates.extend(others)
        chosen = None
        for r0, c0 in candidates:
            absolute = {(r0 + r, c0 + c) for r, c in shape}
            if absolute.isdisjoint(occupied):
                chosen = absolute
                break
        if chosen is None:
            raise RuntimeError("unable to place scene object")
        occupied.update(chosen)
        for r, c in chosen:
            grid[r][c] = obj["color"]
    return grid


def _valid_color_rank_order(selected_names: list[str], legend_names: list[str], rng: random.Random) -> list[str]:
    area_names = sorted(selected_names, key=lambda name: -len(_SHAPES[name]))
    candidates = list(itertools.permutations(selected_names))
    rng.shuffle(candidates)
    for candidate in candidates:
        if list(candidate) != legend_names and list(candidate) != area_names:
            return list(candidate)
    raise RuntimeError("no decisive color-rank order")


def _legend_positions(width: int, count: int, profile: int, rng: random.Random) -> list[int]:
    if profile == 0 and count == 3:
        return [0, width // 2, width - 1]
    if profile == 1 and count == 3:
        return [1, width // 2, width - 2]
    candidates = list(range(width))
    rng.shuffle(candidates)
    positions = sorted(candidates[:count])
    if positions == list(range(count)) or all(b == a + 1 for a, b in zip(positions, positions[1:])):
        positions = [round(i * (width - 1) / (count - 1)) for i in range(count)]
    return positions


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    if domain not in ("demo", "query"):
        raise ValueError("domain must be demo or query")
    dims = _DEMO_DIMS if domain == "demo" else _QUERY_DIMS
    h, w = dims[index]
    selected_count = _SELECTED_COUNTS[domain][index]
    distractor_count = _DISTRACTOR_COUNTS[domain][index]
    rng = _rng(seed, domain, index)

    if domain == "demo" and index < 2:
        selected_names = ["A_ring8", "B_dense7", "C_hook6"]
        legend_names = (["C_hook6", "A_ring8", "B_dense7"] if index == 0
                        else ["B_dense7", "C_hook6", "A_ring8"])
        color_rank_names = (["B_dense7", "A_ring8", "C_hook6"] if index == 0
                            else ["C_hook6", "A_ring8", "B_dense7"])
        transforms = {name: 0 for name in selected_names}
        if index == 1:
            transforms["C_hook6"] = 1
    else:
        cycle = list(_SHAPE_CYCLES[(index + (0 if domain == "demo" else 2)) % len(_SHAPE_CYCLES)])
        selected_names = cycle[:selected_count]
        area_names = sorted(selected_names, key=lambda name: -len(_SHAPES[name]))
        permutations = list(itertools.permutations(selected_names))
        rng.shuffle(permutations)
        legend_names = next(list(p) for p in permutations if list(p) != area_names)
        color_rank_names = _valid_color_rank_order(selected_names, legend_names, rng)
        transforms = {name: rng.randrange(8) for name in selected_names}

    distractor_pool = [name for name in _SHAPES if name not in selected_names]
    rng.shuffle(distractor_pool)
    distractor_names = distractor_pool[:distractor_count]
    all_names = selected_names + distractor_names

    palette = sorted(rng.sample(range(1, 10), len(all_names)))
    selected_palette = palette[:selected_count]
    color_by_name: dict[str, int] = {}
    for rank, name in enumerate(color_rank_names):
        color_by_name[name] = selected_palette[rank]
    for name, color in zip(distractor_names, palette[selected_count:]):
        color_by_name[name] = color

    objects: list[dict[str, Any]] = []
    for name in all_names:
        code = transforms.get(name, rng.randrange(8))
        objects.append({"name": name, "color": color_by_name[name], "shape": _transform(_SHAPES[name], code)})

    if domain == "demo" and index == 0:
        slot_by_name = {"A_ring8": "BR", "B_dense7": "TC", "C_hook6": "BL"}
        slots = [slot_by_name.get(obj["name"], slot) for obj, slot in zip(objects, ("BR", "TC", "BL", "ML", "MR"))]
    elif domain == "demo" and index == 1:
        slot_by_name = {"A_ring8": "ML", "B_dense7": "BR", "C_hook6": "TR"}
        slots = [slot_by_name.get(obj["name"], slot) for obj, slot in zip(objects, ("ML", "BR", "TR", "BL", "BC"))]
    elif domain == "query" and index == 3:
        slots = ["BL", "TR", "BR", "TL", "BC", "ML", "MR"]
    else:
        slot_pool = ["TL", "TC", "TR", "ML", "MC", "MR", "BL", "BC", "BR"]
        rng.shuffle(slot_pool)
        slots = slot_pool[:len(objects)]

    grid = _paint_objects(h, w, objects, slots, _rng(seed, domain + "-layout", index))
    legend_colors = [color_by_name[name] for name in legend_names]
    positions = _legend_positions(w, len(legend_colors), index, _rng(seed, domain + "-legend", index))
    for column, color in zip(positions, legend_colors):
        grid[0][column] = color

    analysis = analyze_scene(grid)
    if analysis["distractor_colors"] == []:
        raise RuntimeError("scene lost its unlisted-color distractor")
    if analysis["legend_positions"] == list(range(len(analysis["legend_positions"]))):
        raise RuntimeError("scene lost sparse legend semantics")
    if [p["color"] for p in _ordered(analysis["selected"], "legend")] == [
            p["color"] for p in _ordered(analysis["selected"], "area_descending")]:
        raise RuntimeError("scene does not distinguish the declared settings")
    return grid


def _rival(name: str, grid: list[list[int]], chosen_mode: str) -> list[list[int]]:
    analysis = analyze_scene(grid)
    selected = analysis["selected"]
    target = _ordered(selected, chosen_mode)
    if name == "legend_reversed":
        pieces = list(reversed(selected))
    elif name == "sorted_color":
        pieces = sorted(selected, key=lambda p: p["color"])
    elif name == "spatial_left_to_right":
        pieces = sorted(selected, key=lambda p: (p["left"], p["top"]))
    elif name == "spatial_top_to_bottom":
        pieces = sorted(selected, key=lambda p: (p["top"], p["left"]))
    elif name == "all_body_objects":
        pieces = sorted(analysis["body"], key=lambda p: (p["left"], p["top"]))
        return _pack_wrapped(pieces)
    elif name == "area_ascending":
        pieces = sorted(selected, key=lambda p: p["occupied_area"])
    elif name == "bbox_area_descending":
        pieces = sorted(selected, key=lambda p: -p["bbox_area"])
    elif name == "bbox_area_ascending":
        pieces = sorted(selected, key=lambda p: p["bbox_area"])
    elif name == "width_descending":
        pieces = sorted(selected, key=lambda p: -p["width"])
    elif name == "height_descending":
        pieces = sorted(selected, key=lambda p: -p["height"])
    elif name == "contiguous_left_prefix_legend":
        colors: list[int] = []
        for value in grid[0]:
            if value == 0:
                break
            colors.append(value)
        by_color = {piece["color"]: piece for piece in analysis["body"]}
        pieces = [by_color[color] for color in colors if color in by_color]
    elif name == "filled_bbox":
        return _pack(target, filled=True)
    elif name == "no_gap":
        return _pack(target, gap=0)
    elif name == "first_two_only":
        return _pack(target[:2])
    else:
        raise KeyError(name)
    return _pack(pieces)


RIVALS = (
    "legend_reversed",
    "sorted_color",
    "spatial_left_to_right",
    "spatial_top_to_bottom",
    "all_body_objects",
    "area_ascending",
    "bbox_area_descending",
    "bbox_area_ascending",
    "width_descending",
    "height_descending",
    "contiguous_left_prefix_legend",
    "filled_bbox",
    "no_gap",
    "first_two_only",
)


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    chosen = _settings(episode.get("settings"))
    chosen_mode = chosen[PARAMETER]
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program_solution does not match episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(len(train), MIN_DEMOS, MAX_DEMOS, "demos")
    if type(len(test)) is not int or len(test) != QUERIES:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    if any(type(pair) is not dict or set(pair) != {"input", "output"} for pair in pairs):
        raise ValueError("every pair must contain exactly input and output")
    for pair in pairs:
        _grid(pair["input"])
        _grid(pair["output"])
        analyze_scene(pair["input"])
    input_digests = [digest(pair["input"]) for pair in pairs]
    if len(set(input_digests)) != len(input_digests):
        raise ValueError("all demonstration and query inputs must be distinct")

    def apply_setting(mode: str, grid: list[list[int]]) -> list[list[int]]:
        return (execute(program({PARAMETER: mode}), grid) if execute is not None
                else apply_rule(grid, mode))

    setting_refutations: dict[str, list[int]] = {}
    survivors: list[dict[str, str]] = []
    for mode in PIECE_ORDERS:
        disagree = [i for i, pair in enumerate(train)
                    if apply_setting(mode, pair["input"]) != pair["output"]]
        setting_refutations[mode] = disagree
        if not disagree:
            survivors.append({PARAMETER: mode})
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the selected setting: {survivors}")

    for pair in pairs:
        if apply_setting(chosen_mode, pair["input"]) != pair["output"]:
            raise ValueError("label disagrees with fixed episode setting")

    rival_refutations: dict[str, list[int]] = {}
    rival_survivors: list[str] = []
    for name in RIVALS:
        disagree = [i for i, pair in enumerate(train)
                    if _rival(name, pair["input"], chosen_mode) != pair["output"]]
        rival_refutations[name] = disagree
        if not disagree:
            rival_survivors.append(name)
    if rival_survivors:
        raise ValueError(f"named shortcut rivals survive the minimum lesson: {rival_survivors}")

    computed = {
        "scope": "two declared piece orders plus fourteen finite shortcut/order/content rivals",
        "racket_checked": execute is not None,
        "setting_survivors": survivors,
        "rival_survivors": rival_survivors,
        "rejected_rivals": list(RIVALS),
        "setting_refutations": setting_refutations,
        "rival_refutations": rival_refutations,
        "queries": [{"input_sha256": digest(pair["input"]),
                     "output_sha256": digest(pair["output"])} for pair in test],
    }
    supplied = episode.get("certificate")
    if supplied is not None and supplied != computed:
        raise ValueError("certificate mismatch: supplied certificate does not recompute")
    return computed


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, MAX_SEED, "seed")
    _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    if type(queries) is not int:
        raise TypeError("queries must be the exact integer 4 (bool is forbidden)")
    if queries != QUERIES:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(settings)
    mode = chosen[PARAMETER]
    train = []
    for index in range(demos):
        grid = _scene(seed, "demo", index)
        train.append({"input": grid, "output": apply_rule(grid, mode)})
    test = []
    for index in range(QUERIES):
        grid = _scene(seed, "query", index)
        test.append({"input": grid, "output": apply_rule(grid, mode)})
    source = program(chosen)
    episode = {
        "schema": "204213f10aff-piece-order-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": source,
        "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    _integer(index, 0, QUERIES - 1, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERIES:
        raise ValueError("episode must retain exactly four controller-side queries")
    return {
        "train": [{"input": copy.deepcopy(pair["input"]),
                   "output": copy.deepcopy(pair["output"])} for pair in train],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


class RacketRunner:
    """One live protected Racket bridge for bounded source/evidence checks."""
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule
        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json",
             HERE / "canonical.rkt", HERE / "area_descending.rkt",
             HERE.parents[1] / "generator.py", REPO / "shared/data/canonical/puzzles.jsonl"]
    return {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}
