"""Proposed task-local endpoint/trace rules; sampling is authoring-only.

Production generator and canonical Racket authority remain unchanged. Outputs
from sample_episode are Python expectations until the retention writer checks
and replaces them with protected-Racket execution results.
"""
from functools import lru_cache
import json
import random

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "33f9169a335e"
MODES = ("endpoint", "trace")
MAX_ATTEMPTS_PER_PAIR = 64

_TRACE_PROGRAM = """(rule!
  (lambda (g)
    (let* ((h (rows g)) (w (cols g)))
      (cellmap g (r c v)
        (if (and (zero? v) (> c 0) (< c (- w 1))
                 (for/or ((top (range 0 r)))
                   (and (!= 0 (at g top (- c 1)))
                        (!= 0 (at g top c))
                        (!= 0 (at g top (+ c 1)))
                        (!= 0 (at g (+ top 1) (- c 1)))
                        (zero? (at g (+ top 1) c))
                        (!= 0 (at g (+ top 1) (+ c 1))))))
            4 v)))))"""


def _mode(mode):
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES!r}")
    return mode


def _integer(value, name, *, lower=None, upper=None):
    if (type(value) is not int or (lower is not None and value < lower)
            or (upper is not None and value > upper)):
        bounds = "" if lower is None else f" in {lower}..{upper}"
        raise ValueError(f"{name} must be an exact integer{bounds}")
    return value


@lru_cache(maxsize=1)
def _generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


@lru_cache(maxsize=1)
def canonical_program():
    """Return the exact selected canonical program, with outer whitespace removed."""
    records = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("task_id") == TASK_ID:
                    records.append(record)
    if len(records) != 1:
        raise ValueError(f"expected one canonical record for {TASK_ID}, got {len(records)}")
    program = records[0].get("program_solution")
    if type(program) is not str or not program.strip():
        raise ValueError(f"canonical program is missing for {TASK_ID}")
    return program.strip()


def rule_source(mode):
    """Materialize the matching Racket rule; endpoint preserves canonical bytes."""
    return canonical_program() if _mode(mode) == "endpoint" else _TRACE_PROGRAM


def python_transform(grid, mode):
    """Authoring mirror on the selected generator's domain; never mutates input."""
    mode = _mode(mode)
    errors = _generator().self_check(grid)
    if errors:
        raise ValueError("outside selected generator domain: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    # Detection reads only the input. No connectivity, color grouping, or
    # equality between the five foreground cells is part of this rule.
    gaps = [(top + 1, col)
            for top in range(height - 1)
            for col in range(1, width - 1)
            if all(grid[top][c] != 0 for c in (col - 1, col, col + 1))
            and grid[top + 1][col - 1] != 0
            and grid[top + 1][col] == 0
            and grid[top + 1][col + 1] != 0]
    result = [list(row) for row in grid]
    for gap_row, col in gaps:
        if mode == "endpoint":
            result[-1][col] = 4
        else:
            for row in range(gap_row, height):
                if grid[row][col] == 0:
                    result[row][col] = 4
    return result


def sample_episode(seed, *, mode="endpoint", input_seed=None,
                   demo_count=2, query_count=4):
    """Sample distinct lawful pairs using the exact selected production source.

    Explicit modes do not depend on seed. With mode=None a local seeded RNG
    selects one mode for the whole episode. Input draws depend only on
    input_seed (default: seed), making mode comparisons input-identical.
    """
    seed = _integer(seed, "seed")
    input_seed = seed if input_seed is None else _integer(input_seed, "input_seed")
    demo_count = _integer(demo_count, "demo_count", lower=1, upper=8)
    query_count = _integer(query_count, "query_count", lower=1, upper=8)
    mode = random.Random(seed).choice(MODES) if mode is None else _mode(mode)
    generator = _generator()
    required = demo_count + query_count
    limit = MAX_ATTEMPTS_PER_PAIR * required
    pairs, seen = [], set()
    last_reason = "no successful draw"
    for attempt in range(limit):
        try:
            candidate = generator.generate(input_seed, attempt)
        except RuntimeError as error:
            last_reason = str(error)
            continue
        errors = generator.self_check(candidate)
        if errors:
            last_reason = "; ".join(errors)
            continue
        key = tuple(tuple(row) for row in candidate)
        if key in seen:
            last_reason = "duplicate input"
            continue
        seen.add(key)
        grid = [list(row) for row in candidate]
        pairs.append({"input": grid, "output": python_transform(grid, mode)})
        if len(pairs) == required:
            return {"task_id": TASK_ID, "status": "proposed", "seed": seed,
                    "input_seed": input_seed, "parameters": {"mode": mode},
                    "demo_count": demo_count, "query_count": query_count,
                    "program": rule_source(mode), "train": pairs[:demo_count],
                    "test": pairs[demo_count:], "attempts": attempt + 1}
    raise RuntimeError(f"could not sample {required} distinct valid inputs in "
                       f"{limit} attempts (accepted {len(pairs)}): {last_reason}")
