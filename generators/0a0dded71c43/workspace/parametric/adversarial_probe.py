#!/usr/bin/env python3
"""Bounded adversarial self-review for the fill/bridge-selection family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_ID = "0a0dded71c43"
SETTINGS = ({"mode": "fill_only"}, {"mode": "select_most_bridges"})


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_0a_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expect_value_error(fn, label: str) -> str:
    try:
        fn()
    except ValueError as exc:
        return f"{label}: {exc}"
    raise AssertionError(f"{label} unexpectedly succeeded")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    proto = _load()
    started = time.monotonic()

    count_corners = ((2, 1), (2, 4), (6, 1), (6, 4))
    episodes_generated = 0
    matched_input_checks = 0
    stress_checks = []
    rival_checks = []
    for seed in range(4):
        for demos, queries in count_corners:
            episodes = [proto.generate(seed, setting, demos, queries) for setting in SETTINGS]
            left_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
            right_inputs = [pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]]
            assert left_inputs == right_inputs
            matched_input_checks += 1
            for setting, episode in zip(SETTINGS, episodes, strict=True):
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                assert episode["certificate"]["survivors"] == [setting]
                assert len({proto.digest(pair["input"]) for pair in episode["train"] + episode["test"]}) == demos + queries
                episodes_generated += 1
            composed = episodes[1]
            assert any(
                proto.largest_component_rival(pair["input"]) != pair["output"]
                for pair in composed["train"]
            )
            first_anchor = proto.analyze_input(composed["train"][0]["input"])["winner_bbox"]
            fixed_refuted = any(
                proto.fixed_location_rival(pair["input"], first_anchor) != pair["output"]
                for pair in composed["train"][1:]
            )
            if demos > 2:
                assert fixed_refuted
            skip_refuted = proto.skip_a_rival(composed["test"][0]["input"]) != composed["test"][0]["output"]
            assert skip_refuted
            rival_checks.append({
                "seed": seed,
                "demos": demos,
                "queries": queries,
                "largest_component_refuted": True,
                "fixed_location_refuted": fixed_refuted,
                "skip_stage_a_refuted": skip_refuted,
            })
            if queries == 4:
                analysis = proto.analyze_input(episodes[0]["test"][3]["input"])
                assert analysis["bbox_height"] >= 24 and analysis["bbox_width"] >= 20
                assert analysis["bridge_count"] >= 15
                assert analysis["largest_component_is_winner"] is False
                stress_checks.append(analysis)

    short = proto.generate(77, SETTINGS[0], 2, 1)
    long = proto.generate(77, SETTINGS[0], 6, 4)
    assert short["test"] == long["test"][:1]

    private_mutation = copy.deepcopy(short)
    private_mutation["settings"] = SETTINGS[1]
    private_mutation["program_solution"] = "private mutation"
    private_mutation["test"][0]["output"] = [[9]]
    private_mutation["certificate"] = {"forged": True}
    assert public_challenge_bytes(private_mutation) == public_challenge_bytes(short)
    assert public_challenge_id(private_mutation) == public_challenge_id(short)
    visible_mutation = copy.deepcopy(short)
    visible_mutation["train"][0]["output"] = [[9]]
    assert public_challenge_id(visible_mutation) != public_challenge_id(short)

    corrupt = copy.deepcopy(short)
    corrupt["train"][0]["output"][0][0] = (corrupt["train"][0]["output"][0][0] + 1) % 10
    duplicate = copy.deepcopy(short)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    rejections = [
        _expect_value_error(lambda: proto.generate(0, SETTINGS[0], True, 4), "boolean demos"),
        _expect_value_error(lambda: proto.generate(-1, SETTINGS[0], 3, 4), "negative seed"),
        _expect_value_error(lambda: proto.generate(0, {"mode": "unknown"}, 3, 4), "unknown mode"),
        _expect_value_error(lambda: proto.certify(corrupt), "corrupt label"),
        _expect_value_error(lambda: proto.certify(duplicate), "duplicate input"),
    ]

    racket = []
    with RacketBridge(timeout=60) as bridge:
        for setting in SETTINGS:
            episode = proto.generate(37, setting, 3, 4)
            certificate = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            racket.append({"settings": setting, "survivors": certificate["survivors"]})
        runtime = bridge.runtime_identity

    result = {
        "schema": "arcpuzzles-parametric-adversarial-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "attempted_surfaces": [
            "all demo/query count corners across four seeds and both matched-input settings",
            "largest-component, fixed-location, and skip-stage-A semantic rivals",
            "query-prefix independence plus public/private tampering",
            "corrupt labels, duplicate inputs, invalid counts/settings, and protected-Racket certificates",
            "four 30x30 stress queries with broad occupied span and nontrivial bridge counts",
        ],
        "episodes_generated": episodes_generated,
        "matched_input_checks": matched_input_checks,
        "rival_checks": rival_checks,
        "stress_checks": stress_checks,
        "rejections": rejections,
        "racket": racket,
        "runtime": runtime,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("prototype.py", "adapter.py", "promotion.json", "rules/fill_only.rkt", "rules/select_most_bridges.rkt")
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": result["task_id"],
        "status": result["status"],
        "episodes_generated": result["episodes_generated"],
        "matched_input_checks": result["matched_input_checks"],
        "stress_checks": len(result["stress_checks"]),
        "elapsed_seconds": result["elapsed_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
