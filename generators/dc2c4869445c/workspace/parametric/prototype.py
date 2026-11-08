"""Canonical reflections or a second-stage selection over reflected copies.

The canonical setting returns the exact selected Racket authority and paints
all cue-directed reflected copies.  The alternate setting preserves the same
object/group/seed/reflection reasoning, but first materializes every reflected
copy, then selects the copy whose transformed bounding-box centre is nearest the
canvas centre.  Selection therefore consumes an input-dependent result of the
reflection step; choosing from the original cue positions is a declared causal
foil and is constructively refuted by the first two demonstrations.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "dc2c4869445c"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
MODES = ("all", "nearest_after_reflection")
DEFAULT_MODE = "all"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

_GENERATOR, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)

_SELECTION_RIVALS = (
    "nearest_cue_before_reflection",
    "farthest_after_reflection",
    "farthest_cue_before_reflection",
    "smallest_seed_color",
    "largest_seed_color",
    "topmost_reflection",
    "leftmost_reflection",
    "nearest_original_main",
    "first_seed_row_major",
    "diagonal_cue_only",
    "vertical_cue_only",
    "horizontal_cue_only",
    "nearest_per_group",
)
RIVALS = {
    "all": ("nearest_after_reflection",) + _SELECTION_RIVALS,
    "nearest_after_reflection": ("all_copies",) + _SELECTION_RIVALS,
}


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"copy_selection"}:
        raise ValueError("settings must contain exactly copy_selection")
    mode = settings["copy_selection"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"copy_selection must be one of {MODES}")
    return mode


def validate_grid(grid: object) -> tuple[int, int]:
    if type(grid) is not list or not 12 <= len(grid) <= 30:
        raise ValueError("grid height must be 12..30")
    if type(grid[0]) is not list or not 12 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 12..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _groups8(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    groups: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        neighbor = current[0] + dr, current[1] + dc
                        if (
                            0 <= neighbor[0] < height
                            and 0 <= neighbor[1] < width
                            and grid[neighbor[0]][neighbor[1]] != 0
                            and neighbor not in seen
                        ):
                            seen.add(neighbor)
                            stack.append(neighbor)
            groups.append(cells)
    return groups


def candidates(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Materialize every cue-directed reflected copy and its selection facts."""
    height, width = validate_grid(grid)
    result: list[dict[str, Any]] = []
    for group_index, cells in enumerate(_groups8(grid)):
        counts: dict[int, int] = {}
        for row, col in cells:
            counts[grid[row][col]] = counts.get(grid[row][col], 0) + 1
        main_color = max(counts, key=lambda color: (counts[color], -color))
        main_cells = [cell for cell in cells if grid[cell[0]][cell[1]] == main_color]
        seed_cells = [cell for cell in cells if grid[cell[0]][cell[1]] != main_color]
        if len(main_cells) < 4 or not seed_cells:
            raise ValueError("each group needs a plurality main shape and at least one cue")
        if counts[main_color] <= max(
            (count for color, count in counts.items() if color != main_color),
            default=0,
        ):
            raise ValueError("main color must be a strict plurality")
        row0 = min(row for row, _ in main_cells)
        row1 = max(row for row, _ in main_cells)
        col0 = min(col for _, col in main_cells)
        col1 = max(col for _, col in main_cells)
        main_distance = abs(row0 + row1 - (height - 1)) + abs(
            col0 + col1 - (width - 1)
        )
        for seed_row, seed_col in seed_cells:
            direction_row = -1 if seed_row < row0 else 1 if seed_row > row1 else 0
            direction_col = -1 if seed_col < col0 else 1 if seed_col > col1 else 0
            target_cells: list[tuple[int, int]] = []
            for row, col in main_cells:
                target_row = (
                    2 * row0 - 1 - row
                    if direction_row < 0
                    else 2 * row1 + 1 - row
                    if direction_row > 0
                    else row
                )
                target_col = (
                    2 * col0 - 1 - col
                    if direction_col < 0
                    else 2 * col1 + 1 - col
                    if direction_col > 0
                    else col
                )
                if not (0 <= target_row < height and 0 <= target_col < width):
                    raise ValueError("admitted parametric inputs may not clip reflected copies")
                target_cells.append((target_row, target_col))
            target_cells.sort()
            target_rows = [row for row, _ in target_cells]
            target_cols = [col for _, col in target_cells]
            reflected_distance = abs(
                min(target_rows) + max(target_rows) - (height - 1)
            ) + abs(min(target_cols) + max(target_cols) - (width - 1))
            cue_distance = abs(2 * seed_row - (height - 1)) + abs(
                2 * seed_col - (width - 1)
            )
            kind = (
                "diagonal"
                if direction_row and direction_col
                else "vertical"
                if direction_row
                else "horizontal"
            )
            result.append(
                {
                    "group": group_index,
                    "main_color": main_color,
                    "main_size": len(main_cells),
                    "main_distance": main_distance,
                    "seed": [seed_row, seed_col],
                    "color": grid[seed_row][seed_col],
                    "kind": kind,
                    "cells": [[row, col] for row, col in target_cells],
                    "reflected_distance": reflected_distance,
                    "cue_distance": cue_distance,
                    "min_row": min(target_rows),
                    "min_col": min(target_cols),
                    "max_row": max(target_rows),
                    "max_col": max(target_cols),
                }
            )
    if len(result) < 2:
        raise ValueError("parametric selection needs at least two reflected candidates")
    return result


