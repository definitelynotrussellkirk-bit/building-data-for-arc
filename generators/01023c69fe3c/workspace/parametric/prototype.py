#!/usr/bin/env python3
"""Native prototype for the crosshair/interior-cue payload family.

``canonical`` is byte-for-byte the selected ARC rule. ``interior_cue`` first
constructs that canonical crosshair/interior grid (step A), uses its derived
blue interior as an input-dependent selector (the intermediate), then restores
remote cells of the selected input color as azure (step B).  Inputs are sampled
independently of the private setting.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "01023c69fe3c"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "interior_cue")
DEFAULT_MODE = "canonical"
DEFAULT_SETTINGS = {"mode": DEFAULT_MODE}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
STATUS = "reviewer-ready prototype; owner acceptance and training admission pending"

_INTERIOR_CUE_PROGRAM = """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (dots (find-color g 2))
         (p1 (first dots))
         (p2 (last dots))
         (r1 (first p1))
         (c1 (second p1))
         (r2 (first p2))
         (c2 (second p2))
         (minr (min r1 r2))
         (maxr (max r1 r2))
         (minc (min c1 c2))
         (maxc (max c1 c2))
         (base
           (grid-from-fn h w
             (lambda (r c)
               (cond
                 ((or (= r r1) (= r r2) (= c c1) (= c c2)) 2)
                 ((and (>= r minr) (<= r maxr)
                       (>= c minc) (<= c maxc)) 1)
                 (else 0)))))
         (cue-pos
           (find-first
             (lambda (p)
               (let* ((r (first p))
                      (c (second p))
                      (v (at g r c)))
                 (and (= (at base r c) 1)
                      (not (= v 0))
                      (not (= v 2)))))
             (grid-positions g)))
         (cue-color
           (if cue-pos
               (at g (first cue-pos) (second cue-pos))
               -1)))
    (grid-from-fn h w
      (lambda (r c)
        (let ((b (at base r c))
              (v (at g r c)))
          (if (and (= b 0) (= v cue-color)) 8 b)))))))"""

# Deliberately wrong causal counterfactual: stage A expands the selector by one
# cell in every direction, so the top-ring decoy is read before the true cue.
_WRONG_EXPANDED_PROGRAM = """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (dots (find-color g 2))
         (p1 (first dots))
         (p2 (last dots))
         (r1 (first p1))
         (c1 (second p1))
         (r2 (first p2))
         (c2 (second p2))
         (minr (min r1 r2))
         (maxr (max r1 r2))
         (minc (min c1 c2))
         (maxc (max c1 c2))
         (base
           (grid-from-fn h w
             (lambda (r c)
               (cond
                 ((or (= r r1) (= r r2) (= c c1) (= c c2)) 2)
                 ((and (>= r minr) (<= r maxr)
                       (>= c minc) (<= c maxc)) 1)
                 (else 0)))))
         (cue-pos
           (find-first
             (lambda (p)
               (let* ((r (first p))
                      (c (second p))
                      (v (at g r c)))
                 (and (>= r (- minr 1)) (<= r (+ maxr 1))
                      (>= c (- minc 1)) (<= c (+ maxc 1))
                      (not (= v 0)) (not (= v 2)))))
             (grid-positions g)))
         (cue-color
           (if cue-pos
               (at g (first cue-pos) (second cue-pos))
               -1)))
    (grid-from-fn h w
      (lambda (r c)
        (let ((b (at base r c))
              (v (at g r c)))
          (if (and (= b 0) (= v cue-color)) 8 b)))))))"""


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    with canonical_path(Path(root)).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise ValueError(f"canonical task not found: {TASK_ID}")


def _validate_mode(mode: str) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def validate_settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    return _validate_mode(settings["mode"])


def program_for(mode: str = DEFAULT_MODE, *, root: Path | str = ROOT) -> str:
    mode = _validate_mode(mode)
    if mode == DEFAULT_MODE:
        return canonical_record(root=root)["program_solution"]
    return _INTERIOR_CUE_PROGRAM


def wrong_intermediate_program() -> str:
    return _WRONG_EXPANDED_PROGRAM


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def validate_counts(demos: int, queries: int) -> None:
    _integer(demos, DEMO_LIMITS[0], DEMO_LIMITS[1], "demos")
    _integer(queries, QUERY_LIMITS[0], QUERY_LIMITS[1], "queries")


def _validate_grid(grid: object) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if any(type(row) is not list or not row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with 1..30 columns")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    return len(grid), width


def _anchors(grid: list[list[int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    _validate_grid(grid)
    dots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(dots) != 2:
        raise ValueError("input must contain exactly two red anchors")
    (r1, c1), (r2, c2) = dots
    if r1 == r2 or c1 == c2:
        raise ValueError("red anchors must have distinct rows and columns")
    return dots[0], dots[1]


def canonical_intermediate(grid: list[list[int]]) -> list[list[int]]:
    h, w = _validate_grid(grid)
    (r1, c1), (r2, c2) = _anchors(grid)
    minr, maxr = sorted((r1, r2))
    minc, maxc = sorted((c1, c2))
    return [
        [
            2
            if r in (r1, r2) or c in (c1, c2)
            else 1
            if minr <= r <= maxr and minc <= c <= maxc
            else 0
            for c in range(w)
        ]
        for r in range(h)
    ]


def cue_profile(grid: list[list[int]]) -> dict[str, Any]:
    base = canonical_intermediate(grid)
    candidates = [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if base[r][c] == 1 and value not in (0, 2)
    ]
    cue_color = candidates[0][2] if candidates else None
    payload = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if cue_color is not None and base[r][c] == 0 and value == cue_color
    ]
    return {
        "base": base,
        "cue_candidates": candidates,
        "cue_color": cue_color,
        "payload": payload,
    }


def _overlay_color(
    grid: list[list[int]],
    color: int | None,
    *,
    paint: int = 8,
    base_only: bool = True,
) -> list[list[int]]:
    base = canonical_intermediate(grid)
    if color is None:
        return [row[:] for row in base]
    return [
        [
            paint
            if grid[r][c] == color and (base[r][c] == 0 or not base_only)
            else base[r][c]
            for c in range(len(base[0]))
        ]
        for r in range(len(base))
    ]


def transform(grid: list[list[int]], mode: str = DEFAULT_MODE) -> list[list[int]]:
    mode = _validate_mode(mode)
    profile = cue_profile(grid)
    if mode == DEFAULT_MODE:
        return [row[:] for row in profile["base"]]
    return _overlay_color(grid, profile["cue_color"])


def wrong_intermediate_value(grid: list[list[int]]) -> dict[str, Any]:
    (r1, c1), (r2, c2) = _anchors(grid)
    minr, maxr = sorted((r1, r2))
    minc, maxc = sorted((c1, c2))
    candidates = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if minr - 1 <= r <= maxr + 1
        and minc - 1 <= c <= maxc + 1
        and value not in (0, 2)
    ]
    return {
        "selector": "one-cell-expanded anchor rectangle, row-major first colored cell",
        "candidates": candidates,
        "cue_color": candidates[0][2] if candidates else None,
    }


def wrong_intermediate_transform(grid: list[list[int]]) -> list[list[int]]:
    return _overlay_color(grid, wrong_intermediate_value(grid)["cue_color"])


def _grid_literal(grid: list[list[int]]) -> str:
    _validate_grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    return bridge.eval_text(f"({wrap_rule(program)} {_grid_literal(grid)})")


_DEMO_PROFILES = (
    {"size": (9, 12), "min_spans": (5, 6), "counts": (3, 5, 2, 4), "crosshair_decoy": True},
    {"size": (12, 10), "min_spans": (7, 5), "counts": (5, 2, 7, 4), "crosshair_decoy": False},
    {"size": (14, 17), "min_spans": (8, 10), "counts": (4, 6, 5, 3), "crosshair_decoy": True},
    {"size": (18, 14), "min_spans": (11, 8), "counts": (6, 4, 7, 5), "crosshair_decoy": False},
    {"size": (22, 25), "min_spans": (14, 16), "counts": (7, 8, 6, 9), "crosshair_decoy": True},
    {"size": (26, 21), "min_spans": (18, 14), "counts": (8, 6, 10, 7), "crosshair_decoy": False},
)
_QUERY_PROFILES = (
    {"size": (8, 12), "min_spans": (4, 6), "counts": (3, 4, 2, 3), "crosshair_decoy": True},
    {"size": (15, 15), "min_spans": (9, 9), "counts": (5, 7, 4, 6), "crosshair_decoy": False},
    {"size": (24, 27), "min_spans": (16, 18), "counts": (7, 8, 9, 6), "crosshair_decoy": True},
    {"size": (30, 30), "min_spans": (22, 22), "counts": (8, 9, 7, 10), "crosshair_decoy": True},
)
_DECOR_COLORS = (3, 4, 5, 6, 7, 9)
# First two rows jointly use all six colors and have different cue colors. This
# defeats every fixed-color selector at the declared two-demonstration minimum.
_ROLE_OFFSETS = (
    (0, 1, 2, 3),
    (1, 4, 5, 0),
    (2, 5, 0, 4),
    (3, 0, 4, 5),
    (4, 2, 3, 1),
    (5, 3, 1, 2),
)


def _rng(seed: int, *parts: object) -> random.Random:
    payload = "|".join((TASK_ID, "cue-family-v2", str(seed), *(str(part) for part in parts)))
    value = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:16], "big")
    return random.Random(value)


def _role_colors(seed: int, split: str, index: int) -> tuple[int, int, int, int]:
    offset = _rng(seed, split, "palette-rotation").randrange(len(_DECOR_COLORS))
    palette = _DECOR_COLORS[offset:] + _DECOR_COLORS[:offset]
    role_offsets = _ROLE_OFFSETS[index % len(_ROLE_OFFSETS)]
    return tuple(palette[position] for position in role_offsets)  # type: ignore[return-value]


def _choose_box(
    h: int,
    w: int,
    min_span_rows: int,
    min_span_cols: int,
    rng: random.Random,
) -> tuple[int, int, int, int]:
    # Two-cell outer margins are reserved for payloads and a one-cell-ring decoy.
    max_r1 = h - 3 - (min_span_rows - 1)
    max_c1 = w - 3 - (min_span_cols - 1)
    if max_r1 < 2 or max_c1 < 2:
        raise ValueError("profile cannot fit its declared anchor span and margins")
    r1 = rng.randint(2, max_r1)
    c1 = rng.randint(2, max_c1)
    r2 = rng.randint(r1 + min_span_rows - 1, h - 3)
    c2 = rng.randint(c1 + min_span_cols - 1, w - 3)
    return r1, c1, r2, c2


def _ring_positions(r1: int, c1: int, r2: int, c2: int) -> list[tuple[int, int]]:
    return (
        [(r1 - 1, c) for c in range(c1 + 1, c2)]
        + [(r2 + 1, c) for c in range(c1 + 1, c2)]
        + [(r, c1 - 1) for r in range(r1 + 1, r2)]
        + [(r, c2 + 1) for r in range(r1 + 1, r2)]
    )


def _take_spread(
    available: dict[int, list[tuple[int, int]]],
    count: int,
    start: int,
) -> list[tuple[int, int]]:
    chosen: list[tuple[int, int]] = []
    for step in range(count):
        for offset in range(4):
            zone = (start + step + offset) % 4
            if available[zone]:
                chosen.append(available[zone].pop())
                break
        else:
            raise ValueError("profile ran out of payload positions")
    return chosen


def sample_scene(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "demo":
        profiles = _DEMO_PROFILES
    elif split == "query":
        profiles = _QUERY_PROFILES
    else:
        raise ValueError("split must be demo or query")
    _integer(index, 0, len(profiles) - 1, "profile index")
    profile = profiles[index]
    h, w = profile["size"]
    min_span_rows, min_span_cols = profile["min_spans"]
    rng = _rng(seed, split, index, "scene")
    r1, c1, r2, c2 = _choose_box(h, w, min_span_rows, min_span_cols, rng)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    anchors = ((r1, c1), (r2, c2)) if rng.randrange(2) else ((r1, c2), (r2, c1))
    for r, c in anchors:
        grid[r][c] = 2

    cue_color, ring_color, other_a, other_b = _role_colors(seed, split, index)
    interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    if not interior:
        raise ValueError("profile has no strict interior")
    cue = rng.choice(interior)
    grid[cue[0]][cue[1]] = cue_color

    top_ring = [(r1 - 1, c) for c in range(c1 + 1, c2)]
    ring_decoy = rng.choice(top_ring)
    grid[ring_decoy[0]][ring_decoy[1]] = ring_color
    # Keep every remote payload outside the one-cell-expanded selector zone.
    # Otherwise an expanded-mask shortcut can encounter a corner payload before
    # the deliberately placed top-ring decoy and accidentally recover the right
    # cue color.
    forbidden = {
        (r, c)
        for r in range(max(0, r1 - 1), min(h - 1, r2 + 1) + 1)
        for c in range(max(0, c1 - 1), min(w - 1, c2 + 1) + 1)
    }

    base = canonical_intermediate(grid)
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if base[r][c] == 0 and (r, c) not in forbidden and grid[r][c] == 0
    ]
    zones: dict[int, list[tuple[int, int]]] = {0: [], 1: [], 2: [], 3: []}
    for r, c in candidates:
        zone = (2 if r >= h / 2 else 0) + (1 if c >= w / 2 else 0)
        zones[zone].append((r, c))
    for zone, cells in zones.items():
        _rng(seed, split, index, "zone", zone).shuffle(cells)

    for color_index, (color, count) in enumerate(
        zip((cue_color, ring_color, other_a, other_b), profile["counts"])
    ):
        for r, c in _take_spread(zones, count, (color_index + index) % 4):
            grid[r][c] = color

    if profile["crosshair_decoy"]:
        crosshair = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if base[r][c] == 2 and grid[r][c] == 0 and (r, c) not in forbidden
        ]
        if not crosshair:
            raise ValueError("profile has no free crosshair cell")
        r, c = rng.choice(crosshair)
        grid[r][c] = cue_color

    facts = scene_profile(grid)
    if len(facts["cue_candidates"]) != 1 or len(facts["ring_decoys"]) != 1:
        raise ValueError("constructed scene violates cue/ring uniqueness")
    if len(facts["payload"]) != profile["counts"][0]:
        raise ValueError("constructed scene lost selected payload cells")
    return grid


def scene_profile(grid: list[list[int]]) -> dict[str, Any]:
    h, w = _validate_grid(grid)
    dots = list(_anchors(grid))
    rows = sorted(r for r, _ in dots)
    cols = sorted(c for _, c in dots)
    r1, r2 = rows
    c1, c2 = cols
    cue = cue_profile(grid)
    ring = [
        (r, c, grid[r][c])
        for r, c in _ring_positions(r1, c1, r2, c2)
        if grid[r][c] not in (0, 2)
    ]
    return {
        "grid_h": h,
        "grid_w": w,
        "anchors": dots,
        "anchor_span_rows": r2 - r1 + 1,
        "anchor_span_cols": c2 - c1 + 1,
        "nonzero_count": sum(value != 0 for row in grid for value in row),
        "cue_candidates": cue["cue_candidates"],
        "cue_color": cue["cue_color"],
        "payload": cue["payload"],
        "ring_decoys": ring,
        "ring_decoy_color": ring[0][2] if len(ring) == 1 else None,
        "decor_counts": dict(sorted(Counter(
            value for row in grid for value in row if value not in (0, 2)
        ).items())),
    }


def _swap_colors(grid: list[list[int]], first: int, second: int) -> list[list[int]]:
    _validate_grid(grid)
    if type(first) is not int or type(second) is not int or first == second:
        raise ValueError("swap colors must be distinct exact integers")
    return [
        [second if value == first else first if value == second else value for value in row]
        for row in grid
    ]


def swap_cue_and_ring_colors(grid: list[list[int]]) -> list[list[int]]:
    """Swap only the two selector cells, leaving both remote payloads fixed.

    This crossed control holds dimensions, anchors, payload positions and color
    frequencies fixed while changing the derived interior cue and final payload.
    """
    profile = scene_profile(grid)
    cue, ring = profile["cue_color"], profile["ring_decoy_color"]
    if cue is None or ring is None or cue == ring:
        raise ValueError("scene needs distinct cue and ring colors")
    if len(profile["cue_candidates"]) != 1 or len(profile["ring_decoys"]) != 1:
        raise ValueError("scene needs one cue cell and one ring decoy")
    result = copy.deepcopy(grid)
    cue_r, cue_c, _ = profile["cue_candidates"][0]
    ring_r, ring_c, _ = profile["ring_decoys"][0]
    result[cue_r][cue_c] = ring
    result[ring_r][ring_c] = cue
    return result


def swap_nuisance_colors(grid: list[list[int]]) -> list[list[int]]:
    profile = scene_profile(grid)
    excluded = {profile["cue_color"], profile["ring_decoy_color"]}
    nuisance = sorted(color for color in profile["decor_counts"] if color not in excluded)
    if len(nuisance) < 2:
        raise ValueError("scene needs two nuisance colors")
    return _swap_colors(grid, nuisance[0], nuisance[1])


def _decor_selector_transform(grid: list[list[int]], selector: str) -> list[list[int]]:
    values = [value for row in grid for value in row if value not in (0, 2)]
    counts = Counter(values)
    if not counts:
        return canonical_intermediate(grid)
    if selector == "most":
        color = min(counts, key=lambda value: (-counts[value], value))
    elif selector == "least":
        color = min(counts, key=lambda value: (counts[value], value))
    else:
        raise ValueError(selector)
    return _overlay_color(grid, color)


def _all_decor_payloads(grid: list[list[int]]) -> list[list[int]]:
    base = canonical_intermediate(grid)
    return [
        [8 if base[r][c] == 0 and grid[r][c] not in (0, 2) else base[r][c]
         for c in range(len(base[0]))]
        for r in range(len(base))
    ]


def _preserve_payload_color(grid: list[list[int]]) -> list[list[int]]:
    color = cue_profile(grid)["cue_color"]
    return _overlay_color(grid, color, paint=color if color is not None else 8)


def _paint_cue_cells_too(grid: list[list[int]]) -> list[list[int]]:
    return _overlay_color(grid, cue_profile(grid)["cue_color"], base_only=False)


def _fixed_color_transform(color: int) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: _overlay_color(grid, color)


def _rival_bank() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    bank: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "canonical_only": lambda grid: transform(grid, "canonical"),
        "interior_cue": lambda grid: transform(grid, "interior_cue"),
        "expanded_interior": wrong_intermediate_transform,
        "all_decor_payloads": _all_decor_payloads,
        "most_frequent_decor": lambda grid: _decor_selector_transform(grid, "most"),
        "least_frequent_decor": lambda grid: _decor_selector_transform(grid, "least"),
        "preserve_payload_color": _preserve_payload_color,
        "paint_cue_cells_too": _paint_cue_cells_too,
    }
    bank.update({f"fixed_color_{color}": _fixed_color_transform(color) for color in _DECOR_COLORS})
    return bank


def _digest_grid(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _episode_mode(episode: dict[str, Any]) -> str:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    return validate_settings(episode.get("settings"))


def _verify_episode_core(episode: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    mode = _episode_mode(episode)
    seed = _integer(episode.get("seed"), 0, 2**63 - 1, "seed")
    del seed
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode train/test must be lists")
    validate_counts(len(train), len(test))
    pairs = train + test
    normalized: list[dict[str, Any]] = []
    for pair in pairs:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each episode pair must contain exactly input and output")
        _validate_grid(pair["input"])
        _validate_grid(pair["output"])
        normalized.append(pair)
    digests = [_digest_grid(pair["input"]) for pair in normalized]
    if len(digests) != len(set(digests)):
        raise ValueError("all demonstration and query inputs must be distinct")
    expected_program = program_for(mode)
    if episode.get("program_solution") != expected_program:
        raise ValueError("episode program differs from selected setting")
    expected_hash = hashlib.sha256(expected_program.encode("utf-8")).hexdigest()
    if episode.get("program_sha256") != expected_hash:
        raise ValueError("episode program hash differs from selected program")
    for index, pair in enumerate(normalized):
        if pair["output"] != transform(pair["input"], mode):
            raise ValueError(f"label mismatch at pair {index}")
    return mode, normalized


def certify(episode: dict[str, Any]) -> dict[str, Any]:
    mode, _ = _verify_episode_core(episode)
    train = episode["train"]
    survivors = [
        {"mode": candidate}
        for candidate in MODES
        if all(transform(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    if survivors != [{"mode": mode}]:
        raise ValueError(f"demonstrations do not identify selected setting: {survivors}")

    selected_name = "canonical_only" if mode == "canonical" else "interior_cue"
    details: dict[str, Any] = {}
    failures: list[str] = []
    addressed: list[str] = []
    for name, rival in _rival_bank().items():
        differing = [
            index
            for index, pair in enumerate(train)
            if rival(pair["input"]) != pair["output"]
        ]
        if name == selected_name:
            if differing:
                raise ValueError(f"selected mirror {name} disagrees with demonstrations")
            status = "selected_reference"
        elif differing:
            status = "refuted"
        else:
            status = "survives_all_demonstrations"
            failures.append(name)
        addressed.append(name)
        details[name] = {"status": status, "distinguishing_demo_indices": differing}
    return {
        "survivors": survivors,
        "minimum_demonstrations_checked": len(train),
        "rivals_refuted": addressed,
        "all_rivals_refuted": not failures,
        "unrefuted_rivals": failures,
        "rival_checks": details,
    }


def verify_episode(episode: dict[str, Any]) -> None:
    mode, _ = _verify_episode_core(episode)
    certificate = certify(episode)
    if certificate["survivors"] != [{"mode": mode}] or not certificate["all_rivals_refuted"]:
        raise ValueError("episode teaching certificate failed")


def generate_episode(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    mode = _validate_mode(mode)
    validate_counts(demos, queries)
    train_inputs = [sample_scene(seed, "demo", index) for index in range(demos)]
    query_bank = [sample_scene(seed, "query", index) for index in range(4)]
    order = list(range(4))
    _rng(seed, "query-presentation").shuffle(order)
    test_inputs = [query_bank[index] for index in order[:queries]]
    all_inputs = train_inputs + test_inputs
    fingerprints = {_digest_grid(grid) for grid in all_inputs}
    if len(fingerprints) != len(all_inputs):
        raise ValueError("all demonstration and query inputs must be distinct")
    program = program_for(mode)
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"mode": mode},
        "train": [{"input": grid, "output": transform(grid, mode)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, mode)} for grid in test_inputs],
        "program_solution": program,
        "program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
        "query_source_indices": order[:queries],
        "status": STATUS,
    }
    episode["certificate"] = certify(episode)
    verify_episode(episode)
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    _integer(query_index, 0, len(test) - 1, "query_index")
    visible_train = []
    for pair in train:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("demonstrations need input/output")
        _validate_grid(pair["input"])
        _validate_grid(pair["output"])
        visible_train.append({"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])})
    query = test[query_index]
    if type(query) is not dict or "input" not in query:
        raise ValueError("query needs input")
    _validate_grid(query["input"])
    return {
        "train": visible_train,
        "test": [{"input": copy.deepcopy(query["input"])}],
    }


def sequential_views(episode: dict[str, Any]) -> list[dict[str, Any]]:
    test = episode.get("test") if isinstance(episode, dict) else None
    if type(test) is not list or not test:
        raise ValueError("episode needs queries")
    return [public_turn(episode, index) for index in range(len(test))]


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(public_challenge_bytes(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(episode)
