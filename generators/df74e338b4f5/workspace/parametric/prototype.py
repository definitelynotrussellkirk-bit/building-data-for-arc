"""Parametric recoloring-scope family for ``df74e338b4f5``.

All settings share one input grammar: two to four strictly nested hollow
color-9 rectangles and same-colored marker cells at every containment depth.
The canonical setting recolors every marker by its strict frame-containment
depth.  The alternative first computes all positive marker depths and their
histogram, selects the least frequent positive depth (ties go to the deepest),
and recolors only markers in that selected class.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

TASK_ID = "df74e338b4f5"
SCOPES = ("all_markers", "rarest_positive_depth")
DEFAULT_SCOPE = "all_markers"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

_HERE = Path(__file__).resolve().parent
_RULES = {
    "all_markers": _HERE / "rules" / "canonical.rkt",
    "rarest_positive_depth": _HERE / "rules" / "rarest_positive_depth.rkt",
}

# (height, width, frame count, exact marker count by depth 0..frame_count)
# The first two demonstrations jointly expose frequency selection, a non-deepest
# tie winner, both axis-only containment mistakes, and the exclusion of depth 0.
_DEMO_PROFILES = (
    (13, 15, 2, (1, 4, 3)),
    (17, 19, 3, (3, 1, 1, 3)),
    (19, 17, 3, (2, 1, 3, 2)),
    (21, 23, 4, (3, 3, 1, 2, 4)),
    (22, 18, 3, (2, 4, 2, 1)),
    (24, 22, 4, (3, 1, 1, 3, 2)),
)
_QUERY_PROFILES = (
    (14, 18, 2, (1, 3, 2)),
    (18, 14, 2, (2, 2, 1)),
    (23, 27, 4, (3, 1, 2, 1, 3)),
    (30, 30, 4, (4, 4, 1, 3, 2)),
)
_MARKER_COLORS = (5, 6, 7, 8)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
BBox = tuple[int, int, int, int]
Grid = list[list[int]]


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in [{low}, {high}]")
    return value


def _scope(value: str) -> str:
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"recolor_scope must be one of {SCOPES}")
    return value


def rule_text(recolor_scope: str) -> str:
    return _RULES[_scope(recolor_scope)].read_text()


def _outline(box: BBox) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _area(box: BBox) -> int:
    r0, c0, r1, c1 = box
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _components_of_nine(grid: Grid) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 9 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == 9
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            components.append(cells)
    return components


def _depth_at(row: int, col: int, boxes: list[BBox]) -> int:
    return sum(r0 < row < r1 and c0 < col < c1 for r0, c0, r1, c1 in boxes)


def _row_span_depth(row: int, boxes: list[BBox]) -> int:
    return sum(r0 < row < r1 for r0, _, r1, _ in boxes)


def _column_span_depth(col: int, boxes: list[BBox]) -> int:
    return sum(c0 < col < c1 for _, c0, _, c1 in boxes)


def analyze(grid: Grid) -> dict:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact ARC colors")

    components = _components_of_nine(grid)
    boxes: list[BBox] = []
    for cells in components:
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        box = min(rows), min(cols), max(rows), max(cols)
        if set(cells) != _outline(box):
            raise ValueError("every color-9 component must be a complete hollow rectangle")
        boxes.append(box)
    boxes.sort(key=lambda box: (-_area(box), box))
    if not 2 <= len(boxes) <= 4:
        raise ValueError("the parametric grammar requires two to four frames")
    for outer, inner in zip(boxes, boxes[1:]):
        or0, oc0, or1, oc1 = outer
        ir0, ic0, ir1, ic1 = inner
        if min(ir0 - or0, ic0 - oc0, or1 - ir1, oc1 - ic1) < 2:
            raise ValueError("successive frames need a one-cell blank moat")

    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    marker_colors = {grid[row][col] for row, col in markers}
    if len(marker_colors) != 1:
        raise ValueError("all marker cells must share one nonzero non-frame color")
    depths = {(row, col): _depth_at(row, col, boxes) for row, col in markers}
    counts = Counter(depths.values())
    expected = set(range(len(boxes) + 1))
    if set(counts) != expected:
        raise ValueError(f"markers must expose every depth {sorted(expected)}")
    positive = {depth: counts[depth] for depth in range(1, len(boxes) + 1)}
    selected = min(positive, key=lambda depth: (positive[depth], -depth))
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "boxes": boxes,
        "frame_count": len(boxes),
        "markers": markers,
        "marker_color": next(iter(marker_colors)),
        "depths": depths,
        "depth_counts": dict(sorted(counts.items())),
        "positive_depth_counts": positive,
        "selected_positive_depth": selected,
    }


def apply_scope(grid: Grid, recolor_scope: str) -> Grid:
    scope = _scope(recolor_scope)
    info = analyze(grid)
    output = deepcopy(grid)
    selected = info["selected_positive_depth"]
    for row, col in info["markers"]:
        depth = info["depths"][(row, col)]
        if scope == "all_markers" or depth == selected:
            output[row][col] = depth
    return output


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:recolor-scope-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _nested_boxes(
    height: int,
    width: int,
    frame_count: int,
    rng: random.Random,
    *,
    maximal: bool = False,
) -> list[BBox]:
    minimum_outer = 7 + 4 * (frame_count - 1)
    if height < minimum_outer + 2 or width < minimum_outer + 2:
        raise ValueError("profile is too small for nested frames plus exterior space")
    outer_h = height - 2 if maximal else rng.randint(minimum_outer, height - 2)
    outer_w = width - 2 if maximal else rng.randint(minimum_outer, width - 2)
    top = 1 if maximal else rng.randint(1, height - outer_h - 1)
    left = 1 if maximal else rng.randint(1, width - outer_w - 1)
    boxes: list[BBox] = [(top, left, top + outer_h - 1, left + outer_w - 1)]

    while len(boxes) < frame_count:
        current = boxes[-1]
        remaining_after = frame_count - len(boxes) - 1
        minimum_next = 7 + 4 * remaining_after
        current_h = current[2] - current[0] + 1
        current_w = current[3] - current[1] + 1

        def insets(size: int) -> tuple[int, int]:
            if maximal:
                return 2, 2
            spare = size - 4 - minimum_next
            extra = rng.randint(0, min(3, max(0, spare)))
            first = rng.randint(0, extra)
            return 2 + first, 2 + extra - first

        inset_top, inset_bottom = insets(current_h)
        inset_left, inset_right = insets(current_w)
        boxes.append(
            (
                current[0] + inset_top,
                current[1] + inset_left,
                current[2] - inset_bottom,
                current[3] - inset_right,
            )
        )
    return boxes


def _draw_frames(height: int, width: int, boxes: list[BBox]) -> Grid:
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for box in boxes:
        for row, col in _outline(box):
            if grid[row][col] != 0:
                raise RuntimeError("nested frame construction overlapped")
            grid[row][col] = 9
    return grid


def _axis_killer_pair(
    grid: Grid,
    boxes: list[BBox],
    quotas: dict[int, int],
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int]]:
    row_killers: list[tuple[int, int]] = []
    col_killers: list[tuple[int, int]] = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            depth = _depth_at(row, col, boxes)
            if _row_span_depth(row, boxes) != depth:
                row_killers.append((row, col))
            if _column_span_depth(col, boxes) != depth:
                col_killers.append((row, col))
    rng.shuffle(row_killers)
    rng.shuffle(col_killers)
    for first in row_killers:
        first_depth = _depth_at(*first, boxes)
        if quotas.get(first_depth, 0) < 1:
            continue
        for second in col_killers:
            if first == second:
                continue
            second_depth = _depth_at(*second, boxes)
            needed = 2 if second_depth == first_depth else 1
            if quotas.get(second_depth, 0) >= needed:
                return first, second
    raise RuntimeError("profile cannot place both axis-only shortcut witnesses")


def _spread_choice(
    candidates: list[tuple[int, int]],
    selected: list[tuple[int, int]],
    rng: random.Random,
) -> tuple[int, int]:
    if not candidates:
        raise RuntimeError("marker profile exhausted its depth region")
    used_rows = {row for row, _ in selected}
    used_cols = {col for _, col in selected}
    jitter = {cell: rng.random() for cell in candidates}

    def score(cell: tuple[int, int]):
        row, col = cell
        distance = min(
            (abs(row - other_row) + abs(col - other_col) for other_row, other_col in selected),
            default=999,
        )
        return (row not in used_rows, col not in used_cols, distance, jitter[cell])

    return max(candidates, key=score)


def _place_markers(
    grid: Grid,
    boxes: list[BBox],
    counts: tuple[int, ...],
    marker_color: int,
    rng: random.Random,
) -> None:
    quotas = {depth: count for depth, count in enumerate(counts)}
    selected = list(_axis_killer_pair(grid, boxes, quotas, rng))
    for row, col in selected:
        quotas[_depth_at(row, col, boxes)] -= 1

    candidates_by_depth: dict[int, list[tuple[int, int]]] = {
        depth: [] for depth in range(len(boxes) + 1)
    }
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0 and (row, col) not in selected:
                candidates_by_depth[_depth_at(row, col, boxes)].append((row, col))

    for depth in range(len(boxes) + 1):
        for _ in range(quotas[depth]):
            candidates = [cell for cell in candidates_by_depth[depth] if cell not in selected]
            cell = _spread_choice(candidates, selected, rng)
            selected.append(cell)

    for row, col in selected:
        grid[row][col] = marker_color


def _make_input(seed: int, split: str, index: int) -> Grid:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, frame_count, counts = profiles[index]
    rng = _rng(seed, split, index)
    boxes = _nested_boxes(
        height,
        width,
        frame_count,
        rng,
        maximal=(split == "test" and index == len(_QUERY_PROFILES) - 1),
    )
    grid = _draw_frames(height, width, boxes)
    marker_color = rng.choice(_MARKER_COLORS)
    _place_markers(grid, boxes, counts, marker_color, rng)
    info = analyze(grid)
    if tuple(info["depth_counts"][depth] for depth in range(frame_count + 1)) != counts:
        raise RuntimeError("constructed marker histogram drifted")
    return grid


def _paint_selected_depth(grid: Grid, selected_depth: int) -> Grid:
    info = analyze(grid)
    output = deepcopy(grid)
    for row, col in info["markers"]:
        depth = info["depths"][(row, col)]
        if depth == selected_depth:
            output[row][col] = depth
    return output


def audit_rivals(recolor_scope: str) -> dict[str, Callable[[Grid], Grid]]:
    scope = _scope(recolor_scope)

    def row_span_only(grid: Grid) -> Grid:
        info = analyze(grid)
        output = deepcopy(grid)
        for row, col in info["markers"]:
            output[row][col] = _row_span_depth(row, info["boxes"])
        return output

    def column_span_only(grid: Grid) -> Grid:
        info = analyze(grid)
        output = deepcopy(grid)
        for row, col in info["markers"]:
            output[row][col] = _column_span_depth(col, info["boxes"])
        return output

    def constant_one(grid: Grid) -> Grid:
        info = analyze(grid)
        output = deepcopy(grid)
        for row, col in info["markers"]:
            output[row][col] = 1
        return output

    def inside_any_frame(grid: Grid) -> Grid:
        info = analyze(grid)
        output = deepcopy(grid)
        for row, col in info["markers"]:
            output[row][col] = int(info["depths"][(row, col)] > 0)
        return output

    def deepest_positive_only(grid: Grid) -> Grid:
        info = analyze(grid)
        return _paint_selected_depth(grid, info["frame_count"])

    def shallowest_rarest_tie(grid: Grid) -> Grid:
        info = analyze(grid)
        counts = info["positive_depth_counts"]
        selected = min(counts, key=lambda depth: (counts[depth], depth))
        return _paint_selected_depth(grid, selected)

    def most_frequent_positive_depth(grid: Grid) -> Grid:
        info = analyze(grid)
        counts = info["positive_depth_counts"]
        selected = max(counts, key=lambda depth: (counts[depth], depth))
        return _paint_selected_depth(grid, selected)

    def rarest_including_depth_zero(grid: Grid) -> Grid:
        info = analyze(grid)
        counts = info["depth_counts"]
        selected = min(counts, key=lambda depth: (counts[depth], -depth))
        return _paint_selected_depth(grid, selected)

    # The same rival set is intentionally evaluated for both settings.  For the
    # canonical setting, selection-only rivals fail because they preserve some
    # markers; for the alternate, all-marker rivals fail on scope and/or depth.
    del scope
    return {
        "row_span_only": row_span_only,
        "column_span_only": column_span_only,
        "constant_one": constant_one,
        "inside_any_frame": inside_any_frame,
        "deepest_positive_only": deepest_positive_only,
        "shallowest_rarest_tie": shallowest_rarest_tie,
        "most_frequent_positive_depth": most_frequent_positive_depth,
        "rarest_including_depth_zero": rarest_including_depth_zero,
    }


def public_projection(episode: dict) -> dict:
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_challenge_bytes(episode: dict) -> bytes:
    return json.dumps(
        public_projection(episode),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode() + b"\n"


def public_challenge_id(episode: dict) -> str:
    return hashlib.sha256(public_challenge_bytes(episode)).hexdigest()


def generate_episode(
    seed: int,
    *,
    recolor_scope: str = DEFAULT_SCOPE,
    demos: int = 3,
    queries: int = 4,
) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    scope = _scope(recolor_scope)
    _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _integer("queries", queries, MIN_QUERIES, MAX_QUERIES)

    train_inputs = [_make_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_make_input(seed, "test", index) for index in range(queries)]
    train = [
        {"input": deepcopy(grid), "output": apply_scope(grid, scope)}
        for grid in train_inputs
    ]
    test = [
        {"input": deepcopy(grid), "output": apply_scope(grid, scope)}
        for grid in test_inputs
    ]
    episode = {
        "schema": "nesting-depth-recolor-scope-parametric-v1",
        "status": "proposed",
        "approved": False,
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"recolor_scope": scope},
        "demo_count": demos,
        "query_count": queries,
        "train": train,
        "test": test,
        "program_solution": rule_text(scope),
    }
    episode["public_challenge_id"] = public_challenge_id(episode)
    return episode