def _selection_key(candidate: dict[str, Any], metric: str) -> tuple[Any, ...]:
    seed_row, seed_col = candidate["seed"]
    common = candidate["color"], seed_row, seed_col
    if metric == "nearest_after_reflection":
        return candidate["reflected_distance"], *common
    if metric == "nearest_cue_before_reflection":
        return candidate["cue_distance"], *common
    if metric == "farthest_after_reflection":
        return -candidate["reflected_distance"], *common
    if metric == "farthest_cue_before_reflection":
        return -candidate["cue_distance"], *common
    if metric == "smallest_seed_color":
        return candidate["color"], seed_row, seed_col
    if metric == "largest_seed_color":
        return -candidate["color"], seed_row, seed_col
    if metric == "topmost_reflection":
        return candidate["min_row"], *common
    if metric == "leftmost_reflection":
        return candidate["min_col"], *common
    if metric == "nearest_original_main":
        return candidate["main_distance"], *common
    if metric == "first_seed_row_major":
        return seed_row, seed_col, candidate["color"]
    if metric in ("diagonal_cue_only", "vertical_cue_only", "horizontal_cue_only"):
        desired = metric.split("_", 1)[0]
        return (0 if candidate["kind"] == desired else 1), candidate["color"], seed_row, seed_col
    raise ValueError(f"unknown candidate metric {metric!r}")


def winner(grid: list[list[int]], metric: str = "nearest_after_reflection") -> dict[str, Any]:
    return min(candidates(grid), key=lambda candidate: _selection_key(candidate, metric))


