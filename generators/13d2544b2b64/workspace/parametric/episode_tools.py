"""Small reusable authoring tools for bounded rule-parameter episodes.

No canonical generator or production runtime interface is changed here.
Racket outputs are mandatory; there is deliberately no Python-label fallback.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
import hashlib
import json
from typing import Any


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("episode seed must be a literal nonnegative integer")
    return seed


class ParameterSpace:
    """Strict finite parameter declarations and source-independent seed draws."""

    def __init__(self, allowed: Mapping[str, Sequence[Any]], defaults: Mapping[str, Any]):
        self.allowed = {name: tuple(values) for name, values in allowed.items()}
        if not self.allowed or any(not values for values in self.allowed.values()):
            raise ValueError("parameter domains must be nonempty")
        if set(defaults) != set(self.allowed):
            raise ValueError("parameter defaults must cover every declared name")
        self.defaults = dict(defaults)
        self.normalize(defaults)

    def normalize(self, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if parameters is None:
            parameters = {}
        if not isinstance(parameters, Mapping):
            raise ValueError("parameters must be a mapping")
        unknown = [name for name in parameters if name not in self.allowed]
        if unknown:
            raise ValueError(f"unknown parameter(s): {unknown!r}")
        result = dict(self.defaults)
        for name, value in parameters.items():
            if not any(type(value) is type(allowed) and value == allowed
                       for allowed in self.allowed[name]):
                raise ValueError(f"parameter {name} must be one of {self.allowed[name]!r}")
            result[name] = value
        return result

    def choose(self, seed: int, *, namespace: str) -> dict[str, Any]:
        validate_seed(seed)
        result = {}
        for name, values in self.allowed.items():
            raw = hashlib.sha256(f"{namespace}:{name}:{seed}".encode()).digest()
            result[name] = values[int.from_bytes(raw[:8], "big") % len(values)]
        return result


def grid_copy(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or len(grid) > 30:
        raise ValueError("grid must contain 1..30 rows")
    if any(not isinstance(row, list) or not row or len(row) > 30 for row in grid):
        raise ValueError("grid rows must contain 1..30 colors")
    if len({len(row) for row in grid}) != 1:
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be literal integers 0..9")
    return [row[:] for row in grid]


def grid_differences(expected: list[list[int]], actual: list[list[int]]) -> list[dict]:
    if len(expected) != len(actual) or any(len(a) != len(b) for a, b in zip(expected, actual)):
        return [{"shape_mismatch": True, "expected": expected, "actual": actual}]
    return [{"row": r, "col": c, "expected": a, "actual": b}
            for r, (erow, arow) in enumerate(zip(expected, actual))
            for c, (a, b) in enumerate(zip(erow, arow)) if a != b]


class RacketRunner:
    """Execute exact authored rule! expressions with the included bridge.

    A lexical rule! binding applies the supplied function to the literal grid.
    This preserves the complete authored program without stripping or rewriting
    it. Every call is self-contained; reference source and labels remain private.
    """

    def __init__(self, *, timeout: float = 20.0):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=timeout)
        self.executions: list[dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.bridge.shutdown()

    @property
    def runtime_identity(self) -> dict:
        return self.bridge.runtime_identity

    def run(self, source: str, inputs: Sequence[list[list[int]]]) -> list[list[list[int]]]:
        if not isinstance(source, str) or not source.lstrip().startswith("(rule!"):
            raise ValueError("Racket source must be an authored rule! expression")
        outputs = []
        for value in inputs:
            grid = grid_copy(value)
            literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            expression = f"(let ((rule! (lambda (fn) (fn '{literal}))))\n{source}\n)"
            output = grid_copy(self.bridge.eval_text(expression))
            self.executions.append({
                "program_sha256": digest_bytes(source.encode()),
                "input_sha256": digest_json(grid),
                "output_sha256": digest_json(output),
            })
            outputs.append(output)
        return outputs


def rival_report(demonstrations: list[dict], queries: list[dict],
                 programs: Mapping[str, str], *, runner: RacketRunner) -> dict:
    """Execute every declared candidate; queries cannot establish identifiability."""
    pairs = demonstrations + queries
    result = {}
    for name, source in programs.items():
        outputs = runner.run(source, [pair["input"] for pair in pairs])
        diffs = [grid_differences(pair["output"], output) for pair, output in zip(pairs, outputs)]
        demo_diffs = [{"pair_index": i, "cells": cells}
                      for i, cells in enumerate(diffs[:len(demonstrations)]) if cells]
        query_diffs = [{"pair_index": i, "cells": cells}
                       for i, cells in enumerate(diffs[len(demonstrations):]) if cells]
        result[name] = {
            "program_sha256": digest_bytes(source.encode()),
            "demo_mismatch_indices": [row["pair_index"] for row in demo_diffs],
            "query_mismatch_indices": [row["pair_index"] for row in query_diffs],
            "refuted_by_demonstrations": bool(demo_diffs),
            "demo_differences": demo_diffs,
            "query_differences": query_diffs,
        }
    return result


def public_challenge(episode: Mapping[str, Any]) -> dict:
    """Allowlist projection, with no references shared with the private record."""
    result = {
        "train": [{"input": grid_copy(pair["input"]), "output": grid_copy(pair["output"])}
                  for pair in episode["train"]],
        "test": [{"input": grid_copy(pair["input"])} for pair in episode["test"]],
    }
    return copy.deepcopy(result)
