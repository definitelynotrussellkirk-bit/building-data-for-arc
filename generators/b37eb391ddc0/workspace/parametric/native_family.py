"""Cue-selected diagonal-completion variants for b37eb391ddc0.

The exact canonical setting completes every adjacent same-colour diagonal pair.
The alternate setting locates the unique colour-1 cue, finds the active diagonal
pair whose doubled centre is closest to that cue, carries that pair's colour as
an intermediate, and completes every active pair of that selected colour.

Inputs are private-setting neutral, count-prefix stable, and include a dense,
distributed 30x30 query.  Python claims are independently replayed through the
selected Racket programs by native qualification.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import random
from pathlib import Path
from typing import Sequence


TASK_ID = "b37eb391ddc0"
HOME = Path(__file__).resolve().parent
SETTINGS = (
    {"completion_scope": "all_pairs"},
    {"completion_scope": "cue_selected_color"},
)
DEFAULT = {"completion_scope": "all_pairs"}
_DEMO_PROFILES = ((10, 12), (12, 15), (15, 18), (18, 21), (22, 24), (26, 28))
_QUERY_PROFILES = ((12, 14), (18, 20), (24, 26), (30, 30))
_SELECTED_COLORS = (4, 5, 3, 6, 4, 7, 5, 3, 6, 2)
_ACTIVE_COLORS = (2, 3, 4, 5, 6, 7, 8)
_DIRECTIONS = ((1, 1, "main"), (1, -1, "anti"))


def _selector_program(compare: str) -> str:
    if compare not in ("<", ">"):
        raise ValueError(compare)
    return f"""(rule! (let ((dummy 0))
  (define (colors-reading grid)
    (remove-duplicates
      (filter (lambda (v) (not (= v 0)))
              (map (lambda (p) (at grid (first p) (second p)))
                   (grid-positions grid)))))
  (define directions (list (list 1 1) (list 1 -1)))
  (define cue-cells (find-color g 1))
  (define candidates
    (for/fold ((acc '()))
              ((color (in-list (filter (lambda (v) (not (= v 1)))
                                       (colors-reading g)))))
      (let ((cells (find-color g color)))
        (for/fold ((acc2 acc)) ((p (in-list cells)))
          (for/fold ((acc3 acc2)) ((d (in-list directions)))
            (let ((q (list (+ (first p) (first d))
                           (+ (second p) (second d)))))
              (if (member? q cells)
                  (cons (list color p q) acc3)
                  acc3)))))))
  (if (or (empty? cue-cells) (empty? candidates))
      g
      (let* ((cue (first cue-cells))
             (score
               (lambda (candidate)
                 (+ (abs (- (+ (first (second candidate))
                                (first (third candidate)))
                             (* 2 (first cue))))
                    (abs (- (+ (second (second candidate))
                                (second (third candidate)))
                             (* 2 (second cue)))))))
             (selected
               (for/fold ((best (first candidates)))
                         ((candidate (in-list (rest candidates))))
                 (if ({compare} (score candidate) (score best))
                     candidate
                     best)))
             (selected-color (first selected))
             (cells (find-color g selected-color)))
        (for/fold ((out g)) ((p (in-list cells)))
          (for/fold ((acc out)) ((d (in-list directions)))
            (let ((q (list (+ (first p) (first d))
                           (+ (second p) (second d)))))
              (if (member? q cells)
                  (let* ((rs (sort (list (first p) (first q)) <))
                         (cs (sort (list (second p) (second q)) <)))
                    (for*/fold ((acc2 acc))
                               ((r (in-list rs)) (c (in-list cs)))
                      (set-cell acc2 r c selected-color)))
                  acc))))))))"""


_CUE_SELECTED_PROGRAM = _selector_program("<")
_FARTHEST_SELECTED_PROGRAM = _selector_program(">")


def _scope(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"completion_scope"}:
        raise ValueError("settings must contain exactly completion_scope")
    value = settings["completion_scope"]
    if type(value) is not str:
        raise TypeError("completion_scope must be a string")
    if value not in ("all_pairs", "cue_selected_color"):
        raise ValueError("completion_scope must be all_pairs|cue_selected_color")
    return value


def setting_name(settings: object) -> str:
    return _scope(settings)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def program(settings: object) -> str:
    if _scope(settings) == "all_pairs":
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    return _CUE_SELECTED_PROGRAM


def counterfactual_program(name: str) -> str:
    if name != "farthest_pair_color":
        raise ValueError("only farthest_pair_color is a causal counterfactual")
    return _FARTHEST_SELECTED_PROGRAM


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid dimensions must be in 1..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with literal colors 0..9")
    return deepcopy(value)


def _color_order(grid: Sequence[Sequence[int]]) -> list[int]:
    result: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in result:
                result.append(value)
    return result


def _positions(grid: Sequence[Sequence[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _matching_pairs(grid: Sequence[Sequence[int]]) -> list[dict]:
    records: list[dict] = []
    for color in _color_order(grid):
        cells = _positions(grid, color)
        cell_set = set(cells)
        for row, col in cells:
            for dr, dc, orientation in _DIRECTIONS:
                q = row + dr, col + dc
                if q in cell_set:
                    rows = sorted((row, q[0]))
                    cols = sorted((col, q[1]))
                    records.append(
                        {
                            "color": color,
                            "p": (row, col),
                            "q": q,
                            "orientation": orientation,
                            "box": tuple((rr, cc) for rr in rows for cc in cols),
                        }
                    )
    return records


def _score(record: dict, cue: tuple[int, int]) -> int:
    return abs(record["p"][0] + record["q"][0] - 2 * cue[0]) + abs(
        record["p"][1] + record["q"][1] - 2 * cue[1]
    )


def _paint(output: list[list[int]], record: dict) -> None:
    for row, col in record["box"]:
        output[row][col] = record["color"]


def _selected_record(grid: Sequence[Sequence[int]], mode: str) -> dict:
    cues = _positions(grid, 1)
    if len(cues) != 1:
        raise ValueError("scene requires exactly one color-1 cue")
    candidates = [record for record in _matching_pairs(grid) if record["color"] != 1]
    if not candidates:
        raise ValueError("scene requires an active diagonal pair")
    cue = cues[0]
    if mode == "nearest_pair_color":
        return min(candidates, key=lambda record: (_score(record, cue), candidates.index(record)))
    if mode == "farthest_pair_color":
        return max(candidates, key=lambda record: (_score(record, cue), -candidates.index(record)))
    if mode == "first_pair_color":
        return candidates[0]
    if mode == "last_pair_color":
        return candidates[-1]
    if mode == "smallest_pair_color":
        color = min(record["color"] for record in candidates)
        return next(record for record in candidates if record["color"] == color)
    if mode == "largest_pair_color":
        color = max(record["color"] for record in candidates)
        return next(record for record in candidates if record["color"] == color)
    raise ValueError(mode)


def reference_with_selector(grid: object, selector: str) -> list[list[int]]:
    source = _grid(grid)
    records = _matching_pairs(source)
    output = deepcopy(source)
    if selector == "all_pairs":
        for record in records:
            _paint(output, record)
        return output
    if selector == "nearest_pair_only":
        _paint(output, _selected_record(source, "nearest_pair_color"))
        return output
    if selector.startswith("fixed_color_"):
        selected_color = int(selector.rsplit("_", 1)[1])
    else:
        selected_color = _selected_record(source, selector)["color"]
    for record in records:
        if record["color"] == selected_color:
            _paint(output, record)
    return output


def reference(grid: object, settings: object) -> list[list[int]]:
    scope = _scope(settings)
    if scope == "all_pairs":
        return reference_with_selector(grid, "all_pairs")
    return reference_with_selector(grid, "nearest_pair_color")


def _stable_rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|cue-selected-color-v1|{seed}|{role}|{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _place_pair(
    grid: list[list[int]],
    origin: tuple[int, int],
    orientation: str,
    color: int,
    occupied_companion: bool,
) -> None:
    row, col = origin
    if orientation == "main":
        endpoints = ((row, col), (row + 1, col + 1))
        companions = ((row, col + 1), (row + 1, col))
    elif orientation == "anti":
        endpoints = ((row, col + 1), (row + 1, col))
        companions = ((row, col), (row + 1, col + 1))
    else:
        raise ValueError(orientation)
    for rr, cc in endpoints + companions:
        if grid[rr][cc] != 0:
            raise RuntimeError("motif overlap")
    for rr, cc in endpoints:
        grid[rr][cc] = color
    if occupied_companion:
        grid[companions[0][0]][companions[0][1]] = 9


def _safe_singleton(grid: list[list[int]], row: int, preferred_col: int) -> bool:
    height, width = len(grid), len(grid[0])
    for shift in range(width):
        col = (preferred_col + shift) % width
        if grid[row][col] != 0:
            continue
        for color in (9, 8, 7, 6, 5, 4, 3, 2):
            if all(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] != color
                for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
            ):
                grid[row][col] = color
                return True
    return False


def _scene(
    seed: int,
    role: str,
    index: int,
    shape: tuple[int, int],
    ordinal: int,
) -> list[list[int]]:
    height, width = shape
    if not (10 <= height <= 30 and 10 <= width <= 30):
        raise ValueError("scene dimensions must lie in 10..30")
    rng = _stable_rng(seed, role, index)
    grid = [[0] * width for _ in range(height)]
    origins = [
        (row, col)
        for row in range(1, height - 1, 3)
        for col in range(1, width - 1, 3)
        if row + 1 < height and col + 1 < width
    ]
    if len(origins) < 8:
        raise RuntimeError("profile has too few motif slots")
    anchor = origins[1]
    cue = 0, anchor[1]
    grid[cue[0]][cue[1]] = 1
    selected_color = _SELECTED_COLORS[ordinal % len(_SELECTED_COLORS)]

    def centre_score(origin: tuple[int, int]) -> int:
        return abs(2 * origin[0] + 1 - 2 * cue[0]) + abs(2 * origin[1] + 1 - 2 * cue[1])

    ordered_by_distance = sorted(origins, key=lambda origin: (centre_score(origin), origin))
    if ordered_by_distance[0] != anchor:
        raise RuntimeError("reserved anchor is not the cue-nearest pair")
    second_selected = ordered_by_distance[len(ordered_by_distance) // 2]
    farthest = ordered_by_distance[-1]
    if second_selected in (anchor, farthest):
        second_selected = ordered_by_distance[2]
    nonselected = [color for color in _ACTIVE_COLORS if color != selected_color]
    cursor = 0
    for motif_index, origin in enumerate(origins):
        if origin in (anchor, second_selected):
            color = selected_color
        else:
            color = nonselected[cursor % len(nonselected)]
            cursor += 1
        if origin == farthest and color == selected_color:
            color = nonselected[-1]
        orientation = "main" if (motif_index + ordinal) % 2 == 0 else "anti"
        _place_pair(
            grid,
            origin,
            orientation,
            color,
            occupied_companion=(motif_index % 4 == 0),
        )

    # Make large scenes visually distributed across most rows and columns without
    # introducing new same-colour diagonal pairs.
    for row in range(height):
        if not any(grid[row][col] != 0 for col in range(width)):
            if not _safe_singleton(grid, row, (row * 7 + rng.randrange(width)) % width):
                raise RuntimeError("could not place row-spread distractor")
    for col in range(width):
        if not any(grid[row][col] != 0 for row in range(height)):
            placed = False
            for row in range(height):
                if _safe_singleton(grid, row, col):
                    placed = True
                    break
            if not placed:
                raise RuntimeError("could not place column-spread distractor")

    summary = scene_summary(grid)
    if not summary["nearest_unique"]:
        raise RuntimeError("cue-nearest pair is ambiguous")
    if summary["selected_color"] != selected_color:
        raise RuntimeError("cue selected the wrong teaching color")
    if summary["selected_color_pairs"] < 2 or summary["nonselected_pairs"] < 2:
        raise RuntimeError("scene lacks global selected-color/nonselected witnesses")
    return grid


def _plan(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [
        _scene(seed, "demo", index, shape, index)
        for index, shape in enumerate(_DEMO_PROFILES)
    ]
    queries = [
        _scene(seed, "query", index, shape, len(_DEMO_PROFILES) + index)
        for index, shape in enumerate(_QUERY_PROFILES)
    ]
    return demos, queries


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    _scope(settings)
    demo_inputs, query_inputs = _plan(seed)
    return {
        "train": [
            {"input": deepcopy(grid), "output": reference(grid, settings)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": deepcopy(grid), "output": reference(grid, settings)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program(settings),
        "sampling": {
            "schema": "b37eb391ddc0-cue-selected-color-sampling-v1",
            "matched_inputs_across_settings": True,
            "prefix_stable_counts": True,
            "full_demo_count": 6,
            "full_query_count": 4,
        },
    }


def public_turn(episode: object, query_index: int = 0) -> dict:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    query_index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def scene_summary(grid: object) -> dict:
    source = _grid(grid)
    cues = _positions(source, 1)
    records = [record for record in _matching_pairs(source) if record["color"] != 1]
    cue = cues[0] if len(cues) == 1 else (-1000, -1000)
    scores = [_score(record, cue) for record in records]
    selected = records[scores.index(min(scores))] if records else None
    counts = Counter(record["color"] for record in records)
    occupied_rows = sum(any(value != 0 for value in row) for row in source)
    occupied_cols = sum(
        any(source[row][col] != 0 for row in range(len(source)))
        for col in range(len(source[0]))
    )
    selected_color = selected["color"] if selected is not None else None
    return {
        "shape": [len(source), len(source[0])],
        "cue_count": len(cues),
        "matching_pairs": len(records),
        "candidate_colors": len(counts),
        "nearest_unique": bool(scores) and scores.count(min(scores)) == 1,
        "selected_color": selected_color,
        "selected_color_pairs": counts.get(selected_color, 0),
        "nonselected_pairs": len(records) - counts.get(selected_color, 0),
        "occupied_rows": occupied_rows,
        "occupied_cols": occupied_cols,
    }


_RIVALS = (
    "all_pairs",
    "nearest_pair_color",
    "nearest_pair_only",
    "farthest_pair_color",
    "first_pair_color",
    "last_pair_color",
    "smallest_pair_color",
    "largest_pair_color",
    "fixed_color_2",
    "fixed_color_3",
    "fixed_color_4",
    "fixed_color_5",
    "fixed_color_6",
    "fixed_color_7",
    "fixed_color_8",
)


def teaching_survivors(demos: object, settings: object) -> tuple[str, ...]:
    _scope(settings)
    if type(demos) is not list or len(demos) < 2:
        raise ValueError("at least two demonstrations are required")
    survivors = []
    for name in _RIVALS:
        if all(reference_with_selector(pair["input"], name) == pair["output"] for pair in demos):
            survivors.append("cue_selected_color" if name == "nearest_pair_color" else name)
    return tuple(dict.fromkeys(survivors))
