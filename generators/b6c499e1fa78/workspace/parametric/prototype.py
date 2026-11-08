"""Source-bound parametric family for b6c499e1fa78.

The source task marks gray keys red when they fit a blue-wall opening or branch.
The episode-fixed ``branch_policy`` preserves that exact rule as ``unconditional``
and adds a nearby, genuinely sequential setting ``matched_area``:

A. Find every key whose top rows fit an opening and derive the set of their
   *full occupied areas* (the keys have tails, so this is not opening area).
B. Recolor all fitting keys, and recolor a branched key only when its full area
   belongs to the input-derived set from A.

Inputs are generated independently of the setting.  The first two demonstrations
are constructive crossed controls that distinguish full key area from opening
area, bounding-box area, parity, residue, thresholds, first-key, and unlock-all
shortcuts while retaining the canonical match-or-branch reasoning.
"""
from __future__ import annotations

import copy
from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "b6c499e1fa78"
PARAMETER = "branch_policy"
BRANCH_POLICIES = ("unconditional", "matched_area")
DEFAULT = {PARAMETER: "unconditional"}
SETTINGS = [{PARAMETER: value} for value in BRANCH_POLICIES]
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERIES = 4
MAX_SEED = 2**63 - 1

_PROGRAM_FILES = {
    "unconditional": HERE / "canonical.rkt",
    "matched_area": HERE / "matched_area.rkt",
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Two-row opening shapes.  Every matching key extends below the opening-height
# slice, making full key area an input-derived quantity distinct from opening area.
_OPEN_L3 = ((0, 0), (1, 0), (1, 1))
_OPEN_Z4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_OPEN_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_OPEN_J4 = ((0, 0), (0, 1), (0, 2), (1, 0))

_MATCH_KEYS: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (1, 0), (1, 1), (2, 1)),
    5: ((0, 0), (1, 0), (1, 1), (2, 1), (3, 1)),
    6: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (3, 2)),
}
_MATCH_OPENINGS = {4: _OPEN_L3, 5: _OPEN_L3, 6: _OPEN_Z4}

_BRANCH_KEYS: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 1), (1, 2), (1, 3)),
}

# Non-branching, non-matching distractors.  They make color/frequency/"all gray"
# shortcuts fail without introducing a third semantic branch.
_DECOYS: dict[str, tuple[tuple[int, int], ...]] = {
    "bar3": ((0, 0), (0, 1), (0, 2)),
    "snake6": ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)),
    "snake9": ((0, 0), (0, 1), (0, 2), (0, 3),
               (1, 3), (2, 3), (2, 4), (2, 5), (3, 5)),
}

_DEMO_DIMS = ((18, 18), (19, 20), (21, 22), (23, 24), (25, 26), (27, 28))
_QUERY_DIMS = ((17, 17), (21, 21), (25, 25), (30, 30))

