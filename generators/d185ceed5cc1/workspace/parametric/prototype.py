"""Native matched-input parametric family for ``d185ceed5cc1``.

``all_right`` is the byte-identical selected canonical Racket rule.  The
nearby ``densest_left`` setting keeps the same color-8 segmentation and stable
pebble order, but performs a real two-stage decision on every row:

1. split the row into maximal non-wall segments and count the pebbles in each;
2. select the unique count-argmax segment and pack it left, while packing every
   other segment right.

The task-local sampler constructively makes the argmax unique and makes a
wider distractor disagree with it.  Python outputs are deterministic claims;
native qualification re-executes every retained label in protected Racket.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "d185ceed5cc1"
CANONICAL_PROGRAM_SHA256 = "a1ebff603893a7911dd0126809628107bf218b68ce2a907a411354b0c9b4cfa5"
PACKING_RULES = ("all_right", "densest_left")
SETTINGS = (
    {"packing_rule": "all_right"},
    {"packing_rule": "densest_left"},
)
DEFAULT_SETTINGS = SETTINGS[0]
Grid = list[list[int]]


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    segments: int
    allow_odd_row_total: bool = False


# Prefix-stable curricula.  The first two demonstrations are sufficient to
# distinguish the settings and jointly expose both even and odd row totals.
DEMO_PROFILES = (
    Profile(6, 13, 3, False),
    Profile(7, 14, 3, True),
    Profile(10, 19, 4, False),
    Profile(12, 21, 4, False),
    Profile(14, 23, 4, False),
    Profile(16, 26, 5, False),
)
QUERY_PROFILES = (
    Profile(10, 15, 3, True),
    Profile(18, 22, 4, False),
    Profile(24, 27, 5, False),
    Profile(30, 30, 5, False),
)


def _root_and_canonical() -> tuple[Path, Path]:
    for root in Path(__file__).resolve().parents:
        direct = root / "data/canonical/puzzles.jsonl"
        if direct.is_file() and (root / "RUNTIME_MANIFEST.json").is_file():
            return root, direct
        shared = root / "shared/data/canonical/puzzles.jsonl"
        if shared.is_file():
            return root, shared
    raise FileNotFoundError("parametric prototype needs its source or staged runtime")


ROOT, CANONICAL_PATH = _root_and_canonical()
PARAMETRIC_HOME = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def canonical_record() -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one selected canonical row; found {len(matches)}")
    source = matches[0].get("program_solution")
    if (
        not isinstance(source, str)
        or hashlib.sha256(source.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256
    ):
        raise ValueError("selected canonical program changed; re-author and requalify")
    return matches[0]


def normalize_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"packing_rule"}:
        raise ValueError("settings must contain exactly packing_rule")
    value = settings["packing_rule"]
    if type(value) is not str or value not in PACKING_RULES:
        raise ValueError("packing_rule must be all_right or densest_left")
    return {"packing_rule": value}


def program(settings: object) -> str:
    selected = normalize_settings(settings)["packing_rule"]
    filename = "canonical.rkt" if selected == "all_right" else "densest_left.rkt"
    source = (PARAMETRIC_HOME / filename).read_text(encoding="utf-8")
    if selected == "all_right" and source != canonical_record()["program_solution"]:
        raise ValueError("canonical.rkt must remain byte-identical to selected authority")
    return source


def _exact_integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value: object) -> Grid:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def _segments(row: list[int]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    start = 0
    index = 0
    for end in range(len(row) + 1):
        if end < len(row) and row[end] != 8:
            continue
        values = [value for value in row[start:end] if value != 0]
        result.append(
            {
                "index": index,
                "start": start,
                "end": end,
                "width": end - start,
                "values": values,
                "count": len(values),
            }
        )
        index += 1
        start = end + 1
    return result


def _changed_cells(left: Grid, right: Grid) -> int:
    return sum(
        a != b
        for left_row, right_row in zip(left, right, strict=True)
        for a, b in zip(left_row, right_row, strict=True)
    )


def _solve_with_selector(grid: object, selector: str, *, reverse_values: bool = False) -> Grid:
    source = _grid(grid)
    output: Grid = []
    for row in source:
        descriptors = _segments(row)
        max_count = max((record["count"] for record in descriptors), default=0)
        max_width = max((record["width"] for record in descriptors), default=0)
        result = list(row)
        for record in descriptors:
            values = list(record["values"])
            if reverse_values:
                values.reverse()
            if selector == "all_right":
                pack_left = False
            elif selector == "densest_left":
                pack_left = record["count"] > 0 and record["count"] == max_count
            elif selector == "widest_left":
                pack_left = record["count"] > 0 and record["width"] == max_width
            else:
                raise ValueError(f"unknown selector {selector}")
            empty = [0] * (record["width"] - len(values))
            packed = values + empty if pack_left else empty + values
            result[record["start"] : record["end"]] = packed
        output.append(result)
    return output


def solve(grid: object, settings: object) -> Grid:
    selected = normalize_settings(settings)["packing_rule"]
    return _solve_with_selector(grid, selected)


def solve_widest_left(grid: object) -> Grid:
    return _solve_with_selector(grid, "widest_left")


def _profile(split: str, index: int) -> Profile:
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if type(index) is not int or not 0 <= index < len(profiles):
        raise ValueError(f"{split} index must be in 0..{len(profiles) - 1}")
    return profiles[index]


def _row_counts(profile: Profile, row_index: int) -> list[int]:
    counts = list(range(profile.segments, 0, -1))
    # The second demonstration includes both row-total parities.  The extra
    # pebble never ties the unique count winner.
    if profile.allow_odd_row_total and row_index % 2 == 1:
        counts[-1] += 1
    return counts


def _role_indices(seed: int, split: str, index: int, row_index: int, count: int) -> tuple[int, int]:
    split_bias = 0 if split == "demo" else 37
    winner = (seed + split_bias + 3 * index + row_index) % count
    offset = 1 + ((seed // max(1, count) + index + row_index) % (count - 1))
    widest = (winner + offset) % count
    return winner, widest


def _widths_for_counts(width: int, counts: list[int], winner: int, widest: int) -> list[int]:
    available = width - (len(counts) - 1)
    widths = [count + 1 for count in counts]
    extra = available - sum(widths)
    if extra < 1:
        raise ValueError("profile lacks room for a wider non-winning distractor")
    widths[widest] += extra
    if not widths[widest] > widths[winner]:
        raise ValueError("constructive widest distractor is not strictly wider")
    return widths


def _assign_roles(base_counts: list[int], winner: int, widest: int) -> list[int]:
    result = [0] * len(base_counts)
    result[winner] = base_counts[0]
    result[widest] = base_counts[1]
    remaining_indices = [i for i in range(len(base_counts)) if i not in (winner, widest)]
    for position, value in zip(remaining_indices, base_counts[2:], strict=True):
        result[position] = value
    return result


def _colors_for_segment(count: int, role: str, flip: bool) -> list[int]:
    if role == "winner":
        values = [3, 1, 2, 4, 5]
    elif role == "widest":
        values = [9, 7, 6, 5, 4]
    else:
        values = [6, 2, 5, 1, 4]
    chosen = values[:count]
    if flip:
        chosen = list(reversed(chosen))
    return chosen


def _spread_positions(width: int, count: int, *, left_edge: bool, right_edge: bool) -> list[int]:
    if count == 1:
        if left_edge:
            return [0]
        if right_edge:
            return [width - 1]
        return [width // 2]
    positions = [round(i * (width - 1) / (count - 1)) for i in range(count)]
    if len(set(positions)) != count:
        raise ValueError("segment is too narrow for constructive spread")
    return positions


def _sample_row(seed: int, split: str, index: int, row_index: int, profile: Profile) -> list[int]:
    base_counts = _row_counts(profile, row_index)
    winner, widest = _role_indices(seed, split, index, row_index, profile.segments)
    counts = _assign_roles(base_counts, winner, widest)
    widths = _widths_for_counts(profile.width, counts, winner, widest)

    row: list[int] = []
    for segment_index, (segment_width, pebble_count) in enumerate(zip(widths, counts, strict=True)):
        cells = [0] * segment_width
        role = "winner" if segment_index == winner else "widest" if segment_index == widest else "other"
        colors = _colors_for_segment(
            pebble_count,
            role,
            flip=(seed + index + row_index + segment_index) % 2 == 1,
        )
        positions = _spread_positions(
            segment_width,
            pebble_count,
            left_edge=segment_index == 0,
            right_edge=segment_index == profile.segments - 1,
        )
        for position, color in zip(positions, colors, strict=True):
            cells[position] = color
        row.extend(cells)
        if segment_index != profile.segments - 1:
            row.append(8)
    if len(row) != profile.width:
        raise AssertionError("constructive row width drifted")
    return row


def sample_input(seed: int, split: str, index: int) -> Grid:
    _exact_integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    profile = _profile(split, index)
    grid = [
        _sample_row(seed, split, index, row_index, profile)
        for row_index in range(profile.height)
    ]
    facts = analyze(grid)
    if not facts["settings_differ"]:
        raise AssertionError("constructed input did not distinguish settings")
    if any(not row["unique_winner"] for row in facts["rows"]):
        raise AssertionError("constructed row lacks a unique count winner")
    if any(row["winner_index"] == row["widest_index"] for row in facts["rows"]):
        raise AssertionError("constructed wrong-intermediate distractor collapsed")
    return grid


def analyze(grid: object) -> dict[str, Any]:
    source = _grid(grid)
    row_facts: list[dict[str, Any]] = []
    for row_index, row in enumerate(source):
        descriptors = _segments(row)
        counts = [record["count"] for record in descriptors]
        widths = [record["width"] for record in descriptors]
        winner_count = max(counts, default=0)
        widest_width = max(widths, default=0)
        winners = [i for i, value in enumerate(counts) if value == winner_count]
        widest = [i for i, value in enumerate(widths) if value == widest_width]
        winner_index = winners[0] if len(winners) == 1 else -1
        widest_index = widest[0] if len(widest) == 1 else -1
        row_facts.append(
            {
                "row": row_index,
                "segment_counts": counts,
                "segment_widths": widths,
                "row_total": sum(counts),
                "unique_winner": len(winners) == 1 and winner_count > 0,
                "winner_index": winner_index,
                "winner_count": winner_count,
                "winner_width": widths[winner_index] if winner_index >= 0 else None,
                "widest_index": widest_index,
                "widest_width": widest_width,
            }
        )
    default = _solve_with_selector(source, "all_right")
    alternate = _solve_with_selector(source, "densest_left")
    wrong = _solve_with_selector(source, "widest_left")
    return {
        "height": len(source),
        "width": len(source[0]),
        "rows": row_facts,
        "winner_positions": sorted({row["winner_index"] for row in row_facts}),
        "settings_differ": default != alternate,
        "changed_cells_between_settings": _changed_cells(default, alternate),
        "wrong_intermediate_changes_output": alternate != wrong,
        "changed_cells_vs_widest": _changed_cells(alternate, wrong),
        "nonzero_cells": sum(cell != 0 for row in source for cell in row),
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_integer(seed, 0, 2**63 - 1, "seed")
    normalized = normalize_settings(settings)
    _exact_integer(demos, 2, 6, "demos")
    _exact_integer(queries, 1, 4, "queries")
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": solve(grid, normalized)})
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": solve(grid, normalized)})
    return {
        "train": train,
        "test": test,
        "program_solution": program(normalized),
    }


def public_turn(episode: object, query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _exact_integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def _racket_two_pass(metric: str, selected_left: str, *, reverse_values: bool = False) -> str:
    if metric not in ("count", "width"):
        raise ValueError("metric must be count or width")
    metric_expr = "(length vals)" if metric == "count" else "(- end cc)"
    value_expr = "(reverse vals)" if reverse_values else "vals"
    return f"""(rule! (let ((dummy 0))
  (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((r (in-range (rows g))))
    (let ((best
           (let find-best ((cc 0) (best 0))
             (cond
               ((>= cc (cols g)) best)
               ((= (at g r cc) 8) (find-best (+ cc 1) best))
               (else
                (let find-end ((end cc))
                  (if (and (< end (cols g)) (not (= (at g r end) 8)))
                      (find-end (+ end 1))
                      (let* ((vals (filter (lambda (v) (not (= v 0)))
                                           (map (lambda (x) (at g r x)) (range cc end))))
                             (score {metric_expr}))
                        (find-best end (if (> score best) score best))))))))))
      (let loop ((c 0) (acc out))
        (cond
          ((>= c (cols g)) acc)
          ((= (at g r c) 8) (loop (+ c 1) (set-cell acc r c 8)))
          (else
           (let find-end ((end c))
             (if (and (< end (cols g)) (not (= (at g r end) 8)))
                 (find-end (+ end 1))
                 (let* ((vals (filter (lambda (v) (not (= v 0)))
                                      (map (lambda (x) (at g r x)) (range c end))))
                        (score {'(length vals)' if metric == 'count' else '(- end c)'})
                        (write (if {selected_left} c (- end (length vals))))
                        (ordered {value_expr})
                        (next (for/fold ((acc2 acc)) ((v (in-list ordered)) (i (in-naturals)))
                                (set-cell acc2 r (+ write i) v))))
                   (loop end next)))))))))))"""


def _racket_one_pass(condition: str) -> str:
    return f"""(rule! (let ((dummy 0))
  (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((r (in-range (rows g))))
    (let loop ((c 0) (acc out))
      (cond
        ((>= c (cols g)) acc)
        ((= (at g r c) 8) (loop (+ c 1) (set-cell acc r c 8)))
        (else
         (let find-end ((end c))
           (if (and (< end (cols g)) (not (= (at g r end) 8)))
               (find-end (+ end 1))
               (let* ((vals (filter (lambda (v) (not (= v 0)))
                                    (map (lambda (x) (at g r x)) (range c end))))
                      (write (if {condition} c (- end (length vals))))
                      (next (for/fold ((acc2 acc)) ((v (in-list vals)) (i (in-naturals)))
                              (set-cell acc2 r (+ write i) v))))
                 (loop end next))))))))))"""


def _racket_row_parity() -> str:
    return """(rule! (let ((dummy 0))
  (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((r (in-range (rows g))))
    (let ((row-total
           (length (filter (lambda (v) (and (not (= v 0)) (not (= v 8))))
                           (map (lambda (x) (at g r x)) (range 0 (cols g)))))))
      (let loop ((c 0) (acc out))
        (cond
          ((>= c (cols g)) acc)
          ((= (at g r c) 8) (loop (+ c 1) (set-cell acc r c 8)))
          (else
           (let find-end ((end c))
             (if (and (< end (cols g)) (not (= (at g r end) 8)))
                 (find-end (+ end 1))
                 (let* ((vals (filter (lambda (v) (not (= v 0)))
                                      (map (lambda (x) (at g r x)) (range c end))))
                        (write (if (odd? row-total) c (- end (length vals))))
                        (next (for/fold ((acc2 acc)) ((v (in-list vals)) (i (in-naturals)))
                                (set-cell acc2 r (+ write i) v))))
                   (loop end next)))))))))))"""


def rival_programs() -> dict[str, str]:
    """Finite executable competitors used only by the teaching audit."""
    return {
        "all_left": _racket_one_pass("#t"),
        "first_segment_left": _racket_one_pass("(= c 0)"),
        "last_segment_left": _racket_one_pass("(= end (cols g))"),
        "odd_count_left": _racket_one_pass("(odd? (length vals))"),
        "at_least_two_left": _racket_one_pass("(>= (length vals) 2)"),
        "row_odd_left": _racket_row_parity(),
        "widest_left": (PARAMETRIC_HOME / "wrong_widest.rkt").read_text(encoding="utf-8"),
        "inverse_densest": _racket_two_pass(
            "count",
            "(and (> score 0) (not (= score best)))",
        ),
        "reverse_order_densest": _racket_two_pass(
            "count",
            "(and (> score 0) (= score best))",
            reverse_values=True,
        ),
    }
