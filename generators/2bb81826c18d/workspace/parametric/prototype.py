"""Proposed episode-level periodic rectangle erasure; no production registration.

The exact Racket expression is the output authority.  Only the public
RacketBridge methods are used; no Python output mirror supplies labels.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path


TASK_ID = "2bb81826c18d"
VERSION = "parametric-prototype-1"
SETTINGS = ((2, 0), (2, 1), (3, 0), (3, 1), (3, 2))
CANONICAL = (2, 0)


def validate_setting(period, phase):
    if type(period) is not int or type(phase) is not int or (period, phase) not in SETTINGS:
        raise ValueError("period must be 2 or 3 and phase an integer in range(period)")
    return period, phase


def choose_setting(seed):
    """Choose once per episode, independently of scene drawing and pair count."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer, excluding booleans")
    digest = hashlib.sha256(f"{VERSION}|rule|{seed}".encode()).digest()
    return SETTINGS[int.from_bytes(digest, "big") % len(SETTINGS)]


def racket_program(period=2, phase=0):
    """Return the exact executable Racket lambda for a bounded rule setting.

    A raw backward scan includes the current cell and the border. Subtracting
    two gives a zero-based interior coordinate. The canonical rule subtracts
    one on each axis; the resulting +2 sum is equivalent modulo two.
    """
    period, phase = validate_setting(period, phase)
    return f"""(lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (cellmap g (r c v)
      (if (zero? v)
          0
          (if (or (zero? r) (= r (- h 1))
                  (zero? c) (= c (- w 1))
                  (!= (at g (- r 1) c) v)
                  (!= (at g (+ r 1) c) v)
                  (!= (at g r (- c 1)) v)
                  (!= (at g r (+ c 1)) v))
              v
              (let* ((dr (let loop ((d 1))
                           (if (and (>= (- r d) 0)
                                    (= (at g (- r d) c) v))
                               (loop (+ d 1)) d)))
                     (dc (let loop ((d 1))
                           (if (and (>= (- c d) 0)
                                    (= (at g r (- c d)) v))
                               (loop (+ d 1)) d)))
                     (ir (- dr 2))
                     (ic (- dc 2)))
                (if (= (modulo (+ ir ic) {period}) {phase}) 0 v)))))))"""


def canonical_program(root):
    """Read the selected task's single unambiguous canonical rule text."""
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected one unambiguous canonical program for this task")
    return programs.pop()


def executable_expression(program):
    """Remove only the canonical REPL registration wrapper, when present."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket text")
    expression = program.strip()
    if expression.startswith("(rule!") and expression.endswith(")"):
        expression = expression[len("(rule!"):-1].strip()
    if not expression.startswith("(lambda "):
        raise ValueError("This prototype executes a lambda, optionally wrapped in rule!")
    return expression


def validate_scene(grid):
    """Check the prototype's solid, separated, uniquely colored rectangles."""
    if not isinstance(grid, list) or not 10 <= len(grid) <= 24:
        raise ValueError("scene height must be 10..24")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("scene rows must be nonempty lists")
    width = len(grid[0])
    if not 10 <= width <= 24 or any(len(row) != width for row in grid):
        raise ValueError("scene must be rectangular with width 10..24")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("scene cells must be integer ARC colors 0..9")
    colors = {value for row in grid for value in row}
    if 0 not in colors or not 1 <= len(colors - {0}) <= 4:
        raise ValueError("scene needs background zero and 1..4 rectangle colors")
    rectangles = []
    for color in sorted(colors - {0}):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        if bottom - top < 2 or right - left < 2:
            raise ValueError("rectangles must be at least 3x3")
        if len(cells) != (bottom - top + 1) * (right - left + 1):
            raise ValueError("each color must form one solid rectangle")
        rectangles.append({"top": top, "left": left, "height": bottom - top + 1,
                           "width": right - left + 1, "color": color})
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value:
                continue
            for nr, nc in ((r + 1, c), (r, c + 1)):
                if nr < len(grid) and nc < width and grid[nr][nc] not in (0, value):
                    raise ValueError("rectangles must not touch orthogonally")
    return rectangles


def execute_racket(program, inputs, *, bridge=None):
    """Execute every supplied lawful scene; fail visibly on runtime errors."""
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("inputs must be a nonempty list of scenes")
    for grid in inputs:
        validate_scene(grid)
    expression = executable_expression(program)
    if bridge is None:
        with RacketBridge(timeout=15) as opened:
            return execute_racket(program, inputs, bridge=opened)
    outputs = []
    for grid in inputs:
        bridge.define_grid("parametric_input", grid)
        output = bridge.eval_text(f"({expression} parametric_input)")
        if (not isinstance(output, list) or len(output) != len(grid)
                or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in output)
                or any(type(value) is not int or not 0 <= value <= 9 for row in output for value in row)):
            raise ValueError("Racket did not return an ARC grid with the input shape")
        outputs.append(output)
    return outputs


