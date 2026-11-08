"""Matched-input parametric family for translated cue discovery and relay.

The default program is the exact selected canonical source.  The alternate first
computes the canonical translated footprint, reads the unique foreign cue color
under that footprint, and then paints every cell of that color as a remote relay.
All Python labels are claims; native qualification re-executes the Racket source.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Iterable

HOME = Path(__file__).resolve().parent
MODES = ("translate_only", "translated_cue_relay")


def _read(name: str) -> str:
    return (HOME / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError("finish_rule is not declared")
    return _read("canonical.rkt" if mode == "translate_only" else "translated_cue_relay.rkt")


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _rng(seed: int, stream: str, slot: int) -> random.Random:
    raw = hashlib.sha256(f"8738-parametric-v1:{seed}:{stream}:{slot}".encode()).digest()
    return random.Random(int.from_bytes(raw[:8], "big"))


_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 1), (3, 2), (3, 3)),
)

_DEMOS = (
    (14, 16, -3, 4, False),
    (15, 14, 4, -3, False),
    (18, 18, 0, 5, False),
    (20, 16, -5, 0, False),
    (22, 20, 3, 4, False),
    (24, 24, -4, -5, False),
)
_QUERIES = (
    (13, 15, 2, 4, False),
    (18, 20, -4, 5, False),
    (24, 26, -3, 3, True),
    (30, 30, 6, -7, False),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(shape, variant: int):
    cells = list(shape)
    if variant & 1:
        cells = [(c, -r) for r, c in cells]
    if variant & 2:
        cells = [(r, -c) for r, c in cells]
    return _normalize(cells)


def _components_of_color(grid, color: int):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    component.add(q)
                    todo.append(q)
        result.append(component)
    return sorted(result, key=lambda x: min(x))


def _marker(grid, color: int) -> tuple[int, int]:
    found = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if len(found) != 1:
        raise ValueError(f"expected one marker {color}")
    return found[0]


def _scene_state(grid):
    greens = _components_of_color(grid, 3)
    if not greens:
        raise ValueError("missing green component")
    size = max(map(len, greens))
    largest = [cells for cells in greens if len(cells) == size]
    if len(largest) != 1:
        raise ValueError("largest green component is not unique")
    a = _marker(grid, 2)
    b = _marker(grid, 1)
    delta = (b[0] - a[0], b[1] - a[1])
    moved = {(r + delta[0], c + delta[1]) for r, c in largest[0]}
    return largest[0], delta, moved


def _cue_for(grid, cells) -> int:
    h, w = len(grid), len(grid[0])
    colors = []
    for r, c in sorted(cells):
        if 0 <= r < h and 0 <= c < w and 4 <= grid[r][c] <= 9 and grid[r][c] not in colors:
            colors.append(grid[r][c])
    if len(colors) != 1:
        raise ValueError(f"expected one landing cue color, found {colors}")
    return colors[0]


def output_for(grid, mode: str):
    if mode not in MODES:
        raise ValueError("unknown finish_rule")
    _, _, moved = _scene_state(grid)
    cells = set(moved)
    if mode == "translated_cue_relay":
        cue = _cue_for(grid, moved)
        cells |= {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == cue}
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = 8
    return out


def _counterfactual_output(grid):
    _, (dr, dc), moved = _scene_state(grid)
    greens = _components_of_color(grid, 3)
    main = max(greens, key=len)
    wrong_probe = {(r - dr, c - dc) for r, c in main}
    cue = _cue_for(grid, wrong_probe)
    cells = set(moved) | {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == cue}
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = 8
    return out


def _counterfactual_program() -> str:
    return """(rule!\n  (let* ((shape (argmax obj-size (filter (lambda (o) (= (obj-color o) 3)) (objects g 0))))\n         (a (first (find-color g 2)))\n         (b (first (find-color g 1)))\n         (dr (- (first b) (first a)))\n         (dc (- (second b) (second a)))\n         (moved (map (lambda (p) (list (+ (first p) dr) (+ (second p) dc))) (obj-cells shape)))\n         (wrong-probe (map (lambda (p) (list (- (first p) dr) (- (second p) dc))) (obj-cells shape)))\n         (visible (filter (lambda (p) (in-bounds? (first p) (second p) h w)) wrong-probe))\n         (cue-colors (remove-duplicates (filter (lambda (v) (and (>= v 4) (<= v 9)))\n           (map (lambda (p) (at g (first p) (second p))) visible))))\n         (cue (first cue-colors))\n         (relay-cells (find-color g cue)))\n    (paint-cells (empty-grid h w 0) (append moved relay-cells) 8)))"""


def _place(grid, cells, color: int, occupied: set[tuple[int, int]]) -> bool:
    h, w = len(grid), len(grid[0])
    if any(not (0 <= r < h and 0 <= c < w) or (r, c) in occupied for r, c in cells):
        return False
    for r, c in cells:
        grid[r][c] = color
        occupied.add((r, c))
    return True


def _first_fit(grid, shape, color: int, occupied, anchors):
    for r0, c0 in anchors:
        cells = {(r0 + r, c0 + c) for r, c in shape}
        if _place(grid, cells, color, occupied):
            return cells
    raise RuntimeError("no free placement")


def _payload_shape(size: int, vertical: bool = False):
    cells = []
    for i in range(size):
        cells.append((i, 0) if vertical else (0, i))
    if size >= 5:
        cells += [(1, 1), (1, size - 2)] if not vertical else [(1, 1), (size - 2, 1)]
    return _normalize(cells)


def _marker_pair(h, w, dr, dc, occupied):
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            b = (r + dr, c + dc)
            if 0 <= b[0] < h and 0 <= b[1] < w and (r, c) not in occupied and b not in occupied:
                return (r, c), b
    raise RuntimeError("no marker pair")


def _build(seed: int, slot: int, spec, *, query: bool):
    h, w, dr, dc, partial = spec
    rng = _rng(seed, "query" if query else "demo", slot)
    grid = [[0] * w for _ in range(h)]
    occupied: set[tuple[int, int]] = set()
    shape = _transform(_SHAPES[slot % len(_SHAPES)], rng.randrange(4))
    bh = max(r for r, _ in shape) + 1
    bw = max(c for _, c in shape) + 1
    if partial:
        r0 = 2
        c0 = max(1, min(w - bw - 1, w // 2 - bw // 2))
    else:
        low_r, high_r = abs(dr) + 1, h - bh - abs(dr) - 1
        low_c, high_c = abs(dc) + 1, w - bw - abs(dc) - 1
        if low_r > high_r or low_c > high_c:
            raise RuntimeError("scene too small for two-sided probe")
        r0 = rng.randint(low_r, high_r)
        c0 = rng.randint(low_c, high_c)
    main = {(r0 + r, c0 + c) for r, c in shape}
    _place(grid, main, 3, occupied)
    moved = {(r + dr, c + dc) for r, c in main}
    visible = sorted((r, c) for r, c in moved if 0 <= r < h and 0 <= c < w and (r, c) not in occupied)
    if len(visible) < 2:
        raise RuntimeError("translation retained too few cells")
    reverse = {(r - dr, c - dc) for r, c in main}
    reverse_visible = sorted((r, c) for r, c in reverse if 0 <= r < h and 0 <= c < w and (r, c) not in occupied and (r, c) not in moved)
    if not reverse_visible:
        raise RuntimeError("reverse probe has no free cue cell")
    cue = 4 + (slot % 4)
    wrong = 4 + ((slot + 1) % 4)
    correct_point = visible[len(visible) // 2]
    wrong_point = reverse_visible[len(reverse_visible) // 2]
    _place(grid, {correct_point}, cue, occupied)
    _place(grid, {wrong_point}, wrong, occupied)
    # Reserve every other correct/reverse probe position so later payloads and
    # distractors cannot create a second cue under either intermediate.
    occupied.update((r, c) for r, c in moved | reverse if 0 <= r < h and 0 <= c < w)

    edge_anchors = [(0, 0), (0, max(0, w - 12)), (max(0, h - 3), 0), (max(0, h - 3), max(0, w - 12))]
    rng.shuffle(edge_anchors)
    relay_size = 10 if h == 30 else 5 + slot % 3
    _first_fit(grid, _payload_shape(relay_size), cue, occupied,
               [(r, c) for r, c in edge_anchors] + [(r, c) for r in range(h) for c in range(w)])
    _first_fit(grid, _payload_shape(4 + slot % 2, vertical=True), wrong, occupied,
               [(0, w - 3), (h - 8, w - 3)] + [(r, c) for r in range(h) for c in range(w)])

    # Smaller green decoys preserve the largest-component selection branch.
    _first_fit(grid, ((0, 0), (0, 1), (1, 0)), 3, occupied,
               [(h - 3, w - 3), (0, w // 2)] + [(r, c) for r in range(h) for c in range(w)])
    _first_fit(grid, ((0, 0), (1, 0)), 3, occupied,
               [(h - 3, 0), (0, w - 2)] + [(r, c) for r in range(h) for c in range(w)])

    marker2, marker1 = _marker_pair(h, w, dr, dc, occupied)
    _place(grid, {marker2}, 2, occupied)
    _place(grid, {marker1}, 1, occupied)

    # Foreign distractors; the 30x30 role deliberately spreads real content to
    # every boundary without using the selected cue colors at the probe sites.
    distractor_colors = [x for x in (8, 9, 6, 7, 5, 4) if x not in (cue, wrong)]
    for index, color in enumerate(distractor_colors[:2]):
        length = min(7 + slot, w - 2)
        _first_fit(grid, _payload_shape(length, vertical=bool(index)), color, occupied,
                   [(0, 1 + index * max(2, w // 2)), (1 + index * 3, 0)]
                   + [(r, c) for r in range(h) for c in range(w)])
    if h == 30 and w == 30:
        bands = [
            ({(0, c) for c in range(1, 29)}, distractor_colors[0]),
            ({(29, c) for c in range(1, 29)}, distractor_colors[1]),
            ({(r, 0) for r in range(1, 29)}, distractor_colors[0]),
            ({(r, 29) for r in range(1, 29)}, distractor_colors[1]),
        ]
        for cells, color in bands:
            for p in sorted(cells):
                if p not in occupied and p not in moved and p not in reverse:
                    grid[p[0]][p[1]] = color
                    occupied.add(p)
    # Sanity checks are deliberately pixel-derived.
    state = analyze_input(grid)
    if state["cue_color"] != cue or state["wrong_cue_color"] != wrong:
        raise RuntimeError("constructed cue contract drifted")
    return grid


def select_inputs(seed: int, demos: int, queries: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = [{"input": _build(seed, i, _DEMOS[i], query=False)} for i in range(demos)]
    test = [{"input": _build(seed, i, _QUERIES[i], query=True)} for i in range(queries)]
    return {"train": train, "test": test}


def analyze_input(grid):
    main, (dr, dc), moved = _scene_state(grid)
    cue = _cue_for(grid, moved)
    reverse = {(r - dr, c - dc) for r, c in main}
    wrong = _cue_for(grid, reverse)
    h, w = len(grid), len(grid[0])
    return {
        "delta": [dr, dc],
        "main_cells": len(main),
        "retained_moved_cells": sum(0 <= r < h and 0 <= c < w for r, c in moved),
        "cue_color": cue,
        "wrong_cue_color": wrong,
        "relay_cells": [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == cue],
        "wrong_relay_cells": [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == wrong],
    }


def _shortcut_outputs(grid, chosen):
    canonical = output_for(grid, "translate_only")
    relay = output_for(grid, "translated_cue_relay")
    main, (dr, dc), moved = _scene_state(grid)
    cue = _cue_for(grid, moved)
    reverse = {(r - dr, c - dc) for r, c in main}
    wrong = _cue_for(grid, reverse)
    h, w = len(grid), len(grid[0])

    def paint(cells):
        out = [[0] * w for _ in range(h)]
        for r, c in cells:
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = 8
        return out

    foreign = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if 4 <= v <= 9}
    cue_cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == cue}
    wrong_cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == wrong}
    moved_cue = {(r + dr, c + dc) for r, row in enumerate(grid) for c, v in enumerate(row) if v == cue}
    return {
        "opposite_setting": relay if chosen == "translate_only" else canonical,
        "reverse_probe_relay": paint(set(moved) | wrong_cells),
        "relay_all_foreign": paint(set(moved) | foreign),
        "translate_payload_too": paint(set(moved) | moved_cue),
        "leave_payload_color": deepcopy(grid),
    }


def assess_demos(demos, chosen: str):
    if chosen not in MODES:
        raise ValueError("unknown finish_rule")
    setting_survivors = [mode for mode in MODES if all(output_for(p["input"], mode) == p["output"] for p in demos)]
    names = list(_shortcut_outputs(demos[0]["input"], chosen))
    survivors = [name for name in names if all(_shortcut_outputs(p["input"], chosen)[name] == p["output"] for p in demos)]
    return {"demonstrations": len(demos), "setting_survivors": setting_survivors,
            "harmful_shortcut_survivors": survivors, "rivals_tested": len(names)}


def generate_episode(seed: int, mode: str, demos: int, queries: int):
    if mode not in MODES:
        raise ValueError("unknown finish_rule")
    selected = select_inputs(seed, demos, queries)
    result = {"program_solution": program_for(mode), "train": [], "test": []}
    for split in ("train", "test"):
        result[split] = [{"input": deepcopy(row["input"]), "output": output_for(row["input"], mode)}
                         for row in selected[split]]
    return result


def causal_case(grid):
    info = analyze_input(grid)
    return {
        "input": deepcopy(grid),
        "settings": {"finish_rule": "translated_cue_relay"},
        "intermediate_value": {
            "translated_cells_retained": info["retained_moved_cells"],
            "cue_color": info["cue_color"],
            "wrong_cue_color": info["wrong_cue_color"],
        },
        "program": program_for("translated_cue_relay"),
        "output": output_for(grid, "translated_cue_relay"),
        "counterfactual_program": _counterfactual_program(),
        "counterfactual_output": _counterfactual_output(grid),
        "ablation": "wrong_intermediate",
    }
