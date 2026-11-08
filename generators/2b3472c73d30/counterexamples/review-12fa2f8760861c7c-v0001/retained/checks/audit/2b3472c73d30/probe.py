"""Bounded findings-only probe; run through WORK/run_with_racket.py.

This reads the selected generator and canonical row. It writes only beside
itself, and never edits the audited generator or its hooks.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
TASK = "2b3472c73d30"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def intended(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for color in set(row) - {0}:
            cols = [c for c, v in enumerate(row) if v == color]
            if len(cols) == 2:
                left, right = cols
                if all(v == 0 for v in row[left + 1:right]):
                    out[r][left:right + 1] = [color] * (right - left + 1)
    return out


def rival_skip_row_with_nonpair_color(grid):
    """Wrong rule: a singleton/triple anywhere vetoes the whole row."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        counts = Counter(v for v in row if v != 0)
        if any(count != 2 for count in counts.values()):
            continue
        out[r] = intended([row])[0]
    return out


def load_module():
    source = ROOT / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_row_bridge", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return source, module


def prepare():
    from arcpuzzles import Catalog

    source, module = load_module()
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = [line for line in ledger.read_text().splitlines(keepends=True)
            if json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    row = json.loads(rows[0])
    (HERE / "canonical.jsonl").write_text(rows[0])
    index = source.parent / "evidence/review_index.json"
    metadata = {
        "task_id": TASK,
        "generator_path": str(source),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": module.VERSION,
        "declared_rule_hash": module.RULE_HASH,
        "canonical_ledger_path": str(ledger),
        "canonical_row_sha256_including_newline": hashlib.sha256(rows[0].encode()).hexdigest(),
        "canonical_program_sha256_exact_unwrapped": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "canonical_program_normalized_hash": hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12],
        "review_index_path": str(index),
        "review_index_present": index.exists(),
        "scope": "Findings-only support/teaching audit; no source edits and no battery.",
    }
    write("source_metadata.json", metadata)
    write("catalog_description.json", Catalog(ROOT).describe(TASK))
    if index.exists():
        (HERE / "review_index.json").write_bytes(index.read_bytes())
    lines = source.read_text().splitlines()
    excerpts = []
    for first, last in ((127, 171), (264, 285), (335, 403)):
        excerpts.extend(f"{n}: {lines[n - 1]}" for n in range(first, min(last, len(lines)) + 1))
        excerpts.append("")
    (HERE / "source_excerpts.txt").write_text("\n".join(excerpts) + "\n")

    minimal = [
        [1, 0, 1, 0, 2, 0, 0],
        [3, 0, 3, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    padded = [r + [0, 0] for r in minimal] + [[0] * 9]
    write("input.json", minimal)
    records = []
    for name, grid in (("minimal_5x7", minimal), ("same_defect_at_generated_easy_shape_6x9", padded)):
        analysis = module._analyze(grid)
        assert analysis["errors"] == []
        assert module.rule_mirror(grid) == intended(grid)
        assert rival_skip_row_with_nonpair_color(grid) != intended(grid)
        records.append({"name": name, "kind": "witness", "input": grid,
                        "self_check": module.self_check(grid),
                        "observed_overrides": module.observe_overrides(grid),
                        "facts": analysis["facts"]})
    pairs = row["train"] + [row["test"]]
    for i, pair in enumerate(pairs):
        grid = pair["input"]
        assert module.self_check(grid) == []
        assert intended(grid) == pair["output"]
        assert rival_skip_row_with_nonpair_color(grid) == pair["output"]
        records.append({"name": f"canonical_{i}", "kind": "canonical", **pair})

    observations = []
    # At most 128 draws per family/band. Retain one grid per profile/band
    # for actual selected-authority labels: 30 generated + 3 canonical + 2 witnesses.
    for band_i, band in enumerate(("easy", "medium", "hard")):
        for family in ("linked", "generalized"):
            expected = {p[0] for p in module.PUBLIC_PROFILES} if family == "linked" else set(module.GENERAL_PROFILES)
            seen = set()
            for sample_index in range(128):
                seed = 260008 + band_i * 1000
                grid = module.generate(seed, sample_index, difficulty=band, scene_family=family)
                analysis = module._analyze(grid)
                assert analysis["errors"] == []
                facts = analysis["facts"]
                profile = facts["linked_profile"] or facts["generalized_profile"]
                assert intended(grid) == module.rule_mirror(grid)
                assert rival_skip_row_with_nonpair_color(grid) == intended(grid)
                observation = {"seed": seed, "sample_index": sample_index,
                               "difficulty": band, "scene_family": family,
                               "profile": profile, "self_check": [],
                               "rival_matches_mirror": True}
                observations.append(observation)
                if profile not in seen:
                    records.append({"name": f"generated_{band}_{profile}",
                                    "kind": "generated", "input": grid, **observation})
                    seen.add(profile)
                if seen == expected:
                    break
            assert seen == expected, (band, family, seen, expected)
    write("records.json", records)
    write("bounded_draw_observations.json", observations)
    write("coverage_inputs.json", [r["input"] for r in records])
    print(json.dumps({"status": "prepared", "generator_sha256": metadata["generator_sha256"],
                      "records": len(records), "bounded_draws": len(observations),
                      "review_index_present": metadata["review_index_present"]}))


def analyze():
    source, module = load_module()
    records = json.loads((HERE / "records.json").read_text())
    receipt = json.loads((HERE / "coverage_racket.json").read_text())
    metadata = json.loads((HERE / "source_metadata.json").read_text())
    assert receipt["generator_sha256"] == metadata["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == len(records)
    results = []
    for record, execution in zip(records, receipt["results"]):
        assert execution["error"] is None, execution
        actual = execution["output"]
        grid = record["input"]
        assert actual == intended(grid) == module.rule_mirror(grid)
        rival = rival_skip_row_with_nonpair_color(grid)
        assert (actual != rival) == (record["kind"] == "witness")
        results.append({"name": record["name"], "kind": record["kind"],
                        "input": grid, "actual_selected_racket_output": actual,
                        "rival_output": rival, "rival_matches_actual": rival == actual,
                        "self_check": module.self_check(grid),
                        "different_cells_zero_based": [[r, c] for r in range(len(grid))
                                                        for c in range(len(grid[0]))
                                                        if actual[r][c] != rival[r][c]]})
    minimal_receipt = json.loads((HERE / "racket.json").read_text())
    assert minimal_receipt["rule_hash_matches_catalog"] is True
    assert minimal_receipt["generator_sha256"] == metadata["generator_sha256"]
    assert minimal_receipt["results"][0]["error"] is None
    assert minimal_receipt["results"][0]["output"] == results[0]["actual_selected_racket_output"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == metadata["generator_sha256"]
    write("comparisons.json", results)
    summary = {
        "task_id": TASK,
        "finding_type": "support/teaching defect",
        "rival": "skip_row_with_nonpair_color",
        "rival_classification": "canonical-fit rival; not a sampler-only shortcut",
        "actual_authority": {k: receipt[k] for k in ("generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_hash_matches_catalog")},
        "source_unchanged": True,
        "canonical_pairs_checked_with_actual_racket": sum(r["kind"] == "canonical" for r in results),
        "generated_profiles_checked_with_actual_racket": sum(r["kind"] == "generated" for r in results),
        "witnesses_checked_with_actual_racket": sum(r["kind"] == "witness" for r in results),
        "all_racket_labels_match_generator_mirror": True,
        "rival_fits_all_canonical_and_generated_labels": True,
        "witnesses_validated": True,
        "minimal_witness_shape": [5, 7],
        "minimum_nonzero_cells_under_self_check_and_this_rival": 5,
        "minimality_reason": "The validator requires two distinct visible eligible pairs (at least four endpoints) and 5x7 dimensions. A color of non-two count requires at least one additional cell on an eligible row; this witness uses exactly five nonzero cells and changes exactly two blank cells.",
        "same_witness_at_sampled_shape": [6, 9],
        "sampler_structure": "All linked rows contain one eligible pair. Generalized constructors assign positive rows separately from blocked, triple, and adjacent rows. Only multi_color_row combines pairs, and both colors have count two. Thus no emitted grid can place a singleton/triple alongside a visibly eligible bridge in the same row.",
        "bound": "Finite Racket checks cover 3 canonical pairs and one realization of each of 10 profiles at each of 3 bands, plus 2 witnesses. All-support rival agreement follows from constructor inspection, not from the finite sample count.",
        "recommendation": "Add a generated row containing a visible eligible pair plus an unrelated singleton (outside its interval); cover eligible pairs alongside count/blocker decoys in the same row, and retain this canonical-fit rival as a lesson counterexample check.",
    }
    write("findings.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
