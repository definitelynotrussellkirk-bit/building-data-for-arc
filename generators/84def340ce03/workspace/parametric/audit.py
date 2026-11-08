#!/usr/bin/env python3
"""Protected-Racket bounded learnability audit for feedback-routed rings."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable, Iterable

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "84def340ce03"
HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
RUNTIME = REPO / "shared" / "runtime"
ROUTINGS = ("direct", "feedback_min")


def _load_exact(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _source_hashes() -> dict[str, str]:
    relative_paths = (
        "adapter.py",
        "audit.py",
        "promotion.json",
        "prototype.py",
        "rules/direct.rkt",
        "rules/feedback_min.rkt",
    )
    return {
        path: hashlib.sha256((HOME / path).read_bytes()).hexdigest()
        for path in relative_paths
    }


def _first_disagreement(outputs: list[list[list[int]]], expected: list[list[list[int]]]) -> int:
    for index, (actual, wanted) in enumerate(zip(outputs, expected, strict=True)):
        if actual != wanted:
            return index
    raise RuntimeError("candidate unexpectedly survived the bounded split")


def build_report(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
) -> dict:
    """Replay selected labels in protected Racket and pressure-test finite rivals."""
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    if not seeds or any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seeds):
        raise ValueError("seeds must be nonempty exact integers in 0..2**63-1")
    if not demo_counts or any(type(count) is not int or not 2 <= count <= 6 for count in demo_counts):
        raise ValueError("demo_counts must be nonempty exact integers in 2..6")

    adapter = _load_exact("_arc_84def340ce03_audit_adapter", HOME / "adapter.py")
    prototype = _load_exact("_arc_84def340ce03_audit_prototype", HOME / "prototype.py")
    programs = {routing: adapter.program({"routing": routing}) for routing in ROUTINGS}
    candidates: dict[str, Callable[[list[list[int]]], list[list[int]]] | None] = {
        "direct": None,
        "feedback_min": None,
        **prototype.RIVALS,
    }

    cache: dict[tuple[str, str], list[list[int]]] = {}
    evaluations = 0
    checks: list[dict] = []
    minimal_counterexample = None

    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
                nonlocal evaluations
                key = (program, json.dumps(grid, separators=(",", ":")))
                if key not in cache:
                    cache[key] = apply(program, grid)
                    evaluations += 1
                return cache[key]

            def predict(name: str, grid: list[list[int]]) -> list[list[int]]:
                if name in programs:
                    return execute(programs[name], grid)
                function = candidates[name]
                if function is None:
                    raise AssertionError(name)
                return function(grid)

            for seed in seeds:
                for demos in demo_counts:
                    for routing in ROUTINGS:
                        settings = {"routing": routing}
                        episode = adapter.generate(seed, settings, demos, 4)
                        demo_inputs = [pair["input"] for pair in episode["train"]]
                        query_inputs = [pair["input"] for pair in episode["test"]]
                        selected_program = programs[routing]
                        expected_demo = [execute(selected_program, grid) for grid in demo_inputs]
                        expected_query = [execute(selected_program, grid) for grid in query_inputs]
                        claimed = [pair["output"] for pair in episode["train"] + episode["test"]]
                        authoritative = expected_demo + expected_query
                        if claimed != authoritative:
                            raise RuntimeError(
                                f"Python claim disagrees with Racket for seed={seed}, demos={demos}, routing={routing}"
                            )
                        python_selected = [
                            prototype.render(grid, routing)
                            for grid in demo_inputs + query_inputs
                        ]
                        python_matches = python_selected == authoritative
                        if not python_matches:
                            raise RuntimeError("independent Python mirror disagrees with protected Racket")

                        demo_predictions = {
                            name: [predict(name, grid) for grid in demo_inputs]
                            for name in candidates
                        }
                        query_predictions = {
                            name: [predict(name, grid) for grid in query_inputs]
                            for name in candidates
                        }
                        declared_survivors = [
                            name for name in ROUTINGS
                            if demo_predictions[name] == expected_demo
                        ]
                        bounded_survivors = [
                            name for name in candidates
                            if demo_predictions[name] == expected_demo
                        ]
                        if declared_survivors != [routing] or bounded_survivors != [routing]:
                            raise RuntimeError(
                                f"visible lesson did not isolate {routing}: "
                                f"declared={declared_survivors}, bounded={bounded_survivors}"
                            )

                        eliminated = {}
                        for name in candidates:
                            if name == routing:
                                continue
                            eliminated[name] = {
                                "first_demo_disagreement": _first_disagreement(
                                    demo_predictions[name], expected_demo
                                ),
                                "first_query_disagreement": _first_disagreement(
                                    query_predictions[name], expected_query
                                ),
                            }
                        checks.append({
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "settings": settings,
                            "declared_survivors": declared_survivors,
                            "bounded_survivors": bounded_survivors,
                            "python_selected_matches_racket": python_matches,
                            "racket_label_count": demos + 4,
                            "eliminated_candidates": eliminated,
                        })

                        if routing == "feedback_min" and minimal_counterexample is None:
                            rival_name = "source_min_not_rendered"
                            query_index = eliminated[rival_name]["first_query_disagreement"]
                            minimal_counterexample = {
                                "seed": seed,
                                "demos": demos,
                                "query_index": query_index,
                                "selected": routing,
                                "rival": rival_name,
                                "input": query_inputs[query_index],
                                "expected_racket": expected_query[query_index],
                                "rival_output": query_predictions[rival_name][query_index],
                                "why": (
                                    "The rival reads the previous unrotated source tile; "
                                    "the selected rule reads the completed rendered ring."
                                ),
                            }
        finally:
            bridge.close()

    if minimal_counterexample is None:
        raise RuntimeError("audit did not retain a feedback counterexample")
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "source_sha256": _source_hashes(),
        "racket": identity,
        "racket_evaluations": evaluations,
        "scope": {
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "queries": 4,
            "settings": [{"routing": routing} for routing in ROUTINGS],
            "named_plausible_rivals": list(prototype.RIVALS),
            "claim_limit": (
                "Finite declared-setting and named-rival audit only; no uniqueness "
                "claim over unrestricted programs and no claim of training benefit."
            ),
        },
        "checks": checks,
        "minimal_counterexample": minimal_counterexample,
        "conclusion": (
            "Every checked visible lesson leaves only its selected declared setting "
            "and eliminates all four named shortcut rules; every retained label was "
            "replayed by the same-checkout protected Racket backend."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="JSON evidence path")
    args = parser.parse_args(argv)
    report = build_report()
    destination = Path(args.out).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(destination),
        "checks": len(report["checks"]),
        "racket_evaluations": report["racket_evaluations"],
        "protected": report["racket"]["protected"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
