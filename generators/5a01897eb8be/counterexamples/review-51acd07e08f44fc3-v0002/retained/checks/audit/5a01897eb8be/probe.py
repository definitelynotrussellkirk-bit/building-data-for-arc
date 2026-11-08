"""Bounded, findings-only replay for audit 5a01897eb8be.

This probe imports only the audited generator's public generate/self_check
functions. Reference outputs are obtained separately with arcpuzzles apply.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "5a01897eb8be"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def first_seen_solid_rings(grid):
    """Rival: read only first-appearance color order; measure no shape."""
    background = grid[0][0]
    colors = list(dict.fromkeys(c for row in grid for c in row if c != background))
    side = 2 * len(colors) - 1
    return [[colors[min(r, c, side - r - 1, side - c - 1)]
             for c in range(side)] for r in range(side)]


def shape_info(grid):
    background = grid[0][0]
    colors = list(dict.fromkeys(c for row in grid for c in row if c != background))
    result = []
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        result.append({"color": color, "bbox": [r0, c0, r1, c1],
                       "bbox_max_dim": max(r1-r0+1, c1-c0+1), "cell_count": len(cells)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    repo, out = Path(args.repo).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = repo / "generators" / TASK_ID / "generator.py"
    sys.path.insert(0, str(repo / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_5a_source", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    cases = []
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(4):
            grid = generator.generate(0, sample_index, difficulty=difficulty)
            cases.append({"case_id": f"generated-{difficulty}-seed0-index{sample_index}",
                          "kind": "generated", "seed": 0, "sample_index": sample_index,
                          "difficulty": difficulty, "overrides": {}, "input": grid,
                          "domain": "Unmodified production generate() result."})

    base = cases[0]
    counterfactual = [[0 for _ in row] for row in base["input"]]
    # The base is a 6x16 grid with singleton color 7 and a size-3 L of color 9.
    # Repack exactly those two shapes on one shelf in ascending size order.
    infos = sorted(shape_info(base["input"]), key=lambda info: info["bbox_max_dim"])
    assert [info["bbox_max_dim"] for info in infos] == [1, 3]
    top = min(info["bbox"][0] for info in infos)
    left = min(info["bbox"][1] for info in infos)
    for info in infos:
        r0, c0, _, _ = info["bbox"]
        for r, row in enumerate(base["input"]):
            for c, value in enumerate(row):
                if value == info["color"]:
                    counterfactual[top+r-r0][left+c-c0] = value
        left += info["bbox_max_dim"] + 1
    cases.append({"case_id": "ascending-shelf-counterfactual", "kind": "counterfactual",
                  "seed": None, "sample_index": None, "difficulty": "easy", "overrides": None,
                  "derived_from": {"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": {}},
                  "construction": "Preserve source grid dimensions, background, colors, normalized shape cells and orientations; repack the singleton before the L on the same shelf with one-cell gaps.",
                  "input": counterfactual,
                  "domain": "Passes self_check and all stated INVARIANTS (zero top-left, singleton plus an L, distinct odd sizes {1,3}). Outside the production sampler's fixed descending-size shelf order. This is a reference-domain/structural-domain witness, not a sampled production input."})

    canonical_path = repo / "shared/data/canonical/puzzles.jsonl"
    selected = []
    for line in canonical_path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            selected.append(row)
    canonical = next(row for row in selected if row.get("source") == "training")
    for split in ("train", "test"):
        for index, pair in enumerate(canonical[split]):
            cases.append({"case_id": f"canonical-{split}-{index}", "kind": "canonical",
                          "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
                          "input": pair["input"], "canonical_output": pair["output"],
                          "domain": "Official training-source canonical pair; outside zero-background generator support."})

    for case in cases:
        case["self_check_errors"] = generator.self_check(case["input"], difficulty=case["difficulty"])
        case["input_sha256_compact_json"] = grid_hash(case["input"])
        case["shape_info_in_first_appearance_order"] = shape_info(case["input"])
        case["rival_output"] = first_seen_solid_rings(case["input"])
    rule = canonical["program_solution"]
    provenance = {"task_id": TASK_ID, "generator_version": generator.VERSION,
                  "generator_path": "repo/generators/5a01897eb8be/generator.py",
                  "generator_sha256": sha256(source), "generator_declared_rule_hash": generator.RULE_HASH,
                  "canonical_file_sha256": sha256(canonical_path),
                  "canonical_program_sha256_utf8": hashlib.sha256(rule.encode()).hexdigest(),
                  "canonical_row_sources": [row.get("source") for row in selected],
                  "distinct_canonical_programs": len({row["program_solution"] for row in selected}),
                  "probe_sha256": sha256(Path(__file__)), "cases": cases}
    (out / "input.json").write_text(json.dumps([case["input"] for case in cases], indent=2) + "\n")
    (out / "probe.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"task_id": TASK_ID, "generator_sha256": provenance["generator_sha256"],
                      "declared_rule_hash": generator.RULE_HASH, "generated_cases": 12,
                      "counterfactual_cases": 1, "canonical_cases": 4,
                      "generated_selfcheck_passes": sum(not case["self_check_errors"] for case in cases if case["kind"] == "generated"),
                      "counterfactual_selfcheck_errors": cases[12]["self_check_errors"],
                      "canonical_selfcheck_rejections": sum(bool(case["self_check_errors"]) for case in cases if case["kind"] == "canonical")}, indent=2))


if __name__ == "__main__":
    main()
