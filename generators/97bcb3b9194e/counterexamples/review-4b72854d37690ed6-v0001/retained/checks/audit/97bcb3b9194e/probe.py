from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "97bcb3b9194e"
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


def canonical_color_only_rival(gen, grid):
    records, errors = gen._component_records(grid)
    assert not errors
    counts = []
    for record in records:
        counts.append(sum(grid[r][c] in (4, 6) for r, c in record["cells"]))
    best = records[counts.index(min(counts))]
    r1, c1, r2, c2 = best["bbox"]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


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
    grid = [[0] * 11 for _ in range(12)]
    for row in range(1, 4):
        for col in range(1, 4):
            grid[row][col] = 1
        for col in range(6, 9):
            grid[row][col] = 1
    grid[1][1] = 4
    grid[1][6] = 2
    grid[1][7] = 2

    intended = gen.rule_mirror(grid)
    rival = canonical_color_only_rival(gen, grid)
    assert gen.self_check(grid) == []
    assert intended != rival

    canonical = canonical_pairs()
    canonical_matches = sum(canonical_color_only_rival(gen, pair["input"]) == pair["output"] for pair in canonical)
    canonical_mark_colors = sorted({
        value
        for pair in canonical
        for row in pair["input"]
        for value in row
        if value not in (0, 1)
    })

    generated_matches = 0
    generated_mark_colors = set()
    samples = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(200):
            generated = gen.generate(800_000 + band_index * 10_000 + index, index, difficulty=band)
            generated_mark_colors.update(
                value for row in generated for value in row if value not in (0, 1)
            )
            generated_matches += canonical_color_only_rival(gen, generated) == gen.rule_mirror(generated)
            samples += 1

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (OUT / "python-intended.json").write_text(json.dumps(intended, indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    finding = {
        "schema": "arcpuzzles-audit-finding-v1",
        "task_id": TASK,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "rival": "count only canonical mark colors 4 and 6, then crop the minimum-count rectangle",
        "canonical_pair_appearances_checked": len(canonical),
        "canonical_pair_appearances_matched": canonical_matches,
        "canonical_mark_colors": canonical_mark_colors,
        "production_samples_checked": samples,
        "production_samples_matched": generated_matches,
        "production_mark_colors": sorted(generated_mark_colors),
        "witness_self_check": gen.self_check(grid),
        "witness_intended_differs_from_rival": intended != rival,
        "witness_differing_shape": [len(intended), len(intended[0]), len(rival), len(rival[0])],
        "domain": "self_check-accepted 12x11 scene with one color-4 mark versus two color-2 marks",
        "limits": "Finite canonical and 600-sample production check; source palette declaration limits emitted marks to colors 4 and 6.",
    }
    (OUT / "finding.json").write_text(json.dumps(finding, indent=2) + "\n")
    print(json.dumps(finding, indent=2))


if __name__ == "__main__":
    main()
