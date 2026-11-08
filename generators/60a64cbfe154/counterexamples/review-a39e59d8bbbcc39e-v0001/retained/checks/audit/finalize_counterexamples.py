from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def jhash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def diffs(a, b):
    return [
        {"row": r, "col": c, "authority": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]

# ff76: supported Racket results versus no-mirror rival.
ff_dir = ROOT / "checks/audit/ff76baf6c2d9"
ff_receipt = json.loads((ff_dir / "racket.json").read_text())
ff_rivals = json.loads((ff_dir / "rival.json").read_text())
ff_cases = []
for result, rival in zip(ff_receipt["results"], ff_rivals):
    authority = result["output"]
    ff_cases.append(
        {
            "index": result["index"],
            "input": result["input"],
            "authority_output": authority,
            "rival_output": rival,
            "input_sha256": result["input_sha256"],
            "authority_output_sha256": result["output_sha256"],
            "rival_output_sha256": jhash(rival),
            "rival_matches_authority": rival == authority,
            "differences": diffs(authority, rival),
        }
    )
assert [case["rival_matches_authority"] for case in ff_cases] == [True, True, True, False]
ff_counterexample = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "ff76baf6c2d9",
    "finding": "three demonstrations omit the color-2 mirror branch; the query requires it",
    "generator_sha256": ff_receipt["generator_sha256"],
    "rule_hash": ff_receipt["executed_rule_hash"],
    "rule_text_sha256": ff_receipt["rule_text_sha256"],
    "seed": 800009,
    "sample_indices": [36, 37, 38, 39],
    "difficulty": "easy",
    "lesson_policy": "first three consecutive samples are demonstrations; fourth is query",
    "validator": {"function": "self_check", "errors": [[], [], [], []]},
    "documented_generator_domain": True,
    "rival": "copy requested templates without the special horizontal reflection for color 2",
    "supported_racket_command": ff_receipt["command"],
    "supported_racket_cwd": "repo",
    "cases": ff_cases,
    "diagnostic_scan": json.loads((ff_dir / "scan.json").read_text()),
}
(ff_dir / "counterexample.json").write_text(
    json.dumps(ff_counterexample, indent=2, sort_keys=True) + "\n"
)

# 60a6: supported Racket result versus first-occupied-cell alignment rival.
sixty_dir = ROOT / "checks/audit/60a64cbfe154"
sixty_receipt = json.loads((sixty_dir / "racket.json").read_text())
sixty_rival = json.loads((sixty_dir / "rival.json").read_text())
result = sixty_receipt["results"][0]
authority = result["output"]
assert authority != sixty_rival
sixty_counterexample = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "60a64cbfe154",
    "finding": "all generated shapes occupy their bbox top-left, so a first-occupied-cell alignment shortcut is never contradicted",
    "generator_sha256": sixty_receipt["generator_sha256"],
    "rule_hash": sixty_receipt["executed_rule_hash"],
    "rule_text_sha256": sixty_receipt["rule_text_sha256"],
    "seed": None,
    "sample_index": None,
    "overrides": None,
    "input_origin": "hand-constructed documented-domain witness",
    "validator": {"function": "self_check", "errors": []},
    "documented_generator_domain": True,
    "domain_basis": [
        "10x10 grid is within declared grid_h/grid_w domains 8..14",
        "exactly two colors, each with one isolated singleton marker and one connected multi-cell shape",
        "both translated bounding boxes fit in bounds",
    ],
    "rival": "translate each shape so its lexicographically first occupied cell, rather than bbox top-left, lands on the marker",
    "supported_racket_command": sixty_receipt["command"],
    "supported_racket_cwd": "repo",
    "input": result["input"],
    "authority_output": authority,
    "rival_output": sixty_rival,
    "input_sha256": result["input_sha256"],
    "authority_output_sha256": result["output_sha256"],
    "rival_output_sha256": jhash(sixty_rival),
    "differences": diffs(authority, sixty_rival),
    "domain_scan": json.loads((sixty_dir / "domain_scan.json").read_text()),
}
(sixty_dir / "counterexample.json").write_text(
    json.dumps(sixty_counterexample, indent=2, sort_keys=True) + "\n"
)

print(json.dumps({
    "ff_demo_matches": [case["rival_matches_authority"] for case in ff_cases],
    "ff_query_diff_cells": len(ff_cases[-1]["differences"]),
    "sixty_diff_cells": len(sixty_counterexample["differences"]),
}, indent=2, sort_keys=True))
