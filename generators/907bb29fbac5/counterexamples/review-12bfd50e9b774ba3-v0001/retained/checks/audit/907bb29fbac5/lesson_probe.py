#!/usr/bin/env python3
"""Test a concrete lesson-level rival without importing reference runner internals."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from probe import gallery, load_generator

HERE = Path(__file__).resolve().parent
LESSON = HERE / "lesson"


def write(name, value):
    (LESSON / name).write_text(json.dumps(value, indent=2) + "\n")


def search():
    LESSON.mkdir(exist_ok=True)
    gen = load_generator()
    census = []
    selected = None
    for seed in range(32):
        grids = [gen.generate(seed, i, difficulty="hard") for i in range(4)]
        profiles = [gen.observe_overrides(g)["overlap_profile"] for g in grids]
        errors = [gen.self_check(g) for g in grids]
        matches = [gallery(g, "global_core_erasure") == gallery(g, "xor") for g in grids]
        assert not any(errors)
        item = {"seed": seed, "sample_indices": [0, 1, 2, 3], "difficulty": "hard",
                "profiles": profiles, "self_check_errors": errors,
                "rival_matches_independent_xor": matches}
        census.append(item)
        if matches == [True, True, True, False] and selected is None:
            selected = {**item, "inputs": grids}
    write("search.json", {"seed_range_inclusive": [0, 31], "sample_indices": [0, 1, 2, 3],
                          "difficulty": "hard", "grid_count": 128,
                          "rival_definition": "blank diagonal; off-diagonal tile (a,b) = (A union B) minus (A intersect B intersect C)",
                          "census": census, "selected": selected})
    assert selected is not None, "No ambiguous episode candidate in bounded range"
    write("input.json", selected["inputs"])
    write("rival.json", [gallery(g, "global_core_erasure") for g in selected["inputs"]])
    write("independent_xor.json", [gallery(g, "xor") for g in selected["inputs"]])
    write("domain_validation.json", [
        {"sample_index": i, "split": "train" if i < 3 else "test",
         "self_check_errors": gen.self_check(g), "observed_axes": gen.observe_overrides(g),
         "semantic_observables": gen.semantic_observables(g)}
        for i, g in enumerate(selected["inputs"])])
    print(json.dumps({"selected_seed": selected["seed"], "profiles": selected["profiles"],
                      "rival_matches": selected["rival_matches_independent_xor"],
                      "searched_seed_range_inclusive": [0, 31], "searched_grid_count": 128}, indent=2))


def compare():
    selected = json.loads((LESSON / "search.json").read_text())["selected"]
    episode, = [json.loads(line) for line in (LESSON / "episode.jsonl").read_text().splitlines()]
    record = json.loads((LESSON / "racket.json").read_text())
    rival = json.loads((LESSON / "rival.json").read_text())
    expected = json.loads((LESSON / "independent_xor.json").read_text())
    pairs = episode["train"] + episode["test"]
    assert len(pairs) == 4 and len(record["results"]) == 4
    production_matches_candidates = [p["input"] for p in pairs] == selected["inputs"]
    executed = [r["output"] for r in record["results"]]
    matches = [r == e for r, e in zip(rival, executed)]
    differences = [{"row": r, "col": c, "racket": executed[3][r][c], "rival": rival[3][r][c]}
                   for r in range(14) for c in range(14) if executed[3][r][c] != rival[3][r][c]]
    summary = {
        "classification": "Reproduced lesson-level shortcut; no incorrect reference labels",
        "seed": selected["seed"], "difficulty": "hard", "sample_indices": episode["sample_indices"],
        "train_count": len(episode["train"]), "test_count": len(episode["test"]),
        "production_matches_candidates": production_matches_candidates,
        "production_rejections": episode["rejections"],
        "profiles": selected["profiles"], "rival_matches_public_racket": matches,
        "query_mismatched_cells": differences,
        "public_generation_outputs_match_public_apply": [p["output"] for p in pairs] == executed,
        "independent_xor_matches_public_apply": expected == executed,
        "reference_errors": [r["error"] for r in record["results"]],
        "executed_rule_hash": record["executed_rule_hash"],
        "rule_hash_matches_catalog": record["rule_hash_matches_catalog"],
        "approved": episode.get("approved"),
    }
    write("comparison.json", summary)
    print(json.dumps(summary, indent=2))
    assert production_matches_candidates
    assert not summary["production_rejections"]
    assert matches == [True, True, True, False]
    assert len(differences) == 6
    assert summary["public_generation_outputs_match_public_apply"]
    assert summary["independent_xor_matches_public_apply"]
    assert not any(summary["reference_errors"])
    assert summary["rule_hash_matches_catalog"]


if __name__ == "__main__":
    {"search": search, "compare": compare}[sys.argv[1]]()
