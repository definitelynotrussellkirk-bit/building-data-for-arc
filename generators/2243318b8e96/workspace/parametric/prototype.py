"""Source-bound cue-parity family for ARC task 2243318b8e96.

The canonical ``absolute`` setting is byte-for-byte the selected Racket rule:
odd four-connected same-color objects become 3 and even objects become 8.
The two alternatives add a genuine episode-fixed, input-derived dependency:

A. locate the unique color-1 cue object and compute its size parity;
B. compare every object's size parity with that intermediate, painting matches
   3 (``same_as_cue``) or 8 (``opposite_to_cue``).

Inputs are sampled independently of the private setting.  The first two
constructive demonstrations use opposite cue parities, uniquely separating all
three settings while crossing cue-frequency rank and total-foreground parity.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
import random
from typing import Callable

TASK_ID = "2243318b8e96"
HERE = Path(__file__).resolve().parent
DEFAULT = {"parity_reference": "absolute"}
PARAMETERS = {
    "parity_reference": ["absolute", "same_as_cue", "opposite_to_cue"],
}
SETTINGS = [{"parity_reference": value} for value in PARAMETERS["parity_reference"]]

CANONICAL_PROGRAM = """(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (objects g 0)])
    (paint-cells out (obj-cells obj) (if (= (modulo (obj-size obj) 2) 1) 3 8))))"""

SAME_AS_CUE_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (cue (first (filter (lambda (obj) (= (obj-color obj) 1)) objs)))
         (cue-parity (modulo (obj-size cue) 2)))
    (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((obj objs))
      (paint-cells out (obj-cells obj)
        (if (= (modulo (obj-size obj) 2) cue-parity) 3 8))))))"""

