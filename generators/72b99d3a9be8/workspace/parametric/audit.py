"""Bounded protected-Racket and sampler audit for 72b99d3a9be8."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_audit_72_adapter_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run(out: Path, *, seeds=(0, 17, 41), demos=2, queries=4):
    adapter = _load_adapter()
    colors = (2, 3)
    wrapped = {}
    evaluations = 0
    episodes = []
    causal = None
    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket is required")

        def execute(program, grid):
            nonlocal evaluations
            wrapped.setdefault(program, wrap_rule(program))
            evaluations += 1
            return bridge.eval_text(f"({wrapped[program]} {_literal(grid)})")

        for seed in seeds:
            for color in colors:
                settings = {"reflector_color": color}
                episode = adapter.generate(seed, settings, demos, queries)
                selected = adapter.program(settings)
                other_color = 3 if color == 2 else 2
                other = adapter.program({"reflector_color": other_color})
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = execute(selected, pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError((seed, color, split, index, "selected parity"))
                        other_actual = execute(other, pair["input"])
                        if split == "train" and other_actual == pair["output"]:
                            raise AssertionError((seed, color, split, index, "other setting survived"))
                        if color == 3 and causal is None and other_actual != pair["output"]:
                            causal = {
                                "settings": settings,
                                "program": selected,
                                "input": pair["input"],
                                "output": pair["output"],
                                "counterfactual_program": other,
                                "counterfactual_output": other_actual,
                                "intermediate_value": adapter.dependency_intermediate(pair["input"], color),
                                "counterfactual_intermediate_value": adapter.dependency_intermediate(pair["input"], other_color),
                                "ablation": "wrong_intermediate",
                            }
                audit = adapter.audit_episode(episode, color)
                if audit["survivors"] != [f"setting:{color}"] or audit["ambiguous_query_rivals"]:
                    raise AssertionError((seed, color, audit))
                episodes.append({"seed": seed, "settings": settings, "audit": audit})

    sampler = {"prefix_checks": 0, "episodes": 0, "pairs": 0, "exact_30x30": 0}
    for seed in range(128):
        for color in colors:
            settings = {"reflector_color": color}
            small = adapter.generate(seed, settings, 2, 4)
            large = adapter.generate(seed, settings, 6, 4)
            if small["train"] != large["train"][:2] or small["test"] != large["test"]:
                raise AssertionError((seed, color, "prefix instability"))
            pairs = large["train"] + large["test"]
            if len({json.dumps(p["input"], separators=(",", ":")) for p in pairs}) != len(pairs):
                raise AssertionError((seed, color, "duplicate inputs"))
            sampler["prefix_checks"] += 1
            sampler["episodes"] += 1
            sampler["pairs"] += len(pairs)
            sampler["exact_30x30"] += sum((len(p["input"]), len(p["input"][0])) == (30, 30) for p in pairs)
    if causal is None:
        raise AssertionError("no causal case")
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "task_id": "72b99d3a9be8",
        "status": "passed",
        "scope": {
            "seeds": list(seeds),
            "demos": demos,
            "queries": queries,
            "rivals": [
                "other_setting", "identity", "straight", "stop_at_reflector",
                "wrong_axis", "forward_only", "backward_only",
            ],
            "universal_identifiability": False,
        },
        "racket": {k: identity[k] for k in identity if k in {
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
            "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
        }},
        "racket_evaluations": evaluations,
        "episodes": episodes,
        "query_changing_demo_survivors": [],
        "sampler": sampler,
        "limits": "Finite declared settings/rivals, three protected-Racket seeds and 128 prefix-stress seeds; no universal uniqueness claim.",
    }
    _write(out / "self_audit.json", report)
    _write(out / "audited_case.json", causal)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "racket_evaluations": report["racket_evaluations"],
        "sampler": report["sampler"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
