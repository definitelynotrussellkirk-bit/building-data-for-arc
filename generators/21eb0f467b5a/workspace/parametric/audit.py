"""Bounded finite-rival self-audit for the keyed-segment family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def _load_family():
    path = Path(__file__).with_name("family.py")
    spec = importlib.util.spec_from_file_location("_audit_21eb0f467b5a_family", path)
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
    for seed in (0, 17, 31, 97, 211, 509):
        for demos in (2, 3, 6):
            for mode in family.PROGRAMS:
                episode = family.generate(seed, {"connection_mode": mode}, demos, 4)
                report = family.teaching_report(episode, mode)
                row = {"seed": seed, "demos": demos, "mode": mode, **report}
                rows.append(row)
                pair_checks += len(episode["train"]) + len(episode["test"])
                rival_checks += len(family.RIVALS) * len(episode["train"])
                if report["setting_survivors"] != [mode] or report["surviving_rivals"]:
                    failures.append(row)
    return {
        "schema": "arcpuzzles-task-parametric-self-audit-v1",
        "task_id": "21eb0f467b5a",
        "status": "passed" if not failures else "failed",
        "jobs": len(rows),
        "labeled_pairs": pair_checks,
        "rival_demo_checks": rival_checks,
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
