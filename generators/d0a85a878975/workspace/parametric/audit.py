#!/usr/bin/env python3
"""Bounded deterministic self-audit for the square-tally block-order family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_adapter():
    path = HERE / "adapter.py"
    body = path.read_bytes()
    name = "_d0_audit_" + hashlib.sha256(path.as_posix().encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signature(grid):
    return json.dumps(grid, separators=(",", ":"))


def sweep(adapter, seeds: range) -> dict:
    failures = []
    episodes = pairs = public_turns = matched = 0
    sizes = set()
    profiles = set()
    for seed in seeds:
        full_by_setting = {
            setting: adapter.generate(seed, {"block_order": setting}, 6, 4)
            for setting in adapter.BLOCK_ORDERS
        }
        expected_inputs = None
        for setting, full in full_by_setting.items():
            inputs = [signature(pair["input"]) for pair in full["train"] + full["test"]]
            if expected_inputs is None:
                expected_inputs = inputs
            elif inputs != expected_inputs:
                failures.append({"seed": seed, "setting": setting, "code": "setting_dependent_inputs"})
            if len(inputs) != len(set(inputs)):
                failures.append({"seed": seed, "setting": setting, "code": "duplicate_input"})
            for pair in full["train"] + full["test"]:
                facts = adapter.analyze(pair["input"])
                sizes.add((facts["grid_h"], facts["grid_w"]))
                profiles.add((tuple(facts["sizes"]), tuple(facts["raw_counts"].get(s, 0) for s in facts["sizes"])))
                if pair["output"] != adapter.solve(pair["input"], {"block_order": setting}):
                    failures.append({"seed": seed, "setting": setting, "code": "claim_mismatch"})
                if adapter.solve(pair["input"], {"block_order": "construction"}) == adapter.solve(
                    pair["input"], {"block_order": "reverse_construction"}
                ):
                    failures.append({"seed": seed, "setting": setting, "code": "settings_do_not_disagree"})
            report = adapter.lesson_report(
                {"train": full["train"][:2], "test": full["test"]},
                {"block_order": setting},
            )
            if report["surviving_rivals"] or report["query_disagreements"]:
                failures.append({"seed": seed, "setting": setting, "code": "teaching_hole", "report": report})
        matched += 1
        for demos in range(2, 7):
            for queries in range(1, 5):
                for setting in adapter.BLOCK_ORDERS:
                    episode = adapter.generate(seed, {"block_order": setting}, demos, queries)
                    full = full_by_setting[setting]
                    if episode["train"] != full["train"][:demos] or episode["test"] != full["test"][:queries]:
                        failures.append({"seed": seed, "setting": setting, "demos": demos, "queries": queries, "code": "prefix_instability"})
                    episodes += 1
                    pairs += demos + queries
                    for index in range(queries):
                        view = adapter.public_turn(episode, index)
                        if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
                            failures.append({"seed": seed, "setting": setting, "code": "public_projection_leak"})
                        public_turns += 1
    if (30, 30) not in sizes:
        failures.append({"code": "missing_30x30"})
    return {
        "seeds": list(seeds),
        "episodes": episodes,
        "pairs": pairs,
        "public_turns": public_turns,
        "matched_input_comparisons": matched,
        "grid_sizes": [list(item) for item in sorted(sizes)],
        "profiles": [[list(sizes_), list(counts)] for sizes_, counts in sorted(profiles)],
        "failures": failures,
    }


def protected_racket(adapter) -> dict:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    cache = {}
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError(f"unexpected Racket identity: {identity}")
        for seed in (0, 17):
            for setting in adapter.BLOCK_ORDERS:
                settings = {"block_order": setting}
                episode = adapter.generate(seed, settings, 2, 4)
                wrapped = wrap_rule(adapter.program(settings))
                for pair in episode["train"] + episode["test"]:
                    key = (setting, signature(pair["input"]))
                    if key not in cache:
                        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                        cache[key] = bridge.eval_text(f"({wrapped} {literal})")
                    if cache[key] != pair["output"]:
                        raise AssertionError(f"Python/Racket disagreement for {seed}/{setting}")
        return {"identity": identity, "evaluations": len(cache), "seeds": [0, 17]}
    finally:
        bridge.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=16)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 128:
        parser.error("--seeds must be in 1..128")
    if args.out.exists():
        parser.error("--out must not already exist")
    adapter = load_adapter()
    report = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "d0a85a878975",
        "settings": [dict(item) for item in adapter.SETTINGS],
        "bounded_scope": "finite seeds and declared rivals only; not universal uniqueness or owner acceptance",
    }
    report["sweep"] = sweep(adapter, range(args.seeds))
    report["protected_racket"] = protected_racket(adapter)
    report["status"] = "passed" if not report["sweep"]["failures"] else "failed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "episodes": report["sweep"]["episodes"], "pairs": report["sweep"]["pairs"], "racket_evaluations": report["protected_racket"]["evaluations"]}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
