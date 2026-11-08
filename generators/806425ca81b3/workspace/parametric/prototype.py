"""Unapproved bounded rule variants of ARC 22168020 / 806425ca81b3.

All episode labels and parameter-rival predictions use the real Racket bridge.
The Python mirror is an independent parity oracle, never the label authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
import random
import sys
from tempfile import TemporaryDirectory

from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, validate_grid
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


TASK_ID = "806425ca81b3"
VERSION = "prototype-1"
ROOT = find_root(__file__)
DEFAULT_PARAMETERS = {"axis": "row", "min_anchors": 2}
SETTINGS = tuple({"axis": axis, "min_anchors": count}
                 for axis in ("row", "column") for count in (2, 3))


def validate_parameters(parameters=None) -> dict:
    """Return a fresh complete setting; reject unknown keys and coercions."""
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be a mapping")
    if set(parameters) - set(DEFAULT_PARAMETERS):
        raise ValueError("unknown parameter keys")
    result = {**DEFAULT_PARAMETERS, **parameters}
    if type(result["axis"]) is not str or result["axis"] not in ("row", "column"):
        raise ValueError("axis must be 'row' or 'column'")
    if type(result["min_anchors"]) is not int or result["min_anchors"] not in (2, 3):
        raise ValueError("min_anchors must be integer 2 or 3")
    return result


def _seed(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer; booleans are not seeds")
    return seed


def _rng(seed, stream):
    digest = hashlib.sha256(f"{VERSION}:{_seed(seed)}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def sample_parameters(seed: int) -> dict:
    """Draw one fixed episode setting using a separate deterministic stream."""
    return dict(_rng(seed, "parameters").choice(SETTINGS))


@lru_cache(maxsize=1)
def _canonical():
    records = Catalog(ROOT).get(TASK_ID)["variants"]
    if len(records) != 1 or not records[0].get("program_solution"):
        raise ValueError("expected one unambiguous canonical Racket authority")
    return records[0]


def canonical_record() -> dict:
    return deepcopy(_canonical())


def materialize_rule(parameters=None) -> str:
    """Return exact executable source, preserving canonical default bytes."""
    params = validate_parameters(parameters)
    if params == DEFAULT_PARAMETERS:
        return _canonical()["program_solution"]
    column = params["axis"] == "column"
    extent, index = ("h", "r") if column else ("w", "c")
    at = "(cell-at g k c)" if column else "(cell-at g r k)"
    count = params["min_anchors"]
    return f"""(rule!
 ;; In each {params['axis']}, collect anchors independently for each nonzero color.
 ;; A color needs at least {count} anchors before it can fill any intervening zeros.
 ;; Preserve every original nonzero cell; never extend past the outer anchors.
 ;; If spans overlap outside the sampled grammar, the smallest color wins.
 (lambda (g)
  (grid-from-fn h w
   (lambda (r c)
    (let ((v (cell-at g r c)))
     (if (!= v 0) v
      (let* ((colors (unique
                      (filter (lambda (value) (!= value 0))
                        (map (lambda (k) {at}) (range 0 {extent})))))
             (color
              (find-first
               (lambda (candidate)
                (let ((positions
                       (filter (lambda (k) (= candidate {at}))
                         (range 0 {extent}))))
                 (and (>= (length positions) {count})
                      (< (first positions) {index})
                      (> (last positions) {index}))))
               colors)))
       (if color color 0))))))))
