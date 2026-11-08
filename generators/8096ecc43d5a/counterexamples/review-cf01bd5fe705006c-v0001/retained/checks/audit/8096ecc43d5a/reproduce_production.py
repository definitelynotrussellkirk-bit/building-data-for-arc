#!/usr/bin/env python3
"""Reproduce the compact production witness with a one-code alternate rule."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, load_selected_generator

from probe_codebooks import INTENDED, TASK, crop, fitting_maps, named_map, prediction


def main():
    root = Path.cwd().resolve()
    evidence = Path(__file__).resolve().parent
    gen, source, generator_hash = load_selected_generator(TASK, root=root)
    episode, = Catalog(root).generate(
        TASK, count=1, seed=2, difficulty="easy", n_train=3, n_test=1,
        sample_index=0, overrides={}, reference="canonical", allow_unapproved=True,
        timeout=120,
    )
    (evidence / "production_episode.json").write_text(json.dumps(episode, indent=2) + "\n")
    assert episode["sample_indices"] == [0, 1, 2, 3]
    assert episode["rejections"] == []
    assert episode["provenance"]["generator_sha256"] == generator_hash
    assert episode["executed_rule_hash"] == gen.RULE_HASH == "04788c0240d6"
    pairs = []
    for index, pair in enumerate(episode["train"] + episode["test"]):
        assert pair["input"] == gen.generate(2, index, difficulty="easy")
        assert gen.self_check(pair["input"]) == []
        pairs.append({**pair, "sample_index": index, "codes": [v for v in pair["input"][0] if v],
                      "motif_crop": crop(pair["input"]), "profile": gen.schedule_profile(2, index, "easy")})
    # A single wrong association: code 3 means LR reflection rather than 180.
    rival = (1, 4, 4, 6)
    demos, query = pairs[:3], pairs[3]
    demo_outputs = [prediction(pair, rival) for pair in demos]
    assert demo_outputs == [pair["output"] for pair in demos]
    rival_query = prediction(query, rival)
    assert rival_query != query["output"]
    fitting = fitting_maps(demos)
    divergent = [mapping for mapping in fitting if prediction(query, mapping) != query["output"]]
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    for pair in canonical:
        pair["codes"] = [v for v in pair["input"][0] if v]
    result = {
        "status": "reproduced_production_teaching_ambiguity",
        "generator_sha256": generator_hash, "generator_version": gen.VERSION,
        "executed_rule_hash": episode["executed_rule_hash"],
        "rule_source_sha256": hashlib.sha256(episode["program"].encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "enumeration_probe_sha256": hashlib.sha256((evidence / "probe_codebooks.py").read_bytes()).hexdigest(),
        "recipe": {"seed": 2, "difficulty": "easy", "sample_index": 0, "n_train": 3,
                   "n_test": 1, "overrides": {}, "sample_indices": episode["sample_indices"]},
        "real_racket_executions": 4,
        "declared_lesson_check": episode["lesson_check"],
        "intended_map": named_map(INTENDED), "rival_map": named_map(rival),
        "demonstrations": demos, "query": query,
        "rival_demonstration_outputs": demo_outputs, "rival_query_output": rival_query,
        "fitting_codebooks": len(fitting), "query_divergent_codebooks": len(divergent),
        "rival_fits_canonical_pairs": [prediction(pair, rival) == pair["output"] for pair in canonical],
        "limitations": "The rival is excluded by some canonical pairs; those pairs are absent from this generated lesson. This is a teaching ambiguity, not an incorrect Racket label or a contradiction of the documented twelve-rival guarantee.",
    }
    (evidence / "production_witness.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("demonstrations", "query", "rival_demonstration_outputs", "declared_lesson_check")}, indent=2))


if __name__ == "__main__":
    main()
