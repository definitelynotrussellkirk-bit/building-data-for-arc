"""Findings-only A1 audit: height-primary, cell-count-secondary rival."""
from collections import Counter
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
ROOT = WORK / "repo"
SOURCE = ROOT / "generators/79b307b1e4da/generator.py"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs


def load_generator():
    spec = importlib.util.spec_from_file_location("audited_79b307b1e4da", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def items(grid):
    body = grid[1:]
    unseen = {(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value}
    result = []
    while unseen:
        start = min(unseen)
        color = body[start[0]][start[1]]
        unseen.remove(start)
        stack, cells = [start], []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen and body[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        result.append({"height": max(r for r, c in cells) - r0 + 1,
                       "width": max(c for r, c in cells) - c0 + 1,
                       "size": len(cells), "color": color,
                       "cells": sorted((r - r0, c - c0) for r, c in cells)})
    return result


def rival(grid):
    """Sort by height, then cell count, retaining the rest of the public rule."""
    palette = [value for value in grid[0] if value]
    objects = sorted(items(grid), key=lambda obj: (-obj["height"], -obj["size"], -obj["width"]))
    output = [[0] * (sum(obj["width"] for obj in objects) + len(objects) - 1)
              for _ in range(max(obj["height"] for obj in objects))]
    left = 0
    for color, obj in zip(palette, objects):
        for row, col in obj["cells"]:
            output[row][left + col] = color
        left += obj["width"] + 1
    return output


def prepare():
    gen = load_generator()
    cases = []
    for pair in canonical_pairs(gen.TASK_ID, root=ROOT):
        cases.append({"kind": "canonical", "identity": {key: pair[key] for key in ("variant", "split", "pair_index")},
                      "input": pair["input"], "canonical_output": pair["output"]})
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for profile_index, profile in enumerate(gen.SCENE_PROFILES):
            seed = band_index * len(gen.SCENE_PROFILES) + profile_index
            overrides = {"scene_profile": profile}
            cases.append({"kind": "generated", "seed": seed, "sample_index": 7,
                          "difficulty": band, "overrides": overrides,
                          "input": gen.generate(seed, 7, difficulty=band, **overrides)})
    grid = [[0] * 9 for _ in range(7)]
    grid[0][:3] = [2, 4, 6]
    # Wider 3x3, five-cell L; narrower 3x2, six-cell rectangle; singleton.
    for r, c in ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)):
        grid[1 + r][c] = 9
    for r in range(3):
        for c in range(2):
            grid[1 + r][5 + c] = 6
    grid[5][4] = 8
    cases.append({"kind": "authored_counterexample", "name": "width_vs_count_tiebreak",
                  "construction": "3x3 L of size 5, 3x2 rectangle of size 6, 1x1 singleton; palette 2,4,6",
                  "input": grid})
    for index, case in enumerate(cases):
        case["index"] = index
        case["validator_reasons"] = gen.self_check(case["input"])
        case["observed_profile"] = gen.observe_overrides(case["input"]).get("scene_profile")
        case["documented_domain"] = "accepted by self_check; declared scene_profile and calibrated bbox/dimension envelope"
        case["object_signatures"] = [{key: obj[key] for key in ("height", "width", "size", "color")} for obj in items(case["input"])]
        case["rival_output"] = rival(case["input"])
        assert case["validator_reasons"] == [], case
        if case["kind"] == "canonical":
            assert case["rival_output"] == case["canonical_output"]
    recipes = sorted(set(recipe for bank in gen._PROFILE_RECIPES.values() for recipe in bank))
    proof = []
    for recipe in recipes:
        width_order = sorted(range(3), key=lambda i: (-recipe[i][0], -recipe[i][1]))
        count_order = sorted(range(3), key=lambda i: (-recipe[i][0], -recipe[i][2], -recipe[i][1]))
        proof.append({"recipe": recipe, "width_order": width_order, "count_order": count_order})
        assert width_order == count_order
    report = {"finding_id": "A1", "task_id": gen.TASK_ID, "version": gen.VERSION,
              "generator_path": str(SOURCE), "generator_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
              "declared_rule_hash": gen.RULE_HASH,
              "rival": "height descending, then cell count descending, then width descending",
              "recipe_support_proof": proof, "cases": cases}
    (OUT / "input.json").write_text(json.dumps({"inputs": [case["input"] for case in cases]}, separators=(",", ":")) + "\n")
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"inputs": len(cases), "canonical": 3, "generated": 15,
                      "authored": 1, "unique_recipes": len(recipes),
                      "generator_sha256": report["generator_sha256"],
                      "authored_validator": cases[-1]["validator_reasons"],
                      "authored_profile": cases[-1]["observed_profile"]}, indent=2))


def score():
    report = json.loads((OUT / "audit.json").read_text())
    authority = json.loads((OUT / "racket.json").read_text())
    assert sha256(SOURCE.read_bytes()).hexdigest() == report["generator_sha256"] == authority["generator_sha256"]
    assert authority["executed_rule_hash"] == report["declared_rule_hash"] == authority["catalog_rule_hash"]
    assert authority["rule_hash_matches_catalog"]
    report["authority"] = {key: authority[key] for key in (
        "reference", "executed_rule_hash", "catalog_rule_hash", "rule_hash_matches_catalog",
        "rule_text_sha256", "generator_sha256", "command", "cwd")}
    fit, total = Counter(), Counter()
    for case, result in zip(report["cases"], authority["results"], strict=True):
        assert result["error"] is None, result
        assert result["index"] == case["index"] and result["input"] == case["input"]
        case["actual_racket_output"] = result["output"]
        case["input_sha256"] = result["input_sha256"]
        case["rival_matches_racket"] = case["rival_output"] == result["output"]
        if case["kind"] == "canonical":
            assert result["output"] == case["canonical_output"]
        total[case["kind"]] += 1
        fit[case["kind"]] += case["rival_matches_racket"]
    assert fit["canonical"] == 3 and fit["generated"] == 15
    assert fit["authored_counterexample"] == 0
    report["result"] = {"classification": "reproduced generated-support shortcut gap",
                        "rival_fit": {key: {"fit": fit[key], "total": total[key]} for key in total}}
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"source_sha256": report["generator_sha256"],
                      "executed_rule_hash": authority["executed_rule_hash"],
                      "rule_text_sha256": authority["rule_text_sha256"],
                      **report["result"],
                      "witness_actual": report["cases"][-1]["actual_racket_output"],
                      "witness_rival": report["cases"][-1]["rival_output"]}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "score": score}[sys.argv[1]]()
