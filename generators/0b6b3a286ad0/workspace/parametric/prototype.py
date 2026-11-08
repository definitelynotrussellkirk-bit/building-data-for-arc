"""One or two template-key lookups; private Python labels are checked by Racket."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

TASK_ID = "0b6b3a286ad0"
VERSION = "lookup-depth-v1"
SETTINGS = ({"lookup_depth": 1}, {"lookup_depth": 2})
# H,W,V1-height,V2-height,first-key,(successor-key for V1,V2).
DEMO_PROFILES = (
    (15, 26, 11, 6, 1, (2, 1)),
    (15, 26, 8, 15, 2, (1, 2)),
    (15, 26, 14, 12, 2, (1, 1)),
    (23, 29, 22, 17, 1, (2, 2)),
    (27, 30, 21, 26, 1, (1, 2)),
    (29, 29, 28, 24, 2, (2, 1)),
)
QUERY_PROFILES = (
    (8, 25, 4, 7, 1, (1, 2)),
    (22, 29, 21, 16, 2, (2, 2)),
    (30, 30, 30, 27, 1, (2, 1)),
    (26, 28, 25, 21, 2, (2, 1)),
)
_RAW_MASKS = (
    ((1, 1, 1), (0, 0, 1), (0, 1, 1)),
    ((1, 1, 0), (1, 0, 0), (1, 1, 1)),
    ((0, 1, 1), (1, 1, 0), (1, 0, 0)),
    ((1, 0, 0), (1, 1, 1), (0, 0, 1)),
    ((1, 1, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 0, 1), (1, 1, 1), (0, 1, 0)),
    ((1, 1, 0), (0, 1, 1), (0, 0, 1)),
    ((0, 0, 1), (1, 1, 1), (1, 0, 0)),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"lookup_depth"}:
        raise ValueError("settings must name exactly lookup_depth")
    return _integer(settings["lookup_depth"], 1, 2, "lookup_depth")


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list
            or len(row) != len(grid[0]) or any(type(v) is not int or not 0 <= v <= 9
            for v in row) for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def variants(grid, mode="dihedral"):
    result, current = [], [list(row) for row in grid]
    for _ in range(4 if mode != "identity" else 1):
        if current not in result: result.append(current)
        current = rotate(current)
    if mode == "dihedral":
        current = [list(reversed(row)) for row in grid]
        for _ in range(4):
            if current not in result: result.append(current)
            current = rotate(current)
    return result


_MASKS = tuple({tuple(tuple(row) for row in transformed)
                for mask in _RAW_MASKS if len(variants(mask)) == 8
                for transformed in variants(mask)})
# Stable sorting avoids hash-randomization dependence across processes.
_MASKS = tuple(sorted(_MASKS))


def find_matches(board, template, wildcard=True, transforms="identity", allow_missing=0, colorblind=False):
    validate_grid(board); validate_grid(template)
    if type(wildcard) is not bool or type(colorblind) is not bool:
        raise ValueError("matching flags must be booleans")
    if transforms not in ("identity", "rotations", "dihedral"):
        raise ValueError("unknown transform mode")
    _integer(allow_missing, 0, 1, "allow_missing")
    matches = set()
    for pattern in variants(template, transforms):
        ph, pw = len(pattern), len(pattern[0])
        for r in range(len(board) - ph + 1):
            for c in range(len(board[0]) - pw + 1):
                missing = 0
                for dr, row in enumerate(pattern):
                    for dc, value in enumerate(row):
                        if value == 0 and wildcard: continue
                        actual = board[r + dr][c + dc]
                        missing += (bool(actual) != bool(value)) if colorblind else (actual != value)
                if missing <= allow_missing: matches.add((r, c))
    return sorted(matches)


def _crop(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v not in (0, 9)]
    if not cells: raise ValueError("library panels must contain a nonzero crop")
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in panel[r1:r2 + 1]]


def parse(grid):
    validate_grid(grid)
    separators = {c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)}
    panels, start = [], 0
    for c in range(len(grid[0]) + 1):
        if c == len(grid[0]) or c in separators:
            if c > start: panels.append([row[start:c] for row in grid])
            start = c + 1
    if len(panels) != 5: raise ValueError("expected exactly five separator-delimited panels")
    return dict(zip(("key1", "value1", "key2", "value2"), map(_crop, panels[:4])), query=panels[4])


def mirror(grid, settings):
    depth = _settings(settings)
    p = parse(grid)
    selected = p["value1"] if find_matches(p["query"], p["key1"]) else p["value2"]
    if depth == 2:
        selected = p["value1"] if find_matches(selected, p["key1"]) else p["value2"]
    return [row[:] for row in selected]


def program(settings):
    depth = _settings(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_bytes().decode("utf-8")
    if depth == 1: return canonical
    last = "(if (empty? (find-matches query k1 0)) v2 v1)"
    if canonical.count(last) != 1: raise ValueError("canonical lookup expression has drifted")
    return canonical.replace(last, "(let ((selected " + last + ")) (if (empty? (find-matches selected k1 0)) v2 v1))")


def _colored(mask, color):
    return [[color if v else 0 for v in row] for row in mask]


def _anchors(length, rng):
    count = (length + 1) // 4
    if count <= 1: return [rng.randrange(length - 2)]
    return [round(i * (length - 3) / (count - 1)) for i in range(count)]


def _state(height, width, target, key1, key2, frame, rng, *, value_panel, target_copies=1):
    grid = [[frame if value_panel else 0] * width for _ in range(height)]
    chosen, other = (key1, key2) if target == 1 else (key2, key1)
    near = [row[:] for row in other]
    occupied = [(r, c) for r, row in enumerate(near) for c, v in enumerate(row) if v]
    r, c = rng.choice(occupied); near[r][c] = 0
    reflected = [list(reversed(row)) for row in other]
    wrong_color = [[frame if v else 0 for v in row] for row in other]
    alternatives = [rotate(other), near, reflected, rotate(rotate(other)),
                    rotate(rotate(rotate(other))), wrong_color]
    slots = [(r, c) for r in _anchors(height, rng) for c in _anchors(width, rng)]
    # Independent key locations; teaching states vary the target color's rank.
    if not 1 <= target_copies <= len(slots):
        raise AssertionError("target multiplicity exceeds available motif slots")
    selected_slots = set(rng.sample(range(len(slots)), target_copies))
    decoy_index = 0
    for i, (r0, c0) in enumerate(slots):
        if i in selected_slots:
            pattern = chosen
        else:
            pattern = alternatives[decoy_index % len(alternatives)]
            decoy_index += 1
        for r, row in enumerate(pattern):
            for c, v in enumerate(row):
                if v: grid[r0 + r][c0 + c] = v
                elif pattern is chosen: grid[r0 + r][c0 + c] = frame
    return grid


def _input(seed, split, index):
    rng = random.Random(int.from_bytes(hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode()).digest(), "big"))
    profiles = list(DEMO_PROFILES if split == "train" else QUERY_PROFILES)
    if split != "train":
        order_rng = random.Random(int.from_bytes(hashlib.sha256(
            f"{TASK_ID}:{VERSION}:{seed}:query-order".encode()).digest(), "big"))
        order_rng.shuffle(profiles)
    h, w, v1h, v2h, initial, successors = profiles[index]
    a, b, frame = rng.sample(range(1, 9), 3)
    mask1, mask2 = rng.sample(_MASKS, 2)
    key1, key2 = _colored(mask1, a), _colored(mask2, b)
    value1 = _state(v1h, 4, successors[0], key1, key2, frame, rng, value_panel=True,
                    target_copies=2 if split == "train" and index == 0 else 1)
    value2 = _state(v2h, 4, successors[1], key1, key2, frame, rng, value_panel=True)
    query = _state(h, w - 18, initial, key1, key2, frame, rng, value_panel=False,
                   target_copies=5 if split == "train" and index == 1 else 1)
    result = [[] for _ in range(h)]
    for i, crop in enumerate((key1, value1, key2, value2)):
        top = rng.randint(0, h - len(crop))
        for r in range(h):
            result[r].extend(crop[r - top] if top <= r < top + len(crop) else [0] * len(crop[0]))
            result[r].append(9)
    for row, qrow in zip(result, query): row.extend(qrow)
    facts = analyze(result)
    if facts["first_index"] != initial - 1 or facts["successor_indices"] != [s - 1 for s in successors]:
        raise AssertionError("constructive template placement changed a required branch")
    p = parse(result)
    for state, target in zip((p["query"], p["value1"], p["value2"]), (initial,) + successors):
        if not find_matches(state, p[f"key{target}"]) or find_matches(state, p[f"key{3-target}"]):
            raise AssertionError("each state must visibly contain exactly its intended key")
    return result


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed"); _settings(settings)
    _integer(demos, 3, 6, "demos"); _integer(queries, 1, 4, "queries")
    episode = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _input(seed, split, index)
            episode[split].append({"input": grid, "output": mirror(grid, settings)})
    return episode


def analyze(grid):
    p = parse(grid)
    first = 0 if find_matches(p["query"], p["key1"]) else 1
    values = (p["value1"], p["value2"])
    successors = [0 if find_matches(value, p["key1"]) else 1 for value in values]
    return {"first_index": first, "second_index": successors[first],
            "successor_indices": successors, "selected_value": values[first],
            "query_key1_matches": [list(x) for x in find_matches(p["query"], p["key1"])],
            "intermediate_key1_matches": [list(x) for x in find_matches(values[first], p["key1"])],
            "input_shape": [len(grid), len(grid[0])],
            "value_shapes": [[len(v), len(v[0])] for v in values]}
