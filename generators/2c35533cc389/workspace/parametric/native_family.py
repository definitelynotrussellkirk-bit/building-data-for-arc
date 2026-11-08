"""Native parametric directional-paint family for task 2c35533cc389.

The canonical setting paints one cell to the right.  The retained fixed-left
setting mirrors that direction.  The sequential ``anchor_inward`` setting first
compares the red counts on the two vertical borders, treats the strict minority
border as an input-derived anchor side, then paints every original red source one
cell inward from that side.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "2c35533cc389"
PARAMETER = "direction_rule"
MODES = ("fixed_right", "fixed_left", "anchor_inward")
DEFAULT = {PARAMETER: "fixed_right"}
HERE = Path(__file__).resolve().parent

FIXED_LEFT_PROGRAM = """(rule!
 ;; Every red(2) gets a blue(1) painted immediately to its LEFT (in bounds).
 (paint-cells g
              (filter (lambda (p) (>= (second p) 0))
                      (map (lambda (p) (list (first p) (- (second p) 1)))
                           (find-color g 2)))
              1))"""

ANCHOR_INWARD_PROGRAM = """(rule!
 (let* ((reds (find-color g 2))
        (left-count (count-if (lambda (p) (= (second p) 0)) reds))
        (right-count (count-if (lambda (p) (= (second p) (- w 1))) reds))
        (delta (if (< left-count right-count) 1 -1))
        (targets
          (filter (lambda (p) (and (>= (second p) 0) (< (second p) w)))
                  (map (lambda (p)
                         (list (first p) (+ (second p) delta)))
                       reds))))
   (paint-cells g targets 1)))"""

RIVALS = MODES + (
    "anchor_outward",
    "sourcewise_inward",
    "sourcewise_outward",
    "majority_half_inward",
    "topmost_side_inward",
)

# height, width, red count, left-border red count, right-border red count.
DEMO_SPECS = (
    (8, 10, 12, 1, 3),
    (9, 11, 14, 3, 1),
    (12, 14, 18, 1, 4),
    (16, 18, 24, 4, 1),
    (20, 22, 34, 2, 5),
    (24, 26, 48, 5, 2),
)
QUERY_SPECS = (
    (10, 13, 16, 3, 1),
    (15, 17, 24, 1, 4),
    (24, 27, 46, 5, 2),
    (30, 30, 90, 2, 7),
)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must contain exactly direction_rule")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"direction_rule must be one of {MODES}")
    return mode


def program(settings: dict[str, str]) -> str:
    mode = _mode(settings)
    if mode == "fixed_right":
        return (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if mode == "fixed_left":
        return FIXED_LEFT_PROGRAM
    return ANCHOR_INWARD_PROGRAM


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 2 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 2..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or value not in (0, 2) for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular and contain only exact colors 0 and 2")
    return len(grid), width


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(sources) < 2:
        raise ValueError("at least two red sources are required")
    left_count = sum(c == 0 for _, c in sources)
    right_count = sum(c == width - 1 for _, c in sources)
    if left_count == 0 or right_count == 0 or left_count == right_count:
        raise ValueError("vertical border red counts must be positive and unequal")
    anchor_side = "left" if left_count < right_count else "right"
    direction = "right" if anchor_side == "left" else "left"
    source_set = set(sources)
    adjacent = any((r, c + 1) in source_set for r, c in sources)
    return {
        "height": height,
        "width": width,
        "sources": sources,
        "source_count": len(sources),
        "left_border_count": left_count,
        "right_border_count": right_count,
        "anchor_side": anchor_side,
        "direction": direction,
        "adjacent_source_witness": adjacent,
    }


def _paint_with_delta(grid: list[list[int]], delta: int) -> list[list[int]]:
    _height, width = _validate_grid(grid)
    out = deepcopy(grid)
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    for r, c in sources:
        target = c + delta
        if 0 <= target < width:
            out[r][target] = 1
    return out


def _paint_sourcewise(grid: list[list[int]], *, inward: bool) -> list[list[int]]:
    _height, width = _validate_grid(grid)
    out = deepcopy(grid)
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    for r, c in sources:
        toward_center = 1 if 2 * c < width - 1 else -1
        delta = toward_center if inward else -toward_center
        target = c + delta
        if 0 <= target < width:
            out[r][target] = 1
    return out


def claim(grid: list[list[int]], mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in RIVALS:
        raise ValueError(f"unknown direction claim: {mode!r}")
    facts = analyze(grid)
    if mode == "fixed_right":
        return _paint_with_delta(grid, 1)
    if mode == "fixed_left":
        return _paint_with_delta(grid, -1)
    if mode == "anchor_inward":
        return _paint_with_delta(grid, 1 if facts["direction"] == "right" else -1)
    if mode == "anchor_outward":
        return _paint_with_delta(grid, -1 if facts["direction"] == "right" else 1)
    if mode == "sourcewise_inward":
        return _paint_sourcewise(grid, inward=True)
    if mode == "sourcewise_outward":
        return _paint_sourcewise(grid, inward=False)
    if mode == "majority_half_inward":
        left = sum(2 * c < facts["width"] - 1 for _, c in facts["sources"])
        right = len(facts["sources"]) - left
        return _paint_with_delta(grid, 1 if left > right else -1)
    topmost = min(facts["sources"])
    return _paint_with_delta(grid, 1 if 2 * topmost[1] < facts["width"] - 1 else -1)


def _rng(seed: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:native-v2:{seed}:{stream}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(seed: int, stream: str, spec: tuple[int, int, int, int, int]) -> list[list[int]]:
    height, width, count, left_count, right_count = spec
    if not (height >= 4 and width >= 7 and left_count != right_count and count >= left_count + right_count + 5):
        raise ValueError("invalid scene specification")
    rng = _rng(seed, stream)
    positions: set[tuple[int, int]] = set()

    interior_rows = list(range(1, height - 1))
    rng.shuffle(interior_rows)
    if max(left_count, right_count) > len(interior_rows):
        raise ValueError("border count exceeds available interior rows")
    for row in interior_rows[:left_count]:
        positions.add((row, 0))
    rng.shuffle(interior_rows)
    for row in interior_rows[:right_count]:
        positions.add((row, width - 1))

    anchor_side = "left" if left_count < right_count else "right"
    majority_side = "right" if anchor_side == "left" else "left"
    if majority_side == "right":
        top_col = width - 2
        bottom_col = max(width // 2 + 1, width - 3)
        chain_start = max(width // 2 + 1, width - 5)
    else:
        top_col = 1
        bottom_col = min(width // 2 - 1, 2)
        chain_start = 1
    chain_start = min(max(1, chain_start), width - 4)
    positions.update({(0, top_col), (height - 1, bottom_col)})
    positions.update((height // 2, chain_start + offset) for offset in range(3))

    left_candidates = [
        (r, c)
        for r in range(1, height - 1)
        for c in range(1, max(2, width // 2))
        if (r, c) not in positions
    ]
    right_candidates = [
        (r, c)
        for r in range(1, height - 1)
        for c in range(max(1, width // 2), width - 1)
        if (r, c) not in positions
    ]
    rng.shuffle(left_candidates)
    rng.shuffle(right_candidates)
    primary = right_candidates if majority_side == "right" else left_candidates
    secondary = left_candidates if majority_side == "right" else right_candidates
    desired_primary = max(0, (count * 3) // 4 - sum(
        (2 * c >= width - 1) if majority_side == "right" else (2 * c < width - 1)
        for _, c in positions
    ))
    for cell in primary[:desired_primary]:
        if len(positions) >= count:
            break
        positions.add(cell)
    for cell in secondary + primary[desired_primary:]:
        if len(positions) >= count:
            break
        positions.add(cell)
    if len(positions) != count:
        raise RuntimeError(f"could not place {count} distinct red sources")

    grid = [[0] * width for _ in range(height)]
    for r, c in positions:
        grid[r][c] = 2
    facts = analyze(grid)
    if facts["anchor_side"] != anchor_side or not facts["adjacent_source_witness"]:
        raise RuntimeError("constructed scene violated its semantic contract")
    return grid


def teaching_check(episode: dict[str, Any]) -> list[dict[str, Any]]:
    selected = _mode(episode.get("settings"))
    findings: list[dict[str, Any]] = []
    for rival in RIVALS:
        if rival == selected:
            continue
        fits = all(claim(pair["input"], rival) == pair["output"] for pair in episode["train"])
        if not fits:
            continue
        disagree = [
            index
            for index, pair in enumerate(episode["test"])
            if claim(pair["input"], rival) != pair["output"]
        ]
        if disagree:
            findings.append({"rival": rival, "query_indices": disagree})
    return findings


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    mode = _mode(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(spec: tuple[int, int, int, int, int], stream: str) -> dict[str, list[list[int]]]:
        grid = _scene(seed, stream, spec)
        return {"input": grid, "output": claim(grid, mode)}

    episode = {
        "train": [pair(spec, f"demo:{index}") for index, spec in enumerate(DEMO_SPECS[:demos])],
        "test": [pair(spec, f"query:{index}") for index, spec in enumerate(QUERY_SPECS[:queries])],
        "program_solution": program(settings),
        "settings": dict(settings),
    }
    episode["certificate"] = {
        "finite_rivals": list(RIVALS),
        "findings": teaching_check(episode),
    }
    return episode


def public_turn_bytes(episode: dict[str, Any], index: int = 0) -> bytes:
    if type(index) is not int or not 0 <= index < len(episode.get("test", [])):
        raise ValueError("query index out of range")
    public = {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }
    return (json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
