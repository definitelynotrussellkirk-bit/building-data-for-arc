"""Episode-fixed modal transform composition for ``4296e507c770``.

The canonical ``direct`` setting is the exact selected ARC rule.  The alternate
setting counts transform-marker colors, takes the unique repeated color as a
global transform, then applies that transform *after* each marker's local
transform before stamping the normalized color-2 template.
"""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "4296e507c770"
HERE = Path(__file__).resolve().parent
PARAMETER_NAME = "stamp_rule"
SETTINGS = ("direct", "modal_postcompose")
SHORTCUTS = (
    "global_only",
    "modal_precompose",
    "fixed_lr",
    "fixed_ud",
    "fixed_cw",
    "first_marker",
    "last_marker",
)
DEFAULT_SETTING = "direct"
PROTOTYPE_VERSION = "1.0.0"

# height, width, template size, repeated marker color
DEMO_PROFILES = (
    (12, 18, 5, 4),
    (13, 18, 6, 6),
    (16, 20, 7, 5),
    (18, 22, 8, 4),
    (22, 24, 9, 6),
    (24, 26, 4, 5),
)
QUERY_PROFILES = (
    (14, 20, 7, 5),
    (18, 24, 8, 4),
    (24, 28, 6, 6),
    (30, 30, 9, 3),
)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_MARKER_COLORS = (3, 4, 5, 6)
_OP_FOR_COLOR = {3: 0, 4: 1, 5: 2, 6: 3}
_ALLOWED = {0, 2, 3, 4, 5, 6}

# Reviewed production fallback shapes: connected, <=4x4, and full D4 orbit.
_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (0, 1), (0, 2), (1, 0)),
    5: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
    6: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    7: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)),
    9: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
}

_D4_SEQUENCES = (
    (),
    (1,),
    (2,),
    (3,),
    (4,),
    (5,),
    (1, 3),
    (3, 1),
)

# Stable stress-case orders.  Ordinary examples randomize this multiset while
# keeping the repeated cue away from the first/last positions; these fixed
# orders make the 30x30 boundary witness deterministic and guarantee that its
# stamped output reaches every edge.
_STRESS_COLOR_ORDERS = {
    3: (4, 3, 5, 3, 6),
    4: (5, 4, 3, 4, 6),
    5: (4, 5, 3, 5, 6),
    6: (4, 6, 3, 6, 5),
}


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _setting(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER_NAME}
        or type(settings[PARAMETER_NAME]) is not str
        or settings[PARAMETER_NAME] not in SETTINGS
    ):
        raise ValueError("settings must contain only stamp_rule=direct|modal_postcompose")
    return settings[PARAMETER_NAME]


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _transform_offsets(
    cells: Iterable[tuple[int, int]], operation: int
) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    if not points:
        return ()
    height = max(row for row, _ in points) + 1
    width = max(col for _, col in points) + 1
    transformed = []
    for row, col in points:
        if operation == 0:
            point = (row, col)
        elif operation == 1:
            point = (row, width - 1 - col)
        elif operation == 2:
            point = (height - 1 - row, col)
        elif operation == 3:
            point = (col, height - 1 - row)
        elif operation == 4:
            point = (height - 1 - row, width - 1 - col)
        elif operation == 5:
            point = (width - 1 - col, row)
        else:
            raise ValueError("operation must be in 0..5")
        transformed.append(point)
    return _normalize(transformed)


def _apply_operations(
    shape: Iterable[tuple[int, int]], operations: Iterable[int]
) -> tuple[tuple[int, int], ...]:
    result = _normalize(shape)
    for operation in operations:
        result = _transform_offsets(result, operation)
    return result


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            row, col = stack.pop()
            for drow, dcol in _CARDINAL:
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _facts(grid: object) -> dict[str, Any]:
    data = _grid(grid)
    height, width = len(data), len(data[0])
    used = {value for row in data for value in row}
    if not used <= _ALLOWED:
        raise ValueError("input may contain only colors 0, 2, 3, 4, 5, and 6")
    template_cells = {
        (row, col)
        for row, values in enumerate(data)
        for col, value in enumerate(values)
        if value == 2
    }
    components = _components(template_cells)
    if len(components) != 1:
        raise ValueError("exactly one connected color-2 template is required")
    shape = _normalize(components[0])
    markers = sorted(
        (row, col, value)
        for row, values in enumerate(data)
        for col, value in enumerate(values)
        if value in _MARKER_COLORS
    )
    if not markers:
        raise ValueError("at least one transform marker is required")
    marker_counts = Counter(value for _, _, value in markers)
    max_count = max(marker_counts.values())
    modal = [color for color, count in marker_counts.items() if count == max_count]
    modal_color = modal[0] if len(modal) == 1 else None
    orbit = {
        _apply_operations(shape, sequence)
        for sequence in _D4_SEQUENCES
    }
    return {
        "height": height,
        "width": width,
        "template_cells": sorted(template_cells),
        "shape": shape,
        "template_size": len(shape),
        "template_bbox": [
            max(row for row, _ in shape) + 1,
            max(col for _, col in shape) + 1,
        ],
        "markers": markers,
        "marker_count": len(markers),
        "marker_counts": dict(sorted(marker_counts.items())),
        "modal_color": modal_color,
        "d4_orbit_size": len(orbit),
    }


