"""Bounded protected-Racket self-audit for the 84fd bend-order family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge


HOME = Path(__file__).resolve().parent
_PATH = HOME / "family.py"
_NAME = "_84fd4bcdc53c_audit_family_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = FAMILY
_SPEC.loader.exec_module(FAMILY)


def run(output: Path, seeds: tuple[int, ...] = (0, 17, 211)) -> dict:
    failures: list[dict] = []
    rows: list[dict] = []
    evaluations = 0
    rival_checks = 0
    visible_pairs = 0
    public_checks = 0
    cross_setting_query_disagreements = 0
    thirty_by_thirty = 0
    causal_case = None
    programs = {mode: FAMILY.program({"bend_order": mode}) for mode in FAMILY.MODES}

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket is required")

        for seed in seeds:
            banks = FAMILY.episode_inputs(seed)
            grids = banks["train"] + banks["test"]
            actual: dict[str, list[list[list[int]]]] = {}

            for mode in FAMILY.MODES:
                actual[mode] = [FAMILY.execute_racket(programs[mode], grid, bridge) for grid in grids]
                evaluations += len(grids)
                claims = [FAMILY.solve(grid, mode) for grid in grids]
                if actual[mode] != claims:
                    mismatch = [i for i, (a, b) in enumerate(zip(actual[mode], claims, strict=True)) if a != b]
                    failures.append({
                        "seed": seed,
                        "mode": mode,
                        "kind": "racket_claim_mismatch",
                        "indices": mismatch,
                    })

            disagreements = sum(
                actual[FAMILY.MODES[0]][6 + index] != actual[FAMILY.MODES[1]][6 + index]
                for index in range(4)
            )
            cross_setting_query_disagreements += disagreements
            if disagreements != 4:
                failures.append({"seed": seed, "kind": "query_setting_collision", "count": disagreements})
            if len(grids[-1]) == len(grids[-1][0]) == 30:
                thirty_by_thirty += 1

            for mode in FAMILY.MODES:
                full = FAMILY.generate(seed, {"bend_order": mode}, 6, 4)
                visible_pairs += len(full["train"]) + len(full["test"])
                for query_index in range(4):
                    public = FAMILY.public_turn(full, query_index)
                    public_checks += 1
                    if (
                        set(public) != {"train", "test"}
                        or len(public["test"]) != 1
                        or set(public["test"][0]) != {"input"}
                    ):
                        failures.append({
                            "seed": seed,
                            "mode": mode,
                            "kind": "public_projection",
                            "query": query_index,
                        })

                for demos in (2, 3, 6):
                    selected = actual[mode][:demos]
                    survivors = [candidate for candidate in FAMILY.MODES if actual[candidate][:demos] == selected]
                    if survivors != [mode]:
                        failures.append({
                            "seed": seed,
                            "mode": mode,
                            "demos": demos,
                            "kind": "setting_survivors",
                            "survivors": survivors,
                        })

                    rival_survivors: list[str] = []
                    for rival in FAMILY.RIVALS:
                        predictions = [FAMILY.rival_outputs(grid, mode)[rival] for grid in banks["train"][:demos]]
                        rival_checks += demos
                        if predictions == selected:
                            rival_survivors.append(rival)
                            query_predictions = [FAMILY.rival_outputs(grid, mode)[rival] for grid in banks["test"]]
                            if query_predictions != actual[mode][6:]:
                                failures.append({
                                    "seed": seed,
                                    "mode": mode,
                                    "demos": demos,
                                    "kind": "dangerous_rival",
                                    "rival": rival,
                                })

                    rows.append({
                        "seed": seed,
                        "settings": {"bend_order": mode},
                        "demos": demos,
                        "queries": 4,
                        "setting_survivors": survivors,
                        "rival_survivors": rival_survivors,
                    })

            if seed == 17:
                grid = banks["test"][3]
                intended_mode = "vertical_then_horizontal"
                counterfactual_mode = "horizontal_then_vertical"
                intended = actual[intended_mode][9]
                counterfactual = actual[counterfactual_mode][9]
                if intended == counterfactual:
                    failures.append({"seed": seed, "kind": "causal_output_unchanged"})
                causal_case = {
                    "settings": {"bend_order": intended_mode},
                    "program": programs[intended_mode],
                    "input": grid,
                    "output": intended,
                    "counterfactual_program": programs[counterfactual_mode],
                    "counterfactual_output": counterfactual,
                    "intermediate_value": FAMILY.dependency_intermediate(grid, intended_mode),
                    "counterfactual_intermediate": FAMILY.dependency_intermediate(grid, counterfactual_mode),
                    "ablation": "wrong_intermediate",
                }

    report = {
        "schema": "arcpuzzles-84fd4bcdc53c-parametric-audit-v1",
        "status": "passed" if not failures else "failed",
        "task_id": FAMILY.TASK_ID,
        "racket": identity,
        "seeds": list(seeds),
        "settings": list(FAMILY.SETTINGS),
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "episode_jobs": len(rows),
        "visible_pairs": visible_pairs,
        "protected_racket_evaluations": evaluations,
        "declared_rival_checks": rival_checks,
        "public_projection_checks": public_checks,
        "cross_setting_query_disagreements": cross_setting_query_disagreements,
        "thirty_by_thirty_query_banks": thirty_by_thirty,
        "rows": rows,
        "failures": failures,
        "causal_case": causal_case,
        "scope": (
            "Finite seeds 0/17/211, exact setting programs, demo prefixes 2/3/6, "
            "four queries, and nine named Python rivals. Every selected label and "
            "the causal pair execute in protected Racket; this is not universal uniqueness."
        ),
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "causal-case.json").write_text(
        json.dumps(causal_case, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "status",
        "episode_jobs",
        "visible_pairs",
        "protected_racket_evaluations",
        "declared_rival_checks",
        "public_projection_checks",
        "cross_setting_query_disagreements",
        "thirty_by_thirty_query_banks",
        "failures",
    )}, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return 0 if run(args.out)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
