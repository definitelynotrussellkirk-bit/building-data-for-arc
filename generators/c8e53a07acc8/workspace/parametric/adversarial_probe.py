#!/usr/bin/env python3
"""Bounded adversarial review for the c8e53 anchor-size family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_c8e53_probe_prototype", HERE / "prototype.py")
assert SPEC and SPEC.loader
proto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proto)


def expect_reject(name, call):
    try:
        call()
    except (ValueError, RuntimeError) as exc:
        return {"name": name, "rejected": True, "error": f"{type(exc).__name__}: {exc}"}
    raise AssertionError(f"tamper survived: {name}")


def main() -> int:
    records = []
    racket_pairs = 0
    with proto.RacketRunner() as execute:
        for seed in (0, 17):
            for demos in (2, 6):
                episodes = [proto.generate(seed, setting, demos, 4) for setting in proto.SETTINGS]
                inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
                assert inputs == [pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]]
                assert len({proto.digest(grid) for grid in inputs}) == demos + 4
                assert len(inputs[-1]) == 30 and len(inputs[-1][0]) == 30
                assert all(
                    proto.transform(grid, proto.SETTINGS[0]) != proto.transform(grid, proto.SETTINGS[1])
                    for grid in inputs
                )
                for episode in episodes:
                    certificate = proto.certify(episode, execute)
                    racket_pairs += demos + 4
                    assert certificate["survivors"] == [episode["settings"]]
                    records.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": episode["settings"],
                        "pair_count": demos + 4,
                        "survivors": certificate["survivors"],
                        "racket_checked": certificate["racket_checked"],
                        "input_sha256": [proto.digest(grid) for grid in inputs],
                        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
                    })

    episode = proto.generate(91, proto.SETTINGS[1], 2, 4)
    visible = proto.public_turn(episode, 0)
    original_bytes = proto.public_challenge_bytes(visible)
    original_id = proto.public_id(episode, 0)
    mutated = copy.deepcopy(episode)
    mutated["seed"] = 999999
    mutated["settings"] = copy.deepcopy(proto.SETTINGS[0])
    mutated["program_solution"] = proto.program(proto.SETTINGS[0])
    mutated["test"][0]["output"] = mutated["test"][1]["output"]
    mutated["test"][1]["input"] = [[0]]
    assert proto.public_challenge_bytes(proto.public_turn(mutated, 0)) == original_bytes
    assert proto.public_id(mutated, 0) == original_id

    tamper = []
    bad = copy.deepcopy(episode)
    bad["train"][0]["output"] = bad["train"][0]["input"]
    tamper.append(expect_reject("wrong_demo_label", lambda: proto.certify(bad)))
    bad = copy.deepcopy(episode)
    bad["test"][0]["input"] = copy.deepcopy(bad["train"][0]["input"])
    tamper.append(expect_reject("duplicate_input", lambda: proto.certify(bad)))
    bad = copy.deepcopy(episode)
    bad["program_solution"] = proto.program(proto.SETTINGS[0])
    tamper.append(expect_reject("program_setting_mismatch", lambda: proto.certify(bad)))
    tamper.append(expect_reject(
        "bool_seed",
        lambda: proto.generate(True, proto.SETTINGS[0], 2, 4),
    ))

    report = {
        "schema": "c8e53-anchor-size-adversarial-v1",
        "status": "passed",
        "scope": {
            "seeds": [0, 17],
            "demo_counts": [2, 6],
            "settings": proto.SETTINGS,
            "queries_per_episode": 4,
        },
        "checks": {
            "same_inputs_across_settings": True,
            "every_pair_distinguishes_settings": True,
            "demo_only_unique_survivor": True,
            "all_inputs_distinct": True,
            "substantive_30x30_query": True,
            "public_projection_private_invariant": True,
            "tamper_rejections": tamper,
        },
        "racket": execute.identity,
        "racket_checked_pairs": racket_pairs,
        "records": records,
        "source_sha256": proto.source_hashes(),
        "limits": "Finite two-seed boundary-count review; not a universal proof.",
    }
    out = HERE / "evidence" / "adversarial.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "passed", "out": str(out), "racket_checked_pairs": racket_pairs}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
