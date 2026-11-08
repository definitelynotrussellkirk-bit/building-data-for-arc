#!/usr/bin/env python3
"""Bounded lesson, export, sampler, and protected-Racket audit.

Run from the packet outer directory::

    python3 review.py run python3 \
      generators/17b0b2791dd2/workspace/parametric/audit.py \
      --out ../checks/17b0b2791dd2/self-audit

Passing means that no rule in the finite ``rivals.py`` inventory fit every
visible demonstration while changing a retained query for the requested
seeds/counts. It is not a universal uniqueness, owner-acceptance, or training
claim.
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
    spec = importlib.util.spec_from_file_location(f"_p17b0_audit_{name}", path)
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
        HERE.parents[1] / "tests" / "test_parametric_17b0b2791dd2.py",
        ROOT / "src" / "arcpuzzles" / "parametric_worker.py",
    ]
    return {
        str(path.relative_to(ROOT)): _sha_bytes(path.read_bytes())
        for path in paths
    }


def _pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def run_bounded(
    *,
    sampler_seeds: Iterable[int] = range(8),
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
    if not demo_counts or any(type(value) is not int or not 2 <= value <= 6 for value in demo_counts):
        raise ValueError("demo_counts must contain exact integers in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    if type(execute_racket) is not bool:
        raise ValueError("execute_racket must be bool")

    started = time.perf_counter()
    policies = tuple(prototype.POLICIES)
    report = {
        "schema": "17b0b2791dd2-nearest-horizontal-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "running",
        "scope": (
            "Finite explicit shortcut inventory; bounded seed census at minimum, "
            "ordinary, and maximum demo counts; four sequential queries; protected-"
            "Racket parity on selected official programs. No universal uniqueness."
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
        "input_sizes": set(),
        "selector_counts": set(),
        "candidate_counts": set(),
        "harmful_survivors": [],
        "public_projection_failures": [],
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
                        seed,
                        {"target_policy": policy},
                        demos=demos,
                        queries=queries,
                    )
                    for policy in policies
                }
                sequences = [_inputs(episodes[policy]) for policy in policies]
                if any(sequence != sequences[0] for sequence in sequences[1:]):
                    raise AssertionError(f"setting-dependent inputs: seed={seed} demos={demos}")

                for policy, episode in episodes.items():
                    pairs = _pairs(episode)
                    serialized = [
                        json.dumps(pair["input"], separators=(",", ":"))
                        for pair in pairs
                    ]
                    if len(serialized) != len(set(serialized)):
                        raise AssertionError(
                            f"duplicate input: seed={seed} demos={demos} policy={policy}"
                        )
                    if len(episode["train"]) != demos or len(episode["test"]) != queries:
                        raise AssertionError("requested split count changed")

                    other = policies[1 - policies.index(policy)]
                    if all(
                        prototype.solve(pair["input"], {"target_policy": other})
                        == pair["output"]
                        for pair in episode["train"]
                    ):
                        raise AssertionError(
                            f"official alternative survived demos: {seed=} {demos=} {policy=}"
                        )

                    for pair in pairs:
                        grid = pair["input"]
                        facts = prototype.observables(grid)
                        report["input_sizes"].add((len(grid), len(grid[0])))
                        report["selector_counts"].add(facts["selector_count"])
                        report["candidate_counts"].add(facts["candidate_count"])
                    for name in rivals.NAMES:
                        predicted = [
                            rivals.output(prototype, pair["input"], name)
                            for pair in pairs
                        ]
                        demo_match = all(
                            predicted[index] == pair["output"]
                            for index, pair in enumerate(episode["train"])
                        )
                        query_disagreement = any(
                            predicted[demos + index] != pair["output"]
                            for index, pair in enumerate(episode["test"])
                        )
                        if demo_match and query_disagreement:
                            report["harmful_survivors"].append(
                                {
                                    "seed": seed,
                                    "demos": demos,
                                    "selected": policy,
                                    "rival": name,
                                }
                            )

                    for query_index in range(queries):
                        try:
                            public = prototype.public_challenge(episode, query_index)
                            if set(public) != {"train", "test"}:
                                raise AssertionError("unexpected public keys")
                            if public["train"] != episode["train"]:
                                raise AssertionError("demonstrations changed")
                            if public["test"] != [
                                {"input": episode["test"][query_index]["input"]}
                            ]:
                                raise AssertionError("query projection changed")
                            visible = json.dumps(public, sort_keys=True, separators=(",", ":"))
                            forbidden = (
                                "target_policy",
                                "program_solution",
                                json.dumps(
                                    episode["test"][query_index]["output"],
                                    separators=(",", ":"),
                                ),
                            )
                            if any(token in visible for token in forbidden):
                                raise AssertionError("private value leaked")
                        except Exception as error:
                            report["public_projection_failures"].append(
                                {
                                    "seed": seed,
                                    "demos": demos,
                                    "selected": policy,
                                    "query_index": query_index,
                                    "type": type(error).__name__,
                                    "message": str(error),
                                }
                            )

                    report["sampler_requests"] += 1
                    report["sampler_input_count"] += len(pairs)

        if report["harmful_survivors"]:
            raise AssertionError(
                f"{len(report['harmful_survivors'])} finite rivals fit demos and changed queries"
            )
        if report["public_projection_failures"]:
            raise AssertionError(
                f"{len(report['public_projection_failures'])} public projections failed"
            )

        if execute_racket:
            runtime = ROOT / "shared" / "runtime"
            cache: dict[tuple[str, str], list[list[int]]] = {}
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
                            settings = {"target_policy": policy}
                            episode = prototype.generate(
                                seed,
                                settings,
                                demos=min(demo_counts),
                                queries=queries,
                            )
                            selected_program = prototype.program(settings)
                            other = policies[1 - policies.index(policy)]
                            other_program = prototype.program({"target_policy": other})
                            for pair_index, pair in enumerate(_pairs(episode)):
                                actual = execute(selected_program, pair["input"])
                                if actual != pair["output"]:
                                    report["racket_parity_failures"].append(
                                        {
                                            "seed": seed,
                                            "selected": policy,
                                            "pair_index": pair_index,
                                            "input_sha256": _sha_json(pair["input"]),
                                            "expected_sha256": _sha_json(pair["output"]),
                                            "actual_sha256": _sha_json(actual),
                                        }
                                    )
                            if policy not in report["minimal_racket_cases"]:
                                for pair_index, pair in enumerate(episode["train"]):
                                    selected_output = execute(selected_program, pair["input"])
                                    other_output = execute(other_program, pair["input"])
                                    if selected_output != other_output:
                                        report["minimal_racket_cases"][policy] = {
                                            "seed": seed,
                                            "split": "train",
                                            "pair_index": pair_index,
                                            "settings": settings,
                                            "selected_program_sha256": _sha_bytes(
                                                selected_program.encode()
                                            ),
                                            "other_program_sha256": _sha_bytes(
                                                other_program.encode()
                                            ),
                                            "input": pair["input"],
                                            "selected_racket_output": selected_output,
                                            "other_racket_output": other_output,
                                        }
                                        break
                finally:
                    if bridge is not None:
                        bridge.close()
            report["racket_evaluations"] = len(cache)
            if report["racket_parity_failures"]:
                raise AssertionError(
                    f"{len(report['racket_parity_failures'])} protected-Racket parity failures"
                )
            if set(report["minimal_racket_cases"]) != set(policies):
                raise AssertionError("missing protected-Racket setting distinction case")

    except Exception as error:
        report["failures"].append(
            {"type": type(error).__name__, "message": str(error)}
        )

    report["input_sizes"] = [list(value) for value in sorted(report["input_sizes"])]
    report["selector_counts"] = sorted(report["selector_counts"])
    report["candidate_counts"] = sorted(report["candidate_counts"])
    report["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    report["status"] = "passed" if not report["failures"] else "failed"
    report["limits"] = (
        "Only the listed rivals, requested seeds/counts, generated grammar, and "
        "selected protected-Racket executions were checked."
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sampler-seeds", type=int, default=8)
    parser.add_argument("--execution-seed", type=int, action="append")
    parser.add_argument("--demo-count", type=int, action="append")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("choose a fresh output directory")
    if not 1 <= args.sampler_seeds <= 4096:
        parser.error("--sampler-seeds must be in 1..4096")
    report = run_bounded(
        sampler_seeds=range(args.sampler_seeds),
        execution_seeds=tuple(args.execution_seed or (0, 17)),
        demo_counts=tuple(args.demo_count or (2, 3, 6)),
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
        "public_projection_failures": len(report["public_projection_failures"]),
        "racket_parity_failures": len(report["racket_parity_failures"]),
        "failures": report["failures"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
