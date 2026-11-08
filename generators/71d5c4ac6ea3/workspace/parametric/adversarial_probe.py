#!/usr/bin/env python3
"""Bounded adversarial self-review for the anchor/offset rotation family."""
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
TASK_ID = "71d5c4ac6ea3"
SETTINGS = ({"offset_mode": "as_drawn"}, {"offset_mode": "rotate_cw"})


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_71d_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _anchor(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(points) != 1:
        raise AssertionError(f"expected one anchor, found {len(points)}")
    return points[0]


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
                assert len({_anchor(pair["input"]) for pair in episode["train"]}) >= 2
                episodes_generated += 1

            rotated = episodes[1]
            fixed_origin = _anchor(rotated["train"][0]["input"])
            fixed_refuted = any(
                proto.fixed_origin_rival(pair["input"], fixed_origin, SETTINGS[1]) != pair["output"]
                for pair in rotated["train"][1:]
            )
            absolute_refuted = any(
                proto.absolute_position_rival(pair["input"]) != pair["output"]
                for pair in rotated["train"]
            )
            reflection_refuted = any(
                proto.reflect_offsets_rival(pair["input"]) != pair["output"]
                for pair in rotated["train"]
            )
            assert fixed_refuted and absolute_refuted and reflection_refuted
            rival_checks.append({
                "seed": seed,
                "demos": demos,
                "queries": queries,
                "fixed_origin_refuted": fixed_refuted,
                "absolute_position_refuted": absolute_refuted,
                "reflection_refuted": reflection_refuted,
            })

            if queries == 4:
                analysis = proto.analyze_input(episodes[0]["test"][3]["input"])
                assert analysis["offset_count"] >= 7
                assert analysis["seed_count"] >= 5
                assert analysis["content_bbox_height"] >= 24
                assert analysis["content_bbox_width"] >= 24
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
        _expect_value_error(lambda: proto.generate(0, {"offset_mode": "unknown"}, 3, 4), "unknown mode"),
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
            "fixed-origin, absolute-position, and reflection semantic rivals",
            "anchor movement in every 2..6-demo lesson",
            "query-prefix independence plus public/private tampering",
            "corrupt labels, duplicate inputs, invalid counts/settings, and protected-Racket certificates",
            "eight 30x30 stress episodes with broad occupied span and at least seven offsets/five seeds",
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
            for name in (
                "prototype.py",
                "adapter.py",
                "promotion.json",
                "rules/as_drawn.rkt",
                "rules/rotate_cw.rkt",
            )
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
