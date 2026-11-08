"""Generate ordered two-color cursors that consume an aligned waypoint route.

This second 5545f144-inspired family preserves the panel-sequence and
waypoint semantics of gen1 while replacing the geometric three-cell arrow
with a typed head/tail domino.  The head color is identified by its repeated
singleton waypoints; the tail color records orientation.  This forces color
role and relative-vector reasoning instead of the gen1 tip-shape shortcut.
"""
from __future__ import annotations

from collections import Counter
import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.waypoint_route.gen1 import _sample_route


TASK_ID = "generic_waypoint_route_gen2"
GENERATOR_ID = "waypoint_route.gen2"
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
   (define objs (objects-multicolor panel bg))
   (define cursor (first (filter (lambda (o) (= (obj-size o) 2)) objs)))
   (define cells (obj-cells cursor))
   (define singles
    (map (lambda (o) (first (obj-cells o)))
         (filter (lambda (o) (= (obj-size o) 1)) objs)))
   (define head
    (first
     (filter
      (lambda (p)
       (> (count-if
           (lambda (q) (= (at panel (first q) (second q))
                          (at panel (first p) (second p))))
           singles)
          0))
      cells)))
   (define tail (first (filter (lambda (p) (not (equal? p head))) cells)))
   (define head-color (at panel (first head) (second head)))
   (define tail-color (at panel (first tail) (second tail)))
   (define dots
    (filter
     (lambda (p) (= (at panel (first p) (second p)) head-color))
     singles))
   (define traced
    (let loop ((pos head) (remaining dots) (last-delta (list 0 0)))
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
   (define dr (cond ((< (first delta) 0) -1)
                    ((> (first delta) 0) 1)
                    (else 0)))
   (define dc (cond ((< (second delta) 0) -1)
                    ((> (second delta) 0) 1)
                    (else 0)))
   (define r (first final))
   (define c (second final))
   (set-cell
    (set-cell (empty-grid h pw bg) r c head-color)
    (- r dr) (- c dc) tail-color))))"""


def _normalized_rule_text(source: str) -> str:
    return " ".join(source.split())


RULE_HASH = hashlib.sha256(_normalized_rule_text(PROGRAM).encode()).hexdigest()[:12]


def _components4(grid: list[list[int]], bg: int) -> list[list[tuple[int, int]]]:
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
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        result.append(sorted(cells))
    return result


def _last_panel(grid: list[list[int]]) -> tuple[list[list[int]], int]:
    h, w = len(grid), len(grid[0])
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    separators = [
        c
        for c in range(w)
        if grid[0][c] != bg and all(grid[r][c] == grid[0][c] for r in range(h))
    ]
    if not separators:
        raise ValueError("no full-height separator")
    start = max(separators) + 1
    return [row[start:] for row in grid], bg


def _unit(delta: tuple[int, int]) -> tuple[int, int]:
    dr, dc = delta
    return ((dr > 0) - (dr < 0), (dc > 0) - (dc < 0))


def _cursor_cells(
    head: tuple[int, int], delta: tuple[int, int]
) -> tuple[tuple[int, int], tuple[int, int]]:
    dr, dc = _unit(delta)
    return head, (head[0] - dr, head[1] - dc)


def _parse_last_state(grid: list[list[int]]) -> dict:
    panel, bg = _last_panel(grid)
    components = _components4(panel, bg)
    cursors = [cells for cells in components if len(cells) == 2]
    singles = [cells[0] for cells in components if len(cells) == 1]
    if len(cursors) != 1 or not singles:
        raise ValueError("expected one two-cell cursor and remaining waypoints")
    cursor = cursors[0]
    single_colors = Counter(panel[r][c] for r, c in singles)
    heads = [p for p in cursor if single_colors[panel[p[0]][p[1]]] > 0]
    if len(heads) != 1:
        raise ValueError("cursor head color is not uniquely tied to waypoints")
    head = heads[0]
    tail = next(p for p in cursor if p != head)
    head_color = panel[head[0]][head[1]]
    tail_color = panel[tail[0]][tail[1]]
    dots = [p for p in singles if panel[p[0]][p[1]] == head_color]
    if len(dots) != len(singles):
        raise ValueError("all singleton waypoints must use the head color")
    return {
        "panel": panel,
        "bg": bg,
        "head": head,
        "tail": tail,
        "head_color": head_color,
        "tail_color": tail_color,
        "dots": dots,
    }


def _apply(grid: list[list[int]]) -> list[list[int]]:
    state = _parse_last_state(grid)
    position = state["head"]
    remaining = list(state["dots"])
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
    head, tail = _cursor_cells(position, delta)
    h, w = len(state["panel"]), len(state["panel"][0])
    out = [[state["bg"]] * w for _ in range(h)]
    out[head[0]][head[1]] = state["head_color"]
    out[tail[0]][tail[1]] = state["tail_color"]
    return out


def strict_canonical_like(grid) -> list[str]:
    errors: list[str] = []
    try:
        state = _parse_last_state(grid)
        panel = state["panel"]
        panel_width = len(panel[0])
        panel_count = (len(grid[0]) + 1) // (panel_width + 1)
        if not 2 <= panel_count <= 3:
            errors.append("expected two or three equal sequence panels")
        if state["head_color"] == state["tail_color"]:
            errors.append("cursor head and tail colors must differ")
        if len(grid) > 30 or len(grid[0]) > 30:
            errors.append("grid exceeds ARC canvas")
        _apply(grid)
    except (TypeError, ValueError, IndexError, KeyError) as exc:
        errors.append(str(exc))
    return errors


def _witness_two_color_cursor(grid) -> bool:
    try:
        state = _parse_last_state(grid)
        return state["head_color"] != state["tail_color"]
    except (TypeError, ValueError, IndexError, KeyError):
        return False


def _witness_head_color_roles(grid) -> bool:
    try:
        state = _parse_last_state(grid)
        return bool(state["dots"]) and all(
            state["panel"][r][c] == state["head_color"] for r, c in state["dots"]
        )
    except (TypeError, ValueError, IndexError, KeyError):
        return False


def _witness_unique_route(grid) -> bool:
    try:
        _apply(grid)
        return True
    except (TypeError, ValueError, IndexError, KeyError):
        return False


def _copy_last_panel_rival(grid):
    return _last_panel(grid)[0]


def _head_only_rival(grid):
    state = _parse_last_state(grid)
    correct = _apply(grid)
    return [
        [state["bg"] if value == state["tail_color"] else value for value in row]
        for row in correct
    ]


SEMANTIC_WITNESSES = {
    "ordered_two_color_cursor": _witness_two_color_cursor,
    "head_color_repeats_as_waypoints": _witness_head_color_roles,
    "unique_aligned_waypoint_trace": _witness_unique_route,
}

SEMANTIC_RIVALS = {
    "copy_last_panel": _copy_last_panel_rival,
    "discard_tail_orientation": _head_only_rival,
}


def lesson_identifiable(train, query) -> list[str]:
    errors: list[str] = []
    if len(train) < 3:
        errors.append("need three demonstrations")
    for index, pair in enumerate(list(train) + [query]):
        try:
            if _apply(pair["input"]) != pair["output"]:
                errors.append(f"pair {index} disagrees with the ordered-cursor rule")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(f"pair {index} is invalid: {exc}")
    widths = {len(pair["input"][0]) for pair in train if pair.get("input")}
    if len(widths) < 2:
        errors.append("demonstrations do not vary sequence geometry")
    return errors


def _profile(profile_index: int, difficulty: str) -> tuple[int, int, int, int]:
    profiles = {
        "easy": [(8, 7, 2, 1), (9, 8, 2, 2), (10, 7, 3, 1)],
        "medium": [(10, 8, 3, 1), (11, 9, 2, 2), (12, 8, 3, 2)],
        "hard": [(12, 9, 3, 2), (13, 8, 3, 2), (14, 9, 3, 2)],
    }
    return profiles[difficulty][profile_index % len(profiles[difficulty])]


def _build_pair(rng, difficulty: str, profile_index: int) -> dict:
    h, panel_width, panel_count, consumed = _profile(profile_index, difficulty)
    bg, head_color, tail_color, separator = rng.sample(range(10), 4)
    points = _sample_route(rng, h, panel_width, panel_count * consumed)
    panels: list[list[list[int]]] = []
    for panel_index in range(panel_count):
        route_index = panel_index * consumed
        head = points[route_index]
        reference = points[route_index - 1] if route_index else points[1]
        delta = (head[0] - reference[0], head[1] - reference[1])
        if route_index == 0:
            delta = (reference[0] - head[0], reference[1] - head[1])
        head_cell, tail_cell = _cursor_cells(head, delta)
        remaining = points[route_index + 1 :]
        cursor_set = {head_cell, tail_cell}
        if any(
            abs(r - pr) + abs(c - pc) <= 1
            for r, c in cursor_set
            for pr, pc in remaining
        ):
            raise ValueError("cursor touches an unconsumed waypoint")
        panel = [[bg] * panel_width for _ in range(h)]
        panel[head_cell[0]][head_cell[1]] = head_color
        panel[tail_cell[0]][tail_cell[1]] = tail_color
        for r, c in remaining:
            panel[r][c] = head_color
        panels.append(panel)

    grid = [[] for _ in range(h)]
    for index, panel in enumerate(panels):
        for r in range(h):
            if index:
                grid[r].append(separator)
            grid[r].extend(panel[r])
    final_delta = (points[-1][0] - points[-2][0], points[-1][1] - points[-2][1])
    final_head, final_tail = _cursor_cells(points[-1], final_delta)
    output = [[bg] * panel_width for _ in range(h)]
    output[final_head[0]][final_head[1]] = head_color
    output[final_tail[0]][final_tail[1]] = tail_color
    return {
        "input": grid,
        "output": output,
        "witness": {
            "panel_count": panel_count,
            "consumed_per_transition": consumed,
            "route_legs": len(points) - 1,
            "cursor_encoding": "ordered_head_tail_colors",
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
    offset = ctx.draw_rng("profile_offset").randrange(3)
    while len(pairs) < 4:
        if attempt >= 300:
            raise ValueError("could not build four valid ordered-cursor lessons")
        rng = ctx.draw_rng(f"pair.{len(pairs)}.{attempt}")
        attempt += 1
        try:
            pair = _build_pair(rng, difficulty, offset + len(pairs))
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
            "identify_head_by_repeated_color_role",
            "trace_unique_aligned_waypoints",
            "orient_tail_opposite_final_vector",
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
        errors.append("task program must equal the pinned ordered-cursor PROGRAM")
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
            state = _parse_last_state(grid)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(f"pair {index} is structurally invalid: {exc}")
            continue
        if expected != output:
            errors.append(f"pair {index} output disagrees with the ordered-cursor oracle")
        if grid == output:
            errors.append(f"pair {index} is an identity task")
        if len(grid) > 30 or len(grid[0]) > 30:
            errors.append(f"pair {index} exceeds the 30x30 ARC canvas")
        signatures.add((len(grid), len(state["panel"][0]), len(grid[0])))
    if len(signatures) < 2:
        errors.append("lesson should vary panel or sequence geometry")
    return errors


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.waypoint_route import parity_check

    passed, total = parity_check(generate_task, n=25, version_label=TASK_ID)
    raise SystemExit(0 if passed == total else 1)
