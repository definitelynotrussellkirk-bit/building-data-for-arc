"""Bounded source-bound audit for the d1bf9a8e4c69 parametric lesson.

The default CLI executes all declared programs through the packet's protected
Racket runtime.  ``run_audit`` also accepts an injected evaluator so the audit's
selection, cache, and causal-case logic can be regression-tested cheaply.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
TASK_ID = "d1bf9a8e4c69"
PROGRAM_FILES = {
    "corners_only": "canonical.rkt",
    "nearest_corner_bridge": "nearest_corner_bridge.rkt",
    "nearest_original_cells": "nearest_original_cells.rkt",
    "column_first_bridge": "column_first_bridge.rkt",
    "first_two_components": "first_two_components.rkt",
    "per_color_groups": "per_color_groups.rkt",
    "farthest_corner_bridge": "farthest_corner_bridge.rkt",
}
DECLARED_SETTINGS = ("corners_only", "nearest_corner_bridge")


def _load(path: Path, stem: str):
    name = f"_{stem}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load(HERE / "prototype.py", "d1bf9a8e4c69_audit_prototype")
_ADAPTER = _load(HERE / "adapter.py", "d1bf9a8e4c69_audit_adapter")


def programs() -> dict[str, str]:
    """Return every declared setting and finite authoring rival as exact text."""
    result = {
        name: (HERE / "rules" / filename).read_text(encoding="utf-8")
        for name, filename in PROGRAM_FILES.items()
    }
    if len(result) != len(set(result.values())):
        raise ValueError("audit programs must be textually distinct")
    return result


def python_apply(source: str, grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror used only to test the audit controller itself."""
    source_to_name = {text: name for name, text in programs().items()}
    try:
        name = source_to_name[source]
        solver = _PROTOTYPE.RIVAL_SOLVERS[name]
    except KeyError as exc:
        raise ValueError("unknown audit program") from exc
    return solver(deepcopy(grid))


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for left_row, right_row in zip(left, right, strict=True)
        for a, b in zip(left_row, right_row, strict=True)
    )


def _validate_counts(seeds, demo_counts, queries):
    if (
        type(seeds) is not list
        or not seeds
        or any(type(seed) is not int or seed < 0 for seed in seeds)
        or len(seeds) != len(set(seeds))
    ):
        raise ValueError("seeds must be a nonempty list of distinct nonnegative integers")
    if (
        type(demo_counts) is not list
        or not demo_counts
        or any(type(count) is not int or not 2 <= count <= 6 for count in demo_counts)
        or len(demo_counts) != len(set(demo_counts))
    ):
        raise ValueError("demo_counts must be distinct integers in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")


