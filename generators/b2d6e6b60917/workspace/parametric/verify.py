#!/usr/bin/env python3
"""Bounded protected-Racket verification for the proposed b2 family."""
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
TASK_ID = "b2d6e6b60917"


def _load():
    spec = importlib.util.spec_from_file_location("_b2_verify_prototype", HERE / "prototype.py")
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
        {"seed": seed, "settings": {"template": template}, "demos": demos, "queries": 4}
        for seed in (0, 17, 91)
        for demos in (2, 3, 6)
        for template in p.TEMPLATES
    ]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert native["racket"]["backend"] == "racket" and native["racket"]["protected"] is True
    episodes = [p.generate(**job) for job in jobs]
    paired_inputs = public_invariance = first_turn = 0
    for seed in (0, 17, 91):
        for demos in (2, 3, 6):
            full = p.generate(seed, {"template": "full"}, demos, 4)
            fragment = p.generate(seed, {"template": "fragment"}, demos, 4)
            assert [x["input"] for split in ("train", "test") for x in full[split]] == [
                x["input"] for split in ("train", "test") for x in fragment[split]
            ]
            paired_inputs += 1
    for episode in episodes:
        single = {"train": episode["train"], "test": [episode["test"][0]]}
        assert p.visible_turn(episode, 0) == public_challenge_bytes(single)
        first_turn += 1
        changed = deepcopy(episode)
        changed["program_solution"] = "private replacement"
        for pair in changed["test"]:
            pair["output"] = [[9]]
        assert public_challenge_bytes(changed) == public_challenge_bytes(episode)
        assert public_challenge_id(changed) == public_challenge_id(episode)
        public_invariance += 1
    source_paths = [HERE / x for x in ("adapter.py", "prototype.py", "verify.py", "promotion.json", "canonical.rkt", "fragment.rkt")]
    source_paths += [HERE.parents[1] / "generator.py", HERE.parents[1] / "tests/test_parametric.py"]
    big = episodes[0]["test"][3]
    occupied = [(r, c) for r, row in enumerate(big["output"]) for c, v in enumerate(row) if v]
    report = {
        "schema": "b2d6e6b60917-protected-parametric-check-v1",
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
        "paired_setting_input_checks": paired_inputs,
        "public_private_invariance_checks": public_invariance,
        "first_turn_projection_checks": first_turn,
        "canonical_pairs_replayed_by_focused_test": len(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)),
        "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths},
        "thirty_by_thirty": {
            "shape": [30, 30],
            "occupied_output_cells": len(occupied),
            "row_span": max(r for r, _ in occupied) - min(r for r, _ in occupied) + 1,
            "column_span": max(c for _, c in occupied) - min(c for _, c in occupied) + 1,
        },
        "adversarial_scope": [
            "finite full/fragment family identified from demonstrations only",
            "same-seed inputs compared across settings",
            "private program and query labels excluded from public bytes/identity",
            "30x30 ray geometry replayed by protected Racket",
        ],
        "limits": [
            "Three fixed seeds and demo counts 2, 3, and 6; not a universal seed proof.",
            "Finite declared family only; bbox-fill and other rivals remain canonical-generator evidence.",
            "Owner qualification and acceptance remain separate.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    out.mkdir(parents=True)
    (out / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for episode in episodes[::6]:
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
