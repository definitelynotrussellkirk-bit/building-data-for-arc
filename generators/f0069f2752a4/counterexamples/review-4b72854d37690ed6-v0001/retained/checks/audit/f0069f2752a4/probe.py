from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "f0069f2752a4"
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
OUT = ROOT / "checks" / "audit" / TASK


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def size_capped_rival(gen, grid):
    info = gen._analysis(grid)
    output = [[0 for _ in row] for row in grid]
    for component in info["border"]:
        if len(component["cells"]) <= 5:
            for row, col in component["cells"]:
                output[row][col] = component["color"]
    return output


def canonical_pairs():
    result = []
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            result.extend(row.get("train", []))
            result.extend(row.get("test", []))
    return result


def main():
    gen = load_generator()
    grid = [[0] * 8 for _ in range(8)]
    for row in (0, 1):
        for col in (0, 1, 2):
            grid[row][col] = 2
    grid[4][4] = 4

    intended = gen.rule_mirror(grid)
    rival = size_capped_rival(gen, grid)
    assert gen.self_check(grid) == []
    assert intended != rival

    canonical = canonical_pairs()
    canonical_matches = sum(
        size_capped_rival(gen, pair["input"]) == gen.rule_mirror(pair["input"])
        for pair in canonical
    )
    canonical_max_survivor = max(
        len(component["cells"])
        for pair in canonical
        for component in gen._analysis(pair["input"])["border"]
    )

    sampled = []
    generated_matches = 0
    generated_max_survivor = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(200):
            generated = gen.generate(700_000 + band_index * 10_000 + index, index, difficulty=band)
            info = gen._analysis(generated)
            generated_max_survivor = max(
                generated_max_survivor,
                max(len(component["cells"]) for component in info["border"]),
            )
            generated_matches += size_capped_rival(gen, generated) == gen.rule_mirror(generated)
            sampled.append((band, index))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (OUT / "python-intended.json").write_text(json.dumps(intended, indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    finding = {
        "schema": "arcpuzzles-audit-finding-v1",
        "task_id": TASK,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "rival": "preserve border-touching components only when size <= 5",
        "canonical_pairs_checked": len(canonical),
        "canonical_pairs_matched": canonical_matches,
        "canonical_max_survivor_cells": canonical_max_survivor,
        "production_samples_checked": len(sampled),
        "production_samples_matched": generated_matches,
        "production_max_survivor_cells": generated_max_survivor,
        "witness_self_check": gen.self_check(grid),
        "witness_intended_differs_from_rival": intended != rival,
        "witness_differing_cells": sum(
            a != b for row_a, row_b in zip(intended, rival) for a, b in zip(row_a, row_b)
        ),
        "domain": "self_check-accepted 8x8 scene with a six-cell border component and one interior singleton",
        "limits": "Finite canonical and 600-sample production check; source inspection establishes the sampler shape bank has at most five cells.",
    }
    (OUT / "finding.json").write_text(json.dumps(finding, indent=2) + "\n")
    print(json.dumps(finding, indent=2))


if __name__ == "__main__":
    main()
