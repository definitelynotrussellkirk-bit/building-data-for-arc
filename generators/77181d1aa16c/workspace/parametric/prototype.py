"""Episode-fixed mapping-policy family for ARC task 77181d1aa16c.

``local_blocks`` is the exact canonical rule: each mirrored target block uses
its own sparse indicator mapping. ``dominant_block`` first infers all three
ordered role mappings and their input-dependent support counts, selects the
unique most-supported block, then applies that selected mapping to all three
mirrored targets.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "77181d1aa16c"
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
SETTINGS = ("local_blocks", "dominant_block")
DEFAULT = "local_blocks"

# (pattern_h, pattern_w, top, bottom, left, right,
#  dominant_block, missing_block, missing_role, duplicate_role)
DEMO_PROFILES = (
    (4, 4, 1, 1, 1, 1, 1, 3, "minor", "major"),
    (5, 6, 1, 1, 1, 1, 2, 1, "major", "minor"),
    (7, 8, 1, 1, 1, 1, 3, 2, "minor", "major"),
    (8, 9, 1, 1, 1, 1, 1, 3, "major", "minor"),
    (10, 11, 1, 1, 1, 1, 2, 1, "minor", "major"),
    (12, 13, 1, 1, 1, 1, 3, 2, "major", "minor"),
)
QUERY_PROFILES = (
    (6, 7, 1, 1, 1, 1, 2, 1, "minor", "major"),   # 14 x 16
    (8, 9, 1, 1, 1, 1, 3, 2, "major", "minor"),   # 18 x 20
    (11, 12, 1, 1, 1, 2, 1, 3, "minor", "major"), # 24 x 27
    (14, 14, 1, 1, 1, 1, 3, 2, "minor", "major"), # 30 x 30
)


def _exact_int(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"mapping_policy"}:
        raise ValueError("settings must contain exactly mapping_policy")
    value = settings["mapping_policy"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("mapping_policy must be local_blocks|dominant_block")
    return value


def _canonical() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise RuntimeError("canonical.rkt is empty")
    return source


def _dominant_program(force_block: int | None = None) -> str:
    source = _canonical()
    start_marker = "     (define (mapped key role)"
    end_marker = "     (build-grid h w (r c)"
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    if force_block is None:
        selector = """     (define (support-count key)
       (length (filter (lambda (i) (= (first i) key)) indicators)))
     (define dominant-key
       (for/fold ((best 1)) ((key (in-list (list 2 3))))
         (if (> (support-count key) (support-count best)) key best)))
"""
    else:
        _exact_int(force_block, 1, 3, "wrong_block")
        selector = f"     (define dominant-key {force_block})\n"
    replacement = selector + """     (define (mapped key role)
       (if (zero? key)
           role
           (let ((hit (find (lambda (i) (and (= (first i) dominant-key)
                                             (= (second i) role)))
                            indicators)))
             (if hit (third hit) 0))))
