"""Small finite source-bound existing-rival review; no qualification changes."""
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(__file__)
OUT = Path(__file__).with_name("peer_learnability.json")
gen, source, sha = load_selected_generator("2dacb90452ce", root=ROOT)
PROGRAM = "(upscale peer_grid 2)"
lessons = []
findings = []
with RacketBridge() as bridge:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for size in (2, 3, 4, 5):
            seed = 424242 + 100 * band_index + size
            pairs = []
            for index in range(3):
                grid = gen.generate(seed, index, difficulty=band, grid_size=size)
                assert gen.self_check(grid) == []
                bridge.define_grid("peer_grid", grid)
                output = bridge.eval_text(PROGRAM)
                assert output == gen.rule_mirror(grid)
                pairs.append({"sample_index": index, "input": grid, "output": output})
            rotations = []
            for qi in range(3):
                demos = [pair for i, pair in enumerate(pairs) if i != qi]
                query = pairs[qi]
                rivals = []
                for name, rival in gen.SEMANTIC_RIVALS.items():
                    fits = all(rival(p["input"]) == p["output"] for p in demos)
                    answer = rival(query["input"])
                    disagrees = answer != query["output"]
                    rivals.append({"name": name, "fits_visible_demos": fits,
                                   "disagrees_on_query": disagrees,
                                   "query_output": answer})
                    if fits and disagrees:
                        findings.append({"seed": seed, "band": band, "size": size,
                                         "query_index": qi, "rival": name})
                reasons = gen.lesson_identifiable(demos, query)
                assert not reasons, reasons
                rotations.append({"query_index": qi, "rivals": rivals,
                                  "lesson_identifiable_reasons": reasons})
            lessons.append({"seed": seed, "difficulty": band, "grid_size": size,
                            "pairs": pairs, "rotations": rotations})
    runtime_identity = bridge.runtime_identity
assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
report = {
    "schema": "bounded-peer-learnability-v1", "task_id": gen.TASK_ID,
    "generator_source": str(source.relative_to(ROOT)), "generator_sha256": sha,
    "rule_hash_claimed_by_generator": gen.RULE_HASH,
    "executed_racket_expression": PROGRAM,
    "runtime_identity": runtime_identity,
    "counts": {"lessons": 12, "racket_labeled_inputs": 36,
               "query_rotations": 36, "rival_rotation_checks": 144,
               "answer_disagreeing_survivors": len(findings)},
    "findings": findings, "lessons": lessons,
    "scope": "Four current named rivals; three consecutive indices at each size and band; finite fixed seeds. No all-rule uniqueness claim, battery, historical-audit disposition, approval, variant or training change."
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"artifact": str(OUT), "generator_sha256": sha, **report["counts"]}))
assert not findings, findings
