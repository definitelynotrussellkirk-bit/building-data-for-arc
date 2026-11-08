"""Native sequential family for corner-marker beam completion.

``beam_only`` is the exact canonical authority.  ``beam_then_highlight_longest``
first performs every canonical blocker-aware beam, then uses the input/output
delta to find the unique emitter that painted the greatest number of previously
zero cells and recolors only that newly painted segment to color 8.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "b91a3b0baac4"
HERE = Path(__file__).resolve().parent
MODES = ("beam_only", "beam_then_highlight_longest")
HYPOTHESES = MODES + (
    "identity",
    "highlight_shortest",
    "highlight_first",
    "highlight_last",
    "highlight_full_longest",
    "ignore_blockers_then_highlight",
)

_DEMO_PROFILES = (
    (9, 12, 2, False),
    (12, 10, 3, False),
    (14, 16, 4, False),
    (18, 18, 1, False),
    (22, 24, 2, False),
    (26, 28, 3, False),
)
_QUERY_PROFILES = (
    (13, 15, 1, False),
    (18, 20, 2, False),
    (24, 27, 3, False),
    (30, 30, 4, True),
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
            "'beam_only'|'beam_then_highlight_longest'}"
        )
    return settings["finish_rule"]


def program(settings: Any) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "beam_only" else "beam_then_highlight_longest.rkt"
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
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


def marker(value: Any) -> tuple[int, int, int]:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    found = [
        (r, c, grid[r][c])
        for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
        if grid[r][c] in (1, 2, 3, 4)
    ]
    if len(found) != 1:
        raise ValueError("grid must have exactly one corner marker in 1..4")
    return found[0]


def direction(value: int) -> tuple[int, int]:
    return {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[value]


def _emitters(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    mr, mc, _ = marker(grid)
    return [
        (r, c, cell)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell not in (0, 5) and (r, c) != (mr, mc)
    ]


def ray_cells(
    value: Any,
    emitter: tuple[int, int, int],
    *,
    blockers_enabled: bool = True,
) -> list[tuple[int, int]]:
    grid = _grid(value)
    _, _, code = marker(grid)
    dr, dc = direction(code)
    r, c, _ = emitter
    h, w = len(grid), len(grid[0])
    cells: list[tuple[int, int]] = []
    r += dr
    c += dc
    while 0 <= r < h and 0 <= c < w:
        if blockers_enabled and grid[r][c] == 5:
            break
        cells.append((r, c))
        r += dr
        c += dc
    return cells


def beam_only(value: Any, *, blockers_enabled: bool = True) -> list[list[int]]:
    grid = deepcopy(_grid(value))
    source = deepcopy(grid)
    for emitter in _emitters(source):
        for row, col in ray_cells(source, emitter, blockers_enabled=blockers_enabled):
            grid[row][col] = emitter[2]
    return grid


def delta_segments(value: Any, *, blockers_enabled: bool = True) -> list[dict[str, Any]]:
    grid = _grid(value)
    result = []
    for emitter in _emitters(grid):
        ray = ray_cells(grid, emitter, blockers_enabled=blockers_enabled)
        fresh = [(row, col) for row, col in ray if grid[row][col] == 0]
        result.append({"emitter": emitter, "ray": ray, "fresh": fresh})
    if not result:
        raise ValueError("grid has no emitters")
    return result


def highlight_segment(value: Any, cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    grid = deepcopy(_grid(value))
    for row, col in cells:
        grid[row][col] = 8
    return grid


def _pick(segments: list[dict[str, Any]], which: str) -> dict[str, Any]:
    if which == "longest":
        return max(segments, key=lambda item: len(item["fresh"]))
    if which == "shortest":
        return min(segments, key=lambda item: len(item["fresh"]))
    if which == "first":
        return segments[0]
    if which == "last":
        return segments[-1]
    raise ValueError(which)


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis: {hypothesis}")
    source = deepcopy(_grid(value))
    if hypothesis == "identity":
        return source
    completed = beam_only(source)
    if hypothesis == "beam_only":
        return completed
    segments = delta_segments(source)
    if hypothesis == "beam_then_highlight_longest":
        return highlight_segment(completed, _pick(segments, "longest")["fresh"])
    if hypothesis == "highlight_shortest":
        return highlight_segment(completed, _pick(segments, "shortest")["fresh"])
    if hypothesis == "highlight_first":
        return highlight_segment(completed, _pick(segments, "first")["fresh"])
    if hypothesis == "highlight_last":
        return highlight_segment(completed, _pick(segments, "last")["fresh"])
    if hypothesis == "highlight_full_longest":
        winner = _pick(segments, "longest")
        er, ec, _ = winner["emitter"]
        return highlight_segment(completed, [(er, ec), *winner["ray"]])
    if hypothesis == "ignore_blockers_then_highlight":
        unblocked = delta_segments(source, blockers_enabled=False)
        return highlight_segment(completed, _pick(unblocked, "longest")["fresh"])
    raise AssertionError(hypothesis)


def transform(value: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    return predict(value, mode)


def observe(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    segments = delta_segments(grid)
    lengths = [len(item["fresh"]) for item in segments]
    active: set[tuple[int, int]] = set()
    _, _, code = marker(grid)
    dr, dc = direction(code)
    for item in segments:
        ray = item["ray"]
        if ray:
            row, col = ray[-1]
        else:
            row, col, _ = item["emitter"]
        rr, cc = row + dr, col + dc
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]) and grid[rr][cc] == 5:
            active.add((rr, cc))
    blockers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell == 5
    }
    winner = _pick(segments, "longest")
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "direction": code,
        "emitter_count": len(segments),
        "fresh_lengths": lengths,
        "unique_longest": lengths.count(max(lengths)) == 1,
        "winning_emitter": list(winner["emitter"]),
        "winning_length": len(winner["fresh"]),
        "active_blocker_count": len(active),
        "irrelevant_blocker_count": len(blockers - active),
    }


def _derived_seed(seed: int, split: str, index: int) -> int:
    raw = json.dumps(
        [TASK_ID, "beam-highlight-longest-v1", seed, split, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _positions(size: int, count: int) -> list[int]:
    values = [round((index + 1) * (size - 1) / (count + 1)) for index in range(count)]
    if len(set(values)) != count or any(not 1 <= value <= size - 2 for value in values):
        raise AssertionError((size, count, values))
    return values


def _lengths(ray_size: int, count: int) -> list[int]:
    maximum = ray_size - 4
    values = [2 + index * (maximum - 2) // (count - 1) for index in range(count)]
    if len(set(values)) != count or values[-1] > maximum:
        raise AssertionError((ray_size, count, values))
    return values


def _point(code: int, line: int, distance: int, h: int, w: int) -> tuple[int, int]:
    if code == 2:
        return line, 2 + distance
    if code == 4:
        return line, w - 3 - distance
    if code == 3:
        return 2 + distance, line
    if code == 1:
        return h - 3 - distance, line
    raise ValueError(code)


def _safe_dense_blockers(
    grid: list[list[int]], code: int, emitter_lines: set[int], marker_pos: tuple[int, int], seed: int
) -> None:
    h, w = len(grid), len(grid[0])
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    for r in range(h):
        for c in range(w):
            line = r if code in (2, 4) else c
            if line in emitter_lines or (r, c) in corners or (r, c) == marker_pos:
                continue
            if (r * 7 + c * 11 + seed) % 5 == 0:
                grid[r][c] = 5
    # Explicitly touch any boundary not already occupied, without creating corners.
    for r, c in ((0, 2), (h - 1, 2), (2, 0), (2, w - 1)):
        line = r if code in (2, 4) else c
        if line not in emitter_lines and (r, c) not in corners and (r, c) != marker_pos:
            grid[r][c] = 5


def _scene(seed: int, height: int, width: int, code: int, stress: bool) -> list[list[int]]:
    rng = random.Random(seed)
    grid = [[0] * width for _ in range(height)]
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    marker_pos = corners[seed % 4]
    grid[marker_pos[0]][marker_pos[1]] = code

    count = 6 if stress else 4
    line_size = height if code in (2, 4) else width
    ray_size = width if code in (2, 4) else height
    lines = _positions(line_size, count)
    base_lengths = _lengths(ray_size, count)
    winner_index = 1 + (seed % (count - 2))
    lengths = base_lengths[:-1]
    rng.shuffle(lengths)
    assigned = lengths[:winner_index] + [base_lengths[-1]] + lengths[winner_index:]
    assigned = assigned[:count]
    if len(assigned) != count:
        raise AssertionError(assigned)

    palette = [color for color in (1, 2, 3, 4, 6, 7, 9) if color != code]
    rng.shuffle(palette)
    for index, (line, length) in enumerate(zip(lines, assigned)):
        emitter = _point(code, line, 0, height, width)
        blocker = _point(code, line, length + 1, height, width)
        upstream = _point(code, line, -2, height, width)
        if any(grid[r][c] != 0 for r, c in (emitter, blocker, upstream)):
            raise AssertionError("beam construction collision")
        grid[emitter[0]][emitter[1]] = palette[index]
        grid[blocker[0]][blocker[1]] = 5
        grid[upstream[0]][upstream[1]] = 5

    if stress:
        _safe_dense_blockers(grid, code, set(lines), marker_pos, seed)

    observed = observe(grid)
    if not observed["unique_longest"]:
        raise AssertionError(observed)
    if observed["active_blocker_count"] < count:
        raise AssertionError(observed)
    if observed["irrelevant_blocker_count"] < count:
        raise AssertionError(observed)
    if predict(grid, "beam_then_highlight_longest") == predict(grid, "beam_only"):
        raise AssertionError("stage B had no observable effect")
    for rival in HYPOTHESES:
        if rival not in MODES and predict(grid, rival) == predict(grid, "beam_then_highlight_longest"):
            raise AssertionError(f"declared rival survived scene: {rival}")
    return grid


def sample_input(seed: int, index: int, *, split: str) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES if split == "test" else None
    if profiles is None:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    h, w, code, stress = profiles[index]
    return _scene(_derived_seed(seed, split, index), h, w, code, stress)


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
        "schema": "b91a3b0baac4-teaching-certificate-v1",
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
    "beam_only",
    "delta_segments",
    "generate",
    "highlight_segment",
    "marker",
    "observe",
    "predict",
    "program",
    "public_turn",
    "sample_input",
    "teaching_certificate",
    "transform",
]
