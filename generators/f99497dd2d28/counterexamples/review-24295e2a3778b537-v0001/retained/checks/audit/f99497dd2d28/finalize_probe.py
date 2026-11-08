from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "probe-pre-racket.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
results = racket["results"]
assert len(results) == 1 + len(pre["production"])
assert racket["generator_sha256"] == pre["generator_sha256"]

canonical = results[0]
assert canonical["output"] == pre["canonical_expected"]
assert canonical["output"] != pre["canonical_rival_output"]
assert canonical["generator_domain"]["status"] == "invalid"

matched = 0
branches = {"lr": 0, "non_lr": 0}
for row, result in zip(pre["production"], results[1:]):
    assert result["generator_domain"]["status"] == "valid"
    assert result["output"] == row["rival_output"]
    matched += 1
    branches["lr" if row["lr_symmetric"] else "non_lr"] += 1

witness = {
    "schema": "arcpuzzles-adversarial-audit-v1",
    "task_id": pre["task_id"],
    "finding_id": "AUD-F994-CANONICAL-BRANCH-GAP",
    "classification": "reproduced generator-domain and teaching defect",
    "generator_sha256": racket["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "rival": "draw a horizontal center line iff the cropped shape is LR-symmetric; otherwise draw a vertical center line",
    "emitted_probe": {
        "count": matched,
        "difficulty_counts": {band: sum(row["difficulty"] == band for row in pre["production"]) for band in ("easy", "medium", "hard")},
        "branch_counts": branches,
        "rival_matches_racket": matched,
        "denominator": len(pre["production"]),
        "calls": [
            {
                "difficulty": row["difficulty"],
                "seed": row["seed"],
                "sample_index": row["sample_index"],
                "overrides": row["overrides"],
            }
            for row in pre["production"]
        ],
    },
    "canonical_counterexample": {
        "canonical_train_index": pre["canonical_index"],
        "input": canonical["input"],
        "racket_output": canonical["output"],
        "rival_output": pre["canonical_rival_output"],
        "features": pre["canonical_features"],
        "generator_domain": canonical["generator_domain"],
        "belongs_to_canonical_task": True,
        "emitted_by_current_generator": False,
    },
    "conclusion": (
        "The current generator only emits LR-symmetric odd-height row cases and non-LR column cases. "
        "Its own validator rejects the canonical LR+UD-symmetric even-height column case, so generated "
        "lessons cannot distinguish the simpler LR-only rival from the selected rule."
    ),
    "commands": {
        "prepare": ["python3", "review.py", "run", "python", "../checks/audit/f99497dd2d28/prepare_probe.py"],
        "racket": racket["command"],
        "racket_cwd": racket["cwd"],
    },
    "evidence_sha256": {
        "probe_pre_racket": hashlib.sha256((HERE / "probe-pre-racket.json").read_bytes()).hexdigest(),
        "racket": hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest(),
    },
}
(HERE / "witness.json").write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
print(json.dumps({"matched": matched, "branches": branches, "canonical_domain": canonical["generator_domain"], "rival_disagrees": canonical["output"] != pre["canonical_rival_output"]}, indent=2))
