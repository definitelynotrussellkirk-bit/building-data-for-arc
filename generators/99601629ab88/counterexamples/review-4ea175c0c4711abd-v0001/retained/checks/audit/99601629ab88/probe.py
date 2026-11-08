"""Bounded, findings-only audit; does not modify generator or rule authority."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = REPO / "generators/99601629ab88/generator.py"
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

def frequency_rival(g):
    counts = Counter(v for row in g for v in row if v != 0)
    divider = min(counts, key=lambda color: (-counts[color], color))
    rows = [r for r, row in enumerate(g) if all(v == divider for v in row)]
    cols = [c for c in range(len(g[0])) if all(row[c] == divider for row in g)]
    if not rows or not cols:
        return [[divider]]
    rb = [-1] + rows + [len(g)]
    cb = [-1] + cols + [len(g[0])]
    rr = [(a + 1, b) for a, b in zip(rb, rb[1:]) if a + 1 < b]
    cc = [(a + 1, b) for a, b in zip(cb, cb[1:]) if a + 1 < b]
    return [[0 if g[r0][c0] in (0, divider) else g[r0][c0]
             for c0, _ in reversed(cc)] for r0, _ in rr]

def digest(data):
    return hashlib.sha256(data).hexdigest()

if __name__ == "__main__":
    records = [json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
               if json.loads(line).get("task_id") == M.TASK_ID]
    rules = [r["program_solution"] for r in records]
    assert rules and len(set(rules)) == 1
    cases = []
    for profile in M.PUBLIC_PROFILES:
        cases.append({"case_id": profile, "seed": 1, "sample_index": 2,
                      "difficulty": "medium", "overrides": {"scene_profile": profile}})
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(M.GENERAL_PROFILES):
            cases.append({"case_id": f"{band}_{profile}", "seed": index + 1,
                          "sample_index": 17 * (index + 1), "difficulty": band,
                          "overrides": {"scene_profile": profile}})
    for case in cases:
        g = M.generate(case["seed"], case["sample_index"], difficulty=case["difficulty"], **case["overrides"])
        case.update({"input": g, "self_check": M.self_check(g),
                     "documented_domain_member": case["overrides"]["scene_profile"] in M.SCENE_PROFILES,
                     "observed": M.observe_overrides(g), "mirror_output": M.rule_mirror(g),
                     "frequency_rival_output": frequency_rival(g),
                     "input_sha256": digest(json.dumps(g, separators=(",", ":")).encode()),
                     "deterministic_replay": g == M.generate(case["seed"], case["sample_index"], difficulty=case["difficulty"], **case["overrides"])})
    canonical_train = []
    for record_index, record in enumerate(records):
        for pair_index, pair in enumerate(record["train"]):
            canonical_train.append({"record_index": record_index, "pair_index": pair_index,
                                    "self_check": M.self_check(pair["input"]),
                                    "mirror_matches_published_train": M.rule_mirror(pair["input"]) == pair["output"],
                                    "frequency_rival_fits_published_train": frequency_rival(pair["input"]) == pair["output"]})
    rejected_unknown = False
    try:
        M.generate(1, 2, typo_axis=1)
    except ValueError:
        rejected_unknown = True
    evidence = {"task_id": M.TASK_ID, "version": M.VERSION,
                "generator_path": "repo/generators/99601629ab88/generator.py",
                "generator_sha256": digest(SOURCE.read_bytes()),
                "selected_rule_sha256": digest(rules[0].encode()),
                "selected_rule_normalized_sha256": digest(" ".join(rules[0].split()).encode()),
                "declared_rule_hash": M.RULE_HASH, "canonical_record_count": len(records),
                "canonical_train": canonical_train, "unknown_axis_rejected": rejected_unknown,
                "cases": cases,
                "commands": [{"cwd": "packet_root", "argv": ["python3", "checks/audit/99601629ab88/probe.py"], "exit_code": 0}]}
    (HERE / "input.json").write_text(json.dumps([case["input"] for case in cases]) + "\n")
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"inputs": len(cases), "validator_rejections": sum(bool(c["self_check"]) for c in cases),
                      "canonical_train_checked": len(canonical_train),
                      "frequency_rival_generated_disagreements_with_mirror": sum(c["frequency_rival_output"] != c["mirror_output"] for c in cases)}))
