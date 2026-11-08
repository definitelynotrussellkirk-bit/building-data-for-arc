"""Focused immutable-generator audit; reference labels come from public CLI files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


TASK = "cf6ef609da0d"
OUT = Path(__file__).resolve().parent


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(root):
    path = root / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid)
              for c, color in enumerate(row) if color == 6}
    answer = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        todo = [first]
        cells = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in unseen:
                    unseen.remove(cell)
                    todo.append(cell)
        answer.append(sorted(cells))
    return answer


def predict(grid, kind):
    groups = components(grid)
    distances = [min(abs(r - c) for r, c in group) for group in groups]
    best = min(distances, default=None)
    output = [[0 for _ in row] for row in grid]
    for group, distance in zip(groups, distances):
        if kind == "nearest_diagonal":
            keep = distance == best
        elif kind == "bbox_diagonal":
            rs, cs = zip(*group)
            keep = max(min(rs), min(cs)) <= min(max(rs), max(cs))
        elif kind == "intended_preview":
            keep = distance == 0
        else:
            raise ValueError(kind)
        if keep:
            for r, c in group:
                output[r][c] = 2
    return output


def prepare(root):
    module, source = load_generator(root)
    canonical = canonical_pairs(TASK, root=find_root(source), labeled_only=True)
    rivals = ("nearest_diagonal", "bbox_diagonal")
    canonical_fit = {
        name: {"matching_pairs": sum(predict(p["input"], name) == p["output"]
                                    for p in canonical),
               "total_pairs": len(canonical)} for name in rivals}
    ordinary = []
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = module.generate(17, index, difficulty=band)
            ordinary.append({"seed": 17, "sample_index": index, "difficulty": band,
                             "overrides": {}, "input": grid,
                             "validator_errors": module.self_check(grid),
                             "rival_output": predict(grid, "nearest_diagonal")})
    witness = module.generate(17, 0, difficulty="medium", texture="none_on_diagonal")
    write("input.json", witness)
    write("rival.json", predict(witness, "nearest_diagonal"))
    write("sample-inputs.json", [p["input"] for p in canonical] +
          [p["input"] for p in ordinary])
    candidate = None
    search_rows = []
    for seed in range(20):
        grids = [module.generate(seed, i, difficulty="medium") for i in range(4)]
        agreement = [predict(g, "bbox_diagonal") == predict(g, "intended_preview")
                     for g in grids]
        search_rows.append({"seed": seed, "sample_indices": list(range(4)),
                            "bbox_matches_intended_preview": agreement})
        if agreement[:3] == [True, True, True] and not agreement[3] and candidate is None:
            candidate = {"seed": seed, "difficulty": "medium", "sample_indices": list(range(4)),
                         "overrides": {}, "inputs": grids,
                         "validator_errors": [module.self_check(g) for g in grids]}
    if candidate is not None:
        write("lesson-inputs.json", candidate["inputs"])
    metadata = {"task_id": TASK, "generator_sha256": digest(source),
                "generator_version": module.VERSION,
                "canonical_fit": canonical_fit, "canonical": canonical,
                "ordinary_samples": ordinary,
                "declared_rivals": {name: list(getattr(module, name, {})) for name in
                                    ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")},
                "nearest_diagonal_witness": {
                    "seed": 17, "sample_index": 0, "difficulty": "medium",
                    "overrides": {"texture": "none_on_diagonal"},
                    "input": witness, "rival_output": predict(witness, "nearest_diagonal"),
                    "validator_errors": module.self_check(witness),
                    "within_documented_generator_domain": True,
                    "domain_reason": "Explicitly declared none_on_diagonal degenerate texture.",
                    "within_ordinary_random_support": False},
                "bbox_candidate_search": {"seed_range": [0, 19], "difficulty": "medium",
                                         "sample_index_range": [0, 3], "rows": search_rows,
                                         "note": "Python preview only; requires Racket verification."},
                "bbox_lesson_candidate": candidate}
    write("prepared.json", metadata)
    print(json.dumps({"generator_sha256": metadata["generator_sha256"],
                      "canonical_fit": canonical_fit, "ordinary_sample_count": len(ordinary),
                      "bbox_candidate_seed": candidate["seed"] if candidate else None,
                      "nearest_witness_validator_errors": module.self_check(witness)}))


def compare(root):
    metadata = json.loads((OUT / "prepared.json").read_text())
    module, source = load_generator(root)
    assert digest(source) == metadata["generator_sha256"]
    reference = json.loads((OUT / "racket.json").read_text())
    samples = json.loads((OUT / "sample-racket.json").read_text())
    for record in (reference, samples):
        assert record["generator_sha256"] == digest(source)
        assert record["rule_hash_matches_catalog"]
        assert all(result["error"] is None for result in record["results"])
    witness = metadata["nearest_diagonal_witness"]
    actual = reference["results"][0]["output"]
    assert actual != witness["rival_output"]
    counterexample = {"task_id": TASK, "generator_sha256": digest(source),
                      "executed_rule_hash": reference["executed_rule_hash"],
                      "rule_text_sha256": reference["rule_text_sha256"],
                      **witness, "racket_output": actual,
                      "rival": "Keep all color-6 components minimizing min(abs(r-c)); recolor to 2.",
                      "racket_command": reference["command"], "racket_cwd": reference["cwd"]}
    write("counterexample.json", counterexample)
    rows = metadata["canonical"] + metadata["ordinary_samples"]
    assert len(rows) == len(samples["results"])
    for row, result in zip(rows, samples["results"]):
        assert result["input"] == row["input"]
        assert predict(row["input"], "nearest_diagonal") == result["output"]
        if "output" in row:
            assert row["output"] == result["output"]
    lesson = json.loads((OUT / "lesson.jsonl").read_text().strip())
    lesson_reference = json.loads((OUT / "lesson-racket.json").read_text())
    assert lesson["provenance"]["generator_sha256"] == digest(source)
    assert lesson_reference["generator_sha256"] == digest(source)
    assert lesson_reference["executed_rule_hash"] == reference["executed_rule_hash"]
    assert lesson_reference["rule_hash_matches_catalog"]
    assert lesson["sample_indices"] == [0, 1, 2, 3]
    assert lesson["rejections"] == []
    pairs = lesson["train"] + lesson["test"]
    assert [p["input"] for p in pairs] == metadata["bbox_lesson_candidate"]["inputs"]
    agreement = []
    for pair, result in zip(pairs, lesson_reference["results"], strict=True):
        assert result["error"] is None
        assert result["input"] == pair["input"]
        assert result["output"] == pair["output"]
        assert module.self_check(pair["input"]) == []
        agreement.append(predict(pair["input"], "bbox_diagonal") == result["output"])
    assert agreement == [True, True, True, False]
    query = pairs[3]
    rival_output = predict(query["input"], "bbox_diagonal")
    changes = [{"row": r, "col": c, "racket": query["output"][r][c], "rival": value}
               for r, row in enumerate(rival_output) for c, value in enumerate(row)
               if value != query["output"][r][c]]
    write("bbox-rival.json", rival_output)
    write("bbox-counterexample.json", {
        "task_id": TASK, "generator_sha256": digest(source),
        "executed_rule_hash": reference["executed_rule_hash"],
        "rule_text_sha256": reference["rule_text_sha256"],
        "rival": "Keep color-6 components whose bounding boxes intersect the main diagonal; recolor to 2.",
        "rival_code": "checks/audit/cf6ef609da0d/probe.py:predict(kind='bbox_diagonal')",
        "seed": lesson["seed"], "episode_index": lesson["episode_index"],
        "difficulty": lesson["provenance"]["difficulty"], "overrides": {},
        "sample_indices": lesson["sample_indices"], "sampling": lesson["sampling"],
        "demonstrations": lesson["train"], "query_sample_index": 3,
        "input": query["input"], "racket_output": query["output"],
        "rival_output": rival_output, "differing_cells": changes,
        "rival_demo_agreement": agreement[:3], "rival_query_agreement": agreement[3],
        "validator_errors": module.self_check(query["input"]),
        "within_documented_generator_domain": True,
        "within_ordinary_random_support": True,
        "domain_reason": "Unmodified default generator; 3 ordinary separated color-6 components, one on the diagonal and two off.",
        "racket_command": lesson_reference["command"], "racket_cwd": lesson_reference["cwd"],
        "public_materialization": "checks/audit/cf6ef609da0d/lesson.jsonl",
        "canonical_rival_fit": metadata["canonical_fit"]["bbox_diagonal"]})
    summary = {"status": "reproduced_distribution_shortcut", "task_id": TASK,
               "generator_sha256": digest(source),
               "executed_rule_hash": reference["executed_rule_hash"],
               "rule_text_sha256": reference["rule_text_sha256"],
               "canonical_matching": len(metadata["canonical"]),
               "canonical_total": len(metadata["canonical"]),
               "ordinary_matching": len(metadata["ordinary_samples"]),
               "ordinary_total": len(metadata["ordinary_samples"]),
               "ordinary_unique_inputs": len({json.dumps(p["input"]) for p in metadata["ordinary_samples"]}),
               "ordinary_seed": 17, "ordinary_indices_per_band": [0, 11],
               "ordinary_bands": ["easy", "medium", "hard"],
               "ordinary_validator_failures": sum(bool(p["validator_errors"]) for p in metadata["ordinary_samples"]),
               "witness_racket_nonzero": sum(v != 0 for row in actual for v in row),
               "witness_rival_nonzero": sum(v != 0 for row in witness["rival_output"] for v in row),
               "bbox_lesson": {"status": "reproduced_production_lesson_ambiguity",
                              "seed": 0, "difficulty": "medium", "overrides": {},
                              "sample_indices": [0, 1, 2, 3], "demonstrations": 3,
                              "queries": 1, "lessons_checked": 1,
                              "rival_demo_matches": 3, "query_differing_cells": changes,
                              "canonical_rival_fit": metadata["canonical_fit"]["bbox_diagonal"],
                              "validator_failures": 0,
                              "note": "One source-bound, standard production lesson; no frequency claim."},
               "limitations": ["Sample agreement alone is finite; source invariant establishes the ordinary-support equivalence.",
                               "Degenerate texture is documented but never chosen by ordinary random generation.",
                               "No wrong generated label is claimed."]}
    write("summary.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "compare"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    {"prepare": prepare, "compare": compare}[args.mode](args.root.resolve())
