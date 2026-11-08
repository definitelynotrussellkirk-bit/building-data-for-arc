"""Native parametric adapter for topmost versus singleton-anchor selection.

The canonical setting keeps the topmost yellow in each column.  The alternate
setting first finds the row of the unique singleton yellow column, then keeps
the yellow nearest that input-derived row in every active column (upper row on
a distance tie).  Inputs are sampled independently of the hidden setting.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "55cfa127936a"
HERE = Path(__file__).resolve().parent
SELECTIONS = ("topmost", "singleton_anchor_nearest")
RIVALS = (
    "bottommost",
    "nearest_anchor_lower_tie",
    "farthest_anchor",
    "nearest_center",
    "nearest_one_third",
    "nearest_two_thirds",
    "nearest_marker_column",
)

_TRAIN_PROFILES = (
    ("low_anchor", 9, 11, "low", 1, 3),
    ("high_anchor", 11, 13, "high", 1, 3),
    ("middle", 14, 17, "middle", 2, 4),
    ("lower_large", 18, 20, "lower", 3, 5),
    ("upper_large", 24, 26, "upper", 3, 7),
    ("wide_dense", 27, 30, "upper", 2, 10),
)
_TEST_PROFILES = (
    ("transfer", 12, 15, "upper", 2, 4),
    ("changed_geometry", 17, 19, "low", 3, 5),
    ("boundary_contacts", 23, 27, "lower", 3, 7),
    ("stress30", 30, 30, "middle", 2, 13),
)


def _settings(value: dict[str, Any]) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    selection = value["selection"]
    if type(selection) is not str or selection not in SELECTIONS:
        raise ValueError(f"selection must be one of {SELECTIONS}")
    return {"selection": selection}


def program(settings: dict[str, Any]) -> str:
    selection = _settings(settings)["selection"]
    name = "canonical.rkt" if selection == "topmost" else "singleton_anchor_nearest.rkt"
    return (HERE / name).read_text()


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not 5 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 5 <= len(grid[0]) <= 30
    ):
        raise ValueError("input must be a rectangular 5..30 grid")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or value not in (0, 4) for value in row)
        for row in grid
    ):
        raise ValueError("input cells must be exact integer colors 0 or 4")
    return len(grid), width


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    yellow_rows = tuple(
        tuple(row for row in range(height) if grid[row][column] == 4)
        for column in range(width)
    )
    singleton_columns = tuple(column for column, rows in enumerate(yellow_rows) if len(rows) == 1)
    active_columns = tuple(column for column, rows in enumerate(yellow_rows) if rows)
    if len(singleton_columns) != 1:
        raise ValueError("input requires exactly one singleton yellow column")
    if len(active_columns) < 6:
        raise ValueError("input requires at least six active columns")
    if any(len(yellow_rows[column]) < 2 for column in active_columns if column not in singleton_columns):
        raise ValueError("every non-anchor active column needs at least two yellow cells")
    anchor_column = singleton_columns[0]
    anchor_row = yellow_rows[anchor_column][0]
    return {
        "height": height,
        "width": width,
        "yellow_rows": yellow_rows,
        "active_columns": active_columns,
        "anchor_column": anchor_column,
        "anchor_row": anchor_row,
    }


def _closest(rows: tuple[int, ...], target: int, *, lower_tie: bool = False) -> int:
    if lower_tie:
        return min(rows, key=lambda row: (abs(row - target), -row))
    return min(rows, key=lambda row: (abs(row - target), row))


def _farthest(rows: tuple[int, ...], target: int) -> int:
    return min(rows, key=lambda row: (-abs(row - target), row))


def _solve_with_selector(grid: list[list[int]], selector) -> list[list[int]]:
    facts = analyze(grid)
    output = [[0] * facts["width"] for _ in range(facts["height"])]
    for column, rows in enumerate(facts["yellow_rows"]):
        if rows:
            output[selector(rows, facts, column)][column] = 4
    return output


def solve_python(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    selection = _settings(settings)["selection"]
    if selection == "topmost":
        return _solve_with_selector(grid, lambda rows, facts, column: rows[0])
    return _solve_with_selector(
        grid,
        lambda rows, facts, column: _closest(rows, facts["anchor_row"]),
    )


def rival_program(name: str) -> str:
    """Return one complete executable Racket shortcut used by the bounded audit."""
    if name not in RIVALS:
        raise ValueError(f"unknown rival: {name}")
    common = """(define (yellow-rows c)
     (filter (lambda (r) (= (at g r c) 4)) (range h)))
   (define anchor-column
     (first (filter (lambda (c) (= (length (yellow-rows c)) 1))
                    (range w))))
   (define anchor-row (first (yellow-rows anchor-column)))"""
    if name == "bottommost":
        chooser = """(define (chosen-row c) (last (yellow-rows c)))"""
    else:
        targets = {
            "nearest_anchor_lower_tie": "anchor-row",
            "farthest_anchor": "anchor-row",
            "nearest_center": "(/ (- h 1) 2)",
            "nearest_one_third": "(/ (- h 1) 3)",
            "nearest_two_thirds": "(/ (* 2 (- h 1)) 3)",
            "nearest_marker_column": "(min (- h 1) anchor-column)",
        }
        target = targets[name]
        if name == "nearest_anchor_lower_tie":
            comparison = "(or (< da db) (and (= da db) (> a b)))"
        elif name == "farthest_anchor":
            comparison = "(or (> da db) (and (= da db) (< a b)))"
        else:
            comparison = "(or (< da db) (and (= da db) (< a b)))"
        chooser = f"""(define target {target})
   (define (better? a b)
     (let ([da (abs (- a target))]
           [db (abs (- b target))])
       {comparison}))
   (define (chosen-row c)
     (first (sort (yellow-rows c) better?)))"""
    return """(rule!
 (let ()
   {common}
   {chooser}
   (grid-from-fn h w
     (lambda (r c)
       (if (= r (chosen-row c)) 4 0)))))
