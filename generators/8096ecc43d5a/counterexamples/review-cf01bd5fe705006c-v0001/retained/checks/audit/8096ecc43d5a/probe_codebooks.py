#!/usr/bin/env python3
"""Bounded audit: all constant D4 codebooks on generated three-demo lessons.

Run through review.py run from the outer packet directory. Labels are obtained
only from Catalog.apply's canonical Racket runtime, never Python predictions.
No solve episode, private-query file, source edit, or broad battery is used.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, load_selected_generator


TASK = "8096ecc43d5a"
INTENDED = (1, 4, 2, 6)
NAMES = (
    "identity", "rotate_cw", "rotate_180", "rotate_ccw", "flip_lr",
    "rotate_cw_after_flip_lr", "flip_ud", "rotate_ccw_after_flip_lr",
)


def transform(grid, action):
    result = [list(row) for row in grid]
    if action >= 4:
        result = [row[::-1] for row in result]
    for _ in range(action % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def crop(grid):
    cells = [(r, c) for r in range(1, len(grid)) for c, x in enumerate(grid[r]) if x]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


MARKER = [[1, 2, 3], [4, 5, 6]]
VARIANTS = [transform(MARKER, action) for action in range(8)]
COMPOSE = [[VARIANTS.index(transform(VARIANTS[inner], outer)) for inner in range(8)]
           for outer in range(8)]
MAPS = list(itertools.product(range(8), repeat=4))


def action_for(codes, mapping):
    action = 0
    for code in codes:
        action = COMPOSE[mapping[code - 1]][action]
    return action


def prediction(pair, mapping):
    return transform(crop(pair["input"]), action_for(pair["codes"], mapping))


def fitting_maps(pairs):
    constraints = []
    for pair in pairs:
        motif = crop(pair["input"])
        allowed = {action for action in range(8) if transform(motif, action) == pair["output"]}
        assert allowed, "Reference output was not a D4 transform of the motif"
        constraints.append((pair["codes"], allowed))
    return [mapping for mapping in MAPS
            if all(action_for(codes, mapping) in allowed for codes, allowed in constraints)]


def named_map(mapping):
    return {str(code): NAMES[action] for code, action in enumerate(mapping, 1)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path.cwd().resolve()
    evidence = Path(__file__).resolve().parent
    gen, source, generator_sha = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    rows = []
    lessons = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(4):
            lesson = []
            for index in range(4):
                grid = gen.generate(seed, index, difficulty=difficulty)
                assert gen.self_check(grid) == []
                record = {"seed": seed, "sample_index": index, "difficulty": difficulty,
                          "overrides": {}, "profile": gen.schedule_profile(seed, index, difficulty),
                          "codes": [v for v in grid[0] if v], "input": grid}
                lesson.append(len(rows))
                rows.append(record)
            lessons.append({"seed": seed, "difficulty": difficulty, "row_indices": lesson})

    applied = Catalog(root).apply(
        TASK, [p["input"] for p in canonical] + [p["input"] for p in rows],
        reference="canonical", check_generator_domain=True, timeout=120,
    )
    (evidence / "racket_apply.json").write_text(json.dumps(applied, indent=2) + "\n")
    assert applied["rule_hash_matches_catalog"]
    assert applied["generator_sha256"] == generator_sha
    results = applied["results"]
    assert len(results) == 52
    assert all(r.get("error") is None and r.get("output") is not None for r in results)
    for pair, result in zip(canonical, results[:4], strict=True):
        assert pair["output"] == result["output"]
        pair["codes"] = [v for v in pair["input"][0] if v]
    for pair, result in zip(rows, results[4:], strict=True):
        pair["output"] = result["output"]
        assert prediction(pair, INTENDED) == pair["output"]

    canonical_maps = fitting_maps(canonical)
    witness = None
    rotations = []
    for lesson in lessons:
        four = [rows[index] for index in lesson["row_indices"]]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(four) if index != query_index]
            query = four[query_index]
            fitting = fitting_maps(demos)
            divergent = [mapping for mapping in fitting if prediction(query, mapping) != query["output"]]
            canonical_survivors = [mapping for mapping in fitting if mapping in canonical_maps]
            declared_survivors = [name for name, rival in gen.LESSON_COMPETITORS.items()
                                  if all(rival(p["input"]) == p["output"] for p in demos)]
            row = {**lesson, "query_index": query_index, "production_order": query_index == 3,
                   "candidate_codebooks": len(MAPS), "fitting_codebooks": len(fitting),
                   "query_divergent_codebooks": len(divergent),
                   "fitting_canonical_codebooks": len(canonical_survivors),
                   "declared_rivals_surviving": declared_survivors}
            rotations.append(row)
            if divergent and (witness is None or (query_index == 3 and not witness["production_order"])):
                rival = min(divergent, key=lambda m: (sum(a != b for a, b in zip(m, INTENDED)), m))
                witness = {**row, "intended_map": named_map(INTENDED), "rival_map": named_map(rival),
                           "rival_actions": list(rival), "demonstrations": demos, "query": query,
                           "rival_demonstration_outputs": [prediction(p, rival) for p in demos],
                           "rival_query_output": prediction(query, rival),
                           "rival_fits_all_four_canonical_pairs": rival in canonical_maps}

    ledger = canonical_path(root)
    authority_rows = [json.loads(line) for line in ledger.read_text().splitlines()
                      if line.strip() and json.loads(line).get("task_id") == TASK]
    rule_sources = {r["program_solution"] for r in authority_rows}
    assert len(rule_sources) == 1
    rule = next(iter(rule_sources))
    binding = {"task_id": TASK, "generator_path": source.relative_to(root).as_posix(),
               "generator_sha256": generator_sha, "generator_version": gen.VERSION,
               "declared_rule_hash": gen.RULE_HASH, "executed_rule_hash": applied["executed_rule_hash"],
               "rule_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
               "canonical_file_sha256": digest(ledger), "probe_sha256": digest(Path(__file__)),
               "support_sha256": digest(root / "shared/runtime/reviewer_support.py"),
               "notes_sha256": digest(source.parent / "notes.md"),
               "tests_sha256": {p.relative_to(root).as_posix(): digest(p)
                                for p in sorted((source.parent / "tests").glob("*.py"))}}
    summary = {"status": "reproduced_teaching_ambiguity" if witness else "no_issue_found",
               "source_binding": binding, "racket_inputs": len(results), "canonical_pairs": len(canonical),
               "generated_inputs": len(rows), "generated_lessons": len(lessons),
               "query_rotations": len(rotations), "candidate_codebooks": len(MAPS),
               "canonical_fitting_codebooks": len(canonical_maps),
               "production_ambiguous": sum(r["production_order"] and r["query_divergent_codebooks"] > 0 for r in rotations),
               "production_checked": len(lessons),
               "rotations_ambiguous": sum(r["query_divergent_codebooks"] > 0 for r in rotations),
               "declared_rival_survivals": sum(bool(r["declared_rivals_surviving"]) for r in rotations),
               "scope": "Seeds 0..3; sample indices 0..3; easy/medium/hard; no overrides; three demonstrations and one query. All 4096 constant D4 codebooks, not arbitrary programs.",
               "rotations": rotations}
    (evidence / "report.json").write_text(json.dumps(summary, indent=2) + "\n")
    (evidence / "witness.json").write_text(json.dumps({"source_binding": binding, "witness": witness}, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("source_binding", "rotations")}, indent=2))
    if witness:
        print(json.dumps({k: v for k, v in witness.items() if k not in ("demonstrations", "query", "rival_demonstration_outputs")}, indent=2))


if __name__ == "__main__":
    main()
