"""Bounding-box rule variants. Python labels are claims until Racket executes them.

Inputs and their ordering are independent of the hidden setting and requested
split lengths. The native worker checks every retained claim through Racket.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random


TASK_ID = "47993d3762b9"
MODES = ("all_corners", "largest_bbox_frame", "smallest_bbox_frame")
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
QUERY_SHAPES = ((9, 11), (17, 24), (24, 26), (30, 30))
EXTRA_DEMO_SHAPES = ((12, 14), (10, 16), (18, 20), (22, 24))


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly one declared mode")
    return settings["mode"]


def program(settings):
    mode = _mode(settings)
    if mode == "all_corners":
        return CANONICAL
    comparison = ">" if mode == "largest_bbox_frame" else "<"
    return f"""(rule!
  (let* ([records
          (for/list ([color (in-list (grid-colors g 0))])
            (let* ([cells (find-color g color)]
                   [bb (bbox-of-cells cells)])
              (list color bb (length cells))))]
         [area (lambda (record)
                 (let ([bb (second record)])
                   (* (+ 1 (- (third bb) (first bb)))
                      (+ 1 (- (fourth bb) (second bb))))))]
         [selected
          (for/fold ([best (first records)]) ([record (in-list (rest records))])
            (if ({comparison} (area record) (area best)) record best))]
         [color (first selected)]
         [bb (second selected)])
    (paint-cells
      (empty-grid (rows g) (cols g) 0)
      (for*/list ([row (in-range (first bb) (+ 1 (third bb)))]
                  [col (in-range (second bb) (+ 1 (fourth bb)))]
                  #:when (or (= row (first bb)) (= row (third bb))
                             (= col (second bb)) (= col (fourth bb))))
        (list row col color)))))"""


def analyze(grid):
    """Return plain geometric facts; never consult labels or the hidden setting."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact colors 0..9")
    cells = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                cells.setdefault(color, []).append((row, col))
    records = []
    for color, positions in sorted(cells.items()):
        top = min(r for r, _ in positions)
        bottom = max(r for r, _ in positions)
        left = min(c for _, c in positions)
        right = max(c for _, c in positions)
        height, width = bottom - top + 1, right - left + 1
        records.append({"color": color, "bbox": [top, left, bottom, right],
                        "height": height, "width": width, "area": height * width,
                        "count": len(positions)})
    return records


def apply_python(grid, settings):
    """Fast sampler label claim; the protected Racket rule is authoritative."""
    mode = _mode(settings)
    records = analyze(grid)
    if mode != "all_corners":
        if not records:
            raise ValueError("frame modes require non-background colors")
        choose = max if mode == "largest_bbox_frame" else min
        records = [choose(records, key=lambda item: item["area"])]
    output = [[0] * len(grid[0]) for _ in grid]
    for record in records:
        top, left, bottom, right = record["bbox"]
        if mode == "all_corners":
            positions = ((top, left), (top, right), (bottom, left), (bottom, right))
        else:
            positions = ((r, c) for r in range(top, bottom + 1)
                         for c in range(left, right + 1)
                         if r in (top, bottom) or c in (left, right))
        for r, c in positions:
            output[r][c] = record["color"]
    return output


def _rng(seed, stream, index=0):
    raw = f"bbox-frame-v1:{seed}:{stream}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _transform(grid, symmetry):
    result = [row[:] for row in grid]
    if symmetry & 1:
        result = [row[::-1] for row in result]
    if symmetry & 2:
        result.reverse()
    if symmetry & 4:
        result = [list(row) for row in zip(*result)]
    return result


def _cloud(height, width, count, rng, *, corners=False, strict_interior=False):
    if corners:
        selected = {(0, 0), (height - 1, width - 1)}
    else:
        selected = {(0, 1), (height - 1, width - 2),
                    (1, 0), (height - 2, width - 1)}
    forbidden = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    candidates = [(r, c) for r in range(height) for c in range(width)
                  if (r, c) not in selected and (r, c) not in forbidden
                  and (not strict_interior or (0 < r < height - 1 and 0 < c < width - 1))]
    if not len(selected) <= count <= len(selected) + len(candidates):
        raise ValueError("cloud count cannot be realized within its grammar")
    selected.update(rng.sample(candidates, count - len(selected)))
    return sorted(selected)


