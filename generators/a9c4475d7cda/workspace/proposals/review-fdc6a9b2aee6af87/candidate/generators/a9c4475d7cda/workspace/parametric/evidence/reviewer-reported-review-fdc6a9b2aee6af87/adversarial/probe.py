#!/usr/bin/env python3
"""Bounded adversarial probe for the a9c4475d7cda threshold prototype.

The probe attacks two surfaces: (1) episode-fixed parameter/Racket parity at
seed boundaries, and (2) public/private export plus exact JSON-scalar guards.
It writes a compact replayable JSON report and exits nonzero on any mismatch.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

TASK = "a9c4475d7cda"
ROOT = Path(__file__).resolve().parents[3] / "repo"
PARAMETRIC = ROOT / "generators" / TASK / "workspace" / "parametric"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_value_error(call, label: str, rejected: list[str]) -> None:
    try:
        call()
    except ValueError:
        rejected.append(label)
        return
    raise AssertionError(f"expected ValueError for {label}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    proto = load(PARAMETRIC / "prototype.py", "a9_threshold_probe_proto")
    adapter = load(PARAMETRIC / "adapter.py", "a9_threshold_probe_adapter")

    parity_rows = []
    input_independence = []
    with proto.RacketEngine() as engine:
        for seed in (0, 2**63 - 1):
            episodes = {
                threshold: proto.generate_episode(
                    seed, threshold=threshold, demos=1, queries=4
                )
                for threshold in proto.THRESHOLDS
            }
            serialized_inputs = {
                threshold: [
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["train"] + episode["test"]
                ]
                for threshold, episode in episodes.items()
            }
            reference = serialized_inputs[proto.THRESHOLDS[0]]
            assert all(serialized_inputs[t] == reference for t in proto.THRESHOLDS)
            outputs = {
                threshold: [pair["output"] for pair in episode["train"] + episode["test"]]
                for threshold, episode in episodes.items()
            }
            assert len({json.dumps(value, sort_keys=True) for value in outputs.values()}) == 3
            input_independence.append({
                "seed": seed,
                "pair_count": len(reference),
                "shared_input_sha256": hashlib.sha256("".join(reference).encode()).hexdigest(),
                "distinct_output_sequences": 3,
            })
            for threshold, episode in episodes.items():
                check = proto.verify_episode_racket(episode, engine=engine)
                assert check["demo_survivors"] == [threshold]
                assert check["label_count"] == 5
                parity_rows.append({
                    "seed": seed,
                    "threshold": threshold,
                    "survivors": check["demo_survivors"],
                    "query_checks": len(check["query_checks"]),
                })
        runtime = engine.runtime_identity
        racket_execution_count = len(engine.executions)

    baseline = proto.generate_episode(17, threshold=2, demos=3, queries=4)
    original_id = proto.public_id(baseline)
    private_mutation = copy.deepcopy(baseline)
    private_mutation["threshold"] = 3
    private_mutation["seed"] = 999
    private_mutation["program_solution"] = "private-canary"
    private_mutation["accepted_inputs"] = [{"private": True}]
    for pair in private_mutation["test"]:
        pair["output"] = [[9]]
    assert proto.public_id(private_mutation) == original_id

    visible_mutation = copy.deepcopy(baseline)
    visible_mutation["test"][0]["input"][0][0] = (
        visible_mutation["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_id(visible_mutation) != original_id

    rejected = []
    bad_episode_args = [
        ("seed-bool", {"seed": True}),
        ("seed-float", {"seed": 1.0}),
        ("threshold-bool", {"threshold": True}),
        ("threshold-float", {"threshold": 2.0}),
        ("demos-bool", {"demos": True}),
        ("queries-float", {"queries": 4.0}),
        ("max-attempts-bool", {"max_attempts": False}),
    ]
    defaults = {"seed": 17, "threshold": 2, "demos": 1, "queries": 1}
    for label, override in bad_episode_args:
        values = {**defaults, **override}
        expect_value_error(lambda values=values: proto.generate_episode(**values), label, rejected)
    for label, settings in [
        ("adapter-threshold-bool", {"threshold": True}),
        ("adapter-threshold-float", {"threshold": 2.0}),
        ("adapter-extra-key", {"threshold": 2, "extra": 0}),
    ]:
        expect_value_error(lambda settings=settings: adapter.program(settings), label, rejected)

    with tempfile.TemporaryDirectory(prefix="a9-threshold-adversarial-") as temp:
        duplicate_out = Path(temp) / "duplicate"
        try:
            proto.write_episodes(duplicate_out, [baseline, copy.deepcopy(baseline)])
        except ValueError as error:
            assert "duplicate visible" in str(error)
        else:
            raise AssertionError("duplicate public payload was accepted")
        assert not duplicate_out.exists()

        tampered = copy.deepcopy(baseline)
        tampered["test"][0]["output"] = [[9]]
        tampered_out = Path(temp) / "tampered"
        try:
            proto.write_episodes(tampered_out, [tampered])
        except ValueError as error:
            assert "label" in str(error)
        else:
            raise AssertionError("tampered label was accepted")
        assert not tampered_out.exists()

    authority = ROOT / "shared/data/base/solutions/training/6773b310__a9c4475d7cda.json"
    canonical_json = json.loads(authority.read_text(encoding="utf-8"))
    target_code = canonical_json["racket_target"]["target_code"]
    assert proto.rule_text(2) == target_code

    report = {
        "schema": "a9c4475d7cda-threshold-adversarial-v1",
        "status": "pass",
        "surfaces": [
            "parameter-fixed input independence and protected-Racket parity",
            "public/private export isolation and exact scalar rejection",
        ],
        "parity": parity_rows,
        "input_independence": input_independence,
        "racket_execution_count": racket_execution_count,
        "racket_runtime": {
            key: runtime[key]
            for key in ("schema", "backend", "protected", "binary_sha256", "bridge_sha256", "prelude_sha256")
        },
        "public_identifier": {
            "baseline": original_id,
            "private_mutation_stable": True,
            "visible_mutation_changes": True,
            "duplicate_rejected_before_output": True,
            "tampered_label_rejected_before_output": True,
        },
        "typed_rejections": rejected,
        "canonical_threshold_2_sha256": hashlib.sha256(proto.rule_text(2).encode()).hexdigest(),
        "limits": [
            "Finite seeds 0 and 2**63-1; thresholds 1, 2, 3.",
            "One demonstration and four queries per setting.",
            "No claim beyond the declared generator grammar and finite rivals.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "parity_cases": len(parity_rows),
        "racket_execution_count": racket_execution_count,
        "typed_rejections": len(rejected),
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
