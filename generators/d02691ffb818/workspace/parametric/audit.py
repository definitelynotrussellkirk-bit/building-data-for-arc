"""Reusable bounded self-audit for d02691ffb818's parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"
_NAME = "parametric_d02691ffb818_audit_source"


def _load():
    module = sys.modules.get(_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_NAME, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_NAME] = module
    spec.loader.exec_module(module)
    return module


P = _load()


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _failure(rows: list[dict[str, Any]], kind: str, **details: Any) -> None:
    rows.append({"kind": kind, **details})


def build_audit(
    *,
    seeds: tuple[int, ...] = (0, 17),
    demo_counts: tuple[int, ...] = (2, 3, 6),
    query_counts: tuple[int, ...] = (1, 4),
    execute_racket: bool = True,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    survivors: dict[str, dict[str, list[str]]] = {}
    totals = {
        "seeds": len(seeds),
        "requests": 0,
        "episodes": 0,
        "labeled_pairs": 0,
        "matched_input_requests": 0,
        "stress_30x30_episodes": 0,
        "racket_evaluations": 0,
    }
    bridge = None
    wrapped: dict[str, str] = {}
    runtime = {"executed": False}
    if execute_racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
        runtime = bridge.runtime_identity
        wrapped = {name: wrap_rule(P.candidate_program(name)) for name in P.CANDIDATE_RULES}

    def execute(name: str, grid):
        if bridge is None:
            return P.solve_candidate(grid, name)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        totals["racket_evaluations"] += 1
        return bridge.eval_text(f"({wrapped[name]} {literal})")

    try:
        for seed in seeds:
            base = P.episode_inputs(seed, demos=2, queries=4)
            survivors[str(seed)] = {}
            racket_outputs: dict[str, list[Any]] = {}
            if execute_racket:
                for candidate in P.CANDIDATE_RULES:
                    outputs = []
                    for grid in base["train"]:
                        output = execute(candidate, grid)
                        expected = P.solve_candidate(grid, candidate)
                        if output != expected:
                            _failure(failures, "racket_candidate_mismatch", seed=seed, candidate=candidate)
                        outputs.append(output)
                    racket_outputs[candidate] = outputs
            for chosen in P.RADIUS_RULES:
                labels = [P.solve(grid, chosen) for grid in base["train"]]
                names = [
                    candidate
                    for candidate in P.CANDIDATE_RULES
                    if all(
                        P.solve_candidate(grid, candidate) == expected
                        for grid, expected in zip(base["train"], labels)
                    )
                ]
                survivors[str(seed)][chosen] = names
                if names != [chosen]:
                    _failure(failures, "finite_rival_survivor", seed=seed, chosen=chosen, survivors=names)
                if execute_racket:
                    racket_names = [name for name, outputs in racket_outputs.items() if outputs == labels]
                    if racket_names != [chosen]:
                        _failure(failures, "racket_finite_rival_survivor", seed=seed, chosen=chosen, survivors=racket_names)

            if execute_racket:
                for chosen in P.RADIUS_RULES:
                    episode = P.generate_episode(seed, chosen, demos=6, queries=4)
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            output = execute(chosen, pair["input"])
                            if output != pair["output"]:
                                _failure(failures, "racket_label_mismatch", seed=seed, chosen=chosen, split=split)

            for demos in demo_counts:
                for queries in query_counts:
                    totals["requests"] += 1
                    episodes = {
                        rule: P.generate_episode(seed, rule, demos=demos, queries=queries)
                        for rule in P.RADIUS_RULES
                    }
                    totals["episodes"] += len(episodes)
                    totals["labeled_pairs"] += len(episodes) * (demos + queries)
                    input_lists = [
                        [pair["input"] for split in ("train", "test") for pair in episode[split]]
                        for episode in episodes.values()
                    ]
                    if input_lists[1:] == input_lists[:-1]:
                        totals["matched_input_requests"] += 1
                    else:
                        _failure(failures, "settings_input_confound", seed=seed, demos=demos, queries=queries)
                    if len({_freeze(grid) for grid in input_lists[0]}) != demos + queries:
                        _failure(failures, "duplicate_visible_input", seed=seed, demos=demos, queries=queries)
                    full = P.generate_episode(seed, P.DEFAULT_RULE, demos=6, queries=4)
                    current = episodes[P.DEFAULT_RULE]
                    if current["train"] != full["train"][:demos] or current["test"] != full["test"][:queries]:
                        _failure(failures, "prefix_instability", seed=seed, demos=demos, queries=queries)
                    one = P.generate_episode(seed, P.DEFAULT_RULE, demos=demos, queries=1)
                    if P.public_view(current, 0) != P.public_view(one, 0):
                        _failure(failures, "first_turn_instability", seed=seed, demos=demos, queries=queries)
                    public = P.public_view(current, 0)
                    if set(public) != {"train", "test"} or set(public["test"][0]) != {"input"}:
                        _failure(failures, "public_projection_leak", seed=seed, demos=demos, queries=queries)
                    if queries == 4:
                        for episode in episodes.values():
                            grid = episode["test"][3]["input"]
                            if len(grid) == 30 and len(grid[0]) == 30:
                                totals["stress_30x30_episodes"] += 1
                            else:
                                _failure(failures, "missing_30x30_stress", seed=seed, demos=demos)
    finally:
        if bridge is not None:
            bridge.close()

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": P.TASK_ID,
        "status": "passed" if not failures else "failed",
        "settings": list(P.RADIUS_RULES),
        "finite_candidates": list(P.CANDIDATE_RULES),
        "finite_rival_survivors": survivors,
        "totals": totals,
        "racket": runtime,
        "failures": failures,
        "source": {
            path.name: _sha256(path)
            for path in (
                PROTOTYPE_PATH,
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "cue_satellite_count.rkt",
                Path(__file__).resolve(),
            )
        },
        "limits": (
            "Finite authored seeds/count boundaries and declared rivals only; "
            "this is not universal identifiability or measured training gain."
        ),
        "training_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    report = build_audit(seeds=tuple(args.seeds), execute_racket=not args.no_racket)
    output = Path(args.out)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output), "totals": report["totals"], "failures": len(report["failures"])}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
