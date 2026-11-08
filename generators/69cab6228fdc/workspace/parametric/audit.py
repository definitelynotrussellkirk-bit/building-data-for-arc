"""Protected-Racket teaching and sampler audit for the recolor-scope family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parent
SETTINGS = ("all_sources", "most_frequent_source")


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_audit_69cab6228fdc_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _write(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run(out: Path, *, seeds=(0, 17, 41), demos=2, queries=4):
    adapter = _load_adapter()
    wrapped = {}
    evaluations = 0
    episodes = []
    witnesses = []
    causal_case = None
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
            for setting in SETTINGS:
                settings = {"recolor_scope": setting}
                episode = adapter.generate(seed, settings, demos, queries)
                selected_program = adapter.program(settings)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = execute(selected_program, pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError((seed, setting, split, index, "selected parity"))
                competitors = []
                other = SETTINGS[1 - SETTINGS.index(setting)]
                competitors.append((f"setting:{other}", adapter.program({"recolor_scope": other}), lambda g, other=other: adapter.transform(g, other)))
                competitors.extend((name, adapter.rival_program(name), lambda g, name=name: adapter.rival_transform(g, name)) for name in adapter.RIVALS)
                survivors = []
                for name, competitor_program, mirror in competitors:
                    demo_outputs = []
                    first_difference = None
                    for index, pair in enumerate(episode["train"]):
                        actual = execute(competitor_program, pair["input"])
                        if actual != mirror(pair["input"]):
                            raise AssertionError((seed, setting, name, index, "rival parity"))
                        demo_outputs.append(actual)
                        if actual != pair["output"] and first_difference is None:
                            first_difference = {"seed": seed, "settings": settings, "rival": name, "split": "train", "pair_index": index}
                    survives = all(actual == pair["output"] for actual, pair in zip(demo_outputs, episode["train"], strict=True))
                    query_changes = False
                    if survives:
                        for pair in episode["test"]:
                            if execute(competitor_program, pair["input"]) != pair["output"]:
                                query_changes = True
                                break
                    if survives and query_changes:
                        survivors.append(name)
                    if first_difference is not None:
                        witnesses.append(first_difference)
                if survivors:
                    raise AssertionError((seed, setting, "query-changing demo survivors", survivors))
                if setting == "most_frequent_source" and causal_case is None:
                    for split in ("train", "test"):
                        for pair_index, pair in enumerate(episode[split]):
                            facts = adapter.analyze(pair["input"])
                            if facts["most_frequent_source"] == facts["sources"][0]:
                                continue
                            counter = adapter.rival_program("first_source_only")
                            counter_output = execute(counter, pair["input"])
                            if counter_output == pair["output"]:
                                continue
                            causal_case = {
                                "settings": settings,
                                "program": selected_program,
                                "input": pair["input"],
                                "output": pair["output"],
                                "counterfactual_program": counter,
                                "counterfactual_output": counter_output,
                                "intermediate_value": {
                                    "source_counts": facts["source_counts"],
                                    "selected_source": facts["most_frequent_source"],
                                    "wrong_source": facts["sources"][0],
                                    "mapping": facts["mapping"],
                                },
                                "ablation": "wrong_intermediate",
                            }
                            break
                        if causal_case is not None:
                            break
                episodes.append({"seed": seed, "settings": settings, "demo_survivors_that_change_query": survivors})

    sampler = {"prefix_checks": 0, "episodes": 0, "pairs": 0, "exact_30x30": 0, "selected_positions": {"first": 0, "middle": 0, "last": 0}}
    for seed in range(128):
        for setting in SETTINGS:
            settings = {"recolor_scope": setting}
            small = adapter.generate(seed, settings, 2, 1)
            large = adapter.generate(seed, settings, 6, 4)
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError((seed, setting, "prefix instability"))
            inputs = [pair["input"] for pair in large["train"] + large["test"]]
            if len({repr(grid) for grid in inputs}) != len(inputs):
                raise AssertionError((seed, setting, "duplicate inputs"))
            for grid in inputs:
                facts = adapter.analyze(grid)
                position = facts["sources"].index(facts["most_frequent_source"])
                label = "first" if position == 0 else "last" if position == len(facts["sources"]) - 1 else "middle"
                sampler["selected_positions"][label] += 1
                sampler["exact_30x30"] += int((len(grid), len(grid[0])) == (30, 30))
            sampler["prefix_checks"] += 1
            sampler["episodes"] += 1
            sampler["pairs"] += len(inputs)
    if causal_case is None:
        raise AssertionError("no causal case")
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "task_id": "69cab6228fdc",
        "status": "passed",
        "scope": {"seeds": list(seeds), "demos": demos, "queries": queries, "rivals": ["other_setting", *_load_adapter().RIVALS], "universal_identifiability": False},
        "racket": {key: identity[key] for key in identity if key in {"schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"}},
        "racket_evaluations": evaluations,
        "episodes": episodes,
        "finite_rival_witnesses": witnesses,
        "query_changing_demo_survivors": [],
        "sampler": sampler,
        "limits": "Finite declared settings/rivals, three Racket-audited seeds and 128 prefix-stress seeds; no universal uniqueness claim.",
    }
    _write(out / "self_audit.json", report)
    _write(out / "audited_case.json", causal_case)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({"status": report["status"], "racket_evaluations": report["racket_evaluations"], "episodes": len(report["episodes"]), "sampler": report["sampler"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
