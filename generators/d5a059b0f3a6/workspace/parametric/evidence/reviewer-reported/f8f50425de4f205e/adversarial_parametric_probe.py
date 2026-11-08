#!/usr/bin/env python3
"""Bounded adversarial checks for d5a059b0f3a6 public export and verifier rejection."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_assertion(label: str, action) -> dict[str, str]:
    try:
        action()
    except AssertionError as exc:
        return {"case": label, "status": "rejected", "message": str(exc)}
    raise AssertionError(f"{label} was accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261023)
    args = parser.parse_args()

    repo_root = Path.cwd()
    parametric = (
        repo_root
        / "generators"
        / "d5a059b0f3a6"
        / "workspace"
        / "parametric"
    )
    prototype = load_module("d5_parametric_adversarial_prototype", parametric / "prototype.py")
    verifier = load_module("d5_parametric_adversarial_verify", parametric / "verify.py")

    episodes = {
        setting: prototype.build_episode(
            args.seed,
            setting=setting,
            n_train=prototype.DEFAULT_N_TRAIN,
            n_test=prototype.DEFAULT_N_TEST,
        )
        for setting in prototype.ALLOWED_SETTINGS
    }
    normal_plan = verifier._public_materialization_plan(
        prototype=prototype,
        episodes=episodes,
    )
    reversed_plan = verifier._public_materialization_plan(
        prototype=prototype,
        episodes=dict(reversed(tuple(episodes.items()))),
    )
    normal_names = [row[0] for row in normal_plan]
    reversed_names = [row[0] for row in reversed_plan]
    assert normal_names == sorted(normal_names)
    assert reversed_names == normal_names

    public_rows: list[dict[str, Any]] = []
    for public_name, setting, challenge in normal_plan:
        verifier._assert_public_redacted(challenge, prototype)
        canonical_bytes = json.dumps(
            challenge,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        expected_name = f"challenge-{hashlib.sha256(canonical_bytes).hexdigest()[:16]}.json"
        assert public_name == expected_name == prototype.public_identifier(challenge)
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == prototype.DEFAULT_N_TRAIN
        assert len(challenge["test"]) == prototype.DEFAULT_N_TEST
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        public_rows.append(
            {
                "filename": public_name,
                "private_setting_for_evidence_only": setting,
                "visible_content_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
                "demonstrations": len(challenge["train"]),
                "queries": len(challenge["test"]),
                "query_outputs_present": False,
                "hidden_metadata_present": False,
            }
        )

    first_challenge = deepcopy(normal_plan[0][2])
    leaked_output = deepcopy(first_challenge)
    leaked_output["test"][0]["output"] = [[0]]
    leaked_seed = deepcopy(first_challenge)
    leaked_seed["seed"] = args.seed

    rejection_rows = [
        expect_assertion(
            "query_output_leak",
            lambda: verifier._assert_public_redacted(leaked_output, prototype),
        ),
        expect_assertion(
            "hidden_seed_metadata",
            lambda: verifier._assert_public_redacted(leaked_seed, prototype),
        ),
    ]

    collision_proxy = SimpleNamespace(
        PARAMETER_NAME=prototype.PARAMETER_NAME,
        ALLOWED_SETTINGS=prototype.ALLOWED_SETTINGS,
        public_challenge=prototype.public_challenge,
        public_identifier=lambda _challenge: "challenge-collision.json",
    )
    rejection_rows.append(
        expect_assertion(
            "visible_identifier_collision",
            lambda: verifier._public_materialization_plan(
                prototype=collision_proxy,
                episodes=episodes,
            ),
        )
    )

    result = {
        "schema": "d5a059b0f3a6-bounded-adversarial-probe-v1",
        "status": "passed",
        "task_id": prototype.TASK_ID,
        "seed": args.seed,
        "budget_scope": "two surfaces: public/private export and verifier rejection paths",
        "public_export": {
            "normal_private_enumeration_public_names": normal_names,
            "reversed_private_enumeration_public_names": reversed_names,
            "order_invariant": True,
            "order_policy": "lexicographic visible-derived filename",
            "rows": public_rows,
        },
        "verifier_rejections": rejection_rows,
        "limits": [
            "one deterministic seed and the two currently proposed settings",
            "does not establish catalog approval or exhaust all side channels",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
