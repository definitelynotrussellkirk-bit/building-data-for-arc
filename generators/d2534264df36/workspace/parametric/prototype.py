"""Proposed complete-rings -> ray-hit -> zero-cross parameter family.

The canonical setting returns the exact source rule.  The two composed settings
first execute that rule, then read the nearest or farthest completed side on the
north center ray and use its position/color to fill only blank cells of the
interior orthogonal cross.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

TASK_ID = "d2534264df36"
MODES = ("complete_only", "nearest_hit", "farthest_hit")
DEFAULT_MODE = "complete_only"
CANONICAL_PROGRAM_SHA256 = "e9c97d0b9abccc1540e52b91d79dd42a2af3fa43b2684d167918aa5ce10d534d"
CANONICAL_RULE_HASH = "205ec75568f5"
SIZES = (19, 23, 27, 30)
ARM_MASKS = (
    (True, False, True),
    (True, True, False),
    (False, True, True),
    (True, True, True),
)
ORIENTATIONS = (
    ("top", "left"),
    ("top", "right"),
    ("bottom", "right"),
    ("bottom", "left"),
)

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]


def _load_local(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = _load_local("d2534264df36_cross_stop_oracle", HERE / "oracle.py")


def _integer(name: str, value, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def _rng(seed: int, sample_index: int, namespace: str) -> random.Random:
    material = f"d253-cross-stop-v1:{seed}:{sample_index}:{namespace}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


@lru_cache(maxsize=2048)
def _case(seed: int, sample_index: int) -> tuple[tuple[tuple[int, ...], ...], dict]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("sample_index", sample_index, 0, 10**6)
    schedule = _rng(seed, sample_index, "schedule")
    if sample_index < 2:
        # The minimum teaching pair is cue-matched by size and exposes every
        # witness morphology, so size or paired-only shortcuts cannot stand in
        # for the rule.
        size = 19
        arm_mask = ARM_MASKS[-1]
    else:
        size = (23, 27, 30, 19)[(sample_index - 2) % 4]
        arm_mask = ARM_MASKS[(sample_index - 2) % len(ARM_MASKS)]
    orientation = ORIENTATIONS[(schedule.randrange(len(ORIENTATIONS)) + sample_index) % len(ORIENTATIONS)]
    armed = [index for index, value in enumerate(arm_mask) if value]
    witness_modes = [None, None, None]
    for order, ring_index in enumerate(armed):
        witness_modes[ring_index] = ("single_row", "single_col", "pair")[order % 3]
    colors = _rng(seed, sample_index, "colors").sample(range(1, 10), 3 + len(armed))
    corner_colors = colors[:3]
    side_iter = iter(colors[3:])
    side_colors = [next(side_iter) if value else None for value in arm_mask]
    grid = [[0 for _ in range(size)] for _ in range(size)]
    vertical, horizontal = orientation
    for index, corner_color in enumerate(corner_colors):
        ring = 1 + 2 * index
        row = ring if vertical == "top" else size - 1 - ring
        col = ring if horizontal == "left" else size - 1 - ring
        grid[row][col] = corner_color
        mode = witness_modes[index]
        if mode is None:
            continue
        toward_row = row + (2 if vertical == "top" else -2)
        toward_col = col + (2 if horizontal == "left" else -2)
        color = side_colors[index]
        if mode in ("single_col", "pair"):
            grid[toward_row][col] = color
        if mode in ("single_row", "pair"):
            grid[row][toward_col] = color
    hub = size // 2
    if any(grid[row][hub] for row in range(size)) or any(grid[hub][col] for col in range(size)):
        raise AssertionError("raw source unexpectedly touches the hub axes")
    metadata = {
        "size": size,
        "orientation": list(orientation),
        "arm_mask": list(arm_mask),
        "witness_modes": witness_modes,
        "corner_colors": corner_colors,
        "side_colors": side_colors,
        "hub": hub,
    }
    frozen = tuple(tuple(row) for row in grid)
    return frozen, metadata


def build_input(seed: int, sample_index: int) -> list[list[int]]:
    frozen, _metadata = _case(seed, sample_index)
    return [list(row) for row in frozen]


def input_metadata(seed: int, sample_index: int) -> dict:
    _frozen, metadata = _case(seed, sample_index)
    return deepcopy(metadata)


def _settings(settings) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an object")
    if set(settings) != {"cross_stop"}:
        raise ValueError("settings must contain exactly cross_stop")
    mode = settings["cross_stop"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"cross_stop must be one of {MODES}")
    return mode


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs: set[str] = set()
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("exactly one canonical program is required")
    source = programs.pop()
    if hashlib.sha256(source.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical program bytes changed")
    normalized = " ".join(source.split())
    if hashlib.sha256(normalized.encode()).hexdigest()[:12] != CANONICAL_RULE_HASH:
        raise ValueError("canonical rule hash changed")
    return source


def _unwrap_rule(source: str) -> str:
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("canonical rule is not a simple rule! wrapper")
    return source[len(prefix):-1]


def _composed_program(mode: str, base_expression: str) -> str:
    if mode not in ("nearest_hit", "farthest_hit"):
        raise ValueError("composition requires nearest_hit or farthest_hit")
    selector = (
        "(nth hits (- (length hits) 1))"
        if mode == "nearest_hit"
        else "(nth hits 0)"
    )
    return f"""(rule! (lambda (g)
  (let* ((base {base_expression})
         (h (rows base))
         (w (cols base))
         (hub (quotient h 2))
         (hits (filter (lambda (r) (> (at base r hub) 0))
                       (range 0 hub))))
    (if (empty? hits)
        base
        (let* ((hit {selector})
               (color (at base hit hub))
               (far (- (- h 1) hit))
               (cross-cells
                 (apply append
                        (list
                          (map (lambda (r) (list r hub))
                               (range (+ hit 1) far))
                          (map (lambda (c) (list hub c))
                               (range (+ hit 1) far))))))
          (reduce (lambda (out rc)
                    (let ((r (nth rc 0))
                          (c (nth rc 1)))
                      (if (= (at out r c) 0)
                          (set-cell out r c color)
                          out)))
                  base
                  cross-cells))))))"""


@lru_cache(maxsize=3)
def _derived_program(mode: str) -> str:
    if mode not in MODES:
        raise ValueError(mode)
    if mode == DEFAULT_MODE:
        return canonical_program()
    canonical_callable = _unwrap_rule(canonical_program())
    return _composed_program(mode, f"({canonical_callable} g)")


@lru_cache(maxsize=2)
def skip_a_program(mode: str) -> str:
    """Counterfactual Step B applied directly to the raw source grid."""
    if mode not in ("nearest_hit", "farthest_hit"):
        raise ValueError("skip-A is defined only for composed settings")
    return _composed_program(mode, "g")


@lru_cache(maxsize=3)
def rule_text(mode: str) -> str:
    expected = _derived_program(mode)
    path = HERE / "rules" / f"{mode}.rkt"
    observed = path.read_text(encoding="utf-8")
    if observed != expected:
        raise ValueError(f"materialized {mode} rule differs from its declared derivation")
    return observed


def program(settings):
    return rule_text(_settings(settings))


def generate(seed, settings, demos, queries):
    mode = _settings(settings)
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 4, 8)
    inputs = [build_input(seed, index) for index in range(demos + queries)]
    frozen = {tuple(tuple(row) for row in grid) for grid in inputs}
    if len(frozen) != len(inputs):
        raise AssertionError("episode inputs must be distinct")
    pairs = [
        {"input": grid, "output": oracle.solve(grid, mode)}
        for grid in inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
