"""Native two-stage family for singleton erasure and survivor bridging.

``erase_only`` is the exact canonical authority. ``erase_then_bridge`` first
removes every singleton same-color 4-connected component, then detects clean
row/column spans containing at least four cells of one surviving color and only
zeroes between their endpoints, and fills those zeroes.  Every sampled scene
contains both a raw-ready span and a span blocked by a singleton, so executing
stage B before stage A is observably wrong.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "b765f6c9ebeb"
HERE = Path(__file__).resolve().parent
MODES = ("erase_only", "erase_then_bridge")
HYPOTHESES = MODES + (
    "identity",
    "bridge_before_erase",
    "bridge_raw_only",
    "erase_then_rows_only",
    "erase_then_cols_only",
    "erase_size_le2_then_bridge",
    "erase_then_fixed_color_7",
    "erase_then_color_blind",
)

# height, width, bridge axes, stress scene.  Prefixes are immutable; seed only
# changes harmless singleton positions/colors outside the protected teaching
# structures.
_DEMO_PROFILES = (
    (9, 12, ("row",), False),
    (12, 10, ("column",), False),
    (14, 16, ("row", "column"), False),
    (18, 18, ("row",), False),
    (22, 24, ("column",), False),
    (26, 28, ("row", "column"), False),
)
_QUERY_PROFILES = (
    (13, 15, ("row",), False),
    (18, 20, ("column",), False),
    (24, 27, ("row", "column"), False),
    (30, 30, ("row", "column"), True),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"finish_rule"}
        or type(settings["finish_rule"]) is not str
        or settings["finish_rule"] not in MODES
    ):
        raise ValueError(
            "settings must be exactly {'finish_rule': "
            "'erase_only'|'erase_then_bridge'}"
        )
    return settings["finish_rule"]


def program(settings: Any) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "erase_only" else "erase_then_bridge.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError(
            "grid must be rectangular 1..30 with exact integer colors 0..9"
        )
    return value


def components(value: Any) -> list[tuple[int, list[tuple[int, int]]]]:
    grid = _grid(value)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            result.append((color, sorted(cells)))
    return result


def erase_singletons(value: Any, *, minimum_size: int = 2) -> list[list[int]]:
    grid = _grid(value)
    if type(minimum_size) is not int or minimum_size < 1:
        raise ValueError("minimum_size must be a positive exact integer")
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        if len(cells) >= minimum_size:
            for row, col in cells:
                result[row][col] = color
    return result


def _line_spans(
    grid: list[list[int]],
    *,
    axes: Iterable[str] = ("row", "column"),
    allowed_colors: set[int] | None = None,
) -> list[dict[str, Any]]:
    enabled = tuple(axes)
    if any(axis not in {"row", "column"} for axis in enabled):
        raise ValueError("axes must contain only row and column")
    height, width = len(grid), len(grid[0])
    spans: list[dict[str, Any]] = []
    if "row" in enabled:
        for row in range(height):
            for color in range(1, 10):
                if allowed_colors is not None and color not in allowed_colors:
                    continue
                positions = [col for col in range(width) if grid[row][col] == color]
                if len(positions) < 4:
                    continue
                lo, hi = min(positions), max(positions)
                segment = grid[row][lo : hi + 1]
                if 0 in segment and all(value in (0, color) for value in segment):
                    spans.append(
                        {"axis": "row", "index": row, "lo": lo, "hi": hi, "color": color}
                    )
    if "column" in enabled:
        for col in range(width):
            for color in range(1, 10):
                if allowed_colors is not None and color not in allowed_colors:
                    continue
                positions = [row for row in range(height) if grid[row][col] == color]
                if len(positions) < 4:
                    continue
                lo, hi = min(positions), max(positions)
                segment = [grid[row][col] for row in range(lo, hi + 1)]
                if 0 in segment and all(value in (0, color) for value in segment):
                    spans.append(
                        {"axis": "column", "index": col, "lo": lo, "hi": hi, "color": color}
                    )
    return spans


def bridge(
    value: Any,
    *,
    axes: Iterable[str] = ("row", "column"),
    allowed_colors: set[int] | None = None,
) -> list[list[int]]:
    grid = deepcopy(_grid(value))
    source = deepcopy(grid)
    spans = _line_spans(source, axes=axes, allowed_colors=allowed_colors)
    # Row spans win at a crossing, matching the protected Racket program.
    for span in [item for item in spans if item["axis"] == "column"]:
        for row in range(span["lo"], span["hi"] + 1):
            if grid[row][span["index"]] == 0:
                grid[row][span["index"]] = span["color"]
    for span in [item for item in spans if item["axis"] == "row"]:
        for col in range(span["lo"], span["hi"] + 1):
            grid[span["index"]][col] = span["color"]
    return grid


def _color_blind_bridge(value: Any) -> list[list[int]]:
    grid = deepcopy(_grid(value))
    source = deepcopy(grid)
    height, width = len(source), len(source[0])
    for row in range(height):
        positions = [col for col in range(width) if source[row][col] != 0]
        if len(positions) >= 4:
            lo, hi = min(positions), max(positions)
            if any(source[row][col] == 0 for col in range(lo, hi + 1)):
                color = source[row][lo]
                for col in range(lo, hi + 1):
                    if grid[row][col] == 0:
                        grid[row][col] = color
    for col in range(width):
        positions = [row for row in range(height) if source[row][col] != 0]
        if len(positions) >= 4:
            lo, hi = min(positions), max(positions)
            if any(source[row][col] == 0 for row in range(lo, hi + 1)):
                color = source[lo][col]
                for row in range(lo, hi + 1):
                    if grid[row][col] == 0:
                        grid[row][col] = color
    return grid


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis: {hypothesis}")
    source = deepcopy(_grid(value))
    if hypothesis == "identity":
        return source
    if hypothesis == "erase_only":
        return erase_singletons(source)
    if hypothesis == "bridge_raw_only":
        return bridge(source)
    if hypothesis == "bridge_before_erase":
        return erase_singletons(bridge(source))
    if hypothesis == "erase_size_le2_then_bridge":
        return bridge(erase_singletons(source, minimum_size=3))
    cleaned = erase_singletons(source)
    if hypothesis == "erase_then_bridge":
        return bridge(cleaned)
    if hypothesis == "erase_then_rows_only":
        return bridge(cleaned, axes=("row",))
    if hypothesis == "erase_then_cols_only":
        return bridge(cleaned, axes=("column",))
    if hypothesis == "erase_then_fixed_color_7":
        return bridge(cleaned, allowed_colors={7})
    if hypothesis == "erase_then_color_blind":
        return _color_blind_bridge(cleaned)
    raise AssertionError(hypothesis)


def transform(value: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    return predict(value, mode)


def observe(value: Any) -> dict[str, Any]:
    source = _grid(value)
    comps = components(source)
    cleaned = erase_singletons(source)
    spans = _line_spans(cleaned)
    return {
        "height": len(source),
        "width": len(source[0]),
        "singleton_count": sum(len(cells) == 1 for _, cells in comps),
        "survivor_count": sum(len(cells) > 1 for _, cells in comps),
        "bridge_axes": [axis for axis in ("row", "column") if any(s["axis"] == axis for s in spans)],
        "bridge_colors": sorted({span["color"] for span in spans}),
        "bridge_span_count": len(spans),
    }


def _derived_seed(seed: int, split: str, index: int) -> int:
    raw = json.dumps(
        [TASK_ID, "erase-then-bridge-input-v1", seed, split, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _put(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        if grid[row][col] != 0:
            raise AssertionError(f"construction collision at {(row, col)}")
        grid[row][col] = color


def _add_horizontal(
    grid: list[list[int]], *, stage_row: int, ready_row: int, start: int, end: int
) -> set[tuple[int, int]]:
    if end - start < 6:
        raise AssertionError("horizontal teaching span too short")
    protected = {(row, col) for row in (stage_row, ready_row) for col in range(start, end + 1)}
    bars = ((start, start + 1), (end - 1, end))
    for row in (stage_row, ready_row):
        _put(grid, ((row, col) for pair in bars for col in pair), 7)
    blocker = (stage_row, (start + end) // 2)
    _put(grid, (blocker,), 9)
    return protected


def _add_vertical(
    grid: list[list[int]], *, stage_col: int, ready_col: int, start: int, end: int
) -> set[tuple[int, int]]:
    if end - start < 6:
        raise AssertionError("vertical teaching span too short")
    protected = {(row, col) for col in (stage_col, ready_col) for row in range(start, end + 1)}
    bars = ((start, start + 1), (end - 1, end))
    for col in (stage_col, ready_col):
        _put(grid, ((row, col) for pair in bars for row in pair), 8)
    blocker = ((start + end) // 2, stage_col)
    _put(grid, (blocker,), 9)
    return protected


def _add_color_blind_decoy(grid: list[list[int]], row: int) -> set[tuple[int, int]]:
    width = len(grid[0])
    left = (1, 2)
    right = (max(5, width - 4), max(6, width - 3))
    _put(grid, ((row, col) for col in left), 5)
    _put(grid, ((row, col) for col in right), 6)
    return {(row, col) for col in range(left[0], right[1] + 1)}


def _add_stress_blocks(grid: list[list[int]]) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    reserved: set[tuple[int, int]] = set()
    for top, left, color in (
        (0, 0, 1),
        (0, width - 5, 2),
        (height - 5, 0, 3),
        (height - 5, width - 5, 4),
    ):
        cells = [(row, col) for row in range(top, top + 5) for col in range(left, left + 5)]
        _put(grid, cells, color)
        reserved.update(cells)
    return reserved


def _singleton_candidates(
    grid: list[list[int]], protected: set[tuple[int, int]]
) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 0 and (row, col) not in protected
    ]


def _safe_singleton(
    grid: list[list[int]], row: int, col: int, color: int
) -> bool:
    return all(
        not (0 <= rr < len(grid) and 0 <= cc < len(grid[0]))
        or grid[rr][cc] != color
        for rr, cc in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
    )


def _add_seeded_singletons(
    grid: list[list[int]], rng: random.Random, protected: set[tuple[int, int]], count: int
) -> None:
    candidates = _singleton_candidates(grid, protected)
    rng.shuffle(candidates)
    placed = 0
    palette = [1, 2, 3, 4, 5, 6, 9]
    for row, col in candidates:
        rng.shuffle(palette)
        color = next((value for value in palette if _safe_singleton(grid, row, col, value)), None)
        if color is None:
            continue
        grid[row][col] = color
        placed += 1
        if placed == count:
            return
    raise RuntimeError("could not place requested singleton distractors")


def _scene(seed: int, height: int, width: int, axes: tuple[str, ...], stress: bool) -> list[list[int]]:
    rng = random.Random(seed)
    grid = [[0] * width for _ in range(height)]
    protected: set[tuple[int, int]] = set()
    if stress:
        protected |= _add_stress_blocks(grid)

    if "row" in axes:
        if stress:
            protected |= _add_horizontal(grid, stage_row=10, ready_row=12, start=6, end=14)
        else:
            stage_row = max(2, height // 3 - 1)
            ready_row = stage_row + 2
            end = width - 3 if axes == ("row",) else max(8, width // 2)
            protected |= _add_horizontal(
                grid, stage_row=stage_row, ready_row=ready_row, start=1, end=end
            )
    if "column" in axes:
        if stress:
            protected |= _add_vertical(grid, stage_col=20, ready_col=22, start=6, end=14)
        else:
            stage_col = 3 if axes == ("column",) else width - 5
            ready_col = stage_col + 2
            end = height - 3 if axes == ("column",) else max(8, height // 2)
            protected |= _add_vertical(
                grid, stage_col=stage_col, ready_col=ready_col, start=1, end=end
            )

    decoy_row = 18 if stress else height - 2
    protected |= _add_color_blind_decoy(grid, decoy_row)
    _add_seeded_singletons(grid, rng, protected, 6 if stress else 4)

    observation = observe(grid)
    if observation["bridge_axes"] != [axis for axis in ("row", "column") if axis in axes]:
        raise AssertionError(f"unexpected bridge axes: {observation}")
    expected_colors = sorted(7 if axis == "row" else 8 for axis in axes)
    if observation["bridge_colors"] != expected_colors:
        raise AssertionError(f"unexpected bridge colors: {observation}")
    if predict(grid, "erase_then_bridge") == predict(grid, "erase_only"):
        raise AssertionError("stage B had no observable effect")
    if predict(grid, "erase_then_bridge") == predict(grid, "bridge_before_erase"):
        raise AssertionError("wrong-order rival survived construction")
    return grid


def sample_input(seed: int, index: int, *, split: str) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES if split == "test" else None
    if profiles is None:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    height, width, axes, stress = profiles[index]
    return _scene(_derived_seed(seed, split, index), height, width, axes, stress)


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    mode = _mode(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen: set[str] = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            source = sample_input(seed, index, split=split)
            key = json.dumps(source, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            episode[split].append({"input": source, "output": transform(source, mode)})
    episode["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return episode


def teaching_certificate(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    train = episode["train"]
    tests = episode.get("test", [])
    survivors = []
    rejected: dict[str, int] = {}
    for name in HYPOTHESES:
        mismatch = next(
            (
                index
                for index, pair in enumerate(train)
                if predict(pair["input"], name) != pair["output"]
            ),
            None,
        )
        if mismatch is None:
            survivors.append(name)
        else:
            rejected[name] = mismatch
    return {
        "schema": "b765f6c9ebeb-teaching-certificate-v1",
        "demos": len(train),
        "queries": len(tests),
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "rejected_at_demo": rejected,
    }


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    tests = episode.get("test")
    if type(train) is not list or type(tests) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(query_index, 0, len(tests) - 1, "query_index")
    visible = {"train": train, "test": [tests[query_index]]}
    return json.loads(public_challenge_bytes(visible))


__all__ = [
    "HYPOTHESES",
    "MODES",
    "bridge",
    "components",
    "erase_singletons",
    "generate",
    "observe",
    "predict",
    "program",
    "public_turn",
    "sample_input",
    "teaching_certificate",
    "transform",
]
