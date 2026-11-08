"""Bounded adversarial and protected-Racket audit for the native tie-marker family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

TASK_ID = "1b2b9283b4ab"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _load(name: str, path: Path):
    body = path.read_bytes()
    module_name = f"_audit_{TASK_ID}_{name}_{hashlib.sha256(body).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


FAMILY = _load("family", HERE / "family.py")
ADAPTER = _load("adapter", HERE / "adapter.py")
GENERATOR = _load("generator", HERE.parents[1] / "generator.py")


def _remap_marker(grid, marker: int):
    if marker == 8:
        return grid
    return [[marker if cell == 8 else cell for cell in row] for row in grid]


def _rivals(grid, marker: int):
    other = 6 if marker == 8 else 8
    result = {
        "declared_other_setting": FAMILY.transform(grid, other),
        "all_seed_colors_as_nearest": FAMILY.transform_all_colors_as_nearest(grid, marker),
    }
    for mode in ("seed_room_tie", "largest_seed_in_room", "ignore_doors",
                 "minimum_color_tie", "unreachable_zero"):
        result[mode] = _remap_marker(GENERATOR.diagnostic_prediction(grid, mode), marker)
    return result


def finite_audit(seeds=range(32), demo_counts=(2, 3, 6)):
    failures = []
    records = []
    witnesses = {}
    for seed in seeds:
        previous_inputs = None
        for demos in demo_counts:
            episodes = {marker: ADAPTER.generate(seed, {"tie_marker": marker}, demos, 4)
                        for marker in FAMILY.TIE_MARKERS}
            inputs = [pair["input"] for pair in episodes[8]["train"] + episodes[8]["test"]]
            if inputs != [pair["input"] for pair in episodes[6]["train"] + episodes[6]["test"]]:
                failures.append({"seed": seed, "demos": demos, "failure": "setting-dependent inputs"})
            if previous_inputs is not None:
                if inputs[:len(previous_inputs[0])] != previous_inputs[0] or inputs[demos:] != previous_inputs[1]:
                    failures.append({"seed": seed, "demos": demos, "failure": "count prefix instability"})
            previous_inputs = (inputs[:demos], inputs[demos:])
            for marker, episode in episodes.items():
                maps = [_rivals(pair["input"], marker) for pair in episode["train"] + episode["test"]]
                names = tuple(maps[0])
                survivors = []
                unresolved = []
                for name in names:
                    predictions = [row[name] for row in maps]
                    demo_match = all(pred == pair["output"]
                                     for pred, pair in zip(predictions[:demos], episode["train"]))
                    if not demo_match:
                        if name not in witnesses:
                            first = next(i for i, (pred, pair) in enumerate(
                                zip(predictions[:demos], episode["train"])) if pred != pair["output"])
                            witnesses[name] = {"seed": seed, "demos": demos, "tie_marker": marker,
                                               "split": "train", "pair_index": first}
                        continue
                    survivors.append(name)
                    disagreements = [i for i, (pred, pair) in enumerate(
                        zip(predictions[demos:], episode["test"])) if pred != pair["output"]]
                    if disagreements:
                        issue = {"seed": seed, "demos": demos, "tie_marker": marker,
                                 "rival": name, "query_disagreements": disagreements}
                        unresolved.append(issue)
                        failures.append(issue)
                records.append({"seed": seed, "demos": demos, "tie_marker": marker,
                                "demo_survivors": survivors,
                                "unresolved_query_disagreements": unresolved})
    boundary = ADAPTER.generate(31, {"tie_marker": 6}, 6, 4)
    stress = boundary["test"][-1]["input"]
    return {
        "schema": "1b2b9283b4ab-native-parametric-audit-v1",
        "status": "passed" if not failures else "failed",
        "episodes_checked": len(tuple(seeds)) * len(tuple(demo_counts)) * len(FAMILY.TIE_MARKERS),
        "seeds": list(seeds), "demo_counts": list(demo_counts), "queries": 4,
        "finite_rivals": sorted(_rivals(boundary["train"][0]["input"], 6)),
        "refutation_witnesses": witnesses, "records": records, "failures": failures,
        "boundary": {"grid": [len(stress), len(stress[0])],
                     "nonwall_cells": sum(cell not in FAMILY.WALLS for row in stress for cell in row),
                     "rooms": len(FAMILY.nearest_color_intermediate(stress)["rooms"])},
        "limits": "Finite named rivals and saved seeds only; no universal uniqueness or training-gain claim.",
    }


def native_probe():
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"tie_marker": marker}, "demos": 2, "queries": 4}
            for marker in FAMILY.TIE_MARKERS for seed in (0, 17)]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    return {
        "racket": result["racket"], "racket_evaluations": result["racket_evaluations"],
        "jobs": jobs, "checks": result["checks"],
        "episode_hashes": [hashlib.sha256(json.dumps(ep, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                           for ep in result["episodes"]],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = finite_audit()
    report["native_probe"] = native_probe()
    report["passed"] = report["status"] == "passed" and report["native_probe"]["racket"].get("protected") is True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "passed": report["passed"],
                      "episodes_checked": report["episodes_checked"],
                      "racket_evaluations": report["native_probe"]["racket_evaluations"],
                      "failures": len(report["failures"]), "boundary": report["boundary"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
