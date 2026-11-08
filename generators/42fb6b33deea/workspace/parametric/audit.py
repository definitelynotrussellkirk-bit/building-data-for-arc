"""Reusable bounded self-audit for the 42fb6b33deea parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"


def _load_prototype():
    name = "parametric_42fb6b33deea_audit_source"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load_prototype()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _exact_int_tuple(name: str, values: Iterable[int], low: int, high: int) -> tuple[int, ...]:
    result = tuple(values)
    if not result or any(type(value) is not int or not low <= value <= high for value in result):
        raise ValueError(f"{name} must contain exact integers in {low}..{high}")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must be distinct")
    return result


def _record_failure(failures: list[dict[str, Any]], kind: str, **context: Any) -> None:
    failures.append({"kind": kind, **context})


def build_audit(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 6),
    query_counts: Iterable[int] = (1, 4),
    execute_racket: bool = True,
) -> dict[str, Any]:
    seeds = _exact_int_tuple("seeds", seeds, 0, 2**63 - 1)
    demo_counts = _exact_int_tuple("demo_counts", demo_counts, 2, 6)
    query_counts = _exact_int_tuple("query_counts", query_counts, 1, 4)
    if type(execute_racket) is not bool:
        raise TypeError("execute_racket must be bool")

    failures: list[dict[str, Any]] = []
    totals = {
        "seeds": len(seeds),
        "requests": 0,
        "episodes": 0,
        "labeled_pairs": 0,
        "matched_input_requests": 0,
        "stress_30x30_episodes": 0,
        "racket_evaluations": 0,
    }
    finite_survivors: dict[str, dict[str, list[str]]] = {}
    runtime_identity: dict[str, Any] | None = None

    bridge = None
    wrapped: dict[str, str] = {}
    if execute_racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
        runtime_identity = {
            key: value
            for key, value in bridge.runtime_identity.items()
            if key in {
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            }
        }
        if runtime_identity.get("backend") != "racket" or runtime_identity.get("protected") is not True:
            bridge.close()
            raise RuntimeError("audit requires protected Racket")
        wrapped = {
            name: wrap_rule(P.candidate_program(name))
            for name in P.CANDIDATE_POLICIES
        }

    def execute(name: str, grid: list[list[int]]) -> list[list[int]]:
        assert bridge is not None
        totals["racket_evaluations"] += 1
        return bridge.eval_text(f"({wrapped[name]} {_literal(grid)})")

    try:
        for seed in seeds:
            base = P.episode_inputs(seed, demos=2, queries=4)
            finite_survivors[str(seed)] = {}
            racket_demo_outputs: dict[str, list[list[list[int]]]] = {}
            if execute_racket:
                for candidate in P.CANDIDATE_POLICIES:
                    outputs = []
                    for grid in base["train"]:
                        output = execute(candidate, grid)
                        python_output = P.solve_candidate(grid, candidate)
                        if output != python_output:
                            _record_failure(
                                failures,
                                "racket_candidate_mismatch",
                                seed=seed,
                                candidate=candidate,
                            )
                        outputs.append(output)
                    racket_demo_outputs[candidate] = outputs

            for chosen in P.FILL_POLICIES:
                labels = [P.solve(grid, chosen) for grid in base["train"]]
                survivors = [
                    candidate
                    for candidate in P.CANDIDATE_POLICIES
                    if all(
                        P.solve_candidate(grid, candidate) == expected
                        for grid, expected in zip(base["train"], labels)
                    )
                ]
                finite_survivors[str(seed)][chosen] = survivors
                if survivors != [chosen]:
                    _record_failure(
                        failures,
                        "finite_rival_survivor",
                        seed=seed,
                        chosen=chosen,
                        survivors=survivors,
                    )
                if execute_racket:
                    racket_survivors = [
                        candidate
                        for candidate, outputs in racket_demo_outputs.items()
                        if outputs == labels
                    ]
                    if racket_survivors != [chosen]:
                        _record_failure(
                            failures,
                            "racket_finite_rival_survivor",
                            seed=seed,
                            chosen=chosen,
                            survivors=racket_survivors,
                        )

            if execute_racket:
                # Check every supported slot once per setting, including 30x30.
                for chosen in P.FILL_POLICIES:
                    episode = P.generate_episode(seed, chosen, demos=6, queries=4)
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            if execute(chosen, pair["input"]) != pair["output"]:
                                _record_failure(
                                    failures,
                                    "racket_label_mismatch",
                                    seed=seed,
                                    chosen=chosen,
                                    split=split,
                                )

            for demos in demo_counts:
                for queries in query_counts:
                    totals["requests"] += 1
                    episodes = {
                        policy: P.generate_episode(seed, policy, demos=demos, queries=queries)
                        for policy in P.FILL_POLICIES
                    }
                    totals["episodes"] += len(episodes)
                    totals["labeled_pairs"] += len(episodes) * (demos + queries)
                    input_lists = [
                        [
                            pair["input"]
                            for split in ("train", "test")
                            for pair in episode[split]
                        ]
                        for episode in episodes.values()
                    ]
                    if input_lists[1:] == input_lists[:-1]:
                        totals["matched_input_requests"] += 1
                    else:
                        _record_failure(
                            failures,
                            "settings_input_confound",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    if len({_freeze(grid) for grid in input_lists[0]}) != demos + queries:
                        _record_failure(
                            failures,
                            "duplicate_visible_input",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    full = P.generate_episode(seed, P.DEFAULT_POLICY, demos=6, queries=4)
                    current = episodes[P.DEFAULT_POLICY]
                    if current["train"] != full["train"][:demos] or current["test"] != full["test"][:queries]:
                        _record_failure(
                            failures,
                            "prefix_instability",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    one_query = P.generate_episode(seed, P.DEFAULT_POLICY, demos=demos, queries=1)
                    if P.public_view(current, 0) != P.public_view(one_query, 0):
                        _record_failure(
                            failures,
                            "first_turn_instability",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    public = P.public_view(current, 0)
                    if set(public) != {"train", "test"} or set(public["test"][0]) != {"input"}:
                        _record_failure(
                            failures,
                            "public_projection_leak",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    if queries == 4:
                        for episode in episodes.values():
                            grid = episode["test"][3]["input"]
                            if len(grid) == 30 and len(grid[0]) == 30:
                                totals["stress_30x30_episodes"] += 1
                            else:
                                _record_failure(
                                    failures,
                                    "missing_30x30_stress",
                                    seed=seed,
                                    demos=demos,
                                )
    finally:
        if bridge is not None:
            bridge.close()

    report = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": P.TASK_ID,
        "status": "passed" if not failures else "failed",
        "settings": list(P.FILL_POLICIES),
        "finite_candidates": list(P.CANDIDATE_POLICIES),
        "finite_rival_survivors": finite_survivors,
        "totals": totals,
        "racket": runtime_identity if runtime_identity is not None else {"executed": False},
        "failures": failures,
        "source": {
            path.name: _sha256(path)
            for path in (
                PROTOTYPE_PATH,
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "selector_area_gate.rkt",
                Path(__file__).resolve(),
            )
        },
        "limits": (
            "Finite authored seeds/count boundaries and declared rivals only; "
            "this is not universal identifiability or measured training gain."
        ),
        "training_admitted": False,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    report = build_audit(seeds=args.seeds, execute_racket=not args.no_racket)
    output = Path(args.out)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "output": str(output),
        "totals": report["totals"],
        "failures": len(report["failures"]),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
