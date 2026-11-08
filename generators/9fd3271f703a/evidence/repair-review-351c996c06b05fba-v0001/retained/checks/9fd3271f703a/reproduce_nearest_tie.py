#!/usr/bin/env python3
"""Bounded protected-Racket review of the nearest-partner tie-break lesson."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "9fd3271f703a"
EXPECTED_RULE_SHA256 = "33a9dd3624dbead369cf3338df8db7111a411fd28ac109469ee64aeff0886292"
TIE_FRAGMENT = "(else (< (obj-c1 a) (obj-c1 b)))"
RIVAL_FRAGMENT = "(else (> (obj-c1 a) (obj-c1 b)))"


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def authored_query():
    """Minimum admitted size/motif count, with two equally near partners."""
    grid = [[8] * 20 for _ in range(20)]
    for col in range(5, 15):
        grid[0][col] = 3
    for start in (3, 13):
        for row in range(8, 11):
            for col in range(start, start + 3):
                grid[row][col] = 2
    for row, col, center in ((2, 8, 3), (8, 8, 2)):
        for dr in range(3):
            for dc in range(3):
                grid[row + dr][col + dc] = 1
        grid[row + 1][col + 1] = center
    return grid


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Choose a fresh output path")
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    canonical_rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    canonical_rows = [row for row in canonical_rows if row.get("task_id") == TASK_ID]
    programs = {row["program_solution"] for row in canonical_rows}
    assert len(programs) == 1
    canonical = programs.pop()
    assert sha(canonical) == EXPECTED_RULE_SHA256
    assert canonical.count(TIE_FRAGMENT) == 1
    rival = canonical.replace(TIE_FRAGMENT, RIVAL_FRAGMENT, 1)
    original = next(row for row in canonical_rows if row.get("source") == "training")
    source_binding = {
        "generator": {"path": generator_path.relative_to(root).as_posix(), "sha256": generator_sha},
        "canonical_program_sha256": sha(canonical),
        "normalized_rule_hash": generator.RULE_HASH,
        "reproducer_sha256": sha(Path(__file__).read_bytes()),
    }
    generated = []
    for index in range(4):
        grid = generator.generate(0, index, difficulty="easy")
        errors = generator.self_check(grid, difficulty="easy")
        assert errors == []
        generated.append({"seed": 0, "sample_index": index, "difficulty": "easy",
                          "observed": generator.observe_overrides(grid), "input": grid})
    query = authored_query()
    query_errors = generator.self_check(query, difficulty="easy")
    observed = generator.observe_overrides(query)
    assert query_errors == []
    assert observed == {"scale_profile": "compact4", "scene_profile": "nearest_control", "palette_profile": "bg8"}
    info, errors = generator._analyse(query)
    assert errors == []
    motif = next(motif for motif in info["motifs"] if (motif["r"], motif["c"]) == (8, 8))
    assert [(candidate["gap"], candidate["box"]) for candidate in motif["candidates"]] == [
        (3, (8, 3, 10, 5)), (3, (8, 13, 10, 15))]

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        wrapped = {name: wrap_rule(source) for name, source in (("canonical", canonical), ("rival", rival))}

        def execute(name, grid):
            return bridge.eval_text(f"({wrapped[name]} {literal(grid)})")

        canonical_checks = []
        for index, pair in enumerate(original["train"]):
            selected = execute("canonical", pair["input"])
            alternative = execute("rival", pair["input"])
            canonical_checks.append({"index": index, "input": pair["input"],
                "output": selected, "rival_output": alternative,
                "canonical_label_matches": selected == pair["output"],
                "rival_fits": alternative == selected})
        for pair in generated:
            pair["output"] = execute("canonical", pair["input"])
            pair["rival_output"] = execute("rival", pair["input"])
            pair["rival_fits"] = pair["output"] == pair["rival_output"]
        selected = execute("canonical", query)
        alternative = execute("rival", query)
    changed = [{"row": row, "col": col, "canonical": selected[row][col], "rival": alternative[row][col]}
               for row in range(20) for col in range(20) if selected[row][col] != alternative[row][col]]
    fits = (all(row["canonical_label_matches"] and row["rival_fits"] for row in canonical_checks)
            and all(row["rival_fits"] for row in generated))
    confirmed = fits and bool(changed)
    assert sha(generator_path.read_bytes()) == generator_sha, "Generator changed while auditing"
    report = {
        "schema": "arcpuzzles-bounded-peer-adversarial-v1", "task_id": TASK_ID,
        "status": "counterexample_found" if confirmed else "hypothesis_not_confirmed",
        "finding": "Rightmost selection among equally near, equal-top-row candidates fits the inspected lessons but fails a lawful tie query.",
        "source_binding": source_binding, "racket": identity,
        "canonical_program": canonical, "rival_program": rival, "rival_program_sha256": sha(rival),
        "rival_edit": {"before": TIE_FRAGMENT, "after": RIVAL_FRAGMENT},
        "canonical_demonstrations": canonical_checks, "generated_demonstrations": generated,
        "query": {"origin": "authored; accepted by current self_check and observe_overrides; not a normal generator draw",
                  "input": query, "output": selected, "rival_output": alternative,
                  "self_check_errors": query_errors, "observed": observed,
                  "tie_motif": {"row": 8, "col": 8, "center": 2, "ring": 1},
                  "candidates": [{"gap": candidate["gap"], "box": candidate["box"], "size": candidate["size"]}
                                 for candidate in motif["candidates"]],
                  "changed_cells": changed},
        "counts": {"canonical_demonstrations": len(canonical_checks), "generated_demonstrations": len(generated),
                   "authored_queries": 1, "racket_evaluations": 2 * (len(canonical_checks) + len(generated) + 1),
                   "query_changed_cells": len(changed)},
        "limits": [
            "One named rival, the three original training demonstrations, and one normal seed-zero four-profile window were checked.",
            "The distinguishing query is authored inside the admitted structural grammar; no emitted ordinary-export query failure is claimed.",
            "No broad generator census, full battery, canonical source change, approval change, or training admission was performed.",
            "A potential teaching improvement is a lawful equal-distance tie control; that change remains a proposal.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], **report["counts"], "out": str(args.out)}, sort_keys=True))
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