def draw_scene(seed, index, *, distinguish=False):
    """Construct separated zones; the first demonstration has a 5x5 witness."""
    if type(seed) is not int or type(index) is not int or index < 0:
        raise ValueError("scene seed/index must be integers and index nonnegative")
    digest = hashlib.sha256(f"{VERSION}|scene|{seed}|{index}".encode()).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    height, width, count = rng.randint(14, 24), rng.randint(14, 24), rng.randint(1, 4)
    margin = rng.choice((0, 1))
    rows, cols = (margin, height - margin), (margin, width - margin)

    def split(interval):
        start, stop = interval
        middle = (start + stop) // 2
        return (start, middle), (middle + 1, stop)

    if count == 1:
        zones = [(*rows, *cols)]
    elif count == 2 and rng.choice((False, True)):
        zones = [(*interval, *cols) for interval in split(rows)]
    elif count == 2:
        zones = [(*rows, *interval) for interval in split(cols)]
    else:
        zones = [(*rr, *cc) for rr in split(rows) for cc in split(cols)]
        rng.shuffle(zones)
        zones = zones[:count]
    grid = [[0] * width for _ in range(height)]
    for position, (zone, color) in enumerate(zip(zones, rng.sample(range(1, 10), count))):
        top, bottom, left, right = zone
        minimum = 5 if distinguish and position == 0 else 3
        rect_h = rng.randint(minimum, min(bottom - top, 12))
        rect_w = rng.randint(minimum, min(right - left, 12))
        row = rng.randint(top, bottom - rect_h)
        col = rng.randint(left, right - rect_w)
        for r in range(row, row + rect_h):
            for c in range(col, col + rect_w):
                grid[r][c] = color
    validate_scene(grid)
    return grid


def check_parameter_rivals(episode, *, bridge=None):
    """Execute each alternative setting on demonstrations and queries."""
    chosen = validate_setting(**episode["parameters"])
    if bridge is None:
        with RacketBridge(timeout=15) as opened:
            return check_parameter_rivals(episode, bridge=opened)
    pairs = episode["train"] + episode["test"]
    inputs = [pair["input"] for pair in pairs]
    report = []
    for setting in SETTINGS:
        if setting == chosen:
            continue
        outputs = execute_racket(racket_program(*setting), inputs, bridge=bridge)
        demo_mismatches = [i for i, pair in enumerate(episode["train"]) if pair["output"] != outputs[i]]
        query_mismatches = [i for i, pair in enumerate(episode["test"])
                            if pair["output"] != outputs[len(episode["train"]) + i]]
        status = ("refuted_by_demonstration" if demo_mismatches else
                  "ambiguous_query" if query_mismatches else "survived_all")
        report.append({"parameters": {"period": setting[0], "phase": setting[1]},
                       "status": status,
                       "first_refuting_demo": demo_mismatches[0] if demo_mismatches else None,
                       "differing_queries": query_mismatches})
    return report


def generate_episode(seed, *, setting=None, n_train=3, n_test=1, bridge=None):
    """A fixed hidden rule, at least one distinguishing demo, Racket labels."""
    sampled = choose_setting(seed)
    chosen = sampled if setting is None else validate_setting(*setting)
    for name, value in (("n_train", n_train), ("n_test", n_test)):
        if type(value) is not int or not 1 <= value <= 8:
            raise ValueError(f"{name} must be an integer in 1..8")
    if bridge is None:
        with RacketBridge(timeout=15) as opened:
            return generate_episode(seed, setting=setting, n_train=n_train, n_test=n_test, bridge=opened)
    program = racket_program(*chosen)
    inputs = []
    seen = set()
    accepted_indices = []
    for index in range(64):
        grid = draw_scene(seed, index, distinguish=not inputs)
        key = json.dumps(grid, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            inputs.append(grid)
            accepted_indices.append(index)
        if len(inputs) == n_train + n_test:
            break
    else:
        raise RuntimeError("bounded sampler failed to produce distinct episode inputs")
    outputs = execute_racket(program, inputs, bridge=bridge)
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs)]
    episode = {"schema": "rectangle-parametric-episode-v1", "status": "prototype",
               "task_id": TASK_ID, "seed": seed,
               "selection": "seeded" if setting is None else "explicit_for_authoring",
               "parameters": {"period": chosen[0], "phase": chosen[1]},
               "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
               "sampling": {"accepted_indices": accepted_indices, "attempts": index + 1},
               "train": pairs[:n_train], "test": pairs[n_train:]}
    rivals = check_parameter_rivals(episode, bridge=bridge)
    if any(row["status"] != "refuted_by_demonstration" for row in rivals):
        raise RuntimeError("constructed demonstrations did not distinguish every declared setting")
    episode["parameter_rivals"] = rivals
    return episode


def public_challenge(episode):
    """Only visible grids: hidden seed, parameters, reference and labels omitted."""
    return {"train": [{"input": copy.deepcopy(pair["input"]),
                        "output": copy.deepcopy(pair["output"])} for pair in episode["train"]],
            "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]]}