OPPOSITE_TO_CUE_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (cue (first (filter (lambda (obj) (= (obj-color obj) 1)) objs)))
         (cue-parity (modulo (obj-size cue) 2)))
    (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((obj objs))
      (paint-cells out (obj-cells obj)
        (if (= (modulo (obj-size obj) 2) cue-parity) 8 3))))))"""

# (height, width, six object sizes).  Object 0 is the unique color-1 cue;
# objects 1 and 2 share a color and meet diagonally but not cardinally.
# The minimum two demos cross cue parity, cue frequency rank, and total parity.
_DEMO_PROFILES = (
    (10, 15, (3, 2, 5, 6, 7, 9)),   # odd cue, least frequency, even total
    (12, 18, (10, 1, 2, 4, 5, 6)),  # even cue, greatest frequency, even total
    (14, 18, (5, 1, 2, 4, 8, 10)),
    (16, 20, (6, 2, 3, 4, 9, 11)),
    (18, 22, (9, 2, 3, 4, 6, 8)),
    (20, 24, (4, 2, 3, 6, 7, 8)),
)
_QUERY_PROFILES = (
    (10, 15, (2, 3, 4, 5, 6, 7)),
    (14, 18, (11, 2, 3, 4, 8, 10)),
    (22, 24, (6, 3, 4, 7, 9, 12)),
    (30, 30, (13, 3, 4, 10, 15, 18)),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def digest(value: object) -> str:
    if isinstance(value, bytes):
        body = value
    else:
        body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"parity_reference"}:
        raise ValueError("settings must contain exactly parity_reference")
    value = settings["parity_reference"]
    if type(value) is not str or value not in PARAMETERS["parity_reference"]:
        raise ValueError("unknown parity_reference")
    return {"parity_reference": value}


def program(settings: object) -> str:
    value = _settings(settings)["parity_reference"]
    return {
        "absolute": CANONICAL_PROGRAM,
        "same_as_cue": SAME_AS_CUE_PROGRAM,
        "opposite_to_cue": OPPOSITE_TO_CUE_PROGRAM,
    }[value]


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty rectangle with 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC integers 0..9")
    return grid


def _components(grid: list[list[int]], connectivity: int = 4) -> list[dict[str, object]]:
    _grid(grid)
    h, w = len(grid), len(grid[0])
    deltas = _CARDINAL if connectivity == 4 else _CARDINAL + _DIAGONAL
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[dict[str, object]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in deltas:
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        result.append({
            "color": color,
            "cells": cells,
            "size": len(cells),
            "bbox": (min(rs), min(cs), max(rs), max(cs)),
        })
    return result


def cue_parity(grid: list[list[int]]) -> int:
    cues = [obj for obj in _components(grid) if obj["color"] == 1]
    if len(cues) != 1:
        raise ValueError(f"expected one color-1 cue object; found {len(cues)}")
    return int(cues[0]["size"]) % 2


def _paint(grid: list[list[int]], chooser: Callable[[dict[str, object]], int],
           connectivity: int = 4) -> list[list[int]]:
    out = [[0] * len(grid[0]) for _ in grid]
    for obj in _components(grid, connectivity):
        color = chooser(obj)
        for r, c in obj["cells"]:  # type: ignore[assignment]
            out[r][c] = color
    return out


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    _grid(grid)
    chosen = _settings(settings)["parity_reference"]
    if chosen == "absolute":
        return _paint(grid, lambda obj: 3 if int(obj["size"]) % 2 else 8)
    reference = cue_parity(grid)
    same_color, other_color = ((3, 8) if chosen == "same_as_cue" else (8, 3))
    return _paint(
        grid,
        lambda obj: same_color if int(obj["size"]) % 2 == reference else other_color,
    )


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(digest([TASK_ID, "cue-parity-v1", seed, domain, index]), 16))


def _snake(size: int, max_h: int, max_w: int, variant: int) -> set[tuple[int, int]]:
    if size < 1 or max_h < 1 or max_w < 1 or size > max_h * max_w:
        raise ValueError("shape does not fit region")
    target = max(2, int(math.sqrt(size)) + (variant % 2))
    widths = sorted(range(1, min(max_w, size) + 1), key=lambda x: (abs(x - target), -x))
    width = next(width for width in widths if math.ceil(size / width) <= max_h)
    cells: list[tuple[int, int]] = []
    for r in range(math.ceil(size / width)):
        columns = range(width) if r % 2 == 0 else range(width - 1, -1, -1)
        for c in columns:
            cells.append((r, c))
            if len(cells) == size:
                break
        if len(cells) == size:
            break
    shape = set(cells)
    if variant & 2:
        max_r = max(r for r, _ in shape)
        shape = {(max_r - r, c) for r, c in shape}
    if variant & 4:
        max_c = max(c for _, c in shape)
        shape = {(r, max_c - c) for r, c in shape}
    return shape


def _normalize(shape: set[tuple[int, int]]) -> set[tuple[int, int]]:
    r0 = min(r for r, _ in shape)
    c0 = min(c for _, c in shape)
    return {(r - r0, c - c0) for r, c in shape}


def _place(shape: set[tuple[int, int]], region: tuple[int, int, int, int], anchor: str) -> set[tuple[int, int]]:
    shape = _normalize(shape)
    r0, c0, r1, c1 = region
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh > r1 - r0 + 1 or sw > c1 - c0 + 1:
        raise ValueError(f"shape {sh}x{sw} does not fit region {region}")
    top = {"tl": r0, "tr": r0, "bl": r1 - sh + 1, "br": r1 - sh + 1,
           "center": r0 + (r1 - r0 + 1 - sh) // 2}[anchor]
    left = {"tl": c0, "bl": c0, "tr": c1 - sw + 1, "br": c1 - sw + 1,
            "center": c0 + (c1 - c0 + 1 - sw) // 2}[anchor]
    return {(top + r, left + c) for r, c in shape}


def _bottom_right_shape(size: int, max_h: int, max_w: int, variant: int) -> set[tuple[int, int]]:
    shape = _snake(size, max_h, max_w, variant)
    max_r = max(r for r, _ in shape)
    max_c = max(c for _, c in shape)
    # Because the snake always contains (0,0), this transformed shape contains
    # (max_r,max_c), the unique intended diagonal-contact anchor.
    return {(max_r - r, max_c - c) for r, c in shape}


def _build_scene(seed: int, domain: str, index: int,
                 spec: tuple[int, int, tuple[int, int, int, int, int, int]]) -> list[list[int]]:
    h, w, sizes = spec
    rng = _rng(seed, domain, index)
    colors = [4, 5, 6, 7, 9]
    rng.shuffle(colors)
    object_colors = [1, 2, 2, colors[0], colors[1], colors[2]]

    mid_r = h // 2
    c1, c2 = w // 3, (2 * w) // 3
    placements: list[set[tuple[int, int]]] = []

    # Cue: top/left boundary.  It is the sole color-1 object.
    region0 = (0, 0, mid_r - 2, c1 - 2)
    rh, rw = region0[2] - region0[0] + 1, region0[3] - region0[1] + 1
    placements.append(_place(_snake(sizes[0], rh, rw, index), region0, "tl"))

    # Same-color components meet exactly diagonally at A and B.  One grows only
    # up/left from A; the other only down/right from B.
    a_r, a_c = max(1, mid_r - 4), c2 - 1
    b_r, b_c = a_r + 1, a_c + 1
    shape1 = _bottom_right_shape(sizes[1], max(1, a_r + 1), max(1, a_c - c1 + 1), 0)
    sh1, sw1 = max(r for r, _ in shape1) + 1, max(c for _, c in shape1) + 1
    placements.append({(a_r - (sh1 - 1) + r, a_c - (sw1 - 1) + c) for r, c in shape1})
    max_h2 = max(1, mid_r - b_r)
    max_w2 = max(1, w - b_c)
    shape2 = _snake(sizes[2], max_h2, max_w2, 0)
    placements.append({(b_r + r, b_c + c) for r, c in shape2})

    bottom_start = mid_r + 1
    regions = (
        (bottom_start, 0, h - 1, c1 - 2),
        (bottom_start, c1, h - 1, c2 - 2),
        (bottom_start, c2, h - 1, w - 1),
    )
    anchors = ("bl", "center", "br")
    for local, (size, region, anchor) in enumerate(zip(sizes[3:], regions, anchors), start=3):
        rh, rw = region[2] - region[0] + 1, region[3] - region[1] + 1
        placements.append(_place(_snake(size, rh, rw, index + local), region, anchor))

    grid = [[0] * w for _ in range(h)]
    for cells, color in zip(placements, object_colors):
        for r, c in cells:
            if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
                raise RuntimeError("constructed placement collision/out-of-bounds")
            grid[r][c] = color

    errors = _scene_errors(grid)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    if sorted(int(obj["size"]) for obj in _components(grid)) != sorted(sizes):
        raise RuntimeError("constructed component sizes differ from profile")
    return grid


def _diagonal_component_contacts(grid: list[list[int]]) -> int:
    comps = _components(grid)
    owner: dict[tuple[int, int], int] = {}
    for index, obj in enumerate(comps):
        for cell in obj["cells"]:  # type: ignore[assignment]
            owner[cell] = index
    contacts: set[tuple[int, int]] = set()
    h, w = len(grid), len(grid[0])
    for (r, c), first in owner.items():
        for dr, dc in _DIAGONAL:
            rr, cc = r + dr, c + dc
            second = owner.get((rr, cc))
            if second is not None and second != first and grid[r][c] == grid[rr][cc]:
                contacts.add(tuple(sorted((first, second))))
    return len(contacts)


def _frequency_rank(values: list[int], cue: int) -> str:
    if cue == min(values) and values.count(cue) == 1:
        return "least"
    if cue == max(values) and values.count(cue) == 1:
        return "most"
    return "middle"


def scene_profile(grid: list[list[int]]) -> dict[str, object]:
    errors = _scene_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    comps = _components(grid)
    occupied = [cell for obj in comps for cell in obj["cells"]]  # type: ignore[misc]
    sizes = [int(obj["size"]) for obj in comps]
    cue_size = next(int(obj["size"]) for obj in comps if obj["color"] == 1)
    h, w = len(grid), len(grid[0])
    return {
        "shape": [h, w],
        "component_count": len(comps),
        "component_sizes": sorted(sizes),
        "nonzero_cells": len(occupied),
        "row_span": max(r for r, _ in occupied) - min(r for r, _ in occupied) + 1,
        "column_span": max(c for _, c in occupied) - min(c for _, c in occupied) + 1,
        "boundary_components": sum(any(r in (0, h - 1) or c in (0, w - 1)
                                           for r, c in obj["cells"]) for obj in comps),
        "diagonal_same_color_contacts": _diagonal_component_contacts(grid),
        "cue_size": cue_size,
        "cue_parity": cue_size % 2,
        "cue_frequency_rank": _frequency_rank(sizes, cue_size),
        "foreground_parity": len(occupied) % 2,
    }


def _scene_errors(grid: object) -> list[str]:
    try:
        checked = _grid(grid)
    except ValueError as exc:
        return [str(exc)]
    comps = _components(checked)
    errors: list[str] = []
    if len(comps) != 6:
        errors.append(f"expected six four-connected same-color objects; found {len(comps)}")
    cues = [obj for obj in comps if obj["color"] == 1]
    if len(cues) != 1:
        errors.append(f"expected one color-1 cue object; found {len(cues)}")
    if any(obj["color"] in (3, 8) for obj in comps):
        errors.append("input colors 3 and 8 are reserved for outputs")
    if comps and not ({0, 1} <= {int(obj["size"]) % 2 for obj in comps}):
        errors.append("scene must contain both odd- and even-sized objects")
    colors = [int(obj["color"]) for obj in comps]
    if colors.count(2) != 2:
        errors.append("expected exactly two separated color-2 objects")
    if _diagonal_component_contacts(checked) < 1:
        errors.append("expected a same-color diagonal component contact")
    return errors


def _bbox_absolute(grid: list[list[int]]) -> list[list[int]]:
    def choose(obj: dict[str, object]) -> int:
        r0, c0, r1, c1 = obj["bbox"]  # type: ignore[misc]
        return 3 if ((r1 - r0 + 1) * (c1 - c0 + 1)) % 2 else 8
    return _paint(grid, choose)


def _eight_absolute(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, lambda obj: 3 if int(obj["size"]) % 2 else 8, connectivity=8)


def _color_total_absolute(grid: list[list[int]]) -> list[list[int]]:
    totals: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value:
                totals[value] = totals.get(value, 0) + 1
    return _paint(grid, lambda obj: 3 if totals[int(obj["color"])] % 2 else 8)


def _foreground_reference(grid: list[list[int]]) -> list[list[int]]:
    reference = sum(value != 0 for row in grid for value in row) % 2
    return _paint(grid, lambda obj: 3 if int(obj["size"]) % 2 == reference else 8)


def _partial_cue_only(grid: list[list[int]]) -> list[list[int]]:
    reference = cue_parity(grid)
    out = [row[:] for row in grid]
    for obj in _components(grid):
        if obj["color"] == 1:
            color = 3 if int(obj["size"]) % 2 == reference else 8
            for r, c in obj["cells"]:  # type: ignore[assignment]
                out[r][c] = color
    return out


EXTRA_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": lambda grid: [row[:] for row in grid],
    "paint_all_3": lambda grid: _paint(grid, lambda obj: 3),
    "paint_all_8": lambda grid: _paint(grid, lambda obj: 8),
    "swapped_absolute_parity": lambda grid: _paint(grid, lambda obj: 8 if int(obj["size"]) % 2 else 3),
    "size_at_most_three": lambda grid: _paint(grid, lambda obj: 3 if int(obj["size"]) <= 3 else 8),
    "bounding_box_area_parity": _bbox_absolute,
    "eight_connected_absolute": _eight_absolute,
    "whole_color_frequency_parity": _color_total_absolute,
    "total_foreground_parity_reference": _foreground_reference,
    "recolor_only_cue": _partial_cue_only,
}


def certify(episode: dict,
            execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be a dict")
    chosen = _settings(episode.get("settings"))
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("episode must contain 2..6 demonstrations")
    if type(test) is not list or len(test) != 4:
        raise ValueError("episode must contain exactly four queries")
    seen: set[str] = set()
    for index, pair in enumerate(train + test):
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError(f"pair {index} needs input and output")
        errors = _scene_errors(pair["input"])
        if errors:
            raise ValueError(f"pair {index} invalid: {errors[0]}")
        key = digest(pair["input"])
        if key in seen:
            raise ValueError("all demonstration and query inputs must be distinct")
        seen.add(key)
        expected = transform(pair["input"], chosen)
        if pair["output"] != expected:
            raise ValueError(f"pair {index} output disagrees with selected transform")

    def apply(text: str, grid: list[list[int]]) -> list[list[int]]:
        if execute is not None:
            return execute(text, grid)
        setting = next(setting for setting in SETTINGS if program(setting) == text)
        return transform(grid, setting)

    survivors = [copy.deepcopy(setting) for setting in SETTINGS
                 if all(apply(program(setting), pair["input"]) == pair["output"] for pair in train)]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")

    rival_results = {
        name: ("survived_all" if all(rival(pair["input"]) == pair["output"] for pair in train)
               else "refuted")
        for name, rival in EXTRA_RIVALS.items()
    }
    if any(value != "refuted" for value in rival_results.values()):
        raise ValueError(f"named shortcut survived demonstrations: {rival_results}")
    return {
        "survivors": survivors,
        "rivals": rival_results,
        "cue_parities": [cue_parity(pair["input"]) for pair in train],
        "queries": [{"index": index, "input_sha256": digest(pair["input"])}
                    for index, pair in enumerate(test)],
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    chosen = _settings(DEFAULT if settings is None else settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 4, 4, "queries")
    demo_grids = [_build_scene(seed, "demo", index, spec)
                  for index, spec in enumerate(_DEMO_PROFILES)]
    query_grids = [_build_scene(seed, "query", index, spec)
                   for index, spec in enumerate(_QUERY_PROFILES)]
    train = [{"input": grid, "output": transform(grid, chosen)} for grid in demo_grids[:demos]]
    test = [{"input": grid, "output": transform(grid, chosen)} for grid in query_grids[:queries]]
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    if type(index) is not int or not 0 <= index < 4:
        raise ValueError("turn index must be an exact integer in 0..3")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode does not contain a four-query bank")
    return {
        "train": copy.deepcopy(train),
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


class RacketRunner:
    def __init__(self):
        self.bridge = None
        self.wrap = None
        self.cache: dict[str, str] = {}

    def __enter__(self):
        self.bridge = importlib.import_module("arc_repl.racket_bridge").RacketBridge(
            max_calls_before_restart=512)
        self.wrap = importlib.import_module("puzzle_generators.rule_wrap").wrap_rule
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.bridge is not None:
            self.bridge.close()
        self.bridge = None

    def __call__(self, text: str, grid: list[list[int]]) -> list[list[int]]:
        if self.bridge is None or self.wrap is None:
            raise RuntimeError("RacketRunner must be used as a context manager")
        wrapped = self.cache.setdefault(text, self.wrap(text))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({wrapped} {literal})")


def _summary(seed: int, demos: int, queries: int, all_settings: bool) -> dict:
    selected = SETTINGS if all_settings else [DEFAULT]
    episodes = [generate(seed, setting, demos, queries) for setting in selected]
    with RacketRunner() as run:
        evaluations = 0
        for episode in episodes:
            for pair in episode["train"] + episode["test"]:
                actual = run(episode["program_solution"], pair["input"])
                if actual != pair["output"]:
                    raise ValueError("protected Racket output disagrees with claimed label")
                evaluations += 1
            episode["racket_certificate"] = certify(episode, run)
    return {
        "schema": "2243318b8e96-cue-parity-evidence-v1",
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "settings": [episode["settings"] for episode in episodes],
        "episodes": episodes,
        "racket": {"backend": "racket", "protected": True, "evaluations": evaluations},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = _summary(args.seed, args.demos, args.queries, args.all_settings)
    body = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body)
    print(json.dumps({
        "status": "passed",
        "settings": len(report["settings"]),
        "racket_evaluations": report["racket"]["evaluations"],
        "receipt": str(args.out) if args.out else None,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
