#!/usr/bin/env python3
"""Bounded demonstration/query shortcut audit; no claim of universal induction.

Run with the repository runtime on PYTHONPATH, after native.py is present.
Selected labels and the native/wrong-anchor rivals execute in protected Racket.
The named object/position heuristics are explicit Python diagnostic mirrors.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator, normalize_grid


TASK_ID = "e521d16d403e"
HERE = Path(__file__).resolve().parent


def _digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _load_native():
    path = HERE / "native.py"
    spec = importlib.util.spec_from_file_location("e521d16d403e_audit_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _execute(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(program)} {literal})"))


def _extra_rivals(generator):
    def predict(grid, name):
        objects = generator._objects(grid)
        eligible = generator._eligible(objects)
        asym = [obj for obj in objects if obj not in eligible]
        if not asym:
            return None
        if name == "largest_asym":
            chosen = max(asym, key=lambda obj: obj["size"])
        elif name == "smallest_asym":
            chosen = min(asym, key=lambda obj: obj["size"])
        elif name == "first_asym":
            chosen = asym[0]
        elif name == "last_asym":
            chosen = asym[-1]
        elif name in ("nearest_asym_to_occupied_anchor", "farthest_asym_from_occupied_anchor"):
            if not eligible:
                return None
            anchor = max(eligible, key=lambda obj: obj["size"])
            ar0, ac0, ar1, ac1 = anchor["bbox"]
            choose = min if name.startswith("nearest") else max
            chosen = choose(asym, key=lambda obj: abs(obj["bbox"][0] + obj["bbox"][2] - ar0 - ar1)
                         + abs(obj["bbox"][1] + obj["bbox"][3] - ac0 - ac1))
        elif name == "bbox_area_width_one_allowed":
            candidates = [obj for obj in objects if obj["lr"]]
            chosen = max(candidates, key=lambda obj: obj["area"]) if candidates else objects[0]
        elif name.startswith(("wide_non_line_lr", "tall_non_line_lr")):
            if not eligible:
                return None
            wide = name.startswith("wide")
            candidates = [obj for obj in eligible if obj["height"] > 1
                          and ((obj["width"] > obj["height"]) if wide
                               else (obj["height"] > obj["width"]))]
            anchor = max(candidates, key=lambda obj: obj["size"]) if candidates else eligible[0]
            if name.endswith("_partner"):
                partners = [obj for obj in objects if obj["color"] == anchor["color"]
                            and obj["bbox"] != anchor["bbox"]]
                chosen = partners[0] if partners else anchor
            else:
                chosen = anchor
        elif name.endswith("_anchor_partner"):
            if not eligible:
                return None
            anchor = (eligible[0] if name.startswith("first") else eligible[-1]
                      if name.startswith("last") else min(eligible, key=lambda obj: obj["size"]))
            partners = [obj for obj in objects if obj["color"] == anchor["color"]
                        and obj["bbox"] != anchor["bbox"]]
            chosen = partners[0] if partners else anchor
        else:
            raise ValueError(name)
        return chosen["crop"]
    names = ("largest_asym", "smallest_asym", "first_asym", "last_asym",
             "nearest_asym_to_occupied_anchor", "farthest_asym_from_occupied_anchor",
             "bbox_area_width_one_allowed", "first_lr_anchor_partner", "last_lr_anchor_partner",
             "smallest_lr_anchor_partner", "wide_non_line_lr", "tall_non_line_lr",
             "wide_non_line_lr_partner", "tall_non_line_lr_partner")
    return {name: (lambda grid, name=name: predict(grid, name)) for name in names}


def audit(seeds=(0, 1), demo_counts=(2, 3, 4, 5, 6), queries=4):
    native = _load_native()
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    settings_rows = list(native.SETTINGS)
    programs = [native.program(settings) for settings in settings_rows]
    # Keep the original two materializations and mutate ONLY the occupied anchor
    # comparator inside the composed third setting for the causal rival.
    occupied_comparator = "(lambda (a b) (> (obj-size a) (obj-size b)))"
    area_comparator = """(lambda (a b)
                         (> (* (+ 1 (- (third (obj-bbox a)) (first (obj-bbox a))))
                               (+ 1 (- (fourth (obj-bbox a)) (second (obj-bbox a)))))
                            (* (+ 1 (- (third (obj-bbox b)) (first (obj-bbox b))))
                               (+ 1 (- (fourth (obj-bbox b)) (second (obj-bbox b)))))))"""
    partner_indices = [i for i, setting in enumerate(settings_rows)
                       if setting.get("selection_rule") == "occupied_anchor_partner"]
    if len(partner_indices) != 1:
        raise ValueError("expected exactly one occupied_anchor_partner setting")
    partner_program = programs[partner_indices[0]]
    if partner_program.count(occupied_comparator) != 1:
        raise ValueError("partner program must expose one guarded occupied comparator")
    wrong_anchor_program = partner_program.replace(occupied_comparator, area_comparator, 1)
    rival_programs = [("native:" + json.dumps(setting, sort_keys=True), program)
                      for setting, program in zip(settings_rows, programs)]
    rival_programs.append(("bbox_anchor_partner", wrong_anchor_program))
    python_rivals = dict(generator.SEMANTIC_RIVALS)
    python_rivals.update(_extra_rivals(generator))
    cases, failures, witnesses = [], [], []
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("audit requires protected Racket")
        for seed in seeds:
            for demos in demo_counts:
                inputs = native.sample_inputs(seed, demos, queries)
                grids = inputs["train"] + inputs["test"]
                if len(inputs["train"]) != demos or len(inputs["test"]) != queries:
                    raise AssertionError("independent count contract failed")
                if len({json.dumps(g) for g in grids}) != len(grids):
                    raise AssertionError("demonstration/query input reuse")
                racket_predictions = {name: [_execute(bridge, program, grid) for grid in grids]
                                      for name, program in rival_programs}
                predictions = {**racket_predictions,
                               **{name: [fn(grid) for grid in grids]
                                  for name, fn in python_rivals.items()}}
                for setting_index, settings in enumerate(settings_rows):
                    selected_name = rival_programs[setting_index][0]
                    gold = predictions[selected_name]
                    rivals = []
                    for name, values in predictions.items():
                        if name == selected_name:
                            continue
                        train_mismatch = [i for i in range(demos) if values[i] != gold[i]]
                        query_mismatch = [i for i in range(queries) if values[demos+i] != gold[demos+i]]
                        status = ("query_equivalent" if not query_mismatch else
                                  "refuted_by_demonstrations" if train_mismatch else "ambiguous_query")
                        rivals.append({"name": name, "status": status,
                                       "demonstration_mismatch_indices": train_mismatch,
                                       "query_mismatch_indices": query_mismatch,
                                       "execution": "protected_racket" if name in racket_predictions else "python_diagnostic"})
                        if status == "ambiguous_query":
                            q = demos + query_mismatch[0]
                            failures.append({"seed": seed, "demos": demos, "settings": settings,
                                             "rival": name, "train": [{"input": g, "output": o}
                                                                 for g, o in zip(grids[:demos], gold[:demos])],
                                             "query": {"input": grids[q], "output": gold[q],
                                                       "rival_prediction": values[q]}})
                    cases.append({"seed": seed, "demos": demos, "queries": queries,
                                  "settings": settings, "rivals": rivals})
                partner_gold = predictions[rival_programs[partner_indices[0]][0]]
                wrong = predictions["bbox_anchor_partner"]
                if len(witnesses) < 2:
                    for grid, actual, counterfactual in zip(grids, partner_gold, wrong):
                        if actual != counterfactual and not any(w["input"] == grid for w in witnesses):
                            witnesses.append({"input": grid, "settings": settings_rows[partner_indices[0]],
                                              "program": partner_program, "output": actual,
                                              "counterfactual_program": wrong_anchor_program,
                                              "counterfactual_output": counterfactual,
                                              "ablation": "wrong_intermediate", "racket": identity})
                            break
    return {"schema": "arcpuzzles-finite-teaching-self-audit-v1", "task_id": TASK_ID,
            "status": "pass" if not failures else "ambiguous", "racket": identity,
            "sources": [{"path": str(p.relative_to(root)), "sha256": _digest(p.read_bytes())}
                        for p in (Path(__file__), HERE / "native.py", generator_path)],
            "generator_sha256": generator_sha, "cases": cases, "failures": failures,
            "racket_backed_counterfactual_witnesses": witnesses,
            "limits": "Finite declared rivals and sampled scenes only; Python heuristics are diagnostic mirrors. "
                      "Query-equivalent rivals need no refutation. All selected labels/native rivals/counterfactuals "
                      "execute through protected Racket. This report makes no universal uniqueness claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demos", nargs="+", type=int, default=[2, 3, 4, 5, 6])
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.seeds, args.demos, args.queries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(report["cases"]),
                      "failures": len(report["failures"]), "report": str(args.out)}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
