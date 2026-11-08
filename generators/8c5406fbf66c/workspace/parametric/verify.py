#!/usr/bin/env python3
"""Bounded authoring audit for the 8c5406fbf66c parametric family.

The audit checks count boundaries, matched inputs, prefix-stable sequential
projection, finite-rival teaching, protected-Racket labels, a substantive 30x30
query, and a wrong-intermediate causal ablation.  It is intentionally scoped to
this task and does not grant native qualification or owner acceptance.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

_HOME = Path(__file__).resolve().parent
_SCOPES = ("all", "key_count_relay")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_adapter():
    path = _HOME / "adapter.py"
    name = "_audit_8c5406fbf66c_" + hashlib.sha256(str(path).encode()).hexdigest()
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("Racket result is not a nonempty grid")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width for row in value):
        raise ValueError("Racket result is ragged")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("Racket result contains non-ARC cells")
    return value


@contextmanager
def protected_executor():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    wrapped: dict[str, str] = {}
    evaluations = {"count": 0}
    try:
        identity = dict(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires a protected Racket backend")

        def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            literal = "'(" + " ".join(
                "(" + " ".join(map(str, row)) + ")" for row in grid
            ) + ")"
            evaluations["count"] += 1
            return _grid(bridge.eval_text(f"({wrapped[program]} {literal})"))

        yield execute, identity, evaluations
    finally:
        bridge.close()


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def audit(
    *,
    seeds: Iterable[int] = (0, 17),
    count_cases: Iterable[tuple[int, int]] = ((2, 1), (3, 4), (6, 4)),
    execute: Callable[[str, list[list[int]]], list[list[int]]],
    runtime_identity: dict[str, Any],
) -> dict[str, Any]:
    adapter = load_adapter()
    seeds = tuple(seeds)
    count_cases = tuple(count_cases)
    if not seeds or not count_cases:
        raise ValueError("audit needs seeds and count cases")

    episodes = 0
    jobs = 0
    labels = 0
    finite_rivals: set[str] = set()
    per_job = []
    large_query = None

    for seed in seeds:
        for demos, queries in count_cases:
            generated = {
                scope: adapter.generate(seed, {"window_scope": scope}, demos, queries)
                for scope in _SCOPES
            }
            if _inputs(generated["all"]) != _inputs(generated["key_count_relay"]):
                raise AssertionError("settings did not receive matched inputs")
            for scope, episode in generated.items():
                program = adapter.program({"window_scope": scope})
                for pair in episode["train"] + episode["test"]:
                    actual = execute(program, deepcopy(pair["input"]))
                    if actual != pair["output"]:
                        raise AssertionError(f"Racket label mismatch for {scope}")
                    labels += 1
                teaching = adapter.prototype.teaching_check(episode, scope)
                if teaching["setting_survivors"] != [scope] or teaching["rival_survivors"]:
                    raise AssertionError(f"teaching ambiguity for {scope}: {teaching}")
                finite_rivals.update(teaching["refuted_rivals"])
                jobs += 1
                episodes += 1
                per_job.append(
                    {
                        "seed": seed,
                        "scope": scope,
                        "demos": demos,
                        "queries": queries,
                        "public_first_turn_sha256": hashlib.sha256(
                            adapter.prototype.turn_bytes(episode, 0)
                        ).hexdigest(),
                        "refuted_rivals": teaching["refuted_rivals"],
                    }
                )
                if queries == 4:
                    stress = episode["test"][3]["input"]
                    details = {
                        "dimensions": [len(stress), len(stress[0])],
                        "nonzero_cells": sum(cell != 0 for row in stress for cell in row),
                    }
                    if details["dimensions"] != [30, 30] or details["nonzero_cells"] < 190:
                        raise AssertionError(f"large query is not substantive: {details}")
                    large_query = details

        # Count changes must not mutate shared demonstrations or first query.
        small = adapter.generate(seed, {"window_scope": "key_count_relay"}, 2, 1)
        large = adapter.generate(seed, {"window_scope": "key_count_relay"}, 6, 4)
        if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
            raise AssertionError("count requests are not prefix-stable")
        one_query = adapter.generate(seed, {"window_scope": "key_count_relay"}, 3, 1)
        four_queries = adapter.generate(seed, {"window_scope": "key_count_relay"}, 3, 4)
        if adapter.prototype.turn_bytes(one_query, 0) != adapter.prototype.turn_bytes(four_queries, 0):
            raise AssertionError("first-turn bytes changed with future query count")

    # The first query has source-window count 2.  Force the intermediate to 1;
    # protected execution must select a different area-ranked object.
    seed = seeds[0]
    relay = adapter.generate(seed, {"window_scope": "key_count_relay"}, 3, 4)
    witness_input = relay["test"][0]["input"]
    intermediate = adapter.prototype.analyze_relay(witness_input)["source_window_count"]
    if intermediate == 1:
        raise AssertionError("causal witness needs a non-one intermediate")
    program = adapter.program({"window_scope": "key_count_relay"})
    expected = execute(program, deepcopy(witness_input))
    wrong_program = (_HOME / "wrong_rank_one.rkt").read_text()
    if runtime_identity.get("backend") == "test":
        wrong = adapter.prototype.solve_relay_with_intermediate(witness_input, 1)
    else:
        wrong = execute(wrong_program, deepcopy(witness_input))
    if expected == wrong:
        raise AssertionError("wrong intermediate did not change the final output")

    report = {
        "schema": "arcpuzzles-parametric-authoring-audit-v1",
        "task_id": "8c5406fbf66c",
        "status": "passed",
        "settings": len(_SCOPES),
        "jobs": jobs,
        "episodes": episodes,
        "label_count": labels,
        "seeds": list(seeds),
        "count_cases": [list(case) for case in count_cases],
        "finite_rivals": sorted(finite_rivals),
        "large_query": large_query,
        "causal_ablation": {
            "ablation": "wrong_intermediate",
            "intermediate_value": intermediate,
            "counterfactual_value": 1,
            "changed_output": expected != wrong,
            "input_sha256": hashlib.sha256(
                json.dumps(witness_input, separators=(",", ":")).encode()
            ).hexdigest(),
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(wrong_program.encode()).hexdigest(),
        },
        "racket": runtime_identity,
        "sources": {
            name: _sha(_HOME / name)
            for name in (
                "adapter.py",
                "prototype.py",
                "promotion.json",
                "canonical.rkt",
                "count_relay.rkt",
                "wrong_rank_one.rkt",
            )
        },
        "jobs_detail": per_job,
        "scope": (
            "Finite seeds/counts and named rivals only; this is authoring evidence, "
            "not native qualification, owner acceptance, or training admission."
        ),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    with protected_executor() as (execute, identity, evaluations):
        report = audit(execute=execute, runtime_identity=identity)
        report["racket_evaluations"] = evaluations["count"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    args.out.write_text(raw)
    print(json.dumps({
        "status": report["status"],
        "jobs": report["jobs"],
        "labels": report["label_count"],
        "racket_evaluations": report["racket_evaluations"],
        "out": str(args.out),
        "sha256": hashlib.sha256(raw.encode()).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