"""
    return source[:start] + replacement + source[end:]


_DOMINANT_PROGRAM = _dominant_program()


def program(settings: object) -> str:
    return _canonical() if _policy(settings) == DEFAULT else _DOMINANT_PROGRAM


def counterfactual_program(settings: object, *, wrong_block: int) -> str:
    if _policy(settings) != "dominant_block":
        raise ValueError("counterfactual is defined for dominant_block")
    return _dominant_program(_exact_int(wrong_block, 1, 3, "wrong_block"))


def _basic_grid(grid: object) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be exact integers in 0..9")
    return len(grid), width


def _largest_nonzero_rect(grid: list[list[int]]) -> tuple[int, int, int, int]:
    """Canonical exhaustive scan with first-maximum tie behavior."""
    height, width = _basic_grid(grid)
    zeros = [[0] * (width + 1) for _ in range(height + 1)]
    for row in range(height):
        for col in range(width):
            zeros[row + 1][col + 1] = (
                zeros[row][col + 1] + zeros[row + 1][col]
                - zeros[row][col] + int(grid[row][col] == 0)
            )
    best = (0, 0, 0, 0, 0)
    for top in range(height):
        for bottom in range(top, height):
            for left in range(width):
                for right in range(left, width):
                    area = (bottom - top + 1) * (right - left + 1)
                    if area <= best[0]:
                        continue
                    holes = (
                        zeros[bottom + 1][right + 1] - zeros[top][right + 1]
                        - zeros[bottom + 1][left] + zeros[top][left]
                    )
                    if holes == 0:
                        best = (area, top, left, bottom, right)
    return best[1:]


def _block_key(top: int, left: int, ph: int, pw: int, row: int, col: int) -> int:
    return 2 * int(row >= top + ph) + int(col >= left + pw)


def _role_at(pattern: list[list[int]], top: int, left: int, row: int, col: int,
             *, mirror: bool = True) -> int | None:
    ph, pw = len(pattern), len(pattern[0])
    lower = row >= top + ph
    rightward = col >= left + pw
    local_row = row - (top + ph if lower else top)
    local_col = col - (left + pw if rightward else left)
    if not (0 <= local_row < ph and 0 <= local_col < pw):
        return None
    source_row = ph - 1 - local_row if lower and mirror else local_row
    source_col = pw - 1 - local_col if rightward and mirror else local_col
    return pattern[source_row][source_col]


def _parse(grid: list[list[int]], *, mirror: bool = True, last_indicator: bool = False) -> dict[str, Any]:
    height, width = _basic_grid(grid)
    top, left, bottom, right = _largest_nonzero_rect(grid)
    ph, pw = bottom - top + 1, right - left + 1
    pattern = [row[left:right + 1] for row in grid[top:bottom + 1]]
    counts = Counter(value for row in pattern for value in row if value)
    if len(counts) != 2:
        raise ValueError("source pattern must contain exactly two nonzero colors")
    ranked = sorted(counts, key=lambda color: -counts[color])
    major, minor = ranked[:2]
    if counts[major] <= counts[minor]:
        raise ValueError("source pattern must have a strict majority role")

    indicators: list[dict[str, int]] = []
    mappings: dict[tuple[int, int], int] = {}
    support_counts = {1: 0, 2: 0, 3: 0}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (top <= row <= bottom and left <= col <= right):
                continue
            block = _block_key(top, left, ph, pw, row, col)
            role = _role_at(pattern, top, left, row, col, mirror=mirror)
            if block not in support_counts or role not in (major, minor):
                continue
            record = {"row": row, "col": col, "block": block, "role": role, "color": value}
            indicators.append(record)
            support_counts[block] += 1
            key = (block, role)
            if last_indicator or key not in mappings:
                mappings[key] = value
    dominant = max((1, 2, 3), key=lambda key: (support_counts[key], -key))
    return {
        "height": height,
        "width": width,
        "rect": (top, left, bottom, right),
        "pattern": pattern,
        "pattern_shape": [ph, pw],
        "source_cells": ph * pw,
        "counts": counts,
        "major": major,
        "minor": minor,
        "indicators": indicators,
        "mappings": mappings,
        "support_counts": support_counts,
        "dominant_block": dominant,
    }


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    facts = _parse(grid)
    mapping = {
        str(role): facts["mappings"][(facts["dominant_block"], role)]
        for role in (facts["major"], facts["minor"])
        if (facts["dominant_block"], role) in facts["mappings"]
    }
    return {
        "height": facts["height"],
        "width": facts["width"],
        "rect": list(facts["rect"]),
        "pattern_shape": facts["pattern_shape"],
        "source_cells": facts["source_cells"],
        "major": facts["major"],
        "minor": facts["minor"],
        "support_counts": dict(facts["support_counts"]),
        "dominant_block": facts["dominant_block"],
        "selected_mapping": mapping,
        "indicator_count": len(facts["indicators"]),
    }


def _render(grid: list[list[int]], policy: str, *, last_indicator: bool = False,
            mirror: bool = True, carry_missing: bool = False,
            selected_block: int | str | None = None) -> list[list[int]]:
    facts = _parse(grid, mirror=mirror, last_indicator=last_indicator)
    if selected_block is None:
        selected = facts["dominant_block"] if policy == "dominant_block" else None
    elif selected_block == "fewest":
        selected = min((1, 2, 3), key=lambda key: (facts["support_counts"][key], key))
    elif selected_block == "largest_numeric":
        selected = max(
            (1, 2, 3),
            key=lambda key: (
                sum(color for (block, _), color in facts["mappings"].items() if block == key),
                -key,
            ),
        )
    else:
        selected = _exact_int(selected_block, 1, 3, "selected_block")

    top, left, _, _ = facts["rect"]
    ph, pw = facts["pattern_shape"]
    output = [[0] * facts["width"] for _ in range(facts["height"])]
    for row in range(facts["height"]):
        for col in range(facts["width"]):
            role = _role_at(facts["pattern"], top, left, row, col, mirror=mirror)
            if role not in (facts["major"], facts["minor"]):
                continue
            block = _block_key(top, left, ph, pw, row, col)
            if block == 0:
                output[row][col] = role
                continue
            mapping_block = selected if selected is not None else block
            mapped = facts["mappings"].get((mapping_block, role))
            output[row][col] = role if mapped is None and carry_missing else (mapped or 0)
    return output


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    return _render(grid, _policy(settings))


def _asymmetric(pattern: list[list[int]]) -> bool:
    return (
        pattern != [row[::-1] for row in pattern]
        and pattern != pattern[::-1]
        and pattern != [row[::-1] for row in pattern[::-1]]
    )


def _make_pattern(rng: random.Random, ph: int, pw: int, major: int, minor: int) -> list[list[int]]:
    cells = [(row, col) for row in range(ph) for col in range(pw)]
    safe = {(row, col) for row in range(ph - 1) for col in range(pw - 1)}
    area = ph * pw
    low = max(4, area // 4)
    high = max(low, (area - 1) // 2)
    for _ in range(512):
        n_minor = rng.randint(low, high)
        chosen = set(rng.sample(cells, n_minor))
        if len(chosen & safe) < 2 or len(safe - chosen) < 2:
            continue
        pattern = [[minor if (row, col) in chosen else major for col in range(pw)] for row in range(ph)]
        if _asymmetric(pattern):
            return pattern
    raise RuntimeError("could not construct asymmetric strict-majority pattern")


def _block_position(top: int, left: int, ph: int, pw: int, block: int,
                    source_row: int, source_col: int) -> tuple[int, int]:
    if block == 1:
        return top + source_row, left + 2 * pw - 1 - source_col
    if block == 2:
        return top + 2 * ph - 1 - source_row, left + source_col
    if block == 3:
        return top + 2 * ph - 1 - source_row, left + 2 * pw - 1 - source_col
    raise ValueError("block must be 1..3")


def _indicator_candidates(pattern: list[list[int]], top: int, left: int,
                          block: int, role: int) -> list[tuple[int, int]]:
    ph, pw = len(pattern), len(pattern[0])
    return sorted(
        _block_position(top, left, ph, pw, block, row, col)
        for row in range(ph - 1)
        for col in range(pw - 1)
        if pattern[row][col] == role
    )


def _profile_grid(seed: int, profile_index: int, profile: tuple[Any, ...]) -> list[list[int]]:
    ph, pw, top, bottom, left, right, winner, missing_block, missing_role_name, duplicate_role_name = profile
    rng = random.Random(seed * 1_000_003 + profile_index * 97_409 + 771_811)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    major, minor = palette[:2]
    pattern = _make_pattern(rng, ph, pw, major, minor)
    height = top + 2 * ph + bottom
    width = left + 2 * pw + right
    grid = [[0] * width for _ in range(height)]
    for row in range(ph):
        for col in range(pw):
            grid[top + row][left + col] = pattern[row][col]

    roles = {"major": major, "minor": minor}
    missing = (missing_block, missing_role_name)
    duplicate = (winner, duplicate_role_name)
    descriptors = [(block, role) for block in (1, 2, 3) for role in ("major", "minor")]
    present = [descriptor for descriptor in descriptors if descriptor != missing]
    mapping_colors = dict(zip(present, palette[2:7]))
    duplicate_color = palette[7]

    for descriptor_index, (block, role_name) in enumerate(present):
        candidates = _indicator_candidates(pattern, top, left, block, roles[role_name])
        required = 2 if (block, role_name) == duplicate else 1
        if len(candidates) < required:
            raise RuntimeError(f"insufficient indicator candidates for {(block, role_name)}")
        if (block, role_name) == duplicate:
            positions = (candidates[0], candidates[-1])
            grid[positions[0][0]][positions[0][1]] = mapping_colors[(block, role_name)]
            grid[positions[1][0]][positions[1][1]] = duplicate_color
        else:
            index = (seed + profile_index * 3 + descriptor_index * 5) % len(candidates)
            row, col = candidates[index]
            grid[row][col] = mapping_colors[(block, role_name)]

    expected = (top, left, top + ph - 1, left + pw - 1)
    facts = _parse(grid)
    if facts["rect"] != expected:
        raise AssertionError(f"profile changed source rectangle: {facts['rect']} != {expected}")
    if facts["dominant_block"] != winner:
        raise AssertionError("profile did not realize requested dominant block")
    if sorted(facts["support_counts"].values()) != [1, 2, 3]:
        raise AssertionError("profile support counts must be 1,2,3")
    if any((winner, role) not in facts["mappings"] for role in (major, minor)):
        raise AssertionError("dominant block must provide both role mappings")
    return grid


def _identity(grid):
    return deepcopy(grid)


def _last_indicator(grid):
    return _render(grid, "local_blocks", last_indicator=True)


def _no_mirror(grid):
    return _render(grid, "local_blocks", mirror=False)


def _carry_missing(grid):
    return _render(grid, "local_blocks", carry_missing=True)


def _fixed(block: int):
    return lambda grid: _render(grid, "dominant_block", selected_block=block)


def _fewest(grid):
    return _render(grid, "dominant_block", selected_block="fewest")


def _largest_numeric(grid):
    return _render(grid, "dominant_block", selected_block="largest_numeric")


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "last_indicator_wins": _last_indicator,
    "copy_without_mirroring": _no_mirror,
    "carry_source_when_missing": _carry_missing,
    "fixed_block_1": _fixed(1),
    "fixed_block_2": _fixed(2),
    "fixed_block_3": _fixed(3),
    "fewest_supported_block": _fewest,
    "largest_numeric_mapping_block": _largest_numeric,
}


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    demos = episode["train"]
    queries = episode["test"]
    declared = [
        {"mapping_policy": "local_blocks"},
        {"mapping_policy": "dominant_block"},
    ]
    survivors = [
        setting for setting in declared
        if all(transform(pair["input"], setting) == pair["output"] for pair in demos)
    ]
    rows = {}
    harmful = []
    for name, rival in RIVALS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        disagreements = [rival(pair["input"]) != pair["output"] for pair in queries]
        rows[name] = {"fits_all_demos": fits, "query_disagreements": disagreements}
        if fits and any(disagreements):
            harmful.append(name)
    return {
        "declared_survivors": survivors,
        "harmful_survivors": harmful,
        "rivals": rows,
        "query_identifiable": [
            transform(pair["input"], declared[0]) != transform(pair["input"], declared[1])
            for pair in queries
        ],
        "query_answers_used_for_fitting": False,
        "scope": "finite two-setting family plus nine executable shortcuts; not universal uniqueness",
    }


def _pair(grid: list[list[int]], settings: object) -> dict[str, Any]:
    return {"input": grid, "output": transform(grid, settings)}


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    _policy(settings)
    demo_bank = [
        _pair(_profile_grid(seed, index, profile), settings)
        for index, profile in enumerate(DEMO_PROFILES)
    ]
    query_bank = [
        _pair(_profile_grid(seed, len(DEMO_PROFILES) + index, profile), settings)
        for index, profile in enumerate(QUERY_PROFILES)
    ]
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": demo_bank[:demos],
        "test": query_bank[:queries],
        "program_solution": program(settings),
    }


def model_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


visible_turn = model_view
