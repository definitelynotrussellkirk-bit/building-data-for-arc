"""Bounded adversarial and protected-Racket audit for template orientation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

TASK_ID = "bf5bed969a6d"
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


def _intermediate_variant(grid, transform):
    base = FAMILY.template_intermediate(grid, "as_is")
    offsets = FAMILY._d4(base["offsets"], transform)
    return {"source_cells": base["source_cells"], "offsets": offsets,
            "height": max(r for r, _ in offsets) + 1,
            "width": max(c for _, c in offsets) + 1}


def _stamp_subset(grid, mode: str, selection: str, *, template_color=False):
    intermediate = FAMILY.template_intermediate(grid, mode)
    components = [(color, cells) for color, cells in FAMILY._components(grid) if color != 2]
    if selection == "first":
        selected = {0}
    elif selection == "largest":
        selected = {max(range(len(components)), key=lambda i: len(components[i][1]))}
    elif selection == "all":
        selected = set(range(len(components)))
    else:
        raise ValueError(selection)
    output = [[0 for _ in row] for row in grid]
    th, tw = intermediate["height"], intermediate["width"]
    for index, (color, cells) in enumerate(components):
        for r, c in cells:
            output[r][c] = color
        if index not in selected:
            continue
        r0, c0, r1, c1 = FAMILY._bbox(cells)
        sr = r0 + 1 + ((r1 - r0 - 1 - th) // 2)
        sc = c0 + 1 + ((c1 - c0 - 1 - tw) // 2)
        paint = 2 if template_color else color
        for dr, dc in intermediate["offsets"]:
            rr, cc = sr + dr, sc + dc
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = paint
    return output


def _rivals(grid, mode: str):
    other = "rotate_cw" if mode == "as_is" else "as_is"
    return {
        "declared_other_setting": FAMILY.transform(grid, other),
        "fixed_L_template": FAMILY.transform_with_fixed_intermediate(grid, mode),
        "rotate_180": FAMILY._paint_with_intermediate(grid, _intermediate_variant(grid, 2)),
        "reflect_left_right": FAMILY._paint_with_intermediate(grid, _intermediate_variant(grid, 4)),
        "stamp_first_component_only": _stamp_subset(grid, mode, "first"),
        "stamp_largest_component_only": _stamp_subset(grid, mode, "largest"),
        "stamp_in_source_color": _stamp_subset(grid, mode, "all", template_color=True),
    }


def finite_audit(seeds=range(32), demo_counts=(2, 3, 6)):
    failures = []
    records = []
    witnesses = {}
    for seed in seeds:
        for demos in demo_counts:
            episodes = {mode: ADAPTER.generate(seed, {"template_transform": mode}, demos, 4)
                        for mode in FAMILY.TRANSFORMS}
            inputs_a = [p["input"] for p in episodes["as_is"]["train"] + episodes["as_is"]["test"]]
            inputs_b = [p["input"] for p in episodes["rotate_cw"]["train"] + episodes["rotate_cw"]["test"]]
            if inputs_a != inputs_b:
                failures.append({"seed": seed, "demos": demos, "failure": "setting-dependent inputs"})
            for mode, episode in episodes.items():
                maps = [_rivals(pair["input"], mode) for pair in episode["train"] + episode["test"]]
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
                            witnesses[name] = {"seed": seed, "demos": demos,
                                               "template_transform": mode,
                                               "split": "train", "pair_index": first}
                        continue
                    survivors.append(name)
                    disagreements = [i for i, (pred, pair) in enumerate(
                        zip(predictions[demos:], episode["test"])) if pred != pair["output"]]
                    if disagreements:
                        issue = {"seed": seed, "demos": demos, "template_transform": mode,
                                 "rival": name, "query_disagreements": disagreements}
                        unresolved.append(issue)
                        failures.append(issue)
                records.append({"seed": seed, "demos": demos, "template_transform": mode,
                                "demo_survivors": survivors,
                                "unresolved_query_disagreements": unresolved})
    boundary = ADAPTER.generate(31, {"template_transform": "rotate_cw"}, 6, 4)
    stress = boundary["test"][-1]["input"]
    return {
        "schema": "bf5bed969a6d-native-parametric-audit-v1",
        "status": "passed" if not failures else "failed",
        "episodes_checked": len(tuple(seeds)) * len(tuple(demo_counts)) * len(FAMILY.TRANSFORMS),
        "seeds": list(seeds), "demo_counts": list(demo_counts), "queries": 4,
        "finite_rivals": sorted(_rivals(boundary["train"][0]["input"], "rotate_cw")),
        "refutation_witnesses": witnesses, "records": records, "failures": failures,
        "boundary": {"grid": [len(stress), len(stress[0])],
                     "nonzero_cells": sum(cell != 0 for row in stress for cell in row),
                     "same_color_components": FAMILY.same_color_component_count(stress)},
        "limits": "Finite named rivals and saved seeds only; no universal uniqueness or training-gain claim.",
    }


def native_probe():
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"template_transform": mode}, "demos": 2, "queries": 4}
            for mode in FAMILY.TRANSFORMS for seed in (0, 17)]
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
