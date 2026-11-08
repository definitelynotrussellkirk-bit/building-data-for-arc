#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import load_selected_generator

TASK_ID = "5e8e4691afde"
EXPECTED_GENERATOR = "4ada1ccad8e5662a4cc0a80763d2c5400e22436b1f40a091b033fc4865b44e02"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
PROTOTYPE = REPO / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("peer_5e8e4691afde_parametric_probe", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main():
    _generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=REPO)
    if generator_sha != EXPECTED_GENERATOR:
        raise ValueError(f"peer source drift: {generator_sha}")
    prototype = load_prototype()
    selected = prototype.Setting(1, 2)
    with prototype.RacketLabeler(timeout=30.0, startup_timeout=60.0) as labeler:
        episode = prototype.make_episode(
            labeler,
            23,
            0,
            setting=selected,
            demos=2,
            queries=4,
            max_attempts=4096,
        )
        default_predictions = labeler.outputs(
            prototype.program_for(prototype.DEFAULT),
            [pair["input"] for pair in episode["test"]],
        )
        identity = {
            key: labeler.bridge.runtime_identity[key]
            for key in ("backend", "protected", "binary_sha256", "prelude_sha256")
        }
        evaluations = labeler.evaluated_pairs
    certificate = episode["identifiability"]
    default_elimination = next(
        row
        for row in certificate["eliminations"]
        if row["setting"] == prototype.DEFAULT.as_dict()
    )
    query_disagreements = [
        index
        for index, (pair, predicted) in enumerate(zip(episode["test"], default_predictions))
        if pair["output"] != predicted
    ]
    report = {
        "schema": "arcpuzzles-peer-bounded-no-finding-v1",
        "task_id": TASK_ID,
        "status": "no_finding",
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": generator_sha,
        "prototype_path": str(PROTOTYPE.relative_to(REPO)),
        "prototype_sha256": hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
        "racket": identity,
        "probe": {
            "seed": 23,
            "episode_index": 0,
            "selected_setting": selected.as_dict(),
            "demonstrations": 2,
            "queries": 4,
            "candidate_settings": certificate["candidate_count"],
            "survivors": certificate["survivors"],
            "canonical_default_mismatching_demonstrations": default_elimination["mismatching_demonstrations"],
            "canonical_default_query_disagreements": query_disagreements,
            "dimensions": episode["sampling"]["dimensions"],
            "racket_program_input_evaluations": evaluations,
        },
        "finding": None,
        "summary": "The selected quarter-turn/scale rule was the sole survivor among all eight declared settings using only two protected-Racket-labeled demonstrations. The canonical default was refuted by the visible demos and disagreed on all retained queries.",
        "limits": "One seed, one noncanonical setting, and the finite eight-setting family only; not universal learnability or a production approval.",
    }
    if certificate["survivors"] != [selected.as_dict()]:
        raise ValueError("selected setting was not uniquely identified")
    if not default_elimination["mismatching_demonstrations"]:
        raise ValueError("canonical default was not refuted by demonstrations")
    if query_disagreements != [0, 1, 2, 3]:
        raise ValueError(f"canonical default did not disagree on all four queries: {query_disagreements}")
    out = HERE / "no-finding.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "no_finding", "path": str(out.relative_to(WORK)), "survivors": certificate["survivors"], "default_query_disagreements": query_disagreements, "racket_evaluations": evaluations}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
