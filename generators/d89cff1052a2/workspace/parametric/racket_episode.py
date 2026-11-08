"""Task-local Racket labeler and finite-rival episode audit, reusable by authors.

All labels and rival predictions come from the included Racket executor.  This
module accepts arbitrary fully labelled train/test episodes and exact ``rule!``
programs; it knows nothing about reflection parameters or a particular sampler.
It is an authoring helper, not a production interface or an approval gate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import Any


JSON_HASH_ALGORITHM = "sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8'))"


def json_hash(value: Any) -> str:
    """Hash canonical JSON content, independently of whitespace in a saved file."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def validate_grid(grid: list) -> None:
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be in 1..30")
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be in 1..30")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal integers in 0..9")


class RacketOracle:
    """One protected Racket process; immutable results cached by code and input.

    The small adapter intentionally reuses the included ArcExecutor's ``rule!``
    loader and grid application path. It does not reimplement rule wrapping or
    transformation semantics. This local adapter is serial, not thread safe.
    """

    def __init__(self):
        if os.environ.get("ARC_FORCE_PYTHON_EVAL"):
            raise RuntimeError("ARC_FORCE_PYTHON_EVAL conflicts with Racket-only labelling")
        from arc_repl.executor import ArcExecutor

        self.executor = ArcExecutor({"train": [], "test": []}, auto_scan_on_load=False, use_racket=True)
        if not self.executor.use_racket or self.executor._bridge is None:
            self.executor.close()
            raise RuntimeError("A real Racket backend is required")
        self.runtime_identity = copy.deepcopy(self.executor._bridge.runtime_identity)
        self._functions: dict[str, str] = {}
        self._outputs: dict[tuple[str, str], list] = {}
        self.executions = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.executor.close()

    def label(self, program: str, grid: list) -> list:
        from arc_repl.builtins import Grid, _unwrap
        from arc_repl.parser import Symbol, parse

        validate_grid(grid)
        if not isinstance(program, str):
            raise TypeError("program must be exact Racket source text")
        digest = text_hash(program)
        key = digest, json_hash(grid)
        if key not in self._outputs:
            if digest not in self._functions:
                parsed = parse(program)
                if not (isinstance(parsed, list) and len(parsed) == 2
                        and isinstance(parsed[0], Symbol) and parsed[0].name == "rule!"):
                    raise ValueError("expected one executable (rule! ...) program")
                response = self.executor.step(program)
                if response.startswith("ERROR"):
                    raise RuntimeError(response)
                self._functions[digest] = self.executor._rule_fn
            self.executor._rule_fn = self._functions[digest]
            output = _unwrap(self.executor._apply_rule(Grid(copy.deepcopy(grid))))
            validate_grid(output)
            self.executions += 1
            self._outputs[key] = copy.deepcopy(output)
        return copy.deepcopy(self._outputs[key])


def public_challenge(episode: dict) -> dict:
    """Whitelist public ARC fields; never serialize a private object then prune."""
    return {
        "train": [{"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
                  for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def score_episode(episode: dict, candidates: dict[str, str], selected: str, *, oracle: RacketOracle) -> dict:
    """Check production demos and every single-pair query holdout.

    A rival is ambiguous only when it fits every demonstration and disagrees on
    a query. ``survived_all`` is reported separately. Errors and mismatched
    reference labels fail closed. ``parameters_identified`` additionally demands
    that demonstrations refute every alternative, even answer-equivalent ones.
    """
    if selected not in candidates or not candidates:
        raise ValueError("selected program must be present in a nonempty candidate map")
    if not episode.get("train") or not episode.get("test"):
        raise ValueError("a complete episode needs demonstrations and queries")
    pairs = episode["train"] + episode["test"]
    for pair in pairs:
        validate_grid(pair["input"])
        validate_grid(pair["output"])
    predictions: dict[str, list] = {}
    errors: dict[str, str] = {}
    for name, program in candidates.items():
        try:
            predictions[name] = [oracle.label(program, pair["input"]) for pair in pairs]
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
    reference_matches = selected not in errors and all(
        actual == pair["output"] for actual, pair in zip(predictions.get(selected, []), pairs)
    )

    def score(demos: list[int], queries: list[int]) -> dict:
        rivals = {}
        for name in candidates:
            if name == selected:
                continue
            if name in errors:
                rivals[name] = {"status": "execution_error", "error": errors[name], "demo_fit": None}
                continue
            values = predictions[name]
            refuting = [index for index in demos if values[index] != pairs[index]["output"]]
            differing = [index for index in queries if values[index] != pairs[index]["output"]]
            ambiguous = not refuting and bool(differing)
            rivals[name] = {
                "status": "refuted_by_demonstrations" if refuting else "ambiguous_query" if ambiguous else "survived_all",
                "demo_fit": not refuting,
                "refuting_demo_indices": refuting,
                "differing_query_indices": differing,
                "prediction_sha256": [json_hash(value) for value in values],
                "query_differences": [
                    {"pair_index": index, "input": pairs[index]["input"],
                     "expected": pairs[index]["output"], "prediction": values[index]}
                    for index in differing
                ] if ambiguous else [],
            }
        ambiguous = any(row["status"] == "ambiguous_query" for row in rivals.values())
        identified = reference_matches and not errors and all(
            row["status"] == "refuted_by_demonstrations" for row in rivals.values()
        )
        return {
            "demonstration_indices": demos,
            "query_indices": queries,
            "status": "error" if errors or not reference_matches else "ambiguous" if ambiguous else "no_ambiguity_found",
            "parameters_identified": bool(identified),
            "rivals": rivals,
        }

    n_train = len(episode["train"])
    production = score(list(range(n_train)), list(range(n_train, len(pairs))))
    rotations = [score([index for index in range(len(pairs)) if index != query], [query])
                 for query in range(len(pairs))]
    statuses = [production["status"], *(row["status"] for row in rotations)]
    return {
        "schema": "task-local-racket-episode-audit-v1",
        "json_hash_algorithm": JSON_HASH_ALGORITHM,
        "selected": selected,
        "episode_pairs_sha256": json_hash({"train": episode["train"], "test": episode["test"]}),
        "program_sha256": {name: text_hash(program) for name, program in candidates.items()},
        "reference_labels_match": reference_matches,
        "errors": errors,
        "status": "error" if "error" in statuses else "ambiguous" if "ambiguous" in statuses else "no_ambiguity_found",
        "parameters_identified": all(row["parameters_identified"] for row in [production, *rotations]),
        "production": production,
        "rotations": rotations,
        "scope": "finite supplied candidates and labelled pairs; not universal identifiability or approval",
    }
