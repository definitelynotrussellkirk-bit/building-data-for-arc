"""Native parent-choice adapter with task-local, depth-complete teaching inputs.

Only the input grammar is extended: rectangular 3..30 by 5..30 boards still
contain 2/5 seeds in row zero and background 7 everywhere below. The canonical
production generator and both reviewed Racket materializations stay unchanged.
The first demonstration reaches the maximum depth possible at width 30 and
includes the next, extinct row. A second demonstration exposes an interior
support hole that a bounding-endpoint shortcut would miss.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[4]
_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py").resolve()
_PROTOTYPE_NAME = "_parent_choice_prototype_" + hashlib.sha256(
    str(_PROTOTYPE_PATH).encode()
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_PROTOTYPE_NAME, _PROTOTYPE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("Cannot load the adjacent parent-choice prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_PROTOTYPE_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"different_parent"}:
        raise ValueError("settings must name exactly different_parent")
    value = settings["different_parent"]
    if type(value) is not str or value not in ("right", "left"):
        raise ValueError("different_parent must be right or left")
    return value


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain integer in {low}..{high}")
    return value


def program(settings):
    """Return the exact reviewed Racket materialization for this setting."""
    return _PROTOTYPE.materialize_rule(_setting(settings), root=ROOT)


def _rng(seed, split, index):
    # Neither parameter settings nor requested counts influence these streams.
    return random.Random(f"f59691ac00f3:native-v1:{seed}:{split}:{index}")


def _mixed_motif(rng):
    # Adjacent values along one parity provide 22, 25, 55, and 52 witnesses.
    motif = [2, 2, 5, 5, 2]
    if rng.randrange(2):
        motif = [7 - color for color in motif]
    if rng.randrange(2):
        motif.reverse()
    return motif


def _dense_top(width, rng):
    top = [rng.choice((2, 5)) for _ in range(width)]
    for col, color in zip(range(0, 9, 2), _mixed_motif(rng), strict=True):
        top[col] = color
    return top


def _gapped_top(width, rng):
    top = [7] * width
    for col in (0, 4, 6, 8):
        top[col] = rng.choice((2, 5))
    start = width - 9
    for col in range(start, width):
        top[col] = rng.choice((2, 5))
    for col, color in zip(range(start, width, 2), _mixed_motif(rng), strict=True):
        top[col] = color
    # In particular c0/c4 are present while c2 is absent: row2,c2 must stay 7.
    return top


def _single_parity_top(width, rng):
    parity = rng.randrange(2)
    top = [7] * width
    for col in range(parity, width, 2):
        top[col] = rng.choice((2, 5))
    for col, color in zip(range(parity, parity + 9, 2), _mixed_motif(rng), strict=True):
        top[col] = color
    return top


def _grid(height, top):
    return [list(top), *[[7] * len(top) for _ in range(height - 1)]]


def _demo(seed, index):
    rng = _rng(seed, "train", index)
    if index == 0:
        return _grid(16, _dense_top(30, rng))
    if index == 1:
        return _grid(12, _gapped_top(23, rng))
    if index == 2:
        return _grid(9, [rng.choice((2, 5))] * 17)
    if index == 3:
        return _grid(8, _single_parity_top(21, rng))
    if index == 4:
        return _grid(11, _gapped_top(26, rng))
    return _grid(13, _gapped_top(29, rng))


def _query(seed, index):
    rng = _rng(seed, "test", index)
    if index == 0:
        color = rng.choice((2, 5))
        return _grid(3, [color, 7, 7 - color, 7, color])
    if index == 1:
        return _grid(11, _gapped_top(19, rng))
    if index == 2:
        return _grid(30, _dense_top(30, rng))
    if seed % 3 == 0:
        top = _gapped_top(30, rng)
    elif seed % 3 == 1:
        top = [rng.choice((2, 5))] * 30
    else:
        top = _single_parity_top(30, rng)
    return _grid(30, top)


def generate(seed, settings, demos, queries):
    """Produce independent requested counts with labels derived from Racket.

    Sampling uses fixed profile slots, separate train/query RNG streams, and
    no setting-dependent branches. Query prefixes stay fixed when either
    requested count changes. Profile dimensions and the two large queries'
    distinct supports/palettes ensure all inputs in an episode are distinct.
    """
    _setting(settings)
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    source = program(settings)
    inputs = [_demo(seed, index) for index in range(demos)] + [
        _query(seed, index) for index in range(queries)
    ]
    outputs = _PROTOTYPE.execute_rule_many(source, inputs)
    pairs = [
        {"input": grid, "output": output}
        for grid, output in zip(inputs, outputs, strict=True)
    ]
    return {"train": pairs[:demos], "test": pairs[demos:], "program_solution": source}
