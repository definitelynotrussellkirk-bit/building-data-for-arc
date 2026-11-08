"""One bounded visible-lesson ambiguity probe; gold labels come from Racket.

From the outer packet directory:
  WORK/.venv/bin/python review.py run python3 ../checks/99d5bc858270/corner_priority_probe.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator, public_challenge_id

TASK = "99d5bc858270"


def vertical_corner_priority(grid):
    """Plausible wrong rule: top/bottom edges win a corner tie."""
    h, w = len(grid), len(grid[0])
    lights = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value == 4]
    if len(lights) != 1:
        raise ValueError("Expected exactly one yellow light")
    lr, lc = lights[0]
    if lr == 0:
        dr, dc = 1, 0
    elif lr == h - 1:
        dr, dc = -1, 0
    elif lc == 0:
        dr, dc = 0, 1
    elif lc == w - 1:
        dr, dc = 0, -1
    else:
        raise ValueError("Expected a border light")
    casters = [(r, c, value) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value not in (0, 4)]
    out = [[0] * w for _ in range(h)]
    for r, c, _ in casters:
        r, c = r + dr, c + dc
        while 0 <= r < h and 0 <= c < w:
            out[r][c] = 4
            r, c = r + dr, c + dc
    for r, c, value in casters:
        out[r][c] = value
    return out


def main():
    root = Path.cwd()
    generator, source, source_hash = load_selected_generator(TASK, root=root)
    variants = Catalog()._variants().get(TASK)
    programs = [row["program_solution"] for row in variants
                if hashlib.sha256(row["program_solution"].encode()).hexdigest()
                .startswith(generator.RULE_HASH)]
    assert len(programs) == 1, "Selected canonical authority is ambiguous"
    program = programs[0]
    canonical = next(row for row in variants if row["program_solution"] == program)
    grids = [generator.generate(6, i, difficulty="easy") for i in range(3)]
    assert len({json.dumps(grid) for grid in grids}) == 3
    assert all(not generator.self_check(grid) for grid in grids)
    apply, identity, bridge = _real_evaluator(Path("shared/runtime").resolve())
    try:
        gold = [apply(program, grid) for grid in grids]
        canonical_test = canonical["test"]
        canonical_pairs = list(canonical["train"]) + (
            canonical_test if isinstance(canonical_test, list) else [canonical_test])
        canonical_gold = [apply(program, pair["input"]) for pair in canonical_pairs]
    finally:
        bridge.close()
    rival = [vertical_corner_priority(grid) for grid in grids]
    demos = [dict(input=grid, output=output) for grid, output in zip(grids[:2], gold[:2])]
    query = dict(input=grids[2], output=gold[2])
    findings = generator.lesson_identifiable(demos, query)
    fit = [candidate == output for candidate, output in zip(rival, gold)]
    known_rival_fit = [generator.SEMANTIC_RIVALS["farthest_caster_per_projection"](grid)
                      == output for grid, output in zip(grids, gold)]
    canonical_fit = [vertical_corner_priority(pair["input"]) == output
                     for pair, output in zip(canonical_pairs, canonical_gold)]
    canonical_stored_match = [pair["output"] == output
                             for pair, output in zip(canonical_pairs, canonical_gold)]
    assert fit == [True, True, False]
    assert not findings
    assert known_rival_fit == [False, False, False]
    assert all(canonical_stored_match)
    result = {
        "schema": "arcpuzzles-bounded-peer-check-v1",
        "task_id": TASK,
        "status": "reproduced_visible_lesson_ambiguity",
        "generator_sha256": source_hash,
        "rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_identity": identity,
        "sample": {"seed": 6, "difficulty": "easy", "demo_indices": [0, 1],
                   "query_index": 2, "overrides": {}},
        "light_positions": [generator.observe_overrides(grid)["light_position"] for grid in grids],
        "unique_inputs": 3,
        "self_check_errors": [generator.self_check(grid) for grid in grids],
        "lesson_identifiable_errors": findings,
        "competitor": "vertical_corner_priority",
        "competitor_matches_demos_then_query": fit,
        "declared_farthest_rival_matches_demos_then_query": known_rival_fit,
        "canonical_competitor_matches": canonical_fit,
        "canonical_stored_outputs_match_protected_racket": canonical_stored_match,
        "protected_racket_executions": len(grids) + len(canonical_pairs),
        "public_challenge_id": public_challenge_id({"train": demos, "test": [query]}),
        "demonstrations": demos,
        "query": query,
        "competitor_query_output": rival[2],
        "query_disagreement_cells": sum(a != b for ra, rb in zip(rival[2], gold[2])
                                        for a, b in zip(ra, rb)),
        "scope": "One pinned raw 2-demo/1-query generator window; no production-runner frequency claim. The rival is not canonical-fitting. Every retained gold label was executed by protected Racket.",
        "repair_proposal": "Declare vertical_corner_priority as a finite rival and require a distinguishing corner demonstration when a corner query is allowed; then validate lesson assembly. No repair applied.",
        "reproduce": "WORK/.venv/bin/python review.py run python3 ../checks/99d5bc858270/corner_priority_probe.py",
    }
    destination = Path(__file__).with_name("corner_priority_result.json")
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "generator_sha256", "rule_sha256", "light_positions",
        "competitor_matches_demos_then_query", "lesson_identifiable_errors",
        "canonical_competitor_matches", "protected_racket_executions",
        "query_disagreement_cells", "public_challenge_id")}))


if __name__ == "__main__":
    main()
