"""Bounded finite-rival self-audit for the ruler-threshold family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def _load_family():
    path = Path(__file__).with_name("family.py")
    spec = importlib.util.spec_from_file_location("_audit_6c894e4b9bf5_family", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run():
    family = _load_family()
    rows = []
    failures = []
    for seed in (0, 17, 31, 97):
        for demos in (2, 3, 6):
            for mode in family.PROGRAMS:
                episode = family.generate(seed, {"selection_mode": mode}, demos, 4)
                report = family.teaching_report(episode, mode)
                row = {"seed": seed, "demos": demos, "mode": mode, **report}
                rows.append(row)
                if report["setting_survivors"] != [mode] or report["surviving_rivals"]:
                    failures.append(row)
    return {
        "schema": "arcpuzzles-task-parametric-self-audit-v1",
        "task_id": "6c894e4b9bf5",
        "status": "passed" if not failures else "failed",
        "jobs": len(rows),
        "failures": failures,
        "rows": rows,
        "limits": "Four seeds, demo counts 2/3/6, two settings and seven named finite rivals.",
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
