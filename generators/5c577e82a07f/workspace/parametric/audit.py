#!/usr/bin/env python3
"""Reusable bounded audit for the 5c577e82a07f enclosure family.

The Python sweep covers supported count prefixes, matched inputs, uniqueness of
the completed-grid enclosure selector, and the declared finite rival bank.  The
optional protected-Racket pass independently executes both declared programs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

HERE = Path(__file__).resolve().parent


def _load_adjacent(filename: str, stem: str):
    path = HERE / filename
    name = f"_{stem}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load_adjacent("prototype.py", "enclosure_prototype")
adapter = _load_adjacent("adapter.py", "enclosure_adapter")


def _key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def run_python_sweep(
    *,
    seeds: Iterable[int],
    demo_counts: Iterable[int] = range(2, 7),
    query_counts: Iterable[int] = range(1, 5),
) -> dict:
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    query_counts = tuple(query_counts)
    report = {
        "schema": "arcpuzzles-parametric-enclosure-audit-v1",
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "query_counts": list(query_counts),
        "episodes": 0,
        "pairs": 0,
        "matched_input_comparisons": 0,
        "prefix_checks": 0,
        "topology_checks": 0,
        "rival_checks": 0,
        "generation_failures": [],
        "rival_failures": [],
    }
    for seed in seeds:
        cache = {}
        for demos in demo_counts:
            for queries in query_counts:
                for policy in adapter.POLICIES:
                    try:
                        episode = adapter.generate(
                            seed,
                            {"enclosure_policy": policy},
                            demos=demos,
                            queries=queries,
                        )
                        cache[(policy, demos, queries)] = episode
                        report["episodes"] += 1
                        report["pairs"] += demos + queries
                        keys = [_key(grid) for grid in _inputs(episode)]
                        if len(keys) != len(set(keys)):
                            raise AssertionError("duplicate episode input")
                        for pair in episode["train"] + episode["test"]:
                            analysis = prototype.analyze_after_borders(pair["input"])
                            report["topology_checks"] += 1
                            if len(analysis["enclosed_regions"]) < 2 or not analysis["unique_largest"]:
                                raise AssertionError("missing unique multi-region enclosure topology")
                            if prototype.solve(pair["input"], policy) != pair["output"]:
                                raise AssertionError("Python label claim mismatch")
                    except Exception as exc:  # retained in the bounded report
                        report["generation_failures"].append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "queries": queries,
                                "policy": policy,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                left = cache.get(("borders_only", demos, queries))
                right = cache.get(("largest_enclosure", demos, queries))
                if left is not None and right is not None:
                    report["matched_input_comparisons"] += 1
                    if _inputs(left) != _inputs(right):
                        report["generation_failures"].append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "queries": queries,
                                "error": "settings received different inputs",
                            }
                        )

        for policy in adapter.POLICIES:
            # These checks are intentionally exactly two per seed/setting.
            low_train = cache.get((policy, min(demo_counts), max(query_counts)))
            high_train = cache.get((policy, max(demo_counts), max(query_counts)))
            low_query = cache.get((policy, max(demo_counts), min(query_counts)))
            if low_train is not None and high_train is not None:
                report["prefix_checks"] += 1
                if low_train["train"] != high_train["train"][: min(demo_counts)]:
                    report["generation_failures"].append(
                        {"seed": seed, "policy": policy, "error": "demo prefix drift"}
                    )
            if low_query is not None and high_train is not None:
                report["prefix_checks"] += 1
                if low_query["test"] != high_train["test"][: min(query_counts)]:
                    report["generation_failures"].append(
                        {"seed": seed, "policy": policy, "error": "query prefix drift"}
                    )
            teaching = cache.get((policy, min(demo_counts), max(query_counts)))
            if teaching is not None:
                report["rival_checks"] += len(prototype.RIVALS[policy])
                survivors = prototype.surviving_rivals(teaching["train"], policy)
                if survivors:
                    report["rival_failures"].append(
                        {"seed": seed, "policy": policy, "survivors": survivors}
                    )
    return report


def _rule_application(source: str, grid) -> str:
    from puzzle_generators.rule_wrap import wrap_rule

    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"({wrap_rule(source)} '({rows}))"


def run_racket_audit(*, seeds=(0, 17, 41), demos=3, queries=4) -> dict:
    from arc_repl.racket_bridge import RacketBridge

    result = {
        "seeds": list(seeds),
        "demos": demos,
        "queries": queries,
        "evaluations": 0,
        "failures": [],
        "program_sha256": {},
    }
    with RacketBridge(timeout=20, startup_timeout=60, max_calls_before_restart=96) as bridge:
        for policy in adapter.POLICIES:
            source = adapter.program({"enclosure_policy": policy})
            result["program_sha256"][policy] = hashlib.sha256(source.encode()).hexdigest()
            for seed in seeds:
                episode = adapter.generate(seed, {"enclosure_policy": policy}, demos, queries)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        result["evaluations"] += 1
                        try:
                            observed = bridge.eval_text(_rule_application(source, pair["input"]))
                            if observed != pair["output"]:
                                raise AssertionError("protected Racket output differs from claim")
                        except Exception as exc:
                            result["failures"].append(
                                {
                                    "policy": policy,
                                    "seed": seed,
                                    "split": split,
                                    "index": index,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )
    return result


def _public_projection(episode):
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def write_evidence(out: Path, *, stress_seeds: int = 50) -> dict:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    public_dir = out / "public"
    public_dir.mkdir()

    python_report = run_python_sweep(seeds=range(stress_seeds))
    racket_report = run_racket_audit()
    public_rows = []
    for policy in adapter.POLICIES:
        episode = adapter.generate(0, {"enclosure_policy": policy}, demos=3, queries=4)
        public = _public_projection(episode)
        public_id = public_challenge_id(public)
        path = public_dir / f"{public_id}.json"
        path.write_bytes(public_challenge_bytes(public))
        public_rows.append(
            {
                "policy": policy,
                "public_id": public_id,
                "path": path.relative_to(out).as_posix(),
                "bytes_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )

    report = {
        "schema": "arcpuzzles-parametric-enclosure-evidence-v1",
        "status": "pass"
        if not python_report["generation_failures"]
        and not python_report["rival_failures"]
        and not racket_report["failures"]
        else "fail",
        "python_sweep": python_report,
        "protected_racket": racket_report,
        "public_challenges": public_rows,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(HERE.glob("*"))
            if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
        },
        "finite_scope": (
            "The rival result covers only the declared executable bank and the listed seeds/counts; "
            "it is not a proof of unrestricted hypothesis uniqueness."
        ),
    }
    (out / "audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stress-seeds", type=int, default=50)
    args = parser.parse_args(argv)
    if not 1 <= args.stress_seeds <= 500:
        parser.error("--stress-seeds must be in 1..500")
    report = write_evidence(args.out, stress_seeds=args.stress_seeds)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": report["python_sweep"]["episodes"],
                "pairs": report["python_sweep"]["pairs"],
                "racket_evaluations": report["protected_racket"]["evaluations"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
