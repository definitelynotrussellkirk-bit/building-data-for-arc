#!/usr/bin/env python3
"""Bounded adversarial checks for the reconciled parametric export path."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
PARAMETRIC = REPO / "generators" / "0f7d80015d9d" / "workspace" / "parametric"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import public_challenge_bytes  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    prototype = load_module("_adversarial_parametric_prototype", PARAMETRIC / "prototype.py")
    retainer = load_module("_adversarial_parametric_retainer", PARAMETRIC / "retain.py")
    checked = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    retained_manifest = json.loads(
        (PARAMETRIC / "evidence" / "manifest.json").read_text(encoding="utf-8")
    )

    episodes = [
        prototype.build_episode(
            20261023 + index,
            setting=setting,
            n_train=3,
            n_test=4,
        )
        for index, setting in enumerate(prototype.SETTINGS)
    ]
    planned = prototype.plan_public_batch(reversed(episodes))
    planned_ids = [row["public_id"] for row in planned]
    if planned_ids != sorted(planned_ids):
        raise AssertionError("reversed settings leaked into public write order")

    hidden_duplicate = deepcopy(episodes[0])
    hidden_duplicate["seed"] = 999999
    hidden_duplicate["program"] = "private replacement"
    hidden_duplicate["test"][0]["output"] = [[9]]
    try:
        prototype.plan_public_batch([episodes[0], hidden_duplicate])
    except ValueError as exc:
        duplicate_plan_error = str(exc)
    else:
        raise AssertionError("duplicate visible payload was accepted by batch planner")

    retained_ids = []
    for path in sorted((PARAMETRIC / "examples").glob("*.json")):
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != path.stem:
            raise AssertionError(f"retained public file does not hash to ID: {path.name}")
        if raw != public_challenge_bytes(json.loads(raw)):
            raise AssertionError(f"retained public file is not canonical bytes: {path.name}")
        retained_ids.append(path.stem)
    if retained_ids != sorted(retained_ids) or len(retained_ids) != 4:
        raise AssertionError("retained public inventory is incomplete or unsorted")

    reversed_checked = deepcopy(checked)
    reversed_checked["episodes"] = list(reversed(reversed_checked["episodes"]))
    with tempfile.TemporaryDirectory(prefix="parametric-adversarial-") as temp:
        temp_root = Path(temp)
        examples = temp_root / "examples"
        racket = temp_root / "racket"
        retained = retainer.retain_verified_batch(
            checks_dir=HERE,
            checked=reversed_checked,
            examples_dir=examples,
            racket_dir=racket,
        )
        temp_ids = [row["public_id"] for row in retained]
        if temp_ids != sorted(temp_ids):
            raise AssertionError("retention leaked private manifest order")
        for path in sorted(examples.glob("*.json")):
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != path.stem:
                raise AssertionError(f"temporary retained file hash mismatch: {path.name}")

        duplicate_checked = deepcopy(checked)
        duplicate_checked["episodes"].append(deepcopy(duplicate_checked["episodes"][0]))
        duplicate_examples = temp_root / "duplicate-examples"
        duplicate_racket = temp_root / "duplicate-racket"
        try:
            retainer.retain_verified_batch(
                checks_dir=HERE,
                checked=duplicate_checked,
                examples_dir=duplicate_examples,
                racket_dir=duplicate_racket,
            )
        except ValueError as exc:
            duplicate_retention_error = str(exc)
        else:
            raise AssertionError("duplicate verifier row was accepted by retention")
        if duplicate_examples.exists() or duplicate_racket.exists():
            raise AssertionError("retention mutated destinations before duplicate rejection")

    result = {
        "schema": "0f7d80015d9d-parametric-export-adversarial-v1",
        "status": "passed",
        "task_id": "0f7d80015d9d",
        "generator_sha256": checked["generator_sha256"],
        "canonical_rule_hash": retained_manifest["canonical_rule_hash"],
        "source_sha256": {
            "prototype.py": sha256(PARAMETRIC / "prototype.py"),
            "retain.py": sha256(PARAMETRIC / "retain.py"),
            "checks_manifest": sha256(HERE / "manifest.json"),
            "retained_manifest": sha256(PARAMETRIC / "evidence" / "manifest.json"),
        },
        "surfaces": {
            "reversed_order_and_duplicate_visible_payload": {
                "planned_public_ids": planned_ids,
                "sorted": True,
                "duplicate_rejected": True,
                "error": duplicate_plan_error,
            },
            "raw_identity_and_retention_preflight": {
                "retained_public_ids": retained_ids,
                "raw_sha_matches_id": True,
                "canonical_bytes": True,
                "reverse_manifest_sorted": True,
                "duplicate_manifest_rejected": True,
                "destinations_absent_after_rejection": True,
                "error": duplicate_retention_error,
            },
        },
        "limitations": [
            "This bounded pass exercises two export/retention failure surfaces, not the full generator domain.",
            "Production generator and canonical Racket authority are read-only inputs to this check.",
        ],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
