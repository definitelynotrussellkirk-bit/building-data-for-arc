"""Native cell-count versus bounding-box-area family for 2786bc764238."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "2786bc764238"
METRICS = ("cell_count", "bbox_area")
_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_CANONICAL = (_HOME / "canonical.rkt").read_text(encoding="utf-8")


def _load_generator():
    path = _TASK_HOME / "generator.py"
    name = "_parametric_source_2786bc764238"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_generator()

_CANONICAL_SORT = """(objs (sort (objects mask 0)
                     (lambda (a b)
                       (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                             [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                             [else (< (obj-c1 a) (obj-c1 b))]))))"""
_BBOX_SORT = """(bbox-area (lambda (obj)
                      (* (+ 1 (- (obj-r2 obj) (obj-r1 obj)))
                         (+ 1 (- (obj-c2 obj) (obj-c1 obj))))))
         (objs (sort (objects mask 0)
                     (lambda (a b)
                       (cond [(not (= (bbox-area a) (bbox-area b))) (> (bbox-area a) (bbox-area b))]
                             [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                             [else (< (obj-c1 a) (obj-c1 b))]))))"""
if _CANONICAL.count(_CANONICAL_SORT) != 1:
    raise RuntimeError("canonical component comparator changed; refusing unsafe rewrite")
_BBOX_PROGRAM = _CANONICAL.replace(_CANONICAL_SORT, _BBOX_SORT)


def _metric(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"selection_metric"}:
        raise ValueError("settings must name exactly selection_metric")
    value = settings["selection_metric"]
    if type(value) is not str or value not in METRICS:
        raise ValueError("selection_metric must be 'cell_count' or 'bbox_area'")
    return value


def program(settings: dict[str, Any]) -> str:
    metric = _metric(settings)
    return _CANONICAL if metric == "cell_count" else _BBOX_PROGRAM


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def _rng(seed: int, phase: str, slot: int, attempt: int) -> random.Random:
    raw = f"{TASK_ID}|metric-family-v1|{seed}|{phase}|{slot}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _normalize(cells):
    cells = set(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _transform(cells, code: int):
    cells = set(cells)
    if code >= 4:
        cells = {(r, -c) for r, c in cells}
    for _ in range(code % 4):
        cells = {(c, -r) for r, c in cells}
    return _normalize(cells)


def _rect(height: int, width: int):
    return frozenset((r, c) for r in range(height) for c in range(width))


def _frame(height: int, width: int):
    return frozenset(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _corner_path(height: int, width: int):
    return frozenset({*( (0, c) for c in range(width) ), *( (r, width - 1) for r in range(1, height) )})


def _dense_holey(height: int, width: int):
    cells = set(_rect(height, width))
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if (r * 3 + c * 5) % 7 == 0:
                cells.remove((r, c))
    return frozenset(cells)


def _line(length: int):
    return frozenset((0, c) for c in range(length))


def _vline(length: int):
    return frozenset((r, 0) for r in range(length))


def _shape(kind: str, height: int, width: int):
    if kind == "rect":
        return _rect(height, width)
    if kind == "frame":
        return _frame(height, width)
    if kind == "path":
        return _corner_path(height, width)
    if kind == "dense_holey":
        return _dense_holey(height, width)
    if kind == "line":
        return _line(width)
    if kind == "vline":
        return _vline(height)
    raise ValueError(kind)


# First shape is the unique cell-count winner; second is the unique bbox-area
# winner.  Remaining components vary the near-miss structure.
_DEMO_PROFILES = (
    # Every lesson contains explicit taller and wider low-area decoys.  Thus
    # bbox-area cannot be learned as largest height/width, while the first two
    # shapes remain the unique cell-count and bbox-area winners respectively.
    (12, 15, (("rect", 3, 3), ("path", 4, 4), ("vline", 5, 1), ("line", 1, 5))),
    (13, 16, (("frame", 4, 4), ("path", 5, 5), ("vline", 6, 1), ("line", 1, 6))),
    (14, 18, (("frame", 4, 5), ("path", 6, 5), ("vline", 7, 1), ("line", 1, 6))),
    (15, 20, (("rect", 4, 5), ("path", 7, 5), ("vline", 8, 1), ("line", 1, 6))),
    (18, 24, (("frame", 6, 6), ("path", 8, 7), ("vline", 9, 1), ("line", 1, 8))),
    (20, 26, (("frame", 7, 7), ("path", 10, 8), ("vline", 11, 1), ("line", 1, 9))),
)
_QUERY_PROFILES = (
    (9, 12, (("rect", 2, 3), ("path", 3, 3), ("line", 1, 3))),
    (16, 18, (("frame", 5, 5), ("path", 7, 6), ("rect", 3, 4), ("line", 1, 5))),
    (24, 20, (("frame", 7, 7), ("path", 10, 8), ("rect", 4, 5), ("frame", 4, 4))),
    (30, 30, (("dense_holey", 9, 9), ("path", 12, 12), ("frame", 10, 10), ("rect", 6, 6), ("frame", 8, 8))),
)


def _dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _boxes_intersect(left, right):
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    return not (lr2 < rr1 or rr2 < lr1 or lc2 < rc1 or rc2 < lc1)


def _halo(cells, height: int, width: int):
    result = set(cells)
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    result.add((nr, nc))
    return result


def _place_shapes(height: int, width: int, shapes, rng):
    candidates = []
    for shape in shapes:
        sh, sw = _dims(shape)
        rows = []
        for top in range(height - sh + 1):
            for left in range(width - sw + 1):
                cells = frozenset((top + r, left + c) for r, c in shape)
                rows.append((cells, _bbox(cells)))
        rng.shuffle(rows)
        candidates.append(rows)

    order = sorted(range(len(shapes)), key=lambda i: _bbox_area(shapes[i]), reverse=True)
    placed: dict[int, frozenset[tuple[int, int]]] = {}
    boxes: list[tuple[int, int, int, int]] = []
    forbidden: set[tuple[int, int]] = set()
    visits = 0

    def rec(position: int):
        nonlocal forbidden, visits
        if position == len(order):
            return True
        index = order[position]
        for cells, box in candidates[index]:
            visits += 1
            if visits > 120000:
                return False
            if cells & forbidden or any(_boxes_intersect(box, other) for other in boxes):
                continue
            old_forbidden = forbidden
            forbidden = forbidden | _halo(cells, height, width)
            boxes.append(box)
            placed[index] = cells
            if rec(position + 1):
                return True
            del placed[index]
            boxes.pop()
            forbidden = old_forbidden
        return False

    if not rec(0):
        raise RuntimeError(f"could not place {len(shapes)} clean components in {height}x{width}")
    return [placed[index] for index in range(len(shapes))]


def _components(grid):
    return _GENERATOR._components(grid)


def _winner(grid, metric: str):
    comps = _components(grid)
    if metric == "cell_count":
        return sorted(comps, key=lambda c: (-c["size"], c["bbox"][0], c["bbox"][1]))[0]
    return sorted(comps, key=lambda c: (-_GENERATOR._bbox_area(c), c["bbox"][0], c["bbox"][1]))[0]


def _predict(grid, metric: str):
    return _GENERATOR._crop(grid, _winner(grid, metric))


def _rival_predict(grid, rival: str):
    comps = _components(grid)
    if rival == "topmost":
        winner = sorted(comps, key=lambda c: (c["bbox"][0], c["bbox"][1], -c["size"]))[0]
    elif rival == "leftmost":
        winner = sorted(comps, key=lambda c: (c["bbox"][1], c["bbox"][0], -c["size"]))[0]
    elif rival == "largest_height":
        winner = sorted(comps, key=lambda c: (-(c["bbox"][2] - c["bbox"][0] + 1), c["bbox"][0], c["bbox"][1]))[0]
    elif rival == "largest_width":
        winner = sorted(comps, key=lambda c: (-(c["bbox"][3] - c["bbox"][1] + 1), c["bbox"][0], c["bbox"][1]))[0]
    elif rival == "global_bbox":
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]
    else:
        raise ValueError(rival)
    return _GENERATOR._crop(grid, winner)


def _span(grid):
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return (
        max(r for r, _ in occupied) - min(r for r, _ in occupied),
        max(c for _, c in occupied) - min(c for _, c in occupied),
    )


def _accepted_input(*, seed: int, phase: str, slot: int, profile, seen: set[str]):
    height, width, specs = profile
    base_shapes = [_shape(*spec) for spec in specs]
    cell_sizes = [len(shape) for shape in base_shapes]
    bbox_areas = [_bbox_area(shape) for shape in base_shapes]
    if cell_sizes.count(max(cell_sizes)) != 1 or bbox_areas.count(max(bbox_areas)) != 1:
        raise RuntimeError(f"invalid profile winners for {phase}[{slot}]")
    if cell_sizes.index(max(cell_sizes)) == bbox_areas.index(max(bbox_areas)):
        raise RuntimeError(f"profile metrics do not disagree for {phase}[{slot}]")

    for attempt in range(160):
        rng = _rng(seed, phase, slot, attempt)
        shapes = [_transform(shape, rng.randrange(8)) for shape in base_shapes]
        try:
            placements = _place_shapes(height, width, shapes, rng)
        except RuntimeError:
            continue
        colors = rng.sample(list(range(1, 10)), len(shapes))
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for cells, color in zip(placements, colors):
            for r, c in cells:
                grid[r][c] = color
        comps = _components(grid)
        if len(comps) != len(shapes):
            continue
        sizes = [c["size"] for c in comps]
        areas = [_GENERATOR._bbox_area(c) for c in comps]
        if sizes.count(max(sizes)) != 1 or areas.count(max(areas)) != 1:
            continue
        if _winner(grid, "cell_count")["cells"] == _winner(grid, "bbox_area")["cells"]:
            continue
        if _predict(grid, "cell_count") == _predict(grid, "bbox_area"):
            continue
        if phase == "demo":
            # Each individual demonstration defeats simple location and
            # one-dimensional geometry shortcuts for either declared setting.
            rivals = ("topmost", "leftmost", "largest_height", "largest_width", "global_bbox")
            if any(
                _predict(grid, metric) == _rival_predict(grid, rival)
                for metric in METRICS
                for rival in rivals
            ):
                continue
        if (height, width) == (30, 30) and min(_span(grid)) < 24:
            continue
        digest = _digest(grid)
        if digest in seen:
            continue
        seen.add(digest)
        return grid
    raise RuntimeError(f"bounded {phase} sampling exhausted for slot {slot}")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    metric = _metric(settings)
    _validate_request(seed, demos, queries)
    seen: set[str] = set()
    train = []
    for slot, profile in enumerate(_DEMO_PROFILES[:demos]):
        grid = _accepted_input(seed=seed, phase="demo", slot=slot, profile=profile, seen=seen)
        train.append({"input": copy.deepcopy(grid), "output": _predict(grid, metric)})
    test = []
    for slot, profile in enumerate(_QUERY_PROFILES):
        grid = _accepted_input(seed=seed, phase="query", slot=slot, profile=profile, seen=seen)
        test.append({"input": copy.deepcopy(grid), "output": _predict(grid, metric)})
    return {"train": train, "test": test, "program_solution": program(settings)}
