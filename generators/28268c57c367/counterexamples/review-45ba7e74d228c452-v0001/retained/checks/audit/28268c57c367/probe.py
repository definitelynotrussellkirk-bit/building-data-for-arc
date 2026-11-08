"""Findings-only, public-authority probe for generator 28268c57c367.

Run `prepare`, public `arcpuzzles apply`, then `analyze` through review.py run.
The conditional rival is an intentional diagnostic rule, not an attempted solve.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "28268c57c367"
HERE = Path(__file__).resolve().parent
NEW_RIVAL = "nearest_when_no_offwall_gray"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def conditional_rival(grid):
    """First ownership only when off-wall gray exists; otherwise nearest wins."""
    wall = next(c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid))
    use_first = any(5 in row[:wall] for row in grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        first = nearest = None
        for c, value in enumerate(row[:wall]):
            if value not in (0, 5):
                nearest = value
                if first is None:
                    first = value
            elif value == 0:
                color = first if use_first else nearest
                if color is not None:
                    out[r][c] = color
    return out


def differences(expected, actual):
    assert len(expected) == len(actual)
    assert all(len(a) == len(b) for a, b in zip(expected, actual))
    return [
        {"row": r, "column": c, "racket": wanted, "rival": actual[r][c]}
        for r, row in enumerate(expected)
        for c, wanted in enumerate(row)
        if wanted != actual[r][c]
    ]


def setup():
    # Audit evidence lives outside repo; review.py run sets the public runtime cwd.
    root = find_root(Path.cwd())
    module, source, source_sha = load_selected_generator(TASK, root=root)
    return root, module, source, source_sha


def prepare():
    root, module, source, source_sha = setup()
    # The assigned target's canonical record, retained in this packet.
    canonical_file = root / "shared/data/base/solutions/banks/d7b013a675b4/medium_k13__28268c57c367.json"
    canonical_record = json.loads(canonical_file.read_text())
    pairs = canonical_pairs(TASK, root=root)
    grids = [pair["input"] for pair in pairs]
    records = [
        {"case_index": i, "case_id": f"canonical-{i}", "origin": "canonical",
         "self_check_errors": module.self_check(pair["input"]),
         "documented_domain": "canonical pair and accepted broader lawful rule domain",
         "expected_output_sha256": digest(pair["output"])}
        for i, pair in enumerate(pairs)
    ]
    settings = [
        (band, seed, index, {})
        for band in ("easy", "medium", "hard")
        for seed in range(4)
        for index in range(4)
    ]
    settings += [("medium", 6, 0, {}), ("medium", 6, 0, {"n_gray": 0})]
    for band, seed, index, overrides in settings:
        grid = module.generate(seed, index, difficulty=band, **overrides)
        observed = module.observe_overrides(grid)
        errors = module.self_check(grid)
        assert not errors, (band, seed, index, overrides, errors)
        for name, value in overrides.items():
            assert observed[name] == value
        for name, axis in module.AXES.items():
            low, high = map(int, axis["valid"].split(".."))
            assert low <= observed[name] <= high, (name, observed)
        assert observed["wall_col"] <= observed["grid_w"] - 2
        assert observed["n_distinct_colors"] <= observed["n_cells"]
        records.append({
            "case_index": len(grids), "case_id": f"{band}-s{seed}-i{index}" + ("-gray0" if overrides else ""),
            "origin": "generated", "difficulty": band, "seed": seed,
            "sample_index": index, "overrides": overrides,
            "profile": module.schedule_profile(seed, index, band),
            "self_check_errors": errors, "observed_axes": observed,
            "documented_domain": "returned by selected generator; every documented axis bound holds",
        })
        grids.append(grid)
    assert len(grids) <= 64
    for record, grid in zip(records, grids):
        record["input_sha256"] = digest(grid)
    rule_code = canonical_record["racket_target"]["raw_code"]
    metadata = {
        "schema": "28268c57c367-conditional-ownership-audit-v1",
        "task_id": TASK, "generator_version": module.VERSION,
        "generator_source": str(source.relative_to(root)), "generator_sha256": source_sha,
        "declared_rule_hash": module.RULE_HASH,
        "canonical_record": str(canonical_file.relative_to(root)),
        "canonical_record_sha256": hashlib.sha256(canonical_file.read_bytes()).hexdigest(),
        "canonical_rule_raw_code_sha256": hashlib.sha256(rule_code.encode()).hexdigest(),
        "canonical_pairs": len(pairs), "case_count": len(grids),
        "default_population_policy": {
            "bands": ["easy", "medium", "hard"], "seed_range": [0, 3],
            "sample_index_range": [0, 3], "draw_count": 48,
            "additional_natural_case": {"difficulty": "medium", "seed": 6, "sample_index": 0},
            "selection": "direct generate, no filtering or rejection, no overrides",
        },
        "counterexample_policy": {"difficulty": "medium", "seed": 6, "sample_index": 0,
                                  "overrides": {"n_gray": 0}},
        "lesson_policy": {"demonstrations": 3, "production": "indices 0,1,2 demos; 3 query",
                          "rotations": "each one of indices 0..3 held out; remaining three demos",
                          "cohorts": "same seed and band, seed 0..3, easy/medium/hard"},
        "diagnostic_rival": NEW_RIVAL,
        "diagnostic_rival_description": "Nearest-source ownership when no off-wall gray exists; otherwise first-source ownership. Preserve every original nonzero cell and right-side content.",
        "declared_canonical_shortcuts": sorted(module.CANONICAL_SHORTCUTS),
        "declared_lesson_competitors": sorted(module.LESSON_COMPETITORS),
        "cases": records,
    }
    write("input.json", grids)
    write("population.json", metadata)
    print(json.dumps({"prepared_cases": len(grids), "generator_sha256": source_sha,
                      "canonical_pairs": len(pairs), "default_draws": 49, "pinned_draws": 1}))


def analyze():
    root, module, source, source_sha = setup()
    metadata = json.loads((HERE / "population.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    grids = json.loads((HERE / "input.json").read_text())
    assert metadata["generator_sha256"] == source_sha
    assert racket["generator_sha256"] == source_sha
    assert racket["executed_rule_hash"] == module.RULE_HASH
    assert racket["rule_hash_matches_catalog"] is True
    labels = racket["results"]
    assert len(labels) == len(grids)
    assert all("output" in label for label in labels)
    assert all(label["valid_output"] and not label["error"] for label in labels)
    outputs = [label["output"] for label in labels]
    canonical_count = metadata["canonical_pairs"]
    canonical = canonical_pairs(TASK, root=root)
    assert [pair["output"] for pair in canonical] == outputs[:canonical_count]
    rivals = dict(module.LESSON_COMPETITORS)
    rivals[NEW_RIVAL] = conditional_rival
    original_digest = digest(grids)
    predictions = {name: [rival(grid) for grid in grids] for name, rival in rivals.items()}
    assert digest(grids) == original_digest, "Rival modified inputs"
    default_ids = [record["case_index"] for record in metadata["cases"]
                   if record["origin"] == "generated" and not record["overrides"]]
    pinned_ids = [record["case_index"] for record in metadata["cases"]
                  if record["origin"] == "generated" and record["overrides"]]
    canonical_ids = list(range(canonical_count))
    counts = {}
    for name, guesses in predictions.items():
        counts[name] = {
            "canonical": {"matched": sum(guesses[i] == outputs[i] for i in canonical_ids), "total": len(canonical_ids)},
            "unrestricted_default": {"matched": sum(guesses[i] == outputs[i] for i in default_ids), "total": len(default_ids)},
            "pinned_counterexample": {"matched": sum(guesses[i] == outputs[i] for i in pinned_ids), "total": len(pinned_ids)},
        }
    for name in module.CANONICAL_SHORTCUTS:
        assert counts[name]["canonical"]["matched"] == canonical_count
    assert counts[NEW_RIVAL]["canonical"]["matched"] == canonical_count
    assert counts[NEW_RIVAL]["unrestricted_default"]["matched"] == len(default_ids)
    assert counts[NEW_RIVAL]["pinned_counterexample"]["matched"] == 0
    production = []
    rotations = []
    for offset in range(canonical_count, canonical_count + 48, 4):
        ids = list(range(offset, offset + 4))
        for query_position in range(4):
            demos = [i for j, i in enumerate(ids) if j != query_position]
            refuters = {name: [i for i in demos if predictions[name][i] != outputs[i]] for name in rivals}
            result = {"first_case_index": offset, "query_position": query_position,
                      "query_case_index": ids[query_position], "demo_case_indices": demos,
                      "rival_refuting_demo_indices": refuters}
            rotations.append(result)
            if query_position == 3:
                production.append(result)
    assert all(all(row["rival_refuting_demo_indices"][name] for name in module.LESSON_COMPETITORS)
               for row in rotations)
    witness_index = pinned_ids[0]
    witness = metadata["cases"][witness_index]
    report = {
        "task_id": TASK, "generator_sha256": source_sha,
        "declared_rule_hash": module.RULE_HASH,
        "canonical_rule_raw_code_sha256": metadata["canonical_rule_raw_code_sha256"],
        "authority": "public arcpuzzles apply; actual response in racket.json",
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "authority_command": racket["command"], "authority_cwd": racket["cwd"],
        "exact_wrapper_commands": "checks/audit/28268c57c367/commands.json",
        "authority_response_sha256": hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest(),
        "racket_case_count": len(grids), "unique_inputs": len({digest(g) for g in grids}),
        "default_draws": len(default_ids),
        "default_unique_inputs": len({digest(grids[i]) for i in default_ids}),
        "validator_rejections": sum(bool(record["self_check_errors"]) for record in metadata["cases"]),
        "all_canonical_outputs_match_racket": True,
        "rival_fit_counts": counts,
        "source_bound_reason": [
            "For unrestricted defaults, core has two or three source cells on distinct rows; nearest-source and first-source therefore agree.",
            "For unrestricted defaults, rich always has two or three off-wall gray cells; the conditional rival selects first-source ownership.",
            "Consequently the conditional rival fits every unrestricted default input by construction, independent of seed, index, or supported difficulty. This is a source-level argument, not a claim of exhaustive random testing.",
        ],
        "source_locations": ["generators/28268c57c367/generator.py:90-101",
                             "generators/28268c57c367/generator.py:111-130"],
        "lesson_results": {"production_views": len(production), "rotation_views": len(rotations),
                           "named_competitors_refuted_in_every_view": True,
                           "conditional_rival_refuted_views": sum(bool(row["rival_refuting_demo_indices"][NEW_RIVAL]) for row in rotations),
                           "views_overlap_same_48_default_inputs": True,
                           "scope": "direct assembly; finite named-rival checks, not production materialization or universal induction"},
        "counterexample": {**witness, "input": grids[witness_index],
                           "actual_racket_output": outputs[witness_index],
                           "rival_output": predictions[NEW_RIVAL][witness_index],
                           "differing_cells": differences(outputs[witness_index], predictions[NEW_RIVAL][witness_index]),
                           "documented_default_lesson_guarantee_applies": False,
                           "default_lesson_guarantee_note": "Notes explicitly exclude pinned lessons. The finding concerns the default distribution's inability to teach this additional canonical-fitting rival, not a violation of the declared four-rival guarantee."},
        "production_views": production, "rotation_views": rotations,
        "finding": "Reproduced canonical-fitting default-support shortcut; no output-label defect established",
        "selected_source_unchanged": hashlib.sha256(source.read_bytes()).hexdigest() == source_sha,
        "status": "EXPECTED_COUNTEREXAMPLE_REPRODUCED",
    }
    assert report["selected_source_unchanged"]
    write("counterexample.json", report)
    print(json.dumps({"status": report["status"], "racket_cases": len(grids),
                      "unique_inputs": report["unique_inputs"], "default_draws": len(default_ids),
                      "default_unique_inputs": report["default_unique_inputs"],
                      "new_rival": counts[NEW_RIVAL],
                      "differing_cells": report["counterexample"]["differing_cells"],
                      "production_views": len(production), "rotation_views": len(rotations)}))


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
