"""Matched-input parametric family for selecting one green component.

The canonical setting recolors the smallest green component.  The alternate is
sequential: step A measures the unique blue key object's size (2..4), and step B
uses that input-dependent value as a one-based rank among four size-ordered green
components.  Python produces deterministic label claims; native qualification
re-executes both exact programs through protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "04e2ffe8dc8e"
HERE = Path(__file__).resolve().parent
MODES = ("smallest_green", "key_rank_green")
PROGRAM_FILES = {
    "smallest_green": "canonical.rkt",
    "key_rank_green": "key_rank.rkt",
}
DEMO_SHAPES = ((14, 16), (16, 14), (18, 18), (20, 17), (22, 24), (26, 22))
QUERY_SHAPES = ((13, 17), (19, 21), (24, 26), (30, 30))
DECOY_COLORS = (2, 4, 5, 7, 8, 9)

# Four distinct green areas.  The alternate key size is a rank, not an area.
_GREEN_RECTANGLES = ((1, 2), (2, 3), (3, 4), (4, 5))


def _integer(value: Any, name: str, low: int | None = None, high: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if low is not None and value < low:
        raise ValueError(f"{name} must be at least {low}")
    if high is not None and value > high:
        raise ValueError(f"{name} must be at most {high}")
    return value


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"selection_mode"}:
        raise ValueError("settings must contain exactly selection_mode")
    mode = settings["selection_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("selection_mode must be smallest_green or key_rank_green")
    return mode


def _grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _rng(seed: int, stream: str, index: int) -> random.Random:
    raw = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def program(settings: dict[str, str]) -> str:
    mode = _settings(settings)
    return (HERE / PROGRAM_FILES[mode]).read_text(encoding="utf-8")


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for neighbor in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(cells)
    return result


def _ordered_greens(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    greens = _components(grid, 3)
    if len(greens) != 4:
        raise ValueError(f"expected exactly four green components, got {len(greens)}")
    ordered = sorted(greens, key=lambda cells: (len(cells), min(cells)))
    sizes = [len(cells) for cells in ordered]
    if len(set(sizes)) != 4:
        raise ValueError("green component sizes must be distinct")
    return ordered


def intermediate_value(grid: list[list[int]]) -> int:
    """Step A: return the size of the unique blue key component."""
    _grid(grid)
    keys = _components(grid, 1)
    if len(keys) != 1:
        raise ValueError(f"expected one blue key component, got {len(keys)}")
    rank = len(keys[0])
    if rank not in (2, 3, 4):
        raise ValueError("blue key size must encode rank 2, 3, or 4")
    return rank


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    """Pure Python label claim matching the two exact Racket programs."""
    mode = _settings(settings)
    source = _grid(grid)
    ordered = _ordered_greens(source)
    rank = 1 if mode == "smallest_green" else intermediate_value(source)
    output = deepcopy(source)
    for row, col in ordered[rank - 1]:
        output[row][col] = 6
    return output


def selected_green_rank(source: list[list[int]], output: list[list[int]]) -> int:
    """Recover the rank of the original green component changed to magenta."""
    _grid(source)
    _grid(output)
    if (len(source), len(source[0])) != (len(output), len(output[0])):
        raise ValueError("source and output shapes differ")
    changed = {
        (row, col)
        for row in range(len(source))
        for col in range(len(source[0]))
        if source[row][col] == 3 and output[row][col] == 6
    }
    for rank, component in enumerate(_ordered_greens(source), 1):
        if changed == set(component):
            return rank
    raise ValueError("output does not recolor exactly one original green component")


def _place_rectangle(
    grid: list[list[int]],
    region: tuple[int, int, int, int],
    shape: tuple[int, int],
    rng: random.Random,
) -> None:
    row0, row1, col0, col1 = region
    height, width = shape
    if rng.randrange(2):
        height, width = width, height
    if height > row1 - row0 or width > col1 - col0:
        height, width = width, height
    if height > row1 - row0 or width > col1 - col0:
        raise ValueError("green rectangle does not fit its quadrant")
    top = rng.randint(row0, row1 - height)
    left = rng.randint(col0, col1 - width)
    for row in range(top, top + height):
        for col in range(left, left + width):
            if grid[row][col] != 0:
                raise ValueError("quadrant placement overlap")
            grid[row][col] = 3


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    """Construct a setting-independent scene with broad spatial distractors."""
    _integer(seed, "seed", 0)
    _integer(index, "index", 0)
    _integer(height, "height", 13, 30)
    _integer(width, "width", 14, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    rng = _rng(seed, stream, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    middle_row, middle_col = height // 2, width // 2
    regions = [
        (0, middle_row, 0, middle_col),
        (0, middle_row, middle_col + 1, width),
        (middle_row + 1, height, 0, middle_col),
        (middle_row + 1, height, middle_col + 1, width),
    ]
    shapes = list(_GREEN_RECTANGLES)
    rng.shuffle(shapes)
    for region, shape in zip(regions, shapes):
        _place_rectangle(grid, region, shape, rng)

    # A single connected blue component encodes rank 2..4.  It lives on the
    # reserved center cross, so changing the hidden rule never changes inputs.
    rank = 2 + ((seed + index + (0 if stream == "train" else 1)) % 3)
    if rng.randrange(2):
        start = max(0, min(height - rank, middle_row - rank // 2))
        for row in range(start, start + rank):
            grid[row][middle_col] = 1
    else:
        start = max(0, min(width - rank, middle_col - rank // 2))
        for col in range(start, start + rank):
            grid[middle_row][col] = 1

    # A phase-shifted lattice spreads distractors over the whole canvas rather
    # than padding a tiny core.  Colors 1, 3 and 6 are deliberately excluded.
    phase = rng.randrange(7)
    color_phase = rng.randrange(len(DECOY_COLORS))
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 and (3 * row + 5 * col + phase) % 7 == 0:
                grid[row][col] = DECOY_COLORS[(row + 2 * col + color_phase) % len(DECOY_COLORS)]

    # Preserve the exact four-green/one-key grammar and ensure every generated
    # example is genuinely discriminating.
    _ordered_greens(grid)
    if intermediate_value(grid) == 1:
        raise AssertionError("rank sampler produced a non-discriminating key")
    return grid


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict[str, Any]:
    """Native adapter contract: deterministic, matched and count-independent."""
    _integer(seed, "seed", 0, 2**63 - 1)
    mode = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result: dict[str, Any] = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": {"selection_mode": mode},
        "seed": seed,
        "prototype": True,
    }
    seen: set[str] = set()
    for split, shapes in (("train", DEMO_SHAPES[:demos]), ("test", QUERY_SHAPES[:queries])):
        for index, (height, width) in enumerate(shapes):
            grid = sample_input(seed, split, index, height, width)
            digest = json.dumps(grid, separators=(",", ":"))
            if digest in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(digest)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result


def _fixed_rank_program(rank: int) -> str:
    _integer(rank, "rank", 1, 4)
    return f"""(rule!
  (let* ((greens (filter (lambda (obj) (= (obj-color obj) 3)) (objects g 0)))
         (ordered
          (sort greens
                (lambda (a b)
                  (if (= (obj-size a) (obj-size b))
                      (cell< (first (sort (obj-cells a) cell<))
                             (first (sort (obj-cells b) cell<)))
                      (< (obj-size a) (obj-size b))))))
         (target (list-ref ordered {rank - 1})))
    (paint-cells g (obj-cells target) 6)))"""


def counterfactual_program(rank: int) -> str:
    """Wrong-intermediate ablation: force B to consume a fixed rank."""
    return _fixed_rank_program(rank)


class RacketEngine:
    """Small protected-Racket test helper; native worker remains authoritative."""

    def __init__(self) -> None:
        self.bridge = None
        self._wrapped: dict[str, str] = {}

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=60)
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            self.bridge = None
            raise ValueError("tests require the protected Racket backend")
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.bridge is not None:
            self.bridge.close()
            self.bridge = None

    def apply(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        if self.bridge is None:
            raise RuntimeError("RacketEngine must be used as a context manager")
        _grid(grid)
        from puzzle_generators.rule_wrap import wrap_rule

        wrapped = self._wrapped.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return _grid(self.bridge.eval_text(f"({wrapped} {literal})"))


def verify_episode(episode: dict[str, Any], *, engine: RacketEngine | None = None) -> dict[str, Any]:
    """Bounded demo-only setting identification plus all query label checks."""
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    mode = _settings(episode.get("settings"))
    expected_program = program({"selection_mode": mode})
    if episode.get("program_solution") != expected_program:
        raise ValueError("episode program does not match settings")
    normalized: dict[str, list[dict[str, list[list[int]]]]] = {}
    for split in ("train", "test"):
        pairs = episode.get(split)
        if type(pairs) is not list or not pairs:
            raise ValueError(f"episode {split} must be a nonempty list")
        normalized[split] = []
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair needs input and output")
            normalized[split].append({"input": deepcopy(_grid(pair["input"])), "output": deepcopy(_grid(pair["output"]))})
    digests = [json.dumps(pair["input"], separators=(",", ":")) for pairs in normalized.values() for pair in pairs]
    if len(digests) != len(set(digests)):
        raise ValueError("all episode inputs must be distinct")

    owned = engine is None
    runtime = RacketEngine().__enter__() if owned else engine
    try:
        survivors = []
        for candidate in MODES:
            settings = {"selection_mode": candidate}
            if all(runtime.apply(program(settings), pair["input"]) == pair["output"] for pair in normalized["train"]):
                survivors.append(settings)
        chosen = {"selection_mode": mode}
        if survivors != [chosen]:
            raise ValueError("demonstrations do not identify the selected setting")
        checks = []
        for index, pair in enumerate(normalized["test"]):
            actual = runtime.apply(expected_program, pair["input"])
            if actual != pair["output"]:
                raise ValueError(f"query label mismatch at index {index}")
            checks.append({"index": index, "identified_from_demonstrations": True})
        return {"fit_scope": "demonstrations_only", "survivors": survivors, "query_checks": checks}
    finally:
        if owned:
            runtime.__exit__(None, None, None)
