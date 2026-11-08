"""Source-bound anchor/offset stamping episodes; proposed until owner acceptance.

Stage A locates the unique color-9 anchor and extracts the color-1 cells as
anchor-relative offsets.  Stage B stamps those offsets at every color-2 seed
on a blank canvas.  The alternative setting rotates the *extracted offsets*
clockwise before stamping, preserving the same input distribution.  Anchor
positions move across every lesson so a fixed-origin shortcut cannot fit the
training examples.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "71d5c4ac6ea3"
HOME = Path(__file__).resolve().parent
MODES = ("as_drawn", "rotate_cw")
DEMO_PROFILES = (
    (9, 10, 3, 2),
    (10, 12, 4, 2),
    (12, 14, 4, 3),
    (14, 16, 5, 3),
    (16, 18, 6, 4),
    (18, 20, 6, 4),
)
QUERY_PROFILES = (
    (12, 14, 4, 2),
    (18, 20, 5, 3),
    (24, 27, 6, 4),
    (30, 30, 8, 5),
)

# Every prefix is asymmetric, nonzero, and distinct from both its clockwise
# rotation and its horizontal reflection.  Variants prevent a memorized shape
# while retaining exact profile counts.
_OFFSET_FAMILIES = (
    ((0, 1), (1, 1), (2, 0), (1, -2), (-1, -1), (-2, 1), (3, 2), (-2, -3)),
    ((1, 0), (1, -1), (0, -2), (-2, -1), (-1, 2), (2, 2), (-3, 1), (2, -3)),
    ((0, -1), (-1, -1), (-2, 0), (-1, 2), (1, 1), (2, -1), (-3, -2), (2, 3)),
    ((-1, 0), (-1, 1), (0, 2), (2, 1), (1, -2), (-2, -2), (3, -1), (-2, 3)),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings: Any) -> dict[str, str]:
    if (
        type(settings) is not dict
        or set(settings) != {"offset_mode"}
        or type(settings["offset_mode"]) is not str
        or settings["offset_mode"] not in MODES
    ):
        raise ValueError("settings must contain exactly offset_mode=as_drawn|rotate_cw")
    return {"offset_mode": settings["offset_mode"]}


def program(settings: Any) -> str:
    mode = settings_value(settings)["offset_mode"]
    return (HOME / "rules" / f"{mode}.rkt").read_text(encoding="utf-8")


def strict_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return copy.deepcopy(value)


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, "offset-rotation-v1", seed, split, index], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest(), "big"))


def _points(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color)


def extract_offsets(grid: list[list[int]], origin: tuple[int, int] | None = None) -> list[tuple[int, int]]:
    source = strict_grid(grid)
    anchors = _points(source, 9)
    if len(anchors) != 1:
        raise ValueError(f"expected exactly one color-9 anchor, found {len(anchors)}")
    ar, ac = anchors[0] if origin is None else origin
    return [(r - ar, c - ac) for r, c in _points(source, 1)]


def rotate_offset(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return dc, -dr


def _stamp(
    grid: list[list[int]], offsets: Iterable[tuple[int, int]], seeds: Iterable[tuple[int, int]]
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for sr, sc in seeds:
        for dr, dc in offsets:
            rr, cc = sr + dr, sc + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 8
    return out


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    source = strict_grid(grid)
    mode = settings_value(settings)["offset_mode"]
    offsets = extract_offsets(source)
    if mode == "rotate_cw":
        offsets = [rotate_offset(offset) for offset in offsets]
    return _stamp(source, offsets, _points(source, 2))


def fixed_origin_rival(
    grid: list[list[int]], origin: tuple[int, int] | list[int], settings: Any
) -> list[list[int]]:
    source = strict_grid(grid)
    if type(origin) not in (tuple, list) or len(origin) != 2:
        raise ValueError("origin must be a row/column pair")
    mode = settings_value(settings)["offset_mode"]
    offsets = extract_offsets(source, (int(origin[0]), int(origin[1])))
    if mode == "rotate_cw":
        offsets = [rotate_offset(offset) for offset in offsets]
    return _stamp(source, offsets, _points(source, 2))


def absolute_position_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: use absolute coordinates of the 1s as offsets."""
    source = strict_grid(grid)
    return _stamp(source, _points(source, 1), _points(source, 2))