def _paint(grid: list[list[int]], selected: list[dict[str, Any]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    for candidate in selected:
        for row, col in candidate["cells"]:
            output[row][col] = candidate["color"]
    return output


def _output_for_metric(grid: list[list[int]], metric: str) -> list[list[int]]:
    all_candidates = candidates(grid)
    if metric == "all_copies":
        return _paint(grid, all_candidates)
    if metric == "nearest_per_group":
        selected = [
            min(
                [candidate for candidate in all_candidates if candidate["group"] == group],
                key=lambda candidate: _selection_key(candidate, "nearest_after_reflection"),
            )
            for group in sorted({candidate["group"] for candidate in all_candidates})
        ]
        return _paint(grid, selected)
    return _paint(
        grid,
        [min(all_candidates, key=lambda candidate: _selection_key(candidate, metric))],
    )


def transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return _output_for_metric(
        grid, "all_copies" if mode == "all" else "nearest_after_reflection"
    )


def rival_names(mode: str) -> tuple[str, ...]:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return RIVALS[mode]


def rival_output(grid: list[list[int]], mode: str, rival: str) -> list[list[int]]:
    if rival not in rival_names(mode):
        raise ValueError(f"undeclared rival {rival!r} for {mode}")
    metric = (
        "nearest_after_reflection"
        if mode == "all" and rival == "nearest_after_reflection"
        else "all_copies"
        if mode == "nearest_after_reflection" and rival == "all_copies"
        else rival
    )
    return _output_for_metric(grid, metric)


def _metric_primary_racket(metric: str) -> str:
    return {
        "nearest_after_reflection": "center-distance",
        "nearest_cue_before_reflection": "cue-distance",
        "farthest_after_reflection": "(- 999 center-distance)",
        "farthest_cue_before_reflection": "(- 999 cue-distance)",
        "smallest_seed_color": "scolor",
        "largest_seed_color": "(- 10 scolor)",
        "topmost_reflection": "tr1",
        "leftmost_reflection": "tc1",
        "nearest_original_main": "main-distance",
        "first_seed_row_major": "(+ (* sr 31) sc)",
        "diagonal_cue_only": "(if (and (not (eq? dir-r 'mid)) (not (eq? dir-c 'mid))) 0 1)",
        "vertical_cue_only": "(if (and (not (eq? dir-r 'mid)) (eq? dir-c 'mid)) 0 1)",
        "horizontal_cue_only": "(if (and (eq? dir-r 'mid) (not (eq? dir-c 'mid))) 0 1)",
    }[metric]


def _single_selection_program(metric: str) -> str:
    primary = _metric_primary_racket(metric)
    return f"""(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (groups (objects-multicolor g 0))
         (candidates
          (for/fold ((acc (list)))
            ((grp groups))
            (let* ((cells (obj-cells grp))
                   (cell-colors
                    (map (lambda (cell)
                           (list (first cell) (second cell)
                                 (at g (first cell) (second cell))))
                         cells))
                   (colors (remove-duplicates (map third cell-colors)))
                   (color-counts
                    (map (lambda (col)
                           (list col
                                 (count-if (lambda (cc) (= (third cc) col))
                                           cell-colors)))
                         colors))
                   (sorted (sort color-counts
                                 (lambda (a b) (> (second a) (second b)))))
                   (main-color (first (first sorted)))
                   (main-cells
                    (filter (lambda (cc) (= (third cc) main-color)) cell-colors))
                   (mrs (map first main-cells))
                   (mcs (map second main-cells))
                   (mr1 (min-list mrs)) (mr2 (max-list mrs))
                   (mc1 (min-list mcs)) (mc2 (max-list mcs))
                   (main-distance
                    (+ (abs (- (+ mr1 mr2) (- h 1)))
                       (abs (- (+ mc1 mc2) (- w 1)))))
                   (seeds (filter (lambda (cc) (!= (third cc) main-color))
                                  cell-colors)))
              (append
               acc
               (map
                (lambda (seed)
                  (let* ((sr (first seed)) (sc (second seed))
                         (scolor (third seed))
                         (dir-r (cond ((< sr mr1) 'above)
                                      ((> sr mr2) 'below)
                                      (else 'mid)))
                         (dir-c (cond ((< sc mc1) 'left)
                                      ((> sc mc2) 'right)
                                      (else 'mid)))
                         (targets
                          (map
                           (lambda (mc)
                             (let* ((mr (first mc)) (mcl (second mc))
                                    (nr (cond
                                         ((eq? dir-r 'above) (- (- (* 2 mr1) 1) mr))
                                         ((eq? dir-r 'below) (- (+ (* 2 mr2) 1) mr))
                                         (else mr)))
                                    (nc (cond
                                         ((eq? dir-c 'left) (- (- (* 2 mc1) 1) mcl))
                                         ((eq? dir-c 'right) (- (+ (* 2 mc2) 1) mcl))
                                         (else mcl))))
                               (list nr nc)))
                           main-cells))
                         (trs (map first targets)) (tcs (map second targets))
                         (tr1 (min-list trs)) (tr2 (max-list trs))
                         (tc1 (min-list tcs)) (tc2 (max-list tcs))
                         (center-distance
                          (+ (abs (- (+ tr1 tr2) (- h 1)))
                             (abs (- (+ tc1 tc2) (- w 1)))))
                         (cue-distance
                          (+ (abs (- (* 2 sr) (- h 1)))
                             (abs (- (* 2 sc) (- w 1)))))
                         (primary {primary})
                         (key (+ (* primary 100000) (* scolor 1000)
                                 (* sr 31) sc)))
                    (list key scolor targets sr sc)))
                seeds)))))
         (best
          (for/fold ((chosen (first candidates)))
            ((candidate (in-list (rest candidates))))
            (if (< (first candidate) (first chosen)) candidate chosen))))
    (for/fold ((out g))
      ((cell (in-list (third best))))
      (set-cell out (first cell) (second cell) (second best))))))"""


def _per_group_program() -> str:
    # Deliberate shortcut: reflect candidates correctly, but choose one per group
    # instead of one globally.  This is executable evidence, not an admitted rule.
    body = _single_selection_program("nearest_after_reflection")
    marker = "(candidates\n          (for/fold"
    if marker not in body:
        raise AssertionError("single-selection template changed")
    # A standalone explicit program is clearer than trying to mutate the parsed
    # candidate list after group identity has been discarded.
    return """(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g)) (groups (objects-multicolor g 0)))
    (for/fold ((out g))
      ((grp groups))
      (let* ((cells (obj-cells grp))
             (cell-colors (map (lambda (cell)
                                 (list (first cell) (second cell)
                                       (at g (first cell) (second cell)))) cells))
             (colors (remove-duplicates (map third cell-colors)))
             (color-counts (map (lambda (col)
                                  (list col (count-if (lambda (cc) (= (third cc) col))
                                                      cell-colors))) colors))
             (sorted (sort color-counts (lambda (a b) (> (second a) (second b)))))
             (main-color (first (first sorted)))
             (main-cells (filter (lambda (cc) (= (third cc) main-color)) cell-colors))
             (mrs (map first main-cells)) (mcs (map second main-cells))
             (mr1 (min-list mrs)) (mr2 (max-list mrs))
             (mc1 (min-list mcs)) (mc2 (max-list mcs))
             (seeds (filter (lambda (cc) (!= (third cc) main-color)) cell-colors))
             (candidates
              (map (lambda (seed)
                     (let* ((sr (first seed)) (sc (second seed)) (scolor (third seed))
                            (dir-r (cond ((< sr mr1) 'above) ((> sr mr2) 'below) (else 'mid)))
                            (dir-c (cond ((< sc mc1) 'left) ((> sc mc2) 'right) (else 'mid)))
                            (targets (map (lambda (mc)
                                            (let* ((mr (first mc)) (mcl (second mc))
                                                   (nr (cond ((eq? dir-r 'above) (- (- (* 2 mr1) 1) mr))
                                                             ((eq? dir-r 'below) (- (+ (* 2 mr2) 1) mr))
                                                             (else mr)))
                                                   (nc (cond ((eq? dir-c 'left) (- (- (* 2 mc1) 1) mcl))
                                                             ((eq? dir-c 'right) (- (+ (* 2 mc2) 1) mcl))
                                                             (else mcl))))
                                              (list nr nc))) main-cells))
                            (trs (map first targets)) (tcs (map second targets))
                            (distance (+ (abs (- (+ (min-list trs) (max-list trs)) (- h 1)))
                                         (abs (- (+ (min-list tcs) (max-list tcs)) (- w 1)))))
                            (key (+ (* distance 100000) (* scolor 1000) (* sr 31) sc)))
                       (list key scolor targets))) seeds))
             (best (for/fold ((chosen (first candidates)))
                     ((candidate (in-list (rest candidates))))
                     (if (< (first candidate) (first chosen)) candidate chosen))))
        (for/fold ((painted out)) ((cell (in-list (third best))))
          (set-cell painted (first cell) (second cell) (second best))))))))"""


def program(settings: object) -> str:
    mode = _mode(settings)
    return (HERE / "canonical.rkt").read_text() if mode == "all" else _single_selection_program("nearest_after_reflection")


def rival_program(mode: str, rival: str) -> str:
    if rival not in rival_names(mode):
        raise ValueError(f"undeclared rival {rival!r}")
    if mode == "all" and rival == "nearest_after_reflection":
        return _single_selection_program("nearest_after_reflection")
    if mode == "nearest_after_reflection" and rival == "all_copies":
        return (HERE / "canonical.rkt").read_text()
    if rival == "nearest_per_group":
        return _per_group_program()
    return _single_selection_program(rival)


def teaching_report(demos: object, settings: object) -> dict[str, Any]:
    mode = _mode(settings)
    if type(demos) is not list or not 2 <= len(demos) <= 6:
        raise ValueError("teaching requires 2..6 demonstrations")
    for pair in demos:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("demonstrations need input and output")
        if pair["output"] != transform(pair["input"], mode):
            raise ValueError("demonstration label disagrees with selected setting")
    refutations = {
        rival: [
            index
            for index, pair in enumerate(demos)
            if rival_output(pair["input"], mode, rival) != pair["output"]
        ]
        for rival in rival_names(mode)
    }
    survivors = [name for name, indices in refutations.items() if not indices]
    return {
        "all_refuted": not survivors,
        "surviving_rivals": survivors,
        "refutations": refutations,
        "fit_scope": "visible demonstrations only; finite declared rivals",
        "uses_query_answers": False,
    }


def causal_state(grid: list[list[int]]) -> dict[str, Any]:
    reflected = winner(grid, "nearest_after_reflection")
    cue = winner(grid, "nearest_cue_before_reflection")
    intended = _paint(grid, [reflected])
    wrong = _paint(grid, [cue])
    changed = sum(
        intended[row][col] != wrong[row][col]
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )
    return {
        "selected_reflected_seed": reflected["seed"],
        "selected_cue_seed": cue["seed"],
        "selected_reflected_distance": reflected["reflected_distance"],
        "selected_cue_distance": cue["cue_distance"],
        "changed_output_cells": changed,
        "intermediate": "all reflected candidate coordinate sets and their transformed bounding boxes",
        "wrong_intermediate": "original cue coordinates ranked before reflection",
    }


def _digest_int(text: str, bits: int = 63) -> int:
    value = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    return value & ((1 << bits) - 1)


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _admissible(grid: list[list[int]], *, groups: int, stress: bool = False) -> bool:
    try:
        facts = candidates(grid)
    except ValueError:
        return False
    if len(facts) != groups * 3:
        return False
    best_distance = min(candidate["reflected_distance"] for candidate in facts)
    if sum(candidate["reflected_distance"] == best_distance for candidate in facts) != 1:
        return False
    if transform(grid, "all") == transform(grid, "nearest_after_reflection"):
        return False
    if stress:
        occupied_rows = [row for row, values in enumerate(grid) if any(values)]
        occupied_cols = [
            col
            for col in range(len(grid[0]))
            if any(grid[row][col] for row in range(len(grid)))
        ]
        if (
            len(grid) != 30
            or len(grid[0]) != 30
            or max(occupied_rows) - min(occupied_rows) < 15
            or max(occupied_cols) - min(occupied_cols) < 10
        ):
            return False
    return True


def _draw(seed: int, stream: str, attempt: int, height: int, width: int, groups: int) -> list[list[int]]:
    generator_seed = _digest_int(f"{TASK_ID}/reflection-selection/v1/{seed}/{stream}/{attempt}/seed")
    sample_index = _digest_int(
        f"{TASK_ID}/reflection-selection/v1/{seed}/{stream}/{attempt}/index", bits=31
    )
    return _GENERATOR.generate(
        generator_seed,
        sample_index,
        difficulty="hard",
        grid_h=height,
        grid_w=width,
        n_groups=groups,
        seeds_per_group=3,
    )


def _coverage_mask(grid: list[list[int]]) -> int:
    intended = transform(grid, "nearest_after_reflection")
    return sum(
        1 << index
        for index, rival in enumerate(_SELECTION_RIVALS)
        if rival_output(grid, "nearest_after_reflection", rival) != intended
    )


def _teaching_pair(seed: int) -> tuple[list[list[int]], list[list[int]], int]:
    full = (1 << len(_SELECTION_RIVALS)) - 1
    shapes = (
        (14, 14, 2),
        (16, 20, 2),
        (20, 16, 2),
        (22, 24, 3),
        (24, 22, 3),
        (26, 28, 3),
        (28, 26, 3),
        (30, 30, 3),
    )
    retained: list[tuple[list[list[int]], int]] = []
    seen: set[str] = set()
    for attempt in range(128):
        height, width, groups = shapes[attempt % len(shapes)]
        try:
            grid = _draw(seed, "teaching", attempt, height, width, groups)
        except ValueError:
            continue
        key = _grid_key(grid)
        if key in seen or not _admissible(grid, groups=groups):
            continue
        seen.add(key)
        mask = _coverage_mask(grid)
        for old_grid, old_mask in retained:
            if old_mask | mask == full:
                return old_grid, grid, attempt + 1
        retained.append((grid, mask))
    raise RuntimeError("no joint two-demonstration rival cover in 128 candidates")


def _one_input(
    seed: int,
    stream: str,
    height: int,
    width: int,
    groups: int,
    seen: set[str],
    *,
    stress: bool = False,
) -> list[list[int]]:
    for attempt in range(128):
        try:
            grid = _draw(seed, stream, attempt, height, width, groups)
        except ValueError:
            continue
        key = _grid_key(grid)
        if key not in seen and _admissible(grid, groups=groups, stress=stress):
            seen.add(key)
            return grid
    raise RuntimeError(f"could not sample {stream} in 128 candidates")


@lru_cache(maxsize=128)
def _inputs_json(seed: int) -> str:
    first, second, attempts = _teaching_pair(seed)
    seen = {_grid_key(first), _grid_key(second)}
    demos = [first, second]
    for index, (height, width, groups) in enumerate(
        ((18, 18, 2), (20, 22, 2), (22, 20, 3), (26, 26, 3))
    ):
        demos.append(
            _one_input(seed, f"extra-demo-{index}", height, width, groups, seen)
        )
    queries = []
    for index, (height, width, groups) in enumerate(
        ((14, 18, 2), (20, 24, 2), (24, 30, 3), (30, 30, 3))
    ):
        queries.append(
            _one_input(
                seed,
                f"query-{index}",
                height,
                width,
                groups,
                seen,
                stress=index == 3,
            )
        )
    return json.dumps(
        {"demos": demos, "queries": queries, "teaching_candidates": attempts},
        separators=(",", ":"),
    )


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, *DEMO_LIMITS, "demos")
    _integer(queries, *QUERY_LIMITS, "queries")
    mode = _mode(settings)
    inputs = json.loads(_inputs_json(seed))
    train = [
        {"input": grid, "output": transform(grid, mode)}
        for grid in inputs["demos"][:demos]
    ]
    test = [
        {"input": grid, "output": transform(grid, mode)}
        for grid in inputs["queries"][:queries]
    ]
    teaching = teaching_report(train, {"copy_selection": mode})
    if not teaching["all_refuted"]:
        raise RuntimeError(f"constructive teaching contract failed: {teaching}")
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"copy_selection": mode},
        "train": train,
        "test": test,
        "program_solution": program({"copy_selection": mode}),
        "teaching": teaching,
        "teaching_candidates": inputs["teaching_candidates"],
        "source": {
            "generator": str(Path(_GENERATOR_PATH).relative_to(ROOT)),
            "generator_sha256": _GENERATOR_SHA256,
        },
        "reference": "proposed_parametric",
        "training_admitted": False,
        "label_status": "python_claims_until_protected_racket_execution",
    }


def public_turn(episode: object, index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode must contain test pairs")
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": episode["test"][index]["input"]}],
        }
    )
