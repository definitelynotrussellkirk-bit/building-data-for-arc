"""Source-bound audit: an undeclared positional-role lesson rival.

Run through the packet's review.py run wrapper. Racket remains the authority;
the local count map is only a diagnostic and is checked against apply receipts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "7017b91a367d"
SOURCE_SHA = "8f48fb04488be1f42a863fb60eb4587aaa433a5c4c560345cedd251ec3c700dc"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest_bytes(json.dumps(grid, separators=(",", ":")).encode())


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n")


def masks(grid):
    return [[sum((grid[r][c + 6 * panel] != 0) << panel for panel in range(3))
             for c in range(5)] for r in range(5)]


def mirror(grid):
    return [[(0, 2, 4, 8)[mask.bit_count()] for mask in row] for row in masks(grid)]


def ignore_left_singletons(grid):
    """Wrong input-only rule: suppress cells belonging only to the left panel."""
    return [[0 if mask == 1 else (0, 2, 4, 8)[mask.bit_count()]
             for mask in row] for row in masks(grid)]


def differences(expected, actual):
    return [{"row": r, "column": c, "racket": expected[r][c], "rival": actual[r][c]}
            for r in range(5) for c in range(5) if expected[r][c] != actual[r][c]]


def load_source():
    gen, path, sha = load_selected_generator(TASK, root=ROOT)
    assert sha == SOURCE_SHA, (sha, SOURCE_SHA)
    rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open()
            if line.strip() and json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    program = rows[0]["program_solution"]
    return gen, path, program


def prepare():
    gen, path, program = load_source()
    (HERE / "audited_generator.py").write_bytes(path.read_bytes())
    (HERE / "audited_rule.rkt").write_text(program)
    rule_sha = digest_bytes(program.encode())
    normalized_hash = digest_bytes(" ".join(program.split()).encode())[:12]
    assert normalized_hash == gen.RULE_HASH == "aa994ed25e88"
    save("source.json", {
        "task_id": TASK, "generator_path": str(path.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA,
        "selected_rule": "shared/data/canonical/puzzles.jsonl: exact task program_solution",
        "rule_text_sha256": rule_sha, "rule_hash": normalized_hash,
        "generator_snapshot": "audited_generator.py", "rule_snapshot": "audited_rule.rkt",
        "scope": "Findings-only audit. No generator or shared-source edits.",
    })

    # Retain the exact small discovery survey: hard seeds 0..4, indices 0..3.
    survey = []
    for seed in range(5):
        grids = [gen.generate(seed, index, difficulty="hard") for index in range(4)]
        present = [sorted({value for row in masks(grid) for value in row}) for grid in grids]
        survey.append({"seed": seed, "sample_indices": list(range(4)),
                       "occupancy_masks": present,
                       "rival_ambiguous": all(1 not in item for item in present[:3]) and 1 in present[3]})
    grids = [gen.generate(4, index, difficulty="hard") for index in range(4)]
    checks = [gen.self_check(grid, difficulty="hard") for grid in grids]
    assert checks == [[], [], [], []]
    assert len({grid_hash(grid) for grid in grids}) == 4
    assert survey[-1]["rival_ambiguous"]
    save("input.json", {"inputs": grids})
    save("rival.json", {
        "rival": "ignore_left_singletons", "definition": ignore_left_singletons.__doc__,
        "input_only": True, "source_sha256": SOURCE_SHA,
        "predictions": [{"sample_index": index, "input_sha256": grid_hash(grid),
                         "output": ignore_left_singletons(grid)} for index, grid in enumerate(grids)]
    })

    # A separate bounded diagnostic: templates do not permit ignoring any whole
    # panel everywhere. This is a complete analysis of the 240 declared masks,
    # independent of Racket and not a claim about all lawful input shapes.
    partial_information = []
    variants = list(gen._VARIANT_TO_PROFILE)
    assert len(variants) == 240
    for subset in ((0,), (1,), (2,), (0, 1), (0, 2), (1, 2)):
        keys = defaultdict(set)
        bitset = sum(1 << panel for panel in subset)
        for pattern in variants:
            key = tuple(tuple(mask & bitset for mask in row) for row in pattern)
            output = tuple(tuple(mask.bit_count() for mask in row) for row in pattern)
            keys[key].add(output)
        partial_information.append({"observed_panels": subset, "distinct_keys": len(keys),
                                    "ambiguous_keys": sum(len(values) > 1 for values in keys.values())})
    canonical = canonical_pairs(TASK, root=ROOT)
    save("prepare.json", {
        "task_id": TASK, "generator_sha256": SOURCE_SHA, "rule_text_sha256": rule_sha,
        "probe": "Preliminary Python analysis; final authority comparison is in finding.json.",
        "selection_survey": {"difficulty": "hard", "seeds": [0, 1, 2, 3, 4],
                             "episodes": 5, "generated_grids": 20, "rows": survey},
        "selected": {"seed": 4, "difficulty": "hard", "sample_indices": [0, 1, 2, 3],
                     "demonstrations": 3, "queries": 1, "self_check": checks,
                     "distinct_inputs": 4,
                     "mask_counts": [{str(mask): sum(row.count(mask) for row in masks(grid))
                                      for mask in range(8)} for grid in grids]},
        "template_information_diagnostic": {"mask_variants": len(variants), "rows": partial_information},
        "canonical_pair_count": len(canonical),
        "new_rival_canonical_matches": sum(ignore_left_singletons(pair["input"]) == pair["output"]
                                            for pair in canonical),
        "declared_rivals": {name: list(getattr(gen, name, {}))
                            for name in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")},
    })
    print(json.dumps({"prepared": True, "seed": 4, "sample_indices": [0, 1, 2, 3],
                      "generator_sha256": SOURCE_SHA, "rule_text_sha256": rule_sha}))


def verify():
    gen, _, program = load_source()
    source = json.loads((HERE / "source.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    episodes = [json.loads(line) for line in (HERE / "production.jsonl").read_text().splitlines() if line.strip()]
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode["seed"] == 4
    assert episode["sample_indices"] == [0, 1, 2, 3], episode.get("sample_indices")
    assert episode["provenance"]["generator_sha256"] == SOURCE_SHA
    assert episode["executed_rule_hash"] == "aa994ed25e88"
    assert applied["generator_sha256"] == SOURCE_SHA
    # source.json hashes the canonical rule! program. Public apply hashes the
    # converted callable Racket text under its rule_text_sha256 field.
    assert source["rule_text_sha256"] == digest_bytes(program.encode())
    assert episode["program"] == program
    assert applied["rule_hash_matches_catalog"]
    assert applied["executed_rule_hash"] == "aa994ed25e88"
    grids = json.loads((HERE / "input.json").read_text())["inputs"]
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert len(applied["results"]) == len(pairs) == 4
    comparisons = []
    for index, (grid, pair, result) in enumerate(zip(grids, pairs, applied["results"], strict=True)):
        assert grid == pair["input"] == result["input"]
        output = result["output"]
        assert output == pair["output"] == mirror(grid)
        assert gen.self_check(grid, difficulty="hard") == []
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        prediction = ignore_left_singletons(grid)
        comparisons.append({"sample_index": index, "split": "train" if index < 3 else "test",
                            "input_sha256": grid_hash(grid), "output_sha256": grid_hash(output),
                            "self_check": [], "rival_matches": prediction == output,
                            "differences": differences(output, prediction)})
    assert [item["rival_matches"] for item in comparisons] == [True, True, True, False]
    declared = {}
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        declared[namespace] = {name: {"demo_matches": [rival(pair["input"]) == pair["output"] for pair in pairs[:3]],
                                    "query_matches": rival(pairs[3]["input"]) == pairs[3]["output"]}
                               for name, rival in getattr(gen, namespace, {}).items()}
    hook = gen.lesson_identifiable(pairs[:3], pairs[3])
    assert hook == []
    report = {
        "finding_id": "A2-7017-1", "classification": "reproduced teaching ambiguity",
        "task_id": TASK, "generator_sha256": SOURCE_SHA,
        "rule_hash": "aa994ed25e88", "canonical_program_sha256": source["rule_text_sha256"],
        "executed_callable_sha256": applied["rule_text_sha256"],
        "source_unchanged": digest_bytes((ROOT / "generators" / TASK / "generator.py").read_bytes()) == SOURCE_SHA,
        "production": {"seed": 4, "difficulty": "hard", "sample_indices": episode["sample_indices"],
                       "demonstration_count": 3, "query_count": 1,
                       "policy": "production order; first three accepted pairs are demonstrations",
                       "rejections": episode["rejections"], "retained_episode": "production.jsonl"},
        "rival": {"name": "ignore_left_singletons", "definition": ignore_left_singletons.__doc__,
                  "demonstrations_matched": 3, "demonstrations_total": 3,
                  "query_disagrees": True, "query_changed_cells": len(comparisons[3]["differences"]),
                  "is_canonical_shortcut": False,
                  "limitation": "The rival is refuted by at least one original canonical pair; the finding concerns this generated lesson."},
        "racket_comparisons": comparisons,
        "declared_rival_results": declared,
        "lesson_identifiable_returned": hook,
        "root_cause": "The placement schedule guarantees border evidence and all total count levels, but not singleton evidence for every panel. The only declared rival concerns the central border.",
        "scope": "One exact production episode, four independent public apply results; no population failure rate or universal identifiability claim. No full battery or audit-source fix.",
    }
    save("finding.json", report)
    print(json.dumps({"status": "REPRODUCED", "finding_id": report["finding_id"],
                      "demo_matches": 3, "query_changed_cells": report["rival"]["query_changed_cells"],
                      "generator_sha256": SOURCE_SHA}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify"))
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else verify)()
