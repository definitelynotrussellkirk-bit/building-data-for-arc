"""Findings-only authoring probe. Labels come exclusively from public apply."""
from pathlib import Path
import hashlib
import json
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK = "a4a3b7fe72bd"
ROOT = find_root(__file__)
gen, source, source_sha = load_selected_generator(TASK, root=ROOT)


def count_side_rival(grid):
    """Sort by true length, but infer square side as twice the color count."""
    info = gen.observe_overrides(grid)
    colors = sorted(
        (c for c in {v for row in grid for v in row} if c),
        key=lambda c: sum(row.count(c) for row in grid), reverse=True,
    )
    n = 2 * info["n_colors"]
    return [[colors[min(r, c, n - 1 - r, n - 1 - c)]
             for c in range(n)] for r in range(n)]


if sys.argv[1] == "prepare":
    canonical = canonical_pairs(TASK, root=ROOT)
    canonical_summary = [{
        "variant": p["variant"], "split": p["split"],
        "pair_index": p["pair_index"],
        "self_check": gen.self_check(p["input"]),
        "mirror_agrees": gen.rule_mirror(p["input"]) == p["output"],
        "count_side_rival_agrees": count_side_rival(p["input"]) == p["output"],
        "observed": gen.observe_overrides(p["input"]),
    } for p in canonical]
    inputs = [gen.generate(0, i, difficulty="medium") for i in range(6, 10)]
    (HERE / "input.json").write_text(json.dumps(inputs) + "\n")
    report = {
        "task_id": TASK, "generator_sha256": source_sha,
        "generator_path": str(source.relative_to(ROOT)),
        "seed": 0, "sample_indices": list(range(6, 10)),
        "difficulty": "medium", "overrides": {},
        "self_check": [gen.self_check(g) for g in inputs],
        "observed": [gen.observe_overrides(g) for g in inputs],
        "canonical": canonical_summary,
        "rival": "output side = 2 * nonzero color count; colors still ranked by length",
        "rival_outputs": [count_side_rival(g) for g in inputs],
        "declared_canonical_shortcuts": list(getattr(gen, "CANONICAL_SHORTCUTS", {})),
        "declared_lesson_competitors": list(getattr(gen, "LESSON_COMPETITORS", {})),
        "declared_local_hypotheses": list(gen._HYPOTHESES),
    }
    (HERE / "prepare.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generator_sha256": source_sha, "output_sides":
                      [gen.observe_overrides(g)["max_length"] for g in inputs],
                      "self_check": report["self_check"]}))
elif sys.argv[1] == "evaluate":
    receipt = json.loads((HERE / "racket.json").read_text())
    prepared = json.loads((HERE / "prepare.json").read_text())
    assert source_sha == receipt["generator_sha256"] == prepared["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"]
    pairs = [{"input": r["input"], "output": r["output"]} for r in receipt["results"]]
    assert all(r["valid_output"] and not r["error"] for r in receipt["results"])
    episode = json.loads((HERE / "episode.jsonl").read_text().splitlines()[0])
    assert episode["train"] + episode["test"] == pairs
    assert episode["provenance"]["generator_sha256"] == source_sha
    assert episode["sample_indices"] == [6, 7, 8, 9]
    assert episode["lesson_check"]["status"] == "passed_declared_hook"
    agrees = [count_side_rival(p["input"]) == p["output"] for p in pairs]
    findings = gen.lesson_identifiable(pairs[:3], pairs[3])
    report = {
        "task_id": TASK, "generator_sha256": source_sha,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_text_sha256": receipt["rule_text_sha256"],
        "seed": 0, "sample_indices": [6, 7, 8, 9],
        "difficulty": "medium", "overrides": {},
        "demonstration_count": 3, "ordering": "indices 6,7,8 demos; index 9 query",
        "rival_matches_racket": agrees,
        "lesson_identifiable": findings,
        "actual_output_sides": [len(p["output"]) for p in pairs],
        "rival_output_sides": [len(count_side_rival(p["input"])) for p in pairs],
        "inputs_validator_accepted": [gen.self_check(p["input"]) == [] for p in pairs],
        "canonical_pair_count": len(prepared["canonical"]),
        "canonical_unique_input_count": len({json.dumps(p["input"]) for p in canonical_pairs(TASK, root=ROOT)}),
        "canonical_validator_and_mirror_pass": all(not p["self_check"] and p["mirror_agrees"] for p in prepared["canonical"]),
        "canonical_count_side_rival_match_count": sum(p["count_side_rival_agrees"] for p in prepared["canonical"]),
        "local_hypotheses": {name: {
            "demo_matches": [gen._hypothesis_output(name, p["input"]) == p["output"] for p in pairs[:3]],
            "query_matches": gen._hypothesis_output(name, pairs[3]["input"]) == pairs[3]["output"],
        } for name in gen._HYPOTHESES},
        "racket_evidence": "checks/audit/a4a3b7fe72bd/racket.json",
        "public_episode_status": episode["lesson_check"]["status"],
        "public_episode_rejection_count": len(episode["rejections"]),
        "public_episode_matches_apply": True,
    }
    (HERE / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
    assert agrees == [True, True, True, False]
    assert findings == [], findings
    print(json.dumps({k: report[k] for k in ("generator_sha256", "executed_rule_hash", "rival_matches_racket", "lesson_identifiable", "actual_output_sides", "rival_output_sides")}))
else:
    raise ValueError("Use prepare or evaluate")
