"""Source-bound adversarial probe for c9c600cd5283 (audit only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "c9c600cd5283"
BANDS = ("easy", "medium", "hard")
PER_BAND = 100


def intended(grid):
    out = [row[:] for row in grid]
    h = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[h - 1 - r][c] = value
    return out


def upper_only(grid):
    out = [row[:] for row in grid]
    h = len(grid)
    for r in range(h // 2):
        for c, value in enumerate(grid[r]):
            if value:
                out[h - 1 - r][c] = value
    return out


def digest_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main():
    repo = Path.cwd().resolve()
    gen, source, source_sha = load_selected_generator(TASK_ID, root=repo)
    pairs = canonical_pairs(TASK_ID, root=repo, labeled_only=True)
    canonical = []
    for pair in pairs:
        expected = intended(pair["input"])
        rival = upper_only(pair["input"])
        canonical.append({
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "intended_matches_label": expected == pair["output"],
            "rival_matches_label": rival == pair["output"],
            "rival_disagrees": rival != expected,
            "self_check_errors": gen.self_check(pair["input"]),
        })

    band_results = {}
    unique = set()
    witness = None
    for band_i, band in enumerate(BANDS):
        only_upper = 0
        rival_equivalent = 0
        lawful = 0
        for i in range(PER_BAND):
            seed = 400000 + band_i * 10000 + i
            sample_index = i
            grid = gen.generate(seed, sample_index, difficulty=band)
            unique.add(digest_grid(grid))
            errors = gen.self_check(grid)
            lawful += not errors
            cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
            is_upper = bool(cells) and all(r < len(grid) // 2 for r, _ in cells)
            only_upper += is_upper
            equivalent = intended(grid) == upper_only(grid)
            rival_equivalent += equivalent
            if witness is None:
                witness = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": band,
                    "input": grid,
                    "self_check_errors": errors,
                    "only_upper_sources": is_upper,
                    "rival_equals_intended": equivalent,
                }
        band_results[band] = {
            "requested": PER_BAND,
            "lawful": lawful,
            "only_upper_sources": only_upper,
            "upper_only_rival_equals_intended": rival_equivalent,
        }

    first = pairs[0]
    out_dir = Path(__file__).resolve().parent
    (out_dir / "input.json").write_text(json.dumps(first["input"], indent=2) + "\n")
    (out_dir / "rival.json").write_text(json.dumps(upper_only(first["input"]), indent=2) + "\n")
    report = {
        "schema": "audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha,
        "canonical_pairs": canonical,
        "sample_recipe": "100 draws per band; seed=400000+band_index*10000+i, sample_index=i",
        "bands": band_results,
        "total_draws": len(BANDS) * PER_BAND,
        "unique_inputs": len(unique),
        "first_generated_witness": witness,
        "finding": "The generator and self_check admit only strict-upper source cells, so upper_only reflection is observationally identical on generated support even though it disagrees with every canonical pair.",
    }
    (out_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
