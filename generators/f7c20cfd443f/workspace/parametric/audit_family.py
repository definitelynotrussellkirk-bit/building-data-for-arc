"""Reproducible bounded sampler, protected-Racket rival audit, and private/public examples.

Run through review.py run. This is authoring evidence, not native acceptance.
Outputs must be new. No training controller or training admission is provided.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
_spec = importlib.util.spec_from_file_location("_f7_audit_adapter", HERE / "adapter.py")
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)
MODES = ("all", "largest", "smallest")


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write_examples(episodes, destination):
    """Serialize one-query projections. Callers must verify private labels first."""
    from reviewer_support import public_challenge_bytes, public_challenge_id
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Choose a new output: {destination}")
    public, private = {}, []
    for episode in episodes:
        ids = []
        for index in range(len(episode["test"])):
            challenge = adapter.public_turn(episode, index)
            payload, identifier = public_challenge_bytes(challenge), public_challenge_id(challenge)
            if identifier in public:
                raise ValueError("duplicate visible challenge")
            public[identifier] = payload
            ids.append(identifier)
        private.append({"episode": deepcopy(episode), "public_ids": ids})
    (destination / "public").mkdir(parents=True, exist_ok=False)
    for identifier, payload in sorted(public.items()):
        (destination / "public" / f"{identifier}.json").write_bytes(payload)
    result = {"schema": "f7-halo-authoring-examples-v1", "private_episodes": private,
              "training_admitted": False, "owner_acceptance": "pending",
              "consumer": "Reveal exactly one hash-named public file per turn; keep this manifest private."}
    (destination / "private.json").write_bytes(raw(result))
    return result


def summarize(grid):
    groups = adapter.components(adapter.dilate(grid))
    return {"height": len(grid), "width": len(grid[0]),
            "gray_seeds": sum(v == 5 for row in grid for v in row),
            "halo_component_areas": sorted(map(len, groups))}


def audit(destination):
    from arcpuzzles.parametric_worker import _real_evaluator
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Choose a new evidence directory: {destination}")
    source = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted([*HERE.glob("*.py"), *HERE.glob("*.rkt")])}
    source[(HERE / "promotion.json").relative_to(ROOT).as_posix()] = hashlib.sha256((HERE / "promotion.json").read_bytes()).hexdigest()
    sampling, failures = [], []
    for seed in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17):
        for demos in (2, 3, 6):
            same_inputs = None
            for mode in MODES:
                try:
                    episode = adapter.generate(seed, {"selection": mode}, demos, 4)
                    inputs = [p["input"] for split in ("train", "test") for p in episode[split]]
                    if same_inputs is not None and inputs != same_inputs:
                        raise AssertionError("setting-dependent input sampling")
                    same_inputs = inputs
                    teaching = adapter.teaching_check(episode)
                    if teaching["surviving_rivals"] or teaching["query_ambiguities"]:
                        raise AssertionError(f"underidentified lesson: {teaching}")
                    single = adapter.generate(seed, {"selection": mode}, demos, 1)
                    if adapter.public_turn(single, 0) != adapter.public_turn(episode, 0):
                        raise AssertionError("query-count-dependent first turn")
                    first = summarize(episode["test"][0]["input"])
                    if len(set(first["halo_component_areas"])) < 2:
                        raise AssertionError("first query does not require selection")
                    stress = summarize(episode["test"][-1]["input"])
                    if (stress["gray_seeds"] < 30 or len(stress["halo_component_areas"]) < 2
                            or len(set(stress["halo_component_areas"])) < 2):
                        raise AssertionError(f"unsubstantive stress scene: {stress}")
                    sampling.append({"seed": seed, "demos": demos, "selection": mode,
                                     "query_profiles": [summarize(p["input"]) for p in episode["test"]]})
                except Exception as error:
                    failures.append({"seed": seed, "demos": demos, "selection": mode,
                                     "error": f"{type(error).__name__}: {error}"})
    if failures:
        raise AssertionError(json.dumps({"sampler_failures": failures}))

    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations, executed, rivals, examples, boundaries = 0, [], [], [], []
    def run(program, grid):
        nonlocal evaluations
        evaluations += 1
        return apply(program, grid)
    try:
        for seed, demos in ((0, 6), (17, 2)):
            for mode in MODES:
                episode = adapter.generate(seed, {"selection": mode}, demos, 4)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = run(episode["program_solution"], pair["input"])
                        if actual != pair["output"]:
                            raise AssertionError((mode, seed, split, index, "Racket label mismatch"))
                executed.append({"seed": seed, "selection": mode, "demos": demos, "queries": 4,
                                 "labels": demos + 4})
                for name in adapter.rival_names(mode):
                    program = adapter.rival_program(mode, name)
                    outputs = [run(program, p["input"]) for p in episode["train"][:2]]
                    if outputs != [adapter.rival_output(p["input"], mode, name) for p in episode["train"][:2]]:
                        raise AssertionError((mode, name, "Racket rival mismatch"))
                    rejecting = [i for i, answer in enumerate(outputs) if answer != episode["train"][i]["output"]]
                    if not rejecting:
                        raise AssertionError((mode, seed, name, "rival survives first two demonstrations"))
                    index = rejecting[0]
                    rivals.append({"selection": mode, "seed": seed, "rival": name,
                                   "program": program, "rejecting_demo_indices": rejecting,
                                   "case": {"input": episode["train"][index]["input"],
                                            "expected": episode["train"][index]["output"],
                                            "rival_output": outputs[index]}})
                if seed == 0:
                    example = deepcopy(episode)
                    example["train"] = example["train"][:3]
                    examples.append(example)
        for h, w, seeds in ((7, 7, ((0, 0), (0, 2), (3, 3), (6, 6))),
                            (30, 30, tuple((r, c) for r in range(0, 30, 3) for c in range(0, 30, 3)))):
            grid = [[0] * w for _ in range(h)]
            for r, c in seeds:
                grid[r][c] = 5
            adapter.validate_grid(grid)
            labels = {}
            for mode in MODES:
                expected = adapter.transform(grid, mode)
                labels[mode] = run(adapter.program({"selection": mode}), grid)
                if labels[mode] != expected:
                    raise AssertionError((h, w, mode, "boundary label mismatch"))
            boundaries.append({"input": grid, "outputs": labels, **summarize(grid)})
    finally:
        bridge.close()

    destination.mkdir(parents=True, exist_ok=False)
    write_examples(examples, destination / "examples")
    result = {"schema": "f7-halo-parametric-audit-v1", "status": "passed", "source_files": source,
              "command": " ".join(sys.argv), "racket": identity, "racket_evaluations": evaluations,
              "sampling": {"attempted": len(sampling), "succeeded": len(sampling), "failed": 0,
                           "records": sampling}, "executed_episodes": executed,
              "self_review": {"cases": rivals, "surviving_rivals": [],
                              "query_ambiguities": [], "fit_scope": "first two visible demonstrations only"},
              "boundaries": boundaries, "training_admitted": False, "owner_acceptance": "pending",
              "limits": "Finite declared rivals and sampled seeds only. Python census is distinct from listed protected-Racket jobs; no learning-gain claim."}
    (destination / "audit.json").write_bytes(raw(result))
    print(json.dumps({"status": "passed", "sampler_episodes": len(sampling),
                      "executed_episodes": len(executed), "rival_cases": len(rivals),
                      "racket_evaluations": evaluations, "report": str(destination / "audit.json")}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    audit(parser.parse_args().out)
