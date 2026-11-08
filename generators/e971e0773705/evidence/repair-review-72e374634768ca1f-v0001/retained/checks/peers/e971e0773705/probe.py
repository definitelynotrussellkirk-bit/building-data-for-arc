"""Replay one production lesson against a plausible 8-connected rival.

From the outer packet:
WORK/.venv/bin/python review.py run python3 ../checks/peers/e971e0773705/probe.py
Only result.json beside this script is written. No source or approval is changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from arcpuzzles.runtime import generate
from reviewer_support import find_root, load_selected_generator, public_challenge_id

TASK = "e971e0773705"
EXPECTED_SOURCE = "1bb0029217dfe3bc4d19aeed64933a5d41db97231c4596a74253544ff650e5b9"
EXPECTED_RULE = "2855526e979d"
HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    assert source_hash == EXPECTED_SOURCE, ("source changed", source_hash)
    catalog = Catalog(ROOT)
    authority = {v["program_solution"] for v in catalog.get(TASK)["variants"]}
    assert len(authority) == 1, "Canonical authority must be unique"
    canonical = authority.pop()
    rule_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert rule_hash == EXPECTED_RULE
    needle = "(list cr (+ cc 1))"
    assert canonical.count(needle) == 1
    rival = canonical.replace(needle, needle + " (list (- cr 1) (- cc 1))"
                              " (list (- cr 1) (+ cc 1))"
                              " (list (+ cr 1) (- cc 1))"
                              " (list (+ cr 1) (+ cc 1))")
    # Use native production assembly; its first three accepted inputs are demos.
    episode = generate(catalog, TASK, count=1, seed=1, n_train=3, n_test=4,
                       sample_index=0, allow_unapproved=True, timeout=60)[0]
    assert episode["sample_indices"] == list(range(7))
    assert episode["executed_rule_hash"] == EXPECTED_RULE
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert len({digest(p["input"]) for split in ("train", "test") for p in episode[split]}) == 7
    apply, runtime_identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    checks = []
    try:
        for split in ("train", "test"):
            for index, pair in enumerate(episode[split]):
                sample_index = index + (3 if split == "test" else 0)
                grid = module.generate(seed=1, sample_index=sample_index)
                assert grid == pair["input"]
                assert module.self_check(grid) == []
                actual = apply(canonical, grid)
                prediction = apply(rival, grid)
                assert actual == pair["output"], "Native and protected replay labels disagree"
                facts = module._facts(grid)
                checks.append({"split": split, "index": index, "sample_index": sample_index,
                               "input_sha256": digest(grid), "counts_top_bottom": [facts["top_count"], facts["bottom_count"]],
                               "scene_profile": module._analysis(grid)["scene_profile"],
                               "rival_output": prediction, "matches": prediction == actual})
    finally:
        bridge.close()
    demo_fits = all(c["matches"] for c in checks if c["split"] == "train")
    query_disagreements = [c["index"] for c in checks if c["split"] == "test" and not c["matches"]]
    finding = demo_fits and bool(query_disagreements)
    minimal = None
    if finding:
        qi = query_disagreements[0]
        minimal = {"train": episode["train"], "test": [episode["test"][qi]],
                   "original_query_index": qi,
                   "rival_query_output": next(c["rival_output"] for c in checks if c["split"] == "test" and c["index"] == qi)}
    result = {"schema": "arc-peer-learnability-probe-v1", "task_id": TASK,
              "generator_source": source.relative_to(ROOT).as_posix(), "generator_sha256": source_hash,
              "normalized_canonical_rule_hash": rule_hash,
              "canonical_program": canonical, "rival_program": rival,
              "rival": "Treat diagonally touching red cells as connected; otherwise execute the same orientation classifier, capped counts, and emblem.",
              "runtime_identity": runtime_identity,
              "production_recipe": {"seed": 1, "sample_index": 0, "n_train": 3, "n_test": 4, "difficulty": None, "overrides": {}},
              "production_accepted_indices": episode["sample_indices"],
              "production_rejections": episode["rejections"],
              "production_public_id": public_challenge_id(episode),
              "scope": {"production_episodes": 1, "demos": 3, "queries": 4, "rivals": 1,
                        "canonical_protected_replays": 7, "rival_protected_replays": 7},
              "checks": checks, "demo_fits": demo_fits, "query_disagreements": query_disagreements,
              "finding": finding, "minimal_lesson": minimal,
              "limits": ["One seed and one connectivity rival; not universal uniqueness or frequency evidence.",
                         "The retained minimal lesson preserves all three visible demos and one disagreeing query.",
                         "No production repair, safety approval, parametric acceptance, or training admission is claimed."]}
    (HOME / "result.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"finding": finding, "demo_fits": demo_fits, "query_disagreements": query_disagreements,
                      "scope": result["scope"], "result": str(HOME / "result.json")}))


if __name__ == "__main__":
    main()
