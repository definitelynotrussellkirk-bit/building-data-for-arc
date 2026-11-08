"""Bounded teaching and execution audit for the e942ce41cbf5 family.

The broad pass is deterministic Python diagnostics over a finite named rival
inventory.  The protected pass executes both admitted setting programs through
Racket and then compares the same diagnostic rivals against those labels.  It
proves only the listed seeds and rivals, not universal identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

_PROTO_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("_e942ce41cbf5_self_audit_prototype", _PROTO_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype: {_PROTO_PATH}")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PROTOTYPE
_SPEC.loader.exec_module(PROTOTYPE)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _settings(policy: str) -> dict[str, str]:
    return {"operation_policy": policy}


def _serialize(grid: Grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _render_variant(
    grid: Grid,
    *,
    policy: str,
    forced_transform: int | None = None,
    pretransform_rank: bool = False,
    forced_control4: int | None = None,
    swap_4_6: bool = False,
) -> Grid:
    blue, red_raw, operation, transform = PROTOTYPE._parse(grid)
    red = PROTOTYPE._transform(red_raw, transform if forced_transform is None else forced_transform)
    if swap_4_6:
        actual_operation = {3: 3, 4: 6, 6: 4}[operation]
    elif forced_control4 is not None and operation == 4:
        actual_operation = forced_control4
    elif policy == "canonical":
        actual_operation = operation
    elif policy == "rank_control4":
        rank_red = red_raw if pretransform_rank else red
        actual_operation = PROTOTYPE._ranked_op(blue, rank_red, operation)
    else:  # pragma: no cover - internal inventory construction
        raise ValueError(f"unknown diagnostic policy {policy!r}")
    return PROTOTYPE._render(PROTOTYPE._combine(blue, red, actual_operation))


def rivals_for(policy: str) -> dict[str, Rival]:
    if policy == "canonical":
        return {
            "other_setting_rank_control4": lambda grid: _render_variant(grid, policy="rank_control4"),
            "swap_controls_4_and_6": lambda grid: _render_variant(
                grid, policy="canonical", swap_4_6=True
            ),
            "fixed_identity_transform": lambda grid: _render_variant(
                grid, policy="canonical", forced_transform=7
            ),
            "fixed_rotate_transform": lambda grid: _render_variant(
                grid, policy="canonical", forced_transform=8
            ),
            "fixed_flip_transform": lambda grid: _render_variant(
                grid, policy="canonical", forced_transform=9
            ),
        }
    if policy == "rank_control4":
        return {
            "other_setting_canonical": lambda grid: _render_variant(grid, policy="canonical"),
            "rank_control4_before_transform": lambda grid: _render_variant(
                grid, policy="rank_control4", pretransform_rank=True
            ),
            "control4_always_xor": lambda grid: _render_variant(
                grid, policy="rank_control4", forced_control4=6
            ),
            "control4_always_intersection": lambda grid: _render_variant(
                grid, policy="rank_control4", forced_control4=4
            ),
            "fixed_identity_transform": lambda grid: _render_variant(
                grid, policy="rank_control4", forced_transform=7
            ),
            "fixed_rotate_transform": lambda grid: _render_variant(
                grid, policy="rank_control4", forced_transform=8
            ),
            "fixed_flip_transform": lambda grid: _render_variant(
                grid, policy="rank_control4", forced_transform=9
            ),
        }
    raise ValueError(f"unknown policy {policy!r}")


def _audit_rivals(
    *,
    seed: int,
    policy: str,
    episode: dict[str, Any],
    authoritative_labels: list[Grid] | None = None,
) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pairs = episode["train"] + episode["test"]
    labels = authoritative_labels or [pair["output"] for pair in pairs]
    demo_pool = len(episode["train"])
    checks = 0
    gaps: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    benign: list[dict[str, Any]] = []
    for demos in range(2, demo_pool + 1):
        for name, rival in rivals_for(policy).items():
            checks += 1
            try:
                outputs = [rival(pair["input"]) for pair in pairs]
            except Exception as exc:  # every rival must be total over admitted inputs
                errors.append(
                    {
                        "seed": seed,
                        "settings": _settings(policy),
                        "demos": demos,
                        "rival": name,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            mismatch = next((i for i in range(demos) if outputs[i] != labels[i]), None)
            if mismatch is not None:
                continue
            query_index = next(
                (
                    i - demo_pool
                    for i in range(demo_pool, len(pairs))
                    if outputs[i] != labels[i]
                ),
                None,
            )
            record = {
                "seed": seed,
                "settings": _settings(policy),
                "demos": demos,
                "rival": name,
            }
            if query_index is None:
                benign.append(record)
            else:
                gaps.append(
                    {
                        **record,
                        "query_index": query_index,
                        "minimal_case": {
                            "train": episode["train"][:demos],
                            "query": episode["test"][query_index],
                            "rival_output": outputs[demo_pool + query_index],
                        },
                    }
                )
    return checks, gaps, errors, benign


def structural_audit(seeds: Iterable[int]) -> dict[str, Any]:
    seed_list = [int(seed) for seed in seeds]
    if not seed_list or len(seed_list) != len(set(seed_list)) or any(seed < 0 for seed in seed_list):
        raise ValueError("seeds must be a nonempty collection of distinct nonnegative integers")
    report: dict[str, Any] = {
        "schema": "arcpuzzles-e942ce41cbf5-structural-audit-v1",
        "status": "pass",
        "seeds": seed_list,
        "episodes": 0,
        "lesson_prefixes": 0,
        "rival_checks": 0,
        "teaching_gaps": [],
        "rival_errors": [],
        "benign_survivors": [],
        "stress_30x30": 0,
        "causal_cases": 0,
        "public_projection_checks": 0,
        "matched_input_checks": 0,
        "prefix_checks": 0,
        "claim_scope": "finite listed rivals and seeds only",
    }
    for seed in seed_list:
        episodes = {
            policy: PROTOTYPE.generate(seed, _settings(policy), demos=6, queries=4)
            for policy in PROTOTYPE.POLICIES
        }
        left_inputs = [pair["input"] for pair in episodes["canonical"]["train"] + episodes["canonical"]["test"]]
        right_inputs = [pair["input"] for pair in episodes["rank_control4"]["train"] + episodes["rank_control4"]["test"]]
        if left_inputs != right_inputs:
            raise AssertionError(f"settings do not share inputs for seed {seed}")
        report["matched_input_checks"] += 1

        for policy, episode in episodes.items():
            report["episodes"] += 1
            all_pairs = episode["train"] + episode["test"]
            if len({_serialize(pair["input"]) for pair in all_pairs}) != len(all_pairs):
                raise AssertionError(f"duplicate input for seed={seed}, policy={policy}")
            for pair in all_pairs:
                if pair["output"] != PROTOTYPE.solve(pair["input"], policy):
                    raise AssertionError(f"Python label mismatch for seed={seed}, policy={policy}")

            for demos in range(2, 7):
                short = PROTOTYPE.generate(seed, _settings(policy), demos=demos, queries=1)
                if short["train"] != episode["train"][:demos] or short["test"] != episode["test"][:1]:
                    raise AssertionError(f"prefix instability for seed={seed}, policy={policy}, demos={demos}")
                report["prefix_checks"] += 1
                report["lesson_prefixes"] += 1

            public = PROTOTYPE.public_turn(episode, 0)
            if set(public) != {"train", "test"} or len(public["test"]) != 1 or set(public["test"][0]) != {"input"}:
                raise AssertionError("public turn leaked private data")
            report["public_projection_checks"] += 1

            stress = episode["test"][3]["input"]
            nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
            if (
                [len(stress), len(stress[0])] != [30, 30]
                or len(nonzero) < 150
                or len({r for r, _ in nonzero}) < 24
                or len({c for _, c in nonzero}) < 24
                or not any(r in (0, 29) or c in (0, 29) for r, c in nonzero)
            ):
                raise AssertionError(f"insubstantial 30x30 stress for seed={seed}, policy={policy}")
            report["stress_30x30"] += 1
            description = PROTOTYPE.describe_case(stress)
            if (
                description["pre_transform_relation"] == description["post_transform_relation"]
                or description["wrong_pretransform_operation"] == description["ranked_operation"]
            ):
                raise AssertionError(f"missing causal relation reversal for seed={seed}")
            report["causal_cases"] += 1

            checks, gaps, errors, benign = _audit_rivals(
                seed=seed, policy=policy, episode=episode
            )
            report["rival_checks"] += checks
            report["teaching_gaps"].extend(gaps)
            report["rival_errors"].extend(errors)
            report["benign_survivors"].extend(benign)

    if report["teaching_gaps"] or report["rival_errors"]:
        report["status"] = "fail"
    return report


def _racket_grid(grid: Grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def protected_audit(seeds: Iterable[int]) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    seed_list = [int(seed) for seed in seeds]
    if not seed_list or len(seed_list) != len(set(seed_list)):
        raise ValueError("protected seeds must be distinct and nonempty")
    report: dict[str, Any] = {
        "schema": "arcpuzzles-e942ce41cbf5-protected-audit-v1",
        "status": "pass",
        "seeds": seed_list,
        "jobs": [],
        "racket_evaluations": 0,
        "rival_checks": 0,
        "teaching_gaps": [],
        "rival_errors": [],
        "benign_survivors": [],
        "causal_counterfactuals": [],
        "claim_scope": "protected setting labels plus finite Python diagnostic rivals",
    }
    wrong_program = (HERE / "wrong_pretransform_rank.rkt").read_text(encoding="utf-8")
    with RacketBridge() as bridge:
        report["racket"] = dict(bridge.runtime_identity)
        if report["racket"].get("backend") != "racket" or report["racket"].get("protected") is not True:
            raise RuntimeError(f"protected Racket required, got {report['racket']}")

        def execute(program: str, grid: Grid) -> Grid:
            report["racket_evaluations"] += 1
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        for seed in seed_list:
            for policy in PROTOTYPE.POLICIES:
                episode = PROTOTYPE.generate(seed, _settings(policy), demos=6, queries=4)
                program = PROTOTYPE.program(_settings(policy))
                labels = [execute(program, pair["input"]) for pair in episode["train"] + episode["test"]]
                claimed = [pair["output"] for pair in episode["train"] + episode["test"]]
                if labels != claimed:
                    raise AssertionError(f"protected label mismatch for seed={seed}, policy={policy}")
                checks, gaps, errors, benign = _audit_rivals(
                    seed=seed,
                    policy=policy,
                    episode=episode,
                    authoritative_labels=labels,
                )
                report["rival_checks"] += checks
                report["teaching_gaps"].extend(gaps)
                report["rival_errors"].extend(errors)
                report["benign_survivors"].extend(benign)
                report["jobs"].append(
                    {
                        "seed": seed,
                        "settings": _settings(policy),
                        "demos": 6,
                        "queries": 4,
                        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                        "labels": len(labels),
                    }
                )
                if policy == "rank_control4":
                    pair = episode["test"][3]
                    wrong = execute(wrong_program, pair["input"])
                    if wrong == pair["output"]:
                        raise AssertionError(f"causal counterfactual unchanged for seed={seed}")
                    report["causal_counterfactuals"].append(
                        {
                            "seed": seed,
                            "settings": _settings(policy),
                            "input": pair["input"],
                            "output": pair["output"],
                            "counterfactual_output": wrong,
                            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                            "counterfactual_program_sha256": hashlib.sha256(wrong_program.encode()).hexdigest(),
                            "ablation": "wrong_intermediate",
                        }
                    )
    if report["teaching_gaps"] or report["rival_errors"]:
        report["status"] = "fail"
    return report


def run(*, broad_seed_count: int = 32, protected_seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    if type(broad_seed_count) is not int or not 1 <= broad_seed_count <= 256:
        raise ValueError("broad_seed_count must be an integer in 1..256")
    broad = structural_audit(range(broad_seed_count))
    protected = protected_audit(protected_seeds)
    return {
        "schema": "arcpuzzles-e942ce41cbf5-self-audit-v1",
        "status": "pass" if broad["status"] == protected["status"] == "pass" else "fail",
        "broad": broad,
        "protected": protected,
        "limits": "Finite named rivals and seeds only; no universal uniqueness or training-gain claim.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--broad-seed-count", type=int, default=32)
    parser.add_argument("--protected-seed", type=int, action="append", dest="protected_seeds")
    args = parser.parse_args(argv)
    seeds = args.protected_seeds or [0, 17]
    report = run(broad_seed_count=args.broad_seed_count, protected_seeds=seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "broad_episodes": report["broad"]["episodes"],
                "lesson_prefixes": report["broad"]["lesson_prefixes"],
                "rival_checks": report["broad"]["rival_checks"] + report["protected"]["rival_checks"],
                "racket_evaluations": report["protected"]["racket_evaluations"],
                "causal_counterfactuals": len(report["protected"]["causal_counterfactuals"]),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
