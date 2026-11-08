#!/usr/bin/env python3
"""Bounded learnability/count/spread audit for the ff973026bfbe family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def _load(name: str):
    path = HERE / f"{name}.py"
    key = f"_ff973026bfbe_audit_{name}_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(key, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    prototype = _load("prototype")
    adapter = _load("adapter")
    failures: list[dict] = []
    episodes = 0
    pairs = 0
    stress_pairs = 0
    for seed in range(args.seeds):
        matched: dict[str, list] = {}
        for selected in prototype.SETTINGS:
            setting = {"column_policy": selected}
            for demos in (2, 3, 6):
                episode = adapter.generate(seed, setting, demos, 4)
                episodes += 1
                pairs += len(episode["train"]) + len(episode["test"])
                audit = prototype.audit_episode(episode, selected)
                if audit["surviving_declared_rules"] != [selected] or audit["harmful_shortcut_survivors"]:
                    failures.append({"seed": seed, "setting": selected, "demos": demos, "audit": audit})
                metrics = prototype.input_metrics(episode["test"][-1]["input"])
                if metrics["height"] == metrics["width"] == 30 and metrics["boundary_sides"] == ["bottom", "left", "right", "top"]:
                    stress_pairs += 1
                else:
                    failures.append({"seed": seed, "setting": selected, "demos": demos, "stress": metrics})
                if demos == 3:
                    matched[selected] = [pair["input"] for pair in episode["train"] + episode["test"]]
            minimum = adapter.generate(seed, setting, 2, 1)
            full = adapter.generate(seed, setting, 6, 4)
            if minimum["train"] != full["train"][:2] or minimum["test"] != full["test"][:1]:
                failures.append({"seed": seed, "setting": selected, "prefix": False})
        if matched[prototype.CANONICAL] != matched[prototype.ALTERNATE]:
            failures.append({"seed": seed, "matched_inputs": False})

    report = {
        "schema": "ff973026bfbe-parametric-audit-v1",
        "seeds": args.seeds,
        "episodes": episodes,
        "labeled_pairs": pairs,
        "stress_30x30_pairs": stress_pairs,
        "declared_shortcuts": sorted(prototype.SHORTCUTS),
        "failure_count": len(failures),
        "failures": failures[:32],
        "status": "passed" if not failures else "failed",
    }
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    print(body, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
