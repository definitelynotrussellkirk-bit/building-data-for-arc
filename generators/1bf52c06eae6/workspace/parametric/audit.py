"""Bounded finite-rival audit for the square-priority family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def _load_family():
    path = Path(__file__).with_name("family.py")
    spec = importlib.util.spec_from_file_location("_audit_1bf52c06eae6_family", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run():
    family = _load_family()
    rows, failures = [], []
    pair_checks = 0
    rival_checks = 0
    selected_colors: set[int] = set()
    selected_ranks: set[int] = set()
    for seed in (0, 17, 31, 97, 211, 509):
        for demos in (2, 3, 6):
            for mode in family.PROGRAMS:
                episode = family.generate(seed, {"priority_mode": mode}, demos, 4)
                report = family.teaching_report(episode, mode)
                row = {"seed": seed, "demos": demos, "mode": mode, **report}
                rows.append(row)
                pair_checks += len(episode["train"]) + len(episode["test"])
                rival_checks += len(family.RIVALS) * len(episode["train"])
                if mode == "probe_demote":
                    for pair in episode["train"] + episode["test"]:
                        color = family.selected_color(pair["input"])
                        selected_colors.add(color)
                        ordered = family.boxes(pair["input"], exclude_probe=True)
                        selected_ranks.add([box[1] for box in ordered].index(color))
                if report["setting_survivors"] != [mode] or report["surviving_rivals"]:
                    failures.append(row)
    if len(selected_colors) < 4 or len(selected_ranks) < 3:
        failures.append({"reason": "insufficient input-dependent intermediate diversity",
                         "selected_colors": sorted(selected_colors),
                         "selected_ranks": sorted(selected_ranks)})
    return {
        "schema": "arcpuzzles-task-parametric-self-audit-v1",
        "task_id": "1bf52c06eae6",
        "status": "passed" if not failures else "failed",
        "jobs": len(rows),
        "labeled_pairs": pair_checks,
        "rival_demo_checks": rival_checks,
        "selected_colors": sorted(selected_colors),
        "selected_ranks": sorted(selected_ranks),
        "failures": failures,
        "rows": rows,
        "limits": "Six seeds, demo counts 2/3/6, two settings and eight named finite rivals.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run()
    text = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