def _teaching(seed, index):
    # Shared palette and symmetry preserve changed winners across the two demos.
    shared = _rng(seed, "teaching-palette")
    palette = shared.sample(range(1, 10), 3)
    symmetry = shared.randrange(8)
    layouts = (
        ((1, 1, 5, 5, 4), (1, 10, 3, 8, 7), (8, 6, 7, 3, 5)),
        ((1, 10, 3, 8, 7), (7, 1, 5, 5, 4), (10, 10, 4, 7, 6)),
    )
    rng = _rng(seed, "teaching-cells", index)
    grid = [[0] * 19 for _ in range(16)]
    for color, (top, left, height, width, count) in zip(palette, layouts[index]):
        for r, c in _cloud(height, width, count, rng, strict_interior=True):
            grid[top + r][left + c] = color
    return _transform(grid, symmetry)


def _sample(seed, stream, index, shape):
    rng = _rng(seed, stream, index)
    height, width = shape
    split_r, split_c = height // 2, width // 2
    slots = ((0, 0, split_r - 1, split_c - 1),
             (0, split_c + 1, split_r - 1, width - 1),
             (split_r + 1, 0, height - 1, split_c - 1),
             (split_r + 1, split_c + 1, height - 1, width - 1))
    count = 4 if shape == (30, 30) else rng.choice((2, 3, 4))
    # Always include diagonally opposite slots, then choose remaining distractors.
    order = [0, 3] + rng.sample([1, 2], 2)
    chosen_slots = [slots[i] for i in order[:count]]
    palette = rng.sample(range(1, 10), count)
    for attempt in range(64):
        boxes = []
        for top, left, bottom, right in chosen_slots:
            available_h, available_w = bottom - top + 1, right - left + 1
            lower = 0.80 if shape == (30, 30) else 0.55
            bh = rng.randint(max(3, math.ceil(lower * available_h)), available_h)
            bw = rng.randint(max(3, math.ceil(lower * available_w)), available_w)
            # Outer anchoring gives genuine edge contacts on all four sides.
            r = top if top == 0 else bottom - bh + 1
            c = left if left == 0 else right - bw + 1
            boxes.append((r, c, bh, bw))
        if len({bh * bw for _, _, bh, bw in boxes}) == count:
            break
    else:
        raise RuntimeError("bounded sampler could not obtain unique bbox areas")
    grid = [[0] * width for _ in range(height)]
    for i, (color, (top, left, bh, bw)) in enumerate(zip(palette, boxes)):
        dense = shape == (30, 30)
        corners = not dense and (index + i) % 3 == 0
        density = rng.uniform(0.40, 0.68) if dense else rng.uniform(0.13, 0.45)
        cell_count = max(4, min(bh * bw - 4, round(bh * bw * density)))
        for r, c in _cloud(bh, bw, cell_count, rng, corners=corners):
            if grid[top + r][left + c]:
                raise AssertionError("nonoverlapping slots collided")
            grid[top + r][left + c] = color
    return _transform(grid, rng.randrange(4))  # preserve requested H/W


def generate(seed, settings, demos=3, queries=4):
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _mode(settings)
    training = [_teaching(seed, i) for i in range(2)]
    training += [_sample(seed, "demos", i, EXTRA_DEMO_SHAPES[i]) for i in range(demos - 2)]
    query_shapes = list(QUERY_SHAPES)
    _rng(seed, "query-profile-order").shuffle(query_shapes)
    tests = [_sample(seed, "queries", i, query_shapes[i]) for i in range(queries)]
    grids = training + tests
    if len({json.dumps(grid) for grid in grids}) != len(grids):
        raise RuntimeError("sampler produced a repeated input")
    for grid in grids:
        records = analyze(grid)
        if not 2 <= len(records) <= 4 or len({x["area"] for x in records}) != len(records):
            raise AssertionError("sampled geometry violates unique-area grammar")
    def pairs(inputs):
        return [{"input": grid, "output": apply_python(grid, settings)} for grid in inputs]
    return {"train": pairs(training), "test": pairs(tests),
            "program_solution": program(settings), "settings": dict(settings), "seed": seed}


def _public_helpers():
    # Bind the shared serializer to this source tree, never a cached sibling.
    root = HERE.parents[3]
    path = root / "shared/runtime/reviewer_support.py"
    spec = importlib.util.spec_from_file_location("_bbox_public_support", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_challenge(episode, query_index=0):
    """Projection only: one visible query, with no future or private information."""
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    selected = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(_public_helpers().public_challenge_bytes(selected))


def public_id(episode, query_index=0):
    return _public_helpers().public_challenge_id(public_challenge(episode, query_index))
