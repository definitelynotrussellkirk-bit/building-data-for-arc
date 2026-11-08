"""Bounded protected-Racket audit for the endpoint-cap parametric family.

Checks exact Racket/Python parity, visible-example identifiability, eight
plausible wrong rules, prefix stability, matched inputs, public projection
privacy, and a source-bound post-cap-connectivity counterfactual.
"""
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

HERE = Path(__file__).resolve().parent
TASK_ID = "577d2db13443"


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_audit_577d2db13443_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _freeze(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def run(
    out: Path,
    *,
    seeds: tuple[int, ...] = (0, 17, 97),
    demo_counts: tuple[int, ...] = (2, 3, 6),
    queries: int = 4,
) -> dict[str, Any]:
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    adapter = _load_adapter()
    wrapped: dict[str, str] = {}
    cache: dict[tuple[str, str], list[list[int]]] = {}
    evaluations = 0
    episodes: list[dict[str, Any]] = []
    witnesses: dict[str, dict[str, Any]] = {}
    causal_case: dict[str, Any] | None = None

    bridge = RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=96)
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket is required")

        def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            key = (hashlib.sha256(program.encode()).hexdigest(), _freeze(grid))
            if key not in cache:
                wrapped.setdefault(program, wrap_rule(program))
                cache[key] = bridge.eval_text(f"({wrapped[program]} {_literal(grid)})")
                evaluations += 1
            return cache[key]

        canonical = adapter.program({"finish": "caps_only"})
        canonical_sha = hashlib.sha256(canonical.encode()).hexdigest()
        expected_sha = "a811558a15fb8476dc33ee271dc391ab53717b42ff625990feffa515ddda14c9"
        if canonical_sha != expected_sha:
            raise AssertionError(("canonical byte drift", canonical_sha))

        for seed in seeds:
            for demos in demo_counts:
                by_setting = {
                    json.dumps(setting, sort_keys=True): adapter.generate(seed, setting, demos, queries)
                    for setting in adapter.SETTINGS
                }
                input_sequences = [
                    [pair["input"] for pair in episode["train"] + episode["test"]]
                    for episode in by_setting.values()
                ]
                if input_sequences[1:] != input_sequences[:-1]:
                    raise AssertionError((seed, demos, "settings confound inputs"))
                if len({_freeze(grid) for grid in input_sequences[0]}) != demos + queries:
                    raise AssertionError((seed, demos, "duplicate visible input"))

                for setting in adapter.SETTINGS:
                    episode = by_setting[json.dumps(setting, sort_keys=True)]
                    selected_program = adapter.program(setting)
                    for split in ("train", "test"):
                        for pair_index, pair in enumerate(episode[split]):
                            actual = execute(selected_program, pair["input"])
                            if actual != pair["output"]:
                                raise AssertionError((seed, demos, setting, split, pair_index, "label mismatch"))

                    setting_survivors = [
                        candidate
                        for candidate in adapter.SETTINGS
                        if all(
                            execute(adapter.program(candidate), pair["input"]) == pair["output"]
                            for pair in episode["train"]
                        )
                    ]
                    if setting_survivors != [setting]:
                        raise AssertionError((seed, demos, setting, "setting survivors", setting_survivors))

                    rival_rows = []
                    for rival in adapter.RIVALS_BY_FINISH[setting["finish"]]:
                        rival_program = adapter.rival_program(setting, rival)
                        rival_key = f"{setting['finish']}:{rival}"
                        first_difference = None
                        survives = True
                        for pair_index, pair in enumerate(episode["train"]):
                            claimed = adapter.rival_output(pair["input"], setting, rival)
                            if claimed != pair["output"]:
                                survives = False
                                if first_difference is None:
                                    first_difference = (pair_index, pair, claimed)
                        if survives:
                            raise AssertionError((seed, demos, setting, "surviving rival", rival))
                        # One protected-Racket source-bound witness per rival is enough to
                        # bind the executable wrong rule; Python checks every visible demo.
                        if rival_key not in witnesses and first_difference is not None:
                            pair_index, pair, claimed = first_difference
                            actual = execute(rival_program, pair["input"])
                            if actual != claimed:
                                raise AssertionError((seed, demos, setting, rival, pair_index, "rival parity"))
                            witnesses[rival_key] = {
                                "seed": seed,
                                "demos": demos,
                                "settings": setting,
                                "rival": rival,
                                "pair_index": pair_index,
                                "input": pair["input"],
                                "selected_output": pair["output"],
                                "rival_output": actual,
                                "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                                "rival_program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
                            }
                        rival_rows.append({"name": rival, "survives_all_demos": survives})

                    teaching = adapter.teaching_check(episode, setting)
                    if teaching["survivors"] != [setting] or teaching["surviving_rivals"]:
                        raise AssertionError((seed, demos, setting, "Python teaching check", teaching))

                    if setting["finish"] == "highlight_largest_cap_component" and causal_case is None:
                        for split in ("train", "test"):
                            for pair_index, pair in enumerate(episode[split]):
                                counterfactual = adapter.rival_program(setting, "largest_cap_bbox")
                                counterfactual_output = execute(counterfactual, pair["input"])
                                if counterfactual_output == pair["output"]:
                                    continue
                                stats = adapter.cap_component_stats(pair["input"])
                                causal_case = {
                                    "settings": setting,
                                    "program": selected_program,
                                    "input": pair["input"],
                                    "output": pair["output"],
                                    "counterfactual_program": counterfactual,
                                    "counterfactual_output": counterfactual_output,
                                    "intermediate_value": {
                                        "post_cap_components": stats,
                                        "selected_by_occupied_cells": max(stats, key=lambda row: row["size"]),
                                        "wrong_selection_by_bbox_area": max(stats, key=lambda row: row["bbox_area"]),
                                    },
                                    "ablation": "wrong_intermediate",
                                    "selection": {
                                        "seed": seed,
                                        "demos": demos,
                                        "split": split,
                                        "pair_index": pair_index,
                                    },
                                }
                                break
                            if causal_case is not None:
                                break

                    episodes.append({
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "settings": setting,
                        "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                        "setting_survivors": setting_survivors,
                        "rivals": rival_rows,
                    })

        prefix_checks = 0
        public_checks = 0
        query_orders: set[tuple[tuple[int, int], ...]] = set()
        large_positions: set[int] = set()
        for seed in range(64):
            full_by_setting = [adapter.generate(seed, setting, 6, 4) for setting in adapter.SETTINGS]
            left_inputs = [pair["input"] for pair in full_by_setting[0]["train"] + full_by_setting[0]["test"]]
            right_inputs = [pair["input"] for pair in full_by_setting[1]["train"] + full_by_setting[1]["test"]]
            if left_inputs != right_inputs:
                raise AssertionError((seed, "full matched inputs"))
            for setting, full in zip(adapter.SETTINGS, full_by_setting, strict=True):
                for demos in range(2, 7):
                    for query_count in range(1, 5):
                        episode = adapter.generate(seed, setting, demos, query_count)
                        if episode["train"] != full["train"][:demos] or episode["test"] != full["test"][:query_count]:
                            raise AssertionError((seed, setting, demos, query_count, "prefix instability"))
                        prefix_checks += 1
                for query_index in range(4):
                    public = adapter.public_turn(full, query_index)
                    if set(public) != {"train", "test"} or public["test"] != [{"input": full["test"][query_index]["input"]}]:
                        raise AssertionError((seed, setting, query_index, "public projection"))
                    raw = json.dumps(public, sort_keys=True)
                    if any(token in raw for token in ("program_solution", "highlight_largest", "settings", "seed", "query_count")):
                        raise AssertionError((seed, setting, query_index, "private metadata leak"))
                    public_checks += 1
            order = tuple((len(pair["input"]), len(pair["input"][0])) for pair in full_by_setting[0]["test"])
            query_orders.add(order)
            large_positions.add(order.index((30, 30)))
        if len(query_orders) < 2 or len(large_positions) < 2:
            raise AssertionError("query order does not vary independently")
    finally:
        bridge.shutdown()

    expected_witnesses = sum(len(names) for names in adapter.RIVALS_BY_FINISH.values())
    if len(witnesses) != expected_witnesses:
        raise AssertionError(("missing finite-rival witnesses", len(witnesses), expected_witnesses))
    if causal_case is None:
        raise AssertionError("no causal wrong-intermediate case found")

    source_files = sorted(
        [HERE / "adapter.py", HERE / "audit.py", HERE / "promotion.json", HERE / "README.md"]
        + list(HERE.glob("*.rkt")),
        key=lambda path: path.name,
    )
    report = {
        "schema": "arcpuzzles-parametric-teaching-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": {
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "queries": queries,
            "settings": list(adapter.SETTINGS),
            "rivals_by_finish": {key: list(value) for key, value in adapter.RIVALS_BY_FINISH.items()},
        },
        "racket": identity,
        "racket_evaluations": evaluations,
        "episodes": episodes,
        "witnesses": list(witnesses.values()),
        "sampler": {
            "prefix_checks": prefix_checks,
            "public_projection_checks": public_checks,
            "distinct_query_orders": len(query_orders),
            "large_query_positions": sorted(large_positions),
        },
        "source": {path.name: _sha(path) for path in source_files},
        "limits": (
            "Finite authored settings, eight declared rivals, three protected-Racket seeds, "
            "and 64 deterministic prefix/privacy seeds only; no universal uniqueness or learning claim."
        ),
        "training_admitted": False,
    }
    out.mkdir(parents=True, exist_ok=False)
    _write(out / "self_audit.json", report)
    _write(out / "audited_case.json", causal_case)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17, 97])
    args = parser.parse_args(argv)
    report = run(args.out, seeds=tuple(args.seeds))
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
