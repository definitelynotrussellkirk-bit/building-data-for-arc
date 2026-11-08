"""Bounded self-audit for the be6269bef667 native parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def load(name):
    path = HERE / name
    module_name = "_be62_audit_" + name.replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be new")
    adapter, rivals = load("adapter.py"), load("rivals.py")
    settings = ({"weighting": "unit"}, {"weighting": "plurality_double"})
    rows = []
    for seed in range(32):
        for demos in (2, 3, 6):
            for setting in settings:
                episode = adapter.generate(seed, setting, demos, 4)
                survivors = [
                    name for name in rivals.RIVAL_NAMES
                    if all(rivals.predict(pair["input"], name) == pair["output"] for pair in episode["train"])
                ]
                if survivors != [setting["weighting"]]:
                    raise ValueError(f"ambiguous lesson seed={seed} demos={demos} setting={setting}: {survivors}")
                if not all(rivals.predict(pair["input"], survivors[0]) == pair["output"] for pair in episode["test"]):
                    raise ValueError("surviving setting failed a query")
                rows.append({"seed": seed, "demos": demos, "settings": setting, "survivors": survivors})

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    evaluations = 0
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        for seed in (0, 17):
            for setting in settings:
                episode = adapter.generate(seed, setting, 2, 4)
                source = wrap_rule(adapter.program(setting))
                for pair in episode["train"] + episode["test"]:
                    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                    if bridge.eval_text(f"({source} {literal})") != pair["output"]:
                        raise ValueError("protected Racket parity mismatch")
                    evaluations += 1

    stress = adapter.generate(17, settings[0], 2, 4)["test"][2]
    report = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "be6269bef667",
        "status": "pass",
        "episodes": len(rows),
        "seeds": 32,
        "demo_counts": [2, 3, 6],
        "settings": list(settings),
        "rivals": list(rivals.RIVAL_NAMES),
        "ambiguities": 0,
        "racket": identity,
        "racket_evaluations": evaluations,
        "stress": {
            "shape": [len(stress["input"]), len(stress["input"][0])],
            "input_nonzero": sum(value != 0 for row in stress["input"] for value in row),
            "output_nonzero": sum(value != 0 for row in stress["output"] for value in row),
            "max_output": max(max(row) for row in stress["output"]),
        },
        "program_sha256": {
            setting["weighting"]: hashlib.sha256(adapter.program(setting).encode()).hexdigest()
            for setting in settings
        },
        "limits": "Finite named-rival and two-seed Racket parity audit; not a proof of universal identifiability or training benefit.",
    }
    write(args.out, report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
