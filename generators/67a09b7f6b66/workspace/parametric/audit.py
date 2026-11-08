"""Protected-Racket teaching and sampler audit for the chamber-legend family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parent
RIVALS_BY_SETTING = {
    "absolute_count": ("position_only", "occupied_rows", "fixed_anchor_2", "fixed_anchor_3"),
    "anchor_cycle": ("position_only", "occupied_rows", "fixed_anchor_1", "fixed_anchor_2", "fixed_anchor_3"),
}


def _load_adapter():
    path = HOME / "adapter.py"
    name = "_audit_67a09_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run(out: Path, *, seeds: tuple[int, ...] = (0, 17, 41), demos: int = 3, queries: int = 4):
    adapter = _load_adapter()
    wrapped: dict[str, str] = {}
    evaluations = 0

    with RacketBridge(timeout=30, startup_timeout=60) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket is required")

        def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            evaluations += 1
            return bridge.eval_text(f"({wrapped[program]} {_literal(grid)})")

        episodes = []
        witnesses: dict[str, dict[str, Any]] = {}
        causal_case = None
        sampler = {
            "episodes": 0,
            "pairs": 0,
            "anchor_counts": {"1": 0, "2": 0, "3": 0},
            "anchor_chambers": {"0": 0, "1": 0, "2": 0},
            "wall_shared": 0,
            "exact_30x30": 0,
            "prefix_checks": 0,
        }

        for seed in seeds:
            for setting in ("absolute_count", "anchor_cycle"):
                settings = {"legend_mapping": setting}
                episode = adapter.generate(seed, settings, demos, queries)
                selected_program = adapter.program(settings)
                selected_outputs = []
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(episode[split]):
                        actual = execute(selected_program, pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError((seed, setting, split, pair_index, "selected label mismatch"))
                        selected_outputs.append(actual)
                        facts = adapter.analyze(pair["input"])
                        sampler["pairs"] += 1
                        sampler["anchor_counts"][str(facts["anchor_count"])] += 1
                        sampler["anchor_chambers"][str(facts["anchor_chamber"])] += 1
                        sampler["wall_shared"] += int(8 in facts["legend"])
                        sampler["exact_30x30"] += int((facts["height"], facts["width"]) == (30, 30))
                survivors = []
                rival_summaries = []
                for rival in RIVALS_BY_SETTING[setting]:
                    rival_program = adapter.rival_program(rival)
                    demo_outputs = []
                    first_difference = None
                    for pair_index, pair in enumerate(episode["train"]):
                        actual = execute(rival_program, pair["input"])
                        claimed = adapter.rival_transform(pair["input"], rival)
                        if actual != claimed:
                            raise AssertionError((seed, setting, rival, pair_index, "rival parity mismatch"))
                        demo_outputs.append(actual)
                        if actual != pair["output"] and first_difference is None:
                            first_difference = {
                                "seed": seed,
                                "setting": setting,
                                "rival": rival,
                                "split": "train",
                                "pair_index": pair_index,
                                "input": pair["input"],
                                "selected_output": pair["output"],
                                "rival_output": actual,
                                "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                                "rival_program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
                            }
                    survives = all(
                        output == pair["output"]
                        for output, pair in zip(demo_outputs, episode["train"], strict=True)
                    )
                    if survives:
                        survivors.append(rival)
                    if first_difference is not None:
                        witnesses.setdefault(f"{setting}:{rival}", first_difference)
                    rival_summaries.append({"name": rival, "survives_all_demos": survives})
                if survivors:
                    raise AssertionError((seed, setting, "demo-surviving rivals", survivors))

                if setting == "anchor_cycle" and causal_case is None:
                    for split in ("train", "test"):
                        for pair_index, pair in enumerate(episode[split]):
                            facts = adapter.analyze(pair["input"])
                            if facts["anchor_count"] == 1:
                                continue
                            counterfactual_program = adapter.rival_program("fixed_anchor_1")
                            counterfactual_output = execute(counterfactual_program, pair["input"])
                            if counterfactual_output == pair["output"]:
                                continue
                            causal_case = {
                                "settings": settings,
                                "program": selected_program,
                                "input": pair["input"],
                                "output": pair["output"],
                                "counterfactual_program": counterfactual_program,
                                "counterfactual_output": counterfactual_output,
                                "intermediate_value": {
                                    "anchor_chamber": facts["anchor_chamber"],
                                    "anchor_count": facts["anchor_count"],
                                    "count_order": facts["count_order"],
                                },
                                "ablation": "wrong_intermediate",
                                "selection": {
                                    "seed": seed,
                                    "split": split,
                                    "pair_index": pair_index,
                                },
                            }
                            break
                        if causal_case is not None:
                            break

                episodes.append({
                    "seed": seed,
                    "settings": settings,
                    "counts": {"demos": demos, "queries": queries},
                    "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                    "rivals": rival_summaries,
                    "demo_survivors": survivors,
                })
                sampler["episodes"] += 1

        # Cheap deterministic/prefix/count-boundary sampler pass without more Racket calls.
        for seed in range(64):
            for setting in ("absolute_count", "anchor_cycle"):
                settings = {"legend_mapping": setting}
                small = adapter.generate(seed, settings, 2, 1)
                large = adapter.generate(seed, settings, 6, 4)
                if small["train"] != large["train"][:2] or small["test"][0] != large["test"][0]:
                    raise AssertionError((seed, setting, "prefix instability"))
                if len({json.dumps(pair["input"]) for pair in large["train"] + large["test"]}) != 10:
                    raise AssertionError((seed, setting, "duplicate inputs"))
                sampler["prefix_checks"] += 1

    if causal_case is None:
        raise AssertionError("no wrong-intermediate causal case was found")
    if len(witnesses) != sum(len(value) for value in RIVALS_BY_SETTING.values()):
        raise AssertionError(("missing finite-rival witnesses", sorted(witnesses)))

    source = {
        "adapter": "generators/67a09b7f6b66/workspace/parametric/adapter.py",
        "adapter_sha256": _sha(HOME / "adapter.py"),
        "native_sha256": _sha(HOME / "native.py"),
        "canonical_sha256": _sha(HOME / "canonical.rkt"),
        "anchor_cycle_sha256": _sha(HOME / "anchor_cycle.rkt"),
        "promotion_sha256": _sha(HOME / "promotion.json"),
    }
    report = {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "task_id": "67a09b7f6b66",
        "status": "passed",
        "scope": {
            "seeds": list(seeds),
            "demos": demos,
            "queries": queries,
            "rivals_by_setting": {key: list(value) for key, value in RIVALS_BY_SETTING.items()},
            "sampler_prefix_seeds": 64,
            "universal_identifiability": False,
        },
        "source": source,
        "racket": {
            key: identity[key]
            for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "racket_evaluations": evaluations,
        "episodes": episodes,
        "witnesses": list(witnesses.values()),
        "sampler": sampler,
        "query_changing_demo_survivors": [],
        "limits": "Finite rival set, three Racket-audited seeds and 64 prefix-stress seeds; no universal uniqueness claim.",
    }
    out.mkdir(parents=True, exist_ok=False)
    _write(out / "self_audit.json", report)
    _write(out / "audited_case.json", causal_case)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "episodes": len(report["episodes"]),
        "racket_evaluations": report["racket_evaluations"],
        "witnesses": len(report["witnesses"]),
        "sampler": report["sampler"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