def reflect_offsets_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: mirror the extracted pattern left/right instead of rotating."""
    source = strict_grid(grid)
    reflected = [(dr, -dc) for dr, dc in extract_offsets(source)]
    return _stamp(source, reflected, _points(source, 2))


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    source = strict_grid(grid)
    anchors = _points(source, 9)
    offsets = _points(source, 1)
    seeds = _points(source, 2)
    active = anchors + offsets + seeds
    if active:
        r0 = min(r for r, _ in active)
        c0 = min(c for _, c in active)
        r1 = max(r for r, _ in active)
        c1 = max(c for _, c in active)
        bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
    else:
        bbox_h = bbox_w = 0
    extracted = extract_offsets(source) if len(anchors) == 1 else []
    return {
        "anchor": [] if len(anchors) != 1 else list(anchors[0]),
        "offset_count": len(offsets),
        "seed_count": len(seeds),
        "offsets": [list(offset) for offset in extracted],
        "content_bbox_height": bbox_h,
        "content_bbox_width": bbox_w,
    }


def _profile_offsets(seed: int, split: str, index: int, count: int) -> list[tuple[int, int]]:
    split_bias = 0 if split == "demo" else 2
    family = _OFFSET_FAMILIES[(seed + index + split_bias) % len(_OFFSET_FAMILIES)]
    return list(family[:count])


def _fits(point: tuple[int, int], offsets: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    r, c = point
    return all(0 <= r + dr < h and 0 <= c + dc < w for dr, dc in offsets)


def _spread_points(
    candidates: list[tuple[int, int]], count: int, start: tuple[int, int], rng: random.Random
) -> list[tuple[int, int]]:
    if len(candidates) < count:
        raise ValueError("profile has too few lawful seed positions")
    remaining = list(candidates)
    # First seed is far from the legend; later seeds maximize distance from all
    # chosen positions.  Random tie-breaking remains deterministic per episode.
    best_distance = max(abs(r - start[0]) + abs(c - start[1]) for r, c in remaining)
    first_pool = [p for p in remaining if abs(p[0] - start[0]) + abs(p[1] - start[1]) == best_distance]
    first = first_pool[rng.randrange(len(first_pool))]
    selected = [first]
    remaining.remove(first)
    while len(selected) < count:
        scores = {
            point: min(abs(point[0] - r) + abs(point[1] - c) for r, c in selected)
            for point in remaining
        }
        best = max(scores.values())
        pool = [point for point, score in scores.items() if score == best]
        chosen = pool[rng.randrange(len(pool))]
        selected.append(chosen)
        remaining.remove(chosen)
    return selected


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    h, w, n_offsets, n_seeds = profiles[index]
    offsets = _profile_offsets(seed, split, index, n_offsets)
    rotated = [rotate_offset(offset) for offset in offsets]
    rng = _rng(seed, split, index)

    anchor_candidates = [
        (r, c) for r in range(h) for c in range(w) if _fits((r, c), offsets, h, w)
    ]
    anchor_candidates.sort()
    if split == "query" and index == len(QUERY_PROFILES) - 1:
        # Keep the legend in the upper-left and force seeds toward the opposite
        # extremes, making the 30x30 stress canvas visibly exercised.
        anchor = min(anchor_candidates, key=lambda p: (p[0] + p[1], p[0], p[1]))
    else:
        # Consecutive demos take consecutive lawful anchor positions.  Because
        # every profile has >6 candidates, 2..6 demos always show movement.
        base = (seed * 11 + (0 if split == "demo" else 5)) % len(anchor_candidates)
        anchor = anchor_candidates[(base + index) % len(anchor_candidates)]

    legend_cells = {anchor, *((anchor[0] + dr, anchor[1] + dc) for dr, dc in offsets)}
    safe_for_both = list(dict.fromkeys([*offsets, *rotated]))
    seed_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in legend_cells and _fits((r, c), safe_for_both, h, w)
    ]
    seeds = _spread_points(seed_candidates, n_seeds, anchor, rng)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[anchor[0]][anchor[1]] = 9
    for dr, dc in offsets:
        grid[anchor[0] + dr][anchor[1] + dc] = 1
    for r, c in seeds:
        if grid[r][c] != 0:
            raise AssertionError("seed collided with the offset legend")
        grid[r][c] = 2

    # These are construction invariants, not retry heuristics.  Failing here
    # means the profile/library itself changed incompatibly.
    original = transform(grid, {"offset_mode": "as_drawn"})
    rotated_output = transform(grid, {"offset_mode": "rotate_cw"})
    if original == rotated_output:
        raise ValueError("profile does not distinguish as_drawn from rotate_cw")
    return grid


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    own = bridge is None
    runtime = RacketBridge(timeout=60) if own else bridge
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in strict_grid(grid)) + ")"
    try:
        return strict_grid(runtime.eval_text(f"({wrap_rule(source)} {literal})"))
    finally:
        if own:
            runtime.close()


def _execute_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for mode in MODES:
        if source == program({"offset_mode": mode}):
            return transform(grid, {"offset_mode": mode})
    raise ValueError("unknown program")


def certify(
    episode: Any,
    *,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = settings_value(episode.get("settings"))
    expected_program = program(settings)
    if episode.get("program_solution") != expected_program:
        raise ValueError("program_solution differs from selected setting")
    train, test = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or not 2 <= len(train) <= 6:
        raise ValueError("train count must be 2..6")
    if not isinstance(test, list) or not 1 <= len(test) <= 4:
        raise ValueError("test count must be 1..4")
    pairs = train + test
    normalized = []
    for pair in pairs:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each pair requires input and output")
        normalized.append((strict_grid(pair["input"]), strict_grid(pair["output"])))
    if len({digest(grid) for grid, _ in normalized}) != len(normalized):
        raise ValueError("all demonstration and query inputs must be distinct")
    if len({_points(pair["input"], 9)[0] for pair in train}) < 2:
        raise ValueError("demonstrations must teach anchor-relative movement")

    run = _execute_python if execute is None else execute
    survivors = []
    for mode in MODES:
        source = program({"offset_mode": mode})
        if all(run(source, pair["input"]) == pair["output"] for pair in train):
            survivors.append({"offset_mode": mode})
    if survivors != [settings]:
        raise ValueError(f"demonstrations do not identify selected label rule: {survivors}")

    query_checks = []
    for pair in test:
        actual = run(expected_program, pair["input"])
        if actual != pair["output"]:
            raise ValueError("query label differs from selected rule")
        query_checks.append({"input_sha256": digest(pair["input"]), "label_matches": True})
    return {
        "fit_scope": "demonstrations_only",
        "survivors": survivors,
        "queries": query_checks,
    }


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    selected = settings_value(settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    train = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
        "variant_approved": False,
        "training_admitted": False,
    }
    episode["certificate"] = certify(episode)
    return episode