""".format(common=common, chooser=chooser)


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    if name not in RIVALS:
        raise ValueError(f"unknown rival: {name}")
    if name == "bottommost":
        selector = lambda rows, facts, column: rows[-1]
    elif name == "nearest_anchor_lower_tie":
        selector = lambda rows, facts, column: _closest(rows, facts["anchor_row"], lower_tie=True)
    elif name == "farthest_anchor":
        selector = lambda rows, facts, column: _farthest(rows, facts["anchor_row"])
    elif name == "nearest_center":
        selector = lambda rows, facts, column: _closest(rows, (facts["height"] - 1) // 2)
    elif name == "nearest_one_third":
        selector = lambda rows, facts, column: _closest(rows, (facts["height"] - 1) // 3)
    elif name == "nearest_two_thirds":
        selector = lambda rows, facts, column: _closest(rows, (2 * (facts["height"] - 1)) // 3)
    else:
        selector = lambda rows, facts, column: _closest(
            rows, min(facts["height"] - 1, facts["anchor_column"])
        )
    return _solve_with_selector(grid, selector)


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    raw = f"{TASK_ID}:singleton-anchor-v1:{seed}:{domain}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _anchor(height: int, kind: str, rng: random.Random) -> int:
    if kind == "low":
        base = height - 2
    elif kind == "high":
        base = 1
    elif kind == "middle":
        base = height // 2
    elif kind == "lower":
        base = (2 * height) // 3
    elif kind == "upper":
        base = height // 3
    else:
        raise ValueError(f"unknown anchor kind: {kind}")
    jitter = 0 if kind in {"low", "high"} else rng.choice((-1, 0, 1))
    return max(1, min(height - 2, base + jitter))


def _core_rows(height: int, anchor: int, pattern: int) -> set[int]:
    raw = {
        0: (0, anchor - 1, anchor + 1, height - 1),
        1: (0, anchor, height - 1),
        2: (0, anchor - 2, anchor + 3, height - 1),
        3: (anchor - 4, anchor - 1, height - 1),
        4: (0, anchor + 1, anchor + 4),
        5: (0, height // 2, height - 1),
    }[pattern % 6]
    rows = {max(0, min(height - 1, row)) for row in raw}
    if len(rows) < 2:
        rows.update((0, height - 1))
    return rows


def _profile_input(seed: int, split: str, profile: tuple[str, int, int, str, int, int]) -> list[list[int]]:
    name, height, width, anchor_kind, inactive_count, density = profile
    rng = _rng(seed, split + ":" + name)
    anchor_row = _anchor(height, anchor_kind, rng)
    if name == "low_anchor":
        marker_candidates = [column for column in range(1, min(4, width - 1))]
    elif name == "high_anchor":
        marker_candidates = [column for column in range(max(1, width - 4), width - 1)]
    else:
        marker_candidates = [
            column for column in range(1, width - 1)
            if abs(column - anchor_row) >= 2
        ] or list(range(1, width - 1))
    marker_column = rng.choice(marker_candidates)
    inactive_candidates = [column for column in range(1, width - 1) if column != marker_column]
    rng.shuffle(inactive_candidates)
    inactive = set(inactive_candidates[:inactive_count])
    active = [column for column in range(width) if column not in inactive]
    if marker_column not in active:
        raise AssertionError("marker column cannot be inactive")
    grid = [[0] * width for _ in range(height)]
    grid[anchor_row][marker_column] = 4
    offset = rng.randrange(6)
    for ordinal, column in enumerate(active):
        if column == marker_column:
            continue
        rows = _core_rows(height, anchor_row, ordinal + offset)
        target = min(height, max(len(rows), density + rng.randrange(3)))
        choices = [row for row in range(height) if row not in rows]
        rng.shuffle(choices)
        rows.update(choices[: max(0, target - len(rows))])
        for row in rows:
            grid[row][column] = 4
    facts = analyze(grid)
    canonical = solve_python(grid, {"selection": "topmost"})
    alternate = solve_python(grid, {"selection": "singleton_anchor_nearest"})
    if canonical == alternate:
        raise RuntimeError(f"profile {name} failed to distinguish settings")
    if facts["anchor_row"] != anchor_row or facts["anchor_column"] != marker_column:
        raise AssertionError("constructed anchor mismatch")
    return grid


def _query_profiles(seed: int) -> list[tuple[str, int, int, str, int, int]]:
    profiles = list(_TEST_PROFILES)
    _rng(seed, "query-order").shuffle(profiles)
    return profiles


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        return {"ok": False, "reason": "episode needs a training list"}
    chosen_program = episode.get("program_solution")
    expected = [selection for selection in SELECTIONS if program({"selection": selection}) == chosen_program]
    try:
        survivors = [
            selection
            for selection in SELECTIONS
            if all(
                solve_python(pair["input"], {"selection": selection}) == pair["output"]
                for pair in episode["train"]
            )
        ]
        surviving_rivals = [
            name
            for name in RIVALS
            if all(rival_output(pair["input"], name) == pair["output"] for pair in episode["train"])
        ]
    except (KeyError, TypeError, ValueError) as error:
        return {"ok": False, "reason": f"malformed demonstration: {error}"}
    return {
        "ok": survivors == expected and len(survivors) == 1 and not surviving_rivals,
        "survivors": survivors,
        "expected": expected,
        "surviving_rivals": surviving_rivals,
        "finite_settings": list(SELECTIONS),
        "finite_rivals": list(RIVALS),
        "scope": "Demonstration-only finite check; not unrestricted uniqueness.",
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    normalized = _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [_profile_input(seed, "train", profile) for profile in _TRAIN_PROFILES[:demos]]
    test_inputs = [_profile_input(seed, "test", profile) for profile in _query_profiles(seed)[:queries]]
    all_inputs = train_inputs + test_inputs
    keys = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("generated inputs must be distinct")
    result = {
        "train": [
            {"input": grid, "output": solve_python(grid, normalized)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": solve_python(grid, normalized)}
            for grid in test_inputs
        ],
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    certificate = teaching_check(result)
    if not certificate["ok"]:
        raise RuntimeError(f"constructive demonstrations failed teaching check: {certificate}")
    return result


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
