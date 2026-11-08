"""Native parametric adapter for 040bfb038c65.

The canonical setting is byte-for-byte identical to the selected ARC rule.  The
alternate keeps the D4-outlier inference as step A, then uses the outlier's
input-dependent corner anchor to select the farthest repeated-shape object as
step B.  Inputs are shared across settings and include a boundary-spanning
30x30 query.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys


_TASK_ID = "040bfb038c65"
_HOME = Path(__file__).resolve().parent
_GENERATOR_PATH = _HOME.parents[1] / "generator.py"
_CANONICAL_PROGRAM = '(rule!\n  (let ((dummy 0))\n    (define objs (filter (lambda (o) (= (obj-color o) 4)) (objects g 0)))\n    (define (canon obj)\n      (first (sort (map (lambda (cells) (format "~s" cells)) (all-transforms (obj-cells obj))) string<?)))\n    (define keyed (map (lambda (o) (list (canon o) o)) objs))\n    (define odd\n      (let loop ((remaining keyed))\n        (cond [(empty? remaining) #f]\n              [(= (count-where (lambda (x) (equal? (first x) (first (first remaining)))) keyed) 1)\n               (second (first remaining))]\n              [else (loop (rest remaining))])))\n    (if odd (paint-cells g (obj-cells odd) 8) g)))'
_FARTHEST_PARTNER_PROGRAM = '(rule!\n  (let ((dummy 0))\n    (define objs (filter (lambda (o) (= (obj-color o) 4)) (objects g 0)))\n    (define (canon obj)\n      (first (sort (map (lambda (cells) (format "~s" cells)) (all-transforms (obj-cells obj))) string<?)))\n    (define keyed (map (lambda (o) (list (canon o) o)) objs))\n    (define odd\n      (let loop ((remaining keyed))\n        (cond [(empty? remaining) #f]\n              [(= (count-where (lambda (x) (equal? (first x) (first (first remaining)))) keyed) 1)\n               (second (first remaining))]\n              [else (loop (rest remaining))])))\n    (define repeated\n      (if odd\n          (filter (lambda (o) (not (equal? (canon o) (canon odd)))) objs)\n          \'()))\n    (define partner\n      (if (and odd (not (empty? repeated)))\n          (pick-max repeated\n                    (lambda (o)\n                      (+ (abs (- (obj-r1 o) (obj-r1 odd)))\n                         (abs (- (obj-c1 o) (obj-c1 odd))))))\n          #f))\n    (if partner (paint-cells g (obj-cells partner) 8) g)))'
_SETTINGS = {"outsider": _CANONICAL_PROGRAM, "farthest_partner": _FARTHEST_PARTNER_PROGRAM}

_DEMO_SPECS = (
    (7, 9, "smaller_odd", 0),
    (10, 12, "larger_odd", 1),
    (14, 16, "same_size_odd", 3),
    (9, 15, "smaller_odd", 2),
    (13, 10, "larger_odd", 0),
    (8, 16, "same_size_odd", 3),
)
_QUERY_SPECS = (
    (8, 10, "larger_odd", 2),
    (12, 14, "smaller_odd", 3),
    (14, 16, "same_size_odd", 0),
    (30, 30, "larger_odd", 1),
)


def _load_selected_generator():
    name = "_arc_parametric_selected_" + _TASK_ID
    spec = importlib.util.spec_from_file_location(name, _GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load selected generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GENERATOR = _load_selected_generator()


def _validate_settings(settings):
    if not isinstance(settings, dict) or set(settings) != {"target"}:
        raise ValueError("settings must contain exactly the target parameter")
    target = settings["target"]
    if type(target) is not str or target not in _SETTINGS:
        raise ValueError("target must be outsider or farthest_partner")
    return target


def program(settings):
    """Return exact Racket source for one declared private setting."""
    return _SETTINGS[_validate_settings(settings)]


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _shape(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _bbox(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _corner_origin(slot, height, width, shape):
    shape_h, shape_w = _bbox(shape)
    return (
        0 if slot < 2 else height - shape_h,
        0 if slot % 2 == 0 else width - shape_w,
    )


def _repack(base_grid, height, width, odd_slot, rng):
    majorities, oddball = _GENERATOR._class_roles(base_grid)
    majority_shapes = [_shape(obj) for obj in majorities]
    rng.shuffle(majority_shapes)
    odd_shape = _shape(oddball)
    slots = [slot for slot in range(4) if slot != odd_slot]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    shapes = {odd_slot: odd_shape, **dict(zip(slots, majority_shapes))}
    for slot in range(4):
        shape = shapes[slot]
        row0, col0 = _corner_origin(slot, height, width, shape)
        for row, col in shape:
            if grid[row0 + row][col0 + col] != 0:
                raise RuntimeError("corner repack collision")
            grid[row0 + row][col0 + col] = 4
    findings = _GENERATOR.self_check(grid)
    if findings:
        raise RuntimeError("repacked input is outside the canonical grammar: " + "; ".join(findings))
    return grid


def _build_input(seed, pair_index, spec, rotation, attempt):
    height, width, texture, odd_slot = spec
    odd_slot = (odd_slot + rotation) % 4
    mixed_seed = (seed * 1_000_003 + pair_index * 97_409 + attempt * 7_919 + 17) % (2**63)
    base = _GENERATOR.generate(
        mixed_seed,
        pair_index + attempt * 31,
        difficulty="hard",
        grid_h=min(height, 14),
        grid_w=min(width, 16),
        n_majority=3,
        texture=texture,
    )
    return _repack(base, height, width, odd_slot, random.Random(mixed_seed ^ 0x40BFB))


def _farthest_partner_output(grid):
    majorities, oddball = _GENERATOR._class_roles(grid)
    odd_anchor = min(oddball)
    partner = max(
        majorities,
        key=lambda obj: abs(min(obj)[0] - odd_anchor[0]) + abs(min(obj)[1] - odd_anchor[1]),
    )
    output = deepcopy(grid)
    for row, col in partner:
        output[row][col] = 8
    return output


def _labeled_pair(grid, target):
    output = (
        _GENERATOR.rule_mirror(grid)
        if target == "outsider"
        else _farthest_partner_output(grid)
    )
    return {"input": deepcopy(grid), "output": output}


def generate(seed, settings, demos, queries):
    """Generate one episode with shared inputs and private, fixed rule settings."""
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    target = _validate_settings(settings)
    rotation = random.Random(seed ^ 0x40BFB038C65).randrange(4)
    specs = list(_DEMO_SPECS[:demos]) + list(_QUERY_SPECS)
    inputs = []
    seen = set()
    for pair_index, spec in enumerate(specs):
        for attempt in range(64):
            grid = _build_input(seed, pair_index, spec, rotation, attempt)
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                seen.add(key)
                inputs.append(grid)
                break
        else:
            raise RuntimeError("could not construct distinct episode inputs")
    pairs = [_labeled_pair(grid, target) for grid in inputs]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
