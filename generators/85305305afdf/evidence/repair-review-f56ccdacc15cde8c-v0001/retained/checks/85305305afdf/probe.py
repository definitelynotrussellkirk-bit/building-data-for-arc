"""Bounded, source-bound peer check; Python rivals, protected Racket labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "85305305afdf"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SEED = 20261024


def translate(grid):
    """Translate the entire row right, discarding the rightmost column."""
    return [[0] + row[:-1] for row in grid]


def rotate(grid):
    """Circularly translate every row one cell right."""
    return [[row[-1]] + row[:-1] for row in grid]


def sequential(grid):
    """Move rightmost cells first, allowing left cells to use newly freed space."""
    out = [row[:] for row in grid]
    for row in out:
        for col in range(len(row) - 2, -1, -1):
            if row[col] and row[col + 1] == 0:
                row[col + 1], row[col] = row[col], 0
    return out


def main():
    gen, path, source_hash = load_selected_generator(TASK, root=ROOT)
    canonical = next(json.loads(line) for line in canonical_path(ROOT).open()
                     if json.loads(line).get("task_id") == TASK)
    program = canonical["program_solution"]
    rivals = {"whole_row_translation": translate,
              "circular_row_translation": rotate,
              "right_to_left_sequential": sequential}
    draws = [{"seed": SEED, "sample_index": i, "difficulty": "medium", "overrides": {},
              "input": gen.generate(SEED, i, difficulty="medium")}
             for i in range(12)]
    for texture in ("cell_at_right_edge", "cells_blocked"):
        draws.append({"seed": SEED, "sample_index": 12, "difficulty": "medium",
                      "overrides": {"texture": texture},
                      "input": gen.generate(SEED, 12, difficulty="medium", texture=texture)})
    labeled_canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        wrapped = wrap_rule(program)

        def execute(grid):
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            return bridge.eval_text(f"({wrapped} {literal})")

        for draw in draws:
            draw["self_check"] = gen.self_check(draw["input"])
            draw["output"] = execute(draw["input"])
            draw["rival_predictions"] = {name: fn(draw["input"]) for name, fn in rivals.items()}
            draw["rivals_matching"] = [name for name, pred in draw["rival_predictions"].items()
                                       if pred == draw["output"]]
        canonical_checks = [{"split": pair["split"], "input": pair["input"],
                             "output": pair["output"],
                             "racket_matches_stored": execute(pair["input"]) == pair["output"],
                             "self_check": gen.self_check(pair["input"])}
                            for pair in labeled_canonical]
    finally:
        bridge.shutdown()
    ordinary = draws[:12]
    edge, blocked = draws[12:]
    assert all(draw["self_check"] == [] for draw in ordinary)
    assert all(len(draw["rivals_matching"]) == 3 for draw in ordinary)
    assert edge["self_check"] == []
    assert "whole_row_translation" not in edge["rivals_matching"]
    assert "circular_row_translation" not in edge["rivals_matching"]
    assert blocked["self_check"]
    assert "right_to_left_sequential" not in blocked["rivals_matching"]
    assert all(row["racket_matches_stored"] for row in canonical_checks)
    result = {
        "schema": "85305305afdf-bounded-peer-probe-v1",
        "status": "teaching_and_domain_findings_reproduced",
        "task_id": TASK, "generator_source": str(path.relative_to(ROOT)),
        "source_sha256": source_hash,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_program": program,
        "executed_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "rule_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "racket": identity, "protected_racket_evaluations": len(draws) + len(canonical_checks),
        "ordinary_draw_count": len(ordinary), "rival_count": len(rivals),
        "ordinary_matches": {name: sum(name in draw["rivals_matching"] for draw in ordinary)
                             for name in rivals},
        "draws": draws, "canonical_checks": canonical_checks,
        "teaching_witness": {"train_draw_indices": [0, 1, 2], "test_draw_index": 12,
                             "fitting_but_wrong_rivals": ["whole_row_translation", "circular_row_translation"],
                             "scope": "Constructed lesson from generator calls with different overrides; not an emitted default episode."},
        "limits": ["Only 12 ordinary medium draws and 2 explicit textures were executed; no full battery or qualification.",
                   "Racket executed reference labels; rival predictions were executed in Python.",
                   "Blocked texture is not accepted by self_check; it is a canonical-domain coverage issue, not an accepted query witness.",
                   "No automatic approval, audit resolution, source change, or training admission."]}
    (HERE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "source_sha256", "executed_rule_hash", "protected_racket_evaluations", "ordinary_matches")}))


if __name__ == "__main__":
    main()
