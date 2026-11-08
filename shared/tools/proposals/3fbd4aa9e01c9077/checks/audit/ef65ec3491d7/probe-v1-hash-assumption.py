"""Bounded, findings-only audit of the selected ef65ec3491d7 source.

Run through the packet wrapper. Preparation records 5 canonical inputs and
30 normal generated inputs. Use public arcpuzzles apply to label inputs.json,
then run this script with 'analyze'. No selected source is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
)

TASK_ID = "ef65ec3491d7"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def nonwall_regions(grid):
    """4-connected non-cyan components, independent of generator helpers."""
    height, width = len(grid), len(grid[0])
    seen = set()
    regions = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 8 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r + dr, c + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] != 8):
                        seen.add(nxt)
                        stack.append(nxt)
            cells.sort()
            regions.append({"cells": cells,
                            "seeds": [(r, c, grid[r][c]) for r, c in cells
                                      if grid[r][c] != 0]})
    return regions


def first_seed_wins(grid):
    """Preserve original seeds; fill zeros with the first seed in each chamber.

    This deliberately specified rival differs from the selected reference
    when differently colored seeds share one chamber. It is not submitted as
    a solve or claimed to be the correct rule.
    """
    output = [row[:] for row in grid]
    for region in nonwall_regions(grid):
        if not region["seeds"]:
            continue
        color = region["seeds"][0][2]
        for row, col in region["cells"]:
            if grid[row][col] == 0:
                output[row][col] = color
    return output


def prepare():
    module, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    rows = []
    with canonical_path(ROOT).open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    program = programs.pop()
    inputs = []
    cases = []

    def add(case_id, grid, **metadata):
        regions = nonwall_regions(grid)
        case = {"case_id": case_id, "input_index": len(inputs),
                "input_sha256": digest(grid),
                "self_check_errors": module.self_check(grid),
                "max_seeds_in_nonwall_region": max(len(r["seeds"]) for r in regions),
                "seed_colors": sorted({cell for row in grid for cell in row
                                       if cell not in (0, 8)}),
                **metadata}
        inputs.append(grid)
        cases.append(case)

    for pair in pairs:
        add(f"canonical.v{pair['variant']}.{pair['split']}.{pair['pair_index']}",
            pair["input"], origin="canonical", variant=pair["variant"],
            split=pair["split"], pair_index=pair["pair_index"],
            canonical_output=pair["output"], seed=None, sample_index=None, overrides=None)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(10):
            seed = 42_000 + band_index
            grid = module.generate(seed, sample_index, difficulty=band)
            add(f"generated.{band}.{sample_index}", grid, origin="generated",
                seed=seed, sample_index=sample_index, difficulty=band, overrides={})

    anchor = next(case for case in cases
                  if case["origin"] == "generated" and len(case["seed_colors"]) >= 2)
    anchor_grid = inputs[anchor["input_index"]]
    override_probes = []
    for overrides in ({"palette_kind": "warm"}, {"palette_kind": "cool"},
                      {"palette_size": 1}, {"palette_size": 8},
                      {"texture": "warm"}, {"texture": "cool"}):
        grid = module.generate(anchor["seed"], anchor["sample_index"],
                               difficulty=anchor["difficulty"], **overrides)
        override_probes.append({"seed": anchor["seed"],
                                "sample_index": anchor["sample_index"],
                                "difficulty": anchor["difficulty"],
                                "overrides": overrides,
                                "input_sha256": digest(grid),
                                "identical_to_unoverridden_input": grid == anchor_grid,
                                "reference_case_id": anchor["case_id"],
                                "self_check_errors": module.self_check(grid),
                                "realized_seed_color_count": len({cell for row in grid for cell in row
                                                                   if cell not in (0, 8)})})
    report = {"task_id": TASK_ID, "generator_source": str(source),
              "generator_sha256": source_sha, "generator_version": module.VERSION,
              "rule_normalized_sha256": hashlib.sha256(" ".join(program.split()).encode()).hexdigest(),
              "rule_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "canonical_row_count": len(rows), "cases": cases,
              "override_probes": override_probes,
              "lesson_contract_declared": hasattr(module, "LESSON_COMPETITORS"),
              "scope": "All 5 canonical pairs; 30 generated inputs (10 indices per difficulty, 3 fixed seeds); six override calls at one fixed generated input; one deliberate rival."}
    (OUT / "inputs.json").write_text(json.dumps(inputs, separators=(",", ":")) + "\n")
    (OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"inputs": len(inputs), "generated": sum(c["origin"] == "generated" for c in cases),
                      "canonical_multi_seed_cases": [c["case_id"] for c in cases
                                                     if c["origin"] == "canonical" and c["max_seeds_in_nonwall_region"] > 1],
                      "generator_sha256": source_sha,
                      "override_probes": override_probes}, indent=2))


def analyze():
    report = json.loads((OUT / "probe.json").read_text())
    inputs = json.loads((OUT / "inputs.json").read_text())
    applied = json.loads((OUT / "racket.json").read_text())
    assert applied["generator_sha256"] == report["generator_sha256"]
    assert applied["rule_hash_matches_catalog"] is True
    assert applied["executed_rule_hash"] == report["rule_normalized_sha256"]
    assert len(applied["results"]) == len(inputs) == len(report["cases"])
    comparisons = []
    witnesses = []
    for case, grid, actual in zip(report["cases"], inputs, applied["results"], strict=True):
        assert actual["input_sha256"] == case["input_sha256"] == digest(grid)
        assert not actual["error"], actual
        rival = first_seed_wins(grid)
        output = actual["output"]
        diffs = [[r, c] for r in range(len(output)) for c in range(len(output[0]))
                 if output[r][c] != rival[r][c]]
        comparison = {"case_id": case["case_id"], "origin": case["origin"],
                      "rival_matches_racket": not diffs, "difference_count": len(diffs),
                      "max_seeds_in_nonwall_region": case["max_seeds_in_nonwall_region"],
                      "self_check_errors": case["self_check_errors"],
                      "rival_output_sha256": digest(rival), "racket_output_sha256": digest(output)}
        if case["origin"] == "canonical":
            comparison["racket_matches_canonical_output"] = output == case["canonical_output"]
        comparisons.append(comparison)
        if diffs:
            witnesses.append({"finding_id": "A-ef65-1", **case, "input": grid,
                              "actual_racket_output": output, "rival_output": rival,
                              "difference_coordinates_zero_based": diffs,
                              "nonwall_regions_with_multiple_seeds": [r for r in nonwall_regions(grid)
                                                                      if len(r["seeds"]) > 1]})
    natural = [c for c in comparisons if c["origin"] == "generated"]
    canonical = [c for c in comparisons if c["origin"] == "canonical"]
    result = {"task_id": TASK_ID, "generator_sha256": report["generator_sha256"],
              "generator_version": report["generator_version"],
              "executed_rule_hash": applied["executed_rule_hash"],
              "rule_text_sha256": applied["rule_text_sha256"],
              "racket_command": applied["command"], "racket_cwd": applied["cwd"],
              "scope": report["scope"],
              "summary": {"canonical_racket_parity": sum(c["racket_matches_canonical_output"] for c in canonical),
                          "canonical_count": len(canonical),
                          "canonical_rival_agreements": sum(c["rival_matches_racket"] for c in canonical),
                          "generated_rival_agreements": sum(c["rival_matches_racket"] for c in natural),
                          "generated_count": len(natural),
                          "generated_validator_accepted": sum(not c["self_check_errors"] for c in natural),
                          "generated_multiple_seed_regions": sum(c["max_seeds_in_nonwall_region"] > 1 for c in natural),
                          "override_identical_input_count": sum(c["identical_to_unoverridden_input"] for c in report["override_probes"]),
                          "override_probe_count": len(report["override_probes"])},
              "comparisons": comparisons, "witnesses": witnesses,
              "override_probes": report["override_probes"],
              "limitations": ["This is a finite sample against one explicit rival, not an exhaustive identifiability claim.",
                              "Normal generation was inspected; degenerate textures and the full battery were not audited.",
                              "The canonical multi-seed witness is accepted by self_check but outside the normal generator's documented one-seed-per-room subdomain.",
                              "The audit does not modify or approve the selected source."]}
    (OUT / "findings.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"summary": result["summary"], "witnesses": [
        {"case_id": w["case_id"], "differences": len(w["difference_coordinates_zero_based"]),
         "self_check_errors": w["self_check_errors"]} for w in witnesses],
        "executed_rule_hash": applied["executed_rule_hash"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "analyze"))
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else analyze()
