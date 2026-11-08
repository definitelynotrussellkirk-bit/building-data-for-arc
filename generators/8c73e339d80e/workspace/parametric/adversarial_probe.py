#!/usr/bin/env python3
"""Bounded adversarial self-review for the handedness prototype."""
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
TASK_ID = "8c73e339d80e"


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_probe_8c73", path)
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
    invalid = [
        _expect_value_error(lambda: proto.generate(0, settings[0], True, 4), "boolean demos"),
        _expect_value_error(lambda: proto.generate(-1, settings[0], 3, 4), "negative seed"),
        rejection,
    ]

    racket = []
    with RacketBridge() as bridge:
        for setting in settings:
            episode = proto.generate(37, setting, 3, 4)
            certificate = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            racket.append({"settings": setting, "survivors": certificate["survivors"]})
        runtime = bridge.runtime_identity

    stress = proto.generate(17, settings[0], 3, 4)["test"][-1]["input"]
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    result = {
        "schema": "arcpuzzles-parametric-adversarial-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "attempted_surfaces": [
            "all four demo/query count corners across four seeds and both settings",
            "query-prefix independence and public/private tampering",
            "corrupt labels, boolean counts, negative seeds, and fresh Racket certificates",
        ],
        "episodes_generated": successes,
        "matched_input_checks": matched_checks,
        "rejections": invalid,
        "racket": racket,
        "stress": {
            "shape": [len(stress), len(stress[0])],
            "row_span": max(r for r, _ in occupied) - min(r for r, _ in occupied),
            "col_span": max(c for _, c in occupied) - min(c for _, c in occupied),
            "colors": sorted({value for row in stress for value in row}),
            "has_distractors_5_7": {5, 7} <= {value for row in stress for value in row},
        },
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
