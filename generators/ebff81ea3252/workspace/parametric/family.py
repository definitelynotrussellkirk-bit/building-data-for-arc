"""Matched-input parametric plus/decoy family for ARC task ebff81ea3252.

The default is the byte-exact canonical plus recoloring rule.  Alternative
settings first execute that local motif detection, then use the detected orange
plus centers to select the nearest or farthest surviving green decoy component
and recolor it 8.  Native qualification independently executes every label.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "ebff81ea3252"
MODES = ("none", "nearest", "farthest")
SETTINGS = tuple({"decoy_selection": mode} for mode in MODES)
DEMO_SIZES = ((10, 12), (12, 14), (14, 16), (16, 18), (18, 22), (22, 26))
QUERY_SIZES = ((30, 30), (24, 30), (30, 24), (27, 29))
PLUS = frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})
CORNERS = ((0, 0), (0, 2), (2, 0), (2, 2))
BASE_DECOYS = (
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0)}),
    frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}),
)


def _settings(settings) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"decoy_selection"}
        or type(settings["decoy_selection"]) is not str
        or settings["decoy_selection"] not in MODES
    ):
        raise ValueError("settings must be exactly decoy_selection=none|nearest|farthest")
    return settings["decoy_selection"]


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid must have 1..30 list rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    result = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular list-of-lists")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors 0..9")
        result.append(list(row))
    return result


def plus_centers(grid, color: int) -> list[tuple[int, int]]:
    rows = _grid(grid)
    result = []
    for r in range(1, len(rows) - 1):
        for c in range(1, len(rows[0]) - 1):
            if all(rows[rr][cc] == color for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))):
                result.append((r, c))
    return result


def canonical_solve(grid) -> list[list[int]]:
    rows = _grid(grid)
    out = [row[:] for row in rows]
    for r, c in plus_centers(rows, 3):
        for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            out[rr][cc] = 7
    return out


def components(grid, color: int) -> list[tuple[tuple[int, int], ...]]:
    rows = _grid(grid)
    remaining = {(r, c) for r, row in enumerate(rows) for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        found = {start}
        todo = deque([start])
        while todo:
            r, c = todo.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    found.add(point)
                    todo.append(point)
        result.append(tuple(sorted(found)))
    return result


def _distance(cells: Iterable[tuple[int, int]], centers: Iterable[tuple[int, int]]) -> int:
    cells, centers = tuple(cells), tuple(centers)
    if not cells or not centers:
        raise ValueError("distance needs nonempty cells and centers")
    return min(abs(r - rr) + abs(c - cc) for r, c in cells for rr, cc in centers)


def candidate_components(base) -> list[tuple[tuple[int, int], ...]]:
    return [cells for cells in components(base, 3) if len(cells) >= 3]


def solve_with_centers(grid, settings, centers) -> list[list[int]]:
    mode = _settings(settings)
    base = canonical_solve(grid)
    if mode == "none":
        return base
    centers = tuple(tuple(point) for point in centers)
    candidates = candidate_components(base)
    if not centers or len(candidates) < 2:
        raise ValueError("selection settings need detected centers and at least two decoys")
    distances = [_distance(cells, centers) for cells in candidates]
    target = min(distances) if mode == "nearest" else max(distances)
    if distances.count(target) != 1:
        raise ValueError(f"{mode} decoy must be unique")
    chosen = candidates[distances.index(target)]
    out = [row[:] for row in base]
    for r, c in chosen:
        out[r][c] = 8
    return out


def solve(grid, settings) -> list[list[int]]:
    mode = _settings(settings)
    base = canonical_solve(grid)
    centers = plus_centers(base, 7)
    return solve_with_centers(grid, {"decoy_selection": mode}, centers)


def _attached_target_count(grid, centers) -> int:
    rows = _grid(grid)
    green_components = components(rows, 3)
    cell_to_size = {cell: len(cells) for cells in green_components for cell in cells}
    return sum(cell_to_size.get(center, 0) > 5 for center in centers)


def analyze(grid) -> dict:
    try:
        rows = _grid(grid)
    except (TypeError, ValueError) as exc:
        return {"valid_for_all_settings": False, "errors": [str(exc)]}
    errors: list[str] = []
    colors = {value for row in rows for value in row}
    if not colors <= {0, 3}:
        errors.append("input may use only colors 0 and 3")
    original_centers = plus_centers(rows, 3)
    if not original_centers:
        errors.append("at least one exact green plus is required")
    base = canonical_solve(rows)
    centers = plus_centers(base, 7)
    if len(centers) != len(original_centers):
        errors.append("recolored plus centers changed unexpectedly")
    candidates = candidate_components(base)
    if len(candidates) < 3:
        errors.append("at least three surviving green decoy components are required")
    distances = [_distance(cells, centers) for cells in candidates] if centers and candidates else []
    nearest_unique = bool(distances) and distances.count(min(distances)) == 1
    farthest_unique = bool(distances) and distances.count(max(distances)) == 1
    if not nearest_unique:
        errors.append("nearest decoy distance is not unique")
    if not farthest_unique:
        errors.append("farthest decoy distance is not unique")
    nearest_index = distances.index(min(distances)) if nearest_unique else None
    farthest_index = distances.index(max(distances)) if farthest_unique else None
    if nearest_index == farthest_index:
        errors.append("nearest and farthest decoys must differ")
    attached = _attached_target_count(rows, original_centers) if original_centers else 0
    if attached < 1:
        errors.append("at least one plus needs an attached green corner")
    outputs = []
    if not errors:
        outputs = [
            base,
            solve_with_centers(rows, SETTINGS[1], centers),
            solve_with_centers(rows, SETTINGS[2], centers),
        ]
        if len({repr(output) for output in outputs}) != 3:
            errors.append("setting outputs are not distinct")
    fixed_distances = [_distance(cells, [(0, 0)]) for cells in candidates] if candidates else []
    fixed_nearest = fixed_distances.index(min(fixed_distances)) if fixed_distances and fixed_distances.count(min(fixed_distances)) == 1 else None
    fixed_farthest = fixed_distances.index(max(fixed_distances)) if fixed_distances and fixed_distances.count(max(fixed_distances)) == 1 else None
    largest_index = [len(cells) for cells in candidates].index(max(len(cells) for cells in candidates)) if candidates else None
    topmost_index = min(range(len(candidates)), key=lambda i: min(candidates[i])) if candidates else None
    return {
        "valid_for_all_settings": not errors,
        "errors": errors,
        "plus_count": len(original_centers),
        "plus_centers": centers,
        "attached_target_count": attached,
        "candidate_count": len(candidates),
        "candidate_sizes": [len(cells) for cells in candidates],
        "candidate_distances": distances,
        "nearest_index": nearest_index,
        "farthest_index": farthest_index,
        "nearest_distance_unique": nearest_unique,
        "farthest_distance_unique": farthest_unique,
        "fixed_corner_nearest_index": fixed_nearest,
        "fixed_corner_farthest_index": fixed_farthest,
        "largest_index": largest_index,
        "topmost_index": topmost_index,
        "setting_outputs_distinct": not errors and len({repr(output) for output in outputs}) == 3,
    }


def _derived_program(mode: str, *, centers_expr: str | None = None, criterion: str | None = None) -> str:
    if mode not in {"nearest", "farthest"}:
        raise ValueError(mode)
    compare = "<" if mode == "nearest" else ">"
    centers_expr = centers_expr or "detected-centers"
    if criterion == "largest":
        selected = "(first (sort candidates (lambda (a b) (> (obj-size a) (obj-size b)))))"
    elif criterion == "topmost":
        selected = "(first (sort candidates (lambda (a b) (< (first (obj-bbox a)) (first (obj-bbox b))))))"
    else:
        selected = f"(first (sort candidates (lambda (a b) ({compare} (distance a) (distance b)))))"
    return f"""(rule!
  (let ((dummy 0))
    (define base
      (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1))) (c (in-range 1 (- (cols g) 1))))
        (if (and (= (at g r c) 3) (= (at g (- r 1) c) 3) (= (at g (+ r 1) c) 3)
                 (= (at g r (- c 1)) 3) (= (at g r (+ c 1)) 3))
            (paint-cells out (list (list r c) (list (- r 1) c) (list (+ r 1) c)
                                   (list r (- c 1)) (list r (+ c 1))) 7)
            out)))
    (define detected-centers
      (filter
        (lambda (p)
          (let ([r (first p)] [c (second p)])
            (and (> r 0) (< r (- (rows base) 1)) (> c 0) (< c (- (cols base) 1))
                 (= (at base (- r 1) c) 7) (= (at base (+ r 1) c) 7)
                 (= (at base r (- c 1)) 7) (= (at base r (+ c 1)) 7))))
        (find-color base 7)))
    (define centers {centers_expr})
    (define candidates
      (filter (lambda (o) (and (= (obj-color o) 3) (>= (obj-size o) 3))) (objects base 0)))
    (define (distance o)
      (apply min
        (for*/list ([p (in-list (obj-cells o))] [q (in-list centers)])
          (+ (abs (- (first p) (first q))) (abs (- (second p) (second q)))))))
    (define selected {selected})
    (paint-cells base (obj-cells selected) 8)))"""


def program(settings) -> str:
    mode = _settings(settings)
    if mode == "none":
        return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    return _derived_program(mode)


def _rng(seed: int, split: str, index: int, label: str = "scene") -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _orient(cells: Iterable[tuple[int, int]], rng: random.Random) -> frozenset[tuple[int, int]]:
    result = set(cells)
    if rng.randrange(2):
        result = {(r, -c) for r, c in result}
    for _ in range(rng.randrange(4)):
        result = {(c, -r) for r, c in result}
    return _normalize(result)


def _slots(height: int, width: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(0, height - 2, 4) for c in range(0, width - 2, 4)]


def sample_input(seed: int, split: str, index: int, *, height: int, width: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 8, 30, "height")
    _integer(width, 9, 30, "width")
    slots = _slots(height, width)
    target_count = 1
    decoy_count = max(3, min(20, len(slots) - target_count))
    if target_count + decoy_count > len(slots):
        raise ValueError("canvas lacks motif slots")
    rng = _rng(seed, split, index)
    for _ in range(4096):
        order = slots[:]
        rng.shuffle(order)
        target_slots = order[:target_count]
        decoy_slots = order[target_count:target_count + decoy_count]
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for target_index, (r0, c0) in enumerate(target_slots):
            shape = set(PLUS)
            if target_index == 0 or (target_index + index) % 2 == 0:
                shape.add(rng.choice(CORNERS))
            for dr, dc in shape:
                grid[r0 + dr][c0 + dc] = 3
        for decoy_index, (r0, c0) in enumerate(decoy_slots):
            shape = _orient(BASE_DECOYS[(decoy_index + index) % len(BASE_DECOYS)], rng)
            for dr, dc in shape:
                grid[r0 + dr][c0 + dc] = 3
        facts = analyze(grid)
        if not facts.get("valid_for_all_settings"):
            continue
        if facts["nearest_index"] == facts["fixed_corner_nearest_index"]:
            continue
        if facts["farthest_index"] == facts["fixed_corner_farthest_index"]:
            continue
        if facts["nearest_index"] in {facts["largest_index"], facts["topmost_index"]}:
            continue
        if facts["farthest_index"] in {facts["largest_index"], facts["topmost_index"]}:
            continue
        if height >= 24 and width >= 24:
            occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
            if len(occupied) < 80:
                continue
            if height == 30 and width == 30 and (len({r for r, _ in occupied}) < 20 or len({c for _, c in occupied}) < 20):
                continue
        return grid
    raise RuntimeError(f"failed to construct plus/decoy scene {height}x{width}")


def _rival_output(grid, mode: str, name: str) -> list[list[int]]:
    base = canonical_solve(grid)
    centers = plus_centers(base, 7)
    candidates = candidate_components(base)
    if name == "fixed_corner":
        return solve_with_centers(grid, {"decoy_selection": mode}, [(0, 0)])
    if name == "largest":
        sizes = [len(cells) for cells in candidates]
        chosen = candidates[sizes.index(max(sizes))]
    elif name == "topmost":
        chosen = min(candidates, key=lambda cells: min(cells))
    else:
        raise ValueError(name)
    out = [row[:] for row in base]
    for r, c in chosen:
        out[r][c] = 8
    return out


def teaching_check(episode, settings) -> dict:
    mode = _settings(settings)
    demos = episode["train"]
    survivors = [candidate for candidate in SETTINGS if all(solve(pair["input"], candidate) == pair["output"] for pair in demos)]
    rivals = []
    if mode != "none":
        for name in ("fixed_corner", "largest", "topmost"):
            if all(_rival_output(pair["input"], mode, name) == pair["output"] for pair in demos):
                rivals.append(name)
    return {"survivors": survivors, "surviving_rivals": rivals}


def generate(seed, settings, demos=2, queries=4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _settings(settings)
    query_sizes = list(QUERY_SIZES)
    _rng(seed, "query-order", 0).shuffle(query_sizes)

    def pairs(split: str, sizes):
        result = []
        for index, (height, width) in enumerate(sizes):
            grid = sample_input(seed, split, index, height=height, width=width)
            result.append({"input": grid, "output": solve(grid, settings)})
        return result

    episode = {
        "train": pairs("demo", DEMO_SIZES[:demos]),
        "test": pairs("query", query_sizes[:queries]),
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
    }
    inputs = [repr(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("generated inputs are not distinct")
    check = teaching_check(episode, settings)
    if check["survivors"] != [settings] or check["surviving_rivals"]:
        raise RuntimeError(f"demonstrations failed teaching check: {check}")
    return episode


def public_turn(episode, query_index=0) -> dict:
    if type(query_index) is not int:
        raise ValueError("query_index must be an exact integer")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode needs train pairs and selected query")
    return {
        "train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])} for pair in train],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def rival_programs(settings) -> dict[str, str]:
    mode = _settings(settings)
    result = {}
    for candidate in SETTINGS:
        if candidate != settings:
            result["other_setting_" + candidate["decoy_selection"]] = program(candidate)
    if mode != "none":
        result.update({
            "fixed_corner_intermediate": _derived_program(mode, centers_expr="(list (list 0 0))"),
            "largest_decoy": _derived_program(mode, criterion="largest"),
            "topmost_decoy": _derived_program(mode, criterion="topmost"),
        })
    return result