"""


def _transpose(grid):
    return [list(line) for line in zip(*grid)]


def mirror(grid, parameters=None) -> list[list[int]]:
    """Pure parity oracle, defined on every well-formed ARC grid up to 30×30."""
    params = validate_parameters(parameters)
    validate_grid(grid)
    lines = _transpose(grid) if params["axis"] == "column" else grid
    result = deepcopy(lines)
    for line_index, line in enumerate(lines):
        positions = {}
        for index, color in enumerate(line):
            if color:
                positions.setdefault(color, []).append(index)
        for index, color in enumerate(line):
            if color:
                continue
            for candidate in sorted(positions):
                anchors = positions[candidate]
                if len(anchors) >= params["min_anchors"] and anchors[0] < index < anchors[-1]:
                    result[line_index][index] = candidate
                    break
    return _transpose(result) if params["axis"] == "column" else result


def input_errors(grid, parameters=None) -> list[str]:
    """Check the prototype's unambiguous 6..30 teaching grammar."""
    params = validate_parameters(parameters)
    try:
        validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if min(len(grid), len(grid[0])) < 6:
        errors.append("teaching grids require both dimensions in 6..30")
    lines = _transpose(grid) if params["axis"] == "column" else grid
    for line_index, line in enumerate(lines):
        positions = {}
        for index, color in enumerate(line):
            if color:
                positions.setdefault(color, []).append(index)
        spans = [(anchors[0], anchors[-1]) for anchors in positions.values() if len(anchors) >= 2]
        if positions and not spans:
            errors.append(f"active line {line_index} lacks repeated-color anchors")
        if any(max(left_a, left_b) <= min(right_a, right_b)
               for index, (left_a, right_a) in enumerate(spans)
               for left_b, right_b in spans[index + 1:]):
            errors.append(f"active line {line_index} has overlapping repeated-color spans")
    if mirror(grid, params) == grid:
        errors.append("at least one qualifying span must contain a zero")
    return errors


