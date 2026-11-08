"""Adversarial projection-signature audit for generator 3194379886a5."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "3194379886a5"
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "shared" / "runtime"))
sys.path.insert(0, str(REPO / "shared"))


def load():
    spec = importlib.util.spec_from_file_location("audit_319", GEN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def projection_signature(cells):
    """Wrong D4-invariant: unordered sorted row/column population vectors."""
    rows = tuple(sorted(Counter(r for r, _ in cells).values()))
    cols = tuple(sorted(Counter(c for _, c in cells).values()))
    return tuple(sorted((rows, cols)))


def rival(module, grid):
    facts = module._analyze(grid)["facts"]
    query_sig = projection_signature(facts["query_cells"])
    matches = [
        index
        for index, cells in enumerate(facts["prototype_cells"])
        if projection_signature(cells) == query_sig
    ]
    chosen = matches[0] if matches else 0
    output = [[0] * facts["panel_size"] for _ in range(facts["panel_size"])]
    for row, col in facts["prototype_cells"][chosen]:
        output[row][col] = facts["query_color"]
    return output, matches, chosen


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs
    return load_pairs(TASK, root=REPO, labeled_only=True)


def main():
    module = load()
    summary = {
        "schema": "3194379886a5-projection-shortcut-audit-v1",
        "task": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "canonical": {},
        "bands": {},
    }
    pairs = canonical_pairs()
    summary["canonical"] = {
        "labeled_pairs": len(pairs),
        "rival_matches": sum(rival(module, p["input"])[0] == p["output"] for p in pairs),
        "mirror_matches": sum(module.rule_mirror(p["input"]) == p["output"] for p in pairs),
    }

    first_failure = None
    total = correct = collisions = unique = 0
    for family in ("linked", "generalized"):
        for band in ("easy", "medium", "hard"):
            counts = Counter()
            for i in range(2000):
                seed = 12345 + i
                sample_index = i * 17 + 3
                grid = module.generate(
                    seed,
                    sample_index,
                    difficulty=band,
                    scene_family=family,
                )
                true = module.rule_mirror(grid)
                guessed, matches, chosen = rival(module, grid)
                facts = module._analyze(grid)["facts"]
                counts["samples"] += 1
                counts["accepted"] += module.self_check(grid) == []
                counts["correct"] += guessed == true
                counts["unique_signature_match"] += len(matches) == 1
                counts["signature_collision"] += len(matches) > 1
                if guessed != true and first_failure is None:
                    first_failure = {
                        "family": family,
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "true_match_index": facts["match_index"],
                        "signature_matches": matches,
                        "rival_chosen_index": chosen,
                        "input": grid,
                        "true_output": true,
                        "rival_output": guessed,
                    }
            summary["bands"][f"{family}:{band}"] = dict(counts)
            total += counts["samples"]
            correct += counts["correct"]
            collisions += counts["signature_collision"]
            unique += counts["unique_signature_match"]
    summary["aggregate"] = {
        "samples": total,
        "rival_correct": correct,
        "rival_accuracy": correct / total,
        "signature_collisions": collisions,
        "unique_signature_matches": unique,
    }
    if first_failure is None:
        raise AssertionError("expected at least one generated counterexample")
    summary["counterexample"] = {
        key: first_failure[key]
        for key in (
            "family", "difficulty", "seed", "sample_index",
            "true_match_index", "signature_matches", "rival_chosen_index",
        )
    }
    (OUT / "counterexample.json").write_text(json.dumps(first_failure, indent=2) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
