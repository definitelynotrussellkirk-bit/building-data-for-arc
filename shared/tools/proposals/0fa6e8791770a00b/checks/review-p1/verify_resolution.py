#!/usr/bin/env python3
"""Bounded check of the reported P1 against the repaired selected generator."""
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
EXPECTED_SOURCE = "50210d202b830b2e8726ed0f28ab905d0a465512b9297fccf16bef55b116ffa2"


def main():
    root = find_root(__file__)
    gen, source, sha = load_selected_generator("144c5d002191", root=root)
    assert sha == EXPECTED_SOURCE, "Resolution check is bound to the reviewed repair bytes"
    spec = importlib.util.spec_from_file_location("independent_retained_rival", HERE / "reproduce.py")
    old_rival = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old_rival)
    grids = [gen.generate(0, i, difficulty="medium") for i in range(23, 27)]
    fixed = gen.generate(138, 1, difficulty="medium", grid_h=7, grid_w=9, n=4, template_size=4)
    grids.append(fixed)
    applied = Catalog(root).apply("144c5d002191", grids, reference="canonical",
                                  timeout=45, check_generator_domain=True)
    assert applied["generator_sha256"] == sha
    assert applied["executed_rule_hash"] == "c3118b3e9e62"
    assert applied["rule_text_sha256"] == old_rival.RULE_TEXT_SHA256
    pairs = [{"input": row["input"], "output": row["output"]} for row in applied["results"]]
    matches = [old_rival.rival(pair["input"]) == pair["output"] for pair in pairs[:4]]
    assert matches == [False, True, False, False], matches
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
    for query_index in range(4):
        demos = [pair for i, pair in enumerate(pairs[:4]) if i != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []
        assert any(old_rival.rival(pair["input"]) != pair["output"] for pair in demos)
    expected = [[0] * 9 for _ in range(7)]
    for r, c, color in [(0,6,9),(0,7,3),(0,8,9),(1,5,9),(1,6,9),
                        (1,7,9),(1,8,9),(2,4,9),(2,5,9)]:
        expected[r][c] = color
    assert pairs[4]["output"] == expected
    assert sorted(len(cells) for _, cells in old_rival.components(fixed)) == [1, 1, 1, 1, 4]
    assert len(gen.CANONICAL_SHORTCUTS) == 19
    fixed_refutations = {name: rival(fixed) != expected for name, rival in gen.CANONICAL_SHORTCUTS.items()}
    assert all(fixed_refutations.values()), fixed_refutations
    summary = {
        "status": "p1_resolution_verified_for_reported_lesson",
        "task_id": "144c5d002191", "generator_sha256": sha,
        "rule_hash": applied["executed_rule_hash"], "seed": 0,
        "difficulty": "medium", "sample_indices": [23,24,25,26],
        "old_rival_matches_reference": matches,
        "query_still_differs_under_old_rival": not matches[3],
        "production_and_four_rotations_have_refuting_demonstration": True,
        "fixed_witness": {"seed": 138, "sample_index": 1, "difficulty": "medium",
                          "overrides": {"grid_h":7,"grid_w":9,"n":4,"template_size":4},
                          "all_19_declared_canonical_rivals_refuted": fixed_refutations},
        "reference_inputs_count": len(grids),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "limits": "One exact previously failing lesson, its four holdouts, and one fixed composite witness; not a census or an all-seed proof.",
    }
    for name, record in (("resolution_check.json", summary), ("resolution_racket_apply.json", applied)):
        with (HERE / name).open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
