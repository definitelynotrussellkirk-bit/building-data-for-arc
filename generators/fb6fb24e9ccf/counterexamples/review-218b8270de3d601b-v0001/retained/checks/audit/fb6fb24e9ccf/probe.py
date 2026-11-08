"""Read-only targeted audit. Run from packet/repo with the packet interpreter."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
REPO = Path.cwd()
OUT = REPO.parent / "checks/audit/fb6fb24e9ccf"
TASK_ID = "fb6fb24e9ccf"
SOURCE = REPO / f"generators/{TASK_ID}/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audited_generator", SOURCE)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def crop_all(grid):
    cells = [(r, c) for r, row in enumerate(grid)
             for c, color in enumerate(row) if color != 0]
    if not cells:
        return [[0]]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def rival_outer_rows(grid):
    """Infer width solely from first and last occupied rows; copy their span."""
    occupied_rows = [r for r, row in enumerate(grid) if any(row)]
    if not occupied_rows:
        return [[0]]
    r0, r1 = occupied_rows[0], occupied_rows[-1]
    cols = [c for r in (r0, r1) for c, value in enumerate(grid[r]) if value]
    return [row[min(cols):max(cols) + 1] for row in grid[r0:r1 + 1]]


row = next(json.loads(line)
           for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
           if json.loads(line).get("task_id") == TASK_ID)
pairs = row["train"] + row["test"]
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
normalized = " ".join(row["program_solution"].split())
rule_sha = hashlib.sha256(normalized.encode()).hexdigest()
assert source_sha == "a78d9746fa2deeb15c0ac01a8b039686d9afa46a6cb158e7a4c4b71d28f337d9"
assert rule_sha[:12] == generator.RULE_HASH == "debb1a8a129a"

# A connected plus, with all bbox corners zero. This is accepted by the
# validator and lies within every advertised numerical axis range.
witness = [[0] * 7 for _ in range(7)]
for r, c in ((2, 3), (3, 2), (3, 3), (3, 4), (4, 3)):
    witness[r][c] = 2
dump("input.json", witness)

canonical = []
for index, pair in enumerate(pairs):
    canonical.append({
        "pair_index": index,
        "split": "train" if index < len(row["train"]) else "test",
        "validator_errors": generator.self_check(pair["input"]),
        "python_crop_matches_recorded_output": crop_all(pair["input"]) == pair["output"],
        "rival_matches_recorded_output": rival_outer_rows(pair["input"]) == pair["output"],
    })

bands = []
selected = []
for band in ("easy", "medium", "hard"):
    grids = []
    valid = 0
    matches = 0
    for seed in range(25):
        for index in range(4):
            grid = generator.generate(seed, index, difficulty=band)
            grids.append(json.dumps(grid, separators=(",", ":")))
            valid += not generator.self_check(grid, difficulty=band)
            matches += rival_outer_rows(grid) == crop_all(grid)
            if seed == 0:
                selected.append({"seed": seed, "sample_index": index,
                                 "difficulty": band, "overrides": {}, "input": grid})
    bands.append({"band": band, "seed_range_inclusive": [0, 24],
                  "sample_index_range_inclusive": [0, 3], "overrides": {},
                  "draw_count": len(grids), "unique_inputs": len(set(grids)),
                  "validator_passes": valid, "rival_matches_python_crop": matches})

dump("selected_inputs.json", [item["input"] for item in selected] + [pair["input"] for pair in pairs])
result = {
    "task_id": TASK_ID,
    "generator_sha256": source_sha,
    "canonical_record_path": "repo/shared/data/canonical/puzzles.jsonl",
    "canonical_record_sha256": hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    "normalized_rule_sha256": rule_sha,
    "normalized_rule_hash": rule_sha[:12],
    "source_version": generator.VERSION,
    "finding": "Generated crops always permit inferring width from only the first and last occupied rows.",
    "rival_definition": "rival_outer_rows in probe.py",
    "canonical_results": canonical,
    "canonical_rival_matches": sum(x["rival_matches_recorded_output"] for x in canonical),
    "canonical_pair_count": len(canonical),
    "canonical_shortcut_claim": False,
    "declared_canonical_shortcuts": list(getattr(generator, "CANONICAL_SHORTCUTS", [])),
    "declared_lesson_competitors": list(getattr(generator, "LESSON_COMPETITORS", [])),
    "sample_results": bands,
    "selected_racket_input_order": [{k: v for k, v in item.items() if k != "input"}
                                    for item in selected] + [{"canonical_pair_index": i}
                                                            for i in range(len(pairs))],
    "sampler": "direct generator.generate(seed, sample_index, difficulty=band); 25 consecutive four-example windows per band; no production Catalog.generate or broad battery",
    "comparison_authority": "Sample census uses independently written crop_all; selected 12 generated inputs and all 5 canonical pairs are submitted separately to supported apply.",
    "witness": {"origin": "handmade", "seed": None, "sample_index": None,
                "overrides": None, "input": witness,
                "validator_errors": generator.self_check(witness),
                "validator_pass": not generator.self_check(witness),
                "observed_axes": generator.observe_overrides(witness),
                "in_documented_numerical_and_invariant_domain": True,
                "in_normal_generator_support": False,
                "python_expected_output": crop_all(witness),
                "rival_output": rival_outer_rows(witness)},
    "source_unchanged": hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha,
}
if "--finalize" in sys.argv:
    actual = json.loads((OUT / "racket.json").read_text())
    reference_batch = json.loads((OUT / "selected_racket.json").read_text())
    for receipt in (actual, reference_batch):
        assert receipt["generator_sha256"] == source_sha
        assert receipt["executed_rule_hash"] == generator.RULE_HASH
        assert receipt["rule_hash_matches_catalog"]
        assert all(r["valid_output"] and r["error"] is None for r in receipt["results"])
    assert actual["results"][0]["input"] == witness
    assert actual["results"][0]["output"] == crop_all(witness)
    assert actual["results"][0]["output"] != rival_outer_rows(witness)
    expected_inputs = [x["input"] for x in selected] + [p["input"] for p in pairs]
    assert len(reference_batch["results"]) == len(expected_inputs)
    for grid, applied in zip(expected_inputs, reference_batch["results"], strict=True):
        assert grid == applied["input"]
        assert applied["output"] == crop_all(grid)
    result["witness"]["actual_racket_output"] = actual["results"][0]["output"]
    result["witness"]["racket_output_differs_from_rival"] = True
    result["racket_crosscheck"] = {
        "witness_count": 1, "witness_reference_matches_python": 1,
        "generated_count": len(selected),
        "generated_reference_matches_python": len(selected),
        "generated_reference_matches_rival": sum(
            r["output"] == rival_outer_rows(r["input"])
            for r in reference_batch["results"][:len(selected)]),
        "canonical_count": len(pairs),
        "canonical_reference_matches_recorded_output": sum(
            r["output"] == p["output"]
            for p, r in zip(pairs, reference_batch["results"][len(selected):], strict=True)),
    }
dump("probe.json", result)
print(json.dumps({"source_sha256": source_sha, "rule_hash": rule_sha[:12],
                  "bands": bands, "canonical_rival_matches": result["canonical_rival_matches"],
                  "witness_validator_errors": result["witness"]["validator_errors"]}))
