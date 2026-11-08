#!/usr/bin/env python3
"""Bounded protected-Racket verification for the proposed d336 family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "d336f5fb2da4"


def _load():
    spec = importlib.util.spec_from_file_location("_d336_verify_prototype", HERE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    started = time.monotonic()
    p = _load()
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"magenta_rotation": rotation}, "demos": demos, "queries": 4}
        for seed in (0, 17, 91)
        for demos in (2, 3, 6)
        for rotation in p.ROTATIONS
    ]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert native["racket"]["backend"] == "racket" and native["racket"]["protected"] is True
    episodes = [p.generate(**job) for job in jobs]
    paired_input_checks = 0
    first_turn_checks = 0
    for seed in (0, 17, 91):
        for demos in (2, 3, 6):
            cw = p.generate(seed, {"magenta_rotation": "cw"}, demos, 4)
            ccw = p.generate(seed, {"magenta_rotation": "ccw"}, demos, 4)
            assert [x["input"] for s in ("train", "test") for x in cw[s]] == [
                x["input"] for s in ("train", "test") for x in ccw[s]
            ]
            paired_input_checks += 1
    for episode in episodes:
        single = {"train": episode["train"], "test": [episode["test"][0]]}
        assert p.visible_turn(episode, 0) == public_challenge_bytes(single)
        first_turn_checks += 1
        changed = deepcopy(episode)
        changed["program_solution"] = "private"
        for pair in changed["test"]:
            pair["output"] = [[9]]
        assert public_challenge_bytes(changed) == public_challenge_bytes(episode)
        assert public_challenge_id(changed) == public_challenge_id(episode)
    canonical_default = p.program({"magenta_rotation": "cw"})
    canonical_hash = hashlib.sha256(canonical_default.encode()).hexdigest()
    source_paths = [HERE / x for x in ("adapter.py", "prototype.py", "verify.py", "promotion.json", "canonical.rkt", "counterclockwise.rkt")]
    source_paths += [HERE.parents[1] / "generator.py", HERE.parents[1] / "tests/test_generator.py", HERE.parents[1] / "tests/test_parametric.py"]
    report = {
        "schema": "d336f5fb2da4-protected-parametric-check-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "reference": "proposed_parametric",
        "training_admitted": False,
        "qualification_or_acceptance_performed": False,
        "jobs": jobs,
        "native_checks": native["checks"],
        "racket": native["racket"],
        "racket_evaluations": native["racket_evaluations"],
        "verified_pair_labels": sum(job["demos"] + job["queries"] for job in jobs),
        "paired_setting_input_checks": paired_input_checks,
        "first_turn_projection_checks": first_turn_checks,
        "canonical_labeled_pairs": len(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)),
        "canonical_program_sha256": canonical_hash,
        "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths},
        "thirty_by_thirty": {
            "input_shape": [30, 30],
            "query_index": 3,
            "cyan_cells": sum(v == 8 for row in episodes[0]["test"][3]["output"] for v in row),
        },
        "adversarial_scope": [
            "finite alternate handedness replayed from demonstrations only",
            "private program/query labels do not affect public bytes or ID",
            "same seed/count inputs match across settings",
            "strict scalar/count validation covered by pytest",
        ],
        "limits": [
            "Three fixed seeds and demo counts 2, 3, and 6; not a universal seed proof.",
            "Finite cw/ccw family only; arbitrary alternative programs are outside this certificate.",
            "Owner qualification and acceptance remain separate.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    out.mkdir(parents=True)
    (out / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    retained = [episodes[i] for i in range(0, len(episodes), 6)]
    for episode in retained:
        public_id = public_challenge_id(episode)
        (out / f"challenge-{public_id}.json").write_bytes(public_challenge_bytes(episode))
    print(json.dumps({k: report[k] for k in ("status", "verified_pair_labels", "racket_evaluations", "elapsed_seconds")}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    verify(args.out)


if __name__ == "__main__":
    main()