# The first two profiles are the minimum lesson and are intentionally fixed in
# semantic areas across every seed.  Geometry, mirror, wall row and placement vary.
_DEMO_PROFILES = (
    {"match": (4, 6), "branch": (4, 5, 6, 7), "decoy": ("snake6",), "extra_open": ()},
    {"match": (5,), "branch": (4, 5, 7, 8), "decoy": ("snake6", "bar3"), "extra_open": (_OPEN_SQUARE4,)},
    {"match": (4,), "branch": (4, 5, 6, 8), "decoy": ("snake9",), "extra_open": (_OPEN_J4,)},
    {"match": (6,), "branch": (4, 6, 7), "decoy": ("snake6", "bar3"), "extra_open": (_OPEN_SQUARE4,)},
    {"match": (4, 5), "branch": (4, 5, 8), "decoy": ("snake9",), "extra_open": (_OPEN_J4,)},
    {"match": (5, 6), "branch": (5, 6, 7, 8), "decoy": ("snake6", "snake9"), "extra_open": (_OPEN_SQUARE4,)},
)
_QUERY_PROFILES = (
    {"match": (4,), "branch": (4, 5, 6, 7), "decoy": ("snake6",), "extra_open": (_OPEN_SQUARE4,)},
    {"match": (5,), "branch": (4, 5, 6, 8), "decoy": ("snake9",), "extra_open": (_OPEN_J4,)},
    {"match": (6,), "branch": (4, 5, 6, 7, 8), "decoy": ("snake6", "bar3"), "extra_open": (_OPEN_SQUARE4,)},
    {"match": (4, 5, 6), "branch": (4, 5, 6, 7, 8),
     "decoy": ("snake6", "snake9"), "extra_open": (_OPEN_SQUARE4,)},
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in BRANCH_POLICIES:
        raise ValueError(f"{PARAMETER} must be one of {BRANCH_POLICIES!r}")
    return {PARAMETER: value}


def _grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    return grid


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    raw = f"{TASK_ID}|matched-area-v1|{seed}|{domain}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def program(settings: Any) -> str:
    selected = _settings(settings)
    return _PROGRAM_FILES[selected[PARAMETER]].read_text(encoding="utf-8")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _mirror(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in cells)


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    unseen = set(cells)
    found: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        found.append(component)
    return found


def _branched(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    return any(
        sum((r + dr, c + dc) in cells for dr, dc in _CARDINAL) >= 3
        for r, c in cells
    )


def _opening_cells(grid: list[list[int]]) -> tuple[list[set[tuple[int, int]]], tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    wall_rows = [r for r in range(h) if any(grid[r][c] == 1 for c in range(w))]
    if not wall_rows:
        raise ValueError("scene must contain a blue wall")
    rmin, rmax = min(wall_rows), max(wall_rows)
    cells: set[tuple[int, int]] = set()
    for r in range(rmin, rmax + 1):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            blue_above = any(grid[r2][c] == 1 for r2 in range(rmin, r))
            blue_left = any(grid[r][c2] == 1 for c2 in range(0, c))
            blue_right = any(grid[r][c2] == 1 for c2 in range(c + 1, w))
            if blue_above and blue_left and blue_right:
                cells.add((r, c))
    openings = _components(cells)
    if not openings:
        raise ValueError("scene must contain at least one wall opening")
    return openings, (rmin, rmax)


def _gray_pieces(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    return _components(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    )


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    cells = tuple(cells)
    return ((max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
            * (max(c for _, c in cells) - min(c for _, c in cells) + 1))


def _matches(piece: set[tuple[int, int]], openings: list[set[tuple[int, int]]]) -> bool:
    top = min(r for r, _ in piece)
    for opening in openings:
        height = max(r for r, _ in opening) - min(r for r, _ in opening) + 1
        top_slice = {(r, c) for r, c in piece if r < top + height}
        normalized = _normalize(top_slice)
        opening_norm = _normalize(opening)
        if normalized == opening_norm or normalized == _mirror(opening_norm):
            return True
    return False


def analyze_scene(grid: Any) -> dict[str, Any]:
    grid = _grid(grid)
    openings, wall_span = _opening_cells(grid)
    pieces = _gray_pieces(grid)
    if not pieces:
        raise ValueError("scene must contain at least one gray key")
    records: list[dict[str, Any]] = []
    for cells in sorted(pieces, key=lambda x: (min(x), len(x))):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        record = {
            "cells": tuple(sorted(cells)),
            "area": len(cells),
            "bbox_area": _bbox_area(cells),
            "top": min(rows),
            "left": min(cols),
            "bottom": max(rows),
            "right": max(cols),
            "branched": _branched(cells),
            "matches": _matches(cells, openings),
        }
        records.append(record)
    matched = [p for p in records if p["matches"]]
    branched = [p for p in records if p["branched"]]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "wall_span": list(wall_span),
        "openings": [tuple(sorted(x)) for x in openings],
        "opening_areas": [len(x) for x in openings],
        "pieces": records,
        "gray_cells": tuple(sorted(cell for p in records for cell in p["cells"])),
        "matched_piece_areas": [p["area"] for p in matched],
        "matched_piece_bbox_areas": [p["bbox_area"] for p in matched],
        "branch_areas": [p["area"] for p in branched],
        "matched_count": len(matched),
        "branched_count": len(branched),
    }


def _selected_piece_indexes(analysis: dict[str, Any], policy: str) -> set[int]:
    matched_areas = {p["area"] for p in analysis["pieces"] if p["matches"]}
    chosen: set[int] = set()
    for index, piece in enumerate(analysis["pieces"]):
        if piece["matches"]:
            chosen.add(index)
        elif policy == "unconditional" and piece["branched"]:
            chosen.add(index)
        elif policy == "matched_area" and piece["branched"] and piece["area"] in matched_areas:
            chosen.add(index)
    return chosen


def _recolor(grid: list[list[int]], indexes: set[int], analysis: dict[str, Any]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for index in indexes:
        for r, c in analysis["pieces"][index]["cells"]:
            out[r][c] = 2
    return out


def apply_rule(grid: Any, policy: str) -> list[list[int]]:
    if type(policy) is not str or policy not in BRANCH_POLICIES:
        raise ValueError(f"policy must be one of {BRANCH_POLICIES!r}")
    checked = _grid(grid)
    analysis = analyze_scene(checked)
    return _recolor(checked, _selected_piece_indexes(analysis, policy), analysis)


def _paint_wall(grid: list[list[int]], wall_top: int,
                openings: list[tuple[tuple[int, int], ...]], rng: random.Random) -> None:
    h, w = len(grid), len(grid[0])
    if wall_top < 1 or wall_top + 2 >= h // 2 + 1:
        raise RuntimeError("invalid wall position")
    for r in range(wall_top, wall_top + 3):
        for c in range(w):
            grid[r][c] = 1
    entries = list(openings)
    rng.shuffle(entries)
    widths = [_dims(shape)[1] for shape in entries]
    gap = 2
    total = sum(widths) + gap * (len(entries) - 1)
    if total > w - 2:
        raise RuntimeError("opening profile does not fit wall")
    slack = w - 2 - total
    start = 1 + (rng.randrange(slack + 1) if slack else 0)
    cursor = start
    for shape in entries:
        for r, c in shape:
            grid[wall_top + 1 + r][cursor + c] = 0
        cursor += _dims(shape)[1] + gap


def _forbidden(occupied: set[tuple[int, int]]) -> set[tuple[int, int]]:
    blocked = set(occupied)
    for r, c in occupied:
        blocked.update((r + dr, c + dc) for dr, dc in _CARDINAL)
    return blocked


def _place_shapes(h: int, w: int, min_row: int,
                  objects: list[dict[str, Any]], rng: random.Random,
                  border_stress: bool) -> list[set[tuple[int, int]]]:
    """Place same-color components with a one-cell cardinal moat.

    Border constraints are assigned before the free objects.  Repeated complete
    constructive attempts avoid silently dropping an object under dense 30x30
    stress while remaining deterministic for a seed.
    """
    for attempt in range(120):
        local = random.Random(rng.getrandbits(128) ^ attempt)
        order = list(range(len(objects)))
        local.shuffle(order)
        required: dict[int, str] = {}
        if border_stress:
            required[order[0]] = "left"
            required[order[1]] = "right"
            required[order[2]] = "bottom"
            order = order[:3] + sorted(order[3:], key=lambda i: -len(objects[i]["shape"]))
        else:
            order.sort(key=lambda i: -len(objects[i]["shape"]))
            local.shuffle(order)
        occupied: set[tuple[int, int]] = set()
        placed: list[set[tuple[int, int]] | None] = [None] * len(objects)
        ok = True
        for index in order:
            shape = objects[index]["shape"]
            sh, sw = _dims(shape)
            candidates = [(r, c)
                          for r in range(min_row, h - sh + 1)
                          for c in range(0, w - sw + 1)]
            req = required.get(index)
            if req == "left":
                candidates = [(r, c) for r, c in candidates if c == 0]
            elif req == "right":
                candidates = [(r, c) for r, c in candidates if c == w - sw]
            elif req == "bottom":
                candidates = [(r, c) for r, c in candidates if r == h - sh]
            local.shuffle(candidates)
            blocked = _forbidden(occupied)
            choice = None
            for r0, c0 in candidates:
                absolute = {(r0 + r, c0 + c) for r, c in shape}
                if absolute.isdisjoint(blocked):
                    choice = absolute
                    break
            if choice is None:
                ok = False
                break
            placed[index] = choice
            occupied.update(choice)
        if ok and all(x is not None for x in placed):
            return [x for x in placed if x is not None]
    raise RuntimeError("unable to place all gray keys with component separation")


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    if domain not in ("demo", "query"):
        raise ValueError("domain must be demo or query")
    profiles = _DEMO_PROFILES if domain == "demo" else _QUERY_PROFILES
    dims = _DEMO_DIMS if domain == "demo" else _QUERY_DIMS
    profile = dict(profiles[index])
    # Cross the intended intermediate against query dimensions/profile slots:
    # at each of the first three fixed dimensions, fresh seeds choose among
    # full matched-key areas 4, 5 and 6.  The 30x30 stress case deliberately
    # keeps all three while its placement/mirroring nuisance variables vary.
    if domain == "query" and index < 3:
        choices = (4, 5, 6)
        selected = choices[_rng(seed, "query-intermediate", index).randrange(len(choices))]
        profile["match"] = (selected,)
    h, w = dims[index]
    rng = _rng(seed, domain, index)
    grid = [[0] * w for _ in range(h)]
    wall_top = 1 + (rng.randrange(2) if h >= 21 else 0)

    openings: list[tuple[tuple[int, int], ...]] = []
    objects: list[dict[str, Any]] = []
    for ordinal, area in enumerate(profile["match"]):
        mirror = bool(rng.getrandbits(1))
        opening = _MATCH_OPENINGS[area]
        key = _MATCH_KEYS[area]
        if mirror:
            opening = _mirror(opening)
            key = _mirror(key)
        openings.append(opening)
        objects.append({"role": f"match-{area}-{ordinal}", "shape": key})
    for opening in profile["extra_open"]:
        openings.append(_mirror(opening) if rng.getrandbits(1) else _normalize(opening))
    _paint_wall(grid, wall_top, openings, _rng(seed, domain + "-wall", index))

    for ordinal, area in enumerate(profile["branch"]):
        shape = _BRANCH_KEYS[area]
        if rng.getrandbits(1):
            shape = _mirror(shape)
        objects.append({"role": f"branch-{area}-{ordinal}", "shape": shape})
    for ordinal, name in enumerate(profile["decoy"]):
        shape = _DECOYS[name]
        if rng.getrandbits(1):
            shape = _mirror(shape)
        objects.append({"role": f"decoy-{name}-{ordinal}", "shape": shape})

    placements = _place_shapes(
        h, w, wall_top + 4, objects,
        _rng(seed, domain + "-pieces", index),
        border_stress=(domain == "query" and index == 3),
    )
    for cells in placements:
        for r, c in cells:
            grid[r][c] = 5

    analysis = analyze_scene(grid)
    expected_match = sorted(profile["match"])
    expected_branch = sorted(profile["branch"])
    if sorted(analysis["matched_piece_areas"]) != expected_match:
        raise RuntimeError(
            f"constructed matching roles changed: {analysis['matched_piece_areas']} != {expected_match}"
        )
    if sorted(analysis["branch_areas"]) != expected_branch:
        raise RuntimeError(
            f"constructed branch roles changed: {analysis['branch_areas']} != {expected_branch}"
        )
    if apply_rule(grid, "unconditional") == apply_rule(grid, "matched_area"):
        raise RuntimeError("scene does not distinguish branch policies")
    if domain == "query" and index == 3:
        gray = set(analysis["gray_cells"])
        if not ({0, w - 1} <= {c for _, c in gray} and h - 1 in {r for r, _ in gray}):
            raise RuntimeError("30x30 scene lost boundary stress")
    return grid


def _rival_indexes(name: str, analysis: dict[str, Any]) -> set[int]:
    pieces = analysis["pieces"]
    matched = {i for i, p in enumerate(pieces) if p["matches"]}
    branches = {i for i, p in enumerate(pieces) if p["branched"]}
    matched_areas = [p["area"] for p in pieces if p["matches"]]
    opening_areas = set(analysis["opening_areas"])
    bbox_areas = {p["bbox_area"] for p in pieces if p["matches"]}
    if name == "match_only":
        return matched
    if name == "unconditional_branch":
        # Partial-intermediate bypass: perform the branch clause but omit matches.
        return branches
    if name == "opening_area_gate":
        return matched | {i for i in branches if pieces[i]["area"] in opening_areas}
    if name == "matched_bbox_area_gate":
        return matched | {i for i in branches if pieces[i]["area"] in bbox_areas}
    if name == "first_matched_area_gate":
        first = matched_areas[0] if matched_areas else -1
        return matched | {i for i in branches if pieces[i]["area"] == first}
    if name == "area_parity_gate":
        parity = {x % 2 for x in matched_areas}
        return matched | {i for i in branches if pieces[i]["area"] % 2 in parity}
    if name == "area_mod3_gate":
        residues = {x % 3 for x in matched_areas}
        return matched | {i for i in branches if pieces[i]["area"] % 3 in residues}
    if name == "between_extremes_gate":
        lo, hi = min(matched_areas), max(matched_areas)
        return matched | {i for i in branches if lo <= pieces[i]["area"] <= hi}
    if name == "any_match_unlocks_all_branches":
        return branches if matched else set()
    if name == "smallest_matched_area_gate":
        target = min(matched_areas)
        return matched | {i for i in branches if pieces[i]["area"] == target}
    if name == "largest_matched_area_gate":
        target = max(matched_areas)
        return matched | {i for i in branches if pieces[i]["area"] == target}
    if name == "even_branch_gate":
        return matched | {i for i in branches if pieces[i]["area"] % 2 == 0}
    if name == "largest_branch_only":
        largest = max((pieces[i]["area"] for i in branches), default=-1)
        return matched | {i for i in branches if pieces[i]["area"] == largest}
    raise KeyError(name)


RIVALS = (
    "match_only",
    "unconditional_branch",
    "opening_area_gate",
    "matched_bbox_area_gate",
    "first_matched_area_gate",
    "area_parity_gate",
    "area_mod3_gate",
    "between_extremes_gate",
    "any_match_unlocks_all_branches",
    "smallest_matched_area_gate",
    "largest_matched_area_gate",
    "even_branch_gate",
    "largest_branch_only",
)


def _rival(name: str, grid: list[list[int]], chosen_policy: str) -> list[list[int]]:
    del chosen_policy  # Rivals are fixed shortcut hypotheses, not alternate settings.
    analysis = analyze_scene(grid)
    return _recolor(grid, _rival_indexes(name, analysis), analysis)


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    chosen = _settings(episode.get("settings"))
    policy = chosen[PARAMETER]
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program_solution does not match episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(len(train), MIN_DEMOS, MAX_DEMOS, "demos")
    if len(test) != QUERIES:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    if any(type(pair) is not dict or set(pair) != {"input", "output"} for pair in pairs):
        raise ValueError("every pair must contain exactly input and output")
    for pair in pairs:
        _grid(pair["input"])
        _grid(pair["output"])
        analyze_scene(pair["input"])
    input_digests = [digest(pair["input"]) for pair in pairs]
    if len(set(input_digests)) != len(input_digests):
        raise ValueError("all demonstration and query inputs must be distinct")

    def apply_setting(candidate: str, grid: list[list[int]]) -> list[list[int]]:
        if execute is None:
            return apply_rule(grid, candidate)
        return execute(program({PARAMETER: candidate}), grid)

    setting_refutations: dict[str, list[int]] = {}
    survivors: list[dict[str, str]] = []
    for candidate in BRANCH_POLICIES:
        disagree = [i for i, pair in enumerate(train)
                    if apply_setting(candidate, pair["input"]) != pair["output"]]
        setting_refutations[candidate] = disagree
        if not disagree:
            survivors.append({PARAMETER: candidate})
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the selected setting: {survivors}")

    for pair in pairs:
        if apply_setting(policy, pair["input"]) != pair["output"]:
            raise ValueError("label disagrees with fixed episode setting")

    rival_refutations: dict[str, list[int]] = {}
    rival_survivors: list[str] = []
    for name in RIVALS:
        disagree = [i for i, pair in enumerate(train)
                    if _rival(name, pair["input"], policy) != pair["output"]]
        rival_refutations[name] = disagree
        if not disagree:
            rival_survivors.append(name)
    if rival_survivors:
        raise ValueError(f"named shortcut rivals survive the minimum lesson: {rival_survivors}")

    computed = {
        "scope": "two branch policies plus thirteen finite shortcut/intermediate rivals",
        "racket_checked": execute is not None,
        "setting_survivors": survivors,
        "rival_survivors": rival_survivors,
        "rejected_rivals": list(RIVALS),
        "setting_refutations": setting_refutations,
        "rival_refutations": rival_refutations,
        "queries": [
            {"input_sha256": digest(pair["input"]),
             "output_sha256": digest(pair["output"])}
            for pair in test
        ],
    }
    supplied = episode.get("certificate")
    if supplied is not None and supplied != computed:
        raise ValueError("certificate mismatch: supplied certificate does not recompute")
    return computed


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, MAX_SEED, "seed")
    _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    if type(queries) is not int:
        raise TypeError("queries must be the exact integer 4 (bool is forbidden)")
    if queries != QUERIES:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(settings)
    policy = chosen[PARAMETER]
    train = []
    for index in range(demos):
        grid = _scene(seed, "demo", index)
        train.append({"input": grid, "output": apply_rule(grid, policy)})
    test = []
    for index in range(QUERIES):
        grid = _scene(seed, "query", index)
        test.append({"input": grid, "output": apply_rule(grid, policy)})
    source = program(chosen)
    episode = {
        "schema": "b6c499e1fa78-matched-area-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": source,
        "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    _integer(index, 0, QUERIES - 1, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERIES:
        raise ValueError("episode must retain exactly four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]),
             "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


class RacketRunner:
    """One live protected Racket bridge for bounded source/evidence checks."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule
        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "matched_area.rkt",
        HERE / "opening_area_gate.rkt",
        HERE / "match_only.rkt",
        HERE.parents[1] / "generator.py",
        REPO / "shared/data/canonical/puzzles.jsonl",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths if path.is_file()
    }