def features(grid: object) -> dict[str, Any]:
    return copy.deepcopy(_facts(grid))


def _require_modal(facts: dict[str, Any]) -> int:
    if facts["modal_color"] not in _MARKER_COLORS:
        raise ValueError("a unique most-frequent transform-marker color is required")
    return int(facts["modal_color"])


def _policy_output(
    grid: list[list[int]],
    policy: str,
    *,
    modal_override: int | None = None,
) -> list[list[int]]:
    facts = _facts(grid)
    shape = facts["shape"]
    markers = facts["markers"]
    if policy not in (*SETTINGS, *SHORTCUTS):
        raise ValueError(f"unsupported stamp policy: {policy}")

    if policy == "direct":
        global_op = None
    elif policy == "fixed_lr":
        global_op = 1
    elif policy == "fixed_ud":
        global_op = 2
    elif policy == "fixed_cw":
        global_op = 3
    elif policy == "first_marker":
        global_op = _OP_FOR_COLOR[markers[0][2]]
    elif policy == "last_marker":
        global_op = _OP_FOR_COLOR[markers[-1][2]]
    else:
        modal_color = modal_override if modal_override is not None else _require_modal(facts)
        if modal_color not in _MARKER_COLORS:
            raise ValueError("modal override must be one of marker colors 3..6")
        global_op = _OP_FOR_COLOR[modal_color]

    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for anchor_row, anchor_col, color in markers:
        local_op = _OP_FOR_COLOR[color]
        if policy == "direct":
            operations = (local_op,)
        elif policy == "global_only":
            operations = (global_op,)
        elif policy == "modal_precompose":
            operations = (global_op, local_op)
        else:
            operations = (local_op, global_op)
        offsets = _apply_operations(shape, operations)
        for drow, dcol in offsets:
            row, col = anchor_row + drow, anchor_col + dcol
            if not (0 <= row < facts["height"] and 0 <= col < facts["width"]):
                raise ValueError("transformed stamp leaves the grid")
            output[row][col] = 8
    return output


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    return _policy_output(grid, _setting(settings))


def transform_with_modal_override(
    grid: list[list[int]], modal_color: int
) -> list[list[int]]:
    _integer(modal_color, 3, 6, "modal_color")
    return _policy_output(grid, "modal_postcompose", modal_override=modal_color)