def run_audit(
    seeds: list[int],
    demo_counts: list[int],
    queries: int = 4,
    *,
    apply_program: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
    runtime_identity: dict | None = None,
) -> dict:
    """Audit finite learnability, label parity, coverage, and one causal case."""
    _validate_counts(seeds, demo_counts, queries)
    sources = programs()
    bridge = None
    if apply_program is None:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        bridge = RacketBridge(max_calls_before_restart=64)
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            bridge.close()
            raise RuntimeError("self-audit requires protected Racket")
        wrapped: dict[str, str] = {}

        def racket_apply(source, grid):
            if source not in wrapped:
                wrapped[source] = wrap_rule(source)
            literal = "'(" + " ".join(
                "(" + " ".join(map(str, row)) + ")" for row in grid
            ) + ")"
            return bridge.eval_text(f"({wrapped[source]} {literal})")

        apply_program = racket_apply
        runtime_identity = identity
    elif not callable(apply_program):
        raise ValueError("apply_program must be callable")
    elif runtime_identity is None:
        runtime_identity = {"backend": "injected", "protected": False}

    report = {
        "schema": "arcpuzzles-d1bf9a8e4c69-self-audit-v1",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": queries,
        "declared_settings": list(DECLARED_SETTINGS),
        "programs": {
            name: {
                "path": f"generators/{TASK_ID}/workspace/parametric/rules/{PROGRAM_FILES[name]}",
                "sha256": hashlib.sha256(source.encode()).hexdigest(),
            }
            for name, source in sources.items()
        },
        "runtime_identity": runtime_identity,
        "jobs": [],
        "findings": [],
    }
    cache: dict[tuple[str, str], list[list[int]]] = {}
    evaluations = 0

    def apply_cached(name: str, grid: list[list[int]]):
        nonlocal evaluations
        key = (name, _grid_key(grid))
        if key not in cache:
            cache[key] = apply_program(sources[name], deepcopy(grid))
            evaluations += 1
        return deepcopy(cache[key])

    full_episodes: dict[tuple[int, str], dict] = {}
    try:
        for seed in seeds:
            matched_inputs = None
            for finish in DECLARED_SETTINGS:
                full = _ADAPTER.generate(seed, {"finish": finish}, demos=6, queries=4)
                full_episodes[(seed, finish)] = full
                visible = [_grid_key(pair["input"]) for pair in full["train"] + full["test"]]
                if matched_inputs is None:
                    matched_inputs = visible
                elif visible != matched_inputs:
                    report["findings"].append({
                        "kind": "settings_inputs_not_matched",
                        "seed": seed,
                        "finish": finish,
                    })

            for demos in demo_counts:
                for finish in DECLARED_SETTINGS:
                    episode = _ADAPTER.generate(seed, {"finish": finish}, demos=demos, queries=queries)
                    pairs = episode["train"] + episode["test"]
                    selected_outputs = [apply_cached(finish, pair["input"]) for pair in pairs]
                    mismatches = [
                        index
                        for index, (actual, pair) in enumerate(zip(selected_outputs, pairs, strict=True))
                        if actual != pair["output"]
                    ]
                    if mismatches:
                        report["findings"].append({
                            "kind": "selected_program_label_mismatch",
                            "seed": seed,
                            "demos": demos,
                            "queries": queries,
                            "finish": finish,
                            "pair_indexes": mismatches,
                        })

                    survivors = []
                    query_disagreements = {}
                    for name in sources:
                        demo_outputs = [apply_cached(name, pair["input"]) for pair in episode["train"]]
                        if all(
                            actual == pair["output"]
                            for actual, pair in zip(demo_outputs, episode["train"], strict=True)
                        ):
                            survivors.append(name)
                        rival_queries = [apply_cached(name, pair["input"]) for pair in episode["test"]]
                        query_disagreements[name] = sum(
                            actual != pair["output"]
                            for actual, pair in zip(rival_queries, episode["test"], strict=True)
                        )
                    if survivors != [finish]:
                        report["findings"].append({
                            "kind": "finite_survivor_failure",
                            "seed": seed,
                            "demos": demos,
                            "queries": queries,
                            "finish": finish,
                            "survivors": survivors,
                        })
                    report["jobs"].append({
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "settings": {"finish": finish},
                        "survivors": survivors,
                        "query_disagreements": query_disagreements,
                    })

        preferred_seed = 17 if 17 in seeds else seeds[-1]
        episode = full_episodes[(preferred_seed, "nearest_corner_bridge")]
        candidates = list(reversed(episode["test"][:queries])) + list(reversed(episode["train"]))
        causal_case = None
        for pair in candidates:
            intended = apply_cached("nearest_corner_bridge", pair["input"])
            counterfactual = apply_cached("nearest_original_cells", pair["input"])
            if intended == counterfactual:
                continue
            state = _PROTOTYPE.corner_state(pair["input"])
            causal_case = {
                "settings": {"finish": "nearest_corner_bridge"},
                "program": sources["nearest_corner_bridge"],
                "input": deepcopy(pair["input"]),
                "output": intended,
                "counterfactual_program": sources["nearest_original_cells"],
                "counterfactual_output": counterfactual,
                "intermediate_value": {
                    "stage_a_corner_grid": _PROTOTYPE._corner_grid(pair["input"]),
                    "selected_corner_pair": state["nearest_corner_pair"],
                    "selected_corner_distance": state["nearest_corner_distance"],
                    "counterfactual_original_pair": state["nearest_original_pair"],
                    "counterfactual_original_distance": state["nearest_original_distance"],
                    "bridge_orientation": state["orientation"],
                },
                "ablation": "wrong_intermediate",
                "changed_cells": _changed_cells(intended, counterfactual),
            }
            break
        if causal_case is None:
            report["findings"].append({"kind": "missing_causal_counterfactual"})
        report["causal_case"] = causal_case
    finally:
        if bridge is not None:
            bridge.close()

    report["evaluation_count"] = evaluations
    report["cache_entries"] = len(cache)
    report["job_count"] = len(report["jobs"])
    report["finding_count"] = len(report["findings"])
    report["passed"] = not report["findings"] and report["causal_case"] is not None
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--demos", nargs="+", type=int, default=[2, 3, 4, 5, 6])
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", required=True)
    parser.add_argument("--causal-case-out")
    args = parser.parse_args(argv)
    report = run_audit(args.seeds, args.demos, args.queries)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.causal_case_out:
        case_path = Path(args.causal_case_out)
        case_path.parent.mkdir(parents=True, exist_ok=True)
        case_path.write_text(
            json.dumps(report["causal_case"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "passed": report["passed"],
        "job_count": report["job_count"],
        "finding_count": report["finding_count"],
        "evaluation_count": report["evaluation_count"],
        "causal_changed_cells": report["causal_case"]["changed_cells"] if report["causal_case"] else None,
        "out": str(output),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
