#!/usr/bin/env python3
"""Run the bounded lesson, sampler, and protected-Racket rival audit.

Example from the outer packet directory::

    python3 review.py run python3 \
      generators/b650a355848c/workspace/parametric/audit.py \
      --out ../checks/b650a355848c/self-audit

The finite rival inventory is declared in ``rivals.py``.  Passing means no
listed rule fit every visible demonstration while disagreeing on a query for
the bounded seeds/counts; it is not a universal identifiability proof or owner
acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def _load(name: str):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_b650_audit_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_json(value) -> str:
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _source_hashes() -> dict[str, str]:
    paths = [
        HERE / "adapter.py",
        HERE / "prototype.py",
        HERE / "rivals.py",
        HERE / "audit.py",
        HERE / "canonical.rkt",
        HERE / "promotion.json",
        HERE.parents[1] / "generator.py",
        HERE.parents[1] / "tests" / "test_parametric_b650a355848c.py",
        ROOT / "src" / "arcpuzzles" / "parametric_worker.py",
    ]
    return {
        str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
        for path in paths
    }


def _pairs(episode):
    return episode["train"] + episode["test"]


def _input_sequence(episode):
    return [pair["input"] for pair in _pairs(episode)]


def run_bounded(
    *,
    sampler_seeds: Iterable[int] = range(64),
    execution_seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
    queries: int = 4,
    execute_racket: bool = True,
) -> dict:
    prototype = _load("prototype")
    rivals = _load("rivals")
    sampler_seeds = tuple(sampler_seeds)
    execution_seeds = tuple(execution_seeds)
    demo_counts = tuple(demo_counts)
    if not sampler_seeds:
        raise ValueError("sampler_seeds must be nonempty")
    if not demo_counts or any(type(value) is not int for value in demo_counts):
        raise ValueError("demo_counts must contain exact integers")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    if type(execute_racket) is not bool:
        raise ValueError("execute_racket must be bool")

    started = time.perf_counter()
    policies = tuple(prototype.POLICIES)
    statistics = {
        policy: {
            name: {
                "episodes": 0,
                "demo_survivals": 0,
                "query_disagreements": 0,
                "harmful_survivals": 0,
                "all_pair_agreements": 0,
            }
            for name in rivals.NAMES
        }
        for policy in policies
    }
    report = {
        "schema": "b650a355848c-marker-assignment-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "running",
        "scope": (
            "Finite explicit shortcut inventory; 64-seed sampler census by default, "
            "minimum/ordinary/maximum demo counts, four queries, and protected-Racket "
            "parity on two source-bound seeds. No universal uniqueness or training claim."
        ),
        "sources": _source_hashes(),
        "request": {
            "sampler_seeds": list(sampler_seeds),
            "execution_seeds": list(execution_seeds),
            "demo_counts": list(demo_counts),
            "queries": queries,
            "execute_racket": execute_racket,
        },
        "rival_descriptions": dict(rivals.DESCRIPTIONS),
        "sampler_requests": 0,
        "sampler_input_count": 0,
        "sampler_profiles": {},
        "statistics": statistics,
        "harmful_survivors": [],
        "harmless_survivors": [],
        "runtime": None,
        "racket_evaluations": 0,
        "racket_parity_failures": [],
        "minimal_racket_cases": {},
        "failures": [],
    }

    try:
        for seed in sampler_seeds:
            for demos in demo_counts:
                episodes = {
                    policy: prototype.generate(
                        seed, {"assignment_policy": policy}, demos=demos, queries=queries
                    )
                    for policy in policies
                }
                sequences = [_input_sequence(episodes[policy]) for policy in policies]
                if any(sequence != sequences[0] for sequence in sequences[1:]):
                    raise AssertionError(f"setting-dependent inputs: seed={seed} demos={demos}")
                profile_key = str(demos)
                profile = report["sampler_profiles"].setdefault(
                    profile_key,
                    {"requests": 0, "input_sizes": set(), "shape_counts": set()},
                )
                for policy, episode in episodes.items():
                    pairs = _pairs(episode)
                    serialized = [json.dumps(pair["input"], separators=(",", ":"))
                                  for pair in pairs]
                    if len(serialized) != len(set(serialized)):
                        raise AssertionError(
                            f"duplicate input: seed={seed} demos={demos} policy={policy}"
                        )
                    if len(episode["train"]) != demos or len(episode["test"]) != queries:
                        raise AssertionError("requested split count changed")
                    if episode["program_solution"] != prototype.program(
                        {"assignment_policy": policy}
                    ):
                        raise AssertionError("program_solution mismatch")
                    other = policies[1 - policies.index(policy)]
                    if all(
                        prototype.solve(pair["input"], {"assignment_policy": other})
                        == pair["output"]
                        for pair in episode["train"]
                    ):
                        raise AssertionError(
                            f"official setting survived demos: seed={seed} demos={demos} "
                            f"selected={policy}"
                        )
                    for pair in pairs:
                        grid = pair["input"]
                        profile["input_sizes"].add((len(grid), len(grid[0])))
                        profile["shape_counts"].add(
                            prototype.observables(grid)["shape_count"]
                        )
                    for name in rivals.NAMES:
                        predicted = [
                            rivals.output(prototype, pair["input"], name) for pair in pairs
                        ]
                        demo_match = all(
                            predicted[index] == pair["output"]
                            for index, pair in enumerate(episode["train"])
                        )
                        query_disagreement = any(
                            predicted[demos + index] != pair["output"]
                            for index, pair in enumerate(episode["test"])
                        )
                        row = statistics[policy][name]
                        row["episodes"] += 1
                        row["demo_survivals"] += int(demo_match)
                        row["query_disagreements"] += int(query_disagreement)
                        row["harmful_survivals"] += int(demo_match and query_disagreement)
                        row["all_pair_agreements"] += int(demo_match and not query_disagreement)
                        if demo_match and query_disagreement:
                            report["harmful_survivors"].append({
                                "seed": seed,
                                "demos": demos,
                                "queries": queries,
                                "selected": policy,
                                "rival": name,
                            })
                    report["sampler_requests"] += 1
                    report["sampler_input_count"] += len(pairs)
                    profile["requests"] += 1

        for profile in report["sampler_profiles"].values():
            profile["input_sizes"] = [list(value) for value in sorted(profile["input_sizes"])]
            profile["shape_counts"] = sorted(profile["shape_counts"])

        for policy, rows in statistics.items():
            for name, row in rows.items():
                if row["demo_survivals"] and not row["harmful_survivals"]:
                    report["harmless_survivors"].append({
                        "selected": policy,
                        "rival": name,
                        "episodes": row["episodes"],
                        "demo_survivals": row["demo_survivals"],
                        "all_pair_agreements": row["all_pair_agreements"],
                    })

        if report["harmful_survivors"]:
            raise AssertionError(
                f"{len(report['harmful_survivors'])} finite rivals fit demos and changed queries"
            )

        if execute_racket:
            programs = rivals.programs()
            execution_demos = min(demo_counts)
            cache: dict[tuple[str, str], list[list[int]]] = {}
            runtime = ROOT / "shared" / "runtime"
            bridge = None
            with _local_imports(runtime, HERE):
                apply, identity, bridge = _real_evaluator(runtime)
                report["runtime"] = identity
                try:
                    def execute(program: str, grid):
                        key = (_sha_bytes(program.encode()), _sha_json(grid))
                        if key not in cache:
                            cache[key] = _grid(apply(program, grid))
                        return cache[key]

                    for seed in execution_seeds:
                        for policy in policies:
                            settings = {"assignment_policy": policy}
                            episode = prototype.generate(
                                seed, settings, demos=execution_demos, queries=queries
                            )
                            pairs = _pairs(episode)
                            selected_program = prototype.program(settings)
                            selected_outputs = [
                                execute(selected_program, pair["input"]) for pair in pairs
                            ]
                            if any(output != pair["output"]
                                   for output, pair in zip(selected_outputs, pairs, strict=True)):
                                raise AssertionError(
                                    f"selected protected-Racket label mismatch: {seed} {policy}"
                                )
                            for name, rival_program in programs.items():
                                racket_outputs = [
                                    execute(rival_program, pair["input"]) for pair in pairs
                                ]
                                python_outputs = [
                                    rivals.output(prototype, pair["input"], name)
                                    for pair in pairs
                                ]
                                for index, (actual, expected) in enumerate(
                                    zip(racket_outputs, python_outputs, strict=True)
                                ):
                                    if actual != expected:
                                        report["racket_parity_failures"].append({
                                            "seed": seed,
                                            "selected": policy,
                                            "rival": name,
                                            "pair_index": index,
                                            "input_sha256": _sha_json(pairs[index]["input"]),
                                            "expected_sha256": _sha_json(expected),
                                            "actual_sha256": _sha_json(actual),
                                        })
                                demo_match = all(
                                    racket_outputs[index] == selected_outputs[index]
                                    for index in range(execution_demos)
                                )
                                query_disagreement = any(
                                    racket_outputs[execution_demos + index]
                                    != selected_outputs[execution_demos + index]
                                    for index in range(queries)
                                )
                                if demo_match and query_disagreement:
                                    report["harmful_survivors"].append({
                                        "backend": "protected_racket",
                                        "seed": seed,
                                        "demos": execution_demos,
                                        "queries": queries,
                                        "selected": policy,
                                        "rival": name,
                                    })
                                case_key = f"{policy}:{name}"
                                if case_key not in report["minimal_racket_cases"]:
                                    for index in range(execution_demos):
                                        if racket_outputs[index] != selected_outputs[index]:
                                            pair = pairs[index]
                                            report["minimal_racket_cases"][case_key] = {
                                                "seed": seed,
                                                "split": "train",
                                                "pair_index": index,
                                                "selected": policy,
                                                "rival": name,
                                                "description": rivals.DESCRIPTIONS[name],
                                                "selected_program_sha256": _sha_bytes(
                                                    selected_program.encode()
                                                ),
                                                "rival_program_sha256": _sha_bytes(
                                                    rival_program.encode()
                                                ),
                                                "input": pair["input"],
                                                "selected_racket_output": selected_outputs[index],
                                                "rival_racket_output": racket_outputs[index],
                                            }
                                            break
                finally:
                    if bridge is not None:
                        bridge.close()
            report["racket_evaluations"] = len(cache)
            if report["racket_parity_failures"]:
                raise AssertionError(
                    f"{len(report['racket_parity_failures'])} rival Racket/Python parity failures"
                )
            if report["harmful_survivors"]:
                raise AssertionError("protected-Racket harmful rival survived")

    except Exception as error:
        report["failures"].append({
            "type": type(error).__name__,
            "message": str(error),
        })

    report["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    report["status"] = "passed" if not report["failures"] else "failed"
    report["limits"] = (
        "Only the listed rivals, requested seeds/counts, and generated grammar were checked. "
        "A demo survivor is harmless here only when it agrees on every retained query."
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sampler-seeds", type=int, default=64)
    parser.add_argument("--execution-seed", type=int, action="append")
    parser.add_argument("--demo-count", type=int, action="append")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("choose a fresh output directory")
    if not 1 <= args.sampler_seeds <= 4096:
        parser.error("--sampler-seeds must be in 1..4096")
    execution_seeds = tuple(args.execution_seed or (0, 17))
    demo_counts = tuple(args.demo_count or (2, 3, 6))
    report = run_bounded(
        sampler_seeds=range(args.sampler_seeds),
        execution_seeds=execution_seeds,
        demo_counts=demo_counts,
        queries=args.queries,
        execute_racket=not args.no_racket,
    )
    args.out.mkdir(parents=True)
    (args.out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "status": report["status"],
        "sampler_requests": report["sampler_requests"],
        "sampler_input_count": report["sampler_input_count"],
        "racket_evaluations": report["racket_evaluations"],
        "harmful_survivors": len(report["harmful_survivors"]),
        "racket_parity_failures": len(report["racket_parity_failures"]),
        "failures": report["failures"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
