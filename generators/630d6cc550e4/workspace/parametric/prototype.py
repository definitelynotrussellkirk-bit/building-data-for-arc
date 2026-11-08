"""Native ring permutations with per-object color-diversity decisions.

Canonical corners and midpoints move in opposite directions. All emitted labels
are Python claims until independently executed by the protected Racket worker.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import random

TASK_ID = "630d6cc550e4"
MODES = ("canonical", "inverse", "odd_canonical", "even_canonical")
COLORS = (0, 1, 2, 3, 4, 5, 6, 8, 9)
# Clockwise border coordinates; each permutation maps destination to source.
BORDER = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0))
FORWARD = (2, 7, 4, 1, 6, 3, 0, 5)
INVERSE = tuple(FORWARD.index(index) for index in range(8))
IDENTITY = tuple(range(8))
CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g))\n                (blocks (filter (lambda (p) p)\n                                (for*/list ((r (range 0 (- h 2))) (c (range 0 (- w 2))))\n                                  (and\n                                    (and\n                                      (!= (at g r c) 7)\n                                      (= (at g (+ r 1) (+ c 1)) 7)\n                                      (!= (at g r (+ c 1)) 7)\n                                      (!= (at g (+ r 1) c) 7))\n                                    (list r c)))))\n                (src (lambda (dr dc)\n                       (cond\n                         ((and (zero? dr) (zero? dc)) (list 0 2))\n                         ((and (zero? dr) (= dc 1)) (list 1 0))\n                         ((and (zero? dr) (= dc 2)) (list 2 2))\n                         ((and (= dr 1) (zero? dc)) (list 2 1))\n                         ((and (= dr 1) (= dc 2)) (list 0 1))\n                         ((and (= dr 2) (zero? dc)) (list 0 0))\n                         ((and (= dr 2) (= dc 1)) (list 1 2))\n                         ((and (= dr 2) (= dc 2)) (list 2 0))\n                         (else (list dr dc))))))\n           (reduce (lambda (acc blk)\n                     (let* ((r0 (first blk))\n                            (c0 (second blk)))\n                       (reduce (lambda (g1 dr)\n                                 (reduce (lambda (g2 dc)\n                                           (if (and (= dr 1) (= dc 1))\n                                               g2\n                                               (let* ((s (src dr dc)))\n                                                 (set-cell g2\n                                                           (+ r0 dr)\n                                                           (+ c0 dc)\n                                                           (at g\n                                                               (+ r0 (first s))\n                                                               (+ c0 (second s)))))))\n                                         g1\n                                         (list 0 1 2)))\n                               acc\n                               (list 0 1 2))))\n                   g\n                   blocks))))'

FIXED_RIVALS = {
    "identity": IDENTITY,
    "whole_cw": tuple((i - 2) % 8 for i in range(8)),
    "whole_ccw": tuple((i + 2) % 8 for i in range(8)),
    "half_turn": tuple((i + 4) % 8 for i in range(8)),
    "perimeter_cw": tuple((i - 1) % 8 for i in range(8)),
    "perimeter_ccw": tuple((i + 1) % 8 for i in range(8)),
    "perimeter_cw3": tuple((i - 3) % 8 for i in range(8)),
    "perimeter_ccw3": tuple((i + 3) % 8 for i in range(8)),
    "corners_only": tuple(FORWARD[i] if i % 2 == 0 else i for i in range(8)),
    "midpoints_only": tuple(FORWARD[i] if i % 2 else i for i in range(8)),
}
COUNT_EXPRESSIONS = {
    "nonzero_colors": "(length (remove-duplicates (filter (lambda (v) (!= v 0)) values)))",
    "corner_colors": "(length (remove-duplicates (map (lambda (i) (list-ref values i)) (list 0 2 4 6))))",
    "midpoint_colors": "(length (remove-duplicates (map (lambda (i) (list-ref values i)) (list 1 3 5 7))))",
    "nonzero_cells": "(length (filter (lambda (v) (!= v 0)) values))",
    "color_sum": "(apply + values)",
    "top_left": "(first values)",
    "row": "r0",
    "column": "c0",
    "scan_index": "(index-of blocks blk)",
    "zero_present": "(if (member 0 values) 1 0)",
    "global_colors": "(length (remove-duplicates all-colors))",
    "block_count": "(length blocks)",
    "first_colors": "(length (remove-duplicates (colors-at (first blocks))))",
    "global_sum": "(apply + all-colors)",
}
EXTRA_NAMES = tuple(FIXED_RIVALS) + ("fixed_lattice", "first_only") + tuple(
    f"{name}_{parity}" for name in COUNT_EXPRESSIONS for parity in ("odd", "even")
)
CANDIDATE_NAMES = tuple(f"setting:{mode}" for mode in MODES) + EXTRA_NAMES


def validate_settings(settings):
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dictionary")
    if set(settings) - {"ring_motion"}:
        raise ValueError("unknown setting; only ring_motion is supported")
    mode = settings.get("ring_motion", "canonical")
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"ring_motion must be one of {MODES}")
    return {"ring_motion": mode}


def _integer(value, low, high, label):
    if type(value) is not int:
        raise TypeError(f"{label} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{label} must be in {low}..{high}")


def _validate_grid(grid):
    if not isinstance(grid, list) or not 3 <= len(grid) <= 30:
        raise ValueError("grid must have 3..30 rows")
    if not isinstance(grid[0], list) or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 3..30 columns")
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact integer ARC colors")


def detect_rings(grid):
    """Preserve the canonical detector; sampler grammar is checked separately."""
    return [(r, c) for r in range(len(grid) - 2) for c in range(len(grid[0]) - 2)
            if grid[r][c] != 7 and grid[r + 1][c + 1] == 7
            and grid[r][c + 1] != 7 and grid[r + 1][c] != 7]


def _values(grid, position):
    r, c = position
    return [grid[r + dr][c + dc] for dr, dc in BORDER]


def validate_scene(grid, intended=None):
    """Require complete, separated rings with no stray foreground cells."""
    _validate_grid(grid)
    blocks = detect_rings(grid)
    if not blocks or (intended is not None and set(blocks) != set(intended)):
        raise ValueError("detected rings differ from the intended nonempty scene")
    covered = set()
    for index, (r, c) in enumerate(blocks):
        if any(v == 7 for v in _values(grid, (r, c))):
            raise ValueError("incomplete ring")
        for rr, cc in blocks[index + 1:]:
            if not (r + 3 < rr or rr + 3 < r or c + 3 < cc or cc + 3 < c):
                raise ValueError("rings need a full background separator")
        covered.update((r + dr, c + dc) for dr, dc in BORDER)
    foreground = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 7}
    if covered != foreground:
        raise ValueError("stray foreground outside rings")
    return blocks


def _measure(name, values, position, index, all_values):
    if name == "nonzero_colors": return len(set(values) - {0})
    if name == "corner_colors": return len(set(values[::2]))
    if name == "midpoint_colors": return len(set(values[1::2]))
    if name == "nonzero_cells": return sum(v != 0 for v in values)
    if name == "color_sum": return sum(values)
    if name == "top_left": return values[0]
    if name == "row": return position[0]
    if name == "column": return position[1]
    if name == "scan_index": return index
    if name == "zero_present": return int(0 in values)
    if name == "global_colors": return len({v for vs in all_values for v in vs})
    if name == "block_count": return len(all_values)
    if name == "first_colors": return len(set(all_values[0]))
    if name == "global_sum": return sum(sum(vs) for vs in all_values)
    raise ValueError(name)


def _apply_kind(grid, kind):
    output = [row[:] for row in grid]
    blocks = detect_rings(grid)
    all_values = [_values(grid, position) for position in blocks]
    for index, (position, values) in enumerate(zip(blocks, all_values)):
        r, c = position
        if kind.startswith("setting:"):
            mode = kind.split(":", 1)[1]
            forward = (mode == "canonical" or
                       mode == "odd_canonical" and len(set(values)) % 2 == 1 or
                       mode == "even_canonical" and len(set(values)) % 2 == 0)
            mapping = FORWARD if forward else INVERSE
        elif kind in FIXED_RIVALS:
            mapping = FIXED_RIVALS[kind]
        elif kind == "fixed_lattice":
            mapping = FORWARD if r % 4 == 1 and c in (1, len(grid[0]) - 4) else IDENTITY
        elif kind == "first_only":
            mapping = FORWARD if index == 0 else IDENTITY
        else:
            name, parity = kind.rsplit("_", 1)
            count = _measure(name, values, position, index, all_values)
            mapping = FORWARD if count % 2 == (1 if parity == "odd" else 0) else INVERSE
        for (dr, dc), source in zip(BORDER, mapping):
            output[r + dr][c + dc] = values[source]
    return output


def apply_rule(grid, settings):
    mode = validate_settings(settings)["ring_motion"]
    _validate_grid(grid)
    return _apply_kind(grid, f"setting:{mode}")


def rival_outputs(grid, settings=None):
    if settings is not None:
        validate_settings(settings)
    _validate_grid(grid)
    return {kind: _apply_kind(grid, kind) for kind in CANDIDATE_NAMES}


def _racket_list(values):
    return "(list " + " ".join(str(v) for v in values) + ")"


@lru_cache(maxsize=None)
def _program(kind):
    if kind == "setting:canonical":
        return CANONICAL_PROGRAM
    forward, backward, identity = map(_racket_list, (FORWARD, INVERSE, IDENTITY))
    if kind == "setting:inverse":
        indices = backward
    elif kind in ("setting:odd_canonical", "setting:even_canonical"):
        parity = 1 if kind == "setting:odd_canonical" else 0
        indices = f"(if (= (modulo (length (remove-duplicates values)) 2) {parity}) {forward} {backward})"
    elif kind in FIXED_RIVALS:
        indices = _racket_list(FIXED_RIVALS[kind])
    elif kind == "fixed_lattice":
        indices = f"(if (and (= (modulo r0 4) 1) (or (= c0 1) (= c0 (- w 4)))) {forward} {identity})"
    elif kind == "first_only":
        indices = f"(if (equal? blk (first blocks)) {forward} {identity})"
    else:
        name, parity = kind.rsplit("_", 1)
        count = COUNT_EXPRESSIONS[name]
        indices = f"(if (= (modulo {count} 2) {1 if parity == 'odd' else 0}) {forward} {backward})"
    offsets = "(list " + " ".join(_racket_list(p) for p in BORDER) + ")"
    return f"""(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (offsets {offsets})
             (blocks (filter (lambda (p) p)
               (for*/list ((r (range 0 (- h 2))) (c (range 0 (- w 2))))
                 (and (!= (at g r c) 7) (= (at g (+ r 1) (+ c 1)) 7)
                      (!= (at g r (+ c 1)) 7) (!= (at g (+ r 1) c) 7)
                      (list r c)))))
             (colors-at (lambda (p) (map (lambda (d)
               (at g (+ (first p) (first d)) (+ (second p) (second d)))) offsets)))
             (all-colors (apply append (map colors-at blocks))))
        (reduce (lambda (acc blk)
          (let* ((r0 (first blk)) (c0 (second blk))
                 (values (colors-at blk)) (indices {indices}))
            (reduce (lambda (out i)
              (let ((p (list-ref offsets i)))
                (set-cell out (+ r0 (first p)) (+ c0 (second p))
                  (list-ref values (list-ref indices i))))) acc (range 0 8))))
          g blocks))))"""


def program(settings):
    return _program("setting:" + validate_settings(settings)["ring_motion"])


def candidate_programs():
    return {name: _program(name) for name in CANDIDATE_NAMES}


def teaching_certificate(episode, settings):
    mode = validate_settings(settings)["ring_motion"]
    predictions = [rival_outputs(pair["input"]) for pair in episode["train"]]
    survivors = [name for name in CANDIDATE_NAMES if all(
        row[name] == pair["output"] for row, pair in zip(predictions, episode["train"]))]
    declared = [name.split(":", 1)[1] for name in survivors if name.startswith("setting:")]
    extras = [name for name in survivors if not name.startswith("setting:")]
    agreements = [{"query_index": index, "all_survivors_agree": all(
        _apply_kind(pair["input"], name) == pair["output"] for name in survivors)}
        for index, pair in enumerate(episode["test"])]
    return {"fit_source": "train_only", "declared_survivors": declared,
            "extra_survivors": extras, "query_agreement": agreements,
            "passed": declared == [mode] and all(row["all_survivors_agree"] for row in agreements),
            "limitations": "Finite listed rivals only; no universal rule identifiability claim."}


def _rng(seed, *parts):
    raw = json.dumps([TASK_ID, seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _ring_values(rng, count, pool, include_zero):
    choices = [v for v in pool if v != 0]
    palette = ([0] + rng.sample(choices, count - 1) if include_zero
               else rng.sample(choices, count))
    rng.shuffle(palette)
    values = palette + [rng.choice(palette) for _ in range(8 - count)]
    if count == 1:
        return values
    for _ in range(16):
        rng.shuffle(values)
        if [values[i] for i in FORWARD] != [values[i] for i in INVERSE]:
            return values
    values = palette + [palette[0]] * (8 - count)
    assert [values[i] for i in FORWARD] != [values[i] for i in INVERSE]
    return values


def _scene(height, width, positions, rings):
    grid = [[7] * width for _ in range(height)]
    for (r, c), values in zip(positions, rings):
        for (dr, dc), value in zip(BORDER, values):
            grid[r + dr][c + dc] = value
    validate_scene(grid, positions)
    return grid


@lru_cache(maxsize=32)
def _teaching_core(seed):
    positions = (((0, 0), (0, 8), (4, 3), (4, 12)),
                 ((1, 1), (1, 9), (5, 0), (5, 6), (8, 12)))
    counts = ((3, 4, 6, 5), (2, 7, 5, 8, 4))
    zeros = ((True, True, False, False), (True, False, True, False, False))
    last_survivors = {}
    for attempt in range(64):
        grids = []
        for index, (height, width) in enumerate(((7, 15), (11, 15))):
            rng = _rng(seed, "teaching", index, attempt)
            pool = COLORS[:-1] if index == 0 else COLORS
            rings = [_ring_values(rng, k, pool, zero)
                     for k, zero in zip(counts[index], zeros[index])]
            grids.append(_scene(height, width, positions[index], rings))
        # Deliberately vary global palette parity, object-count parity and the
        # first ring's parity, so they cannot imitate a constant local rule.
        if len({v for row in grids[0] for v in row if v != 7}) != 8:
            continue
        outputs = [rival_outputs(grid) for grid in grids]
        last_survivors = {mode: [name for name in CANDIDATE_NAMES if all(
            row[name] == row[f"setting:{mode}"] for row in outputs)] for mode in MODES}
        if all(last_survivors[mode] == [f"setting:{mode}"] for mode in MODES):
            return grids, attempt + 1
    raise RuntimeError(f"teaching core exhausted 64 bounded attempts: {last_survivors}")


def _slots(length, rng):
    count = (length + 1) // 4
    gaps = [1] * (count - 1)
    for _ in range(length - (4 * count - 1)):
        gaps[rng.randrange(len(gaps))] += 1
    starts = [0]
    for gap in gaps:
        starts.append(starts[-1] + 3 + gap)
    assert starts[-1] == length - 3
    return starts


def _random_scene(seed, stream, index, height, width):
    rng = _rng(seed, stream, index)
    rows, cols = _slots(height, rng), _slots(width, rng)
    possible = [(r, c) for r in rows for c in cols]
    positions = [(rows[0], cols[0]), (rows[0], cols[-1]),
                 (rows[-1], cols[0]), (rows[-1], cols[-1])]
    rest = [p for p in possible if p not in positions]
    rng.shuffle(rest)
    count = rng.randint(max(4, len(possible) * 7 // 10), len(possible))
    positions += rest[:count - 4]
    counts = [3, 4] + [1 + (i + rng.randrange(8)) % 8 for i in range(count - 2)]
    rings = [_ring_values(rng, k, COLORS, i % 3 == 0)
             for i, k in enumerate(counts)]
    return _scene(height, width, positions, rings)


def generate(seed, settings, demos=3, queries=4):
    settings = validate_settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    core, attempts = _teaching_core(seed)
    train_inputs = deepcopy(core)
    for index, (height, width) in enumerate(((11, 13), (13, 15), (17, 19), (21, 23))):
        if len(train_inputs) < demos:
            train_inputs.append(_random_scene(seed, "demo", index, height, width))
    test_inputs = [_random_scene(seed, "query", i, h, w) for i, (h, w) in enumerate(
        ((7, 9), (13, 17), (23, 27), (30, 30))[:queries])]
    keys = [json.dumps(g, separators=(",", ":")) for g in train_inputs + test_inputs]
    if len(set(keys)) != len(keys):
        raise AssertionError("duplicate or non-novel input")
    result = {"train": [{"input": grid, "output": apply_rule(grid, settings)} for grid in train_inputs],
              "test": [{"input": grid, "output": apply_rule(grid, settings)} for grid in test_inputs],
              "program_solution": program(settings), "settings": settings,
              "seed": seed, "private_metadata": {"teaching_attempts": attempts}}
    certificate = teaching_certificate(result, settings)
    if not certificate["passed"] or certificate["extra_survivors"]:
        raise AssertionError("constructed lesson failed its finite teaching contract")
    result["teaching"] = certificate
    return result


def public_challenge_bytes(episode):
    """First user turn: no settings, answers, future inputs or query-count hint."""
    from reviewer_support import public_challenge_bytes as native_bytes
    value = {"train": [{"input": pair["input"], "output": pair["output"]}
                       for pair in episode["train"]],
             "test": [{"input": episode["test"][0]["input"]}]}
    return native_bytes(value)
