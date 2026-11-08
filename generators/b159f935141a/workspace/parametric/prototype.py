"""Matched-input parametric family for hollow cardinal-plus completion.

The canonical setting fills every qualifying center.  The alternate first
collects all qualifying centers, counts them by arm color, selects the uniquely
rarest qualifying color, and fills only centers with that selected color.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "b159f935141a"
FILL_SCOPES = ("all_qualifying", "rarest_color_only")
DEFAULT_SCOPE = "all_qualifying"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")

RAREST_PROGRAM = r"""(rule!
 (let* ((records
         (for*/fold ((acc (list)))
                    ((r (in-range 1 (- (rows g) 1)))
                     (c (in-range 1 (- (cols g) 1))))
           (let ((arms (list (at g (- r 1) c)
                             (at g (+ r 1) c)
                             (at g r (- c 1))
                             (at g r (+ c 1)))))
             (if (and (= (at g r c) 0)
                      (!= (first arms) 0)
                      (all? (lambda (v) (= v (first arms))) arms))
                 (cons (list r c (first arms)) acc)
                 acc))))
        (colors (remove-duplicates (map third records)))
        (selected
         (pick-min colors
                   (lambda (color)
                     (count-if (lambda (record) (= (third record) color)) records)))))
   (for/fold ((out g)) ((record records))
     (if (= (third record) selected)
         (set-cell out (first record) (second record) selected)
         out))))"""

WRONG_MOST_COMMON_PROGRAM = RAREST_PROGRAM.replace("(pick-min colors", "(pick-max colors", 1)

# (height, width, qualifying counts by distinct colors, number of decoys)
_DEMO_SPECS = (
    (7, 12, (1, 2), 2),
    (11, 15, (2, 3, 5), 2),
    (12, 16, (2, 1, 3), 3),
    (14, 18, (1, 3, 4), 4),
    (17, 21, (2, 4, 1), 5),
    (21, 25, (5, 2, 1, 3), 6),
)
_QUERY_SPECS = (
    (11, 15, (2, 3, 4), 3),
    (16, 20, (2, 5, 1), 5),
    (24, 26, (1, 3, 5, 7), 6),
    (30, 30, (1, 2, 4, 8), 8),
)
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_DECOY_KINDS = ("horizontal", "vertical", "three", "mixed", "occupied", "diagonal")


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"fill_scope"}:
        raise ValueError("settings must contain exactly fill_scope")
    scope = settings["fill_scope"]
    if type(scope) is not str or scope not in FILL_SCOPES:
        raise ValueError(f"fill_scope must be one of {FILL_SCOPES}")
    return {"fill_scope": scope}


def program(settings: object) -> str:
    scope = validate_settings(settings)["fill_scope"]
    return CANONICAL_PROGRAM if scope == "all_qualifying" else RAREST_PROGRAM


def counterfactual_program() -> str:
    return WRONG_MOST_COMMON_PROGRAM


def _mix(*parts: object) -> int:
    raw = ":".join(map(str, (TASK_ID, "rarest-plus-color-v1", *parts)))
    return int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")


def _qualifying(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    records = []
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            arms = tuple(grid[r + dr][c + dc] for dr, dc in _CARD)
            if grid[r][c] == 0 and arms[0] != 0 and len(set(arms)) == 1:
                records.append((r, c, arms[0]))
    return records


def _decoy_kind(grid: list[list[int]], r: int, c: int) -> str | None:
    center = grid[r][c]
    up, down, left, right = tuple(grid[r + dr][c + dc] for dr, dc in _CARD)
    values = (up, down, left, right)
    nonzero = [value for value in values if value]
    if center == 0 and left == right != 0 and up == down == 0:
        return "horizontal"
    if center == 0 and up == down != 0 and left == right == 0:
        return "vertical"
    if center == 0 and len(nonzero) == 3 and len(set(nonzero)) == 1:
        return "three"
    if center == 0 and len(nonzero) == 4 and len(set(values)) > 1:
        return "mixed"
    if center != 0 and up != 0 and len(set(values)) == 1:
        return "occupied"
    diagonal = tuple(grid[r + dr][c + dc] for dr, dc in _DIAG)
    if center == 0 and not nonzero and diagonal[0] != 0 and len(set(diagonal)) == 1:
        return "diagonal"
    return None


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact integer ARC colors")
    records = _qualifying(grid)
    if not records:
        raise ValueError("scene needs at least one qualifying plus")
    counts = Counter(color for _, _, color in records)
    rarest = min(counts, key=lambda color: (counts[color], color))
    most_common = min(counts, key=lambda color: (-counts[color], color))
    decoys = [
        (r, c, kind)
        for r in range(1, len(grid) - 1)
        for c in range(1, width - 1)
        if (kind := _decoy_kind(grid, r, c)) is not None
    ]
    return {
        "qualifying_centers": records,
        "counts_by_color": dict(sorted(counts.items())),
        "rarest_color": rarest,
        "most_common_color": most_common,
        "decoy_centers": decoys,
    }


def apply_mode(grid: list[list[int]], scope: str) -> list[list[int]]:
    if scope not in FILL_SCOPES:
        raise ValueError(f"unknown fill scope {scope!r}")
    info = analyze(grid)
    selected = None if scope == "all_qualifying" else info["rarest_color"]
    out = deepcopy(grid)
    for r, c, color in info["qualifying_centers"]:
        if selected is None or color == selected:
            out[r][c] = color
    return out


def apply_wrong_most_common(grid: list[list[int]]) -> list[list[int]]:
    info = analyze(grid)
    out = deepcopy(grid)
    for r, c, color in info["qualifying_centers"]:
        if color == info["most_common_color"]:
            out[r][c] = color
    return out


def _slots(height: int, width: int, rng: random.Random) -> list[tuple[int, int]]:
    n_rows = 1 + (height - 3) // 4
    n_cols = 1 + (width - 3) // 4
    max_r0 = height - 2 - 4 * (n_rows - 1)
    max_c0 = width - 2 - 4 * (n_cols - 1)
    r0 = rng.randint(1, max_r0)
    c0 = rng.randint(1, max_c0)
    result = [(r0 + 4 * rr, c0 + 4 * cc) for rr in range(n_rows) for cc in range(n_cols)]
    rng.shuffle(result)
    return result


def _paint_plus(grid: list[list[int]], r: int, c: int, color: int) -> None:
    for dr, dc in _CARD:
        grid[r + dr][c + dc] = color


def _paint_decoy(grid: list[list[int]], r: int, c: int, kind: str, color: int, other: int) -> None:
    if kind == "horizontal":
        grid[r][c - 1] = grid[r][c + 1] = color
    elif kind == "vertical":
        grid[r - 1][c] = grid[r + 1][c] = color
    elif kind == "three":
        for dr, dc in _CARD[:3]:
            grid[r + dr][c + dc] = color
    elif kind == "mixed":
        _paint_plus(grid, r, c, color)
        grid[r][c + 1] = other
    elif kind == "occupied":
        _paint_plus(grid, r, c, color)
        grid[r][c] = other
    elif kind == "diagonal":
        for dr, dc in _DIAG:
            grid[r + dr][c + dc] = color
    else:
        raise ValueError(f"unknown decoy kind {kind!r}")


def _colors(seed: int, split: str, index: int, count: int) -> list[int]:
    palette = list(range(1, 10))
    rng = random.Random(_mix(seed, split, index, "colors"))
    rng.shuffle(palette)
    return palette[:count]


def _build_input(seed: int, split: str, index: int, spec: tuple[int, int, tuple[int, ...], int]) -> list[list[int]]:
    height, width, color_counts, decoy_count = spec
    if len(set(color_counts)) != len(color_counts):
        raise ValueError("qualifying color counts must be distinct")
    rng = random.Random(_mix(seed, split, index, spec))
    slots = _slots(height, width, rng)
    required = sum(color_counts) + decoy_count
    if required > len(slots):
        raise ValueError("scene spec exceeds separated motif capacity")
    colors = _colors(seed, split, index, len(color_counts) + 2)
    rarest_index = min(range(len(color_counts)), key=lambda position: (color_counts[position], position))
    if split == "train" and index in (0, 1):
        # Across the minimum two demonstrations the rarest color is numeric-low
        # once and numeric-high once, so neither color-ID shortcut survives.
        target = min(colors[: len(color_counts)]) if index == 0 else max(colors[: len(color_counts)])
        target_index = colors.index(target)
        colors[rarest_index], colors[target_index] = colors[target_index], colors[rarest_index]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    qualifying_count = sum(color_counts)
    qualifying_slots = slots[:qualifying_count]
    ordered_slots = sorted(qualifying_slots)
    interior = ordered_slots[1:-1]
    rng.shuffle(interior)
    rarest_slots = interior[: color_counts[rarest_index]]
    if len(rarest_slots) != color_counts[rarest_index]:
        raise RuntimeError("rarest motifs do not fit away from scan-order boundaries")
    rarest_positions = set(rarest_slots)
    remaining_slots = [slot for slot in qualifying_slots if slot not in rarest_positions]
    rng.shuffle(remaining_slots)
    expected: list[tuple[int, int, int]] = []
    cursor = 0
    for color_index, (color, count) in enumerate(zip(colors, color_counts)):
        chosen = rarest_slots if color_index == rarest_index else remaining_slots[cursor : cursor + count]
        if color_index != rarest_index:
            cursor += count
        for r, c in chosen:
            _paint_plus(grid, r, c, color)
            expected.append((r, c, color))
    for decoy_index, (r, c) in enumerate(slots[qualifying_count:required]):
        kind = _DECOY_KINDS[(decoy_index + _mix(seed, split, index, "decoy-order")) % len(_DECOY_KINDS)]
        color = colors[(decoy_index + 1) % len(colors)]
        other = colors[(decoy_index + 2) % len(colors)]
        if other == color:
            other = 9 if color != 9 else 8
        _paint_decoy(grid, r, c, kind, color, other)
    observed = _qualifying(grid)
    if sorted(observed) != sorted(expected):
        raise RuntimeError(f"motif interactions changed qualifying centers: {observed!r} != {expected!r}")
    info = analyze(grid)
    if len(info["counts_by_color"]) < 2:
        raise RuntimeError("scene must teach a global color selector")
    return grid


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")


def generate_episode(seed: int, *, fill_scope: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _validate_request(seed, demos, queries)
    if fill_scope not in FILL_SCOPES:
        raise ValueError(f"fill_scope must be one of {FILL_SCOPES}")
    train_inputs = [_build_input(seed, "train", index, _DEMO_SPECS[index]) for index in range(demos)]
    test_inputs = [_build_input(seed, "test", index, _QUERY_SPECS[index]) for index in range(queries)]
    return {
        "train": [{"input": grid, "output": apply_mode(grid, fill_scope)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_mode(grid, fill_scope)} for grid in test_inputs],
        "program_solution": CANONICAL_PROGRAM if fill_scope == "all_qualifying" else RAREST_PROGRAM,
    }


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside the episode")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return (json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")) + "\n").encode()


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0) -> dict[str, Any]:
    episode = generate_episode(seed, fill_scope="rarest_color_only", demos=3, queries=4)
    pair = episode["test"][0]
    info = analyze(pair["input"])
    return {
        "input": pair["input"],
        "settings": {"fill_scope": "rarest_color_only"},
        "intermediate_value": {
            "counts_by_color": {str(key): value for key, value in info["counts_by_color"].items()},
            "rarest_color": info["rarest_color"],
            "most_common_color": info["most_common_color"],
        },
        "program": RAREST_PROGRAM,
        "output": pair["output"],
        "counterfactual_program": WRONG_MOST_COMMON_PROGRAM,
        "counterfactual_output": apply_wrong_most_common(pair["input"]),
        "ablation": "wrong_intermediate",
    }
