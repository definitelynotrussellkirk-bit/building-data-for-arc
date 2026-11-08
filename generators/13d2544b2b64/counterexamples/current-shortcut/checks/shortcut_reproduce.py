"""Reproduce the three current canonical-fitting shortcuts; labels are verified separately by Racket."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

root = Path.cwd()
out = root.parent / "checks" / "shortcuts-final"
out.mkdir(parents=True, exist_ok=True)
generator, source, digest = load_selected_generator("13d2544b2b64", root=root)
pairs = canonical_pairs("13d2544b2b64", root=root)
profiles = {
    "ignore_color_equality": "equality_mismatch",
    "vertical_priority": "horizontal_precedence",
    "background_only": "target_overwrite",
}
cases = []
for name, profile in profiles.items():
    grid = generator.generate(41, 0, scene_profile=profile)
    rival = generator.CANONICAL_SHORTCUTS[name]
    fit = [rival(pair["input"]) == pair["output"] for pair in pairs]
    assert all(fit)
    assert generator.self_check(grid) == []
    expected = generator.rule_mirror(grid)
    prediction = rival(grid)
    assert expected != prediction
    cases.append({
        "rival": name,
        "replay": {"seed": 41, "sample_index": 0, "difficulty": None, "scene_profile": profile},
        "canonical_fit": fit,
        "self_check": [],
        "input": grid,
        "python_mirror_output": expected,
        "rival_output": prediction,
        "differences": [
            {"row": r, "column": c, "official": expected[r][c], "rival": prediction[r][c]}
            for r in range(len(grid)) for c in range(len(grid[0]))
            if expected[r][c] != prediction[r][c]
        ],
    })
record = {"task_id": "13d2544b2b64", "generator_sha256": digest,
          "label_status": "Python mirror, pending separate public Racket apply",
          "canonical_pairs": len(pairs), "cases": cases}
(out / "python-observations.json").write_text(json.dumps(record, indent=2) + "\n")
(out / "inputs.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}, indent=2) + "\n")
print(json.dumps({"generator_sha256": digest, "cases": len(cases), "canonical_pairs": len(pairs),
                  "differences": [case["differences"] for case in cases]}))
