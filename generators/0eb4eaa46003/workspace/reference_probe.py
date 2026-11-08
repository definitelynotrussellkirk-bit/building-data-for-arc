"""Reproduce both seeded teaching phases and the paired crop counterexample.

Run with review.py run; this is authoring work, never a visible-only solve.
The public Catalog.apply API executes and records the actual Racket authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator
from profile_probe import oracle_output, scene


TASK_ID = "0eb4eaa46003"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    fixture = root / "generators" / TASK_ID / "counterexamples" / "equal_profiles_different_crops.json"
    spec = json.loads(fixture.read_text())
    inputs = [gen.generate(17, i, difficulty="hard") for i in (1, 0)]
    descriptions = [{"kind": "generated", "seed": 17, "sample_index": i, "difficulty": "hard"}
                    for i in (1, 0)]
    for alternative in ("target_a", "target_b"):
        grid = [[0] * spec["grid_w"] for _ in range(spec["grid_h"])]
        for place in spec["placements"]:
            shape = spec[alternative if place["role"] == "target" else place["role"]]
            for r, row in enumerate(shape):
                for c, value in enumerate(row):
                    if value == "1":
                        grid[place["top"]+r][place["left"]+c] = place["color"]
        inputs.append(grid)
        descriptions.append({"kind": "hand_constructed", "fixture": fixture.relative_to(root).as_posix(),
                             "alternative": alternative})
    (args.out / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    authority = Catalog(root).apply(TASK_ID, inputs, timeout=180, check_generator_domain=True)
    (args.out / "racket.json").write_text(json.dumps(authority, indent=2) + "\n")
    findings = []
    for grid, label, description in zip(inputs, authority["results"], descriptions, strict=True):
        prediction = oracle_output(grid)
        declared = {namespace: {name: {"output": fn(grid), "differs_from_racket": fn(grid) != label["output"]}
                               for name, fn in getattr(gen, namespace).items()}
                    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")}
        findings.append({**description, "self_check": gen.self_check(grid),
                         "python_matches_racket": prediction == label["output"],
                         "racket_error": label.get("error"), "rivals": declared})
    a, b = scene(inputs[2]), scene(inputs[3])
    paired = {"blue_unchanged": a["blues"][0].mask == b["blues"][0].mask,
              "red_unchanged": a["reds"][0].mask == b["reds"][0].mask,
              "rows_equal": a["matches"][0].rows == b["matches"][0].rows,
              "columns_equal": a["matches"][0].columns == b["matches"][0].columns,
              "racket_outputs_differ": authority["results"][2]["output"] != authority["results"][3]["output"]}
    coverage = {name: [i for i in (0, 1)
                       if findings[i]["rivals"]["SEMANTIC_RIVALS"][name]["differs_from_racket"]]
                for name in gen.SEMANTIC_RIVALS}
    passed = (authority["generator_sha256"] == source_hash and authority["rule_hash_matches_catalog"]
              and all(not f["self_check"] and not f["racket_error"] and f["python_matches_racket"] for f in findings)
              and all(paired.values())
              and all(coverage.values()))
    result = {"schema": "profile-reference-witnesses-v2", "task_id": TASK_ID,
              "generator_sha256": source_hash, "generator_path": source.relative_to(root).as_posix(),
              "rule_hash": authority["executed_rule_hash"], "argv": sys.argv,
              "cwd": str(Path.cwd()), "inputs": findings, "paired_crop_witness": paired,
              "seeded_phase_refutation_coverage": coverage,
              "passed": passed}
    (args.out / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": passed, "racket_inputs": len(inputs), "generator_sha256": source_hash,
                      "rule_hash": authority["executed_rule_hash"], "paired_crop_witness": paired}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
