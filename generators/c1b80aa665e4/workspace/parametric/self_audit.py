"""Bounded structural and protected-Racket audit for c1b80aa665e4."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

_SPEC = importlib.util.spec_from_file_location("_c1b80aa665e4_audit_proto", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load prototype")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PROTOTYPE
_SPEC.loader.exec_module(PROTOTYPE)


def _settings(policy: str) -> dict[str, str]:
    return {"isolation_policy": policy}


def _serialize(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def structural_audit(seeds: Iterable[int]) -> dict[str, Any]:
    seed_list = [int(seed) for seed in seeds]
    if not seed_list or len(seed_list) != len(set(seed_list)) or min(seed_list) < 0:
        raise ValueError("seeds must be distinct nonnegative integers")
    report: dict[str, Any] = {
        "schema": "arcpuzzles-c1b80aa665e4-structural-audit-v1",
        "status": "pass",
        "seeds": seed_list,
        "episodes": 0,
        "lesson_prefixes": 0,
        "rival_checks": 0,
        "teaching_gaps": [],
        "rival_errors": [],
        "stress_30x30": 0,
        "causal_cases": 0,
        "public_projection_checks": 0,
        "claim_scope": "finite named rivals and seeds only",
    }
    for seed in seed_list:
        episodes = {policy: PROTOTYPE.generate(seed, _settings(policy), 6, 4) for policy in PROTOTYPE.POLICIES}
        canonical_inputs = [p["input"] for p in episodes["all_isolated"]["train"] + episodes["all_isolated"]["test"]]
        alternate_inputs = [p["input"] for p in episodes["largest_cluster_color"]["train"] + episodes["largest_cluster_color"]["test"]]
        if canonical_inputs != alternate_inputs:
            raise AssertionError("settings do not share inputs")
        for policy, episode in episodes.items():
            report["episodes"] += 1
            pairs = episode["train"] + episode["test"]
            if len({_serialize(pair["input"]) for pair in pairs}) != len(pairs):
                raise AssertionError("duplicate input")
            for pair in pairs:
                if pair["output"] != PROTOTYPE.solve(pair["input"], policy):
                    raise AssertionError("Python label mismatch")
            for demos in range(2, 7):
                short = PROTOTYPE.generate(seed, _settings(policy), demos, 1)
                if short["train"] != episode["train"][:demos] or short["test"] != episode["test"][:1]:
                    raise AssertionError("prefix instability")
                labels = [pair["output"] for pair in short["train"]]
                for name, rival in PROTOTYPE.rivals_for(policy).items():
                    report["rival_checks"] += len(short["train"])
                    try:
                        predictions = [rival(pair["input"]) for pair in short["train"]]
                    except Exception as exc:
                        report["rival_errors"].append({"seed": seed, "policy": policy, "demos": demos, "rival": name, "error": repr(exc)})
                        continue
                    if predictions == labels:
                        report["teaching_gaps"].append({"seed": seed, "policy": policy, "demos": demos, "rival": name})
                report["lesson_prefixes"] += 1
            public = PROTOTYPE.public_turn(episode, 0)
            if set(public) != {"train", "test"} or len(public["test"]) != 1 or set(public["test"][0]) != {"input"}:
                raise AssertionError("public projection leak")
            report["public_projection_checks"] += 1
            stress = episode["test"][3]["input"]
            nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
            if [len(stress), len(stress[0])] != [30, 30] or len(nonzero) < 45 or len({r for r, _ in nonzero}) < 24 or len({c for _, c in nonzero}) < 24:
                raise AssertionError("insubstantial 30x30 stress")
            report["stress_30x30"] += 1
            if policy == "largest_cluster_color":
                if PROTOTYPE.solve(stress, policy) == PROTOTYPE.solve_with_smallest_cluster_color(stress):
                    raise AssertionError("causal counterfactual unchanged")
                report["causal_cases"] += 1
    if report["teaching_gaps"] or report["rival_errors"]:
        report["status"] = "fail"
    return report


def _racket_grid(grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def protected_audit(seeds: Iterable[int]) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    seed_list = [int(seed) for seed in seeds]
    report: dict[str, Any] = {
        "schema": "arcpuzzles-c1b80aa665e4-protected-audit-v1",
        "status": "pass",
        "seeds": seed_list,
        "jobs": [],
        "racket_evaluations": 0,
        "causal_counterfactuals": [],
    }
    wrong_program = (HERE / "smallest_cluster_color.rkt").read_text(encoding="utf-8")
    with RacketBridge() as bridge:
        report["racket"] = dict(bridge.runtime_identity)
        if report["racket"].get("backend") != "racket" or report["racket"].get("protected") is not True:
            raise RuntimeError("protected Racket required")

        def execute(program: str, grid):
            report["racket_evaluations"] += 1
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        for seed in seed_list:
            for policy in PROTOTYPE.POLICIES:
                episode = PROTOTYPE.generate(seed, _settings(policy), 6, 4)
                program = PROTOTYPE.program(_settings(policy))
                pairs = episode["train"] + episode["test"]
                labels = [execute(program, pair["input"]) for pair in pairs]
                if labels != [pair["output"] for pair in pairs]:
                    raise AssertionError("protected label mismatch")
                report["jobs"].append({
                    "seed": seed,
                    "settings": _settings(policy),
                    "labels": len(labels),
                    "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                })
                if policy == "largest_cluster_color":
                    pair = episode["test"][3]
                    wrong = execute(wrong_program, pair["input"])
                    if wrong == pair["output"]:
                        raise AssertionError("protected causal counterfactual unchanged")
                    report["causal_counterfactuals"].append({
                        "seed": seed,
                        "settings": _settings(policy),
                        "input": pair["input"],
                        "output": pair["output"],
                        "counterfactual_output": wrong,
                        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                        "counterfactual_program_sha256": hashlib.sha256(wrong_program.encode()).hexdigest(),
                        "intermediate_value": PROTOTYPE.describe_case(pair["input"])["anchor_color"],
                        "ablation": "wrong_intermediate",
                    })
    return report


def run(*, broad_seed_count: int = 32, protected_seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    if type(broad_seed_count) is not int or not 1 <= broad_seed_count <= 256:
        raise ValueError("broad_seed_count must be an integer in 1..256")
    broad = structural_audit(range(broad_seed_count))
    protected = protected_audit(protected_seeds)
    return {
        "schema": "arcpuzzles-c1b80aa665e4-self-audit-v1",
        "status": "pass" if broad["status"] == protected["status"] == "pass" else "fail",
        "broad": broad,
        "protected": protected,
        "limits": "Finite named rivals and seeds only; no universal uniqueness claim.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--broad-seed-count", type=int, default=32)
    parser.add_argument("--protected-seed", type=int, action="append", dest="protected_seeds")
    args = parser.parse_args(argv)
    report = run(broad_seed_count=args.broad_seed_count, protected_seeds=args.protected_seeds or [0, 17])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "out": str(args.out),
        "episodes": report["broad"]["episodes"],
        "lesson_prefixes": report["broad"]["lesson_prefixes"],
        "rival_checks": report["broad"]["rival_checks"],
        "racket_evaluations": report["protected"]["racket_evaluations"],
        "causal_counterfactuals": len(report["protected"]["causal_counterfactuals"]),
    }, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
