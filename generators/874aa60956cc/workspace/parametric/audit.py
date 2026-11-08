#!/usr/bin/env python3
"""Bounded learnability audit and protected-Racket causal case."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TASK_ID = "874aa60956cc"
SETTINGS = (
    {"border_mode": "all"},
    {"border_mode": "touch_count_relay"},
)


def _load():
    path = HERE / "adapter.py"
    name = "_audit_adapter_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _raw(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def _real_evaluator():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise RuntimeError("audit requires protected Racket")
    wrapped = {}

    def apply(program, grid):
        if program not in wrapped:
            wrapped[program] = wrap_rule(program)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return bridge.eval_text(f"({wrapped[program]} {literal})")

    return bridge, identity, apply


def _python_sweep(adapter, seeds: int):
    rival_stats = {
        mode: {
            name: {"demo_survivals": 0, "harmful_survivals": 0, "first_harmful": None}
            for name in (
                (["touch_count_relay"] + list(adapter.RIVAL_SOLVERS))
                if mode == "all"
                else list(adapter.RIVAL_SOLVERS)
            )
            if not (mode == "all" and name == "all_pairs")
        }
        for mode in ("all", "touch_count_relay")
    }
    for seed in range(seeds):
        for mode in ("all", "touch_count_relay"):
            episode = adapter.generate(seed, {"border_mode": mode}, 2, 4)
            candidates = {}
            if mode == "all":
                candidates["touch_count_relay"] = lambda grid: adapter.solve(grid, "touch_count_relay")
            for name, solver in adapter.RIVAL_SOLVERS.items():
                if mode == "all" and name == "all_pairs":
                    continue
                candidates[name] = solver
            for name, solver in candidates.items():
                demos_fit = all(solver(pair["input"]) == pair["output"] for pair in episode["train"])
                query_diff = [
                    i for i, pair in enumerate(episode["test"])
                    if solver(pair["input"]) != pair["output"]
                ]
                row = rival_stats[mode][name]
                if demos_fit:
                    row["demo_survivals"] += 1
                if demos_fit and query_diff:
                    row["harmful_survivals"] += 1
                    if row["first_harmful"] is None:
                        row["first_harmful"] = {"seed": seed, "query_indices": query_diff}
    harmful = [
        {"mode": mode, "rival": name, **row}
        for mode, rivals in rival_stats.items()
        for name, row in rivals.items()
        if row["harmful_survivals"]
    ]
    if harmful:
        raise AssertionError(f"visible-demo harmful rival survivors: {harmful}")
    return rival_stats


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--sweep-seeds", type=int, default=64)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)

    adapter = _load()
    sweep = _python_sweep(adapter, args.sweep_seeds)
    bridge, identity, apply = _real_evaluator()
    evaluations = 0
    setting_rows = []
    receipt_episodes = []
    try:
        programs = [adapter.program(settings) for settings in SETTINGS]
        for settings, chosen_program in zip(SETTINGS, programs, strict=True):
            episode = adapter.generate(args.seed, settings, 2, 4)
            survivors = []
            for candidate_settings, candidate_program in zip(SETTINGS, programs, strict=True):
                outputs = []
                for pair in episode["train"]:
                    outputs.append(apply(candidate_program, pair["input"])); evaluations += 1
                if all(got == pair["output"]
                       for got, pair in zip(outputs, episode["train"], strict=True)):
                    survivors.append(candidate_settings)
            if survivors != [settings]:
                raise AssertionError(f"Racket demo survivors differ: {settings}: {survivors}")
            checked = {"train": [], "test": []}
            for split in ("train", "test"):
                for pair in episode[split]:
                    actual = apply(chosen_program, pair["input"]); evaluations += 1
                    if actual != pair["output"]:
                        raise AssertionError(f"Racket label mismatch for {settings} {split}")
                    checked[split].append({"input": pair["input"], "output": actual})
            setting_rows.append({
                "settings": settings,
                "program_sha256": hashlib.sha256(chosen_program.encode()).hexdigest(),
                "survivors": survivors,
                "counts": {"demos": 2, "queries": 4},
            })
            receipt_episodes.append({
                "settings": settings,
                "program": chosen_program,
                "program_sha256": hashlib.sha256(chosen_program.encode()).hexdigest(),
                **checked,
            })

        relay = adapter.generate(args.seed, SETTINGS[1], 3, 4)
        pair = relay["test"][-1]
        analysis = adapter.analyze_input(pair["input"])
        actual_program = adapter.program(SETTINGS[1])
        counter_program = (HERE / "wrong_intermediate.rkt").read_text(encoding="utf-8")
        actual = apply(actual_program, pair["input"]); evaluations += 1
        counter = apply(counter_program, pair["input"]); evaluations += 1
        if actual != pair["output"] or actual == counter:
            raise AssertionError("wrong-intermediate causal case did not change final output")
        causal = {
            "schema": "arcpuzzles-touch-count-relay-causal-case-v1",
            "task_id": TASK_ID,
            "settings": SETTINGS[1],
            "input": pair["input"],
            "input_shape": [len(pair["input"]), len(pair["input"][0])],
            "program": actual_program,
            "program_sha256": hashlib.sha256(actual_program.encode()).hexdigest(),
            "output": actual,
            "counterfactual_program": counter_program,
            "counterfactual_program_sha256": hashlib.sha256(counter_program.encode()).hexdigest(),
            "counterfactual_output": counter,
            "intermediate_value": {
                "controller_color": analysis["controller_color"],
                "candidate_colors": analysis["candidate_colors"],
                "touched_candidate_colors": analysis["touched_candidate_colors"],
                "touch_count": analysis["touch_count"],
                "selected_color": analysis["selected_color"],
                "counterfactual_forced_count": 1,
            },
            "ablation": "wrong_intermediate",
        }
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-touch-count-relay-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": (
            f"{args.sweep_seeds} seeds, two demonstrations and four queries per setting; "
            "finite declared Python rivals plus protected-Racket setting identification and labels. "
            "This does not prove universal uniqueness."
        ),
        "python_jobs": args.sweep_seeds * len(SETTINGS),
        "racket_evaluations": evaluations,
        "racket": {k: identity[k] for k in identity if k in {
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
            "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"
        }},
        "settings": setting_rows,
        "rivals": sweep,
        "causal_case": "causal_case.json",
    }
    receipt = {
        "schema": "arcpuzzles-touch-count-relay-racket-receipt-v1",
        "task_id": TASK_ID,
        "seed": args.seed,
        "racket": report["racket"],
        "racket_evaluations": evaluations,
        "episodes": receipt_episodes,
        "causal_case": causal,
    }
    (out / "report.json").write_bytes(_raw(report))
    (out / "racket_receipt.json").write_bytes(_raw(receipt))
    (out / "causal_case.json").write_bytes(_raw(causal))
    print(json.dumps({
        "status": "passed",
        "python_jobs": report["python_jobs"],
        "racket_evaluations": evaluations,
        "out": str(out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
