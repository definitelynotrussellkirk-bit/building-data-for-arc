"""Bounded protected-Racket self-review and portable example exporter.

Run through review.py run, from the issued packet. This is reviewer evidence;
native qualification/owner acceptance remain separate, unchanged gates.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]


def local_module(filename):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location("_owned_audit_" + filename, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def run(output):
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes

    if output.exists():
        raise ValueError("use a new evidence directory after changing source")
    output.mkdir(parents=True)
    prototype = local_module("prototype.py")
    rivals = local_module("rivals.py")
    programs = {mode: prototype.program({"mode": mode}) for mode in prototype.MODES}
    programs.update({name: text for name, text in rivals.programs().items() if name != "all_fill"})
    runtime = ROOT / "shared/runtime"
    apply, identity, bridge = _real_evaluator(runtime)
    cache, calls = {}, []

    def execute(name, grid):
        key = (name, json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            result = apply(programs[name], grid)
            if not isinstance(result, list):
                raise ValueError(f"{name}: Racket did not return a grid")
            claimed = prototype.candidate_outputs(grid)[name]
            if result != claimed:
                raise ValueError(f"Python/Racket mismatch for {name}")
            cache[key] = result
            calls.append({"program": name,
                          "input_sha256": hashlib.sha256(key[1].encode()).hexdigest(),
                          "output_sha256": hashlib.sha256(json.dumps(result, separators=(",", ":")).encode()).hexdigest()})
        return deepcopy(cache[key])

    episodes, certificates, public_files = [], [], []
    bounded, failures = {"attempted": 0, "succeeded": 0, "failed": 0}, []
    weak_witness = None
    try:
        for seed in (0, 17):
            for mode in prototype.MODES:
                bounded["attempted"] += 1
                episode = prototype.generate(seed, {"mode": mode}, 3, 4)
                # All displayed labels are executed, including full-canvas 30x30.
                for pair in episode["train"] + episode["test"]:
                    pair["output"] = execute(mode, pair["input"])
                # Minimum two-demo context, before consulting any query labels.
                demo_predictions = [{name: execute(name, pair["input"]) for name in programs}
                                    for pair in episode["train"][:2]]
                survivors = [name for name in programs if all(
                    predictions[name] == pair["output"]
                    for predictions, pair in zip(demo_predictions, episode["train"][:2]))]
                if survivors != [mode]:
                    raise ValueError(f"Racket teaching survivors for {mode}: {survivors}")
                certificate = {"seed": seed, "settings": {"mode": mode}, "demonstrations_used": 2,
                    "survivors": survivors,
                    "rejected_by_demonstration": {name: [i for i, pair in enumerate(episode["train"][:2])
                        if demo_predictions[i][name] != pair["output"]] for name in programs if name != mode},
                    "scope": "Declared finite Racket hypotheses only; no universal uniqueness claim"}
                certificates.append(certificate)
                episode["seed"] = seed
                episode["settings"] = {"mode": mode}
                episode["demonstration_only_teaching"] = certificate
                episodes.append(episode)
                for folder, challenge in (
                    ("public_grouped", prototype.public_challenge(episode, all_queries=True)),
                    ("public_first", prototype.public_challenge(episode)),
                ):
                    raw = public_challenge_bytes(challenge)
                    name = hashlib.sha256(raw).hexdigest() + ".json"
                    destination = output / folder / name
                    destination.parent.mkdir(exist_ok=True)
                    # A duplicate visible payload must never overwrite an
                    # earlier row, even when private metadata differs.
                    with destination.open("xb") as stream:
                        stream.write(raw)
                    public_files.append(str(destination.relative_to(output)))
                # No settings/programs/answers or future inputs influence turn one.
                contaminated = deepcopy(episode)
                contaminated.update(seed=-999, settings={"private": 1}, program_solution="changed private reference")
                for pair in contaminated["test"]:
                    pair["output"] = [[9]]
                contaminated["test"][1]["input"] = [[8]]
                assert public_challenge_bytes(prototype.public_challenge(contaminated)) == public_challenge_bytes(prototype.public_challenge(episode))
                single = prototype.generate(seed, {"mode": mode}, 3, 1)
                assert public_challenge_bytes(prototype.public_challenge(single)) == public_challenge_bytes(prototype.public_challenge(episode))
                if mode == "largest_owned" and seed == 0:
                    # Retain a real ambiguity and the constructive repair:
                    # deleting the tie example permits tie_first to fit all demos.
                    deep, tie = episode["train"][1], episode["train"][0]
                    assert execute("tie_first_only", deep["input"]) == deep["output"]
                    assert execute("tie_first_only", tie["input"]) != tie["output"]
                    weak_witness = {"weak_demonstrations": [deep], "query": tie,
                        "intended_program": programs[mode], "rival_program": programs["tie_first_only"],
                        "rival_query_output": execute("tie_first_only", tie["input"]),
                        "repair": "Prepend the tie-largest example; the original lesson is retained as ambiguity evidence."}
                bounded["succeeded"] += 1
        # Cheap API boundary evidence with honest failure counts, separate from
        # the small set of Racket-qualified examples above.
        api = {"attempted": 0, "succeeded": 0, "failed": 0, "settings": list(prototype.MODES),
               "demos": [2, 3, 6], "queries": [1, 4], "seeds": [0, 17, 29]}
        for seed in api["seeds"]:
            for demos in api["demos"]:
                for queries in api["queries"]:
                    for mode in prototype.MODES:
                        api["attempted"] += 1
                        try:
                            prototype.generate(seed, {"mode": mode}, demos, queries)
                            api["succeeded"] += 1
                        except ValueError as error:
                            api["failed"] += 1
                            failures.append({"seed": seed, "mode": mode, "demos": demos,
                                             "queries": queries, "error": str(error)})
        if failures:
            raise ValueError(f"bounded API failures: {failures}")
    finally:
        bridge.close()

    write_json(output / "private.json", {"episodes": episodes, "programs": programs,
        "racket": identity, "executions": calls, "minimal_ambiguity_and_repair": weak_witness})
    sources = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted(HOME.iterdir()) if path.suffix in (".py", ".rkt", ".json")}
    report = {"schema": "nested-frame-parametric-self-review-v1", "status": "passed",
        "command": sys.argv, "source_sha256": sources, "racket": identity,
        "bounded_episodes": bounded, "bounded_api_requests": api,
        "racket_evaluations": len(calls), "distinct_programs": len(programs),
        "teaching_certificates": certificates, "public_files": sorted(public_files),
        "private_file": "private.json", "failures": failures,
        "checks": {"executed_all_example_labels": True, "minimum_two_demo_teaching": True,
                   "matched_inputs_across_settings": all(
                       [p["input"] for p in episodes[i][split]] == [p["input"] for p in episodes[i + 1][split]]
                       for i in (0, 2) for split in ("train", "test")),
                   "first_turn_matches_single_query": True, "private_metadata_invariance": True},
        "limits": ["Finite rivals and seeds only", "Python API sweep is separate from Racket execution",
                   "Largest enclosed zero-component selection is equivalent on this strict grammar",
                   "Source inventory and reviewer evidence do not grant owner acceptance or training admission"]}
    write_json(output / "report.json", report)
    print(json.dumps({k: report[k] for k in ("status", "bounded_episodes", "bounded_api_requests", "racket_evaluations", "distinct_programs")}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.out)
