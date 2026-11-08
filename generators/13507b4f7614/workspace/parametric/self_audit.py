"""Bounded, independent teaching screen; Racket labels, Python diagnostic rivals.

Run via WORK/run_with_racket.py with --out ../checks/13507b4f7614/self-audit.json
--seeds 0 1. One persistent protected bridge labels the six-demo/four-query
pool once per seed and setting; all 2..6 demonstration prefixes reuse it.
Python rivals are a finite adversarial diagnostic, never label authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(HERE), str(ROOT / "shared/runtime")]


# Load the reviewed sibling by exact path, without ambient module-name lookup.
import importlib.util
_RIVALS_PATH = HERE / "rivals.py"
_spec = importlib.util.spec_from_file_location("_rectangle_cross_independent_rivals", _RIVALS_PATH)
_rival_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _rival_module
_spec.loader.exec_module(_rival_module)
Rectangle = _rival_module.Rectangle
rectangles = _rival_module.rectangles
paint = _rival_module.paint
choose = _rival_module.choose
diagnostic = _rival_module.diagnostic
RIVALS = _rival_module.RIVALS


def typed_grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list
            or not 1 <= len(value[0]) <= 30 or any(type(row) is not list or len(row) != len(value[0])
            or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value)):
        raise ValueError("expected exact integer 1..30 rectangular grid")
    return value


def run(seeds):
    import native
    from arc_repl.racket_bridge import RacketBridge

    started = time.monotonic()
    report = {
        "schema": "13507b4f7614-independent-teaching-audit-v1",
        "scope": "Finite diagnostic rival screen, not universal induction proof; authority labels and causal counterfactuals execute through protected Racket.",
        "rival_backend": "independent_python_diagnostic_only",
        "rivals": list(RIVALS), "seeds": seeds, "demo_prefixes": list(range(2, 7)), "queries": 4,
        "source_binding": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (HERE / "native.py", HERE / "rivals.py", Path(__file__))},
        "jobs": [], "causal_cases": [], "errors": [], "input_contract_errors": [],
        "diagnostic_intended_rule_disagreements": [], "racket_evaluations": 0,
    }
    bridge = None
    try:
        bridge = RacketBridge()
        report["racket"] = bridge.runtime_identity
        if report["racket"].get("backend") != "racket" or report["racket"].get("protected") is not True:
            raise ValueError("teaching audit requires protected actual Racket")
        programs = [(setting, native.program(setting)) for setting in native.SETTINGS]
        report["programs"] = [{"settings": setting, "program_sha256": hashlib.sha256(program.encode()).hexdigest(), "characters": len(program), "program": program} for setting, program in programs]
        def execute(program, grid):
            report["racket_evaluations"] += 1
            return typed_grid(native.execute(program, grid, bridge=bridge))

        for seed in seeds:
            pool = native.sample_inputs(seed, demos=6, queries=4)
            inputs = [typed_grid(grid) for grid in pool["train"] + pool["test"]]
            if len(pool["train"]) != 6 or len(pool["test"]) != 4:
                raise ValueError("sampler did not provide exact six-demo/four-query pool")
            if len({json.dumps(grid) for grid in inputs}) != 10:
                raise ValueError("demonstrations and four queries must be pairwise novel")
            for index, grid in enumerate(inputs):
                odds = [obj for obj in rectangles(grid) if obj.odd]
                largest = max((obj.area for obj in odds), default=-1)
                anchors = [obj for obj in odds if obj.area == largest]
                targets = ([obj for obj in odds if obj != anchors[0]
                            and obj.area == anchors[0].h + anchors[0].w - 1]
                           if len(anchors) == 1 else [])
                if len(anchors) != 1 or len(targets) != 1:
                    report["input_contract_errors"].append({"seed": seed,
                        "split": "train" if index < 6 else "test",
                        "index": index if index < 6 else index - 6,
                        "input": grid, "unique_largest_odd": len(anchors) == 1,
                        "matched_other_rectangle_count": len(targets)})
            for count in range(2, 6):
                prefix_pool = native.sample_inputs(seed, demos=count, queries=4)
                if prefix_pool["train"] != pool["train"][:count] or prefix_pool["test"] != pool["test"]:
                    raise ValueError("demo prefixes and query stream must be stable across independent counts")
            rival_outputs, rival_errors = {}, {}
            for name in RIVALS:
                rival_outputs[name] = []
                for index, grid in enumerate(inputs):
                    try:
                        rival_outputs[name].append(typed_grid(diagnostic(grid, name)))
                    except Exception as exc:
                        rival_outputs[name].append(None)
                        rival_errors.setdefault(name, []).append({"input_index": index, "error": f"{type(exc).__name__}: {exc}"})
            for setting, program in programs:
                labels = [execute(program, grid) for grid in inputs]
                intended_name = "all_odd" if setting["selection_rule"] == "all_odd" else "cascade_correct"
                for index, (grid, label) in enumerate(zip(inputs, labels)):
                    diagnostic_label = diagnostic(grid, intended_name)
                    if diagnostic_label != label:
                        report["diagnostic_intended_rule_disagreements"].append({"seed": seed,
                            "settings": setting, "input_index": index, "input": grid,
                            "racket_output": label, "diagnostic_python_output": diagnostic_label})
                pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, labels)]
                job = {"seed": seed, "settings": setting, "program_sha256": hashlib.sha256(program.encode()).hexdigest(), "episode": {"train": pairs[:6], "test": pairs[6:]}, "prefixes": [], "diagnostic_failures": rival_errors}
                for count in range(2, 7):
                    survivors, refuted, inconclusive, gaps = [], [], [], []
                    for name in RIVALS:
                        outputs = rival_outputs[name]
                        failures = [row for row in rival_errors.get(name, []) if row["input_index"] < count or row["input_index"] >= 6]
                        if failures:
                            inconclusive.append({"rival": name, "failures": failures})
                            continue
                        mismatch = next((i for i in range(count) if outputs[i] != labels[i]), None)
                        if mismatch is not None:
                            refuted.append({"rival": name, "demonstration_index": mismatch})
                            continue
                        survivors.append(name)
                        query = next((i for i in range(6, 10) if outputs[i] != labels[i]), None)
                        if query is not None:
                            gaps.append({"rival": name, "query_index": query - 6,
                                "minimal_case": {"seed": seed, "settings": setting, "demos": count,
                                    "train": pairs[:count], "query": pairs[query], "rival_output": outputs[query]}})
                    job["prefixes"].append({"demos": count, "survivors": survivors, "refuted": refuted,
                        "inconclusive": inconclusive, "teaching_gaps": gaps,
                        "status": "fail" if gaps or inconclusive else "pass"})
                report["jobs"].append(job)
                if setting.get("selection_rule") == "cross_area_cascade" and len(report["causal_cases"]) < 2:
                    marker = native.COUNTERFACTUAL_MARKER
                    if program.count(marker) != 1:
                        raise ValueError("counterfactual marker must occur exactly once")
                    counterfactual = program.replace(marker, native.COUNTERFACTUAL_REPLACEMENT)
                    case_index = len(report["causal_cases"])
                    grid = inputs[case_index]
                    altered = execute(counterfactual, grid)
                    anchor = choose([obj for obj in rectangles(grid) if obj.odd], lambda obj: obj.area, largest=True)
                    occupied = lambda output: sum(output[r][c] == 4 for r in range(anchor.top, anchor.bottom + 1) for c in range(anchor.left, anchor.right + 1))
                    if altered == labels[case_index] or occupied(altered) != anchor.h + anchor.w - 1 or occupied(labels[case_index]) != occupied(altered):
                        raise ValueError("wrong-intermediate counterfactual must preserve A's cross and change final output")
                    report["causal_cases"].append({"seed": seed, "input_index": case_index, "input": grid, "settings": setting,
                        "intermediate_value": occupied(labels[case_index]), "counterfactual_intermediate_value": anchor.area,
                        "program": program, "output": labels[case_index], "counterfactual_program": counterfactual,
                        "counterfactual_output": altered, "ablation": "wrong_intermediate", "a_retained": True})
            # Racket setting separation reuses labels, with no additional runtime calls.
            seed_jobs = [job for job in report["jobs"] if job["seed"] == seed]
            for job in seed_jobs:
                for prefix in job["prefixes"]:
                    actual_survivors = [other["settings"] for other in seed_jobs
                        if all(a["output"] == b["output"] for a, b in zip(job["episode"]["train"][:prefix["demos"]], other["episode"]["train"][:prefix["demos"]]))]
                    prefix["actual_racket_setting_survivors"] = actual_survivors
                    if actual_survivors != [job["settings"]]:
                        prefix["status"] = "fail"
        report["bridge_restarts"] = getattr(bridge, "_restarts", None)
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if bridge is not None:
            bridge.close()
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    valid = (report["jobs"] and not report["errors"] and not report["input_contract_errors"]
             and not report["diagnostic_intended_rule_disagreements"])
    report["mandatory_two_demo_status"] = "pass" if valid and all(job["prefixes"][0]["status"] == "pass" for job in report["jobs"]) else "fail"
    report["status"] = "pass" if valid and all(prefix["status"] == "pass" for job in report["jobs"] for prefix in job["prefixes"]) else "fail"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    args = parser.parse_args()
    if not 1 <= len(args.seeds) <= 4 or len(set(args.seeds)) != len(args.seeds) or any(seed < 0 or seed >= 2**63 for seed in args.seeds):
        parser.error("supply one to four distinct seeds in 0..2**63-1")
    report = run(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "status": report["status"], "mandatory_two_demo_status": report["mandatory_two_demo_status"], "jobs": len(report["jobs"]), "rivals": len(RIVALS), "causal_cases": len(report["causal_cases"]), "racket_evaluations": report["racket_evaluations"], "errors": report["errors"], "input_contract_errors": len(report["input_contract_errors"]), "diagnostic_intended_rule_disagreements": len(report["diagnostic_intended_rule_disagreements"])}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
