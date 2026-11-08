"""Bounded protected-Racket audit and reviewer-only example export.

Run via review.py from the packet root. No acceptance or training is granted.
The native qualifier remains the owner handoff; this audits the extra rivals,
count endpoints, phase/position spread, and the existing public projection.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "891a82451a8a"
spec = importlib.util.spec_from_file_location("_ring_audit_prototype", HERE / "prototype.py")
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output):
    from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
    from reviewer_support import public_challenge_bytes, public_challenge_id

    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("choose a new audit output directory")
    output.mkdir(parents=True)
    start = time.monotonic()
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"mode": mode}, "demos": demos, "queries": 4}
            for seed in (0, 17) for mode in prototype.MODES for demos in (2, 6)]
    # Every chosen and rival setting runs through the same-checkout protected
    # runtime, including all 32 query labels at the two demo-count endpoints.
    execution = evaluate_contract(ROOT, TASK, contract, jobs)
    _write(output / "execution.private.json", execution)
    episodes = execution["episodes"]

    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    rival_cases = []
    extra_checks = []
    repair_replays = []
    additional_evaluations = 0
    try:
        for mode in prototype.MODES:
            episode = next(e for e in episodes if e["seed"] == 0 and e["settings"] == {"mode": mode} and len(e["train"]) == 2)
            report = prototype.teaching_report(episode["train"], episode["settings"])
            assert report["all_refuted"]
            for rival, refutations in report["refutations"].items():
                pair_index = refutations[0]
                pair = episode["train"][pair_index]
                rival_program = prototype.rival_program(episode["settings"], rival)
                prediction = apply(rival_program, pair["input"])
                expected = prototype.solve(pair["input"], episode["settings"], rival)
                if prediction != expected or prediction == pair["output"]:
                    raise AssertionError(f"Racket rival disagreement or no refutation: {mode}/{rival}")
                rival_cases.append({"settings": episode["settings"], "rival": rival,
                                    "demo_index": pair_index, "input": pair["input"],
                                    "intended_program": episode["program"], "output": pair["output"],
                                    "rival_program": rival_program, "rival_output": prediction})
        # Check all fixed priority orders and corner omissions on a bounded
        # lesson. Survivors are fitted only to demonstrations, never to answers.
        episode = next(e for e in episodes if e["seed"] == 0 and e["settings"]["mode"] == "corner_relay" and len(e["train"]) == 2)
        for name in prototype.QUERY_RIVALS["corner_relay"]:
            text = prototype.rival_program(episode["settings"], name)
            predictions = [apply(text, p["input"]) for p in episode["train"]]
            additional_evaluations += len(predictions)
            assert predictions == [prototype.solve(p["input"], episode["settings"], name) for p in episode["train"]]
            survives = all(x == p["output"] for x, p in zip(predictions, episode["train"]))
            if survives:
                answers = [apply(text, p["input"]) for p in episode["test"]]
                additional_evaluations += len(answers)
                assert answers == [p["output"] for p in episode["test"]]
            extra_checks.append({"rival": name, "program": text, "fits_demos": survives,
                                 "queries_replayed": 4 if survives else 0,
                                 "query_answers_used_for_fitting": False})
        # Replay both original teaching holes, then verify their repaired
        # same-seed lessons. Keep the counterexamples as small private evidence.
        for filename in ("underidentified-before.private.json", "tie-underidentified-before.private.json"):
            case = json.loads((HERE / "evidence/current" / filename).read_text())
            text = prototype.rival_program(case["settings"], case["rival"])
            old_predictions = []
            for p in case["train"] + case["test"]:
                assert apply(case["program"], p["input"]) == p["output"]
                old_predictions.append(apply(text, p["input"]))
                additional_evaluations += 2
            assert old_predictions[:-1] == [p["output"] for p in case["train"]]
            assert old_predictions[-1] != case["test"][0]["output"]
            repaired = prototype.generate(case["seed"], case["settings"], len(case["train"]), 4)
            for p in repaired["train"] + repaired["test"]:
                assert apply(repaired["program_solution"], p["input"]) == p["output"]
                additional_evaluations += 1
            repaired_fit = all(prototype.solve(p["input"], case["settings"], case["rival"]) == p["output"] for p in repaired["train"])
            if repaired_fit:
                for p in repaired["test"]:
                    assert apply(text, p["input"]) == p["output"]
                    additional_evaluations += 1
            repair_replays.append({"original_case": filename, "rival_program": text,
                "old_demos_fit": True, "old_query_disagrees": True,
                "old_rival_query_output": old_predictions[-1],
                "repaired_rival_fits_demos": repaired_fit, "repaired_queries_safe": True,
                "repaired_episode": repaired})
    finally:
        bridge.close()
    _write(output / "rival-witnesses.private.json", {"racket": identity, "cases": rival_cases,
        "scope": "One protected executed refutation per declared rival; not universal uniqueness."})
    _write(output / "extra-rivals.private.json", {"racket": identity, "checks": extra_checks})
    _write(output / "teaching-repairs.private.json", {"racket": identity, "cases": repair_replays})

    # A small, deterministic sampler probe is explicitly separate from Racket
    # verification. These extra labels are not exported as checked training data.
    sample_results = []
    phases, backgrounds, relays = set(), set(), set()
    candidate_counts = []
    failures = []
    for seed in range(12):
        for mode in prototype.MODES:
            for demos in (2, 3, 6):
                try:
                    e = prototype.generate(seed, {"mode": mode}, demos, 4)
                    assert e["teaching"]["all_refuted"]
                    assert e["query_safety"]["all_queries_safe"]
                    assert len({json.dumps(p["input"]) for p in e["train"] + e["test"]}) == demos + 4
                    for p in e["train"] + e["test"]:
                        info = prototype.analyze(p["input"])
                        phases.add(info[4]); backgrounds.add(info[5])
                        relays.add(prototype.intermediate(p["input"])["selected_corner_index"])
                    candidate_counts.append(e["teaching_candidates"])
                    sample_results.append({"seed": seed, "mode": mode, "demos": demos, "queries": 4})
                except Exception as exc:
                    failures.append({"seed": seed, "mode": mode, "demos": demos, "error": str(exc)})
    if failures:
        _write(output / "sampler-failures.json", failures)
        raise AssertionError("bounded sampler probe failed; retain failures and repair")

    # Opaque names depend only on actual public bytes. A four-query container is
    # controller data; first_turn files expose exactly one query, no total count.
    example_map = []
    for episode in episodes:
        challenge = {"train": episode["train"], "test": episode["test"]}
        public_bytes = public_challenge_bytes(challenge)
        public_id = public_challenge_id(challenge)
        (output / "public").mkdir(exist_ok=True)
        (output / "public" / f"{public_id}.json").write_bytes(public_bytes)
        first = prototype.turn_challenge(episode, 0)
        first_bytes = public_challenge_bytes(first)
        first_id = public_challenge_id(first)
        (output / "first_turn").mkdir(exist_ok=True)
        (output / "first_turn" / f"{first_id}.json").write_bytes(first_bytes)
        single = copy.deepcopy(episode)
        single["test"] = single["test"][:1]
        assert public_challenge_bytes(prototype.turn_challenge(single, 0)) == first_bytes
        mutated = copy.deepcopy(episode)
        mutated.update(seed=-100, settings={"mode": "private-change"}, program="private-change")
        mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
        assert public_challenge_bytes(mutated) == public_bytes
        mutated["test"][-1]["input"][0][0] = (mutated["test"][-1]["input"][0][0] + 1) % 10
        assert public_challenge_bytes(prototype.turn_challenge(mutated, 0)) == first_bytes
        bad = copy.deepcopy(first)
        bad["test"][0]["input"][0][0] = False
        try:
            public_challenge_bytes(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("public projection accepted a Boolean cell")
        example_map.append({"seed": episode["seed"], "settings": episode["settings"],
                            "demos": len(episode["train"]), "queries": len(episode["test"]),
                            "public_id": public_id, "first_turn_id": first_id})
    _write(output / "example-map.private.json", example_map)

    summary = {"schema": "891a82451a8a-parametric-audit-v1", "status": "passed",
        "racket": execution["racket"], "native_execution_jobs": len(jobs),
        "native_racket_evaluations": execution["racket_evaluations"],
        "verified_pair_labels": sum(len(e["train"]) + len(e["test"]) for e in episodes),
        "protected_rival_refutations": len(rival_cases),
        "extra_rivals_checked_in_racket": len(extra_checks),
        "teaching_holes_reproduced_and_repaired": len(repair_replays),
        "additional_racket_evaluations": additional_evaluations,
        "all_teaching_uses_demonstrations_only": True,
        "sampler": {"attempted_episodes": len(sample_results) + len(failures),
                    "successful_episodes": len(sample_results), "failures": failures,
                    "seeds": list(range(12)), "demo_counts": [2, 3, 6], "query_count": 4,
                    "max_candidate_inputs_for_two_demos": max(candidate_counts),
                    "seed_phases_seen": sorted(phases), "backgrounds_seen": sorted(backgrounds),
                    "relay_corners_seen": sorted(relays), "label_basis": "Python diagnostics only"},
        "checked_query_shapes": [[5, 5], [14, 23], [23, 18], [30, 30]],
        "first_turn_equals_single_query": True, "private_metadata_does_not_change_public_names": True,
        "future_inputs_do_not_change_first_turn": True, "boolean_public_cell_rejected": True,
        "source_sha256": {p.name: _hash(p) for p in (HERE / "prototype.py", HERE / "adapter.py",
                            HERE / "canonical.rkt", HERE / "promotion.json", Path(__file__).resolve())},
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "limits": ["Finite declared-rival evidence only; no learning-benefit claim.",
                   "Reviewer evidence only; native owner acceptance and training admission remain separate.",
                   "Input has one seed by the canonical grammar; large outputs use every cell and cycle wrap."],
        "training_admitted": False}
    _write(output / "audit.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    run(parser.parse_args().out)
