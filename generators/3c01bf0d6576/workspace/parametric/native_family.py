"""Native transform-by-example family with an optional post-transform selection step."""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Iterable, Sequence

TASK_ID = "3c01bf0d6576"
DEFAULT = {"finish": "transform_only"}
SETTINGS = (
    {"finish": "transform_only"},
    {"finish": "mark_first_after_transform"},
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _setting(settings: Any = None) -> str:
    if settings is None:
        return "transform_only"
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in {
        "transform_only", "mark_first_after_transform"
    }:
        raise ValueError("finish must be transform_only or mark_first_after_transform")
    return value


def _grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not grid or len(grid) > 30
            or type(grid[0]) is not list or not grid[0] or len(grid[0]) > 30):
        raise ValueError("grid must be a rectangular 1..30 list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must contain exact integer ARC colors")
    return [row[:] for row in grid]


def _xform(grid: Sequence[Sequence[int]], code: int) -> list[list[int]]:
    g = [list(row) for row in grid]
    if code == 0:
        return g
    if code == 1:
        h, w = len(g), len(g[0])
        return [[g[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == 2:
        return [row[::-1] for row in g[::-1]]
    if code == 3:
        h, w = len(g), len(g[0])
        return [[g[r][c] for r in range(h)] for c in range(w)]
    if code == 4:
        return [row[::-1] for row in g]
    if code == 5:
        return g[::-1]
    raise ValueError("transform code must be 0..5")


def _components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] != 0 and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            result.append(cells)
    return sorted(result, key=lambda cells: (
        min(r for r, _ in cells), min(c for _, c in cells)
    ))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _crop(grid: Sequence[Sequence[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    top, left, bottom, right = _bbox(cells)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def analyze(grid: Any) -> dict[str, Any]:
    source = _grid(grid)
    parts = _components(source)
    if len(parts) < 3:
        raise ValueError("transform-by-example input needs at least three components")
    a, ap, b = (_crop(source, part) for part in parts[:3])
    matches = [code for code in range(6) if _xform(a, code) == ap]
    if not matches:
        raise ValueError("the first two crops do not demonstrate a supported transform")
    return {"source": source, "parts": parts, "a": a, "ap": ap,
            "b": b, "transform": matches[0], "matches": matches}


def _mark_first_component(grid: Sequence[Sequence[int]], color: int = 9) -> list[list[int]]:
    output = [list(row) for row in grid]
    first = next(((r, c) for r, row in enumerate(output)
                  for c, value in enumerate(row) if value != 0), None)
    if first is None:
        return output
    queue = deque([first])
    chosen = {first}
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            rr, cc = r + dr, c + dc
            if (0 <= rr < len(output) and 0 <= cc < len(output[0])
                    and output[rr][cc] != 0 and (rr, cc) not in chosen):
                chosen.add((rr, cc))
                queue.append((rr, cc))
    for r, c in chosen:
        output[r][c] = color
    return output


def transform(grid: Any, settings: Any = None) -> list[list[int]]:
    finish = _setting(settings)
    info = analyze(grid)
    intermediate = _xform(info["b"], info["transform"])
    if finish == "mark_first_after_transform":
        return _mark_first_component(intermediate)
    return intermediate


def wrong_order_transform(grid: Any) -> list[list[int]]:
    """Counterfactual: choose/mark the first B component before transforming it."""
    info = analyze(grid)
    return _xform(_mark_first_component(info["b"]), info["transform"])


def wrong_order_program() -> str:
    """Executable counterfactual that marks B before applying the inferred transform."""
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    final = "(apply-transform b (if (eq? cmd #f) 0 cmd))"
    replacement = """(let* ((first-hit (first (filter-cells b
                                      (lambda (r c v) (not (= v 0))))))
             (chosen (connected-region b (first first-hit) (second first-hit)
                       (lambda (r c v) (not (= v 0))) 4))
             (marked (for/fold ([out b]) ([p (in-list chosen)])
                       (set-cell out (first p) (second p) 9))))
        (apply-transform marked (if (eq? cmd #f) 0 cmd)))"""
    if canonical.count(final) != 1:
        raise ValueError("canonical rule no longer has the expected final transform")
    return canonical.replace(final, replacement)


def program(settings: Any = None) -> str:
    finish = _setting(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if finish == "transform_only":
        return canonical
    stripped = canonical.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("canonical rule must be one rule! expression")
    body = stripped[len("(rule!"):-1].strip()
    return """(rule!
  (let* ((transformed %s)
         (first-hit (first (filter-cells transformed
                             (lambda (r c v) (not (= v 0))))))
         (chosen (connected-region transformed (first first-hit) (second first-hit)
                   (lambda (r c v) (not (= v 0))) 4)))
    (for/fold ([out transformed]) ([p (in-list chosen)])
      (set-cell out (first p) (second p) 9))))""" % body


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _paint(canvas: list[list[int]], motif: Sequence[Sequence[int]], top: int, left: int) -> None:
    for row, values in enumerate(motif):
        for column, value in enumerate(values):
            if value:
                if canvas[top + row][left + column] != 0:
                    raise ValueError("motifs overlap")
                canvas[top + row][left + column] = value


def _palette(seed: int, index: int) -> list[int]:
    import hashlib
    import random
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{index}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:16], "big"))
    values = list(range(1, 9))
    rng.shuffle(values)
    return values


def _a_motif(colors: Sequence[int]) -> list[list[int]]:
    # Five connected cells with an asymmetric color arrangement.  All six
    # supported transforms are therefore distinguishable by the full crop.
    return [
        [colors[0], 0, 0],
        [colors[1], colors[2], colors[2]],
        [0, colors[3], 0],
    ]


def _b_motif(height: int, width: int, colors: Sequence[int], salt: int) -> list[list[int]]:
    if height < 3 or width < 3:
        raise ValueError("B motif needs axes at least three")
    motif = [[0] * width for _ in range(height)]
    main: set[tuple[int, int]] = {(row, 0) for row in range(height)}
    main.update((height - 1, column) for column in range(width))
    # Connected variable-width bars make the large cases substantive while
    # retaining an empty top edge.  The isolated top-right cell becomes the
    # row-major first component after a left-right flip.
    for row in range(1, height - 1):
        length = 1 + ((row * 3 + salt) % max(1, width - 2))
        main.update((row, column) for column in range(length + 1))
    for row, column in sorted(main):
        motif[row][column] = colors[(row * 5 + column * 3 + salt) % 5]
    motif[0][width - 1] = colors[6]
    return motif


# (canvas_h, canvas_w, A_top_left, A'_top_left, B_top_left, B_shape, transform)
_SCENES = (
    (11, 15, (1, 1), (1, 10), (7, 5), (3, 3), 4),
    (13, 17, (0, 0), (4, 5), (8, 10), (4, 5), 1),
    (14, 18, (0, 9), (4, 1), (9, 11), (5, 4), 3),
    (16, 20, (1, 1), (1, 15), (9, 6), (5, 7), 5),
    (18, 22, (0, 0), (5, 8), (10, 13), (6, 8), 2),
    (20, 24, (1, 18), (6, 2), (11, 10), (7, 9), 4),
    (22, 26, (0, 0), (5, 20), (12, 8), (8, 10), 1),
    (24, 28, (1, 12), (6, 1), (13, 16), (9, 11), 3),
    (27, 29, (0, 0), (5, 24), (15, 8), (10, 12), 5),
    (30, 30, (0, 0), (0, 27), (18, 9), (12, 12), 2),
)


def _scene(seed: int, index: int) -> list[list[int]]:
    height, width, apos, ppos, bpos, bshape, code = _SCENES[index]
    colors = _palette(seed, index)
    a = _a_motif(colors)
    ap = _xform(a, code)
    b = _b_motif(*bshape, colors, index)
    canvas = [[0] * width for _ in range(height)]
    _paint(canvas, a, *apos)
    _paint(canvas, ap, *ppos)
    _paint(canvas, b, *bpos)
    info = analyze(canvas)
    if info["matches"] != [code]:
        raise RuntimeError(f"scene {index} does not uniquely teach transform {code}")
    return canvas


def layout_signature(grid: Any) -> str:
    parts = _components(_grid(grid))
    if len(parts) < 3:
        raise ValueError("layout needs three components")
    boxes = [_bbox(part) for part in parts[:3]]
    return "horizontal_zones" if boxes[0][0] == boxes[1][0] else "vertical_or_staggered"


def _inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    import hashlib
    import random
    demos = [_scene(seed, index) for index in range(6)]
    queries = [_scene(seed, index) for index in range(6, 10)]
    digest = hashlib.sha256(f"{TASK_ID}:queries:{seed}".encode()).digest()
    random.Random(int.from_bytes(digest[:16], "big")).shuffle(queries)
    return demos, queries


def generate(seed: int, settings: Any = None, demos: int = 4, queries: int = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    finish = _setting(settings)
    demos = _integer(demos, 4, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    setting = {"finish": finish}
    demo_inputs, query_inputs = _inputs(seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        source = [row[:] for row in grid]
        return {"input": source, "output": transform(source, setting)}

    return {
        "settings": setting.copy(),
        "program_solution": program(setting),
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
    }
