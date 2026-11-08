#!/usr/bin/env python3
"""Bounded protected-Racket audit for the stamped-cluster family.

This is intentionally reusable by later reviewers.  It checks matched inputs,
count-independent prefixes, finite teaching rivals, public one-query projection,
30x30 stress, exact Python/Racket parity, and retains one causal counterfactual.
The finite rival set is evidence, not a universal uniqueness proof.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for path in (ROOT / "src", ROOT / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

TASK_ID = "b83ad00fc681"
SEEDS = (0, 17, 97)
DEMO_COUNTS = (2, 3, 6)


def _load():
    path = HERE / "prototype.py"
    name = "_b83_parametric_audit_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load()


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(source)} {_literal(grid)})")


def _grid_hash(grid: Any) -> str:
    raw = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _diff_cells(left, right) -> int:
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def run(out: Path) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    evaluations = 0
    cache_hits = 0
    public_checks = 0
    matched_checks = 0
    stress_checks = 0
    cache: dict[tuple[str, str], list[list[int]]] = {}
    programs = {finish: P.program({"finish": finish}) for finish in P.FINISHES}

    def execute(bridge, source, grid):
        nonlocal evaluations, cache_hits
        key = (hashlib.sha256(source.encode()).hexdigest(), _grid_hash(grid))
        if key in cache:
            cache_hits += 1
            return deepcopy(cache[key])
        value = _execute(bridge, source, grid)
        cache[key] = deepcopy(value)
        evaluations += 1
        return value

    causal_case = None
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket is required")
        for seed in SEEDS:
            maximal = {
                finish: P.generate(seed, {"finish": finish}, 6, 4)
                for finish in P.FINISHES
            }
            for demos in DEMO_COUNTS:
                current = {
                    finish: P.generate(seed, {"finish": finish}, demos, 4)
                    for finish in P.FINISHES
                }
                left, right = (current[P.FINISHES[0]], current[P.FINISHES[1]])
                left_inputs = [pair["input"] for pair in left["train"] + left["test"]]
                right_inputs = [pair["input"] for pair in right["train"] + right["test"]]
                matched_checks += 1
                if left_inputs != right_inputs:
                    failures.append({"seed": seed, "demos": demos, "kind": "settings_changed_inputs"})
                for finish, episode in current.items():
                    if episode["train"] != maximal[finish]["train"][:demos] or episode["test"] != maximal[finish]["test"]:
                        failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "prefix_instability"})
                    encoded = [_grid_hash(pair["input"]) for pair in episode["train"] + episode["test"]]
                    if len(encoded) != len(set(encoded)):
                        failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "duplicate_inputs"})
                    teaching = P.teaching_check(episode, {"finish": finish})
                    if teaching["survivors"] != [finish] or teaching["harmful_survivors"]:
                        failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "teaching", "check": teaching})
                    for pair in episode["train"] + episode["test"]:
                        actual = execute(bridge, programs[finish], pair["input"])
                        if actual != pair["output"]:
                            failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "racket_parity"})
                    for query_index in range(4):
                        public = P.public_turn(episode, query_index)
                        raw = public_challenge_bytes(public)
                        if public_challenge_id(public) != hashlib.sha256(raw).hexdigest():
                            failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "public_id"})
                        if set(public) != {"train", "test"} or len(public["test"]) != 1 or "output" in public["test"][0]:
                            failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "public_projection"})
                        public_checks += 1
                    if len(episode["test"][-1]["input"]) == 30 and len(episode["test"][-1]["input"][0]) == 30:
                        stress_checks += 1
                    else:
                        failures.append({"seed": seed, "demos": demos, "finish": finish, "kind": "missing_30x30"})
                    rows.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": {"finish": finish},
                        "survivors": teaching["survivors"],
                        "harmful_survivors": teaching["harmful_survivors"],
                    })

        episode = P.generate(17, {"finish": "highlight_largest_stamped_cluster"}, 3, 4)
        grid = episode["test"][3]["input"]
        intended = execute(bridge, programs["highlight_largest_stamped_cluster"], grid)
        wrong_source = P.counterfactual_program()
        wrong = execute(bridge, wrong_source, grid)
        info = P.intermediate(grid)
        if intended == wrong:
            failures.append({"kind": "causal_counterfactual_unchanged"})
        causal_case = {
            "settings": {"finish": "highlight_largest_stamped_cluster"},
            "program": programs["highlight_largest_stamped_cluster"],
            "input": grid,
            "output": intended,
            "counterfactual_program": wrong_source,
            "counterfactual_output": wrong,
            "intermediate_value": {
                "binary_stamped_component_sizes": info["cluster_sizes"],
                "selected_size": len(info["target_cells"]),
            },
            "ablation": "wrong_intermediate",
            "different_cells": _diff_cells(intended, wrong),
        }

    report = {
        "schema": "arcpuzzles-b83ad00fc681-parametric-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "scope": "Seeds 0/17/97, demo prefixes 2/3/6, both exact programs, four queries, and four declared Python rivals; finite evidence is not universal uniqueness.",
        "racket": identity,
        "seeds": list(SEEDS),
        "demo_counts": list(DEMO_COUNTS),
        "settings": list(P.FINISHES),
        "declared_rivals": list(P.RIVAL_NAMES),
        "counts": {
            "jobs": len(rows),
            "protected_racket_evaluations": evaluations,
            "racket_cache_hits": cache_hits,
            "matched_input_checks": matched_checks,
            "public_projection_checks": public_checks,
            "thirty_by_thirty_checks": stress_checks,
        },
        "rows": rows,
        "causal_case": causal_case,
        "failures": failures,
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (out / "causal-case.json").write_text(json.dumps(causal_case, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], **report["counts"], "failures": failures}, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return 0 if run(args.out)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
