"""Native-ready direction-policy family for diagonal L-tromino projections.

The canonical setting preserves the selected Racket program byte-for-byte.
The alternate keeps the same source grammar, component discovery, missing-corner
intermediate, fill colors, clipping, and green-last collision precedence while
swapping which source color moves toward versus away from its opening.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "e99db71ae23d"
DIRECTION_POLICIES = (
    "gray_toward_red_away",
    "gray_away_red_toward",
)
CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let ((visited (make-hash))\n                 (pieces (list)))\n             (for* ((r (range 0 h)) (c (range 0 w)))\n                   (when\n                     (and\n                       (or (= (at g r c) 2) (= (at g r c) 5))\n                       (not (hash-has-key? visited (list r c))))\n                     (let ((color (at g r c)))\n                       (let bfs\n                            ((queue (list (list r c))) (cells (list)))\n                            (cond\n                              ((null? queue) (set! pieces (append pieces (list (list color cells)))))\n                              (else (let ((cr (first (car queue)))\n                                          (cc (second (car queue))))\n                                      (if (or\n                                            (hash-has-key? visited (list cr cc))\n                                            (< cr 0)\n                                            (>= cr h)\n                                            (< cc 0)\n                                            (>= cc w)\n                                            (!= (at g cr cc) color))\n                                          (bfs (cdr queue) cells)\n                                          (begin\n                                            (hash-set! visited (list cr cc) #t)\n                                            (bfs (append (cdr queue)\n                                                         (list (list (- cr 1) cc)\n                                                               (list (+ cr 1) cc)\n                                                               (list cr (- cc 1))\n                                                               (list cr (+ cc 1))))\n                                                 (cons (list cr cc) cells)))))))))))\n             (let ((result (make-hash)))\n               (for* ((r (range 0 h)) (c (range 0 w)))\n                     (hash-set! result (list r c) (at g r c)))\n               (for ((pass-info (list (list 5 4) (list 2 3))))\n                 (let ((pass-color (first pass-info))\n                       (fill-color (second pass-info)))\n                   (for ((piece pieces))\n                     (when\n                       (= (first piece) pass-color)\n                       (let* ((cells (second piece))\n                              (rmin (min-of first cells))\n                              (cmin (min-of second cells))\n                              (rmax (max-of first cells))\n                              (cmax (max-of second cells))\n                              (cell-set (make-hash)))\n                         (for ((c cells)) (hash-set! cell-set c #t))\n                         (let* ((opening (find (lambda (p)\n                                                 (not (hash-has-key? cell-set p)))\n                                               (list (list rmin cmin)\n                                                     (list rmin cmax)\n                                                     (list rmax cmin)\n                                                     (list rmax cmax))))\n                                (or2 (first opening))\n                                (oc (second opening))\n                                (dr (if (> (* 2 or2) (+ rmin rmax)) 1 -1))\n                                (dc (if (> (* 2 oc) (+ cmin cmax)) 1 -1))\n                                (sdr (if (= pass-color 5) dr (- 0 dr)))\n                                (sdc (if (= pass-color 5) dc (- 0 dc))))\n                           (for ((cell cells))\n                             (let ((nr (+ (first cell) sdr))\n                                   (nc (+ (second cell) sdc)))\n                               (when\n                                 (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))\n                                 (hash-set! result (list nr nc) fill-color))))))))))\n               (cellmap g (r c v) (hash-ref result (list r c) 0)))))))'

_HERE = Path(__file__).resolve().parent
_GENERATOR_PATH = _HERE.parents[1] / "generator.py"
_SPEC = importlib.util.spec_from_file_location(
    "_e99db71ae23d_source_generator_for_parametric",
    _GENERATOR_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_GENERATOR_PATH)
source = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = source
_SPEC.loader.exec_module(source)

_L_SHAPES = source._L_SHAPES
_CARDINAL = source._CARDINAL

# Every requested episode uses a setting-neutral stream of these six demo roles.
# The first two suffice to distinguish both declared settings and the bounded
# plausible rivals below. Additional demos add coverage rather than changing the
# hidden rule.
_DEMO_ROLES = (
    ("source", "general_orientation_8"),
    ("custom", (14, 16, 10, True, True, False)),
    ("source", "general_dense_14"),
    ("custom", (16, 20, 12, True, True, True)),
    ("source", "general_edge_overlap_6"),
    ("custom", (18, 22, 16, True, True, True)),
)
_QUERY_ROLES = (
    ("source", "general_edge_6"),
    ("custom", (16, 18, 10, True, True, False)),
    ("custom", (21, 24, 14, True, True, False)),
    ("custom", (30, 30, 16, True, True, True)),
)

# Two-piece motifs whose cross-color projections collide under exactly the named
# policy before arbitrary rotation/reflection/translation.
_COLLISION_MOTIFS = {
    "gray_toward_red_away": (
        (5, 0, 1, 4),
        (2, 2, 1, 1),
    ),
    "gray_away_red_toward": (
        (5, 0, 1, 1),
        (2, 0, 2, 4),
    ),
}


def _replace_exact(text: str, old: str, new: str, *, count: int = 1) -> str:
    observed = text.count(old)
    if observed != count:
        raise RuntimeError(f"expected {count} program fragment(s), found {observed}: {old}")
    return text.replace(old, new)


def _program_variant(
    policy: str,
    *,
    green_last: bool = True,
    forced_opening: tuple[int, int] | None = None,
) -> str:
    policy = _validate_policy(policy)
    program = CANONICAL_PROGRAM
    if policy == "gray_away_red_toward":
        program = _replace_exact(
            program,
            "(sdr (if (= pass-color 5) dr (- 0 dr)))",
            "(sdr (if (= pass-color 2) dr (- 0 dr)))",
        )
        program = _replace_exact(
            program,
            "(sdc (if (= pass-color 5) dc (- 0 dc)))",
            "(sdc (if (= pass-color 2) dc (- 0 dc)))",
        )
    if not green_last:
        program = _replace_exact(
            program,
            "(for ((pass-info (list (list 5 4) (list 2 3))))",
            "(for ((pass-info (list (list 2 3) (list 5 4))))",
        )
    if forced_opening is not None:
        if (
            type(forced_opening) is not tuple
            or len(forced_opening) != 2
            or any(type(value) is not int or value not in (-1, 1) for value in forced_opening)
        ):
            raise ValueError("forced_opening must be a pair of exact -1/+1 integers")
        dr, dc = forced_opening
        program = _replace_exact(
            program,
            "(dr (if (> (* 2 or2) (+ rmin rmax)) 1 -1))",
            f"(dr {dr})",
        )
        program = _replace_exact(
            program,
            "(dc (if (> (* 2 oc) (+ cmin cmax)) 1 -1))",
            f"(dc {dc})",
        )
    return program


def _program_both(*, toward: bool, green_last: bool = True) -> str:
    program = CANONICAL_PROGRAM
    dr = "dr" if toward else "(- 0 dr)"
    dc = "dc" if toward else "(- 0 dc)"
    program = _replace_exact(
        program,
        "(sdr (if (= pass-color 5) dr (- 0 dr)))",
        f"(sdr {dr})",
    )
    program = _replace_exact(
        program,
        "(sdc (if (= pass-color 5) dc (- 0 dc)))",
        f"(sdc {dc})",
    )
    if not green_last:
        program = _replace_exact(
            program,
            "(for ((pass-info (list (list 5 4) (list 2 3))))",
            "(for ((pass-info (list (list 2 3) (list 5 4))))",
        )
    return program


def program_for(policy: str) -> str:
    policy = _validate_policy(policy)
    return CANONICAL_PROGRAM if policy == DIRECTION_POLICIES[0] else _program_variant(policy)


def forced_opening_program(policy: str, vector: tuple[int, int] = (1, 1)) -> str:
    return _program_variant(policy, forced_opening=vector)


_RIVAL_PROGRAM_BUILDERS = {
    "both_toward": lambda: _program_both(toward=True),
    "both_away": lambda: _program_both(toward=False),
    "canonical_yellow_wins": lambda: _program_variant(
        "gray_toward_red_away", green_last=False
    ),
    "swapped_yellow_wins": lambda: _program_variant(
        "gray_away_red_toward", green_last=False
    ),
    "canonical_fixed_southeast": lambda: forced_opening_program(
        "gray_toward_red_away", (1, 1)
    ),
    "swapped_fixed_southeast": lambda: forced_opening_program(
        "gray_away_red_toward", (1, 1)
    ),
}
RIVAL_NAMES = tuple(_RIVAL_PROGRAM_BUILDERS)


def rival_program(name: str) -> str:
    if type(name) is not str or name not in _RIVAL_PROGRAM_BUILDERS:
        raise ValueError(f"unknown rival: {name!r}")
    return _RIVAL_PROGRAM_BUILDERS[name]()


def _validate_policy(policy: str) -> str:
    if type(policy) is not str or policy not in DIRECTION_POLICIES:
        raise ValueError("direction_policy is undeclared")
    return policy


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_count(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or value not in (2, 5, 7) for value in row)
            for row in grid
        )
    ):
        raise ValueError("input must be a 1..30 rectangular exact-integer {2,5,7} grid")
    return grid


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _piece_tuple(component: dict[str, Any]) -> tuple[int, int, int, int]:
    shape = component["shape_index"]
    if shape is None:
        raise ValueError("every active component must be a three-cell L-tromino")
    return component["color"], shape, component["row0"], component["col0"]


def _pieces(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    _validate_grid(grid)
    components = source._components(grid)
    pieces = [_piece_tuple(component) for component in components]
    active = sum(value in (2, 5) for row in grid for value in row)
    if active != 3 * len(pieces) or not pieces:
        raise ValueError("active cells must partition into L-trominoes")
    if {piece[0] for piece in pieces} != {2, 5}:
        raise ValueError("both source colors are required")
    return pieces


def _opening_vector(shape_index: int) -> tuple[int, int]:
    return source._shift(5, shape_index)


def _toward_for(color: int, policy: str) -> bool:
    policy = _validate_policy(policy)
    return color == (5 if policy == DIRECTION_POLICIES[0] else 2)


def _targets(
    piece: tuple[int, int, int, int],
    policy: str,
    *,
    forced_opening: tuple[int, int] | None = None,
) -> tuple[tuple[int, int], ...]:
    color, shape_index, _row0, _col0 = piece
    dr, dc = _opening_vector(shape_index) if forced_opening is None else forced_opening
    if not _toward_for(color, policy):
        dr, dc = -dr, -dc
    return tuple((row + dr, col + dc) for row, col in source._piece_cells(piece))


def _apply_config(
    grid: list[list[int]],
    *,
    gray_toward: bool,
    red_toward: bool,
    green_last: bool,
    forced_opening: tuple[int, int] | None = None,
) -> list[list[int]]:
    pieces = _pieces(grid)
    height, width = len(grid), len(grid[0])
    output = _copy_grid(grid)
    passes = ((5, 4), (2, 3)) if green_last else ((2, 3), (5, 4))
    for color, fill in passes:
        toward = gray_toward if color == 5 else red_toward
        for piece in pieces:
            if piece[0] != color:
                continue
            dr, dc = _opening_vector(piece[1]) if forced_opening is None else forced_opening
            if not toward:
                dr, dc = -dr, -dc
            for row, col in source._piece_cells(piece):
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = fill
    return output


def apply_policy(grid: list[list[int]], policy: str) -> list[list[int]]:
    policy = _validate_policy(policy)
    return _apply_config(
        grid,
        gray_toward=policy == DIRECTION_POLICIES[0],
        red_toward=policy == DIRECTION_POLICIES[1],
        green_last=True,
    )


def apply_with_forced_opening(
    grid: list[list[int]], policy: str, vector: tuple[int, int]
) -> list[list[int]]:
    if (
        type(vector) is not tuple
        or len(vector) != 2
        or any(type(value) is not int or value not in (-1, 1) for value in vector)
    ):
        raise ValueError("vector must be an exact (-1/+1, -1/+1) tuple")
    policy = _validate_policy(policy)
    return _apply_config(
        grid,
        gray_toward=policy == DIRECTION_POLICIES[0],
        red_toward=policy == DIRECTION_POLICIES[1],
        green_last=True,
        forced_opening=vector,
    )


def _rival_apply(name: str, grid: list[list[int]]) -> list[list[int]]:
    if name == "both_toward":
        return _apply_config(grid, gray_toward=True, red_toward=True, green_last=True)
    if name == "both_away":
        return _apply_config(grid, gray_toward=False, red_toward=False, green_last=True)
    if name == "canonical_yellow_wins":
        return _apply_config(grid, gray_toward=True, red_toward=False, green_last=False)
    if name == "swapped_yellow_wins":
        return _apply_config(grid, gray_toward=False, red_toward=True, green_last=False)
    if name == "canonical_fixed_southeast":
        return _apply_config(
            grid,
            gray_toward=True,
            red_toward=False,
            green_last=True,
            forced_opening=(1, 1),
        )
    if name == "swapped_fixed_southeast":
        return _apply_config(
            grid,
            gray_toward=False,
            red_toward=True,
            green_last=True,
            forced_opening=(1, 1),
        )
    raise ValueError(name)


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    pieces = _pieces(grid)
    height, width = len(grid), len(grid[0])
    source_cells = {cell for piece in pieces for cell in source._piece_cells(piece)}
    orientation = {
        str(color): sorted({piece[1] for piece in pieces if piece[0] == color})
        for color in (2, 5)
    }
    collision_cells: dict[str, int] = {}
    clipped_cells: dict[str, int] = {}
    source_target_hits: dict[str, int] = {}
    for policy in DIRECTION_POLICIES:
        targets: defaultdict[tuple[int, int], list[int]] = defaultdict(list)
        clipped = 0
        for piece in pieces:
            for target in _targets(piece, policy):
                if 0 <= target[0] < height and 0 <= target[1] < width:
                    targets[target].append(piece[0])
                else:
                    clipped += 1
        collision_cells[policy] = sum(len(set(colors)) > 1 for colors in targets.values())
        clipped_cells[policy] = clipped
        source_target_hits[policy] = len(set(targets) & source_cells)
    rows = [row for row, _ in source_cells]
    cols = [col for _, col in source_cells]
    return {
        "shape": [height, width],
        "piece_count": len(pieces),
        "color_counts": dict(Counter(piece[0] for piece in pieces)),
        "orientation_support": orientation,
        "opening_vectors": [list(_opening_vector(piece[1])) for piece in pieces],
        "collision_cells": collision_cells,
        "clipped_cells": clipped_cells,
        "source_target_hits": source_target_hits,
        "source_span": {"rows": [min(rows), max(rows)], "cols": [min(cols), max(cols)]},
    }


def occupied_quadrants(grid: list[list[int]]) -> list[int]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    result = set()
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (2, 5):
                continue
            result.add((2 if row * 2 >= height else 0) + (1 if col * 2 >= width else 0))
    return sorted(result)


def _derived_rng(seed: int, slot: str) -> random.Random:
    payload = f"{TASK_ID}:direction-policy-v1:{seed}:{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _inside(target: tuple[int, int], height: int, width: int) -> bool:
    return 0 <= target[0] < height and 0 <= target[1] < width


def _can_add(
    piece: tuple[int, int, int, int],
    pieces: list[tuple[int, int, int, int]],
    height: int,
    width: int,
) -> bool:
    cells = set(source._piece_cells(piece))
    if len(cells) != 3 or any(not _inside(cell, height, width) for cell in cells):
        return False
    existing_cells = {cell for current in pieces for cell in source._piece_cells(current)}
    if cells & existing_cells:
        return False
    same_color = {
        cell
        for current in pieces
        if current[0] == piece[0]
        for cell in source._piece_cells(current)
    }
    if any(
        (row + dr, col + dc) in same_color
        for row, col in cells
        for dr, dc in _CARDINAL
    ):
        return False
    for policy in DIRECTION_POLICIES:
        candidate_targets = {
            target for target in _targets(piece, policy) if _inside(target, height, width)
        }
        existing_targets = {
            target
            for current in pieces
            for target in _targets(current, policy)
            if _inside(target, height, width)
        }
        if candidate_targets & (cells | existing_cells):
            return False
        if cells & existing_targets:
            return False
    return True


def _add_group(
    group: list[tuple[int, int, int, int]],
    pieces: list[tuple[int, int, int, int]],
    height: int,
    width: int,
) -> bool:
    trial = list(pieces)
    for piece in group:
        if not _can_add(piece, trial, height, width):
            return False
        trial.append(piece)
    pieces[:] = trial
    return True


def _place_motif(
    rng: random.Random,
    pieces: list[tuple[int, int, int, int]],
    motif: tuple[tuple[int, int, int, int], ...],
    height: int,
    width: int,
) -> bool:
    for _ in range(500):
        transformed = source._transform_pieces(
            list(motif), rng.randrange(4), bool(rng.randrange(2))
        )
        cells = [cell for piece in transformed for cell in source._piece_cells(piece)]
        motif_h = max(row for row, _ in cells) + 1
        motif_w = max(col for _, col in cells) + 1
        if motif_h + 4 > height or motif_w + 4 > width:
            continue
        row_offset = rng.randint(2, height - motif_h - 2)
        col_offset = rng.randint(2, width - motif_w - 2)
        group = source._offset_pieces(transformed, row_offset, col_offset)
        if _add_group(group, pieces, height, width):
            return True
    return False


def _place_requested(
    rng: random.Random,
    pieces: list[tuple[int, int, int, int]],
    height: int,
    width: int,
    color: int,
    shape: int,
) -> bool:
    for _ in range(2500):
        piece = (color, shape, rng.randrange(height - 1), rng.randrange(width - 1))
        if _can_add(piece, pieces, height, width):
            pieces.append(piece)
            return True
    return False


def _render(height: int, width: int, pieces: list[tuple[int, int, int, int]]):
    grid = [[7 for _ in range(width)] for _ in range(height)]
    for piece in pieces:
        for row, col in source._piece_cells(piece):
            grid[row][col] = piece[0]
    return grid


def _custom_scene(
    rng: random.Random,
    height: int,
    width: int,
    count: int,
    dual_collision: bool,
    all_orientations: bool,
    boundary_stress: bool,
) -> list[list[int]]:
    if not 8 <= count <= 16:
        raise ValueError("custom piece count must be in 8..16")
    for _scene_attempt in range(200):
        pieces: list[tuple[int, int, int, int]] = []
        if boundary_stress:
            # These anchors force full source span and make clipping active under
            # opposite direction policies without changing the common grammar.
            anchors = [
                (5, 3, 0, 0),
                (2, 0, height - 2, width - 2),
            ]
            if not _add_group(anchors, pieces, height, width):
                continue
        if dual_collision:
            if not _place_motif(
                rng,
                pieces,
                _COLLISION_MOTIFS[DIRECTION_POLICIES[0]],
                height,
                width,
            ):
                continue
            if not _place_motif(
                rng,
                pieces,
                _COLLISION_MOTIFS[DIRECTION_POLICIES[1]],
                height,
                width,
            ):
                continue
        if all_orientations:
            missing = [
                (color, shape)
                for color in (2, 5)
                for shape in range(4)
                if not any(piece[0] == color and piece[1] == shape for piece in pieces)
            ]
            rng.shuffle(missing)
            if any(
                not _place_requested(rng, pieces, height, width, color, shape)
                for color, shape in missing
            ):
                continue
        while len(pieces) < count:
            color = (2, 5)[rng.randrange(2)]
            shape = rng.randrange(4)
            if not _place_requested(rng, pieces, height, width, color, shape):
                break
        if len(pieces) != count:
            continue
        grid = _render(height, width, pieces)
        try:
            analysis = analyze_scene(grid)
            outputs = [apply_policy(grid, policy) for policy in DIRECTION_POLICIES]
        except ValueError:
            continue
        if any(analysis["source_target_hits"].values()):
            continue
        if outputs[0] == outputs[1]:
            continue
        if any(not ({3, 4} <= {value for row in output for value in row}) for output in outputs):
            continue
        if dual_collision and any(
            analysis["collision_cells"][policy] == 0 for policy in DIRECTION_POLICIES
        ):
            continue
        if all_orientations and any(
            analysis["orientation_support"][str(color)] != [0, 1, 2, 3]
            for color in (2, 5)
        ):
            continue
        if boundary_stress:
            if analysis["source_span"] != {
                "rows": [0, height - 1],
                "cols": [0, width - 1],
            }:
                continue
            if any(analysis["clipped_cells"][policy] == 0 for policy in DIRECTION_POLICIES):
                continue
            if occupied_quadrants(grid) != [0, 1, 2, 3]:
                continue
        return grid
    raise RuntimeError(
        f"could not construct custom scene {height}x{width}/{count} after bounded attempts"
    )


def _source_scene(rng: random.Random, profile: str) -> list[list[int]]:
    for _ in range(200):
        grid = source._draw_general(rng, profile)
        analysis = analyze_scene(grid)
        if any(analysis["source_target_hits"].values()):
            continue
        if apply_policy(grid, DIRECTION_POLICIES[0]) == apply_policy(
            grid, DIRECTION_POLICIES[1]
        ):
            continue
        return grid
    raise RuntimeError(f"could not draw shared-safe source profile {profile}")


def _role_grid(seed: int, split: str, index: int, role) -> list[list[int]]:
    rng = _derived_rng(seed, f"{split}:{index}:{role!r}")
    kind, spec = role
    if kind == "source":
        return _source_scene(rng, spec)
    height, width, count, dual, orientations, boundary = spec
    return _custom_scene(rng, height, width, count, dual, orientations, boundary)


def generate_episode(seed: int, *, policy: str, demos: int, queries: int) -> dict:
    seed = _validate_seed(seed)
    policy = _validate_policy(policy)
    demos = _validate_count("demos", demos, 2, 6)
    queries = _validate_count("queries", queries, 4, 4)
    train_inputs = [
        _role_grid(seed, "demo", index, _DEMO_ROLES[index])
        for index in range(demos)
    ]
    test_inputs = [
        _role_grid(seed, "query", index, role)
        for index, role in enumerate(_QUERY_ROLES)
    ]
    all_inputs = train_inputs + test_inputs
    frozen = [_freeze(grid) for grid in all_inputs]
    if len(frozen) != len(set(frozen)):
        raise RuntimeError("episode construction produced duplicate visible inputs")
    return {
        "train": [
            {"input": _copy_grid(grid), "output": apply_policy(grid, policy)}
            for grid in train_inputs
        ],
        "test": [
            {"input": _copy_grid(grid), "output": apply_policy(grid, policy)}
            for grid in test_inputs
        ],
        "program_solution": program_for(policy),
    }


def lesson_certificate(episode: dict) -> dict[str, Any]:
    if not isinstance(episode, dict):
        raise ValueError("episode must be an object")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must have train/test lists")
    program = episode.get("program_solution")
    program_to_policy = {program_for(policy): policy for policy in DIRECTION_POLICIES}
    if program not in program_to_policy:
        raise ValueError("episode program is not a declared setting")
    selected = program_to_policy[program]
    declared_survivors = [
        policy
        for policy in DIRECTION_POLICIES
        if all(apply_policy(pair["input"], policy) == pair["output"] for pair in train)
    ]
    plausible = {
        DIRECTION_POLICIES[0]: lambda grid: apply_policy(grid, DIRECTION_POLICIES[0]),
        DIRECTION_POLICIES[1]: lambda grid: apply_policy(grid, DIRECTION_POLICIES[1]),
        **{name: (lambda grid, rival=name: _rival_apply(rival, grid)) for name in RIVAL_NAMES},
    }
    plausible_survivors = [
        name
        for name, apply in plausible.items()
        if all(apply(pair["input"]) == pair["output"] for pair in train)
    ]
    query_disagreements = {
        f"query_{index}": apply_policy(pair["input"], selected)
        != apply_policy(
            pair["input"],
            DIRECTION_POLICIES[1] if selected == DIRECTION_POLICIES[0] else DIRECTION_POLICIES[0],
        )
        for index, pair in enumerate(test)
    }
    return {
        "selected": selected,
        "declared_survivors": declared_survivors,
        "plausible_survivors": plausible_survivors,
        "query_disagreements": query_disagreements,
        "identifiable": declared_survivors == [selected]
        and plausible_survivors == [selected]
        and all(query_disagreements.values()),
        "scope": "Finite declared settings plus six authored plausible rivals; not universal uniqueness.",
    }
