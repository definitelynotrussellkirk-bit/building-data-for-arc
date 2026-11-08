#!/usr/bin/env python3
"""Bounded adversarial self-review for the exact-cover label-policy prototype."""
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
TASK_ID = "7bd583886bad"


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_7bd", path)
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
    settings = list(proto.SETTINGS)
    count_corners = ((2, 1), (2, 8), (6, 1), (6, 8))
    successes = 0
    matched_checks = 0
    stress_rows = []
    for seed in range(4):
        for demos, queries in count_corners:
            episodes = [proto.generate(seed, setting, demos, queries) for setting in settings]
            assert [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]] == [
                pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]
            ]
            matched_checks += 1
            for setting, episode in zip(settings, episodes, strict=True):
                assert len(episode["train"]) == demos and len(episode["test"]) == queries
                assert episode["certificate"]["survivors"] == [setting]
                assert len({proto.digest(pair["input"]) for pair in episode["train"] + episode["test"]}) == demos + queries
                successes += 1
            if queries >= 4:
                analysis = proto.analyze_mask(episodes[0]["test"][3]["input"])
                assert analysis["connected"] and analysis["cover_count"] == 1
                assert analysis["bbox_height"] >= 25 and analysis["bbox_width"] >= 25
                stress_rows.append(analysis)

    single = proto.generate(77, settings[0], 2, 1)
    many = proto.generate(77, settings[0], 6, 8)
    assert single["test"] == many["test"][:1]

    private_mutation = copy.deepcopy(single)
    private_mutation["settings"] = settings[1]
    private_mutation["program_solution"] = "private mutation"
    private_mutation["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(private_mutation) == public_challenge_bytes(single)
    assert public_challenge_id(private_mutation) == public_challenge_id(single)
    visible_mutation = copy.deepcopy(single)
    visible_mutation["train"][0]["output"] = [[9]]
    assert public_challenge_id(visible_mutation) != public_challenge_id(single)

    corrupt = copy.deepcopy(single)
    corrupt["train"][0]["output"] = [[0]]
    rejection = _expect_value_error(lambda: proto.certify(corrupt), "corrupt label")
    malformed_mask = copy.deepcopy(many["test"][3]["input"])
    for r, row in enumerate(malformed_mask):
        for c, value in enumerate(row):
            if value == 0:
                malformed_mask[r][c] = 7
                break
        else:
            continue
        break
    invalid = [
        _expect_value_error(lambda: proto.generate(0, settings[0], True, 4), "boolean demos"),
        _expect_value_error(lambda: proto.generate(-1, settings[0], 3, 4), "negative seed"),
        _expect_value_error(lambda: proto.transform(malformed_mask, settings[0]), "non-mask distractor"),
        rejection,
    ]

    racket = []
    with RacketBridge(timeout=60) as bridge:
        for setting in settings:
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
            "all four demo/query count corners across four seeds and both settings",
            "query-prefix independence and public/private tampering",
            "corrupt labels, boolean counts, malformed masks, and fresh Racket certificates",
        ],
        "episodes_generated": successes,
        "matched_input_checks": matched_checks,
        "stress_checks": stress_rows,
        "rejections": invalid,
        "racket": racket,
        "runtime": runtime,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("prototype.py", "adapter.py", "promotion.json")
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("task_id", "status", "episodes_generated", "matched_input_checks", "elapsed_seconds")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
