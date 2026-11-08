"""Small read-only, source-bound audit of the selected 9ce2dcf587b8 generator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
ROOT = WORK / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "9ce2dcf587b8"
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def rays(grid, limit=None):
    """Independent mirror of the unchanged four-diagonal Racket authority."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    markers = [(r, c, value) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value]
    for r, c, value in markers if limit is None else markers[:limit]:
        for dr, dc in DIRECTIONS:
            for distance in range(1, max(h, w)):
                rr, cc = r + dr * distance, c + dc * distance
                if (0 <= rr < h and 0 <= cc < w
                        and grid[rr][cc] == 0 and out[rr][cc] == 0):
                    out[rr][cc] = value
    return out


def color_quota_rival(grid):
    color = next(value for row in grid for value in row if value)
    return rays(grid, 1 + (color - 1) % 3)


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in ledger.read_text().splitlines()
            if json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    rule = rows[0]["program_solution"]
    pairs = canonical_pairs(TASK, root=ROOT)
    canonical_score = []
    for pair in pairs:
        grid = pair["input"]
        canonical_score.append({
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"],
            "height": len(grid), "width": len(grid[0]),
            "markers": [(r, c, value) for r, row in enumerate(grid)
                        for c, value in enumerate(row) if value],
            "self_check_errors": GEN.self_check(grid),
            "independent_mirror_matches_recorded_label": rays(grid) == pair["output"],
            "color_quota_matches_recorded_label": color_quota_rival(grid) == pair["output"],
            "declared_shortcut_matches": {
                name: rival(grid) == pair["output"]
                for name, rival in GEN.CANONICAL_SHORTCUTS.items()},
        })

    default_census = []
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(27):
            seed = 810000 + sample_index
            grid = GEN.generate(seed, sample_index, difficulty=difficulty)
            observed = GEN.observe_overrides(grid)
            default_census.append({
                "seed": seed, "sample_index": sample_index,
                "difficulty": difficulty, "observed": observed,
                "self_check_errors": GEN.self_check(grid),
                "color_quota_matches_mirror": color_quota_rival(grid) == rays(grid),
            })

    override_census = []
    for color in range(1, 10):
        for count in range(1, 4):
            overrides = {"grid_h": 7, "grid_w": 7, "fgc": color, "n_dots": count}
            grid = GEN.generate(4242, 0, difficulty="easy", **overrides)
            override_census.append({
                "seed": 4242, "sample_index": 0, "difficulty": "easy",
                "overrides": overrides, "observed": GEN.observe_overrides(grid),
                "self_check_errors": GEN.self_check(grid),
                "color_quota_matches_mirror": color_quota_rival(grid) == rays(grid),
            })

    overrides = {"grid_h": 7, "grid_w": 7, "fgc": 1, "n_dots": 3}
    grid = GEN.generate(4242, 0, difficulty="easy", **overrides)
    rival = color_quota_rival(grid)
    mirror = rays(grid)
    witness = {
        "seed": 4242, "sample_index": 0, "difficulty": "easy",
        "overrides": overrides,
        "input_origin": "direct selected-generator call with exact advertised overrides",
        "in_documented_generator_domain": True,
        "is_validator_invalid_mutation": False,
        "occurs_under_unoverridden_schedule": False,
        "observed": GEN.observe_overrides(grid),
        "self_check_errors": GEN.self_check(grid),
        "rival": "color_quota_first_markers",
        "mirror_rival_differing_cells": sum(a != b for ra, rb in zip(mirror, rival)
                                            for a, b in zip(ra, rb)),
        "fresh_racket_status": "pending serialized apply by parent",
    }
    save("input.json", grid)
    save("rival_output.json", rival)
    report = {
        "schema": "task-bound-small-audit-v1", "task_id": TASK,
        "generator_path": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA,
        "rule_source": "shared/data/canonical/puzzles.jsonl:361:program_solution",
        "rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "declared_rule_hash": GEN.RULE_HASH,
        "canonical_pair_count": len(pairs),
        "canonical_score": canonical_score,
        "default_population": {"sample_indexes": [0, 26], "seed_formula": "810000 + sample_index",
                               "difficulties": [None, "easy", "medium", "hard"]},
        "default_draws": len(default_census),
        "default_rival_matches_mirror": sum(row["color_quota_matches_mirror"] for row in default_census),
        "default_validator_rejections": sum(bool(row["self_check_errors"]) for row in default_census),
        "default_census": default_census,
        "override_cases": len(override_census),
        "override_exact_matches": sum(row["observed"] == row["overrides"] for row in override_census),
        "override_validator_rejections": sum(bool(row["self_check_errors"]) for row in override_census),
        "override_census": override_census,
        "witness": witness,
    }
    racket_path = HERE / "racket.json"
    if racket_path.exists():
        racket = json.loads(racket_path.read_text())
        assert racket["task_id"] == TASK
        assert racket["generator_sha256"] == SOURCE_SHA
        assert racket["executed_rule_hash"] == GEN.RULE_HASH
        assert racket["rule_hash_matches_catalog"] is True
        assert len(racket["results"]) == 1
        result = racket["results"][0]
        assert result["input"] == grid
        assert result["valid_output"] is True and result["error"] is None
        authoritative = result["output"]
        differing = [(r, c) for r, row in enumerate(authoritative)
                     for c, value in enumerate(row) if value != rival[r][c]]
        assert authoritative == mirror
        assert len(differing) == 10
        witness.update({
            "fresh_racket_status": "verified against fresh supported public apply result",
            "racket_matches_independent_mirror": True,
            "racket_rival_differing_cells": len(differing),
            "racket_rival_differing_positions": differing,
        })
        report["fresh_racket"] = {
            "artifact": "racket.json",
            "artifact_sha256": hashlib.sha256(racket_path.read_bytes()).hexdigest(),
            "generator_sha256": racket["generator_sha256"],
            "executed_rule_hash": racket["executed_rule_hash"],
            "executed_callable_text_sha256": racket["rule_text_sha256"],
            "input_sha256": result["input_sha256"],
            "output_sha256": result["output_sha256"],
            "valid_output": result["valid_output"],
        }
    save("probe.json", report)
    print(json.dumps({
        "generator_sha256": SOURCE_SHA,
        "rule_sha256": report["rule_sha256"],
        "canonical_pair_count": len(pairs),
        "declared_shortcut_mismatch_counts": {
            name: sum(not row["declared_shortcut_matches"][name] for row in canonical_score)
            for name in GEN.CANONICAL_SHORTCUTS},
        "color_quota_canonical_matches": sum(row["color_quota_matches_recorded_label"] for row in canonical_score),
        "default_rival_matches_mirror": report["default_rival_matches_mirror"],
        "default_draws": report["default_draws"],
        "override_exact_matches": report["override_exact_matches"],
        "override_cases": report["override_cases"],
        "witness": witness,
    }, indent=2))


if __name__ == "__main__":
    main()
