"""Rebuild bounded authoring evidence with the packet's real Racket backend.

Run through review.py run. This does not approve source or admit training data.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[3]
    output = Path(args.out).resolve()
    if output.exists():
        raise FileExistsError("Use a fresh evidence output directory")
    spec = importlib.util.spec_from_file_location("_a0444de97675_evidence_adapter", here / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    proto = adapter.prototype
    sys.path[:0] = [str(root / "src"), str(root / "shared/runtime")]
    from arcpuzzles.parametric_worker import evaluate_contract
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import public_challenge_bytes, public_challenge_id, canonical_pairs

    contract = json.loads((here / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"scale": scale}, "demos": demos, "queries": 4}
            for seed, demos in ((91, 2), (2026, 6)) for scale in proto.SCALES]
    execution = evaluate_contract(root, "a0444de97675", contract, jobs)
    execution["owner_acceptance"] = "pending"
    execution["training_admitted"] = False
    observations, ambiguities, attempts = [], [], []
    for seed in (0, 1, 17, 91):
        for demos in range(2, 7):
            baseline_inputs = None
            for scale in proto.SCALES:
                episode = adapter.generate(seed, {"scale": scale}, demos, 4)
                inputs = [[pair["input"] for pair in episode[split]] for split in ("train", "test")]
                if baseline_inputs is None:
                    baseline_inputs = inputs
                assert inputs == baseline_inputs
                assert len({json.dumps(grid) for split in inputs for grid in split}) == demos + 4
                review = proto.teaching_check(episode["train"], episode["test"], scale)
                ambiguities.extend(review["ambiguities"])
                assert review["survivors"] == [f"scale_{scale}"]
                single = adapter.generate(seed, {"scale": scale}, demos, 1)
                first = {"train": episode["train"], "test": episode["test"][:1]}
                assert public_challenge_bytes(single) == public_challenge_bytes(first)
                mutation = copy.deepcopy(first)
                mutation.update(seed=999, settings={"scale": 999}, program="private")
                mutation["test"][0]["output"] = [[9]]
                assert public_challenge_id(first) == public_challenge_id(mutation)
                attempts.append(episode["private_sampling"]["demonstration_attempts"] - demos)
                observations.append({"seed": seed, "scale": scale, "demos": demos,
                                     "queries": 4, "survivors": review["survivors"]})
    assert not ambiguities

    bridge = RacketBridge()
    protected_calls = 0
    try:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        wrapped = {}
        def apply(program, grid):
            nonlocal protected_calls
            protected_calls += 1
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            return bridge.eval_text(f"({wrapped[program]} {literal})")

        canonical_count = 0
        for pair in canonical_pairs("a0444de97675", root=root, labeled_only=True):
            assert apply(adapter.program({"scale": 2}), pair["input"]) == pair["output"]
            canonical_count += 1

        stress = []
        for height, width in ((8, 9), (30, 30), (8, 30), (30, 9)):
            grid = proto.sample_scene(2026, 0, height=height, width=width)
            info = proto.inspect_scene(grid)
            labels = []
            for scale in proto.SCALES:
                actual = apply(adapter.program({"scale": scale}), grid)
                assert actual == proto.solve(grid, scale)
                assert 1 <= len(actual) <= 30 and 1 <= len(actual[0]) <= 30
                labels.append({"scale": scale, "output": actual})
            stress.append({"input": grid, "inspection": info, "labels": labels})

        # Two relevant wrong rules are total on these chosen witnesses and
        # receive actual executable predictions; runtime errors never refute them.
        teaching = []
        for episode in execution["episodes"]:
            scale = episode["settings"]["scale"]
            pair = episode["train"][0]
            chosen = adapter.program({"scale": scale})
            wrong_header = chosen.replace("(= v 1)", "(not (= v 0))")
            wrong_connectivity = chosen.replace("(objects work 0)",
                "(objects (grid-from-fn (rows work) (cols work) "
                "(lambda (r c) (if (= (at work r c) 0) 0 1))) 0)")
            predictions = []
            for name, rival_program in (("count_all_header_nonzero", wrong_header),
                                        ("color_agnostic_components", wrong_connectivity)):
                actual = apply(rival_program, pair["input"])
                assert actual == proto.rival_output(pair["input"], scale, name)
                assert actual != pair["output"]
                predictions.append({"name": name, "program": rival_program, "output": actual})
            teaching.append({"seed": episode["seed"], "settings": episode["settings"],
                             "input": pair["input"], "program": chosen, "output": pair["output"],
                             "wrong_rules": predictions,
                             "demo_only_review": proto.teaching_check(episode["train"], episode["test"], scale)})
    finally:
        bridge.close()

    # All file identities under public/ depend exclusively on one-turn visible
    # bytes. The controller owns examples.private.json and its future queries.
    output.mkdir(parents=True)
    public = output / "public"
    public.mkdir()
    public_ids = []
    for episode in execution["episodes"]:
        turn = {"train": episode["train"], "test": episode["test"][:1]}
        identifier = public_challenge_id(turn)
        (public / f"{identifier}.json").write_bytes(public_challenge_bytes(turn))
        public_ids.append(identifier)
    summary = {
        "schema": "a0444de97675-parametric-checks-v1", "status": "passed",
        "canonical_pairs_executed": canonical_count,
        "bounded_sampler": {"episodes": len(observations), "successes": len(observations),
                            "failures": 0, "max_extra_demonstration_attempts": max(attempts),
                            "demo_counts": [2, 3, 4, 5, 6], "query_count": 4},
        "native_evidence_jobs": len(jobs),
        "native_label_count": sum(item["label_count"] for item in execution["checks"]),
        "protected_racket_evaluations": execution["racket_evaluations"] + protected_calls,
        "declared_rivals": list(proto.RIVALS), "ambiguous_queries": 0,
        "all_inputs_matched_across_scales": True, "first_turn_prefix_stable": True,
        "public_ids_independent_of_private_fields": True,
        "stress": [item["inspection"] for item in stress],
        "racket": execution["racket"], "training_admitted": False,
        "owner_acceptance": "pending",
        "limits": ["Finite settings/seeds and declared rivals only; no universal uniqueness or training-gain claim.",
                   "Python sampler census is separate from the explicitly counted Racket-executed examples.",
                   "Native execution's reference field does not grant owner acceptance.",
                   "One-query files are first-turn samples; only the controller receives future queries."],
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (here / "adapter.py", here / "prototype.py", here / "canonical.rkt", here / "promotion.json", Path(__file__))},
    }
    for name, value in (("summary.json", summary), ("examples.private.json", execution),
                        ("teaching.private.json", teaching), ("stress.private.json", stress)):
        (output / name).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in ("status", "bounded_sampler", "native_label_count",
                                                   "protected_racket_evaluations", "ambiguous_queries")}, indent=2))


if __name__ == "__main__":
    main()
