"""Focused findings-only authoring probe; run through the packet wrapper."""
import hashlib
import importlib.util
import json
from pathlib import Path
from collections import Counter
from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, find_root

HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
TASK = "c1f63ca7d07b"
row = Catalog(ROOT).describe(TASK)
source = ROOT / row["generator"]
spec = importlib.util.spec_from_file_location("audited_generator", source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def seeds(grid):
    h, w = len(grid), len(grid[0])
    result = []
    for r, line in enumerate(grid):
        for c, value in enumerate(line):
            if value:
                distances = [r, h - r - 1, c, w - c - 1]
                result.append({"row": r, "column": c, "color": value,
                               "distances": distances, "ties": distances.count(min(distances))})
    return result


pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical = []
for pair in pairs:
    canonical.append({"split": pair["split"], "pair_index": pair["pair_index"],
                      "self_check": gen.self_check(pair["input"]), "seeds": seeds(pair["input"])})
tie_pair = next(pair for pair in pairs if any(seed["ties"] > 1 for seed in seeds(pair["input"])))
fixture = gen.generate(0, 0, texture="equidistant_borders")
totals = []
for difficulty in (None, "easy", "medium", "hard"):
    counts = Counter()
    hashes = set()
    first_bad = None
    for index in range(40):
        grid = gen.generate(2300 + index, index, difficulty=difficulty)
        hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        errors = gen.self_check(grid)
        counts["draws"] += 1
        counts["validator_pass"] += not errors
        counts["draws_with_tied_seed"] += any(seed["ties"] > 1 for seed in seeds(grid))
        if errors and first_bad is None:
            first_bad = {"seed": 2300 + index, "sample_index": index, "errors": errors, "input": grid}
    totals.append({"difficulty": difficulty, **counts, "unique_inputs": len(hashes), "first_bad": first_bad})

report = {"task_id": TASK, "generator_version": gen.VERSION,
          "generator_sha256": row["generator_sha256"], "rule_hash": row["rule_hash"],
          "source_path": row["generator"], "review_index_exists": (source.parent / "evidence/review_index.json").exists(),
          "canonical": canonical, "production_scope": {"seeds": "2300..2339", "sample_indices": "0..39", "overrides": {}, "per_band": totals},
          "cases": [
              {"kind": "canonical", "variant": tie_pair["variant"], "split": tie_pair["split"],
               "pair_index": tie_pair["pair_index"], "seed": None, "sample_index": None, "overrides": None,
               "input": tie_pair["input"], "expected_canonical_output": tie_pair["output"],
               "self_check": gen.self_check(tie_pair["input"]),
               "documented_generator_domain": "excluded because generator requires unique nearest border; nevertheless retained canonical input"},
              {"kind": "mislabelled_degenerate", "seed": 0, "sample_index": 0,
               "overrides": {"texture": "equidistant_borders"}, "input": fixture,
               "fixture_seeds": seeds(fixture), "self_check": gen.self_check(fixture),
               "intended_degenerate_rival_output": fixture,
               "documented_generator_domain": "explicit declared negative texture, not ordinary production"}],
          "command": ["python3", "review.py", "run", "python3", "../checks/audit/c1f63ca7d07b/probe.py"],
          "cwd": "packet_root", "runtime_cwd": "WORK/repo", "exit_code": 0}
(HERE / "input.json").write_text(json.dumps([tie_pair["input"], fixture]) + "\n")
(HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"generator_sha256": report["generator_sha256"], "rule_hash": report["rule_hash"],
                  "canonical_acceptance": sum(not pair["self_check"] for pair in canonical),
                  "canonical_total": len(canonical), "production": totals}))
