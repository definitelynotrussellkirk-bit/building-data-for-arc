#!/usr/bin/env python3
"""Protected-Racket verification and reusable lesson audit for 3143493b7c83."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from arcpuzzles.parametric_worker import evaluate_contract
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "3143493b7c83"


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_verify_3143493b7c83", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _execute(bridge, program, grid):
    callable_rule = wrap_rule(program)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalize_grid(grid)
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({callable_rule} {literal})"))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(out, witness_out=None, stress_seeds=64):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    if witness_out is not None:
        witness_out = Path(witness_out)
        if witness_out.exists():
            raise FileExistsError(witness_out)
    started = time.monotonic()
    p = _load()
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"match_mode": mode}, "demos": demos, "queries": 4}
        for seed in (0, 17, 91)
        for demos in (2, 3, 6)
        for mode in p.MATCH_MODES
    ]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert native["racket"]["backend"] == "racket"
    assert native["racket"]["protected"] is True

    episodes = [p.generate(**job) for job in jobs]
    paired_input_checks = 0
    public_invariance_checks = 0
    first_turn_checks = 0
    finite_rival_checks = 0
    for seed in (0, 17, 91):
        for demos in (2, 3, 6):
            left = p.generate(seed, {"match_mode": "contains"}, demos, 4)
            right = p.generate(seed, {"match_mode": "exact_bbox"}, demos, 4)
            left_inputs = [pair["input"] for split in ("train", "test") for pair in left[split]]
            right_inputs = [pair["input"] for split in ("train", "test") for pair in right[split]]
            assert left_inputs == right_inputs
            paired_input_checks += 1
    for episode in episodes:
        certificate = p.teaching_certificate(episode)
        assert len(certificate["setting_survivors"]) == 1
        assert certificate["plausible_rival_survivors"] == []
        finite_rival_checks += len(p.PLAUSIBLE_RIVALS)
        first = {"train": episode["train"], "test": [episode["test"][0]]}
        assert p.visible_turn(episode, 0) == public_challenge_bytes(first)
        first_turn_checks += 1
        changed = deepcopy(episode)
        changed["program_solution"] = "private replacement"
        for pair in changed["test"]:
            pair["output"] = [[9]]
        assert public_challenge_bytes(changed) == public_challenge_bytes(episode)
        assert public_challenge_id(changed) == public_challenge_id(episode)
        public_invariance_checks += 1

    # Python-only bounded sampler/reviewer tool: min/max counts, both settings,
    # stable public prefixes, finite rival rejection, and 30x30 reachability.
    stress_episodes = 0
    stress_pairs = 0
    stress_30 = 0
    for seed in range(stress_seeds):
        for demos in (2, 6):
            contains = p.generate(seed, {"match_mode": "contains"}, demos, 4)
            exact = p.generate(seed, {"match_mode": "exact_bbox"}, demos, 4)
            one = p.generate(seed, {"match_mode": "contains"}, demos, 1)
            assert contains["train"] == one["train"]
            assert contains["test"][:1] == one["test"]
            assert [x["input"] for split in ("train", "test") for x in contains[split]] == [
                x["input"] for split in ("train", "test") for x in exact[split]
            ]
            assert p.teaching_certificate(contains)["plausible_rival_survivors"] == []
            assert p.teaching_certificate(exact)["plausible_rival_survivors"] == []
            assert (len(contains["test"][-1]["input"]),
                    len(contains["test"][-1]["input"][0])) == (30, 30)
            stress_episodes += 2
            stress_pairs += 2 * (demos + 4)
            stress_30 += 2

    witness = p.dependency_witness()
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity.get("backend") == "racket" and identity.get("protected") is True
        correct = _execute(bridge, witness["correct_program"], witness["input"])
        wrong = _execute(bridge, witness["wrong_intermediate_program"], witness["input"])
        skipped = _execute(bridge, witness["skip_a_program"], witness["input"])
    assert correct == witness["correct_output"]
    assert wrong == witness["wrong_intermediate_output"]
    assert skipped == witness["skip_a_output"]
    assert correct != wrong and correct != skipped
    witness_report = {
        **witness,
        "status": "passed",
        "reference": "protected_racket",
        "training_admitted": False,
        "program_sha256": {
            "correct": hashlib.sha256(witness["correct_program"].encode()).hexdigest(),
            "wrong_intermediate": hashlib.sha256(witness["wrong_intermediate_program"].encode()).hexdigest(),
            "skip_a": hashlib.sha256(witness["skip_a_program"].encode()).hexdigest(),
        },
        "racket": {k: identity[k] for k in (
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
            "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"
        ) if k in identity},
        "racket_evaluations": 3,
    }

    source_paths = [
        HERE / "adapter.py",
        HERE / "canonical.rkt",
        HERE / "promotion.json",
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE.parents[1] / "generator.py",
        HERE.parents[1] / "tests/test_parametric.py",
    ]
    stress_pair = episodes[0]["test"][-1]
    changed_cells = [(r, c) for r, row in enumerate(stress_pair["output"])
                     for c, value in enumerate(row) if value != stress_pair["input"][r][c]]
    report = {
        "schema": "3143493b7c83-protected-parametric-check-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "reference": "proposed_parametric",
        "training_admitted": False,
        "qualification_or_acceptance_performed": False,
        "jobs": jobs,
        "native_checks": native["checks"],
        "racket": native["racket"],
        "racket_evaluations": native["racket_evaluations"] + 3,
        "verified_pair_labels": sum(job["demos"] + job["queries"] for job in jobs),
        "paired_setting_input_checks": paired_input_checks,
        "public_private_invariance_checks": public_invariance_checks,
        "first_turn_projection_checks": first_turn_checks,
        "finite_plausible_rival_checks": finite_rival_checks,
        "sampler_stress": {
            "seeds": stress_seeds,
            "settings": list(p.MATCH_MODES),
            "demo_counts": [2, 6],
            "episodes": stress_episodes,
            "pairs": stress_pairs,
            "thirty_by_thirty_pairs": stress_30,
        },
        "canonical_pairs_checked_by_focused_test": len(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)),
        "thirty_by_thirty": {
            "shape": [30, 30],
            "changed_cells": len(changed_cells),
            "row_span": max(r for r, _ in changed_cells) - min(r for r, _ in changed_cells) + 1,
            "column_span": max(c for _, c in changed_cells) - min(c for _, c in changed_cells) + 1,
        },
        "dependency_witness": {
            "status": "passed",
            "racket_evaluations": 3,
            "correct_output_differs_from_wrong_intermediate": correct != wrong,
            "correct_output_differs_from_skip_a": correct != skipped,
        },
        "source_sha256": {path.relative_to(ROOT).as_posix(): _sha(path) for path in source_paths},
        "adversarial_scope": [
            "demonstration-only isolation of the two declared settings",
            "five executable plausible wrong rules fitted only to demonstrations",
            "same-seed matched inputs and query-prefix stability",
            "private programs/settings/query answers excluded from public bytes and IDs",
            "wrong-intermediate and skipped-A causal programs executed in protected Racket",
        ],
        "limits": [
            "Native Racket scope is 18 jobs across seeds 0/17/91 and demo counts 2/3/6, not a universal seed proof.",
            "The ambiguity result covers only the five declared plausible rivals.",
            "Reviewer evidence and native qualification do not constitute owner acceptance or training admission.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    out.mkdir(parents=True)
    (out / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (out / "dependency-witness.json").write_text(json.dumps(witness_report, indent=2, sort_keys=True) + "\n")
    public = out / "public"
    public.mkdir()
    for mode in p.MATCH_MODES:
        episode = p.generate(17, {"match_mode": mode}, 3, 4)
        public_id = public_challenge_id(episode)
        (public / f"challenge-{public_id}.json").write_bytes(public_challenge_bytes(episode))
    if witness_out is not None:
        witness_out.parent.mkdir(parents=True, exist_ok=True)
        witness_out.write_bytes((out / "dependency-witness.json").read_bytes())
    print(json.dumps({
        "status": report["status"],
        "verified_pair_labels": report["verified_pair_labels"],
        "racket_evaluations": report["racket_evaluations"],
        "sampler_stress_episodes": stress_episodes,
        "elapsed_seconds": report["elapsed_seconds"],
    }, sort_keys=True))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-out", type=Path)
    parser.add_argument("--stress-seeds", type=int, default=64)
    args = parser.parse_args()
    verify(args.out, args.witness_out, args.stress_seeds)


if __name__ == "__main__":
    main()
