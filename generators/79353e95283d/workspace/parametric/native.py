"""Native, Racket-labelled Boolean panels and overlap-component extension.

The production generator and its authority are unchanged.  The legacy Boolean
prototype supplies OR/XOR programs and the Racket executor; this module supplies
the native contract, constructive lessons, and a genuinely nonlocal fourth rule.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


HOME = Path(__file__).resolve().parent
OPERATIONS = ("and", "or", "xor", "overlap_components")


def _load_legacy():
    path = HOME / "prototype.py"
    name = "_panels_legacy_" + hashlib.sha256(str(path).encode()).hexdigest()
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


COMPONENT_PROGRAM = """(rule! (lambda (g)
  (let* ((right (build-grid (rows g) 3 (r c) (at g r (+ c 4))))
         (seeds (for*/list ((r (in-range (rows g))) (c (in-range 3))
                  #:when (and (= 1 (at g r c)) (= 1 (at right r c))))
                  (list r c)))
         (selected (filter
                     (lambda (obj)
                       (ormap (lambda (cell) (member cell seeds)) (obj-cells obj)))
                     (objects right 0)))
         (reached (apply append (map obj-cells selected))))
    (build-grid (rows g) 3 (r c)
      (if (member (list r c) reached) 2 0)))))
"""


def _operation(settings):
    if (type(settings) is not dict or set(settings) != {"operation"}
            or type(settings["operation"]) is not str
            or settings["operation"] not in OPERATIONS):
        raise ValueError("settings must contain exactly one declared operation")
    return settings["operation"]


def program(settings):
    """Return exact native Racket text, including the unmodified AND authority."""
    operation = _operation(settings)
    if operation == "and":
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    if operation == "overlap_components":
        return COMPONENT_PROGRAM
    legacy = _load_legacy()
    return "(rule! " + legacy.emit_program(legacy.Parameters(operation)).strip() + ")"


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _rng(seed, stream, index):
    key = f"79353e95283d:native-input-v1:{seed}:{stream}:{index}"
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _assemble(left, right, separator, rng):
    # Reflect *inside* each panel; mirroring all seven columns would swap roles.
    if rng.randrange(2):
        left, right = [row[::-1] for row in left], [row[::-1] for row in right]
    if rng.randrange(2):
        left, right = left[::-1], right[::-1]
    return [a + [separator] + b for a, b in zip(left, right)]


def _teaching_motif(seed):
    # Two seeded components, one unseeded diagonal neighbor, left-only marks,
    # a bent two-hop path, and all four aligned Boolean states in only 3x7.
    left = [[1, 0, 1], [1, 0, 0], [0, 0, 1]]
    right = [[1, 1, 0], [0, 1, 0], [1, 0, 1]]
    return _assemble(left, right, 5, _rng(seed, "teaching", 0))


def _long_grid(seed, stream, index, height, separator=None):
    rng = _rng(seed, stream, index)
    left = [[0, 0, 0] for _ in range(height)]
    right = [[1, int(r % 4 == 0), int(r % 4 in (1, 2))]
             for r in range(height)]
    # An endpoint seed and a midpoint seed select the same long component.
    # This refutes the previously surviving "exactly one overlap" shortcut.
    # Far-column fragments remain unseeded; center-column left-only marks are
    # distractors. Content spans the full height, with no padded inactive rows.
    start = 0 if rng.randrange(2) else height - 1
    left[start][0] = 1
    # The midpoint remains below row two under either vertical orientation,
    # so even a two-demo AND lesson refutes a three-row output cap.
    left[height // 2][0] = 1
    for r in range(height):
        if not right[r][1]:
            left[r][1] = int(rng.random() < 0.45)
    if separator is None:
        separator = rng.choice([2, 3, 4, 6, 7, 8, 9])
    return _assemble(left, right, separator, rng)


def _random_grid(seed, stream, index, height, attempt=0):
    rng = _rng(seed, stream, index * 64 + attempt)
    # Density is a proposal control, independent of the hidden operation.
    left_density = rng.choice((0.2, 0.45, 0.75))
    right_density = rng.choice((0.25, 0.55, 0.85))
    left = [[int(rng.random() < left_density) for _ in range(3)]
            for _ in range(height)]
    right = [[int(rng.random() < right_density) for _ in range(3)]
             for _ in range(height)]
    return _assemble(left, right, rng.randrange(2, 10), rng)


def sample_inputs(seed, demos=3, queries=4):
    """Independent deterministic streams, fixed teaching prefix, no labels.

    The native grammar is 1..30 by 7, with uniform separator 2..9 and binary
    panels. Every requested input is distinct. All settings share these bytes.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    height = 8 + _rng(seed, "teaching", 1).randrange(5)
    train = [_teaching_motif(seed), _long_grid(seed, "teaching", 1, height)]
    seen = {tuple(map(tuple, grid)) for grid in train}

    def append_fresh(target, stream, index, height):
        for attempt in range(64):
            grid = _random_grid(seed, stream, index, height, attempt)
            key = tuple(map(tuple, grid))
            if key not in seen:
                seen.add(key)
                target.append(grid)
                return
        raise ValueError("could not construct a novel input in 64 attempts")

    # Extra demos have sizes disjoint from every query size; requesting more
    # demonstrations cannot perturb a query's novelty decision or RNG stream.
    for index, height in enumerate((3, 5, 7, 9)[:demos - 2], start=2):
        append_fresh(train, "extra-demo", index, height)
    test = []
    for index, height in enumerate((1, 14, 18, 30)[:queries]):
        if height == 30:
            grid = _long_grid(seed, "query-stress", index, height)
            key = tuple(map(tuple, grid))
            if key in seen:
                raise ValueError("stress query unexpectedly duplicates another input")
            seen.add(key)
            test.append(grid)
        else:
            append_fresh(test, "query", index, height)
    return train, test


def generate(seed, settings, demos=3, queries=4):
    """Generate exact requested pairs; labels are computed by protected Racket."""
    source = program(settings)
    train, test = sample_inputs(seed, demos, queries)
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("native labels require the protected Racket backend")
        outputs = _load_legacy().execute_program(
            wrap_rule(source), train + test, bridge=bridge)
    if not isinstance(outputs, list) or len(outputs) != demos + queries:
        raise ValueError("Racket did not return the requested label count")
    pairs = [{"input": grid, "output": output}
             for grid, output in zip(train + test, outputs)]
    return {"train": pairs[:demos], "test": pairs[demos:], "program_solution": source}
