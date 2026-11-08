#!/usr/bin/env python3
"""Bounded deterministic self-audit for the quadrant-divider family."""
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
    name = "_3fb_audit_" + hashlib.sha256(path.as_posix().encode() + body).hexdigest()
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
    bboxes = set()
    colors = set()
    block_missing = set()
    frame_missing = set()
    for seed in seeds:
        full_by_setting = {
            setting: adapter.generate(seed, {"divider_reference": setting}, 6, 4)
            for setting in adapter.DIVIDER_REFERENCES
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
                sizes.add(tuple(facts["grid_size"]))
                bboxes.add(tuple(facts["frame_bbox"]))
                colors.add(tuple(sorted(facts["colors"])))
                block_missing.add(facts["block_midrange_missing_quadrant"])
                frame_missing.add(facts["frame_midpoint_missing_quadrant"])
                if pair["output"] != adapter.solve(pair["input"], {"divider_reference": setting}):
                    failures.append({"seed": seed, "setting": setting, "code": "claim_mismatch"})
                if adapter.solve(pair["input"], {"divider_reference": "block_midrange"}) == adapter.solve(
                    pair["input"], {"divider_reference": "frame_midpoint"}
                ):
                    failures.append({"seed": seed, "setting": setting, "code": "settings_do_not_disagree"})
                if len({tuple(item) for item in facts["block_midrange_quadrants"]}) != 3:
                    failures.append({"seed": seed, "setting": setting, "code": "block_divider_collision"})
                if len({tuple(item) for item in facts["frame_midpoint_quadrants"]}) != 3:
                    failures.append({"seed": seed, "setting": setting, "code": "frame_divider_collision"})
            report = adapter.lesson_report(
                {"train": full["train"][:2], "test": full["test"]},
                {"divider_reference": setting},
            )
            if report["surviving_rivals"] or report["query_disagreements"]:
                failures.append({"seed": seed, "setting": setting, "code": "teaching_hole", "report": report})
        matched += 1
        for demos in range(2, 7):
            for queries in range(1, 5):
                for setting in adapter.DIVIDER_REFERENCES:
                    episode = adapter.generate(seed, {"divider_reference": setting}, demos, queries)
                    full = full_by_setting[setting]
                    if episode["train"] != full["train"][:demos] or episode["test"] != full["test"][:queries]:
                        failures.append({
                            "seed": seed,
                            "setting": setting,
                            "demos": demos,
                            "queries": queries,
                            "code": "prefix_instability",
                        })
                    episodes += 1
                    pairs += demos + queries
                    for index in range(queries):
                        view = adapter.public_turn(episode, index)
                        if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
                            failures.append({"seed": seed, "setting": setting, "code": "public_projection_leak"})
                        public_turns += 1
    if (30, 30) not in sizes:
        failures.append({"code": "missing_30x30"})
    if len(bboxes) < 8:
        failures.append({"code": "insufficient_frame_bbox_diversity", "count": len(bboxes)})
    if len(colors) < 4:
        failures.append({"code": "insufficient_color_diversity", "count": len(colors)})
    if len(block_missing) < 2 or len(frame_missing) < 2:
        failures.append({
            "code": "insufficient_missing_quadrant_diversity",
            "block": sorted(block_missing),
            "frame": sorted(frame_missing),
        })
    return {
        "seeds": list(seeds),
        "episodes": episodes,
        "pairs": pairs,
        "public_turns": public_turns,
        "matched_input_comparisons": matched,
        "grid_sizes": [list(item) for item in sorted(sizes)],
        "frame_bboxes": [list(item) for item in sorted(bboxes)],
        "color_sets": [list(item) for item in sorted(colors)],
        "block_midrange_missing_quadrants": sorted(block_missing),
        "frame_midpoint_missing_quadrants": sorted(frame_missing),
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
            for setting in adapter.DIVIDER_REFERENCES:
                settings = {"divider_reference": setting}
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
        "task_id": "3fb5ef8ad60e",
        "settings": [dict(item) for item in adapter.SETTINGS],
        "bounded_scope": "finite seeds and declared rivals only; not universal uniqueness or owner acceptance",
    }
    report["sweep"] = sweep(adapter, range(args.seeds))
    report["protected_racket"] = protected_racket(adapter)
    report["status"] = "passed" if not report["sweep"]["failures"] else "failed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["sweep"]["episodes"],
        "pairs": report["sweep"]["pairs"],
        "racket_evaluations": report["protected_racket"]["evaluations"],
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
