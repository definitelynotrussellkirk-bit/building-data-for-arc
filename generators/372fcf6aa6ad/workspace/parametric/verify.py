#!/usr/bin/env python3
"""Bounded self-review for the 372fcf6aa6ad native parametric family."""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_adapter():
    spec = spec_from_file_location("_verify_adapter_372", HERE / "adapter.py")
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run_audit(*, seed_start: int = 0, seed_count: int = 32, racket_seed_count: int = 2) -> dict[str, Any]:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative integer")
    if type(seed_count) is not int or seed_count < 1:
        raise ValueError("seed_count must be positive")
    if type(racket_seed_count) is not int or not 0 <= racket_seed_count <= seed_count:
        raise ValueError("racket_seed_count must be in 0..seed_count")

    module = _load_adapter()
    lesson_failures = []
    selector_values: set[int] = set()
    episodes = 0
    rival_checks = 0
    thirty_cases = 0
    for seed in range(seed_start, seed_start + seed_count):
        for mode in module.MODES:
            episode = module.generate(seed, {"mode": mode}, 3, 4)
            episodes += 1
            cert = module.certificate(episode["train"], [p["input"] for p in episode["test"]])
            rival_checks += len(module.HYPOTHESES) - 1
            if cert["survivors"] != [mode] or cert["query_changing_survivors"]:
                lesson_failures.append({"seed": seed, "mode": mode, "certificate": cert})
            for pair in episode["train"] + episode["test"]:
                selector_values.add(module.explain_dependency(pair["input"])["selector"])
            large = episode["test"][3]["input"]
            if (len(large), len(large[0])) == (30, 30):
                thirty_cases += 1

    racket_failures = []
    racket_evaluations = 0
    if racket_seed_count:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        with RacketBridge(timeout=20) as bridge:
            for seed in range(seed_start, seed_start + racket_seed_count):
                for mode in module.MODES:
                    episode = module.generate(seed, {"mode": mode}, 3, 4)
                    source = module.program({"mode": mode})
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = bridge.eval_text(f"({wrap_rule(source)} {_literal(pair['input'])})")
                            racket_evaluations += 1
                            if actual != pair["output"]:
                                racket_failures.append({"seed": seed, "mode": mode, "split": split, "index": index})
                relay = module.generate(seed, {"mode": "winner_width_relay"}, 3, 4)
                witness = next(
                    pair for pair in relay["test"] + relay["train"]
                    if module.explain_dependency(pair["input"])["selector"]
                    != module.explain_dependency(pair["input"])["counterfactual_selector"]
                )
                wrong = bridge.eval_text(
                    f"({wrap_rule(module.counterfactual_program())} {_literal(witness['input'])})"
                )
                racket_evaluations += 1
                if wrong == witness["output"]:
                    racket_failures.append({"seed": seed, "mode": "counterfactual", "reason": "unchanged output"})

    passed = not lesson_failures and not racket_failures and selector_values == {1, 2, 3}
    return {
        "schema": "arcpuzzles-parametric-authoring-audit-v1",
        "task_id": "372fcf6aa6ad",
        "status": "passed" if passed else "failed",
        "seed_start": seed_start,
        "seed_count": seed_count,
        "episodes": episodes,
        "named_rival_checks": rival_checks,
        "selector_values": sorted(selector_values),
        "substantive_30x30_cases": thirty_cases,
        "lesson_failures": lesson_failures,
        "racket_seed_count": racket_seed_count,
        "racket_evaluations": racket_evaluations,
        "racket_failures": racket_failures,
        "limits": "Finite named-rival and sampled-seed audit; not a universal uniqueness proof.",
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--racket-seed-count", type=int, default=2)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        racket_seed_count=args.racket_seed_count,
    )
    if args.out:
        write_report(args.out, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
