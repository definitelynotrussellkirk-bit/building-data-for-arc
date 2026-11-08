"""Generate panel sequences whose oriented cursor consumes an aligned route.

Inspired by supplied evaluation task 5545f144.  Each input contains two or
three equal panels separated by a full-height color column.  A three-cell arrow
advances through a nested, shrinking set of singleton waypoints.  Consecutive
waypoints share exactly one row or column, while every nonconsecutive pair has
different row and column coordinates.  The output is the next clean state:
the arrow at the final waypoint, oriented along the final leg.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from itertools import combinations

from puzzle_generators.base import gen_ctx


TASK_ID = "generic_waypoint_route_gen1"
GENERATOR_ID = "waypoint_route.gen1"
VERSION = "1.0.0"

PROGRAM = r"""(rule!
 (lambda (g)
  (let ()
   (define h (rows g))
   (define w (cols g))
   (define bg (mode g -1))
   (define sep-cols
    (filter
     (lambda (c)
      (and (!= (at g 0 c) bg)
           (all? (lambda (r) (= (at g r c) (at g 0 c))) (range 0 h))))
     (range 0 w)))
   (define start (+ 1 (apply max sep-cols)))
   (define panel (subgrid g 0 start (- h 1) (- w 1)))
   (define pw (cols panel))
   (define objs (objects-8 panel bg))
   (define cursor (first (filter (lambda (o) (> (obj-size o) 1)) objs)))
   (define cells (obj-cells cursor))
   (define bb (obj-bbox cursor))
   (define bh (+ 1 (- (third bb) (first bb))))
   (define bw (+ 1 (- (fourth bb) (second bb))))
   (define tip
    (if (> bw bh)
        (first
         (filter
          (lambda (p)
           (= 1 (count-if (lambda (q) (= (first q) (first p))) cells)))
          cells))
        (first
         (filter
          (lambda (p)
           (= 1 (count-if (lambda (q) (= (second q) (second p))) cells)))
          cells))))
   (define dots
    (map (lambda (o) (first (obj-cells o)))
         (filter (lambda (o) (= (obj-size o) 1)) objs)))
   (define traced
    (let loop ((pos tip) (remaining dots) (last-delta (list 0 0)))
     (if (empty? remaining)
         (list pos last-delta)
         (let* ((aligned
                 (filter
                  (lambda (q)
                   (or (= (first q) (first pos))
                       (= (second q) (second pos))))
                  remaining))
                (next (first aligned))
                (delta (list (- (first next) (first pos))
                             (- (second next) (second pos)))))
          (loop next
                (filter (lambda (q) (not (equal? q next))) remaining)
                delta)))))
   (define final (first traced))
   (define delta (second traced))
   (define r (first final))
   (define c (second final))
   (define arrow
    (cond ((< (first delta) 0)
           (list (list r c) (list (+ r 1) (- c 1)) (list (+ r 1) (+ c 1))))
          ((> (first delta) 0)
           (list (list r c) (list (- r 1) (- c 1)) (list (- r 1) (+ c 1))))
          ((< (second delta) 0)
           (list (list r c) (list (- r 1) (+ c 1)) (list (+ r 1) (+ c 1))))
          (else
           (list (list r c) (list (- r 1) (- c 1)) (list (+ r 1) (- c 1))))))
   (paint-cells (empty-grid h pw bg) arrow (obj-color cursor)))))"""


def _normalized_rule_text(source: str) -> str:
    return " ".join(source.split())


RULE_HASH = hashlib.sha256(_normalized_rule_text(PROGRAM).encode("utf-8")).hexdigest()[:12]


_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _arrow_cells(tip: tuple[int, int], delta: tuple[int, int]) -> list[tuple[int, int]]:
    r, c = tip
    dr, dc = delta
    if dr < 0:
        return [(r, c), (r + 1, c - 1), (r + 1, c + 1)]
    if dr > 0:
        return [(r, c), (r - 1, c - 1), (r - 1, c + 1)]
    if dc < 0:
        return [(r, c), (r - 1, c + 1), (r + 1, c + 1)]
    return [(r, c), (r - 1, c - 1), (r + 1, c - 1)]


def _components8(grid: list[list[int]], bg: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != bg}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _DIRS8:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        result.append(sorted(cells))
    return result


def _last_panel(grid: list[list[int]]) -> tuple[list[list[int]], int]:
    h, w = len(grid), len(grid[0])
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    sep_cols = [
        c
        for c in range(w)
        if grid[0][c] != bg and all(grid[r][c] == grid[0][c] for r in range(h))
    ]
    if not sep_cols:
        raise ValueError("no full-height non-background separator")
    start = max(sep_cols) + 1
    return [row[start:] for row in grid], bg


def _tip_of_arrow(cells: list[tuple[int, int]]) -> tuple[int, int]:
    rows = Counter(r for r, _ in cells)
    cols = Counter(c for _, c in cells)
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    candidates = [p for p in cells if (rows[p[0]] if width > height else cols[p[1]]) == 1]
    if len(candidates) != 1:
        raise ValueError("cursor does not have one inferable tip")
    return candidates[0]


def _apply(grid: list[list[int]]) -> list[list[int]]:
    panel, bg = _last_panel(grid)
    h, w = len(panel), len(panel[0])
    objects = _components8(panel, bg)
    cursors = [cells for cells in objects if len(cells) > 1]
    dots = [cells[0] for cells in objects if len(cells) == 1]
    if len(cursors) != 1 or not dots:
        raise ValueError("last panel must contain one cursor and at least one waypoint")
    cursor = cursors[0]
    color = panel[cursor[0][0]][cursor[0][1]]
    position = _tip_of_arrow(cursor)
    remaining = list(dots)
    delta = (0, 0)
    while remaining:
        aligned = [
            point
            for point in remaining
            if point[0] == position[0] or point[1] == position[1]
        ]
        if len(aligned) != 1:
            raise ValueError(f"route has {len(aligned)} aligned successors")
        nxt = aligned[0]
        delta = (nxt[0] - position[0], nxt[1] - position[1])
        remaining.remove(nxt)
        position = nxt
    out = [[bg] * w for _ in range(h)]
    for r, c in _arrow_cells(position, delta):
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError("final arrow leaves the panel")
        out[r][c] = color
    return out


def strict_canonical_like(grid) -> list[str]:
    """Return structural findings for this task-linked canonical profile."""
    errors: list[str] = []
    try:
        panel, bg = _last_panel(grid)
        h, total_w = len(grid), len(grid[0])
        panel_w = len(panel[0])
        separator_count = (total_w - panel_w) // (panel_w + 1)
        objects = _components8(panel, bg)
        cursors = [cells for cells in objects if len(cells) > 1]
        dots = [cells for cells in objects if len(cells) == 1]
        if not 2 <= separator_count + 1 <= 3:
            errors.append("expected two or three equal sequence panels")
        if len(cursors) != 1 or len(cursors[0]) != 3:
            errors.append("expected one three-cell oriented cursor")
        if not dots:
            errors.append("last panel must retain at least one waypoint")
        if h > 30 or total_w > 30:
            errors.append("grid exceeds the ARC 30x30 canvas")
        _apply(grid)
    except (TypeError, ValueError, IndexError) as exc:
        errors.append(str(exc))
    return errors


def _witness_unique_route(grid) -> bool:
    try:
        _apply(grid)
        return True
    except (TypeError, ValueError, IndexError):
        return False


def _witness_nested_sequence(grid) -> bool:
    try:
        panel, _ = _last_panel(grid)
        return len(grid[0]) > 2 * len(panel[0])
    except (TypeError, ValueError, IndexError):
        return False


def _witness_oriented_cursor(grid) -> bool:
    try:
        panel, bg = _last_panel(grid)
        cursors = [cells for cells in _components8(panel, bg) if len(cells) > 1]
        return (
            len(cursors) == 1
            and len(cursors[0]) == 3
            and _tip_of_arrow(cursors[0]) in cursors[0]
        )
    except (TypeError, ValueError, IndexError):
        return False


def _copy_last_panel_rival(grid):
    panel, _ = _last_panel(grid)
    return panel


def _erase_everything_rival(grid):
    panel, bg = _last_panel(grid)
    return [[bg] * len(panel[0]) for _ in range(len(panel))]


SEMANTIC_WITNESSES = {
    "nested_panel_sequence": _witness_nested_sequence,
    "one_oriented_cursor": _witness_oriented_cursor,
    "unique_aligned_waypoint_trace": _witness_unique_route,
}

SEMANTIC_RIVALS = {
    "copy_last_panel": _copy_last_panel_rival,
    "erase_cursor_with_waypoints": _erase_everything_rival,
}


def lesson_identifiable(train, query) -> list[str]:
    errors: list[str] = []
    if len(train) < 3:
        errors.append("need three demonstrations")
    for index, pair in enumerate(list(train) + [query]):
        try:
            if _apply(pair["input"]) != pair["output"]:
                errors.append(f"pair {index} disagrees with the route rule")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(f"pair {index} is invalid: {exc}")
    demo_widths = {len(pair["input"][0]) for pair in train if pair.get("input")}
    if len(demo_widths) < 2:
        errors.append("demonstrations do not vary sequence geometry")
    return errors


def _route_is_clean(points: list[tuple[int, int]]) -> bool:
    for i, point in enumerate(points[:-1]):
        remaining = points[i + 1 :]
        aligned = [q for q in remaining if q[0] == point[0] or q[1] == point[1]]
        if aligned != [points[i + 1]]:
            return False
    return all(
        max(abs(a[0] - b[0]), abs(a[1] - b[1])) > 1
        for a, b in combinations(points, 2)
    )


def _sample_route(rng, h: int, w: int, legs: int) -> list[tuple[int, int]]:
    rows = list(range(1, h - 1))
    cols = list(range(1, w - 1))
    for _ in range(500):
        start = (rng.choice(rows), rng.choice(cols))
        points = [start]
        used_rows = {start[0]}
        used_cols = {start[1]}
        horizontal = bool(rng.randrange(2))
        for _step in range(legs):
            r, c = points[-1]
            if horizontal:
                options = [x for x in cols if x not in used_cols and abs(x - c) >= 3]
                if not options:
                    break
                c = rng.choice(options)
                used_cols.add(c)
            else:
                options = [x for x in rows if x not in used_rows and abs(x - r) >= 3]
                if not options:
                    break
                r = rng.choice(options)
                used_rows.add(r)
            points.append((r, c))
            horizontal = not horizontal
        if len(points) == legs + 1 and _route_is_clean(points):
            return points
    raise ValueError("could not sample a unique aligned route")


def _profile(profile_index: int, difficulty: str) -> tuple[int, int, int, int]:
    choices = {
        "easy": [(8, 7, 2, 1), (9, 8, 3, 1), (10, 9, 2, 2)],
        "medium": [(11, 8, 3, 2), (12, 9, 3, 2), (13, 10, 2, 3)],
        "hard": [(14, 8, 3, 2), (15, 9, 3, 2), (16, 10, 2, 4)],
    }
    return choices[difficulty][profile_index % len(choices[difficulty])]


def _build_pair(rng, difficulty: str, profile_index: int) -> dict:
    h, panel_w, panel_count, consumed = _profile(profile_index, difficulty)
    bg, color, separator = rng.sample(range(10), 3)
    points = _sample_route(rng, h, panel_w, panel_count * consumed)
    panels: list[list[list[int]]] = []
    for panel_index in range(panel_count):
        route_index = panel_index * consumed
        tip = points[route_index]
        if route_index:
            previous = points[route_index - 1]
            delta = (tip[0] - previous[0], tip[1] - previous[1])
        else:
            nxt = points[1]
            delta = (nxt[0] - tip[0], nxt[1] - tip[1])
        arrow = _arrow_cells(tip, delta)
        remaining = points[route_index + 1 :]
        if any(
            max(abs(r - pr), abs(c - pc)) <= 1
            for r, c in arrow
            for pr, pc in remaining
        ):
            raise ValueError("cursor touches an unconsumed waypoint")
        panel = [[bg] * panel_w for _ in range(h)]
        for r, c in arrow + remaining:
            panel[r][c] = color
        panels.append(panel)

    grid = [[] for _ in range(h)]
    for index, panel in enumerate(panels):
        for r in range(h):
            if index:
                grid[r].append(separator)
            grid[r].extend(panel[r])
    output = [[bg] * panel_w for _ in range(h)]
    final_delta = (
        points[-1][0] - points[-2][0],
        points[-1][1] - points[-2][1],
    )
    for r, c in _arrow_cells(points[-1], final_delta):
        output[r][c] = color
    return {
        "input": grid,
        "output": output,
        "witness": {
            "panel_count": panel_count,
            "consumed_per_transition": consumed,
            "route_legs": len(points) - 1,
        },
    }


def generate_task(seed, *, difficulty="medium"):
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
    )
    pairs = []
    attempt = 0
    profile_offset = ctx.draw_rng("profile_offset").randrange(3)
    while len(pairs) < 4:
        if attempt >= 200:
            raise ValueError("could not build four valid route lessons")
        rng = ctx.draw_rng(f"pair.{len(pairs)}.{attempt}")
        attempt += 1
        try:
            pair = _build_pair(
                rng,
                difficulty,
                profile_offset + len(pairs),
            )
            if _apply(pair["input"]) != pair["output"]:
                continue
        except ValueError:
            continue
        pairs.append(pair)
    task = {
        "train": [{"input": p["input"], "output": p["output"]} for p in pairs[:3]],
        "test": [{"input": pairs[3]["input"], "output": pairs[3]["output"]}],
        "program": PROGRAM,
        "chain": [
            "split_panels",
            "identify_oriented_cursor",
            "trace_unique_aligned_waypoints",
            "orient_motif_to_vector",
            "render_clean_state",
        ],
        "meta": {
            "source_task_id": "5545f144",
            "relationship": "semantic_variant",
            "difficulty": difficulty,
            "rule_hash": RULE_HASH,
            "witnesses": [p["witness"] for p in pairs],
        },
    }
    findings = self_check_task(task)
    if findings:
        raise AssertionError(f"generated task failed self_check_task: {findings[:3]}")
    return task


def self_check_task(task) -> list[str]:
    errors: list[str] = []
    if not isinstance(task, dict):
        return ["task must be a dict"]
    if task.get("program") != PROGRAM:
        errors.append("task program must equal the pinned waypoint-route PROGRAM")
    if (task.get("meta") or {}).get("rule_hash") != RULE_HASH:
        errors.append("task meta.rule_hash does not match RULE_HASH")
    train = list(task.get("train") or [])
    test = list(task.get("test") or [])
    if len(train) < 3 or len(test) < 1:
        errors.append("task needs at least three train pairs and one test pair")
    signatures = set()
    for index, pair in enumerate(train + test):
        try:
            grid, output = pair["input"], pair["output"]
            expected = _apply(grid)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(f"pair {index} is structurally invalid: {exc}")
            continue
        if expected != output:
            errors.append(f"pair {index} output disagrees with the route oracle")
        if grid == output:
            errors.append(f"pair {index} is an identity task")
        h, w = len(grid), len(grid[0])
        if h > 30 or w > 30:
            errors.append(f"pair {index} exceeds the 30x30 ARC canvas")
        panel, bg = _last_panel(grid)
        objects = _components8(panel, bg)
        if sum(len(cells) > 1 for cells in objects) != 1:
            errors.append(f"pair {index} does not expose exactly one cursor")
        if sum(len(cells) == 1 for cells in objects) < 1:
            errors.append(f"pair {index} does not expose a remaining waypoint")
        signatures.add((h, len(panel[0]), len(grid[0])))
    if len(signatures) < 2:
        errors.append("lesson should vary panel or sequence geometry")
    return errors


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.waypoint_route import parity_check

    passed, total = parity_check(generate_task, n=25, version_label=TASK_ID)
    raise SystemExit(0 if passed == total else 1)