def _input(seed, sample_index, height, width, active):
    rng = _rng(seed, f"input-{sample_index}")
    grid = [[0] * width for _ in range(height)]
    line_ids = sorted([0, height - 1, *rng.sample(range(1, height - 1), active - 2)])
    for index, line_id in enumerate(line_ids):
        first, second, singleton = rng.sample(range(1, 10), 3)
        line = grid[line_id]
        if index % 3 == 0:
            for position in (rng.randrange(2), width - 1 - rng.randrange(2)):
                line[position] = first
        elif index % 3 == 1:
            for position in (rng.randrange(2), rng.randint(width // 3, 2 * width // 3),
                             width - 1 - rng.randrange(2)):
                line[position] = first
        else:
            for position in (0, width // 3):
                line[position] = first
            for position in (width // 2, width // 2 + 2, width - 1):
                line[position] = second
            # A different-color singleton inside the first span must survive.
            line[rng.randint(1, width // 3 - 1)] = singleton
    return grid


def make_inputs(seed: int, parameters=None) -> dict:
    """Three instructive demos and one 30×30 query with 24 active lines."""
    _seed(seed)
    params = validate_parameters(parameters)
    shapes = ((8, 12, 3), (10, 15, 5), (12, 18, 8), (30, 30, 24))
    grids = [_input(seed, index, *shape) for index, shape in enumerate(shapes)]
    if params["axis"] == "column":
        grids = [_transpose(grid) for grid in grids]
    for grid in grids:
        errors = input_errors(grid, params)
        if errors:
            raise AssertionError("invalid prototype draw: " + "; ".join(errors))
    return {"train": grids[:3], "test": grids[3:]}


def counterfactual_input() -> list[list[int]]:
    """One common lawful grid yielding four different parameterized outputs."""
    grid = [[0] * 7 for _ in range(7)]
    for row, col in ((0, 0), (0, 3), (0, 6), (3, 0), (3, 6), (6, 0), (6, 3), (6, 6)):
        grid[row][col] = 2
    return grid


class ReferenceRuntime:
    """Small adapter over existing bridge and shared rule normalization."""

    def __init__(self, bridge, wrap_rule):
        self.bridge = bridge
        self.wrap_rule = wrap_rule
        self.calls = 0

    def apply(self, program: str, grid) -> list[list[int]]:
        validate_grid(grid)
        literal = "'(" + " ".join("(" + " ".join(map(str, line)) + ")" for line in grid) + ")"
        output = self.bridge.eval_text(f"({self.wrap_rule(program)} {literal})")
        self.calls += 1
        return validate_grid(output, "Racket output")

    def identity(self) -> dict:
        return self.bridge.runtime_identity


@contextmanager
def reference_runtime():
    """Use the public snapshot preparer, then the included real Racket bridge."""
    with TemporaryDirectory(prefix="806425ca81b3-parametric-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        # wrap_rule uses the shared parser under scripts/, available in the
        # public execution layout. Do not reimplement normalization locally.
        modules_before = set(sys.modules)
        sys.path.insert(0, str(stage))
        try:
            from puzzle_generators.rule_wrap import wrap_rule
            with RacketBridge(prelude_path=str(stage / "arc_repl/racket_prelude/arc-prelude.rkt")) as bridge:
                yield ReferenceRuntime(bridge, wrap_rule)
        finally:
            sys.path.remove(str(stage))
            # Do not leave imports pointing at a deleted snapshot. Existing
            # caller modules are untouched; this also permits later use of
            # reviewer_support.load_selected_generator in the same process.
            for name in set(sys.modules) - modules_before:
                module = sys.modules.get(name)
                origins = list(getattr(module, "__path__", []))
                if getattr(module, "__file__", None):
                    origins.append(module.__file__)
                if any(Path(origin).resolve().is_relative_to(stage) for origin in origins):
                    sys.modules.pop(name, None)


def parameter_rivals(episode: dict, *, runtime: ReferenceRuntime) -> dict:
    params = validate_parameters(episode["parameters"])
    remaining, rivals = [params], []
    ambiguous = 0
    for alternative in SETTINGS:
        if alternative == params:
            continue
        rule = materialize_rule(alternative)
        predictions = [[runtime.apply(rule, pair["input"]) for pair in episode[split]]
                       for split in ("train", "test")]
        demo_matches = [prediction == pair["output"]
                        for prediction, pair in zip(predictions[0], episode["train"])]
        query_matches = [prediction == pair["output"]
                         for prediction, pair in zip(predictions[1], episode["test"])]
        survives = all(demo_matches)
        if survives:
            remaining.append(dict(alternative))
            ambiguous += sum(not match for match in query_matches)
        rivals.append({"parameters": dict(alternative), "demo_matches": demo_matches,
                       "query_matches": query_matches, "predictions": {"train": predictions[0], "test": predictions[1]},
                       "status": ("ambiguous_query" if not all(query_matches) else "survived_all")
                       if survives else "refuted_by_demonstrations"})
    return {"remaining_parameters": remaining, "uniquely_identified": len(remaining) == 1,
            "ambiguous_queries": ambiguous, "rivals": rivals,
            "scope": "All three declared parameter rivals; no claim about arbitrary alternative rules."}


def generate_episode(seed: int, parameters=None, *, runtime=None) -> dict:
    params = validate_parameters(parameters)
    inputs = make_inputs(seed, params)
    if runtime is None:
        with reference_runtime() as running:
            return generate_episode(seed, params, runtime=running)
    rule = materialize_rule(params)
    episode = {"schema": "806425ca81b3-parametric-episode-v1", "status": "prototype",
               "seed": seed, "parameters": params,
               "rule": {"text": rule, "sha256": hashlib.sha256(rule.encode()).hexdigest()}}
    for split in ("train", "test"):
        episode[split] = [{"input": grid, "output": runtime.apply(rule, grid)} for grid in inputs[split]]
        for pair in episode[split]:
            if pair["output"] != mirror(pair["input"], params):
                raise AssertionError("Racket/Python parity mismatch")
    episode["identifiability"] = parameter_rivals(episode, runtime=runtime)
    if not episode["identifiability"]["uniquely_identified"]:
        raise AssertionError("episode does not identify its fixed parameter setting")
    return episode


def public_challenge(episode: dict) -> dict:
    """An allowlist projection: labels only for train, never hidden metadata."""
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]]}
