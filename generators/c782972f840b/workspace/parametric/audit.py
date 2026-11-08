"""Reusable bounded self-review for the c782 equivalence-policy family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load():
    name = "_c782_equivalence_audit_prototype"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, HERE / "prototype.py")
        if spec is None or spec.loader is None:
            raise ImportError(HERE / "prototype.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def run_audit(seeds=(0, 17), demo_counts=(2, 3, 6)):
    p = _load()
    findings = []
    episodes = 0
    labels = 0
    rival_checks = 0
    for seed in seeds:
        for demos in demo_counts:
            for policy in p.POLICIES:
                episode = p.generate(seed, {"equivalence_policy": policy}, demos, 4)
                episodes += 1
                labels += demos + 4
                survivors = p.rival_survivors(episode["train"], selected_policy=policy)
                rival_checks += len(p.RIVALS)
                if survivors:
                    findings.append({"seed": seed, "demos": demos, "policy": policy, "survivors": survivors})
                for index, pair in enumerate(episode["test"]):
                    if p.transform(pair["input"], "rotation") == p.transform(pair["input"], "dihedral"):
                        findings.append({"seed": seed, "demos": demos, "policy": policy, "query": index, "issue": "settings do not separate"})
    return {
        "schema": "c782-equivalence-audit-v1",
        "episodes": episodes,
        "selected_labels": labels,
        "rival_checks": rival_checks,
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_audit()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
