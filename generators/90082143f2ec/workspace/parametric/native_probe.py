"""Bounded protected-Racket self-audit and actor-safe example exporter.

Run through review.py run from the issued packet; --out must be a fresh path.
This is task-local reusable evidence tooling, not an owner acceptance command.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Choose a fresh evidence directory")
    path = Path(__file__).with_name("adapter.py")
    spec = importlib.util.spec_from_file_location("axis_native_probe_adapter", path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    rows, examples, matched, label_count = [], [], {}, 0
    with RacketBridge(timeout=10.0, startup_timeout=30.0) as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        for seed in (0, 17):
            for demos in (2, 6):
                for policy in ("more_coherent", "less_coherent"):
                    settings = {"axis_policy": policy}
                    episode = adapter.generate(seed, settings, demos=demos, queries=4)
                    pairs = episode["train"] + episode["test"]
                    inputs = [p["input"] for p in pairs]
                    signatures = [json.dumps(g, separators=(",", ":")) for g in inputs]
                    assert len(set(signatures)) == len(signatures)
                    key = (seed, demos)
                    if key in matched:
                        assert inputs == matched[key]
                    else:
                        matched[key] = inputs
                    source = adapter.program(settings)
                    callable_rule = wrap_rule(source)
                    for pair in pairs:
                        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                        actual = bridge.eval_text(f"({callable_rule} {literal})")
                        assert actual == pair["output"], (seed, demos, policy)
                        label_count += 1
                    teaching = adapter.teaching_report(episode["train"], settings)
                    assert teaching["all_refuted"]
                    single = adapter.generate(seed, settings, demos=demos, queries=1)
                    assert adapter.visible_turn(episode, 0) == adapter.visible_turn(single, 0)
                    public_before = public_challenge_bytes(episode)
                    changed_private = deepcopy(episode)
                    changed_private.update(seed=-1, settings={"private": "changed"}, program_solution="private")
                    for pair in changed_private["test"]:
                        pair["output"] = [[0]]
                    assert public_challenge_bytes(changed_private) == public_before
                    largest = episode["test"][-1]["input"]
                    restored = adapter.solve(largest, {"axis_policy": "more_coherent"})
                    noise = sum(v != restored[r][c] for r, row in enumerate(largest) for c, v in enumerate(row))
                    assert len(largest) == len(largest[0]) == 30
                    assert noise == 162
                    assert all(largest[r][c] != restored[r][c] for r, c in ((0, 0), (0, 29), (29, 0), (29, 29)))
                    rows.append({"seed": seed, "demos": demos, "queries": 4, "settings": settings,
                                 "labels_checked": len(pairs), "teaching": teaching,
                                 "large_query": {"shape": [30, 30], "noise_cells": noise,
                                                 "all_four_corners_noisy": True}})
                    if seed == 0 and demos == 2:
                        examples.append(episode)
    args.out.mkdir(parents=True)
    exported = adapter.write_batch(examples, args.out / "examples")
    report = {"schema": "90082143f2ec-native-axis-self-audit-v1", "status": "passed",
              "episodes_attempted": len(rows), "episodes_passed": len(rows), "episodes_failed": 0,
              "protected_racket_labels": label_count, "runtime_identity": identity,
              "matched_input_settings": True, "first_turn_prefix_invariance": True,
              "private_field_public_byte_invariance": True, "examples": exported, "episodes": rows,
              "adapter_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "scope": "Two seeds, two demonstration counts, both settings, four queries; finite rivals only. No owner acceptance or training admission."}
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "episodes_attempted", "episodes_passed", "episodes_failed", "protected_racket_labels")}))


if __name__ == "__main__":
    main()
