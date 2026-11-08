"""Bounded structural and protected-Racket self-review for this native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable, Any

HOME = Path(__file__).resolve().parent


def _load_family():
    path = HOME / "family.py"
    name = "_ab8_audit_family_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run(*, seeds: Iterable[int] = range(32), protected: bool = True) -> dict[str, Any]:
    family = _load_family()
    seed_values = list(seeds)
    episodes = 0
    pairs = 0
    survivors: list[dict[str, Any]] = []
    rank_failures: list[dict[str, Any]] = []
    public_failures: list[dict[str, Any]] = []
    protected_failures: list[dict[str, Any]] = []
    racket_evaluations = 0

    bridge = None
    wrap_rule = None
    runtime = None
    if protected:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule as wrapper
        bridge = RacketBridge(max_calls_before_restart=128)
        wrap_rule = wrapper
        runtime = bridge.runtime_identity

    try:
        for seed in seed_values:
            for finish in family.SETTINGS:
                settings = {family.PARAMETER: finish}
                episode = family.generate(seed, settings, 6, 4)
                episodes += 1
                all_pairs = episode["train"] + episode["test"]
                pairs += len(all_pairs)
                teaching = family.teaching_check(episode)
                if teaching["surviving_rivals"]:
                    survivors.append({"seed": seed, "finish": finish, "rivals": teaching["surviving_rivals"]})
                for pair_index, pair in enumerate(all_pairs):
                    trace = family.dependency_trace(pair["input"])
                    if not (
                        trace["source_largest_size"] < trace["landed_largest_size"]
                        and trace["source_largest_cells"] != trace["landed_largest_cells"]
                        and trace["landed_largest_unique"]
                    ):
                        rank_failures.append({"seed": seed, "finish": finish, "pair": pair_index, "trace": trace})
                for query_index in range(4):
                    public = family.public_turn(episode, query_index)
                    expected_train = [
                        {"input": pair["input"], "output": pair["output"]}
                        for pair in episode["train"]
                    ]
                    expected_query = [{"input": episode["test"][query_index]["input"]}]
                    if set(public) != {"train", "test"} or public["train"] != expected_train or public["test"] != expected_query:
                        public_failures.append({"seed": seed, "finish": finish, "query": query_index})

                if bridge is not None and wrap_rule is not None:
                    selected = wrap_rule(family.program(settings))
                    for pair_index, pair in enumerate(episode["train"][:2] + episode["test"]):
                        observed = bridge.eval_text(f"({selected} {_literal(pair['input'])})")
                        racket_evaluations += 1
                        if observed != pair["output"]:
                            protected_failures.append({"seed": seed, "finish": finish, "pair": pair_index, "kind": "selected"})
                    if finish == "mark_largest_landed_cluster":
                        wrong = wrap_rule((HOME / "wrong_order.rkt").read_text(encoding="utf-8"))
                        case = episode["test"][3]
                        observed = bridge.eval_text(f"({wrong} {_literal(case['input'])})")
                        racket_evaluations += 1
                        if observed != family.wrong_order_solve(case["input"]) or observed == case["output"]:
                            protected_failures.append({"seed": seed, "finish": finish, "pair": 3, "kind": "wrong_order"})
    finally:
        if bridge is not None:
            bridge.close()

    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": family.TASK_ID,
        "seeds": seed_values,
        "settings": list(family.SETTINGS),
        "episodes": episodes,
        "pairs": pairs,
        "harmful_survivors": survivors,
        "rank_inversion_failures": rank_failures,
        "public_projection_failures": public_failures,
        "protected_failures": protected_failures,
        "racket_evaluations": racket_evaluations,
        "racket": runtime,
        "status": "passed" if not (survivors or rank_failures or public_failures or protected_failures) else "failed",
        "limits": "Finite authored seeds and declared rivals; this is not a proof of unique induction.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32, help="audit seeds 0..N-1")
    parser.add_argument("--no-racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run(seeds=range(args.seeds), protected=not args.no_racket)
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