def _racket_program(global_source: str, composition: str) -> str:
    if composition not in {"post", "pre", "global"}:
        raise ValueError("unknown Racket composition")
    if global_source == "modal":
        global_expr = "(modal-color g)"
    elif global_source == "first":
        global_expr = "(first-marker-color g)"
    elif global_source == "last":
        global_expr = "(last-marker-color g)"
    elif global_source in {"4", "5", "6"}:
        global_expr = global_source
    else:
        raise ValueError("unknown Racket global source")
    if composition == "post":
        offsets = "(transform-offsets (transform-offsets base (op-for-marker color)) global-op)"
    elif composition == "pre":
        offsets = "(transform-offsets (transform-offsets base global-op) (op-for-marker color))"
    else:
        offsets = "(transform-offsets base global-op)"
    return f"""(rule! (let ((dummy 0))
  (define (offset< a b)
    (if (= (first a) (first b))
        (< (second a) (second b))
        (< (first a) (first b))))
  (define (find-single grid color)
    (first (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0))))
  (define (markers grid color) (sort (find-color grid color) cell<))
  (define (all-markers grid)
    (sort (append (markers grid 3) (markers grid 4)
                  (markers grid 5) (markers grid 6)) cell<))
  (define (first-marker-color grid)
    (let ((p (first (all-markers grid))))
      (at grid (first p) (second p))))
  (define (last-marker-color grid)
    (let* ((xs (all-markers grid))
           (p (list-ref xs (- (length xs) 1))))
      (at grid (first p) (second p))))
  (define (modal-color grid)
    (let ((c3 (length (markers grid 3)))
          (c4 (length (markers grid 4)))
          (c5 (length (markers grid 5)))
          (c6 (length (markers grid 6))))
      (cond ((and (> c3 c4) (> c3 c5) (> c3 c6)) 3)
            ((and (> c4 c3) (> c4 c5) (> c4 c6)) 4)
            ((and (> c5 c3) (> c5 c4) (> c5 c6)) 5)
            (else 6))))
  (define (normalize-offsets offsets)
    (if (empty? offsets)
        (list)
        (let* ((r0 (apply min (map first offsets)))
               (c0 (apply min (map second offsets))))
          (sort (map (lambda (p)
                       (list (- (first p) r0) (- (second p) c0)))
                     offsets)
                offset<))))
  (define (relative-offsets obj anchor)
    (let* ((ar (cond ((= anchor 0) (obj-r1 obj))
                     ((= anchor 1) (obj-r1 obj))
                     ((= anchor 2) (obj-r2 obj))
                     (else (obj-r2 obj))))
           (ac (cond ((= anchor 0) (obj-c1 obj))
                     ((= anchor 1) (obj-c2 obj))
                     ((= anchor 2) (obj-c1 obj))
                     (else (obj-c2 obj)))))
      (sort (map (lambda (p)
                   (list (- (first p) ar) (- (second p) ac)))
                 (obj-cells obj))
            offset<)))
  (define (transform-offsets offsets op)
    (let* ((nr (normalize-offsets offsets))
           (h (+ 1 (apply max (map first nr))))
           (w (+ 1 (apply max (map second nr)))))
      (normalize-offsets
       (map (lambda (p)
              (let ((r (first p)) (c (second p)))
                (cond ((= op 0) (list r c))
                      ((= op 1) (list r (- w 1 c)))
                      ((= op 2) (list (- h 1 r) c))
                      ((= op 3) (list c (- h 1 r)))
                      ((= op 4) (list (- h 1 r) (- w 1 c)))
                      (else (list (- w 1 c) r)))))
            nr))))
  (define (place-offsets out offsets anchor color)
    (for/fold ((acc out)) ((p (in-list offsets)))
      (set-cell acc (+ (first anchor) (first p))
                    (+ (second anchor) (second p)) color)))
  (define (op-for-marker color)
    (cond ((= color 3) 0)
          ((= color 4) 1)
          ((= color 5) 2)
          ((= color 6) 3)
          (else 0)))
  (define base (relative-offsets (find-single g 2) 0))
  (define global-op (op-for-marker {global_expr}))
  (for/fold ((out (empty-grid (rows g) (cols g) 0)))
            ((color (in-list (list 3 4 5 6))))
    (for/fold ((acc out)) ((mk (in-list (markers g color))))
      (place-offsets acc {offsets} mk 8)))))"""


def program(settings: dict[str, str]) -> str:
    setting = _setting(settings)
    name = "canonical.rkt" if setting == "direct" else "modal_postcompose.rkt"
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def rival_programs() -> dict[str, str]:
    return {
        "direct": program({PARAMETER_NAME: "direct"}),
        "modal_postcompose": program({PARAMETER_NAME: "modal_postcompose"}),
        "global_only": _racket_program("modal", "global"),
        "modal_precompose": _racket_program("modal", "pre"),
        "fixed_lr": _racket_program("4", "post"),
        "fixed_ud": _racket_program("5", "post"),
        "fixed_cw": _racket_program("6", "post"),
        "first_marker": _racket_program("first", "post"),
        "last_marker": _racket_program("last", "post"),
    }


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {name: _policy_output(grid, name) for name in (*SETTINGS, *SHORTCUTS)}


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:modal-transform-composition-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _random_shape(rng: random.Random, size: int) -> tuple[tuple[int, int], ...]:
    """Draw a connected full-D4-orbit shape inside a 4x4 box."""
    for _ in range(512):
        cells = {(rng.randrange(4), rng.randrange(4))}
        while len(cells) < size:
            frontier = sorted(
                {
                    (row + drow, col + dcol)
                    for row, col in cells
                    for drow, dcol in _CARDINAL
                    if 0 <= row + drow < 4
                    and 0 <= col + dcol < 4
                    and (row + drow, col + dcol) not in cells
                }
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != size:
            continue
        shape = _normalize(cells)
        if len({_apply_operations(shape, ops) for ops in _D4_SEQUENCES}) == 8:
            return shape
    # The reviewed fallbacks are a deterministic last resort, not the normal
    # source of diversity.
    return _apply_operations(_FALLBACK_SHAPES[size], rng.choice(_D4_SEQUENCES))


def _marker_order(rng: random.Random, modal_color: int) -> tuple[int, ...]:
    """Randomize the five-marker multiset without weakening shortcut tests."""
    values = [*_MARKER_COLORS, modal_color]
    for _ in range(128):
        rng.shuffle(values)
        if (
            values[0] != 3
            and values[-1] != 3
            and values[0] != modal_color
            and values[-1] != modal_color
        ):
            return tuple(values)
    raise AssertionError("could not place modal cue away from first/last markers")


def _random_layout(
    rng: random.Random, height: int, width: int
) -> tuple[tuple[tuple[int, int], ...], tuple[int, int, int, int]]:
    """Reserve five disjoint 4x4 marker slots and one template slot."""
    row_cut = height // 2
    col_cuts = (0, width // 3, (2 * width) // 3, width)
    if row_cut < 4 or height - row_cut < 4 or min(
        col_cuts[index + 1] - col_cuts[index] for index in range(3)
    ) < 4:
        raise AssertionError("profile is too small for six 4x4 slots")
    top_row = rng.randint(0, row_cut - 4)
    bottom_row = rng.randint(row_cut, height - 4)
    cols = tuple(
        rng.randint(col_cuts[index], col_cuts[index + 1] - 4)
        for index in range(3)
    )
    anchors = (
        (top_row, cols[0]),
        (top_row, cols[1]),
        (top_row, cols[2]),
        (bottom_row, cols[0]),
        (bottom_row, cols[1]),
    )
    # row_start, row_end, col_start, col_end for the unused bottom-right slot.
    return anchors, (row_cut, height, col_cuts[2], width)


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    height, width, size, modal_color = profiles[index]
    rng = _rng(seed, split, index)
    stress = split == "test" and index == 3

    if stress:
        shape = _FALLBACK_SHAPES[size]
        anchors = (
            (0, 0),
            (0, (width - 4) // 2),
            (0, width - 4),
            (height - 4, 0),
            (height - 4, (width - 4) // 2),
        )
        colors = _STRESS_COLOR_ORDERS[modal_color]
        template_slot = (height - 4, height, width - 4, width)
    else:
        shape = _random_shape(rng, size)
        anchors, template_slot = _random_layout(rng, height, width)
        colors = _marker_order(rng, modal_color)

    if len({_apply_operations(shape, ops) for ops in _D4_SEQUENCES}) != 8:
        raise AssertionError("sampled template lost full D4 asymmetry")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for (row, col), color in zip(anchors, colors):
        grid[row][col] = color

    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    row_start, row_end, col_start, col_end = template_slot
    if stress:
        template_row = row_end - shape_height
        template_col = col_end - shape_width
    else:
        template_row = rng.randint(row_start, row_end - shape_height)
        template_col = rng.randint(col_start, col_end - shape_width)
    for drow, dcol in shape:
        grid[template_row + drow][template_col + dcol] = 2

    facts = _facts(grid)
    if facts["marker_count"] != 5 or facts["modal_color"] != modal_color:
        raise AssertionError("constructed marker-frequency cue drifted")
    if facts["d4_orbit_size"] != 8:
        raise AssertionError("constructed shape is not fully asymmetric")
    # All D4 variants fit inside each reserved 4x4 marker region.
    for policy, output in rival_outputs(grid).items():
        if len(output) != height or len(output[0]) != width:
            raise AssertionError(f"policy {policy} changed output dimensions")
    return grid


def teaching_certificate(train, query_inputs, settings):
    chosen = _setting(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    names = (*SETTINGS, *SHORTCUTS)
    rejected: dict[str, int] = {}
    for index, pair in enumerate(train):
        _grid(pair["output"])
        for name, output in rival_outputs(pair["input"]).items():
            if output != pair["output"]:
                rejected.setdefault(name, index)
    survivors = [name for name in names if name not in rejected]
    if chosen not in survivors:
        raise ValueError("demonstration labels contradict selected stamp rule")
    query_identifiable = []
    for grid in query_inputs:
        outputs = rival_outputs(grid)
        query_identifiable.append(all(outputs[name] == outputs[chosen] for name in survivors))
    return {
        "scope": (
            "two admitted stamp rules plus global-only, reversed composition, "
            "three fixed globals, and first/last-marker shortcuts"
        ),
        "survivors": survivors,
        "rejected": rejected,
        "identified": survivors == [chosen],
        "query_identifiable": query_identifiable,
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(settings),
        "program_solution": program(settings),
        "reference": "proposed_parametric",
        "training_admitted": False,
    }
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _draw(seed, split, index)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    episode["certificate"] = verify_episode(episode)
    return episode


def verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _setting(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution does not match selected stamp rule")
    seen = set()
    for split, bounds in (("train", (2, 6)), ("test", (1, 4))):
        pairs = episode.get(split)
        if type(pairs) is not list or not bounds[0] <= len(pairs) <= bounds[1]:
            raise ValueError(f"unsupported {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            expected = transform(pair["input"], settings)
            _grid(pair["output"])
            if pair["output"] != expected:
                raise ValueError(f"{split} label disagrees with selected stamp rule")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings
    )
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the selected stamp rule")
    return certificate


def visible_turn(episode, index: int) -> bytes:
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][index]]}
    )
